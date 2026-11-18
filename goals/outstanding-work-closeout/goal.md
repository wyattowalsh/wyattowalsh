# Goal — outstanding-work-closeout

Close and prove the outstanding profile-repo work on `dev`: reconcile the dirty tree, fail closed on required surfaces, correct false docs, and land a cleaned dependency bump. Push `dev` and close Dependabot PRs #12 and #14. Leave `main` and the default branch unchanged.

Shared understanding: [`facts.md`](./facts.md)

Execution plan: [`plan.md`](./plan.md)

## Done when

- Every accepted fact in `facts.md` holds.
- Facts marked for automated verification have a concrete test or file check.
- The human gates in `fact-human-gates` are still open: the classic PAT is untouched, `bakeoff.json` has no `accepted` key, OpenSpec tasks 5.1–5.4, 3.2, and 9.5 are unchecked, and the Actions billing lock was not cleared from this goal.
- `dev` is pushed and PRs #12 and #14 are closed. `main` has no new commits from this goal.

Launch with `/goal goals/outstanding-work-closeout/goal.md`
