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
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | Spotify music metrics plugins |
| `X_API_KEY` / `X_API_KEY_SECRET` / `X_ACCESS_TOKEN` / `X_ACCESS_TOKEN_SECRET` | X (Twitter) OAuth 1.0a for latest-posts metrics |

Built-in `GITHUB_TOKEN` is provided by Actions with job-level `permissions`; it
is not a repository secret you create.

### Third-party Actions and secret policy

Third-party Actions (for example metrics or WakaTime) receive only the secrets
those jobs explicitly pass. Prefer pinning Actions to full commit SHAs.
Deeper third-party action allowlisting / secret-handling policy is maintained
separately (fleet leaf B6); this document covers expected secret **scopes** only.

## Comments on this Policy

If you have any suggestions for how this policy could be improved, please submit a pull request or open an issue to discuss.
