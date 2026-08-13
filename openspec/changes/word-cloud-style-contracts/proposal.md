## Why

Two strict-xfail contracts documented requested word-cloud palette tokenization
and topic-versus-language style variants, but the runtime exposed neither
behavior. Ad hoc per-call overrides also needed validation so creative controls
could not be silently ignored or leak output outside the requested target.

## What Changes

- Add deterministic `none`, `coarse`, and `strong` palette-tokenization modes.
- Add validated explicit palette and registered color-function overrides.
- Add semantic topic/language IDs to SVG roots.
- Validate per-call settings without mutating the generator's base settings.
- Reject SVG-only controls for the classic PNG renderer.
- Preserve explicit output targets through markdown fallback generation.

## Capabilities

### New Capabilities

- `word-cloud-style-contracts`: Deterministic palette and semantic SVG output
  behavior across direct and object-oriented entry points.

### Modified Capabilities

None. This repository did not previously have a word-cloud capability document.

## Impact

Affected surfaces are `scripts/word_clouds/`, its dedicated contracts, and the
word-cloud developer documentation. Existing default CLI output names and
tracked word-cloud assets remain unchanged.
