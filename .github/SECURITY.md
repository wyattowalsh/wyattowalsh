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
and as the `lowlighter/metrics` `token:` input when present. Prefer a
**fine-grained PAT** with read-only surface; keep classic PATs as fallback only.

| Token type | Minimum scopes / permissions |
| ---------- | ---------------------------- |
| Fine-grained PAT (preferred) | Repository access for this profile repo (and any private repos you want reflected): **Metadata: Read**, **Contents: Read**. Account permissions: **Profile: Read**. Add **Organization membership / members: Read** only if you need org/collab visibility. |
| Classic PAT (fallback) | `read:user`, `public_repo` (add `read:org` when org/collab visibility is required). |

Do not grant write, admin, or workflow scopes to `METRICS_TOKEN`. Do not reuse it
as a catch-all Actions secret, and never pass Spotify / X credentials into
third-party metrics Actions (`lowlighter/metrics` or forks such as
`felipecrs/metrics` — this workflow pins `lowlighter/metrics` only).

### `GH_TOKEN`

> [!NOTE]
> **Retired for WakaTime.** The third-party `anmol098/waka-readme-stats` Action
> was removed. Waka README updates are first-party (`scripts/wakatime_readme.py`)
> and committed only by the workflow `finalize` job via built-in `GITHUB_TOKEN`.
> `GH_TOKEN` is no longer required for the profile updater. If the secret still
> exists in the repository, rotate/delete it when convenient — do not pass it
> into any Action `with:` inputs.

### Other Actions secrets (names only)

These secrets are optional feature gates in the profile updater workflow. Store
them as Actions secrets; do not document or paste values here:

| Secret | Purpose (high level) |
| ------ | -------------------- |
| `WAKATIME_API_KEY` | First-party WakaTime API auth for the README `<!--START_SECTION:waka-->` zone (`env:` on `generate wakatime` only) |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | First-party repo-owned `metrics-music.svg` supplemental card only |
| `X_API_KEY` / `X_API_KEY_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | First-party repo-owned `metrics-posts.svg` supplemental card only |

Built-in `GITHUB_TOKEN` is provided by Actions with job-level `permissions`; it
is not a repository secret you create.

### Third-party Actions and secret policy

> [!IMPORTANT]
> **Never** pass PATs, Spotify credentials (especially refresh tokens), X OAuth
> secrets, WakaTime API keys, or other broad/long-lived secrets into third-party
> Actions via `with:` inputs. That includes `lowlighter/metrics`, metrics forks
> (for example `felipecrs/metrics`), music plugins (`plugin_music_token`, and
> similar), retired Waka Actions such as `anmol098/waka-readme-stats`, and any
> other community Action that is not this repository’s own `run:` scripts.

Prefer **fine-grained PATs** with the minimum read/write surface documented
above. Prefer pinning third-party Actions to full commit SHAs.

#### First-party vs third-party secret ownership

| Secret | Belongs to | Allowed delivery | Do not |
| ------ | ---------- | ---------------- | ------ |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | **First-party only** | `env:` on repo-owned `run:` steps (for example `uv run … generate supplemental-metrics`) | Pass into any third-party Action `with:` (metrics music plugins, forks, etc.) |
| `X_API_KEY` / `X_API_KEY_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | **First-party only** | `env:` on repo-owned supplemental-metrics steps | Pass into third-party Action `with:` |
| `METRICS_TOKEN` | Shared (narrow GitHub read) | First-party `env:` for GraphQL collectors; third-party metrics `token:` only when a read-scoped PAT is required | Grant write/admin/workflow scopes; reuse as a catch-all PAT |
| `WAKATIME_API_KEY` | **First-party only** | `env:` on repo-owned `generate wakatime` / `scripts.wakatime_readme` steps | Pass into any third-party Action `with:` (including retired `anmol098/waka-readme-stats`) |
| `GH_TOKEN` | **Retired** | Not used by the profile updater | Reintroduce for third-party Waka writers; pass to metrics Actions |
| `GITHUB_TOKEN` | Built-in | Job `permissions` + first-party `env:` / metrics `committer_token` / finalize push as needed | Substitute for Spotify/X/WakaTime secrets or broad PATs |

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
