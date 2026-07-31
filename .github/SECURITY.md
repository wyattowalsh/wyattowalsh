# Security Policy

## Supported Versions

This repository is a GitHub profile automation project (not a versioned product release).
Security fixes apply to the default branch (`main`) only.

| Branch | Supported |
| ------ | --------- |
| `main` | :white_check_mark: |
| other  | :x: |

## Reporting a Vulnerability

We take all security bugs in `wyattowalsh` seriously.
Thank you for improving the security of our project. We appreciate your efforts and
responsible disclosure and will make every effort to acknowledge your
contributions.

To report a security vulnerability, please use the [GitHub Security Advisory "Report a Vulnerability" tab](https://github.com/wyattowalsh/wyattowalsh/security/advisories/new).

Alternatively, you can email us at [wyattowalsh@gmail.com](mailto:wyattowalsh@gmail.com).

**Please do not report security vulnerabilities through public GitHub issues.**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

When reporting a vulnerability, please provide the following information:

* A clear description of the vulnerability.
* Steps to reproduce the vulnerability.
* The version(s) of the project affected.
* Any potential impact of the vulnerability.
* If you have a fix, please include it or describe it.

## Disclosure Policy

When the security team receives a security bug report, they will assign it to a
primary handler. This person will coordinate the fix and release process,
involving the following steps:

* Confirm the problem and determine the affected versions.
* Audit code to find any similar problems.
* Prepare fixes for all releases still under maintenance. These fixes will be
  submitted as pull requests to the `main` branch and applied as soon as
  possible.

## GitHub Actions secrets (expected scopes)

> [!IMPORTANT]
> Document **names and required scopes only**. Never commit token values, paste
> secrets into issues/PRs, or check `.env` files into git.

Configure repository secrets under **Settings → Secrets and variables → Actions**.
Prefer **fine-grained personal access tokens** over classic PATs when GitHub
supports the needed permissions. Rotate tokens periodically and revoke unused ones.

### `METRICS_TOKEN`

Used by `.github/workflows/profile-updater.yml` for GitHub metrics / GraphQL reads
(and as the metrics action token when present).

| Token type | Minimum scopes / permissions |
| ---------- | ---------------------------- |
| Fine-grained PAT | Repository access for this profile repo (and any private repos you want reflected): **Metadata: Read**, **Contents: Read**. Account permissions: **Profile: Read**. Add **Organization membership / members: Read** only if you need org/collab visibility. |
| Classic PAT (fallback) | `read:user`, `public_repo` (add `read:org` when org/collab visibility is required). |

Do not grant write, admin, or workflow scopes to `METRICS_TOKEN`.

### `GH_TOKEN`

Used by the WakaTime README stats job (`anmol098/waka-readme-stats`) to push
generated README section updates.

| Token type | Minimum scopes / permissions |
| ---------- | ---------------------------- |
| Fine-grained PAT | This repository only: **Contents: Read and write**, **Metadata: Read**. |
| Classic PAT (fallback) | `public_repo` (or `repo` if the repository is private). |

Do not reuse a broad org-admin or `workflow`-scoped token for `GH_TOKEN`.

### Other Actions secrets (names only)

These secrets are optional feature gates in the profile updater workflow. Store
them as Actions secrets; do not document or paste values here:

| Secret | Purpose (high level) |
| ------ | -------------------- |
| `WAKATIME_API_KEY` | WakaTime API auth for coding-stats README sections |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | First-party repo-owned `metrics-music.svg` supplemental card only |
| `X_API_KEY` / `X_API_KEY_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | First-party repo-owned `metrics-posts.svg` supplemental card only |

Built-in `GITHUB_TOKEN` is provided by Actions with job-level `permissions`; it
is not a repository secret you create.

### Third-party Actions and secret policy

> [!IMPORTANT]
> **Never** pass PATs, Spotify credentials (especially refresh tokens), X OAuth
> secrets, or other broad/long-lived secrets into third-party Actions via
> `with:` inputs. That includes `lowlighter/metrics`, metrics forks (for example
> `felipecrs/metrics`), music plugins (`plugin_music_token`, and similar), and
> any other community Action that is not this repository’s own `run:` scripts.

Prefer **fine-grained PATs** with the minimum read/write surface documented
above. Prefer pinning third-party Actions to full commit SHAs.

#### First-party vs third-party secret ownership

| Secret | Belongs to | Allowed delivery | Do not |
| ------ | ---------- | ---------------- | ------ |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | **First-party only** | `env:` on repo-owned `run:` steps (for example `uv run … generate supplemental-metrics`) | Pass into any third-party Action `with:` (metrics music plugins, forks, etc.) |
| `X_API_KEY` / `X_API_KEY_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | **First-party only** | `env:` on repo-owned supplemental-metrics steps | Pass into third-party Action `with:` |
| `METRICS_TOKEN` | Shared (narrow GitHub read) | First-party `env:` for GraphQL collectors; third-party metrics `token:` only when a read-scoped PAT is required | Grant write/admin/workflow scopes; reuse as a catch-all PAT |
| `GH_TOKEN` | Third-party WakaTime job | `anmol098/waka-readme-stats` `with: GH_TOKEN` only (contents write for this repo) | Reuse org-admin / `workflow` tokens; pass to metrics Actions |
| `WAKATIME_API_KEY` | Third-party WakaTime job | `anmol098/waka-readme-stats` `with: WAKATIME_API_KEY` only | Pass to metrics or unrelated Actions |
| `GITHUB_TOKEN` | Built-in | Job `permissions` + first-party `env:` / metrics `committer_token` as needed | Substitute for Spotify/X secrets or broad PATs |

#### Explicit: no Spotify on lowlighter metrics

**Never** supply Spotify client ID, client secret, or refresh token to
`lowlighter/metrics` (or any metrics fork) through `with:` inputs such as
`plugin_music_token`, plugin env bridges, or composite secret strings.

Music / recently-played cards must be generated by **first-party** code
(`scripts/supplemental_metrics.py` / `readme generate supplemental-metrics`)
using Spotify secrets only as step `env:` values on those `run:` steps.

Scheduled `generate-profile-metrics` and the manual `probe-full-metrics` lane both keep
`plugin_music: no` on every `lowlighter/metrics` step and never pass Spotify credentials
via Action `with:` inputs. Spotify belongs on the first-party supplemental-metrics
`run:` step only (`env:` delivery).

## Comments on this Policy

If you have any suggestions for how this policy could be improved, please submit a pull request or open an issue to discuss.
