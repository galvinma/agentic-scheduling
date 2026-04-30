import pandas as pd
from ortools.sat.python import cp_model

from app.constraints.physician_constraints import add_physician_constraints
from app.constraints.team_constraints import add_team_constraints

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
    teams = list(teams_df.index)

    model = cp_model.CpModel()

    assign = {}
    for p in range(n_physicians):
        assign[p] = {}
        for w in range(n_weeks):
            assign[p][w] = {}
            for t in teams:
                assign[p][w][t] = model.new_bool_var(f"a_p{p}_w{w}_t{t}")

    gap_b, gap_c, gap_a = add_team_constraints(model, assign, teams_df, requests_df)
    back_to_back, pref_rewards = add_physician_constraints(model, assign, teams_df, requests_df)

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
