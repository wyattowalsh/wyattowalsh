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
