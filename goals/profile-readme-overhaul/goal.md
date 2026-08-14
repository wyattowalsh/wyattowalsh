# Goal — profile-readme-overhaul

Overhaul the GitHub profile README as a designed surface: maximal data in a visual hierarchy, previewed on origin/`dev` only until the maintainer asks to touch `main`.

## Shared understanding

Accepted facts: [`facts.md`](./facts.md)

## Execution plan

Plannotator-approved plan: [`plan.md`](./plan.md)  
Machine graph: [`task-graph.json`](./task-graph.json)

## Done when

- Every accepted fact in `facts.md` holds on the origin/`dev` README preview.
- Facts marked `automatedVerification: true` have concrete checks (tests, workflow asserts, hashes, or render QA).
- `main` is unchanged by this goal unless the maintainer later asks.

Launch with `/goal goals/profile-readme-overhaul/goal.md`
