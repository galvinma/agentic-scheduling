import io

import pandas as pd
import pytest

CLINICIANS = ["Clinician 1", "Clinician 2", "Clinician 3"]
WEEKS = ["6/30/2025", "7/7/2025", "7/14/2025", "7/21/2025"]

# teams.csv fixture: 3 clinicians, 3 teams
# Clinician 3 has 0 on team B → hard block
TEAMS_CSV = """Team,Clinician 1,Clinician 2,Clinician 3
A,3,2,2
B,1,1,0
C,1,1,1
"""

# requests.csv fixture: 4 weeks
# Clinician 2 unavailable week 3 (index 2)
REQUESTS_CSV = """Week Starting,Clinician 1,Clinician 2,Clinician 3
6/30/2025,0,1,0
7/7/2025,1,0,0
7/14/2025,0,-1,1
7/21/2025,0,0,0
"""


@pytest.fixture
def teams_df():
    df = pd.read_csv(io.StringIO(TEAMS_CSV), index_col="Team")
    return df


@pytest.fixture
def requests_df():
    return pd.read_csv(io.StringIO(REQUESTS_CSV))
