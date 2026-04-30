"""Integration tests: run the full solver on small fixtures and check output shape."""

import io

import pandas as pd
import pytest

from app.solver import build_and_solve

# 5 clinicians, 4 weeks: 4/week needed (2A+1B+1C), 5×4=20 capacity, feasible
TEAMS_CSV = """Team,Clinician 1,Clinician 2,Clinician 3,Clinician 4,Clinician 5
A,1,1,1,1,1
B,1,1,1,1,1
C,1,1,1,1,1
"""

REQUESTS_CSV = """Week Starting,Clinician 1,Clinician 2,Clinician 3,Clinician 4,Clinician 5
6/30/2025,0,0,0,0,0
7/7/2025,0,0,0,0,0
7/14/2025,0,0,0,0,0
7/21/2025,0,0,0,0,0
"""


@pytest.fixture
def small_teams():
    return pd.read_csv(io.StringIO(TEAMS_CSV), index_col="Team")


@pytest.fixture
def small_requests():
    return pd.read_csv(io.StringIO(REQUESTS_CSV))


def test_solver_returns_schedule_dataframe(small_teams, small_requests):
    schedule, gaps = build_and_solve(small_teams, small_requests)
    assert schedule is not None
    assert "Week Starting" in schedule.columns
    assert "Team A" in schedule.columns
    assert "Team B" in schedule.columns
    assert "Team C" in schedule.columns


def test_solver_correct_row_count(small_teams, small_requests):
    schedule, gaps = build_and_solve(small_teams, small_requests)
    assert len(schedule) == 4


def test_team_b_single_physician_per_week(small_teams, small_requests):
    schedule, gaps = build_and_solve(small_teams, small_requests)
    for _, row in schedule.iterrows():
        if row["Team B"] != "GAP":
            assignments = [x.strip() for x in str(row["Team B"]).split(",") if x.strip()]
            week = row["Week Starting"]
            assert len(assignments) == 1, f"Team B has {len(assignments)} in week {week}"


def test_team_c_single_physician_per_week(small_teams, small_requests):
    schedule, gaps = build_and_solve(small_teams, small_requests)
    for _, row in schedule.iterrows():
        if row["Team C"] != "GAP":
            assignments = [x.strip() for x in str(row["Team C"]).split(",") if x.strip()]
            assert len(assignments) == 1


def test_no_physician_on_two_teams_same_week(small_teams, small_requests):
    schedule, gaps = build_and_solve(small_teams, small_requests)
    for _, row in schedule.iterrows():
        all_assigned = []
        for col in ["Team A", "Team B", "Team C"]:
            val = str(row[col])
            if val not in ("GAP", "nan", "") and val.strip():
                all_assigned.extend([x.strip() for x in val.split(",") if x.strip()])
        week = row["Week Starting"]
        assert len(all_assigned) == len(set(all_assigned)), f"Duplicate physician in week {week}"


def test_gap_list_type(small_teams, small_requests):
    _, gaps = build_and_solve(small_teams, small_requests)
    assert isinstance(gaps, list)


def test_gap_flagged_when_all_unavailable():
    """When all physicians are unavailable in week 0, that week is flagged as a gap."""
    teams_csv = """Team,Clinician 1,Clinician 2,Clinician 3,Clinician 4,Clinician 5
A,1,1,1,1,1
B,1,1,1,1,1
C,1,1,1,1,1
"""
    # All unavailable in week 0, available weeks 1-3
    requests_csv = """Week Starting,Clinician 1,Clinician 2,Clinician 3,Clinician 4,Clinician 5
6/30/2025,-1,-1,-1,-1,-1
7/7/2025,0,0,0,0,0
7/14/2025,0,0,0,0,0
7/21/2025,0,0,0,0,0
"""
    teams_df = pd.read_csv(io.StringIO(teams_csv), index_col="Team")
    requests_df = pd.read_csv(io.StringIO(requests_csv))
    schedule, gaps = build_and_solve(teams_df, requests_df)
    assert "6/30/2025" in gaps or any("6/30" in str(g) for g in gaps)
    # Week 0 row should show GAP
    row0 = schedule.iloc[0]
    assert "GAP" in (row0["Team B"], row0["Team C"])
