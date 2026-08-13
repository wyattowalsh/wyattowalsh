## ADDED Requirements

### Requirement: Every Shields source URL has a post-encoding budget
Every emitted Shields source URL SHALL be measured after label, query, base64,
and percent encoding and SHALL contain no more than 4,000 characters.

#### Scenario: Encoded local logo fits
- **WHEN** a repo-local SVG produces a complete encoded source URL of 4,000 characters or fewer
- **THEN** the generator SHALL emit that complete embedded-logo URL

#### Scenario: Raw asset appears small but encoded URL exceeds the cap
- **WHEN** base64 and percent encoding expand a local SVG candidate beyond 4,000 characters
- **THEN** the generator SHALL reject that embedded candidate and continue through the fallback policy

### Requirement: Badge logo fallback is deterministic and renderable
The generator SHALL prefer a fitting repo-local SVG, then a configured current
Simple Icons slug that is present in the audited catalog, then a complete badge
without a logo.

#### Scenario: Oversized local logo has a supported slug
- **WHEN** a local SVG candidate exceeds the cap and its configured slug is present in the current audited Simple Icons inventory
- **THEN** the emitted URL SHALL use that slug and remain within the cap

#### Scenario: No supported slug is available
- **WHEN** a local SVG is unreadable or oversized and the entry has no supported configured slug
- **THEN** the generator SHALL emit the complete base badge URL without any logo parameter

#### Scenario: Catalog contains an unsupported slug fallback
- **WHEN** an emitted slug is absent from the audited current Simple Icons inventory
- **THEN** catalog validation SHALL fail before README publication

### Requirement: Badge URLs are never truncated
The generator SHALL preserve the complete syntax and encoded value of every
selected candidate and SHALL NOT shorten, slice, or partially emit a badge URL.

#### Scenario: Slug candidate exceeds the cap but the base badge fits
- **WHEN** adding a supported slug would exceed 4,000 characters and the complete base badge fits
- **THEN** the generator SHALL emit the complete no-logo base badge

#### Scenario: Base badge exceeds the cap
- **WHEN** the complete badge without any logo parameter exceeds 4,000 characters
- **THEN** generation SHALL fail with the badge identity and limit instead of emitting a truncated URL

### Requirement: Compact local alternatives have auditable provenance
Every compact local SVG introduced to keep a badge logo within the cap SHALL be
self-contained, inert, and accompanied by its source collection, canonical
source URL, license, and style classification. A proxy-contained SVG SHALL NOT
depend on inherited `currentColor`; monochrome compact marks SHALL declare an
explicit high-contrast paint and multicolor marks SHALL retain explicit brand
fills.

#### Scenario: Compact authoritative alternative is selected
- **WHEN** an authoritative compact SVG replaces an oversized local logo
- **THEN** its catalog entry SHALL record complete provenance and its final encoded badge URL SHALL retain the embedded logo within the cap

#### Scenario: Local asset safety audit
- **WHEN** catalog validation inspects a repo-local badge SVG
- **THEN** the asset SHALL contain SVG markup and SHALL NOT contain scripts, JavaScript URLs, external HTTP references, embedded raster images, or inherited `currentColor` paint

#### Scenario: Compact logo paint inside the Shields proxy
- **WHEN** a compact local logo is embedded as a Shields data URI
- **THEN** every monochrome path or stroke SHALL use an explicit high-contrast paint and every multicolor brand mark SHALL use explicit fills

### Requirement: Generated and published badge surfaces are verified
The tracked README skills marker zone SHALL match the current generator output,
and the published GitHub profile SHALL render every badge through GitHub/Camo
without a broken request or an unintentionally missing logo.

#### Scenario: README regeneration after integration
- **WHEN** upstream generated content has been merged and skills generation completes
- **THEN** the entire tracked skills marker zone SHALL be byte-for-byte equivalent to the current rendered skills section

#### Scenario: Post-push public audit
- **WHEN** the integrated README is pushed and GitHub/Camo has rendered its badges
- **THEN** every badge request SHALL load successfully and every badge intended to carry a logo SHALL visibly contain one
