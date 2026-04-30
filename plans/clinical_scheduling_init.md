# Plan: Clinical Scheduling Application — Initial Build

## What It Does

A Python CLI tool that reads physician team preferences and weekly availability, runs Google's CP-SAT solver to produce an optimal year-long weekly clinical schedule, and outputs a CSV and a Gantt chart.

## Why

Hospital scheduling is a complex constraint satisfaction problem. Manual scheduling is error-prone and time-consuming. CP-SAT finds optimal or near-optimal solutions that respect hard constraints (availability, contract obligations, team requirements) while honoring soft preferences (preferred weeks, no back-to-back shifts).

## Scope

**In scope:**
- Reading two input CSVs (team preferences, weekly requests)
- Building and solving a CP-SAT model
- Outputting a schedule CSV and matplotlib Gantt chart
- Flagging coverage gaps when a week cannot be fully staffed

**Out of scope:**
- Named physicians (all anonymous: Clinician 1–20)
- Locations (dropped during planning)
- Mid-year staffing changes
- Web UI or database persistence

---

## Inputs

Both CSVs live in `app/inputs/`.

### `teams.csv`
- Rows: teams (A, B, C)
- Columns: Clinician 1–20
- Values: integer number of shifts the physician requests on that team for the year
- **A value of 0 is a hard constraint** — the physician cannot be assigned to that team at all

### `requests.csv`
- Rows: 52 weeks, `Week Starting` column contains the Monday date (6/30/2025 – 6/22/2026)
- Columns: Clinician 1–20
- Values:
  - `-1` = unavailable that week (hard constraint, no assignment allowed)
  - `0` = no preference
  - `1` = prefers to work this week (soft constraint)

---

## Teams

| Team | Minimum Physicians | Notes |
|------|--------------------|-------|
| A    | 2                  | Absorbs all excess capacity |
| B    | 1 (exactly)        | |
| C    | 1 (exactly)        | |

Any physician can be assigned to any team, subject to their team preference (0 = hard block).

---

## Decision Variables

`assign[p][w][t]` ∈ {0, 1} — is physician `p` assigned to team `t` in week `w`?

---

## Constraints

### Hard Constraints
1. Each physician is assigned to at most one team per week
2. Team B has exactly 1 physician per week
3. Team C has exactly 1 physician per week
4. Team A has at least 2 physicians per week
5. If `teams.csv[team][physician] == 0`, that physician cannot be assigned to that team (ever)
6. If `requests.csv[week][physician] == -1`, that physician cannot be assigned any team that week
7. Each physician's total assignments across all teams meets or exceeds their contract total (sum of their row in `teams.csv`)

### Soft Constraints (penalized in objective)
1. **Strong penalty**: physician assigned in consecutive weeks (back-to-back clinical shifts)
2. **Soft reward**: physician assigned in a week where their `requests.csv` value is `1`

### Coverage Gaps
- If a week cannot be fully staffed due to unavailabilities, the solver finds best-effort coverage and flags the gap in stdout and in the output CSV (e.g., a `GAP` marker in the affected team cell).

---

## Objective

Minimize:
- Weighted sum of back-to-back assignment penalties (strong weight)
- Minus weighted sum of preferred-week assignments (soft reward)
- Plus coverage gap penalties (to surface infeasible weeks)

---

## Outputs

Both outputs go to `app/outputs/`.

### `schedule.csv`
- Rows: weeks (one per row, `Week Starting` column)
- Columns: Team A assignments (may be multiple physicians, comma-separated), Team B, Team C
- Gap weeks flagged with `GAP` in the relevant cell

### `schedule.png`
- Matplotlib Gantt chart
- X-axis: weeks (52 weeks of the academic year)
- Y-axis: physicians (Clinician 1–20)
- Color-coded by team: A, B, C (three distinct colors)
- Unassigned weeks shown as blank

---

## Architecture

```
app/
  main.py                          # Entrypoint: load → solve → output
  constraints/
    team_constraints.py            # Team coverage constraints (A min 2, B/C exactly 1)
    physician_constraints.py       # Physician constraints (availability, contract, back-to-back)
  inputs/
    teams.csv
    requests.csv
  outputs/
    schedule.csv                   # Generated
    schedule.png                   # Generated
```

### `app/main.py`
- Parses inputs via pandas
- Instantiates CP-SAT model and solver
- Applies constraints from `constraints/`
- Runs solver
- Writes outputs
- Prints gap warnings to stdout

### `app/constraints/team_constraints.py`
- Team coverage bounds (min/max per team per week)
- Hard team-preference blocks (0 values from teams.csv)

### `app/constraints/physician_constraints.py`
- Availability blocks (-1 values from requests.csv)
- Contract floor (total shifts ≥ contract obligation)
- Back-to-back penalty variables
- Preferred-week reward variables

---

## Key Decisions

- **Contract totals are a floor**, not a ceiling — excess flows to Team A
- **0 in teams.csv is hard** — not a soft preference, a prohibition
- **Back-to-back penalty is strong** — weighted significantly higher than preferred-week rewards
- **Gaps are surfaced, not fatal** — solver continues and flags rather than hard-failing
- **52-week horizon** — academic year 6/30/2025 – 6/22/2026

---

## Open Questions

- What penalty weight ratio should back-to-back violations have vs. preferred-week rewards? (Suggest starting at 10:1, tune from there)
- Should the gap flag in the CSV distinguish which team is understaffed, or just mark the week?
- Is there a solver time limit we should enforce (e.g., 60 seconds) before returning best-found solution?
