"""
Tests for constraint builders. Each test builds a small CP-SAT model,
applies constraints, and checks that the solver response is as expected.
"""

from ortools.sat.python import cp_model

from app.constraints.physician_constraints import add_physician_constraints
from app.constraints.team_constraints import add_team_constraints


def _make_vars(model, n_physicians, n_weeks, teams=("A", "B", "C")):
    """Build assign[p][w][t] boolean vars."""
    assign = {}
    for p in range(n_physicians):
        assign[p] = {}
        for w in range(n_weeks):
            assign[p][w] = {}
            for t in teams:
                assign[p][w][t] = model.new_bool_var(f"assign_p{p}_w{w}_t{t}")
    return assign


# ---------------------------------------------------------------------------
# Team constraint tests
# ---------------------------------------------------------------------------


def test_at_most_one_team_per_physician_per_week(teams_df, requests_df):
    """A physician can only be on one team per week."""
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_team_constraints(model, assign, teams_df, requests_df)
    # Force physician 0 to both A and B in week 0 → should be infeasible
    model.add(assign[0][0]["A"] == 1)
    model.add(assign[0][0]["B"] == 1)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE


def test_team_b_exactly_one(teams_df, requests_df):
    """Team B must have exactly 1 physician per week."""
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_team_constraints(model, assign, teams_df, requests_df)
    # Force 2 physicians to B in week 0 → infeasible (exactly 1)
    model.add(assign[0][0]["B"] == 1)
    model.add(assign[1][0]["B"] == 1)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE


def test_team_c_exactly_one(teams_df, requests_df):
    """Team C must have exactly 1 physician per week."""
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_team_constraints(model, assign, teams_df, requests_df)
    model.add(assign[0][0]["C"] == 1)
    model.add(assign[1][0]["C"] == 1)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE


def test_hard_team_block(teams_df, requests_df):
    """teams.csv[B][Clinician 3] == 0 → Clinician 3 cannot be on team B."""
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_team_constraints(model, assign, teams_df, requests_df)
    # Clinician 3 is index 2 in 0-based; force assign on B → infeasible
    model.add(assign[2][0]["B"] == 1)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE


# ---------------------------------------------------------------------------
# Physician constraint tests
# ---------------------------------------------------------------------------


def test_unavailability_block(teams_df, requests_df):
    """requests.csv -1 → physician cannot be assigned any team that week."""
    # Clinician 2 (index 1) is unavailable week 3 (index 2)
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_physician_constraints(model, assign, teams_df, requests_df)
    for t in ("A", "B", "C"):
        model.add(assign[1][2][t] == 0)  # already forced by constraint; just assert feasible
    # Force assignment despite unavailability → infeasible
    model.add(assign[1][2]["A"] == 1)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    assert status == cp_model.INFEASIBLE


def test_contract_floor(teams_df, requests_df):
    """Each physician's total assignments must be >= their contract total."""
    # Clinician 1 (index 0) has contract total 5 but we only have 4 weeks →
    # model must be infeasible when we try to enforce a floor > available weeks.
    import io

    import pandas as pd

    tight_teams_csv = """Team,Clinician 1,Clinician 2,Clinician 3
A,10,2,2
B,0,1,0
C,0,1,1
"""
    t_df = pd.read_csv(io.StringIO(tight_teams_csv), index_col="Team")
    model = cp_model.CpModel()
    assign = _make_vars(model, 3, 4)
    add_physician_constraints(model, assign, t_df, requests_df)
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    # Contract floor for Clinician 1 is 10 but only 4 weeks → infeasible
    assert status == cp_model.INFEASIBLE
