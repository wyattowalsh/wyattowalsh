## Context

The skills generator can embed a repo-local SVG as a base64 data logo in a
Shields query. Raw SVG byte size is not the request size: base64 expansion and
percent encoding can push the final URL beyond GitHub/Camo's practical limit.
Shields also accepts unknown `logo` values while silently omitting the image,
so the presence of a query parameter is not proof of a rendered logo.

The catalog now has compact, provenance-recorded local replacements for five
formerly oversized logos and current audited Simple Icons fallbacks for the
remaining oversized entries. The source implementation and focused contracts
are complete; tracked README materialization and remote rendering proof occur
after integration with upstream generated content.

## Goals / Non-Goals

**Goals:** bound every final encoded badge request; preserve local logos when
they fit; use only supported slug fallbacks; emit complete no-logo badges when
necessary; retain compact-logo provenance; prove generated and remote public
surfaces.

**Non-Goals:** shortening labels, truncating URLs or SVG payloads, querying
Simple Icons during normal generation, changing Shields providers, redesigning
the skills taxonomy, or overwriting upstream README generation before merge.

## Decisions

1. Measure the complete percent-encoded Shields request URL and enforce an
   inclusive 4,000-character cap. Raw SVG bytes are diagnostic only.
2. Build candidates in this order: embedded local SVG, audited Simple Icons
   slug, complete base badge without a logo. Return the first complete candidate
   that fits.
3. Treat current slug support as a catalog-time contract backed by a sorted,
   audited fixture. Generation does not add a live network dependency.
4. Never truncate a candidate. If the base badge alone exceeds the cap,
   generation fails with the badge identity and limit.
5. Prefer compact authoritative local assets over visual degradation when their
   source metadata, license, inert SVG content, explicit paint, and encoded
   request all pass. Proxy-contained SVGs cannot rely on inherited
   `currentColor`; monochrome marks use an explicit high-contrast color and
   multicolor marks preserve explicit brand fills.
6. Treat the generated README marker zone and the live GitHub/Camo render as
   separate publication gates. Source-green does not imply either gate is green.

## Risks / Trade-offs

- **A supported slug is later removed** -> The audited fixture and catalog
  contract must be refreshed; unsupported fallbacks cannot be published as
  logo-bearing badges.
- **A local SVG grows after an upstream refresh** -> Final encoded-length tests
  deterministically select a supported fallback and report the transition.
- **A compact alternative changes visual treatment** -> Record exact
  provenance, prohibit inherited paint, and require the local candidate to
  remain embedded, high-contrast, and remotely visible.
- **README regeneration overwrites upstream generated content** -> Regenerate
  only after merge, then compare the entire managed marker zone before push.
- **A locally valid URL still fails remotely** -> Keep the post-push GitHub/Camo
  request and visual audit as a distinct, mandatory acceptance gate.

## Rollout Plan

1. Land the bounded generator, compact assets, audited fallbacks, tests, and
   documentation.
2. Merge upstream generated README content, regenerate the skills zone, and
   prove byte-for-byte parity with the current renderer.
3. Push the integrated result and audit the rendered GitHub profile and Camo
   badge requests; close the change only when no badge request is broken.
