# Goal — living-art-overhaul

Redesign the living artworks and the Living Art README section so each shipped piece is a striking, data-informed timelapse with a learnable explanation. Success is the origin/`dev` profile README.

## Shared understanding

Accepted facts: [`facts.md`](./facts.md)  
Grill: [`grill-notes.md`](./grill-notes.md)

## Execution plan

Plannotator-approved plan: [`plan.md`](./plan.md)  
Machine graph: [`task-graph.json`](./task-graph.json) (v3, 107 nodes)

## Done when

- Every accepted fact in `facts.md` holds on the origin/`dev` README preview.
- The section is a 4–6 piece full-width stack: clock intro, visible art, per-piece `<details>` legend.
- Native README video was checked on github.com; the ship form is either playing `<video>` or GIF + in-repo MP4 click-through. No external host.
- A scored bake-off (`bakeoff.json`) named the shipped 4–6 and you accepted or overrode it.
- After that, daily CI, tests, and `living-art-modes` follow only the shipped roster.
- Facts marked `automatedVerification: true` have concrete checks.
- `main` is unchanged by this goal.

Launch with `/goal goals/living-art-overhaul/goal.md`
