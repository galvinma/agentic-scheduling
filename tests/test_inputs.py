def test_teams_csv_shape(teams_df):
    assert teams_df.shape == (3, 3)
    assert list(teams_df.index) == ["A", "B", "C"]


def test_teams_csv_hard_block(teams_df):
    assert teams_df.loc["B", "Clinician 3"] == 0


def test_teams_csv_contract_totals(teams_df):
    # Column sums are total contracted shifts per physician
    assert teams_df["Clinician 1"].sum() == 5
    assert teams_df["Clinician 3"].sum() == 3


def test_requests_csv_shape(requests_df):
    assert requests_df.shape == (4, 4)  # 4 weeks, Week Starting + 3 clinicians
    assert "Week Starting" in requests_df.columns


def test_requests_csv_unavailable(requests_df):
    row = requests_df[requests_df["Week Starting"] == "7/14/2025"].iloc[0]
    assert row["Clinician 2"] == -1


def test_requests_csv_values_in_range(requests_df):
    data = requests_df.drop(columns=["Week Starting"])
    assert data.isin([-1, 0, 1]).all().all()
