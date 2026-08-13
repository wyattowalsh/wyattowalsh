## ADDED Requirements

### Requirement: Palette tokenization is deterministic
All SVG word-cloud entry points SHALL use the same tokenization default and
SHALL support continuous, coarse, and strong color cardinality policies.

#### Scenario: Shared default
- **WHEN** a caller omits palette tokenization
- **THEN** the resolver, renderer, and generator SHALL all use `coarse`

#### Scenario: Strong tokenization
- **WHEN** forty words use `strong` tokenization
- **THEN** the renderer SHALL emit no more than four palette colors

### Requirement: Per-call style overrides are strict and isolated
The object-oriented generator SHALL validate each override against the strict
runtime settings model and SHALL NOT mutate its base settings.

#### Scenario: Topic and language outputs
- **WHEN** one generator emits topic and language SVGs with separate palettes
- **THEN** each root SHALL have its matching semantic ID and the base settings
  SHALL remain unchanged

#### Scenario: Unknown override
- **WHEN** a caller supplies an unknown setting or malformed color
- **THEN** generation SHALL fail before writing output

### Requirement: Renderer boundaries fail closed
SVG-only style controls SHALL NOT be silently accepted by the classic PNG
renderer.

#### Scenario: Classic style override
- **WHEN** classic generation receives a style variant, explicit palette,
  custom color function, or non-default tokenization
- **THEN** generation SHALL fail with an SVG-renderer requirement

### Requirement: Output routing remains explicit
Markdown fallback SHALL preserve a caller's resolved output target and filename
overrides SHALL be bare filenames.

#### Scenario: Explicit markdown target
- **WHEN** frequencies are loaded from markdown for an explicit output path
- **THEN** the result SHALL be written only to that path
