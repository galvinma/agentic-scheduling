from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

TEAM_COLORS = {"A": "#4C72B0", "B": "#DD8452", "C": "#55A868"}


def write_schedule_csv(schedule_df: pd.DataFrame, path: Path):
    schedule_df.to_csv(path, index=False)


def write_gantt_chart(schedule_df: pd.DataFrame, path: Path):
    weeks = list(schedule_df["Week Starting"])
    n_weeks = len(weeks)

    # Collect all unique clinicians across all team columns
    all_clinicians = set()
    for col in ["Team A", "Team B", "Team C"]:
        for cell in schedule_df[col]:
            if str(cell) != "GAP" and str(cell).strip():
                for name in str(cell).split(","):
                    all_clinicians.add(name.strip())

    def _clin_sort_key(c):
        last = c.split()[-1]
        return int(last) if last.isdigit() else 0

    clinicians = sorted(all_clinicians, key=_clin_sort_key)
    n_physicians = len(clinicians)
    clin_index = {c: i for i, c in enumerate(clinicians)}

    fig, ax = plt.subplots(figsize=(max(14, n_weeks * 0.4), max(6, n_physicians * 0.4)))

    for w, row in schedule_df.iterrows():
        for team, col in [("A", "Team A"), ("B", "Team B"), ("C", "Team C")]:
            cell = str(row[col])
            if cell == "GAP" or not cell.strip():
                continue
            for name in cell.split(","):
                name = name.strip()
                if name and name in clin_index:
                    y = clin_index[name]
                    ax.barh(y, 0.8, left=w, color=TEAM_COLORS[team], edgecolor="white", height=0.6)

    ax.set_yticks(range(n_physicians))
    ax.set_yticklabels(clinicians, fontsize=8)
    ax.set_xticks(range(n_weeks))
    ax.set_xticklabels(weeks, rotation=90, fontsize=7)
    ax.set_xlabel("Week")
    ax.set_ylabel("Clinician")
    ax.set_title("Clinical Schedule Gantt Chart")

    legend_patches = [
        mpatches.Patch(color=TEAM_COLORS[t], label=f"Team {t}") for t in ("A", "B", "C")
    ]
    ax.legend(handles=legend_patches, loc="upper right")

    plt.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)
