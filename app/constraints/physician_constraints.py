from ortools.sat.python import cp_model


def add_physician_constraints(
    model: cp_model.CpModel,
    assign: dict,
    teams_df,
    requests_df,
):
    """
    Hard constraints:
    - Availability blocks (requests.csv == -1)
    - Contract floor (total assignments >= contract total from teams.csv)

    Returns (back_to_back_vars, pref_reward_vars) for use in objective.
    """
    clinicians = list(teams_df.columns)
    n_physicians = len(clinicians)
    n_weeks = len(requests_df)
    teams = list(teams_df.index)

    # Availability blocks
    for p, clinician in enumerate(clinicians):
        for w in range(n_weeks):
            if requests_df.iloc[w][clinician] == -1:
                for t in teams:
                    model.add(assign[p][w][t] == 0)

    # Contract floor: total assignments across all teams >= contract total
    for p, clinician in enumerate(clinicians):
        contract_total = int(teams_df[clinician].sum())
        all_assignments = [assign[p][w][t] for w in range(n_weeks) for t in teams]
        model.add(sum(all_assignments) >= contract_total)

    # Back-to-back penalty variables: 1 if physician works in both week w and w+1
    back_to_back = []
    for p in range(n_physicians):
        for w in range(n_weeks - 1):
            worked_w = model.new_bool_var(f"worked_p{p}_w{w}")
            worked_w1 = model.new_bool_var(f"worked_p{p}_w{w + 1}")
            model.add(worked_w == sum(assign[p][w][t] for t in teams))
            model.add(worked_w1 == sum(assign[p][w + 1][t] for t in teams))
            btb = model.new_bool_var(f"btb_p{p}_w{w}")
            model.add_bool_and([worked_w, worked_w1]).only_enforce_if(btb)
            model.add_bool_or([worked_w.Not(), worked_w1.Not()]).only_enforce_if(btb.Not())
            back_to_back.append(btb)

    # Preferred-week reward variables
    pref_rewards = []
    for p, clinician in enumerate(clinicians):
        for w in range(n_weeks):
            if requests_df.iloc[w][clinician] == 1:
                assigned = model.new_bool_var(f"pref_p{p}_w{w}")
                model.add(assigned == sum(assign[p][w][t] for t in teams))
                pref_rewards.append(assigned)

    return back_to_back, pref_rewards
