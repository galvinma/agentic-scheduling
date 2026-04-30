from ortools.sat.python import cp_model


def add_team_constraints(model: cp_model.CpModel, assign: dict, teams_df, requests_df):
    """
    Hard constraints:
    - Each physician assigned to at most one team per week
    - Team B: exactly 1 physician per week (gap slack if infeasible)
    - Team C: exactly 1 physician per week (gap slack if infeasible)
    - Team A: at least 2, at most 4 physicians per week (gap slack if infeasible)
    - teams.csv[team][physician] == 0 → hard block for that team

    Returns (gap_b, gap_c, gap_a) slack variable lists for use in objective.
    """
    clinicians = list(teams_df.columns)
    n_physicians = len(clinicians)
    n_weeks = len(requests_df)
    teams = list(teams_df.index)  # ["A", "B", "C"]

    # Hard block: teams.csv == 0
    for p, clinician in enumerate(clinicians):
        for t in teams:
            if teams_df.loc[t, clinician] == 0:
                for w in range(n_weeks):
                    model.add(assign[p][w][t] == 0)

    # At most one team per physician per week
    for p in range(n_physicians):
        for w in range(n_weeks):
            model.add(sum(assign[p][w][t] for t in teams) <= 1)

    # Coverage constraints with gap slack variables
    gap_b = [model.new_bool_var(f"gap_b_{w}") for w in range(n_weeks)]
    gap_c = [model.new_bool_var(f"gap_c_{w}") for w in range(n_weeks)]
    gap_a = [model.new_int_var(0, 2, f"gap_a_{w}") for w in range(n_weeks)]

    for w in range(n_weeks):
        b_sum = sum(assign[p][w]["B"] for p in range(n_physicians))
        c_sum = sum(assign[p][w]["C"] for p in range(n_physicians))
        a_sum = sum(assign[p][w]["A"] for p in range(n_physicians))

        model.add(b_sum <= 1)
        model.add(b_sum + gap_b[w] >= 1)

        model.add(c_sum <= 1)
        model.add(c_sum + gap_c[w] >= 1)

        model.add(a_sum + gap_a[w] >= 2)
        model.add(a_sum <= 4)

    return gap_b, gap_c, gap_a
