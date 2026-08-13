## Context

SVG renderers already accept named color functions, while the classic backend
uses Pillow's word-cloud implementation. Applying new SVG controls to the
classic path would otherwise be a silent no-op. The generator also supports
both direct frequencies and markdown fallback, so output routing and defaults
must agree across both paths.

## Goals / Non-Goals

**Goals:** deterministic color cardinality; one default across entry points;
strict per-call validation; semantic topic/language SVG identity; output-path
containment; explicit backend boundaries.

**Non-Goals:** changing YAML `WordCloudSettingsModel`, creating new tracked
assets, adding renderer aliases, or emulating SVG palette controls in the
classic PNG backend.

## Decisions

1. Use `coarse` as the shared default and cap it at eight tokens; `strong` caps
   at four and `none` preserves continuous interpolation.
2. Treat an explicit `#RRGGBB` list as authoritative interpolation anchors.
3. Keep the controls runtime-only in `WordCloudSettings`; YAML configuration is
   unchanged until a separate persisted-config contract is requested.
4. Reject classic-renderer use of style variants, explicit palettes, custom
   color functions, or non-default tokenization.
5. Validate each override by constructing a temporary strict settings model;
   never mutate the generator's base settings.
6. Allow only a bare `output_filename`; callers use `output_dir` or
   `output_path` for directory selection.

## Risks / Trade-offs

- **Default colors become discretized** -> The default is identical across
  resolver, engine, and generator paths and is covered by cardinality tests.
- **Classic callers cannot use new controls** -> Failing closed is clearer than
  accepting settings that do nothing.
- **SVG root rewrite could disturb rendering** -> Only root attributes change;
  output content and renderer snapshots remain covered.

## Migration Plan

The previous options were unimplemented, so no persisted migration is needed.
Callers that select the classic backend must omit the SVG-only controls.

## Open Questions

None.
