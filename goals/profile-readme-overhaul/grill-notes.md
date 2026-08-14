# Grill notes — profile-readme-overhaul

## Resolved

- **Density:** Maximal data, designed hierarchy. Enable every cool signal we can get (long windows, all-time where it works). Compose it: primary cards first, dense detail second. First-party widgets stay visually striking, not a dump.
- **Banner:** Reuse the exact remote `main` light/dark banner artifacts; do not regenerate the header as part of this goal.
- **Remove:** GitHub-feed / recent-activity widget (`metrics-activity.svg`); “200+ technologies” copy.
- **Word clouds:** Two clouds — starred topics and starred languages — sized by volume of starred repos.
- **WakaTime:** First-party SVG (not anmol098); show all shareable data.
- **Spotify:** Stays off lowlighter; first-party music widget is redesigned.

- **Habits ownership:** Both. Redesign first-party `metrics-habits.svg` *and* enable lowlighter `plugin_habits` on the production primary card.

- **Habits split:** By job. Lowlighter habits = all of its native facts/charts/languages. First-party habits = everything else it does poorly (focus repos, peak hour, designed streaks, richer layout). Not a restyle of the same recap.

- **Lowlighter maximality:** Every GitHub-native plugin that can render cleanly. Raise windows/limits (calendar toward all years, language threshold 0, more topics/stars/people). `habits` on. Retry `lines` / `achievements` / `gists` only if isolated clean. Keep `music`, `tweets`, and `activity` off.

- **WakaTime privacy:** Public-safe maximal. Include languages, professional editors, OS/device mix (Mac / iOS / watch), coding categories, weekly + yearly + all-time totals, heatmap if the API allows. Project names only when they match a public repo (or an allowlist). No file paths, heartbeats, private-project names, or leisure/social/health/shopping/entertainment app rows. Nothing embarrassing or unprofessional.

- **Living art:** One shared daily spine from account creation → now. Six visual dialects; each style may use the encoding that best depicts that day’s cumulative evolution (not six different clocks). Frame-inspect and redesign until accretion is readable.

- **Shipping:** `dev` only. Success is the origin/`dev` README preview. Do not change `main` until explicitly asked.

- **Badges:** Finish the existing skills system (homepage link + GitHub-camo render QA + retro/throwback icons when they still read). Use the best modern badge stack that still renders on github.com — shields.io is not sacred; adopt shieldscn / simple-icons / first-party SVG where they win.

- **Word clouds:** Bake-off. Topics + langs through existing SVG engines plus a new candidate if none encode star volume well. Score on volume fidelity, GitHub readability, dark/light, and interest. Ship exactly two clouds.

- **Spotify:** Hero + compact extras. Striking recent-listens art object, then a small row of extra listen signals only if they stay beautiful.

- **Blog posts:** Visible designed strip. Still RSS from w4w.dev, 4–5 latest cards with date + one-line hook. Not hidden in `<details>`.

- **View counter:** Restyle the existing incrementer (komarev or equivalent) to match the new footer/badge look. First-party backend only if an existing host makes it trivial; do not stand up new infra for this item.

- **Visibility:** Waka SVG is visible with the other metric cards. Tech stack stays in `<details>`. The `<summary>` has no count and no “honest summary” copy (not “200+ technologies”, not a replacement blurb).

## Open

- None that block facts. Remaining choices (exact badge engine, cloud bake-off winner, per-style living-art encoding, first-party view backend) are implementation spikes under the locks above.
