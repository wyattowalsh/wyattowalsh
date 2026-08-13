## Why

Embedded badge logos can expand substantially after base64 and percent
encoding. Several generated Shields source URLs exceeded the practical request
budget used by GitHub's Camo proxy, and stale Simple Icons slugs could return a
successful badge response without rendering a logo. The public README needs a
deterministic, testable delivery contract that bounds every request without
silently damaging badge URLs or visual identity.

## What Changes

- Cap every final percent-encoded Shields source URL at 4,000 characters.
- Prefer repo-local SVG logos only when their complete encoded URL fits.
- Fall back to a current, audited Simple Icons slug, then to a complete no-logo
  badge when no supported slug is available.
- Never truncate a URL; fail when even the complete base badge cannot fit.
- Use compact local alternatives with explicit source, source URL, license, and
  style provenance when they preserve a logo within the cap.
- Require proxy-contained SVG logos to use explicit paint rather than inherited
  `currentColor`, which Shields may render with unreadable contrast.
- Require the tracked README skills zone to equal the current generated output
  and require a post-publication GitHub/Camo visual audit with no broken badge
  requests.

## Capabilities

### New Capabilities

- `badge-proxy-safety`: Bounded, renderable Shields badge delivery with
  deterministic fallback, auditable local logos, generated README parity, and
  remote rendering assurance.

### Modified Capabilities

None. This repository did not previously have an OpenSpec capability for
profile badge delivery.

## Impact

Affected surfaces are `scripts/skills.py`, `skills.yaml`, repo-local skill SVGs,
the audited Simple Icons slug fixture, focused badge tests, badge documentation,
and the generated skills zone in `README.md`. The contract does not add a
runtime network dependency or change the existing Shields service, README
markers, category structure, or sole-writer workflow.
