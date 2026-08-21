# Living Art README video check

- URL: https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md
- Branch: origin/dev
- Date: 2026-08-20
- Logged-in vs logged-out: logged-out (header Sign in / Sign up; `user-login` meta empty). Desktop blob Preview only; no logged-in session available.
- Desktop vs mobile (if checked): desktop (Playwright viewport). Mobile not checked.
- Markup tried: (paste <video> …)

```html
<video src=".github/assets/img/living-inkgarden.mp4" width="100%" autoplay muted loop playsinline poster=".github/assets/img/living-inkgarden.gif">
<a href=".github/assets/img/living-inkgarden.mp4"><img src=".github/assets/img/living-inkgarden.gif" alt="Ink Garden" width="100%" loading="lazy"/></a>
</video>
```

Same pattern for `living-topo`, `living-genetic`, `living-physarum`, `living-lenia`, `living-ferrofluid`. Full-width stack: intro, `width="100%"`, art outside `<details>`, one `<details>` per piece. Confirmed in blob **Code** view (six `<video>` tags). README file commit on this blob: `ed5dce9` (`feat(readme): present Living Art as a full-width stack`).
- DOM after GitHub render: video present? / stripped? **stripped** — Preview `article.markdown-body` has **0** `<video>` elements (`document.querySelectorAll('video').length === 0`). GitHub removes the entire `<video>` node, including the inner GIF+href fallback. Six empty `<p align="center" dir="auto"></p>` remain, then the six `<details>` titles.
- Autoplay (muted loop): **no** (no player in the rendered DOM)
- Play: no
- Strip: yes
- No-autoplay: n/a (tag never reached the rendered DOM)
- Play / strip / no-autoplay: **strip**
- Decision: gif-fallback
- External hosts present: none (required). Living Art `src`/`href` in source are relative `.github/assets/img/living-*.{gif,mp4}` only. Rendered Living Art HTML has no youtube / cloudinary / user-attachments / iframe / vimeo.
- Screenshot note: Preview tab, logged-out desktop, `blob/dev/README.md` (not the profile overview). After the Living Art separator and intro, the six films are blank gaps; Ink Garden / Topography / Genetic Landscape / Physarum / Lenia / Ferrofluid `<details>` still show. Inner GIF is **not** visible after strip. Code tab still shows the six `<video>` source tags — that is source, not rendered play.

## Post-regen Preview

Smoke only (art visible vs empty slots). Not CAP C3. Decision remains **gif-fallback**.

- When: 2026-08-20, logged-out desktop Playwright, blob **Preview** (pressed), not profile overview / Issues.
- README commit on the blob: `cac367b` (`feat(readme): ship Living Art as gif-fallback`). CDN matched; no stale `ed5dce9` video markup.
- **PASS.** Six art slots show GIFs. Zero empty `<p align="center">` in the Living Art section (the prior strip failure mode).
- Visible living-art `<img>` GIFs: **6** (Ink Garden, Topography, Genetic Landscape, Physarum, Lenia, Ferrofluid). GitHub wraps each in `<animated-image style="width: 100%">`; painted size **1006×1006** = 100% of `article.markdown-body` (full-width). Duplicate hidden player `<img>` copies exist in the DOM (12 nodes total) and were not counted as extra slots.
- `Watch … (MP4)` links: **6**. Rendered `<video>`: **0**.
- `<details>`: **6** living-art titles (art **outside** details). Article also has one Tech Stack `<details>` (7 total) — out of scope.
- External hosts: none (no YouTube / Cloudinary / user-attachments / iframe / vimeo in Living Art HTML). GIF `src` is repo `raw/dev/.github/assets/img/living-*.gif`; MP4 `href` is blob `living-*.mp4`.

## Preview smoke 2026-08-21

Smoke only (art visible vs empty slots). Not CAP C3. Decision remains **gif-fallback**. No `accepted[]`.

- When: 2026-08-21, logged-out desktop Playwright, blob **Preview** (pressed), `https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md` (not profile overview).
- README commit on the blob: `6738308` (`chore(readme): update dynamic sections and skills badges`). Prior note (`2026-08-20` / `cac367b`) is stale.
- **PASS.** gif-fallback still shows.

| Check | Count / result |
|---|---|
| Visible full-width living-art GIFs | **6** (Ink Garden, Topography, Genetic Landscape, Physarum, Lenia, Ferrofluid). Painted **766×766** = 100% of `article` (766px). GitHub `<animated-image>` still adds hidden player copies (12 GIF nodes total); counted 6 visible slots. |
| `Watch … (MP4)` links | **6** |
| Rendered `<video>` | **0** |
| Living-art `<details>` | **6** (art **outside** details; each details imgCount=0) |
| Empty center slots | **0** (no empty `<p align="center">`) |
| YouTube / Cloudinary | **0** (also no iframe / user-attachments / vimeo in Living Art HTML) |
