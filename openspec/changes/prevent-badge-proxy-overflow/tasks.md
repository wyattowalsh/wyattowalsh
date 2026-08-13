## 1. Bounded Badge Generation

- [x] 1.1 Enforce the inclusive 4,000-character cap on final percent-encoded Shields source URLs
- [x] 1.2 Prefer fitting local SVGs, then supported slugs, then complete no-logo badges
- [x] 1.3 Fail instead of truncating when even the complete base badge exceeds the cap
- [x] 1.4 Replace oversized local logos with compact authoritative alternatives and record provenance

## 2. Contracts and Documentation

- [x] 2.1 Cover encoded-length boundaries, fallback order, complete no-logo output, and non-warning fallback logging
- [x] 2.2 Audit every emitted slug against the sorted current Simple Icons fixture
- [x] 2.3 Require compact local replacements to remain embedded with their exact source and license metadata
- [x] 2.4 Reject inherited `currentColor` paint and require explicit high-contrast compact-logo paint
- [x] 2.5 Run focused pytest, Ruff check/format, ty, and diff validation
- [x] 2.6 Document the public URL budget, fallback policy, provenance fields, settings defaults, and managed markers

## 3. Publication Assurance

- [ ] 3.1 After merging upstream generated content, regenerate `README.md` and prove the full skills marker zone matches the current renderer
- [ ] 3.2 After push, audit the rendered GitHub profile and Camo requests and confirm that every badge loads without a broken request or missing intended logo
