This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository informatio
4. Repository files (if enabled)
4. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: docs/**/*.md
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
docs/
  _media/
    example-with-yaml.md
    example.md
  _coverpage.md
  _navbar.md
  _sidebar.md
  adding-pages.md
  cdn.md
  configuration.md
  cover.md
  custom-navbar.md
  deploy.md
  embed-files.md
  emoji.md
  helpers.md
  language-highlight.md
  markdown.md
  plugins.md
  pwa.md
  quickstart.md
  README.md
  themes.md
  ui-kit.md
  vue.md
  write-a-plugin.md
```

# Files

## File: docs/_media/example-with-yaml.md
`````markdown
---
author: John Smith
date: 2020-1-1
---

> This is from the `example-with-yaml.md`
`````

## File: docs/_media/example.md
`````markdown
> This is from the `example.md`
`````

## File: docs/_coverpage.md
`````markdown
<!-- markdownlint-disable first-line-h1 -->

![logo](_media/icon.svg)

# docsify <small>4.13.1</small>

> A magical documentation site generator

- Simple and lightweight
- No statically built HTML files
- Multiple themes

[Get Started](#docsify)
[GitHub](https://github.com/docsifyjs/docsify/)

<!-- ![color](#f0f0f0) -->
<!-- ![](/_media/icon.svg) -->
`````

## File: docs/_navbar.md
`````markdown
<!-- markdownlint-disable first-line-h1 -->

- Translations

  - [English](/)
  - [简体中文](/zh-cn/)
`````

## File: docs/_sidebar.md
`````markdown
<!-- markdownlint-disable first-line-h1 -->

- Getting started

  - [Quick start](quickstart.md)
  - [Adding pages](adding-pages.md)
  - [Cover page](cover.md)
  - [Custom navbar](custom-navbar.md)

- Customization

  - [Configuration](configuration.md)
  - [Themes](themes.md)
  - [List of Plugins](plugins.md)
  - [Write a Plugin](write-a-plugin.md)
  - [Markdown configuration](markdown.md)
  - [Language highlighting](language-highlight.md)
  - [Emoji](emoji.md)

- Guide

  - [Deploy](deploy.md)
  - [Helpers](helpers.md)
  - [Vue compatibility](vue.md)
  - [CDN](cdn.md)
  - [Offline Mode (PWA)](pwa.md)
  - [Embed Files](embed-files.md)
  - [UI Kit](ui-kit.md)

- [Awesome docsify](awesome.md)
- [Changelog](changelog.md)
`````

## File: docs/adding-pages.md
`````markdown
# Adding pages

If you need more pages, you can simply create more markdown files in your docsify directory. If you create a file named `guide.md`, then it is accessible via `/#/guide`.

For example, the directory structure is as follows:

```text
.
└── docs
    ├── README.md
    ├── guide.md
    └── zh-cn
        ├── README.md
        └── guide.md
```

Matching routes

```text
docs/README.md        => http://domain.com
docs/guide.md         => http://domain.com/#/guide
docs/zh-cn/README.md  => http://domain.com/#/zh-cn/
docs/zh-cn/guide.md   => http://domain.com/#/zh-cn/guide
```

## Sidebar

In order to have a sidebar, you can create your own `_sidebar.md` (see [this documentation's sidebar](https://github.com/docsifyjs/docsify/blob/main/docs/_sidebar.md) for an example):

First, you need to set `loadSidebar` to **true**. Details are available in the [configuration paragraph](configuration#loadsidebar).

```html
<!-- index.html -->

<script>
  window.$docsify = {
    loadSidebar: true,
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
```

Create the `_sidebar.md`:

```markdown
<!-- docs/_sidebar.md -->

- [Home](/)
- [Page 1](page-1.md)
```

To create section headers:

```markdown
<!-- docs/_sidebar.md -->

- Section Header 1

  - [Home](/)
  - [Page 1](page-1.md)

- Section Header 2

  - [Page 2](page-2.md)
  - [Page 3](page-3.md)
```

You need to create a `.nojekyll` in `./docs` to prevent GitHub Pages from ignoring files that begin with an underscore.

!> Docsify only looks for `_sidebar.md` in the current folder, and uses that, otherwise it falls back to the one configured using `window.$docsify.loadSidebar` config.

Example file structure:

```text
└── docs/
    ├── _sidebar.md
    ├── index.md
    ├── getting-started.md
    └── running-services.md
```

## Nested Sidebars

You may want the sidebar to update after navigation to reflect the current directory. This can be done by adding a `_sidebar.md` file to each folder.

`_sidebar.md` is loaded from each level directory. If the current directory doesn't have `_sidebar.md`, it will fall back to the parent directory. If, for example, the current path is `/guide/quick-start`, the `_sidebar.md` will be loaded from `/guide/_sidebar.md`.

You can specify `alias` to avoid unnecessary fallback.

```html
<script>
  window.$docsify = {
    loadSidebar: true,
    alias: {
      '/.*/_sidebar.md': '/_sidebar.md',
    },
  };
</script>
```

!> You can create a `README.md` file in a subdirectory to use it as the landing page for the route.

## Set Page Titles from Sidebar Selection

A page's `title` tag is generated from the _selected_ sidebar item name. For better SEO, you can customize the title by specifying a string after the filename.

```markdown
<!-- docs/_sidebar.md -->

- [Home](/)
- [Guide](guide.md 'The greatest guide in the world')
```

## Table of Contents

Once you've created `_sidebar.md`, the sidebar content is automatically generated based on the headers in the markdown files.

A custom sidebar can also automatically generate a table of contents by setting a `subMaxLevel`, compare [subMaxLevel configuration](configuration#submaxlevel).

```html
<!-- index.html -->

<script>
  window.$docsify = {
    loadSidebar: true,
    subMaxLevel: 2,
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
```

## Ignoring Subheaders

When `subMaxLevel` is set, each header is automatically added to the table of contents by default. If you want to ignore a specific header, add `<!-- {docsify-ignore} -->` to it.

```markdown
# Getting Started

## Header <!-- {docsify-ignore} -->

This header won't appear in the sidebar table of contents.
```

To ignore all headers on a specific page, you can use `<!-- {docsify-ignore-all} -->` on the first header of the page.

```markdown
# Getting Started <!-- {docsify-ignore-all} -->

## Header

This header won't appear in the sidebar table of contents.
```

Both `<!-- {docsify-ignore} -->` and `<!-- {docsify-ignore-all} -->` will not be rendered on the page when used.

And the `{docsify-ignore}` and `{docsify-ignore-all}` can do the samething as well.
`````

## File: docs/cdn.md
`````markdown
# CDN

The docsify [npm package](https://www.npmjs.com/package/docsify) is auto-published to CDNs with each release. The contents can be viewed on each CDN.

Docsify recommends [jsDelivr](//cdn.jsdelivr.net) as its preferred CDN:

- https://cdn.jsdelivr.net/npm/docsify/

Other CDNs are available and may be required in locations where jsDelivr is not available:

- https://cdnjs.com/libraries/docsify
- https://unpkg.com/browse/docsify/
- https://www.bootcdn.cn/docsify/

## Specifying versions

Note the `@` version lock in the CDN URLs below. This allows specifying the latest major, minor, patch, or specific [semver](https://semver.org) version number.

- MAJOR versions include breaking changes<br>
  `1.0.0` → `2.0.0`
- MINOR versions include non-breaking new functionality<br>
  `1.0.0` → `1.1.0`
- PATCH versions include non-breaking bug fixes<br>
  `1.0.0` → `1.0.1`

Uncompressed resources are available by omitting the `.min` from the filename.

## Latest "major" version

Specifying the latest major version allows your site to receive all non-breaking enhancements ("minor" updates) and bug fixes ("patch" updates) as they are released. This is good option for those who prefer a zero-maintenance way of keeping their site up to date with minimal risk as new versions are published.

?> When a new major version is released, you will need to manually update the major version number after the `@` symbol in your CDN URLs.

<!-- prettier-ignore -->
```html
<!-- Theme -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/themes/vue.min.css" />

<!-- Docsify -->
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
```

## Specific version

Specifying an exact version prevents any future updates from affecting your site. This is good option for those who prefer to manually update their resources as new versions are published.

?> When a new version is released, you will need to manually update the version number after the `@` symbol in your CDN URLs.

<!-- prettier-ignore -->
```html
<!-- Theme -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5.0.0/themes/vue.min.css" />

<!-- Docsify -->
<script src="//cdn.jsdelivr.net/npm/docsify@5.0.0/dist/docsify.min.js"></script>
```
`````

## File: docs/configuration.md
`````markdown
# Configuration

You can configure Docsify by defining `window.$docsify` as an object:

```html
<script>
  window.$docsify = {
    repo: 'docsifyjs/docsify',
    maxLevel: 3,
    coverpage: true,
  };
</script>
```

The config can also be defined as a function, in which case the first argument is the Docsify `vm` instance. The function should return a config object. This can be useful for referencing `vm` in places like the markdown configuration:

```html
<script>
  window.$docsify = function (vm) {
    return {
      markdown: {
        renderer: {
          code(code, lang) {
            // ... use `vm` ...
          },
        },
      },
    };
  };
</script>
```

## alias

- Type: `Object`

Set the route alias. You can freely manage routing rules. Supports RegExp.
Do note that order matters! If a route can be matched by multiple aliases, the one you declared first takes precedence.

```js
window.$docsify = {
  alias: {
    '/foo/(.*)': '/bar/$1', // supports regexp
    '/zh-cn/changelog': '/changelog',
    '/changelog':
      'https://raw.githubusercontent.com/docsifyjs/docsify/main/CHANGELOG',

    // You may need this if you use routerMode:'history'.
    '/.*/_sidebar.md': '/_sidebar.md', // See #301
  },
};
```

> **Note** If you change [`routerMode`](#routermode) to `'history'`, you may
> want to configure an alias for your `_sidebar.md` and `_navbar.md` files.

## auto2top

- Type: `Boolean`
- Default: `false`

Scrolls to the top of the screen when the route is changed.

```js
window.$docsify = {
  auto2top: true,
};
```

## autoHeader

- Type: `Boolean`
- Default: `false`

If `loadSidebar` and `autoHeader` are both enabled, for each link in `_sidebar.md`, prepend a header to the page before converting it to HTML. See [#78](https://github.com/docsifyjs/docsify/issues/78).

```js
window.$docsify = {
  loadSidebar: true,
  autoHeader: true,
};
```

## basePath

- Type: `String`

Base path of the website. You can set it to another directory or another domain name.

```js
window.$docsify = {
  basePath: '/path/',

  // Load the files from another site
  basePath: 'https://docsify.js.org/',

  // Even can load files from other repo
  basePath:
    'https://raw.githubusercontent.com/ryanmcdermott/clean-code-javascript/master/',
};
```

## catchPluginErrors

- Type: `Boolean`
- Default: `true`

Determines if Docsify should handle uncaught _synchronous_ plugin errors automatically. This can prevent plugin errors from affecting docsify's ability to properly render live site content.

## cornerExternalLinkTarget

- Type: `String`
- Default: `'_blank'`

Target to open external link at the top right corner. Default `'_blank'` (new window/tab)

```js
window.$docsify = {
  cornerExternalLinkTarget: '_self', // default: '_blank'
};
```

## coverpage

- Type: `Boolean|String|String[]|Object`
- Default: `false`

Activate the [cover feature](cover.md). If true, it will load from `_coverpage.md`.

```js
window.$docsify = {
  coverpage: true,

  // Custom file name
  coverpage: 'cover.md',

  // multiple covers
  coverpage: ['/', '/zh-cn/'],

  // multiple covers and custom file name
  coverpage: {
    '/': 'cover.md',
    '/zh-cn/': 'cover.md',
  },
};
```

## el

- Type: `String`
- Default: `'#app'`

The DOM element to be mounted on initialization. It can be a CSS selector string or an actual [HTMLElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement).

```js
window.$docsify = {
  el: '#app',
};
```

## executeScript

- Type: `Boolean`
- Default: `null`

Execute the script on the page. Only parses the first script tag ([demo](themes)). If Vue is detected, this is `true` by default.

```js
window.$docsify = {
  executeScript: true,
};
```

```markdown
## This is test

<script>
  console.log(2333)
</script>
```

Note that if you are running an external script, e.g. an embedded jsfiddle demo, make sure to include the [external-script](plugins.md?id=external-script) plugin.

## ext

- Type: `String`
- Default: `'.md'`

Request file extension.

```js
window.$docsify = {
  ext: '.md',
};
```

## externalLinkRel

- Type: `String`
- Default: `'noopener'`

Default `'noopener'` (no opener) prevents the newly opened external page (when [externalLinkTarget](#externallinktarget) is `'_blank'`) from having the ability to control our page. No `rel` is set when it's not `'_blank'`. See [this post](https://mathiasbynens.github.io/rel-noopener/) for more information about why you may want to use this option.

```js
window.$docsify = {
  externalLinkRel: '', // default: 'noopener'
};
```

## externalLinkTarget

- Type: `String`
- Default: `'_blank'`

Target to open external links inside the markdown. Default `'_blank'` (new window/tab)

```js
window.$docsify = {
  externalLinkTarget: '_self', // default: '_blank'
};
```

## fallbackLanguages

- Type: `Array<string>`

List of languages that will fallback to the default language when a page is requested and it doesn't exist for the given locale.

Example:

- try to fetch the page of `/de/overview`. If this page exists, it'll be displayed.
- then try to fetch the default page `/overview` (depending on the default language). If this page exists, it'll be displayed.
- then display the 404 page.

```js
window.$docsify = {
  fallbackLanguages: ['fr', 'de'],
};
```

## formatUpdated

- Type: `String|Function`

We can display the file update date through **{docsify-updated<span>}</span>** variable. And format it by `formatUpdated`.
See https://github.com/lukeed/tinydate#patterns

```js
window.$docsify = {
  formatUpdated: '{MM}/{DD} {HH}:{mm}',

  formatUpdated(time) {
    // ...

    return time;
  },
};
```

## hideSidebar

- Type : `Boolean`
- Default: `true`

This option will completely hide your sidebar and won't render any content on the side.

```js
window.$docsify = {
  hideSidebar: true,
};
```

## homepage

- Type: `String`
- Default: `'README.md'`

`README.md` in your docs folder will be treated as the homepage for your website, but sometimes you may need to serve another file as your homepage.

```js
window.$docsify = {
  // Change to /home.md
  homepage: 'home.md',

  // Or use the readme in your repo
  homepage:
    'https://raw.githubusercontent.com/docsifyjs/docsify/main/README.md',
};
```

## keyBindings

- Type: `Boolean|Object`
- Default: `Object`
  - <kbd>\\</kbd> Toggle the sidebar menu
  - <kbd>/</kbd> Focus on [search](plugins#full-text-search) field. Also supports <kbd>alt</kbd>&nbsp;/&nbsp;<kbd>ctrl</kbd>&nbsp;+&nbsp;<kbd>k</kbd>.

Binds key combination(s) to a custom callback function.

Key `bindings` are defined as case insensitive string values separated by `+`. Modifier key values include `alt`, `ctrl`, `meta`, and `shift`. Non-modifier key values should match the keyboard event's [key](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key) or [code](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code) value.

The `callback` function receive a [keydown event](https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event) as an argument.

!> Let site visitors know your custom key bindings are available! If a binding is associated with a DOM element, consider inserting a `<kbd>` element as a visual cue (e.g., <kbd>alt</kbd> + <kbd>a</kbd>) or adding [title](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/title) and [aria-keyshortcuts](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Attributes/aria-keyshortcuts) attributes for hover/focus hints.

```js
window.$docsify = {
  keyBindings: {
    // Custom key binding
    myCustomBinding: {
      bindings: ['alt+a', 'shift+a'],
      callback(event) {
        alert('Hello, World!');
      },
    },
  },
};
```

Key bindings can be disabled entirely or individually by setting the binding configuration to `false`.

```js
window.$docsify = {
  // Disable all key bindings
  keyBindings: false,
};
```

```js
window.$docsify = {
  keyBindings: {
    // Disable individual key bindings
    focusSearch: false,
    toggleSidebar: false,
  },
};
```

## loadNavbar

- Type: `Boolean|String`
- Default: `false`

Loads navbar from the Markdown file `_navbar.md` if **true**, else loads it from the path specified.

```js
window.$docsify = {
  // load from _navbar.md
  loadNavbar: true,

  // load from nav.md
  loadNavbar: 'nav.md',
};
```

## loadSidebar

- Type: `Boolean|String`
- Default: `false`

Loads sidebar from the Markdown file `_sidebar.md` if **true**, else loads it from the path specified.

```js
window.$docsify = {
  // load from _sidebar.md
  loadSidebar: true,

  // load from summary.md
  loadSidebar: 'summary.md',
};
```

## logo

- Type: `String`

Website logo as it appears in the sidebar. You can resize it using CSS.

!> Logo will only be visible if `name` prop is also set. See [name](#name) configuration.

```js
window.$docsify = {
  logo: '/_media/icon.svg',
};
```

## markdown

- Type: `Function`

See [Markdown configuration](markdown.md).

```js
window.$docsify = {
  // object
  markdown: {
    smartypants: true,
    renderer: {
      link() {
        // ...
      },
    },
  },

  // function
  markdown(marked, renderer) {
    // ...
    return marked;
  },
};
```

## maxLevel

- Type: `Number`
- Default: `6`

Maximum Table of content level.

```js
window.$docsify = {
  maxLevel: 4,
};
```

## mergeNavbar

- Type: `Boolean`
- Default: `false`

Navbar will be merged with the sidebar on smaller screens.

```js
window.$docsify = {
  mergeNavbar: true,
};
```

## name

- Type: `String`

Website name as it appears in the sidebar.

```js
window.$docsify = {
  name: 'docsify',
};
```

The name field can also contain custom HTML for easier customization:

```js
window.$docsify = {
  name: '<span>docsify</span>',
};
```

## nameLink

- Type: `String`
- Default: `'window.location.pathname'`

The URL that the website `name` links to.

```js
window.$docsify = {
  nameLink: '/',

  // For each route
  nameLink: {
    '/zh-cn/': '#/zh-cn/',
    '/': '#/',
  },
};
```

## nativeEmoji

- Type: `Boolean`
- Default: `false`

Render emoji shorthand codes using GitHub-style emoji images or native emoji characters.

```js
window.$docsify = {
  nativeEmoji: true,
};
```

```markdown
:smile:
:partying_face:
:joy:
:+1:
:-1:
```

GitHub-style images when `false`:

<output data-lang="output">
  <img class="emoji" src="https://github.githubassets.com/images/icons/emoji/unicode/1f604.png" alt="smile">
  <img class="emoji" src="https://github.githubassets.com/images/icons/emoji/unicode/1f973.png" alt="partying_face">
  <img class="emoji" src="https://github.githubassets.com/images/icons/emoji/unicode/1f602.png" alt="joy">
  <img class="emoji" src="https://github.githubassets.com/images/icons/emoji/unicode/1f44d.png" alt="+1">
  <img class="emoji" src="https://github.githubassets.com/images/icons/emoji/unicode/1f44e.png" alt="-1">
</output>

Native characters when `true`:

<output data-lang="output">
  <span class="emoji">😄︎</span>
  <span class="emoji">🥳︎</span>
  <span class="emoji">😂︎</span>
  <span class="emoji">👍︎</span>
  <span class="emoji">👎︎</span>
</output>

To render shorthand codes as text, replace `:` characters with the `&colon;` HTML entity.

```markdown
&colon;100&colon;
```

<output data-lang="output">

&colon;100&colon;

</output>

## noCompileLinks

- Type: `Array<string>`

Sometimes we do not want docsify to handle our links. See [#203](https://github.com/docsifyjs/docsify/issues/203). We can skip compiling of certain links by specifying an array of strings. Each string is converted into to a regular expression (`RegExp`) and the _whole_ href of a link is matched against it.

```js
window.$docsify = {
  noCompileLinks: ['/foo', '/bar/.*'],
};
```

## noEmoji

- Type: `Boolean`
- Default: `false`

Disabled emoji parsing and render all emoji shorthand as text.

```js
window.$docsify = {
  noEmoji: true,
};
```

```markdown
:100:
```

<output data-lang="output">

&colon;100&colon;

</output>

To disable emoji parsing of individual shorthand codes, replace `:` characters with the `&colon;` HTML entity.

```markdown
:100:

&colon;100&colon;
```

<output data-lang="output">

:100:

&colon;100&colon;

</output>

## notFoundPage

- Type: `Boolean|String|Object`
- Default: `false`

Display default "404 - Not Found" message:

```js
window.$docsify = {
  notFoundPage: false,
};
```

Load the `_404.md` file:

```js
window.$docsify = {
  notFoundPage: true,
};
```

Load the customized path of the 404 page:

```js
window.$docsify = {
  notFoundPage: 'my404.md',
};
```

Load the right 404 page according to the localization:

```js
window.$docsify = {
  notFoundPage: {
    '/': '_404.md',
    '/de': 'de/_404.md',
  },
};
```

> Note: The options for fallbackLanguages don't work with the `notFoundPage` options.

## onlyCover

- Type: `Boolean`
- Default: `false`

Only coverpage is loaded when visiting the home page.

```js
window.$docsify = {
  onlyCover: false,
};
```

## relativePath

- Type: `Boolean`
- Default: `false`

If **true**, links are relative to the current context.

For example, the directory structure is as follows:

```text
.
└── docs
    ├── README.md
    ├── guide.md
    └── zh-cn
        ├── README.md
        ├── guide.md
        └── config
            └── example.md
```

With relative path **enabled** and current URL `http://domain.com/zh-cn/README`, given links will resolve to:

```text
guide.md              => http://domain.com/zh-cn/guide
config/example.md     => http://domain.com/zh-cn/config/example
../README.md          => http://domain.com/README
/README.md            => http://domain.com/README
```

```js
window.$docsify = {
  // Relative path enabled
  relativePath: true,

  // Relative path disabled (default value)
  relativePath: false,
};
```

## repo

- Type: `String`

Configure the repository url, or a string of `username/repo`, to add the [GitHub Corner](http://tholman.com/github-corners/) widget in the top right corner of the site.

```js
window.$docsify = {
  repo: 'docsifyjs/docsify',
  // or
  repo: 'https://github.com/docsifyjs/docsify/',
};
```

## requestHeaders

- Type: `Object`

Set the request resource headers.

```js
window.$docsify = {
  requestHeaders: {
    'x-token': 'xxx',
  },
};
```

Such as setting the cache

```js
window.$docsify = {
  requestHeaders: {
    'cache-control': 'max-age=600',
  },
};
```

## routerMode

Configure the URL format that the paths of your site will use.

- Type: `String`
- Default: `'hash'`

```js
window.$docsify = {
  routerMode: 'history', // default: 'hash'
};
```

For statically-deployed sites (f.e. on GitHub Pages) hash-based routing is
simpler to set up. For websites that can re-write URLs, the history-based format
is better (especially for search-engine optimization, hash-based routing is not
so search-engine friendly)

Hash-based routing means all URL paths will be prefixed with `/#/` in the
address bar. This is a trick that allows the site to load `/index.html`, then it
uses the path that follows the `#` to determine what markdown files to load. For
example, a complete hash-based URL may look like this:
`https://example.com/#/path/to/page`. The browser will actually load
`https://example.com` (assuming your static server serves
`index.html` by default, as most do), and then the Docsify JavaScript code will
look at the `/#/...` and determine the markdown file to load and render.
Additionally, when clicking on a link, the Docsify router will change the
content after the hash dynamically. The value of `location.pathname` will still be
`/` no matter what. The parts of a hash path are _not_ sent to the server when
visiting such a URL in a browser.

On the other hand, history-based routing means the Docsify JavaScript will use
the [History API](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
to dynamically change the URL without using a `#`. This means that all URLs will
be considered "real" by search engines, and the full path will be sent to the
server when visiting the URL in your browser. For example, a URL may look like
`https://example.com/path/to/page`. The browser will try to load that full URL
directly from the server, not just `https://example.com`. The upside of this is
that these types of URLs are much more friendly for search engines, and can be
indexed (yay!). The downside, however, is that your server, or the place where
you host your site files, has to be able to handle these URLs. Various static
website hosting services allow "rewrite rules" to be configured, such that a
server can be configured to always send back `/index.html` no matter what path
is visited. The value of `location.pathname` will show `/path/to/page`, because
it was actually sent to the server.

TLDR: start with `hash` routing (the default). If you feel adventurous, learn
how to configure a server, then switch to `history` mode for better experience
without the `#` in the URL and SEO optimization.

> **Note** If you use `routerMode: 'history'`, you may want to add an
> [`alias`](#alias) to make your `_sidebar.md` and `_navbar.md` files always be
> loaded no matter which path is being visited.
>
> ```js
> window.$docsify = {
>   routerMode: 'history',
>   alias: {
>     '/.*/_sidebar.md': '/_sidebar.md',
>     '/.*/_navbar.md': '/_navbar.md',
>   },
> };
> ```

## routes

- Type: `Object`

Define "virtual" routes that can provide content dynamically. A route is a map between the expected path, to either a string or a function. If the mapped value is a string, it is treated as markdown and parsed accordingly. If it is a function, it is expected to return markdown content.

A route function receives up to three parameters:

1. `route` - the path of the route that was requested (e.g. `/bar/baz`)
2. `matched` - the [`RegExpMatchArray`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/match) that was matched by the route (e.g. for `/bar/(.+)`, you get `['/bar/baz', 'baz']`)
3. `next` - this is a callback that you may call when your route function is async

Do note that order matters! Routes are matched the same order you declare them in, which means that in cases where you have overlapping routes, you might want to list the more specific ones first.

```js
window.$docsify = {
  routes: {
    // Basic match w/ return string
    '/foo': '# Custom Markdown',

    // RegEx match w/ synchronous function
    '/bar/(.*)'(route, matched) {
      return '# Custom Markdown';
    },

    // RegEx match w/ asynchronous function
    '/baz/(.*)'(route, matched, next) {
      fetch('/api/users?id=12345')
        .then(response => {
          next('# Custom Markdown');
        })
        .catch(err => {
          // Handle error...
        });
    },
  },
};
```

Other than strings, route functions can return a falsy value (`null` \ `undefined`) to indicate that they ignore the current request:

```js
window.$docsify = {
  routes: {
    // accepts everything other than dogs (synchronous)
    '/pets/(.+)'(route, matched) {
      if (matched[0] === 'dogs') {
        return null;
      } else {
        return 'I like all pets but dogs';
      }
    }

    // accepts everything other than cats (asynchronous)
    '/pets/(.*)'(route, matched, next) {
      if (matched[0] === 'cats') {
        next();
      } else {
        // Async task(s)...
        next('I like all pets but cats');
      }
    }
  }
}
```

Finally, if you have a specific path that has a real markdown file (and therefore should not be matched by your route), you can opt it out by returning an explicit `false` value:

```js
window.$docsify = {
  routes: {
    // if you look up /pets/cats, docsify will skip all routes and look for "pets/cats.md"
    '/pets/cats'(route, matched) {
      return false;
    }

    // but any other pet should generate dynamic content right here
    '/pets/(.+)'(route, matched) {
      const pet = matched[0];
      return `your pet is ${pet} (but not a cat)`;
    }
  }
}
```

## skipLink

- Type: `Boolean|String|Object`
- Default: `'Skip to main content'`

Determines if/how the site's [skip navigation link](https://webaim.org/techniques/skipnav/) will be rendered.

```js
// Render skip link for all routes (default)
window.$docsify = {
  skipLink: 'Skip to main content',
};
```

```js
// Render localized skip links based on route paths
window.$docsify = {
  skipLink: {
    '/es/': 'Saltar al contenido principal',
    '/de-de/': 'Ga naar de hoofdinhoud',
    '/ru-ru/': 'Перейти к основному содержанию',
    '/zh-cn/': '跳到主要内容',
  },
};
```

```js
// Do not render skip link
window.$docsify = {
  skipLink: false,
};
```

## subMaxLevel

- Type: `Number`
- Default: `0`

Add table of contents (TOC) in custom sidebar.

```js
window.$docsify = {
  subMaxLevel: 2,
};
```

If you have a link to the homepage in the sidebar and want it to be shown as active when accessing the root url, make sure to update your sidebar accordingly:

```markdown
- Sidebar
  - [Home](/)
  - [Another page](another.md)
```

For more details, see [#1131](https://github.com/docsifyjs/docsify/issues/1131).

## themeColor ⚠️

!> Deprecated as of v5. Use the `--theme-color` [theme property](themes#theme-properties) to [customize](themes#customization) your theme color.

- Type: `String`

Customize the theme color.

```js
window.$docsify = {
  themeColor: '#3F51B5',
};
```

## topMargin ⚠️

!> Deprecated as of v5. Use the `--scroll-padding-top` [theme property](themes#theme-properties) to specify a scroll margin when using a sticky navbar.

- Type: `Number|String`
- Default: `0`

Adds scroll padding to the top of the viewport. This is useful when you have added a sticky or "fixed" element and would like auto scrolling to align with the bottom of your element.

```js
window.$docsify = {
  topMargin: 90, // 90, '90px', '2rem', etc.
};
```

## vueComponents

- Type: `Object`

Creates and registers global [Vue](https://vuejs.org/guide/essentials/component-basics.html). Components are specified using the component name as the key with an object containing Vue options as the value. Component `data` is unique for each instance and will not persist as users navigate the site.

```js
window.$docsify = {
  vueComponents: {
    'button-counter': {
      template: `
        <button @click="count += 1">
          You clicked me {{ count }} times
        </button>
      `,
      data() {
        return {
          count: 0,
        };
      },
    },
  },
};
```

```markdown
<button-counter></button-counter>
```

<output data-lang="output">
  <button-counter></button-counter>
</output>

## vueGlobalOptions

- Type: `Object`

Specifies global Vue options for use with Vue content not explicitly mounted with [vueMounts](#mounting-dom-elements), [vueComponents](#components), or a [markdown script](#markdown-script). Changes to global `data` will persist and be reflected anywhere global references are used.

```js
window.$docsify = {
  vueGlobalOptions: {
    data() {
      return {
        count: 0,
      };
    },
  },
};
```

```markdown
<p>
  <button @click="count -= 1">-</button>
  {{ count }}
  <button @click="count += 1">+</button>
</p>
```

<output data-lang="output">
  <p>
    <button @click="count -= 1">-</button>
    {{ count }}
    <button @click="count += 1">+</button>
  </p>
</output>

## vueMounts

- Type: `Object`

Specifies DOM elements to mount as Vue instances and their associated options. Mount elements are specified using a [CSS selector](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) as the key with an object containing Vue options as their value. Docsify will mount the first matching element in the main content area each time a new page is loaded. Mount element `data` is unique for each instance and will not persist as users navigate the site.

```js
window.$docsify = {
  vueMounts: {
    '#counter': {
      data() {
        return {
          count: 0,
        };
      },
    },
  },
};
```

```markdown
<div id="counter">
  <button @click="count -= 1">-</button>
  {{ count }}
  <button @click="count += 1">+</button>
</div>
```

<output id="counter">
  <button @click="count -= 1">-</button>
  {{ count }}
  <button @click="count += 1">+</button>
</output>
`````

## File: docs/cover.md
`````markdown
# Cover

Activate the cover feature by setting `coverpage` to **true**. See [coverpage configuration](configuration#coverpage).

## Basic usage

Set `coverpage` to **true**, and create a `_coverpage.md`:

```js
window.$docsify = {
  coverpage: true,
};
```

```markdown
<!-- _coverpage.md -->

![logo](_media/icon.svg)

# docsify

> A magical documentation site generator

- Simple and lightweight
- No statically built HTML files
- Multiple themes

[GitHub](https://github.com/docsifyjs/docsify/)
[Get Started](#docsify)
```

## Customization

The cover page can be customized using [theme properties](themes#theme-properties):

<!-- prettier-ignore -->
```css
:root {
  --cover-bg         : url('path/to/image.png');
  --cover-bg-overlay : rgba(0, 0, 0, 0.5);
  --cover-color      : #fff;
  --cover-title-color: var(--theme-color);
  --cover-title-font : 600 var(--font-size-xxxl) var(--font-family);
}
```

Alternatively, a background color or image can be specified in the cover page markdown.

```markdown
<!-- background color -->

![color](#f0f0f0)
```

```markdown
<!-- background image -->

![](_media/bg.png)
```

## Coverpage as homepage

Normally, the coverpage and the homepage appear at the same time. Of course, you can also separate the coverpage by [`onlyCover`](configuration#onlycover) option.

## Multiple covers

If your docs site is in more than one language, it may be useful to set multiple covers.

For example, your docs structure is like this

```text
.
└── docs
    ├── README.md
    ├── guide.md
    ├── _coverpage.md
    └── zh-cn
        ├── README.md
        └── guide.md
        └── _coverpage.md
```

Now, you can set

```js
window.$docsify = {
  coverpage: ['/', '/zh-cn/'],
};
```

Or a special file name

```js
window.$docsify = {
  coverpage: {
    '/': 'cover.md',
    '/zh-cn/': 'cover.md',
  },
};
```
`````

## File: docs/custom-navbar.md
`````markdown
# Custom navbar

## HTML

If you need custom navigation, you can create a HTML-based navigation bar.

!> Note that documentation links begin with `#/`.

```html
<!-- index.html -->

<body>
  <nav>
    <a href="#/">EN</a>
    <a href="#/zh-cn/">简体中文</a>
  </nav>
  <div id="app"></div>
</body>
```

## Markdown

Alternatively, you can create a custom markdown-based navigation file by setting `loadNavbar` to **true** and creating `_navbar.md`, compare [loadNavbar configuration](configuration#loadnavbar).

```html
<!-- index.html -->

<script>
  window.$docsify = {
    loadNavbar: true,
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
```

```markdown
<!-- _navbar.md -->

- [En](/)
- [chinese](/zh-cn/)
```

To create drop-down menus:

```markdown
<!-- _navbar.md -->

- Translations

  - [En](/)
  - [chinese](/zh-cn/)
```

!> You need to create a `.nojekyll` in `./docs` to prevent GitHub Pages from ignoring files that begin with an underscore.

`_navbar.md` is loaded from each level directory. If the current directory doesn't have `_navbar.md`, it will fall back to the parent directory. If, for example, the current path is `/guide/quick-start`, the `_navbar.md` will be loaded from `/guide/_navbar.md`.

## Nesting

You can create sub-lists by indenting items that are under a certain parent.

```markdown
<!-- _navbar.md -->

- Getting started

  - [Quick start](quickstart.md)
  - [Writing more pages](more-pages.md)
  - [Custom navbar](custom-navbar.md)
  - [Cover page](cover.md)

- Configuration

  - [Configuration](configuration.md)
  - [Themes](themes.md)
  - [Using plugins](plugins.md)
  - [Markdown configuration](markdown.md)
  - [Language highlight](language-highlight.md)
```

renders as

![Nesting navbar](_images/nested-navbar.png 'Nesting navbar')

## Combining custom navbars with the emoji plugin

If you use the [emoji plugin](plugins#emoji):

```html
<!-- index.html -->

<script>
  window.$docsify = {
    // ...
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/emoji.min.js"></script>
```

you could, for example, use flag emojis in your custom navbar Markdown file:

```markdown
<!-- _navbar.md -->

- [:us:, :uk:](/)
- [:cn:](/zh-cn/)
```
`````

## File: docs/deploy.md
`````markdown
# Deploy

Similar to [GitBook](https://www.gitbook.com), you can deploy files to GitHub Pages, GitLab Pages or VPS.

## GitHub Pages

There are three places to populate your docs for your GitHub repository:

- `docs/` folder
- main branch
- gh-pages branch

It is recommended that you save your files to the `./docs` subfolder of the `main` branch of your repository. Then select `main branch /docs folder` as your GitHub Pages source in your repository's settings page.

![GitHub Pages](_images/deploy-github-pages.png)

!> You can also save files in the root directory and select `main branch`.
You'll need to place a `.nojekyll` file in the deploy location (such as `/docs` or the gh-pages branch)

## GitLab Pages

If you are deploying your master branch, create a `.gitlab-ci.yml` with the following script:

?> The `.public` workaround is so `cp` doesn't also copy `public/` to itself in an infinite loop.

```YAML
pages:
  stage: deploy
  script:
  - mkdir .public
  - cp -r * .public
  - mv .public public
  artifacts:
    paths:
    - public
  only:
  - master
```

!> You can replace script with `- cp -r docs/. public`, if `./docs` is your Docsify subfolder.

## Firebase Hosting

!> You'll need to install the Firebase CLI using `npm i -g firebase-tools` after signing into the [Firebase Console](https://console.firebase.google.com) using a Google Account.

Using a terminal, determine and navigate to the directory for your Firebase Project. This could be `~/Projects/Docs`, etc. From there, run `firebase init` and choose `Hosting` from the menu (use **space** to select, **arrow keys** to change options and **enter** to confirm). Follow the setup instructions.

Your `firebase.json` file should look similar to this (I changed the deployment directory from `public` to `site`):

```json
{
  "hosting": {
    "public": "site",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"]
  }
}
```

Once finished, build the starting template by running `docsify init ./site` (replacing site with the deployment directory you determined when running `firebase init` - public by default). Add/edit the documentation, then run `firebase deploy` from the root project directory.

## VPS

Use the following nginx config.

```nginx
server {
  listen 80;
  server_name  your.domain.com;

  location / {
    alias /path/to/dir/of/docs/;
    index index.html;
  }
}
```

## Netlify

1.  Login to your [Netlify](https://www.netlify.com/) account.
2.  In the [dashboard](https://app.netlify.com/) page, click **Add New Site**.
3.  Select GitHub.
4.  Choose the repository where you store your docs, in the **Base Directory** add the subfolder where the files are stored. For example, it should be `docs`.
5.  In the **Build Command** area leave it blank.
6.  In the **Publish directory** area, if you have added the `docs` in the **Base Directory** you will see the publish directory populated with `docs/`
7.  Netlify is smart enough to look for the the `index.html` file inside the `docs/` folder.

### HTML5 router

When using the HTML5 router, you need to set up redirect rules that redirect all requests to your `index.html`. It's pretty simple when you're using Netlify. Just create a file named `_redirects` in the docs directory, add this snippet to the file, and you're all set:

```sh
/*    /index.html   200
```

## Vercel

1. Install [Vercel CLI](https://vercel.com/download), `npm i -g vercel`
2. Change directory to your docsify website, for example `cd docs`
3. Deploy with a single command, `vercel`

## AWS Amplify

1. Set the routerMode in the Docsify project `index.html` to _history_ mode.

```html
<script>
  window.$docsify = {
    loadSidebar: true,
    routerMode: 'history',
  };
</script>
```

2. Login to your [AWS Console](https://aws.amazon.com).
3. Go to the [AWS Amplify Dashboard](https://aws.amazon.com/amplify).
4. Choose the **Deploy** route to setup your project.
5. When prompted, keep the build settings empty if you're serving your docs within the root directory. If you're serving your docs from a different directory, customise your amplify.yml

```yml
version: 0.1
frontend:
  phases:
    build:
      commands:
        - echo "Nothing to build"
  artifacts:
    baseDirectory: /docs
    files:
      - '**/*'
  cache:
    paths: []
```

6. Add the following Redirect rules in their displayed order. Note that the second record is a PNG image where you can change it with any image format you are using.

| Source address | Target address | Type          |
| -------------- | -------------- | ------------- |
| /<\*>.md       | /<\*>.md       | 200 (Rewrite) |
| /<\*>.png      | /<\*>.png      | 200 (Rewrite) |
| /<\*>          | /index.html    | 200 (Rewrite) |

## Stormkit

1.  Login to your [Stormkit](https://www.stormkit.io) account.
2.  Using the user interface, import your docsify project from one of the three supported Git providers (GitHub, GitLab, or Bitbucket).
3.  Navigate to the project’s production environment in Stormkit or create a new environment if needed.
4.  Verify the build command in your Stormkit configuration. By default, Stormkit CI will run `npm run build` but you can specify a custom build command on this page.
5.  Set output folder to `docs`
6.  Click the “Deploy Now” button to deploy your site.

Read more in the [Stormkit Documentation](https://stormkit.io/docs).

## Docker

- Create docsify files

  You need prepare the initial files instead of making them inside the container.
  See the [Quickstart](https://docsify.js.org/#/quickstart) section for instructions on how to create these files manually or using [docsify-cli](https://github.com/docsifyjs/docsify-cli).

  ```sh
  index.html
  README.md
  ```

- Create Dockerfile

  ```Dockerfile
    FROM node:latest
    LABEL description="A demo Dockerfile for build Docsify."
    WORKDIR /docs
    RUN npm install -g docsify-cli@latest
    EXPOSE 3000/tcp
    ENTRYPOINT docsify serve .

  ```

  The current directory structure should be this:

  ```sh
   index.html
   README.md
   Dockerfile
  ```

- Build docker image

  ```sh
  docker build -f Dockerfile -t docsify/demo .
  ```

- Run docker image

  ```sh
  docker run -itp 3000:3000 --name=docsify -v $(pwd):/docs docsify/demo
  ```

## Kinsta Static Site Hosting

You can deploy **Docsify** as a Static Site on [Kinsta](https://kinsta.com/static-site-hosting/).

1. Login or create an account to view your [MyKinsta](https://my.kinsta.com/) dashboard.

2. Authorize Kinsta with your Git provider.

3. Select **Static Sites** from the left sidebar and press **Add sites**.

4. Select the repository and branch you want to deploy.

5. During the build settings, Kinsta will automatically try to fill out the **Build command**, **Node version**, and **Publish directory**. If it won't, fill out the following:

   - Build command: leave empty
   - Node version: leave on default selection or a specific version (e.g. `18.16.0`)
   - Publish directory: `docs`

6. Click the **Create site**.
`````

## File: docs/embed-files.md
`````markdown
# Embed files

With docsify 4.6 it is now possible to embed any type of file.

You can embed these files as video, audio, iframes, or code blocks, and even Markdown files can even be embedded directly into the document.

For example, here is an embedded Markdown file. You only need to do this:

```markdown
[filename](_media/example.md ':include')
```

Then the content of `example.md` will be displayed directly here:

[filename](_media/example.md ':include')

You can check the original content for [example.md](_media/example.md ':ignore').

Normally, this will be compiled into a link, but in docsify, if you add `:include` it will be embedded. You can use single or double quotation marks around as you like.

External links can be used too - just replace the target. If you want to use a gist URL, see [Embed a gist](#embed-a-gist) section.

## Embedded file type

Currently, file extensions are automatically recognized and embedded in different ways.

These types are supported:

- **iframe** `.html`, `.htm`
- **markdown** `.markdown`, `.md`
- **audio** `.mp3`
- **video** `.mp4`, `.ogg`
- **code** other file extension

Of course, you can force the specified type. For example, a Markdown file can be embedded as a code block by setting `:type=code`.

```markdown
[filename](_media/example.md ':include :type=code')
```

You will get:

[filename](_media/example.md ':include :type=code')

## Markdown with YAML Front Matter

Front Matter, commonly utilized in blogging systems like Jekyll, serves to define metadata for a document. The [front-matter.js](https://www.npmjs.com/package/front-matter) package facilitates the extraction of metadata (front matter) from documents.

When using Markdown, YAML front matter will be stripped from the rendered content. The attributes cannot be used in this case.

```markdown
[filename](_media/example-with-yaml.md ':include')
```

You will get just the content

[filename](_media/example-with-yaml.md ':include')

## Embedded code fragments

Sometimes you don't want to embed a whole file. Maybe because you need just a few lines but you want to compile and test the file in CI.

```markdown
[filename](_media/example.js ':include :type=code :fragment=demo')
```

In your code file you need to surround the fragment between `/// [demo]` lines (before and after the fragment).
Alternatively you can use `### [demo]`.

Example:

[filename](_media/example.js ':include :type=code :fragment=demo')

## Tag attribute

If you embed the file as `iframe`, `audio` and `video`, then you may need to set the attributes of these tags.

?> Note, for the `audio` and `video` types, docsify adds the `controls` attribute by default. When you want add more attributes, the `controls` attribute need to be added manually if need be.

```md
[filename](_media/example.mp4 ':include :type=video controls width=100%')
```

```markdown
[cinwell website](https://cinwell.com ':include :type=iframe width=100% height=400px')
```

[cinwell website](https://cinwell.com ':include :type=iframe width=100% height=400px')

Did you see it? You only need to write directly. You can check [MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe) for these attributes.

## The code block highlight

Embedding any type of source code file, you can specify the highlighted language or automatically identify.

```markdown
[](_media/example.html ':include :type=code text')
```

⬇️

[](_media/example.html ':include :type=code text')

?> How to set highlight? You can see [here](language-highlight.md).

## Embed a gist

You can embed a gist as markdown content or as a code block - this is based on the approach at the start of [Embed Files](#embed-files) section, but uses a raw gist URL as the target.

?> **No** plugin or app config change is needed here to make this work. In fact, the "Embed" `script` tag that is copied from a gist will _not_ load even if you make plugin or config changes to allow an external script.

### Identify the gist's metadata

Start by viewing a gist on `gist.github.com`. For the purposes of this guide, we use this gist:

- https://gist.github.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15

Identify the following items from the gist:

| Field        | Example                            | Description                                                                                        |
| ------------ | ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Username** | `anikethsaha`                      | The gist's owner.                                                                                  |
| **Gist ID**  | `c2bece08f27c4277001f123898d16a7c` | Identifier for the gist. This is fixed for the gist's lifetime.                                    |
| **Filename** | `content.md`                       | Select a name of a file in the gist. This needed even on a single-file gist for embedding to work. |

You will need those to build the _raw gist URL_ for the target file. This has the following format:

- `https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/FILENAME`

Here are two examples based on the sample gist:

- https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/content.md
- https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/script.js

?> Alternatively, you can get a raw URL directly clicking the _Raw_ button on a gist file. But, if you use that approach, just be sure to **remove** the revision number between `raw/` and the filename so that the URL matches the pattern above instead. Otherwise your embedded gist will **not** show the latest content when the gist is updated.

Continue with one of the sections below to embed the gist on a Docsify page.

### Render markdown content from a gist

This is a great way to embed content **seamlessly** in your docs, without sending someone to an external link. This approach is well-suited to reusing a gist of say installation instructions across doc sites of multiple repos. This approach works equally well with a gist owned by your account or by another user.

Here is the format:

```markdown
[LABEL](https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/FILENAME ':include')
```

For example:

```markdown
[gist: content.md](https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/content.md ':include')
```

Which renders as:

[gist: content.md](https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/content.md ':include')

The `LABEL` can be any text you want. It acts as a _fallback_ message if the link is broken - so it is useful to repeat the filename here in case you need to fix a broken link. It also makes an embedded element easy to read at a glance.

### Render a codeblock from a gist

The format is the same as the previous section, but with `:type=code` added to the alt text. As with the [Embedded file type](#embedded-file-type) section, the syntax highlighting will be **inferred** from the extension (e.g. `.js` or `.py`), so you can leave the `type` set as `code`.

Here is the format:

```markdown
[LABEL](https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/FILENAME ':include :type=code')
```

For example:

```markdown
[gist: script.js](https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/script.js ':include :type=code')
```

Which renders as:

[gist: script.js](https://gist.githubusercontent.com/anikethsaha/f88893bb563bb7229d6e575db53a8c15/raw/script.js ':include :type=code')
`````

## File: docs/emoji.md
`````markdown
# Emoji

Below is a complete list of emoji shorthand codes. Docsify can be configured to render emoji using GitHub-style emoji images or native emoji characters using the [`nativeEmoji`](configuration#nativeemoji) configuration option.

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(15em, 1fr));">

<!-- START: Auto-generated content (/build/emoji.js) -->

:100: `:100:`

:1234: `:1234:`

:+1: `:+1:`

:-1: `:-1:`

:1st_place_medal: `:1st_place_medal:`

:2nd_place_medal: `:2nd_place_medal:`

:3rd_place_medal: `:3rd_place_medal:`

:8ball: `:8ball:`

:a: `:a:`

:ab: `:ab:`

:abacus: `:abacus:`

:abc: `:abc:`

:abcd: `:abcd:`

:accept: `:accept:`

:accessibility: `:accessibility:`

:accordion: `:accordion:`

:adhesive_bandage: `:adhesive_bandage:`

:adult: `:adult:`

:aerial_tramway: `:aerial_tramway:`

:afghanistan: `:afghanistan:`

:airplane: `:airplane:`

:aland_islands: `:aland_islands:`

:alarm_clock: `:alarm_clock:`

:albania: `:albania:`

:alembic: `:alembic:`

:algeria: `:algeria:`

:alien: `:alien:`

:ambulance: `:ambulance:`

:american_samoa: `:american_samoa:`

:amphora: `:amphora:`

:anatomical_heart: `:anatomical_heart:`

:anchor: `:anchor:`

:andorra: `:andorra:`

:angel: `:angel:`

:anger: `:anger:`

:angola: `:angola:`

:angry: `:angry:`

:anguilla: `:anguilla:`

:anguished: `:anguished:`

:ant: `:ant:`

:antarctica: `:antarctica:`

:antigua_barbuda: `:antigua_barbuda:`

:apple: `:apple:`

:aquarius: `:aquarius:`

:argentina: `:argentina:`

:aries: `:aries:`

:armenia: `:armenia:`

:arrow_backward: `:arrow_backward:`

:arrow_double_down: `:arrow_double_down:`

:arrow_double_up: `:arrow_double_up:`

:arrow_down: `:arrow_down:`

:arrow_down_small: `:arrow_down_small:`

:arrow_forward: `:arrow_forward:`

:arrow_heading_down: `:arrow_heading_down:`

:arrow_heading_up: `:arrow_heading_up:`

:arrow_left: `:arrow_left:`

:arrow_lower_left: `:arrow_lower_left:`

:arrow_lower_right: `:arrow_lower_right:`

:arrow_right: `:arrow_right:`

:arrow_right_hook: `:arrow_right_hook:`

:arrow_up: `:arrow_up:`

:arrow_up_down: `:arrow_up_down:`

:arrow_up_small: `:arrow_up_small:`

:arrow_upper_left: `:arrow_upper_left:`

:arrow_upper_right: `:arrow_upper_right:`

:arrows_clockwise: `:arrows_clockwise:`

:arrows_counterclockwise: `:arrows_counterclockwise:`

:art: `:art:`

:articulated_lorry: `:articulated_lorry:`

:artificial_satellite: `:artificial_satellite:`

:artist: `:artist:`

:aruba: `:aruba:`

:ascension_island: `:ascension_island:`

:asterisk: `:asterisk:`

:astonished: `:astonished:`

:astronaut: `:astronaut:`

:athletic_shoe: `:athletic_shoe:`

:atm: `:atm:`

:atom: `:atom:`

:atom_symbol: `:atom_symbol:`

:australia: `:australia:`

:austria: `:austria:`

:auto_rickshaw: `:auto_rickshaw:`

:avocado: `:avocado:`

:axe: `:axe:`

:azerbaijan: `:azerbaijan:`

:b: `:b:`

:baby: `:baby:`

:baby_bottle: `:baby_bottle:`

:baby_chick: `:baby_chick:`

:baby_symbol: `:baby_symbol:`

:back: `:back:`

:bacon: `:bacon:`

:badger: `:badger:`

:badminton: `:badminton:`

:bagel: `:bagel:`

:baggage_claim: `:baggage_claim:`

:baguette_bread: `:baguette_bread:`

:bahamas: `:bahamas:`

:bahrain: `:bahrain:`

:balance_scale: `:balance_scale:`

:bald_man: `:bald_man:`

:bald_woman: `:bald_woman:`

:ballet_shoes: `:ballet_shoes:`

:balloon: `:balloon:`

:ballot_box: `:ballot_box:`

:ballot_box_with_check: `:ballot_box_with_check:`

:bamboo: `:bamboo:`

:banana: `:banana:`

:bangbang: `:bangbang:`

:bangladesh: `:bangladesh:`

:banjo: `:banjo:`

:bank: `:bank:`

:bar_chart: `:bar_chart:`

:barbados: `:barbados:`

:barber: `:barber:`

:baseball: `:baseball:`

:basecamp: `:basecamp:`

:basecampy: `:basecampy:`

:basket: `:basket:`

:basketball: `:basketball:`

:basketball_man: `:basketball_man:`

:basketball_woman: `:basketball_woman:`

:bat: `:bat:`

:bath: `:bath:`

:bathtub: `:bathtub:`

:battery: `:battery:`

:beach_umbrella: `:beach_umbrella:`

:beans: `:beans:`

:bear: `:bear:`

:bearded_person: `:bearded_person:`

:beaver: `:beaver:`

:bed: `:bed:`

:bee: `:bee:`

:beer: `:beer:`

:beers: `:beers:`

:beetle: `:beetle:`

:beginner: `:beginner:`

:belarus: `:belarus:`

:belgium: `:belgium:`

:belize: `:belize:`

:bell: `:bell:`

:bell_pepper: `:bell_pepper:`

:bellhop_bell: `:bellhop_bell:`

:benin: `:benin:`

:bento: `:bento:`

:bermuda: `:bermuda:`

:beverage_box: `:beverage_box:`

:bhutan: `:bhutan:`

:bicyclist: `:bicyclist:`

:bike: `:bike:`

:biking_man: `:biking_man:`

:biking_woman: `:biking_woman:`

:bikini: `:bikini:`

:billed_cap: `:billed_cap:`

:biohazard: `:biohazard:`

:bird: `:bird:`

:birthday: `:birthday:`

:bison: `:bison:`

:biting_lip: `:biting_lip:`

:black_bird: `:black_bird:`

:black_cat: `:black_cat:`

:black_circle: `:black_circle:`

:black_flag: `:black_flag:`

:black_heart: `:black_heart:`

:black_joker: `:black_joker:`

:black_large_square: `:black_large_square:`

:black_medium_small_square: `:black_medium_small_square:`

:black_medium_square: `:black_medium_square:`

:black_nib: `:black_nib:`

:black_small_square: `:black_small_square:`

:black_square_button: `:black_square_button:`

:blond_haired_man: `:blond_haired_man:`

:blond_haired_person: `:blond_haired_person:`

:blond_haired_woman: `:blond_haired_woman:`

:blonde_woman: `:blonde_woman:`

:blossom: `:blossom:`

:blowfish: `:blowfish:`

:blue_book: `:blue_book:`

:blue_car: `:blue_car:`

:blue_heart: `:blue_heart:`

:blue_square: `:blue_square:`

:blueberries: `:blueberries:`

:blush: `:blush:`

:boar: `:boar:`

:boat: `:boat:`

:bolivia: `:bolivia:`

:bomb: `:bomb:`

:bone: `:bone:`

:book: `:book:`

:bookmark: `:bookmark:`

:bookmark_tabs: `:bookmark_tabs:`

:books: `:books:`

:boom: `:boom:`

:boomerang: `:boomerang:`

:boot: `:boot:`

:bosnia_herzegovina: `:bosnia_herzegovina:`

:botswana: `:botswana:`

:bouncing_ball_man: `:bouncing_ball_man:`

:bouncing_ball_person: `:bouncing_ball_person:`

:bouncing_ball_woman: `:bouncing_ball_woman:`

:bouquet: `:bouquet:`

:bouvet_island: `:bouvet_island:`

:bow: `:bow:`

:bow_and_arrow: `:bow_and_arrow:`

:bowing_man: `:bowing_man:`

:bowing_woman: `:bowing_woman:`

:bowl_with_spoon: `:bowl_with_spoon:`

:bowling: `:bowling:`

:bowtie: `:bowtie:`

:boxing_glove: `:boxing_glove:`

:boy: `:boy:`

:brain: `:brain:`

:brazil: `:brazil:`

:bread: `:bread:`

:breast_feeding: `:breast_feeding:`

:bricks: `:bricks:`

:bride_with_veil: `:bride_with_veil:`

:bridge_at_night: `:bridge_at_night:`

:briefcase: `:briefcase:`

:british_indian_ocean_territory: `:british_indian_ocean_territory:`

:british_virgin_islands: `:british_virgin_islands:`

:broccoli: `:broccoli:`

:broken_heart: `:broken_heart:`

:broom: `:broom:`

:brown_circle: `:brown_circle:`

:brown_heart: `:brown_heart:`

:brown_square: `:brown_square:`

:brunei: `:brunei:`

:bubble_tea: `:bubble_tea:`

:bubbles: `:bubbles:`

:bucket: `:bucket:`

:bug: `:bug:`

:building_construction: `:building_construction:`

:bulb: `:bulb:`

:bulgaria: `:bulgaria:`

:bullettrain_front: `:bullettrain_front:`

:bullettrain_side: `:bullettrain_side:`

:burkina_faso: `:burkina_faso:`

:burrito: `:burrito:`

:burundi: `:burundi:`

:bus: `:bus:`

:business_suit_levitating: `:business_suit_levitating:`

:busstop: `:busstop:`

:bust_in_silhouette: `:bust_in_silhouette:`

:busts_in_silhouette: `:busts_in_silhouette:`

:butter: `:butter:`

:butterfly: `:butterfly:`

:cactus: `:cactus:`

:cake: `:cake:`

:calendar: `:calendar:`

:call_me_hand: `:call_me_hand:`

:calling: `:calling:`

:cambodia: `:cambodia:`

:camel: `:camel:`

:camera: `:camera:`

:camera_flash: `:camera_flash:`

:cameroon: `:cameroon:`

:camping: `:camping:`

:canada: `:canada:`

:canary_islands: `:canary_islands:`

:cancer: `:cancer:`

:candle: `:candle:`

:candy: `:candy:`

:canned_food: `:canned_food:`

:canoe: `:canoe:`

:cape_verde: `:cape_verde:`

:capital_abcd: `:capital_abcd:`

:capricorn: `:capricorn:`

:car: `:car:`

:card_file_box: `:card_file_box:`

:card_index: `:card_index:`

:card_index_dividers: `:card_index_dividers:`

:caribbean_netherlands: `:caribbean_netherlands:`

:carousel_horse: `:carousel_horse:`

:carpentry_saw: `:carpentry_saw:`

:carrot: `:carrot:`

:cartwheeling: `:cartwheeling:`

:cat: `:cat:`

:cat2: `:cat2:`

:cayman_islands: `:cayman_islands:`

:cd: `:cd:`

:central_african_republic: `:central_african_republic:`

:ceuta_melilla: `:ceuta_melilla:`

:chad: `:chad:`

:chains: `:chains:`

:chair: `:chair:`

:champagne: `:champagne:`

:chart: `:chart:`

:chart_with_downwards_trend: `:chart_with_downwards_trend:`

:chart_with_upwards_trend: `:chart_with_upwards_trend:`

:checkered_flag: `:checkered_flag:`

:cheese: `:cheese:`

:cherries: `:cherries:`

:cherry_blossom: `:cherry_blossom:`

:chess_pawn: `:chess_pawn:`

:chestnut: `:chestnut:`

:chicken: `:chicken:`

:child: `:child:`

:children_crossing: `:children_crossing:`

:chile: `:chile:`

:chipmunk: `:chipmunk:`

:chocolate_bar: `:chocolate_bar:`

:chopsticks: `:chopsticks:`

:christmas_island: `:christmas_island:`

:christmas_tree: `:christmas_tree:`

:church: `:church:`

:cinema: `:cinema:`

:circus_tent: `:circus_tent:`

:city_sunrise: `:city_sunrise:`

:city_sunset: `:city_sunset:`

:cityscape: `:cityscape:`

:cl: `:cl:`

:clamp: `:clamp:`

:clap: `:clap:`

:clapper: `:clapper:`

:classical_building: `:classical_building:`

:climbing: `:climbing:`

:climbing_man: `:climbing_man:`

:climbing_woman: `:climbing_woman:`

:clinking_glasses: `:clinking_glasses:`

:clipboard: `:clipboard:`

:clipperton_island: `:clipperton_island:`

:clock1: `:clock1:`

:clock10: `:clock10:`

:clock1030: `:clock1030:`

:clock11: `:clock11:`

:clock1130: `:clock1130:`

:clock12: `:clock12:`

:clock1230: `:clock1230:`

:clock130: `:clock130:`

:clock2: `:clock2:`

:clock230: `:clock230:`

:clock3: `:clock3:`

:clock330: `:clock330:`

:clock4: `:clock4:`

:clock430: `:clock430:`

:clock5: `:clock5:`

:clock530: `:clock530:`

:clock6: `:clock6:`

:clock630: `:clock630:`

:clock7: `:clock7:`

:clock730: `:clock730:`

:clock8: `:clock8:`

:clock830: `:clock830:`

:clock9: `:clock9:`

:clock930: `:clock930:`

:closed_book: `:closed_book:`

:closed_lock_with_key: `:closed_lock_with_key:`

:closed_umbrella: `:closed_umbrella:`

:cloud: `:cloud:`

:cloud_with_lightning: `:cloud_with_lightning:`

:cloud_with_lightning_and_rain: `:cloud_with_lightning_and_rain:`

:cloud_with_rain: `:cloud_with_rain:`

:cloud_with_snow: `:cloud_with_snow:`

:clown_face: `:clown_face:`

:clubs: `:clubs:`

:cn: `:cn:`

:coat: `:coat:`

:cockroach: `:cockroach:`

:cocktail: `:cocktail:`

:coconut: `:coconut:`

:cocos_islands: `:cocos_islands:`

:coffee: `:coffee:`

:coffin: `:coffin:`

:coin: `:coin:`

:cold_face: `:cold_face:`

:cold_sweat: `:cold_sweat:`

:collision: `:collision:`

:colombia: `:colombia:`

:comet: `:comet:`

:comoros: `:comoros:`

:compass: `:compass:`

:computer: `:computer:`

:computer_mouse: `:computer_mouse:`

:confetti_ball: `:confetti_ball:`

:confounded: `:confounded:`

:confused: `:confused:`

:congo_brazzaville: `:congo_brazzaville:`

:congo_kinshasa: `:congo_kinshasa:`

:congratulations: `:congratulations:`

:construction: `:construction:`

:construction_worker: `:construction_worker:`

:construction_worker_man: `:construction_worker_man:`

:construction_worker_woman: `:construction_worker_woman:`

:control_knobs: `:control_knobs:`

:convenience_store: `:convenience_store:`

:cook: `:cook:`

:cook_islands: `:cook_islands:`

:cookie: `:cookie:`

:cool: `:cool:`

:cop: `:cop:`

:copilot: `:copilot:`

:copyright: `:copyright:`

:coral: `:coral:`

:corn: `:corn:`

:costa_rica: `:costa_rica:`

:cote_divoire: `:cote_divoire:`

:couch_and_lamp: `:couch_and_lamp:`

:couple: `:couple:`

:couple_with_heart: `:couple_with_heart:`

:couple_with_heart_man_man: `:couple_with_heart_man_man:`

:couple_with_heart_woman_man: `:couple_with_heart_woman_man:`

:couple_with_heart_woman_woman: `:couple_with_heart_woman_woman:`

:couplekiss: `:couplekiss:`

:couplekiss_man_man: `:couplekiss_man_man:`

:couplekiss_man_woman: `:couplekiss_man_woman:`

:couplekiss_woman_woman: `:couplekiss_woman_woman:`

:cow: `:cow:`

:cow2: `:cow2:`

:cowboy_hat_face: `:cowboy_hat_face:`

:crab: `:crab:`

:crayon: `:crayon:`

:credit_card: `:credit_card:`

:crescent_moon: `:crescent_moon:`

:cricket: `:cricket:`

:cricket_game: `:cricket_game:`

:croatia: `:croatia:`

:crocodile: `:crocodile:`

:croissant: `:croissant:`

:crossed_fingers: `:crossed_fingers:`

:crossed_flags: `:crossed_flags:`

:crossed_swords: `:crossed_swords:`

:crown: `:crown:`

:crutch: `:crutch:`

:cry: `:cry:`

:crying_cat_face: `:crying_cat_face:`

:crystal_ball: `:crystal_ball:`

:cuba: `:cuba:`

:cucumber: `:cucumber:`

:cup_with_straw: `:cup_with_straw:`

:cupcake: `:cupcake:`

:cupid: `:cupid:`

:curacao: `:curacao:`

:curling_stone: `:curling_stone:`

:curly_haired_man: `:curly_haired_man:`

:curly_haired_woman: `:curly_haired_woman:`

:curly_loop: `:curly_loop:`

:currency_exchange: `:currency_exchange:`

:curry: `:curry:`

:cursing_face: `:cursing_face:`

:custard: `:custard:`

:customs: `:customs:`

:cut_of_meat: `:cut_of_meat:`

:cyclone: `:cyclone:`

:cyprus: `:cyprus:`

:czech_republic: `:czech_republic:`

:dagger: `:dagger:`

:dancer: `:dancer:`

:dancers: `:dancers:`

:dancing_men: `:dancing_men:`

:dancing_women: `:dancing_women:`

:dango: `:dango:`

:dark_sunglasses: `:dark_sunglasses:`

:dart: `:dart:`

:dash: `:dash:`

:date: `:date:`

:de: `:de:`

:deaf_man: `:deaf_man:`

:deaf_person: `:deaf_person:`

:deaf_woman: `:deaf_woman:`

:deciduous_tree: `:deciduous_tree:`

:deer: `:deer:`

:denmark: `:denmark:`

:department_store: `:department_store:`

:dependabot: `:dependabot:`

:derelict_house: `:derelict_house:`

:desert: `:desert:`

:desert_island: `:desert_island:`

:desktop_computer: `:desktop_computer:`

:detective: `:detective:`

:diamond_shape_with_a_dot_inside: `:diamond_shape_with_a_dot_inside:`

:diamonds: `:diamonds:`

:diego_garcia: `:diego_garcia:`

:disappointed: `:disappointed:`

:disappointed_relieved: `:disappointed_relieved:`

:disguised_face: `:disguised_face:`

:diving_mask: `:diving_mask:`

:diya_lamp: `:diya_lamp:`

:dizzy: `:dizzy:`

:dizzy_face: `:dizzy_face:`

:djibouti: `:djibouti:`

:dna: `:dna:`

:do_not_litter: `:do_not_litter:`

:dodo: `:dodo:`

:dog: `:dog:`

:dog2: `:dog2:`

:dollar: `:dollar:`

:dolls: `:dolls:`

:dolphin: `:dolphin:`

:dominica: `:dominica:`

:dominican_republic: `:dominican_republic:`

:donkey: `:donkey:`

:door: `:door:`

:dotted_line_face: `:dotted_line_face:`

:doughnut: `:doughnut:`

:dove: `:dove:`

:dragon: `:dragon:`

:dragon_face: `:dragon_face:`

:dress: `:dress:`

:dromedary_camel: `:dromedary_camel:`

:drooling_face: `:drooling_face:`

:drop_of_blood: `:drop_of_blood:`

:droplet: `:droplet:`

:drum: `:drum:`

:duck: `:duck:`

:dumpling: `:dumpling:`

:dvd: `:dvd:`

:e-mail: `:e-mail:`

:eagle: `:eagle:`

:ear: `:ear:`

:ear_of_rice: `:ear_of_rice:`

:ear_with_hearing_aid: `:ear_with_hearing_aid:`

:earth_africa: `:earth_africa:`

:earth_americas: `:earth_americas:`

:earth_asia: `:earth_asia:`

:ecuador: `:ecuador:`

:egg: `:egg:`

:eggplant: `:eggplant:`

:egypt: `:egypt:`

:eight: `:eight:`

:eight_pointed_black_star: `:eight_pointed_black_star:`

:eight_spoked_asterisk: `:eight_spoked_asterisk:`

:eject_button: `:eject_button:`

:el_salvador: `:el_salvador:`

:electric_plug: `:electric_plug:`

:electron: `:electron:`

:elephant: `:elephant:`

:elevator: `:elevator:`

:elf: `:elf:`

:elf_man: `:elf_man:`

:elf_woman: `:elf_woman:`

:email: `:email:`

:empty_nest: `:empty_nest:`

:end: `:end:`

:england: `:england:`

:envelope: `:envelope:`

:envelope_with_arrow: `:envelope_with_arrow:`

:equatorial_guinea: `:equatorial_guinea:`

:eritrea: `:eritrea:`

:es: `:es:`

:estonia: `:estonia:`

:ethiopia: `:ethiopia:`

:eu: `:eu:`

:euro: `:euro:`

:european_castle: `:european_castle:`

:european_post_office: `:european_post_office:`

:european_union: `:european_union:`

:evergreen_tree: `:evergreen_tree:`

:exclamation: `:exclamation:`

:exploding_head: `:exploding_head:`

:expressionless: `:expressionless:`

:eye: `:eye:`

:eye_speech_bubble: `:eye_speech_bubble:`

:eyeglasses: `:eyeglasses:`

:eyes: `:eyes:`

:face_exhaling: `:face_exhaling:`

:face_holding_back_tears: `:face_holding_back_tears:`

:face_in_clouds: `:face_in_clouds:`

:face_with_diagonal_mouth: `:face_with_diagonal_mouth:`

:face_with_head_bandage: `:face_with_head_bandage:`

:face_with_open_eyes_and_hand_over_mouth: `:face_with_open_eyes_and_hand_over_mouth:`

:face_with_peeking_eye: `:face_with_peeking_eye:`

:face_with_spiral_eyes: `:face_with_spiral_eyes:`

:face_with_thermometer: `:face_with_thermometer:`

:facepalm: `:facepalm:`

:facepunch: `:facepunch:`

:factory: `:factory:`

:factory_worker: `:factory_worker:`

:fairy: `:fairy:`

:fairy_man: `:fairy_man:`

:fairy_woman: `:fairy_woman:`

:falafel: `:falafel:`

:falkland_islands: `:falkland_islands:`

:fallen_leaf: `:fallen_leaf:`

:family: `:family:`

:family_man_boy: `:family_man_boy:`

:family_man_boy_boy: `:family_man_boy_boy:`

:family_man_girl: `:family_man_girl:`

:family_man_girl_boy: `:family_man_girl_boy:`

:family_man_girl_girl: `:family_man_girl_girl:`

:family_man_man_boy: `:family_man_man_boy:`

:family_man_man_boy_boy: `:family_man_man_boy_boy:`

:family_man_man_girl: `:family_man_man_girl:`

:family_man_man_girl_boy: `:family_man_man_girl_boy:`

:family_man_man_girl_girl: `:family_man_man_girl_girl:`

:family_man_woman_boy: `:family_man_woman_boy:`

:family_man_woman_boy_boy: `:family_man_woman_boy_boy:`

:family_man_woman_girl: `:family_man_woman_girl:`

:family_man_woman_girl_boy: `:family_man_woman_girl_boy:`

:family_man_woman_girl_girl: `:family_man_woman_girl_girl:`

:family_woman_boy: `:family_woman_boy:`

:family_woman_boy_boy: `:family_woman_boy_boy:`

:family_woman_girl: `:family_woman_girl:`

:family_woman_girl_boy: `:family_woman_girl_boy:`

:family_woman_girl_girl: `:family_woman_girl_girl:`

:family_woman_woman_boy: `:family_woman_woman_boy:`

:family_woman_woman_boy_boy: `:family_woman_woman_boy_boy:`

:family_woman_woman_girl: `:family_woman_woman_girl:`

:family_woman_woman_girl_boy: `:family_woman_woman_girl_boy:`

:family_woman_woman_girl_girl: `:family_woman_woman_girl_girl:`

:farmer: `:farmer:`

:faroe_islands: `:faroe_islands:`

:fast_forward: `:fast_forward:`

:fax: `:fax:`

:fearful: `:fearful:`

:feather: `:feather:`

:feelsgood: `:feelsgood:`

:feet: `:feet:`

:female_detective: `:female_detective:`

:female_sign: `:female_sign:`

:ferris_wheel: `:ferris_wheel:`

:ferry: `:ferry:`

:field_hockey: `:field_hockey:`

:fiji: `:fiji:`

:file_cabinet: `:file_cabinet:`

:file_folder: `:file_folder:`

:film_projector: `:film_projector:`

:film_strip: `:film_strip:`

:finland: `:finland:`

:finnadie: `:finnadie:`

:fire: `:fire:`

:fire_engine: `:fire_engine:`

:fire_extinguisher: `:fire_extinguisher:`

:firecracker: `:firecracker:`

:firefighter: `:firefighter:`

:fireworks: `:fireworks:`

:first_quarter_moon: `:first_quarter_moon:`

:first_quarter_moon_with_face: `:first_quarter_moon_with_face:`

:fish: `:fish:`

:fish_cake: `:fish_cake:`

:fishing_pole_and_fish: `:fishing_pole_and_fish:`

:fishsticks: `:fishsticks:`

:fist: `:fist:`

:fist_left: `:fist_left:`

:fist_oncoming: `:fist_oncoming:`

:fist_raised: `:fist_raised:`

:fist_right: `:fist_right:`

:five: `:five:`

:flags: `:flags:`

:flamingo: `:flamingo:`

:flashlight: `:flashlight:`

:flat_shoe: `:flat_shoe:`

:flatbread: `:flatbread:`

:fleur_de_lis: `:fleur_de_lis:`

:flight_arrival: `:flight_arrival:`

:flight_departure: `:flight_departure:`

:flipper: `:flipper:`

:floppy_disk: `:floppy_disk:`

:flower_playing_cards: `:flower_playing_cards:`

:flushed: `:flushed:`

:flute: `:flute:`

:fly: `:fly:`

:flying_disc: `:flying_disc:`

:flying_saucer: `:flying_saucer:`

:fog: `:fog:`

:foggy: `:foggy:`

:folding_hand_fan: `:folding_hand_fan:`

:fondue: `:fondue:`

:foot: `:foot:`

:football: `:football:`

:footprints: `:footprints:`

:fork_and_knife: `:fork_and_knife:`

:fortune_cookie: `:fortune_cookie:`

:fountain: `:fountain:`

:fountain_pen: `:fountain_pen:`

:four: `:four:`

:four_leaf_clover: `:four_leaf_clover:`

:fox_face: `:fox_face:`

:fr: `:fr:`

:framed_picture: `:framed_picture:`

:free: `:free:`

:french_guiana: `:french_guiana:`

:french_polynesia: `:french_polynesia:`

:french_southern_territories: `:french_southern_territories:`

:fried_egg: `:fried_egg:`

:fried_shrimp: `:fried_shrimp:`

:fries: `:fries:`

:frog: `:frog:`

:frowning: `:frowning:`

:frowning_face: `:frowning_face:`

:frowning_man: `:frowning_man:`

:frowning_person: `:frowning_person:`

:frowning_woman: `:frowning_woman:`

:fu: `:fu:`

:fuelpump: `:fuelpump:`

:full_moon: `:full_moon:`

:full_moon_with_face: `:full_moon_with_face:`

:funeral_urn: `:funeral_urn:`

:gabon: `:gabon:`

:gambia: `:gambia:`

:game_die: `:game_die:`

:garlic: `:garlic:`

:gb: `:gb:`

:gear: `:gear:`

:gem: `:gem:`

:gemini: `:gemini:`

:genie: `:genie:`

:genie_man: `:genie_man:`

:genie_woman: `:genie_woman:`

:georgia: `:georgia:`

:ghana: `:ghana:`

:ghost: `:ghost:`

:gibraltar: `:gibraltar:`

:gift: `:gift:`

:gift_heart: `:gift_heart:`

:ginger_root: `:ginger_root:`

:giraffe: `:giraffe:`

:girl: `:girl:`

:globe_with_meridians: `:globe_with_meridians:`

:gloves: `:gloves:`

:goal_net: `:goal_net:`

:goat: `:goat:`

:goberserk: `:goberserk:`

:godmode: `:godmode:`

:goggles: `:goggles:`

:golf: `:golf:`

:golfing: `:golfing:`

:golfing_man: `:golfing_man:`

:golfing_woman: `:golfing_woman:`

:goose: `:goose:`

:gorilla: `:gorilla:`

:grapes: `:grapes:`

:greece: `:greece:`

:green_apple: `:green_apple:`

:green_book: `:green_book:`

:green_circle: `:green_circle:`

:green_heart: `:green_heart:`

:green_salad: `:green_salad:`

:green_square: `:green_square:`

:greenland: `:greenland:`

:grenada: `:grenada:`

:grey_exclamation: `:grey_exclamation:`

:grey_heart: `:grey_heart:`

:grey_question: `:grey_question:`

:grimacing: `:grimacing:`

:grin: `:grin:`

:grinning: `:grinning:`

:guadeloupe: `:guadeloupe:`

:guam: `:guam:`

:guard: `:guard:`

:guardsman: `:guardsman:`

:guardswoman: `:guardswoman:`

:guatemala: `:guatemala:`

:guernsey: `:guernsey:`

:guide_dog: `:guide_dog:`

:guinea: `:guinea:`

:guinea_bissau: `:guinea_bissau:`

:guitar: `:guitar:`

:gun: `:gun:`

:guyana: `:guyana:`

:hair_pick: `:hair_pick:`

:haircut: `:haircut:`

:haircut_man: `:haircut_man:`

:haircut_woman: `:haircut_woman:`

:haiti: `:haiti:`

:hamburger: `:hamburger:`

:hammer: `:hammer:`

:hammer_and_pick: `:hammer_and_pick:`

:hammer_and_wrench: `:hammer_and_wrench:`

:hamsa: `:hamsa:`

:hamster: `:hamster:`

:hand: `:hand:`

:hand_over_mouth: `:hand_over_mouth:`

:hand_with_index_finger_and_thumb_crossed: `:hand_with_index_finger_and_thumb_crossed:`

:handbag: `:handbag:`

:handball_person: `:handball_person:`

:handshake: `:handshake:`

:hankey: `:hankey:`

:hash: `:hash:`

:hatched_chick: `:hatched_chick:`

:hatching_chick: `:hatching_chick:`

:headphones: `:headphones:`

:headstone: `:headstone:`

:health_worker: `:health_worker:`

:hear_no_evil: `:hear_no_evil:`

:heard_mcdonald_islands: `:heard_mcdonald_islands:`

:heart: `:heart:`

:heart_decoration: `:heart_decoration:`

:heart_eyes: `:heart_eyes:`

:heart_eyes_cat: `:heart_eyes_cat:`

:heart_hands: `:heart_hands:`

:heart_on_fire: `:heart_on_fire:`

:heartbeat: `:heartbeat:`

:heartpulse: `:heartpulse:`

:hearts: `:hearts:`

:heavy_check_mark: `:heavy_check_mark:`

:heavy_division_sign: `:heavy_division_sign:`

:heavy_dollar_sign: `:heavy_dollar_sign:`

:heavy_equals_sign: `:heavy_equals_sign:`

:heavy_exclamation_mark: `:heavy_exclamation_mark:`

:heavy_heart_exclamation: `:heavy_heart_exclamation:`

:heavy_minus_sign: `:heavy_minus_sign:`

:heavy_multiplication_x: `:heavy_multiplication_x:`

:heavy_plus_sign: `:heavy_plus_sign:`

:hedgehog: `:hedgehog:`

:helicopter: `:helicopter:`

:herb: `:herb:`

:hibiscus: `:hibiscus:`

:high_brightness: `:high_brightness:`

:high_heel: `:high_heel:`

:hiking_boot: `:hiking_boot:`

:hindu_temple: `:hindu_temple:`

:hippopotamus: `:hippopotamus:`

:hocho: `:hocho:`

:hole: `:hole:`

:honduras: `:honduras:`

:honey_pot: `:honey_pot:`

:honeybee: `:honeybee:`

:hong_kong: `:hong_kong:`

:hook: `:hook:`

:horse: `:horse:`

:horse_racing: `:horse_racing:`

:hospital: `:hospital:`

:hot_face: `:hot_face:`

:hot_pepper: `:hot_pepper:`

:hotdog: `:hotdog:`

:hotel: `:hotel:`

:hotsprings: `:hotsprings:`

:hourglass: `:hourglass:`

:hourglass_flowing_sand: `:hourglass_flowing_sand:`

:house: `:house:`

:house_with_garden: `:house_with_garden:`

:houses: `:houses:`

:hugs: `:hugs:`

:hungary: `:hungary:`

:hurtrealbad: `:hurtrealbad:`

:hushed: `:hushed:`

:hut: `:hut:`

:hyacinth: `:hyacinth:`

:ice_cream: `:ice_cream:`

:ice_cube: `:ice_cube:`

:ice_hockey: `:ice_hockey:`

:ice_skate: `:ice_skate:`

:icecream: `:icecream:`

:iceland: `:iceland:`

:id: `:id:`

:identification_card: `:identification_card:`

:ideograph_advantage: `:ideograph_advantage:`

:imp: `:imp:`

:inbox_tray: `:inbox_tray:`

:incoming_envelope: `:incoming_envelope:`

:index_pointing_at_the_viewer: `:index_pointing_at_the_viewer:`

:india: `:india:`

:indonesia: `:indonesia:`

:infinity: `:infinity:`

:information_desk_person: `:information_desk_person:`

:information_source: `:information_source:`

:innocent: `:innocent:`

:interrobang: `:interrobang:`

:iphone: `:iphone:`

:iran: `:iran:`

:iraq: `:iraq:`

:ireland: `:ireland:`

:isle_of_man: `:isle_of_man:`

:israel: `:israel:`

:it: `:it:`

:izakaya_lantern: `:izakaya_lantern:`

:jack_o_lantern: `:jack_o_lantern:`

:jamaica: `:jamaica:`

:japan: `:japan:`

:japanese_castle: `:japanese_castle:`

:japanese_goblin: `:japanese_goblin:`

:japanese_ogre: `:japanese_ogre:`

:jar: `:jar:`

:jeans: `:jeans:`

:jellyfish: `:jellyfish:`

:jersey: `:jersey:`

:jigsaw: `:jigsaw:`

:jordan: `:jordan:`

:joy: `:joy:`

:joy_cat: `:joy_cat:`

:joystick: `:joystick:`

:jp: `:jp:`

:judge: `:judge:`

:juggling_person: `:juggling_person:`

:kaaba: `:kaaba:`

:kangaroo: `:kangaroo:`

:kazakhstan: `:kazakhstan:`

:kenya: `:kenya:`

:key: `:key:`

:keyboard: `:keyboard:`

:keycap_ten: `:keycap_ten:`

:khanda: `:khanda:`

:kick_scooter: `:kick_scooter:`

:kimono: `:kimono:`

:kiribati: `:kiribati:`

:kiss: `:kiss:`

:kissing: `:kissing:`

:kissing_cat: `:kissing_cat:`

:kissing_closed_eyes: `:kissing_closed_eyes:`

:kissing_heart: `:kissing_heart:`

:kissing_smiling_eyes: `:kissing_smiling_eyes:`

:kite: `:kite:`

:kiwi_fruit: `:kiwi_fruit:`

:kneeling_man: `:kneeling_man:`

:kneeling_person: `:kneeling_person:`

:kneeling_woman: `:kneeling_woman:`

:knife: `:knife:`

:knot: `:knot:`

:koala: `:koala:`

:koko: `:koko:`

:kosovo: `:kosovo:`

:kr: `:kr:`

:kuwait: `:kuwait:`

:kyrgyzstan: `:kyrgyzstan:`

:lab_coat: `:lab_coat:`

:label: `:label:`

:lacrosse: `:lacrosse:`

:ladder: `:ladder:`

:lady_beetle: `:lady_beetle:`

:lantern: `:lantern:`

:laos: `:laos:`

:large_blue_circle: `:large_blue_circle:`

:large_blue_diamond: `:large_blue_diamond:`

:large_orange_diamond: `:large_orange_diamond:`

:last_quarter_moon: `:last_quarter_moon:`

:last_quarter_moon_with_face: `:last_quarter_moon_with_face:`

:latin_cross: `:latin_cross:`

:latvia: `:latvia:`

:laughing: `:laughing:`

:leafy_green: `:leafy_green:`

:leaves: `:leaves:`

:lebanon: `:lebanon:`

:ledger: `:ledger:`

:left_luggage: `:left_luggage:`

:left_right_arrow: `:left_right_arrow:`

:left_speech_bubble: `:left_speech_bubble:`

:leftwards_arrow_with_hook: `:leftwards_arrow_with_hook:`

:leftwards_hand: `:leftwards_hand:`

:leftwards_pushing_hand: `:leftwards_pushing_hand:`

:leg: `:leg:`

:lemon: `:lemon:`

:leo: `:leo:`

:leopard: `:leopard:`

:lesotho: `:lesotho:`

:level_slider: `:level_slider:`

:liberia: `:liberia:`

:libra: `:libra:`

:libya: `:libya:`

:liechtenstein: `:liechtenstein:`

:light_blue_heart: `:light_blue_heart:`

:light_rail: `:light_rail:`

:link: `:link:`

:lion: `:lion:`

:lips: `:lips:`

:lipstick: `:lipstick:`

:lithuania: `:lithuania:`

:lizard: `:lizard:`

:llama: `:llama:`

:lobster: `:lobster:`

:lock: `:lock:`

:lock_with_ink_pen: `:lock_with_ink_pen:`

:lollipop: `:lollipop:`

:long_drum: `:long_drum:`

:loop: `:loop:`

:lotion_bottle: `:lotion_bottle:`

:lotus: `:lotus:`

:lotus_position: `:lotus_position:`

:lotus_position_man: `:lotus_position_man:`

:lotus_position_woman: `:lotus_position_woman:`

:loud_sound: `:loud_sound:`

:loudspeaker: `:loudspeaker:`

:love_hotel: `:love_hotel:`

:love_letter: `:love_letter:`

:love_you_gesture: `:love_you_gesture:`

:low_battery: `:low_battery:`

:low_brightness: `:low_brightness:`

:luggage: `:luggage:`

:lungs: `:lungs:`

:luxembourg: `:luxembourg:`

:lying_face: `:lying_face:`

:m: `:m:`

:macau: `:macau:`

:macedonia: `:macedonia:`

:madagascar: `:madagascar:`

:mag: `:mag:`

:mag_right: `:mag_right:`

:mage: `:mage:`

:mage_man: `:mage_man:`

:mage_woman: `:mage_woman:`

:magic_wand: `:magic_wand:`

:magnet: `:magnet:`

:mahjong: `:mahjong:`

:mailbox: `:mailbox:`

:mailbox_closed: `:mailbox_closed:`

:mailbox_with_mail: `:mailbox_with_mail:`

:mailbox_with_no_mail: `:mailbox_with_no_mail:`

:malawi: `:malawi:`

:malaysia: `:malaysia:`

:maldives: `:maldives:`

:male_detective: `:male_detective:`

:male_sign: `:male_sign:`

:mali: `:mali:`

:malta: `:malta:`

:mammoth: `:mammoth:`

:man: `:man:`

:man_artist: `:man_artist:`

:man_astronaut: `:man_astronaut:`

:man_beard: `:man_beard:`

:man_cartwheeling: `:man_cartwheeling:`

:man_cook: `:man_cook:`

:man_dancing: `:man_dancing:`

:man_facepalming: `:man_facepalming:`

:man_factory_worker: `:man_factory_worker:`

:man_farmer: `:man_farmer:`

:man_feeding_baby: `:man_feeding_baby:`

:man_firefighter: `:man_firefighter:`

:man_health_worker: `:man_health_worker:`

:man_in_manual_wheelchair: `:man_in_manual_wheelchair:`

:man_in_motorized_wheelchair: `:man_in_motorized_wheelchair:`

:man_in_tuxedo: `:man_in_tuxedo:`

:man_judge: `:man_judge:`

:man_juggling: `:man_juggling:`

:man_mechanic: `:man_mechanic:`

:man_office_worker: `:man_office_worker:`

:man_pilot: `:man_pilot:`

:man_playing_handball: `:man_playing_handball:`

:man_playing_water_polo: `:man_playing_water_polo:`

:man_scientist: `:man_scientist:`

:man_shrugging: `:man_shrugging:`

:man_singer: `:man_singer:`

:man_student: `:man_student:`

:man_teacher: `:man_teacher:`

:man_technologist: `:man_technologist:`

:man_with_gua_pi_mao: `:man_with_gua_pi_mao:`

:man_with_probing_cane: `:man_with_probing_cane:`

:man_with_turban: `:man_with_turban:`

:man_with_veil: `:man_with_veil:`

:mandarin: `:mandarin:`

:mango: `:mango:`

:mans_shoe: `:mans_shoe:`

:mantelpiece_clock: `:mantelpiece_clock:`

:manual_wheelchair: `:manual_wheelchair:`

:maple_leaf: `:maple_leaf:`

:maracas: `:maracas:`

:marshall_islands: `:marshall_islands:`

:martial_arts_uniform: `:martial_arts_uniform:`

:martinique: `:martinique:`

:mask: `:mask:`

:massage: `:massage:`

:massage_man: `:massage_man:`

:massage_woman: `:massage_woman:`

:mate: `:mate:`

:mauritania: `:mauritania:`

:mauritius: `:mauritius:`

:mayotte: `:mayotte:`

:meat_on_bone: `:meat_on_bone:`

:mechanic: `:mechanic:`

:mechanical_arm: `:mechanical_arm:`

:mechanical_leg: `:mechanical_leg:`

:medal_military: `:medal_military:`

:medal_sports: `:medal_sports:`

:medical_symbol: `:medical_symbol:`

:mega: `:mega:`

:melon: `:melon:`

:melting_face: `:melting_face:`

:memo: `:memo:`

:men_wrestling: `:men_wrestling:`

:mending_heart: `:mending_heart:`

:menorah: `:menorah:`

:mens: `:mens:`

:mermaid: `:mermaid:`

:merman: `:merman:`

:merperson: `:merperson:`

:metal: `:metal:`

:metro: `:metro:`

:mexico: `:mexico:`

:microbe: `:microbe:`

:micronesia: `:micronesia:`

:microphone: `:microphone:`

:microscope: `:microscope:`

:middle_finger: `:middle_finger:`

:military_helmet: `:military_helmet:`

:milk_glass: `:milk_glass:`

:milky_way: `:milky_way:`

:minibus: `:minibus:`

:minidisc: `:minidisc:`

:mirror: `:mirror:`

:mirror_ball: `:mirror_ball:`

:mobile_phone_off: `:mobile_phone_off:`

:moldova: `:moldova:`

:monaco: `:monaco:`

:money_mouth_face: `:money_mouth_face:`

:money_with_wings: `:money_with_wings:`

:moneybag: `:moneybag:`

:mongolia: `:mongolia:`

:monkey: `:monkey:`

:monkey_face: `:monkey_face:`

:monocle_face: `:monocle_face:`

:monorail: `:monorail:`

:montenegro: `:montenegro:`

:montserrat: `:montserrat:`

:moon: `:moon:`

:moon_cake: `:moon_cake:`

:moose: `:moose:`

:morocco: `:morocco:`

:mortar_board: `:mortar_board:`

:mosque: `:mosque:`

:mosquito: `:mosquito:`

:motor_boat: `:motor_boat:`

:motor_scooter: `:motor_scooter:`

:motorcycle: `:motorcycle:`

:motorized_wheelchair: `:motorized_wheelchair:`

:motorway: `:motorway:`

:mount_fuji: `:mount_fuji:`

:mountain: `:mountain:`

:mountain_bicyclist: `:mountain_bicyclist:`

:mountain_biking_man: `:mountain_biking_man:`

:mountain_biking_woman: `:mountain_biking_woman:`

:mountain_cableway: `:mountain_cableway:`

:mountain_railway: `:mountain_railway:`

:mountain_snow: `:mountain_snow:`

:mouse: `:mouse:`

:mouse2: `:mouse2:`

:mouse_trap: `:mouse_trap:`

:movie_camera: `:movie_camera:`

:moyai: `:moyai:`

:mozambique: `:mozambique:`

:mrs_claus: `:mrs_claus:`

:muscle: `:muscle:`

:mushroom: `:mushroom:`

:musical_keyboard: `:musical_keyboard:`

:musical_note: `:musical_note:`

:musical_score: `:musical_score:`

:mute: `:mute:`

:mx_claus: `:mx_claus:`

:myanmar: `:myanmar:`

:nail_care: `:nail_care:`

:name_badge: `:name_badge:`

:namibia: `:namibia:`

:national_park: `:national_park:`

:nauru: `:nauru:`

:nauseated_face: `:nauseated_face:`

:nazar_amulet: `:nazar_amulet:`

:neckbeard: `:neckbeard:`

:necktie: `:necktie:`

:negative_squared_cross_mark: `:negative_squared_cross_mark:`

:nepal: `:nepal:`

:nerd_face: `:nerd_face:`

:nest_with_eggs: `:nest_with_eggs:`

:nesting_dolls: `:nesting_dolls:`

:netherlands: `:netherlands:`

:neutral_face: `:neutral_face:`

:new: `:new:`

:new_caledonia: `:new_caledonia:`

:new_moon: `:new_moon:`

:new_moon_with_face: `:new_moon_with_face:`

:new_zealand: `:new_zealand:`

:newspaper: `:newspaper:`

:newspaper_roll: `:newspaper_roll:`

:next_track_button: `:next_track_button:`

:ng: `:ng:`

:ng_man: `:ng_man:`

:ng_woman: `:ng_woman:`

:nicaragua: `:nicaragua:`

:niger: `:niger:`

:nigeria: `:nigeria:`

:night_with_stars: `:night_with_stars:`

:nine: `:nine:`

:ninja: `:ninja:`

:niue: `:niue:`

:no_bell: `:no_bell:`

:no_bicycles: `:no_bicycles:`

:no_entry: `:no_entry:`

:no_entry_sign: `:no_entry_sign:`

:no_good: `:no_good:`

:no_good_man: `:no_good_man:`

:no_good_woman: `:no_good_woman:`

:no_mobile_phones: `:no_mobile_phones:`

:no_mouth: `:no_mouth:`

:no_pedestrians: `:no_pedestrians:`

:no_smoking: `:no_smoking:`

:non-potable_water: `:non-potable_water:`

:norfolk_island: `:norfolk_island:`

:north_korea: `:north_korea:`

:northern_mariana_islands: `:northern_mariana_islands:`

:norway: `:norway:`

:nose: `:nose:`

:notebook: `:notebook:`

:notebook_with_decorative_cover: `:notebook_with_decorative_cover:`

:notes: `:notes:`

:nut_and_bolt: `:nut_and_bolt:`

:o: `:o:`

:o2: `:o2:`

:ocean: `:ocean:`

:octocat: `:octocat:`

:octopus: `:octopus:`

:oden: `:oden:`

:office: `:office:`

:office_worker: `:office_worker:`

:oil_drum: `:oil_drum:`

:ok: `:ok:`

:ok_hand: `:ok_hand:`

:ok_man: `:ok_man:`

:ok_person: `:ok_person:`

:ok_woman: `:ok_woman:`

:old_key: `:old_key:`

:older_adult: `:older_adult:`

:older_man: `:older_man:`

:older_woman: `:older_woman:`

:olive: `:olive:`

:om: `:om:`

:oman: `:oman:`

:on: `:on:`

:oncoming_automobile: `:oncoming_automobile:`

:oncoming_bus: `:oncoming_bus:`

:oncoming_police_car: `:oncoming_police_car:`

:oncoming_taxi: `:oncoming_taxi:`

:one: `:one:`

:one_piece_swimsuit: `:one_piece_swimsuit:`

:onion: `:onion:`

:open_book: `:open_book:`

:open_file_folder: `:open_file_folder:`

:open_hands: `:open_hands:`

:open_mouth: `:open_mouth:`

:open_umbrella: `:open_umbrella:`

:ophiuchus: `:ophiuchus:`

:orange: `:orange:`

:orange_book: `:orange_book:`

:orange_circle: `:orange_circle:`

:orange_heart: `:orange_heart:`

:orange_square: `:orange_square:`

:orangutan: `:orangutan:`

:orthodox_cross: `:orthodox_cross:`

:otter: `:otter:`

:outbox_tray: `:outbox_tray:`

:owl: `:owl:`

:ox: `:ox:`

:oyster: `:oyster:`

:package: `:package:`

:page_facing_up: `:page_facing_up:`

:page_with_curl: `:page_with_curl:`

:pager: `:pager:`

:paintbrush: `:paintbrush:`

:pakistan: `:pakistan:`

:palau: `:palau:`

:palestinian_territories: `:palestinian_territories:`

:palm_down_hand: `:palm_down_hand:`

:palm_tree: `:palm_tree:`

:palm_up_hand: `:palm_up_hand:`

:palms_up_together: `:palms_up_together:`

:panama: `:panama:`

:pancakes: `:pancakes:`

:panda_face: `:panda_face:`

:paperclip: `:paperclip:`

:paperclips: `:paperclips:`

:papua_new_guinea: `:papua_new_guinea:`

:parachute: `:parachute:`

:paraguay: `:paraguay:`

:parasol_on_ground: `:parasol_on_ground:`

:parking: `:parking:`

:parrot: `:parrot:`

:part_alternation_mark: `:part_alternation_mark:`

:partly_sunny: `:partly_sunny:`

:partying_face: `:partying_face:`

:passenger_ship: `:passenger_ship:`

:passport_control: `:passport_control:`

:pause_button: `:pause_button:`

:paw_prints: `:paw_prints:`

:pea_pod: `:pea_pod:`

:peace_symbol: `:peace_symbol:`

:peach: `:peach:`

:peacock: `:peacock:`

:peanuts: `:peanuts:`

:pear: `:pear:`

:pen: `:pen:`

:pencil: `:pencil:`

:pencil2: `:pencil2:`

:penguin: `:penguin:`

:pensive: `:pensive:`

:people_holding_hands: `:people_holding_hands:`

:people_hugging: `:people_hugging:`

:performing_arts: `:performing_arts:`

:persevere: `:persevere:`

:person_bald: `:person_bald:`

:person_curly_hair: `:person_curly_hair:`

:person_feeding_baby: `:person_feeding_baby:`

:person_fencing: `:person_fencing:`

:person_in_manual_wheelchair: `:person_in_manual_wheelchair:`

:person_in_motorized_wheelchair: `:person_in_motorized_wheelchair:`

:person_in_tuxedo: `:person_in_tuxedo:`

:person_red_hair: `:person_red_hair:`

:person_white_hair: `:person_white_hair:`

:person_with_crown: `:person_with_crown:`

:person_with_probing_cane: `:person_with_probing_cane:`

:person_with_turban: `:person_with_turban:`

:person_with_veil: `:person_with_veil:`

:peru: `:peru:`

:petri_dish: `:petri_dish:`

:philippines: `:philippines:`

:phone: `:phone:`

:pick: `:pick:`

:pickup_truck: `:pickup_truck:`

:pie: `:pie:`

:pig: `:pig:`

:pig2: `:pig2:`

:pig_nose: `:pig_nose:`

:pill: `:pill:`

:pilot: `:pilot:`

:pinata: `:pinata:`

:pinched_fingers: `:pinched_fingers:`

:pinching_hand: `:pinching_hand:`

:pineapple: `:pineapple:`

:ping_pong: `:ping_pong:`

:pink_heart: `:pink_heart:`

:pirate_flag: `:pirate_flag:`

:pisces: `:pisces:`

:pitcairn_islands: `:pitcairn_islands:`

:pizza: `:pizza:`

:placard: `:placard:`

:place_of_worship: `:place_of_worship:`

:plate_with_cutlery: `:plate_with_cutlery:`

:play_or_pause_button: `:play_or_pause_button:`

:playground_slide: `:playground_slide:`

:pleading_face: `:pleading_face:`

:plunger: `:plunger:`

:point_down: `:point_down:`

:point_left: `:point_left:`

:point_right: `:point_right:`

:point_up: `:point_up:`

:point_up_2: `:point_up_2:`

:poland: `:poland:`

:polar_bear: `:polar_bear:`

:police_car: `:police_car:`

:police_officer: `:police_officer:`

:policeman: `:policeman:`

:policewoman: `:policewoman:`

:poodle: `:poodle:`

:poop: `:poop:`

:popcorn: `:popcorn:`

:portugal: `:portugal:`

:post_office: `:post_office:`

:postal_horn: `:postal_horn:`

:postbox: `:postbox:`

:potable_water: `:potable_water:`

:potato: `:potato:`

:potted_plant: `:potted_plant:`

:pouch: `:pouch:`

:poultry_leg: `:poultry_leg:`

:pound: `:pound:`

:pouring_liquid: `:pouring_liquid:`

:pout: `:pout:`

:pouting_cat: `:pouting_cat:`

:pouting_face: `:pouting_face:`

:pouting_man: `:pouting_man:`

:pouting_woman: `:pouting_woman:`

:pray: `:pray:`

:prayer_beads: `:prayer_beads:`

:pregnant_man: `:pregnant_man:`

:pregnant_person: `:pregnant_person:`

:pregnant_woman: `:pregnant_woman:`

:pretzel: `:pretzel:`

:previous_track_button: `:previous_track_button:`

:prince: `:prince:`

:princess: `:princess:`

:printer: `:printer:`

:probing_cane: `:probing_cane:`

:puerto_rico: `:puerto_rico:`

:punch: `:punch:`

:purple_circle: `:purple_circle:`

:purple_heart: `:purple_heart:`

:purple_square: `:purple_square:`

:purse: `:purse:`

:pushpin: `:pushpin:`

:put_litter_in_its_place: `:put_litter_in_its_place:`

:qatar: `:qatar:`

:question: `:question:`

:rabbit: `:rabbit:`

:rabbit2: `:rabbit2:`

:raccoon: `:raccoon:`

:racehorse: `:racehorse:`

:racing_car: `:racing_car:`

:radio: `:radio:`

:radio_button: `:radio_button:`

:radioactive: `:radioactive:`

:rage: `:rage:`

:rage1: `:rage1:`

:rage2: `:rage2:`

:rage3: `:rage3:`

:rage4: `:rage4:`

:railway_car: `:railway_car:`

:railway_track: `:railway_track:`

:rainbow: `:rainbow:`

:rainbow_flag: `:rainbow_flag:`

:raised_back_of_hand: `:raised_back_of_hand:`

:raised_eyebrow: `:raised_eyebrow:`

:raised_hand: `:raised_hand:`

:raised_hand_with_fingers_splayed: `:raised_hand_with_fingers_splayed:`

:raised_hands: `:raised_hands:`

:raising_hand: `:raising_hand:`

:raising_hand_man: `:raising_hand_man:`

:raising_hand_woman: `:raising_hand_woman:`

:ram: `:ram:`

:ramen: `:ramen:`

:rat: `:rat:`

:razor: `:razor:`

:receipt: `:receipt:`

:record_button: `:record_button:`

:recycle: `:recycle:`

:red_car: `:red_car:`

:red_circle: `:red_circle:`

:red_envelope: `:red_envelope:`

:red_haired_man: `:red_haired_man:`

:red_haired_woman: `:red_haired_woman:`

:red_square: `:red_square:`

:registered: `:registered:`

:relaxed: `:relaxed:`

:relieved: `:relieved:`

:reminder_ribbon: `:reminder_ribbon:`

:repeat: `:repeat:`

:repeat_one: `:repeat_one:`

:rescue_worker_helmet: `:rescue_worker_helmet:`

:restroom: `:restroom:`

:reunion: `:reunion:`

:revolving_hearts: `:revolving_hearts:`

:rewind: `:rewind:`

:rhinoceros: `:rhinoceros:`

:ribbon: `:ribbon:`

:rice: `:rice:`

:rice_ball: `:rice_ball:`

:rice_cracker: `:rice_cracker:`

:rice_scene: `:rice_scene:`

:right_anger_bubble: `:right_anger_bubble:`

:rightwards_hand: `:rightwards_hand:`

:rightwards_pushing_hand: `:rightwards_pushing_hand:`

:ring: `:ring:`

:ring_buoy: `:ring_buoy:`

:ringed_planet: `:ringed_planet:`

:robot: `:robot:`

:rock: `:rock:`

:rocket: `:rocket:`

:rofl: `:rofl:`

:roll_eyes: `:roll_eyes:`

:roll_of_paper: `:roll_of_paper:`

:roller_coaster: `:roller_coaster:`

:roller_skate: `:roller_skate:`

:romania: `:romania:`

:rooster: `:rooster:`

:rose: `:rose:`

:rosette: `:rosette:`

:rotating_light: `:rotating_light:`

:round_pushpin: `:round_pushpin:`

:rowboat: `:rowboat:`

:rowing_man: `:rowing_man:`

:rowing_woman: `:rowing_woman:`

:ru: `:ru:`

:rugby_football: `:rugby_football:`

:runner: `:runner:`

:running: `:running:`

:running_man: `:running_man:`

:running_shirt_with_sash: `:running_shirt_with_sash:`

:running_woman: `:running_woman:`

:rwanda: `:rwanda:`

:sa: `:sa:`

:safety_pin: `:safety_pin:`

:safety_vest: `:safety_vest:`

:sagittarius: `:sagittarius:`

:sailboat: `:sailboat:`

:sake: `:sake:`

:salt: `:salt:`

:saluting_face: `:saluting_face:`

:samoa: `:samoa:`

:san_marino: `:san_marino:`

:sandal: `:sandal:`

:sandwich: `:sandwich:`

:santa: `:santa:`

:sao_tome_principe: `:sao_tome_principe:`

:sari: `:sari:`

:sassy_man: `:sassy_man:`

:sassy_woman: `:sassy_woman:`

:satellite: `:satellite:`

:satisfied: `:satisfied:`

:saudi_arabia: `:saudi_arabia:`

:sauna_man: `:sauna_man:`

:sauna_person: `:sauna_person:`

:sauna_woman: `:sauna_woman:`

:sauropod: `:sauropod:`

:saxophone: `:saxophone:`

:scarf: `:scarf:`

:school: `:school:`

:school_satchel: `:school_satchel:`

:scientist: `:scientist:`

:scissors: `:scissors:`

:scorpion: `:scorpion:`

:scorpius: `:scorpius:`

:scotland: `:scotland:`

:scream: `:scream:`

:scream_cat: `:scream_cat:`

:screwdriver: `:screwdriver:`

:scroll: `:scroll:`

:seal: `:seal:`

:seat: `:seat:`

:secret: `:secret:`

:see_no_evil: `:see_no_evil:`

:seedling: `:seedling:`

:selfie: `:selfie:`

:senegal: `:senegal:`

:serbia: `:serbia:`

:service_dog: `:service_dog:`

:seven: `:seven:`

:sewing_needle: `:sewing_needle:`

:seychelles: `:seychelles:`

:shaking_face: `:shaking_face:`

:shallow_pan_of_food: `:shallow_pan_of_food:`

:shamrock: `:shamrock:`

:shark: `:shark:`

:shaved_ice: `:shaved_ice:`

:sheep: `:sheep:`

:shell: `:shell:`

:shield: `:shield:`

:shinto_shrine: `:shinto_shrine:`

:ship: `:ship:`

:shipit: `:shipit:`

:shirt: `:shirt:`

:shit: `:shit:`

:shoe: `:shoe:`

:shopping: `:shopping:`

:shopping_cart: `:shopping_cart:`

:shorts: `:shorts:`

:shower: `:shower:`

:shrimp: `:shrimp:`

:shrug: `:shrug:`

:shushing_face: `:shushing_face:`

:sierra_leone: `:sierra_leone:`

:signal_strength: `:signal_strength:`

:singapore: `:singapore:`

:singer: `:singer:`

:sint_maarten: `:sint_maarten:`

:six: `:six:`

:six_pointed_star: `:six_pointed_star:`

:skateboard: `:skateboard:`

:ski: `:ski:`

:skier: `:skier:`

:skull: `:skull:`

:skull_and_crossbones: `:skull_and_crossbones:`

:skunk: `:skunk:`

:sled: `:sled:`

:sleeping: `:sleeping:`

:sleeping_bed: `:sleeping_bed:`

:sleepy: `:sleepy:`

:slightly_frowning_face: `:slightly_frowning_face:`

:slightly_smiling_face: `:slightly_smiling_face:`

:slot_machine: `:slot_machine:`

:sloth: `:sloth:`

:slovakia: `:slovakia:`

:slovenia: `:slovenia:`

:small_airplane: `:small_airplane:`

:small_blue_diamond: `:small_blue_diamond:`

:small_orange_diamond: `:small_orange_diamond:`

:small_red_triangle: `:small_red_triangle:`

:small_red_triangle_down: `:small_red_triangle_down:`

:smile: `:smile:`

:smile_cat: `:smile_cat:`

:smiley: `:smiley:`

:smiley_cat: `:smiley_cat:`

:smiling_face_with_tear: `:smiling_face_with_tear:`

:smiling_face_with_three_hearts: `:smiling_face_with_three_hearts:`

:smiling_imp: `:smiling_imp:`

:smirk: `:smirk:`

:smirk_cat: `:smirk_cat:`

:smoking: `:smoking:`

:snail: `:snail:`

:snake: `:snake:`

:sneezing_face: `:sneezing_face:`

:snowboarder: `:snowboarder:`

:snowflake: `:snowflake:`

:snowman: `:snowman:`

:snowman_with_snow: `:snowman_with_snow:`

:soap: `:soap:`

:sob: `:sob:`

:soccer: `:soccer:`

:socks: `:socks:`

:softball: `:softball:`

:solomon_islands: `:solomon_islands:`

:somalia: `:somalia:`

:soon: `:soon:`

:sos: `:sos:`

:sound: `:sound:`

:south_africa: `:south_africa:`

:south_georgia_south_sandwich_islands: `:south_georgia_south_sandwich_islands:`

:south_sudan: `:south_sudan:`

:space_invader: `:space_invader:`

:spades: `:spades:`

:spaghetti: `:spaghetti:`

:sparkle: `:sparkle:`

:sparkler: `:sparkler:`

:sparkles: `:sparkles:`

:sparkling_heart: `:sparkling_heart:`

:speak_no_evil: `:speak_no_evil:`

:speaker: `:speaker:`

:speaking_head: `:speaking_head:`

:speech_balloon: `:speech_balloon:`

:speedboat: `:speedboat:`

:spider: `:spider:`

:spider_web: `:spider_web:`

:spiral_calendar: `:spiral_calendar:`

:spiral_notepad: `:spiral_notepad:`

:sponge: `:sponge:`

:spoon: `:spoon:`

:squid: `:squid:`

:sri_lanka: `:sri_lanka:`

:st_barthelemy: `:st_barthelemy:`

:st_helena: `:st_helena:`

:st_kitts_nevis: `:st_kitts_nevis:`

:st_lucia: `:st_lucia:`

:st_martin: `:st_martin:`

:st_pierre_miquelon: `:st_pierre_miquelon:`

:st_vincent_grenadines: `:st_vincent_grenadines:`

:stadium: `:stadium:`

:standing_man: `:standing_man:`

:standing_person: `:standing_person:`

:standing_woman: `:standing_woman:`

:star: `:star:`

:star2: `:star2:`

:star_and_crescent: `:star_and_crescent:`

:star_of_david: `:star_of_david:`

:star_struck: `:star_struck:`

:stars: `:stars:`

:station: `:station:`

:statue_of_liberty: `:statue_of_liberty:`

:steam_locomotive: `:steam_locomotive:`

:stethoscope: `:stethoscope:`

:stew: `:stew:`

:stop_button: `:stop_button:`

:stop_sign: `:stop_sign:`

:stopwatch: `:stopwatch:`

:straight_ruler: `:straight_ruler:`

:strawberry: `:strawberry:`

:stuck_out_tongue: `:stuck_out_tongue:`

:stuck_out_tongue_closed_eyes: `:stuck_out_tongue_closed_eyes:`

:stuck_out_tongue_winking_eye: `:stuck_out_tongue_winking_eye:`

:student: `:student:`

:studio_microphone: `:studio_microphone:`

:stuffed_flatbread: `:stuffed_flatbread:`

:sudan: `:sudan:`

:sun_behind_large_cloud: `:sun_behind_large_cloud:`

:sun_behind_rain_cloud: `:sun_behind_rain_cloud:`

:sun_behind_small_cloud: `:sun_behind_small_cloud:`

:sun_with_face: `:sun_with_face:`

:sunflower: `:sunflower:`

:sunglasses: `:sunglasses:`

:sunny: `:sunny:`

:sunrise: `:sunrise:`

:sunrise_over_mountains: `:sunrise_over_mountains:`

:superhero: `:superhero:`

:superhero_man: `:superhero_man:`

:superhero_woman: `:superhero_woman:`

:supervillain: `:supervillain:`

:supervillain_man: `:supervillain_man:`

:supervillain_woman: `:supervillain_woman:`

:surfer: `:surfer:`

:surfing_man: `:surfing_man:`

:surfing_woman: `:surfing_woman:`

:suriname: `:suriname:`

:sushi: `:sushi:`

:suspect: `:suspect:`

:suspension_railway: `:suspension_railway:`

:svalbard_jan_mayen: `:svalbard_jan_mayen:`

:swan: `:swan:`

:swaziland: `:swaziland:`

:sweat: `:sweat:`

:sweat_drops: `:sweat_drops:`

:sweat_smile: `:sweat_smile:`

:sweden: `:sweden:`

:sweet_potato: `:sweet_potato:`

:swim_brief: `:swim_brief:`

:swimmer: `:swimmer:`

:swimming_man: `:swimming_man:`

:swimming_woman: `:swimming_woman:`

:switzerland: `:switzerland:`

:symbols: `:symbols:`

:synagogue: `:synagogue:`

:syria: `:syria:`

:syringe: `:syringe:`

:t-rex: `:t-rex:`

:taco: `:taco:`

:tada: `:tada:`

:taiwan: `:taiwan:`

:tajikistan: `:tajikistan:`

:takeout_box: `:takeout_box:`

:tamale: `:tamale:`

:tanabata_tree: `:tanabata_tree:`

:tangerine: `:tangerine:`

:tanzania: `:tanzania:`

:taurus: `:taurus:`

:taxi: `:taxi:`

:tea: `:tea:`

:teacher: `:teacher:`

:teapot: `:teapot:`

:technologist: `:technologist:`

:teddy_bear: `:teddy_bear:`

:telephone: `:telephone:`

:telephone_receiver: `:telephone_receiver:`

:telescope: `:telescope:`

:tennis: `:tennis:`

:tent: `:tent:`

:test_tube: `:test_tube:`

:thailand: `:thailand:`

:thermometer: `:thermometer:`

:thinking: `:thinking:`

:thong_sandal: `:thong_sandal:`

:thought_balloon: `:thought_balloon:`

:thread: `:thread:`

:three: `:three:`

:thumbsdown: `:thumbsdown:`

:thumbsup: `:thumbsup:`

:ticket: `:ticket:`

:tickets: `:tickets:`

:tiger: `:tiger:`

:tiger2: `:tiger2:`

:timer_clock: `:timer_clock:`

:timor_leste: `:timor_leste:`

:tipping_hand_man: `:tipping_hand_man:`

:tipping_hand_person: `:tipping_hand_person:`

:tipping_hand_woman: `:tipping_hand_woman:`

:tired_face: `:tired_face:`

:tm: `:tm:`

:togo: `:togo:`

:toilet: `:toilet:`

:tokelau: `:tokelau:`

:tokyo_tower: `:tokyo_tower:`

:tomato: `:tomato:`

:tonga: `:tonga:`

:tongue: `:tongue:`

:toolbox: `:toolbox:`

:tooth: `:tooth:`

:toothbrush: `:toothbrush:`

:top: `:top:`

:tophat: `:tophat:`

:tornado: `:tornado:`

:tr: `:tr:`

:trackball: `:trackball:`

:tractor: `:tractor:`

:traffic_light: `:traffic_light:`

:train: `:train:`

:train2: `:train2:`

:tram: `:tram:`

:transgender_flag: `:transgender_flag:`

:transgender_symbol: `:transgender_symbol:`

:triangular_flag_on_post: `:triangular_flag_on_post:`

:triangular_ruler: `:triangular_ruler:`

:trident: `:trident:`

:trinidad_tobago: `:trinidad_tobago:`

:tristan_da_cunha: `:tristan_da_cunha:`

:triumph: `:triumph:`

:troll: `:troll:`

:trolleybus: `:trolleybus:`

:trollface: `:trollface:`

:trophy: `:trophy:`

:tropical_drink: `:tropical_drink:`

:tropical_fish: `:tropical_fish:`

:truck: `:truck:`

:trumpet: `:trumpet:`

:tshirt: `:tshirt:`

:tulip: `:tulip:`

:tumbler_glass: `:tumbler_glass:`

:tunisia: `:tunisia:`

:turkey: `:turkey:`

:turkmenistan: `:turkmenistan:`

:turks_caicos_islands: `:turks_caicos_islands:`

:turtle: `:turtle:`

:tuvalu: `:tuvalu:`

:tv: `:tv:`

:twisted_rightwards_arrows: `:twisted_rightwards_arrows:`

:two: `:two:`

:two_hearts: `:two_hearts:`

:two_men_holding_hands: `:two_men_holding_hands:`

:two_women_holding_hands: `:two_women_holding_hands:`

:u5272: `:u5272:`

:u5408: `:u5408:`

:u55b6: `:u55b6:`

:u6307: `:u6307:`

:u6708: `:u6708:`

:u6709: `:u6709:`

:u6e80: `:u6e80:`

:u7121: `:u7121:`

:u7533: `:u7533:`

:u7981: `:u7981:`

:u7a7a: `:u7a7a:`

:uganda: `:uganda:`

:uk: `:uk:`

:ukraine: `:ukraine:`

:umbrella: `:umbrella:`

:unamused: `:unamused:`

:underage: `:underage:`

:unicorn: `:unicorn:`

:united_arab_emirates: `:united_arab_emirates:`

:united_nations: `:united_nations:`

:unlock: `:unlock:`

:up: `:up:`

:upside_down_face: `:upside_down_face:`

:uruguay: `:uruguay:`

:us: `:us:`

:us_outlying_islands: `:us_outlying_islands:`

:us_virgin_islands: `:us_virgin_islands:`

:uzbekistan: `:uzbekistan:`

:v: `:v:`

:vampire: `:vampire:`

:vampire_man: `:vampire_man:`

:vampire_woman: `:vampire_woman:`

:vanuatu: `:vanuatu:`

:vatican_city: `:vatican_city:`

:venezuela: `:venezuela:`

:vertical_traffic_light: `:vertical_traffic_light:`

:vhs: `:vhs:`

:vibration_mode: `:vibration_mode:`

:video_camera: `:video_camera:`

:video_game: `:video_game:`

:vietnam: `:vietnam:`

:violin: `:violin:`

:virgo: `:virgo:`

:volcano: `:volcano:`

:volleyball: `:volleyball:`

:vomiting_face: `:vomiting_face:`

:vs: `:vs:`

:vulcan_salute: `:vulcan_salute:`

:waffle: `:waffle:`

:wales: `:wales:`

:walking: `:walking:`

:walking_man: `:walking_man:`

:walking_woman: `:walking_woman:`

:wallis_futuna: `:wallis_futuna:`

:waning_crescent_moon: `:waning_crescent_moon:`

:waning_gibbous_moon: `:waning_gibbous_moon:`

:warning: `:warning:`

:wastebasket: `:wastebasket:`

:watch: `:watch:`

:water_buffalo: `:water_buffalo:`

:water_polo: `:water_polo:`

:watermelon: `:watermelon:`

:wave: `:wave:`

:wavy_dash: `:wavy_dash:`

:waxing_crescent_moon: `:waxing_crescent_moon:`

:waxing_gibbous_moon: `:waxing_gibbous_moon:`

:wc: `:wc:`

:weary: `:weary:`

:wedding: `:wedding:`

:weight_lifting: `:weight_lifting:`

:weight_lifting_man: `:weight_lifting_man:`

:weight_lifting_woman: `:weight_lifting_woman:`

:western_sahara: `:western_sahara:`

:whale: `:whale:`

:whale2: `:whale2:`

:wheel: `:wheel:`

:wheel_of_dharma: `:wheel_of_dharma:`

:wheelchair: `:wheelchair:`

:white_check_mark: `:white_check_mark:`

:white_circle: `:white_circle:`

:white_flag: `:white_flag:`

:white_flower: `:white_flower:`

:white_haired_man: `:white_haired_man:`

:white_haired_woman: `:white_haired_woman:`

:white_heart: `:white_heart:`

:white_large_square: `:white_large_square:`

:white_medium_small_square: `:white_medium_small_square:`

:white_medium_square: `:white_medium_square:`

:white_small_square: `:white_small_square:`

:white_square_button: `:white_square_button:`

:wilted_flower: `:wilted_flower:`

:wind_chime: `:wind_chime:`

:wind_face: `:wind_face:`

:window: `:window:`

:wine_glass: `:wine_glass:`

:wing: `:wing:`

:wink: `:wink:`

:wireless: `:wireless:`

:wolf: `:wolf:`

:woman: `:woman:`

:woman_artist: `:woman_artist:`

:woman_astronaut: `:woman_astronaut:`

:woman_beard: `:woman_beard:`

:woman_cartwheeling: `:woman_cartwheeling:`

:woman_cook: `:woman_cook:`

:woman_dancing: `:woman_dancing:`

:woman_facepalming: `:woman_facepalming:`

:woman_factory_worker: `:woman_factory_worker:`

:woman_farmer: `:woman_farmer:`

:woman_feeding_baby: `:woman_feeding_baby:`

:woman_firefighter: `:woman_firefighter:`

:woman_health_worker: `:woman_health_worker:`

:woman_in_manual_wheelchair: `:woman_in_manual_wheelchair:`

:woman_in_motorized_wheelchair: `:woman_in_motorized_wheelchair:`

:woman_in_tuxedo: `:woman_in_tuxedo:`

:woman_judge: `:woman_judge:`

:woman_juggling: `:woman_juggling:`

:woman_mechanic: `:woman_mechanic:`

:woman_office_worker: `:woman_office_worker:`

:woman_pilot: `:woman_pilot:`

:woman_playing_handball: `:woman_playing_handball:`

:woman_playing_water_polo: `:woman_playing_water_polo:`

:woman_scientist: `:woman_scientist:`

:woman_shrugging: `:woman_shrugging:`

:woman_singer: `:woman_singer:`

:woman_student: `:woman_student:`

:woman_teacher: `:woman_teacher:`

:woman_technologist: `:woman_technologist:`

:woman_with_headscarf: `:woman_with_headscarf:`

:woman_with_probing_cane: `:woman_with_probing_cane:`

:woman_with_turban: `:woman_with_turban:`

:woman_with_veil: `:woman_with_veil:`

:womans_clothes: `:womans_clothes:`

:womans_hat: `:womans_hat:`

:women_wrestling: `:women_wrestling:`

:womens: `:womens:`

:wood: `:wood:`

:woozy_face: `:woozy_face:`

:world_map: `:world_map:`

:worm: `:worm:`

:worried: `:worried:`

:wrench: `:wrench:`

:wrestling: `:wrestling:`

:writing_hand: `:writing_hand:`

:x: `:x:`

:x_ray: `:x_ray:`

:yarn: `:yarn:`

:yawning_face: `:yawning_face:`

:yellow_circle: `:yellow_circle:`

:yellow_heart: `:yellow_heart:`

:yellow_square: `:yellow_square:`

:yemen: `:yemen:`

:yen: `:yen:`

:yin_yang: `:yin_yang:`

:yo_yo: `:yo_yo:`

:yum: `:yum:`

:zambia: `:zambia:`

:zany_face: `:zany_face:`

:zap: `:zap:`

:zebra: `:zebra:`

:zero: `:zero:`

:zimbabwe: `:zimbabwe:`

:zipper_mouth_face: `:zipper_mouth_face:`

:zombie: `:zombie:`

:zombie_man: `:zombie_man:`

:zombie_woman: `:zombie_woman:`

:zzz: `:zzz:`

<!-- END: Auto-generated content (/build/emoji.js) -->

</div>
`````

## File: docs/helpers.md
`````markdown
# Doc helper

docsify extends Markdown syntax to make your documents more readable.

> Note: For the special code syntax cases, it's better to put them within code backticks to avoid any conflict from configurations or emojis.

## Callouts

### Important content

Important content like:

```markdown
!> **Time** is money, my friend!
```

is rendered as:

!> **Time** is money, my friend!

### Tips

General tips like:

```markdown
?> _TODO_ unit test
```

are rendered as:

?> _TODO_ unit test

## Link attributes

### disabled

```md
[link](/demo ':disabled')
```

### href

Sometimes we will use some other relative path for the link, and we have to tell docsify that we don't need to compile this link. For example:

```md
[link](/demo/)
```

It will be compiled to `<a href="/#/demo/">link</a>` and will load `/demo/README.md`. Maybe you want to jump to `/demo/index.html`.

Now you can do that

```md
[link](/demo/ ':ignore')
```

You will get `<a href="/demo/">link</a>`html. Do not worry, you can still set the title for the link.

```md
[link](/demo/ ':ignore title')

<a href="/demo/" title="title">link</a>
```

### target

```md
[link](/demo ':target=_blank')
[link](/demo2 ':target=_self')
```

## Task lists

```md
- [ ] foo
- bar
- [x] baz
- [] bam <~ not working
  - [ ] bim
  - [ ] lim
```

- [ ] foo
- bar
- [x] baz
- [] bam <~ not working
  - [ ] bim
  - [ ] lim

## Images

### Class names

```md
![logo](https://docsify.js.org/_media/icon.svg ':class=someCssClass')
```

### IDs

```md
![logo](https://docsify.js.org/_media/icon.svg ':id=someCssId')
```

### Sizes

```md
![logo](https://docsify.js.org/_media/icon.svg ':size=WIDTHxHEIGHT')
![logo](https://docsify.js.org/_media/icon.svg ':size=50x100')
![logo](https://docsify.js.org/_media/icon.svg ':size=100')

<!-- Support percentage -->

![logo](https://docsify.js.org/_media/icon.svg ':size=10%')
```

![logo](https://docsify.js.org/_media/icon.svg ':size=50x100')
![logo](https://docsify.js.org/_media/icon.svg ':size=100')
![logo](https://docsify.js.org/_media/icon.svg ':size=10%')

## Heading IDs

```md
### Hello, world! :id=hello-world
```

## Markdown + HTML

You need to insert a space between the html and markdown content.
This is useful for rendering markdown content in the details element.

```markdown
<details>
<summary>Self-assessment (Click to expand)</summary>

- Abc
- Abc

</details>
```

<details>
<summary>Self-assessment (Click to expand)</summary>

- Abc
- Abc

</details>

Markdown content can also be wrapped in html tags.

```markdown
<div style='color: red'>

- listitem
- listitem
- listitem

</div>
```

<div style='color: red'>

- listitem
- listitem
- listitem

</div>
`````

## File: docs/language-highlight.md
`````markdown
# Language highlighting

## Prism

Docsify uses [Prism](https://prismjs.com) for syntax highlighting within code blocks. Prism supports the following languages by default (additional [language support](#language-support) also available):

- Markup: HTML, XML, SVG, MathML, SSML, Atom, RSS
- CSS
- C-like
- JavaScript

To enable syntax highlighting, create a markdown codeblock using backticks (` ``` `) with a [language](https://prismjs.com/#supported-languages) specified on the first line (e.g., `html`, `css`, `js`):

````text
```html
<p>This is a paragraph</p>
<a href="//docsify.js.org/">Docsify</a>
```
````

````text
```css
p {
  color: red;
}
```
````

````text
```js
function add(a, b) {
  return a + b;
}
```
````

The above markdown will be rendered as:

```html
<p>This is a paragraph</p>
<a href="//docsify.js.org/">Docsify</a>
```

```css
p {
  color: red;
}
```

```js
function add(a, b) {
  return a + b;
}
```

## Language support

Support for additional [languages](https://prismjs.com/#supported-languages) is available by loading the Prism [grammar files](https://cdn.jsdelivr.net/npm/prismjs@1/components/):

!> Prism grammar files must be loaded after Docsify.

```html
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-bash.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-docker.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-git.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-java.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-jsx.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-markdown.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-php.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-rust.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-sql.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-swift.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-typescript.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/prismjs@1/components/prism-yaml.min.js"></script>
```

## Theme support

Docsify's official [themes](themes) are compatible with Prism syntax highlighting themes.

!> Prism themes must be loaded after Docsify themes.

```html
<!-- Light and dark mode -->
<link
  rel="stylesheet"
  href="//cdn.jsdelivr.net/npm/prism-themes@1/themes/prism-one-light.min.css"
/>
```

Themes can be applied in light and/or dark mode

```html
<!-- Dark mode only -->
<link
  rel="stylesheet"
  media="(prefers-color-scheme: dark)"
  href="//cdn.jsdelivr.net/npm/prism-themes@1/themes/prism-one-dark.min.css"
/>

<!-- Light mode only -->
<link
  rel="stylesheet"
  media="(prefers-color-scheme: light)"
  href="//cdn.jsdelivr.net/npm/prism-themes@1/themes/prism-one-light.min.css"
/>
```

The following Docsify [theme properties](themes#theme-properties) will override Prism theme styles by default:

```text
--border-radius
--font-family-mono
--font-size-mono
```

To use the values specified in the Prism theme, set the desired theme property to `unset`:

<!-- prettier-ignore -->
```html
<style>
  :root {
    --border-radius   : unset;
    --font-family-mono: unset;
    --font-size-mono  : unset;
  }
</style>
```

## Dynamic content

Dynamically generated Code blocks can be highlighted using Prism's [`highlightElement()`](https://prismjs.com/docs/Prism.html#.highlightElement) method:

```js
const code = document.createElement('code');
code.innerHTML = "console.log('Hello World!')";
code.setAttribute('class', 'language-javascript');
Prism.highlightElement(code);
```
`````

## File: docs/markdown.md
`````markdown
# Markdown configuration

**docsify** uses [marked](https://github.com/markedjs/marked) as its Markdown parser. You can customize how it renders your Markdown content to HTML by customizing `renderer`:

```js
window.$docsify = {
  markdown: {
    smartypants: true,
    renderer: {
      link() {
        // ...
      },
    },
  },
};
```

?> Configuration Options Reference: [marked documentation](https://marked.js.org/#/USING_ADVANCED.md)

You can completely customize the parsing rules.

```js
window.$docsify = {
  markdown(marked, renderer) {
    // ...

    return marked;
  },
};
```

## Supports mermaid

!> Currently, docsify doesn't support the async mermaid render (the latest mermaid version supported is `v9.3.0`).

```js
//  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.css">
//  <script src="//cdn.jsdelivr.net/npm/mermaid@9.3.0/dist/mermaid.min.js"></script>

let num = 0;
mermaid.initialize({ startOnLoad: false });

window.$docsify = {
  markdown: {
    renderer: {
      code({ text, lang }) {
        if (lang === 'mermaid') {
          return /* html */ `
            <div class="mermaid">${mermaid.render(
              'mermaid-svg-' + num++,
              text,
            )}</div>
          `;
        }
        return this.origin.code.apply(this, arguments);
      },
    },
  },
};
```
`````

## File: docs/plugins.md
`````markdown
# List of Plugins

## Full text search

By default, the hyperlink on the current page is recognized and the content is saved in `IndexedDB`. You can also specify the path to the files.

<!-- prettier-ignore -->
```html
<script>
  window.$docsify = {
    search: 'auto', // default

    search: [
      '/',            // => /README.md
      '/guide',       // => /guide.md
      '/get-started', // => /get-started.md
      '/zh-cn/',      // => /zh-cn/README.md
    ],

    // Complete configuration parameters
    search: {
      // Location in sidebar (default: prepended as first child)
      // Optionally specify insertAfter or insertBefore (not both)
      insertAfter: '.app-name', // CSS selector in .sidebar scope
      insertBefore: '.sidebar-nav', // CSS selector in .sidebar scope

      maxAge: 86400000, // Expiration time, the default one day
      paths: [], // or 'auto'
      placeholder: 'Type to search',

      // Localization
      placeholder: {
        '/zh-cn/': '搜索',
        '/': 'Type to search',
      },

      noData: 'No Results!',

      // Localization
      noData: {
        '/zh-cn/': '找不到结果',
        '/': 'No Results',
      },

      // Headline depth, 1 - 6
      depth: 2,

      hideOtherSidebarContent: true, // Deprecated as of v5

      // To avoid search index collision
      // between multiple websites under the same domain
      namespace: 'website-1',

      // Use different indexes for path prefixes (namespaces).
      // NOTE: Only works in 'auto' mode.
      //
      // When initialiazing an index, we look for the first path from the sidebar.
      // If it matches the prefix from the list, we switch to the corresponding index.
      pathNamespaces: ['/zh-cn', '/ru-ru', '/ru-ru/v1'],

      // You can provide a regexp to match prefixes. In this case,
      // the matching substring will be used to identify the index
      pathNamespaces: /^(\/(zh-cn|ru-ru))?(\/(v1|v2))?/,
    },
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/search.min.js"></script>
```

This plugin ignores diacritical marks when performing a full text search (e.g., "cafe" will also match "café").

## Google Analytics

> Google's Universal Analytics service will no longer process new data in standard properties beginning July 1, 2023. Prepare now by setting up and switching over to a Google Analytics 4 property and docsify's gtag.js plugin.

Install the plugin and configure the track id.

```html
<script>
  window.$docsify = {
    ga: 'UA-XXXXX-Y',
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/ga.min.js"></script>
```

Configure by `data-ga`.

<!-- prettier-ignore -->
```html
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js" data-ga="UA-XXXXX-Y"></script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/ga.min.js"></script>
```

## Google Analytics 4 (GA4)

Install the plugin and configure the track id.

```html
<script>
  // Single ID
  window.$docsify = {
    gtag: 'UA-XXXXX-Y',
  };

  // Multiple IDs
  window.$docsify = {
    gtag: [
      'G-XXXXXXXX', // Google Analytics 4 (GA4)
      'UA-XXXXXXXX', // Google Universal Analytics (GA3)
      'AW-XXXXXXXX', // Google Ads
      'DC-XXXXXXXX', // Floodlight
    ],
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/gtag.min.js"></script>
```

## Emoji

Renders a larger collection of emoji shorthand codes. Without this plugin, Docsify is able to render only a limited number of emoji shorthand codes.

!> Deprecated as of v4.13. Docsify no longer requires this plugin for full emoji support.

```html
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/emoji.min.js"></script>
```

## External Script

If the script on the page is an external one (imports a js file via `src` attribute), you'll need this plugin to make it work.

```html
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/external-script.min.js"></script>
```

## Zoom image

Medium's image zoom. Based on [medium-zoom](https://github.com/francoischalifour/medium-zoom).

```html
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/zoom-image.min.js"></script>
```

Exclude the special image

```markdown
![](image.png ':no-zoom')
```

## Edit on github

Add `Edit on github` button on every pages. Provided by [@njleonzhang](https://github.com/njleonzhang), see this [document](https://github.com/njleonzhang/docsify-edit-on-github)

## Demo code with instant preview and jsfiddle integration

With this plugin, sample code can be rendered on the page instantly, so that the readers can see the preview immediately.
When readers expand the demo box, the source code and description are shown there. if they click the button `Try in Jsfiddle`,
`jsfiddle.net` will be open with the code of this sample, which allow readers to revise the code and try on their own.

[Vue](https://njleonzhang.github.io/docsify-demo-box-vue/) and [React](https://njleonzhang.github.io/docsify-demo-box-react/) are both supported.

## Copy to Clipboard

Add a simple `Click to copy` button to all preformatted code blocks to effortlessly allow users to copy example code from your docs. Provided by [@jperasmus](https://github.com/jperasmus)

```html
<script src="//cdn.jsdelivr.net/npm/docsify-copy-code/dist/docsify-copy-code.min.js"></script>
```

See [here](https://github.com/jperasmus/docsify-copy-code/blob/master/README.md) for more details.

## Disqus

Disqus comments. https://disqus.com/

```html
<script>
  window.$docsify = {
    disqus: 'shortname',
  };
</script>
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/disqus.min.js"></script>
```

## Gitalk

[Gitalk](https://github.com/gitalk/gitalk) is a modern comment component based on GitHub Issue and Preact.

```html
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/gitalk/dist/gitalk.css" />

<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/gitalk.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/gitalk/dist/gitalk.min.js"></script>
<script>
  const gitalk = new Gitalk({
    clientID: 'GitHub Application Client ID',
    clientSecret: 'GitHub Application Client Secret',
    repo: 'GitHub repo',
    owner: 'GitHub repo owner',
    admin: [
      'GitHub repo collaborators, only these guys can initialize github issues',
    ],
    // facebook-like distraction free mode
    distractionFreeMode: false,
  });
</script>
```

## Pagination

Pagination for docsify. By [@imyelo](https://github.com/imyelo)

```html
<script src="//cdn.jsdelivr.net/npm/docsify@5/dist/docsify.min.js"></script>
<script src="//cdn.jsdelivr.net/npm/docsify-pagination/dist/docsify-pagination.min.js"></script>
```

Click [here](https://github.com/imyelo/docsify-pagination#readme) to get more information.

## Tabs

A docsify.js plugin for displaying tabbed content from markdown.

- [Documentation & Demos](https://jhildenbiddle.github.io/docsify-tabs)

Provided by [@jhildenbiddle](https://github.com/jhildenbiddle/docsify-tabs).

## More plugins

See [awesome-docsify](awesome?id=plugins)
`````

## File: docs/pwa.md
`````markdown
# Offline Mode

[Progressive Web Apps](https://developers.google.com/web/progressive-web-apps/) (PWA) are experiences that combine the best of the web with the best of apps. We can enhance our website with service workers to work **offline** or on low-quality networks.

It is also very easy to use.

## Create serviceWorker

Create a `sw.js` file in your project's root directory and copy the following code:

_sw.js_

```js
/* ===========================================================
 * docsify sw.js
 * ===========================================================
 * Copyright 2016 @huxpro
 * Licensed under Apache 2.0
 * Register service worker.
 * ========================================================== */

const RUNTIME = 'docsify';
const HOSTNAME_WHITELIST = [
  self.location.hostname,
  'fonts.gstatic.com',
  'fonts.googleapis.com',
  'cdn.jsdelivr.net',
];

// The Util Function to hack URLs of intercepted requests
const getFixedUrl = req => {
  const now = Date.now();
  const url = new URL(req.url);

  // 1. fixed http URL
  // Just keep syncing with location.protocol
  // fetch(httpURL) belongs to active mixed content.
  // And fetch(httpRequest) is not supported yet.
  url.protocol = self.location.protocol;

  // 2. add query for caching-busting.
  // GitHub Pages served with Cache-Control: max-age=600
  // max-age on mutable content is error-prone, with SW life of bugs can even extend.
  // Until cache mode of Fetch API landed, we have to workaround cache-busting with query string.
  // Cache-Control-Bug: https://bugs.chromium.org/p/chromium/issues/detail?id=453190
  if (url.hostname === self.location.hostname) {
    url.search += (url.search ? '&' : '?') + 'cache-bust=' + now;
  }
  return url.href;
};

/**
 *  @Lifecycle Activate
 *  New one activated when old isnt being used.
 *
 *  waitUntil(): activating ====> activated
 */
self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

/**
 *  @Functional Fetch
 *  All network requests are being intercepted here.
 *
 *  void respondWith(Promise<Response> r)
 */
self.addEventListener('fetch', event => {
  // Skip some of cross-origin requests, like those for Google Analytics.
  if (HOSTNAME_WHITELIST.indexOf(new URL(event.request.url).hostname) > -1) {
    // Stale-while-revalidate
    // similar to HTTP's stale-while-revalidate: https://www.mnot.net/blog/2007/12/12/stale
    // Upgrade from Jake's to Surma's: https://gist.github.com/surma/eb441223daaedf880801ad80006389f1
    const cached = caches.match(event.request);
    const fixedUrl = getFixedUrl(event.request);
    const fetched = fetch(fixedUrl, { cache: 'no-store' });
    const fetchedCopy = fetched.then(resp => resp.clone());

    // Call respondWith() with whatever we get first.
    // If the fetch fails (e.g disconnected), wait for the cache.
    // If there’s nothing in cache, wait for the fetch.
    // If neither yields a response, return offline pages.
    event.respondWith(
      Promise.race([fetched.catch(_ => cached), cached])
        .then(resp => resp || fetched)
        .catch(_ => {
          /* eat any errors */
        }),
    );

    // Update the cache with the version we fetched (only for ok status)
    event.waitUntil(
      Promise.all([fetchedCopy, caches.open(RUNTIME)])
        .then(
          ([response, cache]) =>
            response.ok && cache.put(event.request, response),
        )
        .catch(_ => {
          /* eat any errors */
        }),
    );
  }
});
```

## Register

Now, register it in your `index.html`. It only works on some modern browsers, so we need to check:

_index.html_

```html
<script>
  if (typeof navigator.serviceWorker !== 'undefined') {
    navigator.serviceWorker.register('sw.js');
  }
</script>
```

## Enjoy it

Release your website and start experiencing the magical offline feature.
`````

## File: docs/quickstart.md
`````markdown
# Quick start

It is recommended to install `docsify-cli` globally, which helps initializing and previewing the website locally.

```bash
npm i docsify-cli -g
```

## Initialize

If you want to write the documentation in the `./docs` subdirectory, you can use the `init` command.

```bash
docsify init ./docs
```

## Writing content

After the `init` is complete, you can see the file list in the `./docs` subdirectory.

- `index.html` as the entry file
- `README.md` as the home page
- `.nojekyll` prevents GitHub Pages from ignoring files that begin with an underscore

You can easily update the documentation in `./docs/README.md`, of course you can add [more pages](adding-pages.md).

## Preview your site

Run the local server with `docsify serve`. You can preview your site in your browser on `http://localhost:3000`.

```bash
docsify serve docs
```

?> For more use cases of `docsify-cli`, head over to the [docsify-cli documentation](https://github.com/docsifyjs/docsify-cli).

## Manual initialization

Download or create an `index.html` template using the following markup:

<div id="template">

<a href="#" class="button primary" download="index.html">Download Template</a>

<!-- prettier-ignore -->
```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

    <!-- Core Theme -->
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/themes/core.min.css">
  </head>
  <body class="loading">
    <div id="app"></div>

    <!-- Configuration -->
    <script>
      window.$docsify = {
        //...
      };
    </script>

    <!-- Docsify.js -->
    <script src="//cdn.jsdelivr.net/npm/docsify@5"></script>

    <!-- Plugins (optional) -->
    <!-- <script src="//cdn.jsdelivr.net/npm/docsify@5/dist/plugins/search.min.js"></script> -->
  </body>
</html>
```

</div>

### Specifying docsify versions

?> Note that in both of the examples below, docsify URLs will need to be manually updated when a new major version of docsify is released (e.g. `v5.x.x` => `v6.x.x`). Check the docsify website periodically to see if a new major version has been released.

Specifying a major version in the URL (`@5`) will allow your site to receive non-breaking enhancements (i.e. "minor" updates) and bug fixes (i.e. "patch" updates) automatically. This is the recommended way to load docsify resources.

<!-- prettier-ignore -->
```html
<!-- Core Theme -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/themes/core.min.css">

<!-- Docsify -->
<script src="//cdn.jsdelivr.net/npm/docsify@5"></script>
```

If you prefer to lock docsify to a specific version, specify the full version after the `@` symbol in the URL. This is the safest way to ensure your site will look and behave the same way regardless of any changes made to future versions of docsify.

<!-- prettier-ignore -->
```html
<!-- Core Theme -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5.0.0/themes/core.min.css">

<!-- Docsify -->
<script src="//cdn.jsdelivr.net/npm/docsify@5.0.0"></script>
```

### Manually preview your site

If you have Python installed on your system, you can easily use it to run a static server to preview your site.

```python
# Python 2
cd docs && python -m SimpleHTTPServer 3000
```

```python
# Python 3
cd docs && python -m http.server 3000
```

## Loading dialog

If you want, you can show a loading dialog before docsify starts to render your documentation:

```html
<!-- index.html -->

<div id="app">Please wait...</div>
```

You should set the `data-app` attribute if you changed `el`:

```html
<!-- index.html -->

<div data-app id="main">Please wait...</div>

<script>
  window.$docsify = {
    el: '#main',
  };
</script>
```

Compare [el configuration](configuration#el).

<script>
  (function() {
    const linkElm = document.querySelector('#template a[download="index.html"]');
    const codeElm = document.querySelector('#template code');
    const html = codeElm?.textContent;

    linkElm?.setAttribute('href', `data:text/plain,${html}`);
  })();
</script>
`````

## File: docs/README.md
`````markdown
# docsify

> A magical documentation site generator.

## What it is

Docsify generates your documentation website on the fly. Unlike GitBook, it does not generate static html files. Instead, it smartly loads and parses your Markdown files and displays them as a website. To start using it, all you need to do is create an `index.html` and [deploy it on GitHub Pages](deploy.md).

See the [Quick start](quickstart.md) guide for more details.

## Features

- No statically built html files
- Simple and lightweight
- Smart full-text search plugin
- Multiple themes
- Useful plugin API
- Emoji support

## Examples

Check out the [Showcase](https://github.com/docsifyjs/awesome-docsify#showcase) to see docsify in use.

## Donate

Please consider donating if you think docsify is helpful to you or that my work is valuable. I am happy if you can help me [buy a cup of coffee](https://github.com/QingWei-Li/donate). :heart:

## Community

Users and the development team are usually in the [Discord server](https://discord.gg/3NwKFyR).
`````

## File: docs/themes.md
`````markdown
# Themes

## Core theme

The Docsify "core" theme contains all of the styles and [theme properties](#theme-properties) needed to render a Docsify site. This theme is designed to serve as a minimalist theme on its own, in combination with [theme add-ons](#theme-add-ons), modified using core [classes](#classes), and as a starting point for [customization](#customization).

<!-- prettier-ignore -->
```html
<!-- Core Theme -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/dist/themes/core.min.css" />
```

## Theme add-ons

Theme add-ons are used in combination with the [core theme](#core-theme). Add-ons contain CSS rules that modify [theme properties](#theme-properties) values and/or add custom style declarations. They can often (but not always) be used with other add-ons.

!> Theme add-ons must be loaded after the [core theme](#core-theme).

<!-- prettier-ignore -->
```html
<!-- Core Theme -->
<link rel="stylesheet" href="..." />

<!-- Theme (add-on) -->
<link rel="stylesheet" href="..." />
```

### Core Dark (Add-on)

Dark mode styles for the [core theme](#core-theme). Styles can applied only when an operating system's dark mode is active by specifying a `media` attribute.

<label>
  <input
    class="toggle"
    type="checkbox"
    value="core-dark"
    data-group="addon"
    data-sheet
  >
  Preview Core Dark
</label>
<br>
<label>
  <input
    class="toggle"
    type="checkbox"
    value="core-dark-auto"
    data-group="addon"
    data-sheet
  >
  Preview Core Dark (Dark Mode Only)
</label>

<!-- prettier-ignore -->
```html
<!-- Core Dark (add-on) -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/dist/themes/addons/core-dark.min.css" />
```

<!-- prettier-ignore -->
```html
<!-- Core Dark - Dark Mode Only (add-on) -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/dist/themes/addons/core-dark.min.css" media="(prefers-color-scheme: dark)" />
```

### Vue theme (Add-on)

The popular Docsify v4 theme.

<label>
  <input
   class="toggle"
   type="checkbox"
   value="vue"
   data-group="addon"
   data-sheet
  >
  Preview Vue
</label>

<!-- prettier-ignore -->
```html
<!-- Vue Theme (add-on) -->
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/dist/themes/addons/vue.min.css" />
```

## Classes

The [core theme](#core-theme) provides several CSS classes for customizing your Docsify site. These classes should be applied to the `<body>` element within your `index.html` page.

<!-- prettier-ignore -->
```html
<body class="...">
```

### Loading

Display a loading animation while waiting for Docsify to initialize.

<!-- prettier-ignore -->
```html
<body class="loading">
```

<output data-lang="output">
  <div class="loading" style="margin: auto;"></div>
</output>

### Sidebar chevrons

Display expand/collapse icons on page links in the sidebar.

<label>
  <input class="toggle" type="checkbox" value="sidebar-chevron-right" data-class data-group="sidebar-chevron"> Preview <code>sidebar-chevron-right</code>
</label>
<br>
<label>
  <input class="toggle" type="checkbox" value="sidebar-chevron-left" data-class data-group="sidebar-chevron"> Preview <code>sidebar-chevron-left</code>
</label>

<!-- prettier-ignore -->
```html
<body class="sidebar-chevron-right">
```

<!-- prettier-ignore -->
```html
<body class="sidebar-chevron-left">
```

To prevent chevrons from displaying for specific page links, add a `no-chevron` class as follows:

```md
[My Page](page.md ':class=no-chevron')
```

**Theme properties**

<!-- prettier-ignore -->
```css
:root {
  --sidebar-chevron-collapsed-color: var(--color-mono-3);
  --sidebar-chevron-expanded-color : var(--theme-color);
}
```

### Sidebar groups

Add visual distinction between groups of links in the sidebar.

<label>
  <input class="toggle" type="checkbox" value="sidebar-group-box" data-class data-group="sidebar-group"> Preview <code>sidebar-group-box</code>
</label>
<br>
<label>
  <input class="toggle" type="checkbox" value="sidebar-group-underline" data-class data-group="sidebar-group"> Preview <code>sidebar-group-underline</code>
</label>

<!-- prettier-ignore -->
```html
<body class="sidebar-group-box">
```

<!-- prettier-ignore -->
```html
<body class="sidebar-group-underline">
```

### Sidebar link clamp

Limit multi-line sidebar links to a single line followed by an ellipses.

<label>
  <input class="toggle" type="checkbox" value="sidebar-link-clamp" data-class>
  Preview <code>sidebar-link-clamp</code>
</label>

<!-- prettier-ignore -->
```html
<body class="sidebar-link-clamp">
```

### Sidebar toggle

Display a "hamburger" icon (three lines) in the sidebar toggle button instead of the default "kebab" icon.

<label>
  <input class="toggle" type="checkbox" value="sidebar-toggle-chevron" data-class data-group="sidebar-toggle">
  Preview <code>sidebar-toggle-chevron</code>
</label>
<br>
<label>
  <input class="toggle" type="checkbox" value="sidebar-toggle-hamburger" data-class data-group="sidebar-toggle">
  Preview <code>sidebar-toggle-hamburger</code>
</label>

<!-- prettier-ignore -->
```html
<body class="sidebar-toggle-chevron">
```

<!-- prettier-ignore -->
```html
<body class="sidebar-toggle-hamburger">
```

## Customization

Docsify provides [theme properties](#theme-properties) for simplified customization of frequently modified styles.

1. Add a `<style>` tag after the theme stylesheet in your `index.html`.

   <!-- prettier-ignore -->
   ```html
   <!-- Theme -->
   <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify@5/dist/themes/core.min.css" />

   <!-- Custom theme styles -->
   <style>
     :root {
       /* ... */
     }
   </style>
   ```

   Theme properties can also be set on a per-page basis in markdown.

   ```markdown
   # My Heading

   Hello, World!

   <style>
     :root {
       /* ... */
     }
   </style>
   ```

2. Set custom [theme properties](#theme-properties) within a `:root` declaration.

   <!-- prettier-ignore -->
   ```css
   :root {
     --theme-color: red;
     --font-size  : 15px;
     --line-height: 1.5;
   }
   ```

   Custom [theme properties](#theme-properties) can be conditionally applied in light and/or dark mode.

   <!-- prettier-ignore -->
   ```css
   /* Light and dark mode */
   :root {
     --theme-color: pink;
   }

   /* Light mode only */
   @media (prefers-color-scheme: light) {
     :root {
       --color-bg  : #eee;
       --color-text: #444;
     }
   }

   /* Dark mode only */
   @media screen and (prefers-color-scheme: dark) {
     :root {
       --color-bg  : #222;
       --color-text: #ddd;
     }
   }
   ```

3. Custom fonts can be used by adding web font resources and modifying `--font-family` properties as needed:

   <!-- prettier-ignore -->
   ```css
   /* Fonts: Noto Sans, Noto Emoji, Noto Mono */
   @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Noto+Sans+Mono:wght@100..900&family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap');

   :root {
     --font-family      : 'Noto Sans', sans-serif;
     --font-family-emoji: 'Noto Color Emoji', sans-serif;
     --font-family-mono : 'Noto Sans Mono', monospace;
   }
   ```

   ?> **Theme authors**: Consider providing instructions for loading your recommended web fonts manually instead of including them in your theme using `@import`. This allows users who prefer a different font to avoid loading your recommended web font(s) unnecessarily.

4. Advanced styling may require custom CSS declarations. This is expected, however custom CSS declarations may break when new versions of Docsify are released. When possible, leverage [theme properties](#theme-properties) instead of custom declarations or lock your [CDN](cdn) URLs to a [specific version](cdn#specific-version) to avoid potential issues when using custom CSS declarations.

   ```css
   .sidebar li.active > a {
     border-right: 3px solid var(--theme-color);
   }
   ```

## Theme properties

The following properties are available in all official Docsify themes. Default values for the "Core" theme are shown.

?> **Theme and plugin authors**: We encourage you to leverage these custom theme properties and to offer similar customization options in your projects.

### Common

Below are the most commonly modified theme properties. [Advanced](#advanced) theme properties are also available for use but typically do not need to be modified.

<!-- TODO: Replace TBD with include CSS include below -->

**TBD**

<!-- [vars.css](https://raw.githubusercontent.com/docsifyjs/docsify/main/src/themes/shared/_vars.css ':include') -->

### Advanced

Advanced theme properties are also available for use but typically do not need to be modified. Values derived from [common](#common) theme properties but can be set explicitly if preferred.

<!-- TODO: Replace TBD with include CSS include below -->

**TBD**

<!-- [vars.css](https://raw.githubusercontent.com/docsifyjs/docsify/main/src/themes/shared/_vars.css ':include') -->

## Community

See [Awesome Docsify](awesome) for additional community themes.

<script>
  (function () {
    const toggleElms = Docsify.dom.findAll(
      'input:where([data-class], [data-sheet])',
    );
    const previewSheets = Docsify.dom.findAll(
      'link[rel="stylesheet"][data-sheet]',
    );

    function handleChange(e) {
      const elm = e.target.closest('[data-class], [data-sheet]');
      const value = elm.value;
      const groupVal = elm.getAttribute('data-group');
      const radioGroupName = elm.matches('[type="radio"]') ? elm.name : undefined;

      // Toggle class
      if (elm.matches('[data-class]')) {
        document.body.classList.toggle(value, elm.checked);
      }
      // Toggle sheet
      else {
        const themeSheet = previewSheets.find(
          sheet => sheet.getAttribute('data-sheet') === value,
        );

        themeSheet && (themeSheet.disabled = !elm.checked);
      }

      if (!elm.checked || (!groupVal && !radioGroupName)) {
        return;
      }

      // Group elements & values
      const groupElms = toggleElms.filter(elm =>
        groupVal
          ? groupVal === elm.getAttribute('data-group')
          : radioGroupName === elm.name,
      );
      const groupVals = groupElms.map(elm => elm.value);

      if (groupElms.length <= 1) {
        return;
      }

      if (groupVal) {
        // Uncheck other group elements
        groupElms.forEach(groupElm => {
          if (groupElm !== elm) {
            groupElm.checked = false;
          }
        });
      }

      // Remove group classes
      if (elm.matches('[data-class]')) {
        groupVals.forEach(className => {
          if (className !== value) {
            document.body.classList.remove(className);
          }
        });
      }
      // Disable group sheets
      else {
        const otherSheets = groupVals
          .map(val =>
            previewSheets.find(sheet => sheet.getAttribute('data-sheet') === val),
          )
          .filter(sheet => sheet && sheet.getAttribute('data-sheet') !== value);
        const disableSheets = otherSheets.length ? otherSheets : previewSheets;

        disableSheets.forEach(sheet => sheet.disabled = true);
      }
    }

    // Toggle active elms
    toggleElms.forEach(elm => {
      const value = elm.value;

      // Class toggle
      if (elm.matches('[data-class]')) {
        elm.checked = document.body.classList.contains(value);
      }
      // Sheet toggle
      else {
        const previewSheet = previewSheets.find(
          sheet => sheet.getAttribute('data-sheet') === value,
        );

        elm.checked = previewSheet && !previewSheet.disabled;
      }
    });

    toggleElms.forEach(elm => elm.addEventListener('change', handleChange));
  })();
</script>
`````

## File: docs/ui-kit.md
`````markdown
<!-- markdownlint-disable single-title no-duplicate-heading -->

# UI Kit

<details>
  <summary>View the markdown source for this page</summary>
  <div style="max-height: 50vh; overflow: auto;">

[ui-kit.md](ui-kit.md ':include :type=code')

  </div>
</details>

## Blockquotes

> Cras aliquet nulla quis metus tincidunt, sed placerat enim cursus. Etiam
> turpis nisl, posuere eu condimentum ut, interdum a risus. Sed non luctus mi.
> Quisque malesuada risus sit amet tortor aliquet, a posuere ex iaculis. Vivamus
> ultrices enim dui, eleifend porttitor elit aliquet sed.
>
> _- Quote Source_

#### Nested

<!-- prettier-ignore -->
> Level 1
> > Level 2
> > > Level 3

## Buttons

#### Default

<button>Button</button>

#### Basic

<button type="button">Button</button>
<a href="javascript:void(0);" class="button">Link Button</a>
<input type="button" value="Input Button" class="button">

#### Primary

<button type="button" class="primary">Button</button>
<a href="javascript:void(0);" class="button primary">Link Button</a>
<input type="button" value="Input Button" class="primary">

#### Secondary

<button type="button" class="secondary">Button</button>
<a href="javascript:void(0);" class="button secondary">Link Button</a>
<input type="button" value="Input Button" class="secondary">

## Callouts

!> **Important** callout with `inline code` and additional placeholder text used
to force the content to wrap and span multiple lines.

?> **Tip** callout with `inline code` and additional placeholder text used to
force the content to wrap and span multiple lines.

## Code

This is `inline code`

```javascript
const add = (num1, num2) => num1 + num2;
const total = add(1, 2);

console.log(total); // 3
```

```html
<body>
  <p>Hello</p>
</body>
```

## Colors

#### Theme

<div class="ui-kit-color">
  <figure>
    <div style="background: var(--theme-color-1);"></div>
    <figcaption>1<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-2);"></div>
    <figcaption>2<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-3);"></div>
    <figcaption>3<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-4);"></div>
    <figcaption>4<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color);"></div>
    <figcaption>Theme Color<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-5);"></div>
    <figcaption>5<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-6);"></div>
    <figcaption>6<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-7);"></div>
    <figcaption>7<figcaption>
  </figure>
  <figure>
    <div style="background: var(--theme-color-8);"></div>
    <figcaption>8<figcaption>
  </figure>
</div>

#### Monochromatic

<div class="ui-kit-color">
  <figure>
    <div style="background: var(--color-mono-min); border: 1px solid var(--color-mono-2);"></div>
    <figcaption>Min<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-1);"></div>
    <figcaption>1<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-2);"></div>
    <figcaption>2<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-3);"></div>
    <figcaption>3<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-4);"></div>
    <figcaption>4<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-5);"></div>
    <figcaption>5<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-6);"></div>
    <figcaption>6<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-7);"></div>
    <figcaption>7<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-8);"></div>
    <figcaption>8<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-9);"></div>
    <figcaption>9<figcaption>
  </figure>
  <figure>
    <div style="background: var(--color-mono-max);"></div>
    <figcaption>Max<figcaption>
  </figure>
</div>

## Details

<details>
  <summary>Details (click to open)</summary>

Suscipit nemo aut ex suscipit voluptatem laboriosam odio velit. Ipsum eveniet labore sequi non optio vel. Ut culpa ad accusantium est aut harum ipsam voluptatum. Velit eum incidunt non sint. Et molestiae veniam natus autem vel assumenda ut numquam esse. Non nisi id qui vero corrupti quos et.

</details>

<details open>
  <summary>Details (open by default)</summary>

Suscipit nemo aut ex suscipit voluptatem laboriosam odio velit. Ipsum eveniet labore sequi non optio vel. Ut culpa ad accusantium est aut harum ipsam voluptatum. Velit eum incidunt non sint. Et molestiae veniam natus autem vel assumenda ut numquam esse. Non nisi id qui vero corrupti quos et.

</details>

## Form Elements

### Fieldset

<form>
  <fieldset>
    <legend>Legend</legend>
    <p>
      <label>
        Label<br>
        <input type="text" placeholder="Placeholder">
      </label>
    </p>
  </fieldset>
</form>

### Input

#### Checkbox

<form>
  <label><input type="checkbox" value="HTML" checked> HTML</label><br>
  <label><input type="checkbox" value="CSS"> CSS</label><br>
  <label><input type="checkbox" value="JavaScript"> JavaScript</label>
</form>

#### Datalist

<form>
  <label>
    Label<br>
    <input list="planets">
    <datalist id="planets">
      <option value="Earth">Earth</option>
      <option value="Jupiter">Jupiter</option>
      <option value="Mars">Mars</option>
      <option value="Mercury">Mercury</option>
      <option value="Neptune">Neptune</option>
      <option value="Saturn">Saturn</option>
      <option value="Uranus">Uranus</option>
      <option value="Venus">Venus</option>
    </datalist>
  </label>
</form>

#### Radio

<form>
  <label><input type="radio" name="language" value="HTML" checked> HTML</label><br>
  <label><input type="radio" name="language" value="CSS"> CSS</label><br>
  <label><input type="radio" name="language" value="JavaScript"> JavaScript</label>
</form>

#### Text

<form>
  <label>
    First name<br>
    <input type="text" placeholder="Placeholder">
  </label>
</form>

#### Toggles

<form>
Checkbox (multi-select)

<label><input class="toggle" type="checkbox" checked> HTML</label><br>
<label><input class="toggle" type="checkbox"> CSS</label><br>
<label><input class="toggle" type="checkbox"> JavaScript</label>

Radio (single-select)

<label><input class="toggle" type="radio" name="toggle" checked> HTML</label><br>
<label><input class="toggle" type="radio" name="toggle"> CSS</label><br>
<label><input class="toggle" type="radio" name="toggle"> JavaScript</label>

</form>

### Select

<form>
  <label>
    Label<br>
    <select>
      <option value="Earth">Select a planet...</option>
      <option value="Earth">Earth</option>
      <option value="Jupiter">Jupiter</option>
      <option value="Mars">Mars</option>
      <option value="Mercury">Mercury</option>
      <option value="Neptune">Neptune</option>
      <option value="Saturn">Saturn</option>
      <option value="Uranus">Uranus</option>
      <option value="Venus">Venus</option>
    </select>
  </label>
</form>

### Textarea

<textarea rows="5" cols="40">
Ipsam totam tempora. Dolorum voluptas error tempore asperiores vitae error laboriosam autem possimus.
</textarea>

## Headings

# Heading 1 {docsify-ignore}

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse luctus nulla eu ex varius, a varius elit tincidunt. Aenean arcu magna, gravida id purus a, interdum convallis turpis. Aenean id ipsum eu tortor sollicitudin scelerisque in quis elit.

## Heading 2 {docsify-ignore}

Vestibulum lobortis laoreet nunc vel vulputate. In et augue non lectus pellentesque molestie et ac justo. Sed sed turpis ut diam gravida sagittis nec at neque. Vivamus id tellus est. Nam ac dignissim mi. Vestibulum nec sem convallis, condimentum augue at, commodo diam.

### Heading 3 {docsify-ignore}

Suspendisse sit amet tincidunt nibh, ac interdum velit. Ut orci diam, dignissim at enim sit amet, placerat rutrum magna. Mauris consectetur nibh eget sem feugiat, sit amet congue quam laoreet. Curabitur sed massa metus.

#### Heading 4 {docsify-ignore}

Donec odio orci, facilisis ac vehicula in, vestibulum ut urna. Ut bibendum ullamcorper risus, ac euismod leo maximus sed. In pulvinar sagittis rutrum. Morbi quis cursus diam. Cras ac laoreet nulla, rhoncus sodales dui.

##### Heading 5 {docsify-ignore}

Commodo sit veniam nulla cillum labore ullamco aliquip quis. Consequat nulla fugiat consequat ex duis proident. Adipisicing excepteur tempor exercitation ad. Consectetur voluptate Lorem sint elit exercitation ullamco dolor.

###### Heading 6 {docsify-ignore}

Ipsum ea amet dolore mollit incididunt fugiat nulla laboris est sint voluptate. Ex culpa id amet ipsum amet pariatur ipsum officia sit laborum irure ullamco deserunt. Consequat qui tempor occaecat nostrud proident.

## Horizontal Rule

Text before rule.

---

Text after rule.

## IFrame

[Example](_media/example.html ':include height=200px')

## Images

#### Inline-style

![Docsify Logo](/_media/icon.svg 'This is the Docsify logo!')

#### Reference-style

![Docsify Logo][logo]

[logo]: /_media/icon.svg 'This is the Docsify logo!'

#### Light / Dark Theme

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="_media/moon.svg">
  <source media="(prefers-color-scheme: light)" srcset="_media/sun.svg">
  <img alt="BinaryTree" src="_media/sun.svg" width="122">
</picture>

## Keyboard

#### Default

<kbd>&#8963;</kbd><kbd>&#8997;</kbd><kbd>&#9003;</kbd>

<kbd>Ctrl</kbd><kbd>Alt</kbd><kbd>Del</kbd>

<kbd>&#8963; Control</kbd><kbd>&#8997; Alt</kbd><kbd>&#9003; Delete</kbd>

#### Alternate

<kbd class="alt">&#8963;</kbd><kbd class="alt">&#8997;</kbd><kbd class="alt">&#9003;</kbd>

<kbd class="alt">Ctrl</kbd><kbd class="alt">Alt</kbd><kbd class="alt">Del</kbd>

<kbd class="alt">&#8963; Control</kbd><kbd class="alt">&#8997; Alt</kbd><kbd class="alt">&#9003; Delete</kbd>

#### Entities

<div style="display: grid; grid-template-columns: auto auto 1fr; gap: 1em 0.2em; align-items: end;">
  <div><kbd class="alt">&uarr;</kbd></div>  <div><kbd>&uarr;</kbd></div>  <div>Arrow Up</div>
  <div><kbd class="alt">&darr;</kbd></div>  <div><kbd>&darr;</kbd></div>  <div>Arrow Down</div>
  <div><kbd class="alt">&larr;</kbd></div>  <div><kbd>&larr;</kbd></div>  <div>Arrow Left</div>
  <div><kbd class="alt">&rarr;</kbd></div>  <div><kbd>&rarr;</kbd></div>  <div>Arrow Right</div>
  <div><kbd class="alt">&#8682;</kbd></div> <div><kbd>&#8682;</kbd></div> <div>Caps Lock</div>
  <div><kbd class="alt">&#8984;</kbd></div> <div><kbd>&#8984;</kbd></div> <div>Command</div>
  <div><kbd class="alt">&#8963;</kbd></div> <div><kbd>&#8963;</kbd></div> <div>Control</div>
  <div><kbd class="alt">&#9003;</kbd></div> <div><kbd>&#9003;</kbd></div> <div>Delete</div>
  <div><kbd class="alt">&#8998;</kbd></div> <div><kbd>&#8998;</kbd></div> <div>Delete (Forward)</div>
  <div><kbd class="alt">&#8600;</kbd></div> <div><kbd>&#8600;</kbd></div> <div>End</div>
  <div><kbd class="alt">&#8996;</kbd></div> <div><kbd>&#8996;</kbd></div> <div>Enter</div>
  <div><kbd class="alt">&#9099;</kbd></div> <div><kbd>&#9099;</kbd></div> <div>Escape</div>
  <div><kbd class="alt">&#8598;</kbd></div> <div><kbd>&#8598;</kbd></div> <div>Home</div>
  <div><kbd class="alt">&#8670;</kbd></div> <div><kbd>&#8670;</kbd></div> <div>Page Up</div>
  <div><kbd class="alt">&#8671;</kbd></div> <div><kbd>&#8671;</kbd></div> <div>Page Down</div>
  <div><kbd class="alt">&#8997;</kbd></div> <div><kbd>&#8997;</kbd></div> <div>Option, Alt</div>
  <div><kbd class="alt">&#8629;</kbd></div> <div><kbd>&#8629;</kbd></div> <div>Return</div>
  <div><kbd class="alt">&#8679;</kbd></div> <div><kbd>&#8679;</kbd></div> <div>Shift</div>
  <div><kbd class="alt">&#9251;</kbd></div> <div><kbd>&#9251;</kbd></div> <div>Space</div>
  <div><kbd class="alt">&#8677;</kbd></div> <div><kbd>&#8677;</kbd></div> <div>Tab</div>
  <div><kbd class="alt">&#8676;</kbd></div> <div><kbd>&#8676;</kbd></div> <div>Tab + Shift</div>
 </div>

## Links

[Inline link](https://google.com)

[Inline link with title](https://google.com 'Google')

[Reference link by name][link1]

[Reference link by number][1]

[Reference link by self]

[link1]: https://google.com
[1]: https://google.com
[Reference link by self]: https://google.com

## Lists

### Ordered List

1. Ordered
1. Ordered
   1. Nested
   1. Nested (Wrapping): Similique tempora et. Voluptatem consequuntur ut. Rerum minus et sed beatae. Consequatur ut nemo laboriosam quo architecto quia qui. Corrupti aut omnis velit.
1. Ordered (Wrapping): Error minima modi rem sequi facere voluptatem. Est nihil veritatis doloribus et corporis ipsam. Pariatur eos ipsam qui odit labore est voluptatem enim. Veritatis est qui ut pariatur inventore.

### Unordered List

- Unordered
- Unordered
  - Nested
  - Nested (Wrapping): Quia consectetur sint vel ut excepturi ipsa voluptatum suscipit hic. Ipsa error qui molestiae harum laboriosam. Rerum non amet illo voluptatem odio pariatur. Ut minus enim.
- Unordered (Wrapping): Fugiat qui tempore ratione amet repellendus repudiandae non. Rerum nisi officia enim. Itaque est alias voluptatibus id molestiae accusantium. Cupiditate sequi qui omnis sed facere aliquid quia ut.

### Task List

- [x] Task
- [ ] Task
  - [ ] Subtask
  - [ ] Subtask
  - [x] Subtask
- [ ] Task (Wrapping): Earum consequuntur itaque numquam sunt error omnis ipsum repudiandae. Est assumenda neque eum quia quisquam laborum beatae autem ad. Fuga fugiat perspiciatis harum quia dignissimos molestiae. Officia quo eveniet tempore modi voluptates consequatur. Eum odio adipisci labore.
  - [x] Subtask (Wrapping): Vel possimus eaque laborum. Voluptates qui debitis quaerat atque molestiae quia explicabo doloremque. Reprehenderit perspiciatis a aut impedit temporibus aut quasi quia. Incidunt sed recusandae vitae asperiores sit in.

## Output

<output data-lang="output">
  <p>Et cum fugiat nesciunt voluptates. A atque quos doloribus dolorem quo. Et dignissimos omnis nam. Recusandae voluptatem nam. Tenetur veniam et qui consequatur. Aut sequi atque fuga itaque iusto eum nihil quod iure.</p>
  <ol>
    <li>Item</li>
    <li>Item</li>
    <li>Item</li>
  </ol>
</output>

## Tables

### Alignment

| Left Align | Center Align | Right Align | Non&#8209;Breaking&nbsp;Header |
| ---------- | :----------: | ----------: | ------------------------------ |
| A1         |      A2      |          A3 | A4                             |
| B1         |      B2      |          B3 | B4                             |
| C1         |      C2      |          C3 | C4                             |

### Headerless

|     |     |     |     |
| --- | --- | --- | --- |
| A1  | A2  | A3  | A4  |
| B1  | B2  | B3  | B4  |
| C1  | C2  | C3  | C4  |

### Scrolling

| Header                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dicta&nbsp;in&nbsp;nobis&nbsp;dolor&nbsp;adipisci&nbsp;qui.&nbsp;Accusantium&nbsp;voluptates&nbsp;est&nbsp;dolor&nbsp;laboriosam&nbsp;qui&nbsp;voluptatibus.&nbsp;Veritatis&nbsp;eos&nbsp;aspernatur&nbsp;iusto&nbsp;et&nbsp;dicta&nbsp;quas.&nbsp;Fugit&nbsp;voluptatem&nbsp;dolorum&nbsp;qui&nbsp;quisquam.&nbsp;nihil |
| Aut&nbsp;praesentium&nbsp;officia&nbsp;aut&nbsp;delectus.&nbsp;Quas&nbsp;atque&nbsp;reprehenderit&nbsp;saepe.&nbsp;Et&nbsp;voluptatibus&nbsp;qui&nbsp;dolores&nbsp;rem&nbsp;facere&nbsp;in&nbsp;dignissimos&nbsp;id&nbsp;aut.&nbsp;Debitis&nbsp;excepturi&nbsp;delectus&nbsp;et&nbsp;quos&nbsp;numquam&nbsp;magnam.      |
| Sed&nbsp;eum&nbsp;atque&nbsp;at&nbsp;laborum&nbsp;aut&nbsp;et&nbsp;repellendus&nbsp;ullam&nbsp;dolor.&nbsp;Cupiditate&nbsp;saepe&nbsp;voluptatibus&nbsp;odit&nbsp;est&nbsp;pariatur&nbsp;qui.&nbsp;Hic&nbsp;sunt&nbsp;nihil&nbsp;optio&nbsp;enim&nbsp;eum&nbsp;laudantium.&nbsp;Repellendus&nbsp;voluptate.              |

## Text Elements

<mark>Marked text</mark>

<pre>Preformatted text</pre>

<samp>Sample Output</samp>

<small>Small Text</small>

This is <sub>subscript</sub>

This is <sup>superscript</sup>

<ins>Underlined Text</ins>

## Text Styles

Body text

**Bold text**

_Italic text_

**_Bold and italic text_**

~~Strikethrough~~
`````

## File: docs/vue.md
`````markdown
# Vue compatibility

Docsify allows [Vue.js](https://vuejs.org) content to be added directly to your markdown pages. This can greatly simplify working with data and adding reactivity to your site.

Vue [template syntax](https://vuejs.org/guide/essentials/template-syntax) can be used to add dynamic content to your pages. Vue content becomes more interesting when [data](#data), [computed properties](#computed-properties), [methods](#methods), and [lifecycle hooks](#lifecycle-hooks) are used. These options can be specified as [global options](#global-options) or within DOM [mounts](#mounts) and [components](#components).

## Setup

To get started, add Vue.js to your `index.html` file. Choose the production version for your live site or the development version for helpful console warnings and [Vue.js devtools](https://github.com/vuejs/vue-devtools) support.

```html
<!-- Production -->
<script src="//cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>

<!-- Development -->
<script src="//cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"></script>
```

## Template syntax

Vue [template syntax](https://vuejs.org/guide/essentials/template-syntax) offers several useful features like support for [JavaScript expressions](https://vuejs.org/guide/essentials/template-syntax.html#using-javascript-expressions) and Vue [directives](https://vuejs.org/guide/essentials/template-syntax.html#directives) for loops and conditional rendering.

```markdown
<!-- Hide in docsify, show elsewhere (e.g. GitHub) -->
<p v-if="false">Text for GitHub</p>

<!-- Sequenced content (i.e. loop)-->
<ul>
  <li v-for="i in 3">Item {{ i }}</li>
</ul>

<!-- JavaScript expressions -->
<p>2 + 2 = {{ 2 + 2 }}</p>
```

<output data-lang="output">
  <p v-if="false">Text for GitHub</p>

  <ul>
    <li v-for="i in 3">Item {{ i }}</li>
  </ul>

  <p>2 + 2 = {{ 2 + 2 }}</p>
</output>

[View output on GitHub](https://github.com/docsifyjs/docsify/blob/develop/docs/vue.md#template-syntax)

## Code Blocks

Docsify ignores Vue template syntax within code blocks by default:

````markdown
```
{{ message }}
```
````

To process Vue template syntax within a code block, wrap the code block in an element with a `v-template` attribute:

````markdown
<div v-template>

```
{{ message }}
```

</div>
````

## Data

```js
{
  data() {
    return {
      message: 'Hello, World!'
    };
  }
}
```

<!-- prettier-ignore-start -->
```markdown
<!-- Show message in docsify, show "{{ message }}" elsewhere (e.g. GitHub)  -->
{{ message }}

<!-- Show message in docsify, hide elsewhere (e.g. GitHub)  -->
<p v-text="message"></p>
```
<!-- prettier-ignore-end -->

<output data-lang="output">
  <p>{{ message }}</p>

  <p v-text="message"></p>
</output>

[View output on GitHub](https://github.com/docsifyjs/docsify/blob/develop/docs/vue.md#data)

## Computed properties

```js
{
  computed: {
    timeOfDay() {
      const date = new Date();
      const hours = date.getHours();

      if (hours < 12) {
        return 'morning';
      }
      else if (hours < 18) {
        return 'afternoon';
      }
      else {
        return 'evening'
      }
    }
  },
}
```

```markdown
Good {{ timeOfDay }}!
```

<output data-lang="output">

Good {{ timeOfDay }}!

</output>

## Methods

```js
{
  data() {
    return {
      message: 'Hello, World!'
    };
  },
  methods: {
    hello() {
      alert(this.message);
    }
  },
}
```

```markdown
<button @click="hello">Say Hello</button>
```

<output data-lang="output">
  <p><button @click="hello">Say Hello</button></p>
</output>

## Lifecycle Hooks

```js
{
  data() {
    return {
      images: null,
    };
  },
  created() {
    fetch('https://api.domain.com/')
      .then(response => response.json())
      .then(data => (this.images = data))
      .catch(err => console.log(err));
  }
}

// API response:
// [
//   { title: 'Image 1', url: 'https://domain.com/1.jpg' },
//   { title: 'Image 2', url: 'https://domain.com/2.jpg' },
//   { title: 'Image 3', url: 'https://domain.com/3.jpg' },
// ];
```

```markdown
<div style="display: flex;">
  <figure style="flex: 1;">
    <img v-for="image in images" :src="image.url" :title="image.title">
    <figcaption>{{ image.title }}</figcaption>
  </figure>
</div>
```

<output data-lang="output">
  <div style="display: flex;">
    <figure v-for="image in images" style="flex: 1; text-align: center;">
      <img :src="image.url">
      <figcaption>{{ image.title }}</figcaption>
    </figure>
  </div>
</output>

## Global options

Use `vueGlobalOptions` to specify global Vue options for use with Vue content not explicitly mounted with [vueMounts](#mounts), [vueComponents](#components), or a [markdown script](#markdown-script). Changes to global `data` will persist and be reflected anywhere global references are used.

```js
window.$docsify = {
  vueGlobalOptions: {
    data() {
      return {
        count: 0,
      };
    },
  },
};
```

```markdown
<p>
  <button @click="count += 1">+</button>
  {{ count }}
  <button @click="count -= 1">-</button>
</p>
```

<output data-lang="output">
  <p>
    <button @click="count += 1">+</button>
    {{ count }}
    <button @click="count -= 1">-</button>
  </p>
</output>

Notice the behavior when multiple global counters are rendered:

<output data-lang="output">
  <p>
    <button @click="count += 1">+</button>
    {{ count }}
    <button @click="count -= 1">-</button>
  </p>
</output>

Changes made to one counter affect the both counters. This is because both instances reference the same global `count` value. Now, navigate to a new page and return to this section to see how changes made to global data persist between page loads.

## Mounts

Use `vueMounts` to specify DOM elements to mount as Vue instances and their associated options. Mount elements are specified using a [CSS selector](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) as the key with an object containing Vue options as their value. Docsify will mount the first matching element in the main content area each time a new page is loaded. Mount element `data` is unique for each instance and will not persist as users navigate the site.

```js
window.$docsify = {
  vueMounts: {
    '#counter': {
      data() {
        return {
          count: 0,
        };
      },
    },
  },
};
```

```markdown
<div id="counter">
  <button @click="count += 1">+</button>
  {{ count }}
  <button @click="count -= 1">-</button>
</div>
```

<output id="counter">
  <button @click="count += 1">+</button>
  {{ count }}
  <button @click="count -= 1">-</button>
</output>

## Components

Use `vueComponents` to create and register global [Vue components](https://vuejs.org/guide/essentials/component-basics.html). Components are specified using the component name as the key with an object containing Vue options as the value. Component `data` is unique for each instance and will not persist as users navigate the site.

```js
window.$docsify = {
  vueComponents: {
    'button-counter': {
      template: `
        <button @click="count += 1">
          You clicked me {{ count }} times
        </button>
      `,
      data() {
        return {
          count: 0,
        };
      },
    },
  },
};
```

```markdown
<button-counter></button-counter>
<button-counter></button-counter>
```

<output data-lang="output">
  <button-counter></button-counter>
  <button-counter></button-counter>
</output>

## Markdown script

Vue content can mounted using a `<script>` tag in your markdown pages.

!> Only the first `<script>` tag in a markdown file is executed. If you wish to mount multiple Vue instances using a script tag, all instances must be mounted within the first script tag in your markdown.

```html
<script>
  Vue.createApp({
    // Options...
  }).mount('#example');
</script>
```

## Technical Notes

- Docsify processes Vue content in the following order on each page load:
  1. Execute markdown `<script>`
  1. Register global `vueComponents`
  1. Mount `vueMounts`
  1. Auto-mount unmounted `vueComponents`
  1. Auto-mount unmounted Vue template syntax using `vueGlobalOptions`
- When auto-mounting Vue content, docsify will mount each top-level element in your markdown that contains template syntax or a component. For example, in the following HTML the top-level `<p>`, `<my-component />`, and `<div>` elements will be mounted.
  ```html
  <p>{{ foo }}</p>
  <my-component />
  <div>
    <span>{{ bar }}</span>
    <some-other-component />
  </div>
  ```
- Docsify will not mount an existing Vue instance or an element that contains an existing Vue instance.
- Docsify will automatically destroy/unmount all Vue instances it creates before each page load.
`````

## File: docs/write-a-plugin.md
`````markdown
# Write a plugin

A docsify plugin is a function with the ability to execute custom JavaScript code at various stages of Docsify's lifecycle.

## Setup

Docsify plugins can be added directly to the `plugins` array:

```js
window.$docsify = {
  plugins: [
    function myPlugin1(hook, vm) {
      // ...
    },
    function myPlugin2(hook, vm) {
      // ...
    },
  ],
};
```

Alternatively, a plugin can be stored in a separate file and "installed" using a standard `<script>` tag:

```js
// docsify-plugin-myplugin.js

{
  function myPlugin(hook, vm) {
    // ...
  }

  // Add plugin to docsify's plugin array
  window.$docsify = window.$docsify || {};
  $docsify.plugins = [...($docsify.plugins || []), myPlugin];
}
```

```html
<script src="docsify-plugin-myplugin.js"></script>
```

## Template

Below is a plugin template with placeholders for all available lifecycle hooks.

1. Copy the template
1. Modify the `myPlugin` name as appropriate
1. Add your plugin logic
1. Remove unused lifecycle hooks
1. Save the file as `docsify-plugin-[name].js`
1. Load your plugin using a standard `<script>` tag

```js
{
  function myPlugin(hook, vm) {
    // Invoked one time when docsify script is initialized
    hook.init(() => {
      // ...
    });

    // Invoked one time when the docsify instance has mounted on the DOM
    hook.mounted(() => {
      // ...
    });

    // Invoked on each page load before new markdown is transformed to HTML.
    // Supports asynchronous tasks (see beforeEach documentation for details).
    hook.beforeEach(markdown => {
      // ...
      return markdown;
    });

    // Invoked on each page load after new markdown has been transformed to HTML.
    // Supports asynchronous tasks (see afterEach documentation for details).
    hook.afterEach(html => {
      // ...
      return html;
    });

    // Invoked on each page load after new HTML has been appended to the DOM
    hook.doneEach(() => {
      // ...
    });

    // Invoked one time after rendering the initial page
    hook.ready(() => {
      // ...
    });
  }

  // Add plugin to docsify's plugin array
  window.$docsify = window.$docsify || {};
  $docsify.plugins = [myPlugin, ...($docsify.plugins || [])];
}
```

## Lifecycle Hooks

Lifecycle hooks are provided via the `hook` argument passed to the plugin function.

### init()

Invoked one time when docsify script is initialized.

```js
hook.init(() => {
  // ...
});
```

### mounted()

Invoked one time when the docsify instance has mounted on the DOM.

```js
hook.mounted(() => {
  // ...
});
```

### beforeEach()

Invoked on each page load before new markdown is transformed to HTML.

```js
hook.beforeEach(markdown => {
  // ...
  return markdown;
});
```

For asynchronous tasks, the hook function accepts a `next` callback as a second argument. Call this function with the final `markdown` value when ready. To prevent errors from affecting docsify and other plugins, wrap async code in a `try/catch/finally` block.

```js
hook.beforeEach((markdown, next) => {
  try {
    // Async task(s)...
  } catch (err) {
    // ...
  } finally {
    next(markdown);
  }
});
```

### afterEach()

Invoked on each page load after new markdown has been transformed to HTML.

```js
hook.afterEach(html => {
  // ...
  return html;
});
```

For asynchronous tasks, the hook function accepts a `next` callback as a second argument. Call this function with the final `html` value when ready. To prevent errors from affecting docsify and other plugins, wrap async code in a `try/catch/finally` block.

```js
hook.afterEach((html, next) => {
  try {
    // Async task(s)...
  } catch (err) {
    // ...
  } finally {
    next(html);
  }
});
```

### doneEach()

Invoked on each page load after new HTML has been appended to the DOM.

```js
hook.doneEach(() => {
  // ...
});
```

### ready()

Invoked one time after rendering the initial page.

```js
hook.ready(() => {
  // ...
});
```

## Tips

- Access Docsify methods and properties using `window.Docsify`
- Access the current Docsify instance using the `vm` argument
- Developers who prefer using a debugger can set the [`catchPluginErrors`](configuration#catchpluginerrors) configuration option to `false` to allow their debugger to pause JavaScript execution on error
- Be sure to test your plugin on all supported platforms and with related configuration options (if applicable) before publishing

## Examples

#### Page Footer

```js
window.$docsify = {
  plugins: [
    function pageFooter(hook, vm) {
      const footer = /* html */ `
        <hr/>
        <footer>
          <span><a href="https://github.com/QingWei-Li">cinwell</a> &copy;2017.</span>
          <span>Proudly published with <a href="https://github.com/docsifyjs/docsify" target="_blank">docsify</a>.</span>
        </footer>
      `;

      hook.afterEach(html => {
        return html + footer;
      });
    },
  ],
};
```

### Edit Button (GitHub)

```js
window.$docsify = {
  plugins: [
    function editButton(hook, vm) {
      // The date template pattern
      $docsify.formatUpdated = '{YYYY}/{MM}/{DD} {HH}:{mm}';

      hook.beforeEach(html => {
        const url =
          'https://github.com/docsifyjs/docsify/blob/main/docs/' +
          vm.route.file;
        const editHtml = '[📝 EDIT DOCUMENT](' + url + ')\n';

        return (
          editHtml +
          html +
          '\n----\n' +
          'Last modified {docsify-updated}' +
          editHtml
        );
      });
    },
  ],
};
```
`````
