"""Tests for output writing (CSV and PNG)."""

import pandas as pd
import pytest

from app.outputs import write_gantt_chart, write_schedule_csv


@pytest.fixture
def sample_schedule():
    return pd.DataFrame(
        {
            "Week Starting": ["6/30/2025", "7/7/2025", "7/14/2025"],
            "Team A": ["Clinician 1, Clinician 2", "Clinician 3", "GAP"],
            "Team B": ["Clinician 3", "Clinician 1", "GAP"],
            "Team C": ["Clinician 4", "Clinician 2", "GAP"],
        }
    )


def test_write_schedule_csv_creates_file(tmp_path, sample_schedule):
    out = tmp_path / "schedule.csv"
    write_schedule_csv(sample_schedule, out)
    assert out.exists()
    loaded = pd.read_csv(out)
    assert list(loaded.columns) == ["Week Starting", "Team A", "Team B", "Team C"]
    assert len(loaded) == 3


def test_write_schedule_csv_gap_preserved(tmp_path, sample_schedule):
    out = tmp_path / "schedule.csv"
    write_schedule_csv(sample_schedule, out)
    loaded = pd.read_csv(out)
    assert loaded.iloc[2]["Team A"] == "GAP"


def test_write_gantt_chart_creates_png(tmp_path, sample_schedule):
    out = tmp_path / "schedule.png"
    write_gantt_chart(sample_schedule, out)
    assert out.exists()
    assert out.stat().st_size > 0
