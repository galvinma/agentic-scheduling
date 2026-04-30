from ortools.sat.python import cp_model


def add_team_constraints(model: cp_model.CpModel, assign: dict, teams_df, requests_df):
    """
    Hard constraints:
    - Each physician assigned to at most one team per week
    - Team B: exactly 1 physician per week
    - Team C: exactly 1 physician per week
    - Team A: at least 2 physicians per week
    - teams.csv[team][physician] == 0 → hard block for that team
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

    # Team B exactly 1, Team C exactly 1
    for w in range(n_weeks):
        model.add(sum(assign[p][w]["B"] for p in range(n_physicians)) == 1)
        model.add(sum(assign[p][w]["C"] for p in range(n_physicians)) == 1)

    # Team A at least 2
    for w in range(n_weeks):
        model.add(sum(assign[p][w]["A"] for p in range(n_physicians)) >= 2)
