import pandas as pd
from ortools.sat.python import cp_model

BACK_TO_BACK_PENALTY = 10
PREF_REWARD = 1
GAP_PENALTY = 1000


def build_and_solve(teams_df, requests_df, time_limit: int = 60):
    """
    Build and solve the CP-SAT scheduling model.

    Returns:
        schedule_df: DataFrame with columns [Week Starting, Team A, Team B, Team C]
        gaps: list of week strings where coverage requirements could not be met
    """
    clinicians = list(teams_df.columns)
    n_physicians = len(clinicians)
    n_weeks = len(requests_df)
    teams = list(teams_df.index)  # e.g. ["A", "B", "C"]

    model = cp_model.CpModel()

    # Decision variables: assign[p][w][t] ∈ {0,1}
    assign = {}
    for p in range(n_physicians):
        assign[p] = {}
        for w in range(n_weeks):
            assign[p][w] = {}
            for t in teams:
                assign[p][w][t] = model.new_bool_var(f"a_p{p}_w{w}_t{t}")

    # Hard: at most one team per physician per week
    for p in range(n_physicians):
        for w in range(n_weeks):
            model.add(sum(assign[p][w][t] for t in teams) <= 1)

    # Hard: team-block (teams.csv == 0) and availability (-1)
    for p, clinician in enumerate(clinicians):
        for t in teams:
            if teams_df.loc[t, clinician] == 0:
                for w in range(n_weeks):
                    model.add(assign[p][w][t] == 0)
        for w in range(n_weeks):
            if requests_df.iloc[w][clinician] == -1:
                for t in teams:
                    model.add(assign[p][w][t] == 0)

    # Hard: contract floor
    for p, clinician in enumerate(clinicians):
        contract = int(teams_df[clinician].sum())
        model.add(sum(assign[p][w][t] for w in range(n_weeks) for t in teams) >= contract)

    # Coverage constraints with gap slack variables
    # Team B: exactly 1 (or gap)
    # Team C: exactly 1 (or gap)
    # Team A: at least 2 (or reduced by gap slack)
    gap_b = [model.new_bool_var(f"gap_b_{w}") for w in range(n_weeks)]
    gap_c = [model.new_bool_var(f"gap_c_{w}") for w in range(n_weeks)]
    gap_a = [model.new_int_var(0, 2, f"gap_a_{w}") for w in range(n_weeks)]

    for w in range(n_weeks):
        b_sum = sum(assign[p][w]["B"] for p in range(n_physicians))
        c_sum = sum(assign[p][w]["C"] for p in range(n_physicians))
        a_sum = sum(assign[p][w]["A"] for p in range(n_physicians))

        # B: between 0 and 1; must have 1 unless gap
        model.add(b_sum <= 1)
        model.add(b_sum + gap_b[w] >= 1)

        # C: between 0 and 1; must have 1 unless gap
        model.add(c_sum <= 1)
        model.add(c_sum + gap_c[w] >= 1)

        # A: at least 2 unless gap absorbs shortfall
        model.add(a_sum + gap_a[w] >= 2)

    # Soft: back-to-back penalty
    back_to_back = []
    for p in range(n_physicians):
        for w in range(n_weeks - 1):
            worked_w = model.new_bool_var(f"wk_p{p}_w{w}")
            worked_w1 = model.new_bool_var(f"wk_p{p}_w{w + 1}")
            model.add(worked_w == sum(assign[p][w][t] for t in teams))
            model.add(worked_w1 == sum(assign[p][w + 1][t] for t in teams))
            btb = model.new_bool_var(f"btb_p{p}_w{w}")
            model.add_bool_and([worked_w, worked_w1]).only_enforce_if(btb)
            model.add_bool_or([worked_w.Not(), worked_w1.Not()]).only_enforce_if(btb.Not())
            back_to_back.append(btb)

    # Soft: preferred-week rewards
    pref_rewards = []
    for p, clinician in enumerate(clinicians):
        for w in range(n_weeks):
            if requests_df.iloc[w][clinician] == 1:
                assigned = model.new_bool_var(f"pref_p{p}_w{w}")
                model.add(assigned == sum(assign[p][w][t] for t in teams))
                pref_rewards.append(assigned)

    # Objective: minimize penalties, maximize rewards
    penalty_terms = [BACK_TO_BACK_PENALTY * v for v in back_to_back]
    penalty_terms += [GAP_PENALTY * v for v in gap_b]
    penalty_terms += [GAP_PENALTY * v for v in gap_c]
    penalty_terms += [GAP_PENALTY * v for v in gap_a]
    reward_terms = [PREF_REWARD * v for v in pref_rewards]

    model.minimize(sum(penalty_terms) - sum(reward_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, []

    # Extract solution
    rows = []
    gaps = []
    for w in range(n_weeks):
        week_label = requests_df.iloc[w]["Week Starting"]
        is_gap = solver.value(gap_b[w]) or solver.value(gap_c[w]) or solver.value(gap_a[w]) > 0

        team_a_physicians = []
        team_b_physicians = []
        team_c_physicians = []

        for p, clinician in enumerate(clinicians):
            if solver.value(assign[p][w]["A"]):
                team_a_physicians.append(clinician)
            if solver.value(assign[p][w]["B"]):
                team_b_physicians.append(clinician)
            if solver.value(assign[p][w]["C"]):
                team_c_physicians.append(clinician)

        rows.append(
            {
                "Week Starting": week_label,
                "Team A": ", ".join(team_a_physicians) if team_a_physicians else "GAP",
                "Team B": ", ".join(team_b_physicians) if team_b_physicians else "GAP",
                "Team C": ", ".join(team_c_physicians) if team_c_physicians else "GAP",
            }
        )

        if is_gap:
            gaps.append(week_label)

    return pd.DataFrame(rows), gaps
