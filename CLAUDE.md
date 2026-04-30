# CLAUDE.md

This is a python based command line application that produces clinical schedules. It leverages Google's CP-SAT solver to find optimal scheduling solutions for hospital systems that need to balance clinician and institutional constraints.

## Language & Style

- Python 3.12+ and common supporting libraries.
- Keep files simple and readable.

## Commands
- \`python -m app.main\` — Execute the scheduling workflow

## Architecture

- \`app/main.py\` — Command line entrypoint to produce the schedule. 
- \`app/constraints/\` — Directory for CP-SAT constraint definitions. 
- \`app/inputs/\` — Input spreadsheet directory.
- \`app/outputs/\` — Output schedule directory.

## Conventions
- Use pandas for all spreadsheet manipulation
