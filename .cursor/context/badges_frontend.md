└── frontend
    ├── babel.config.cjs
    ├── blog
        ├── 2023-07-03-new-frontend.md
        ├── 2023-07-29-tag-filter.md
        ├── 2023-11-29-simpleicons10.md
        ├── 2024-01-13-simpleicons11.md
        ├── 2024-06-01-simpleicons12.md
        ├── 2024-07-05-simpleicons13.md
        ├── 2024-07-10-sunsetting-shields-custom-logos.md
        ├── 2024-09-25-rce.md
        ├── 2024-11-14-token-pool.md
        └── 2024-12-27-simpleicons14.md
    ├── categories
        └── .gitkeep
    ├── docs
        ├── index.md
        ├── logos.md
        └── static-badges.md
    ├── docusaurus.config.cjs
    ├── package.json
    ├── sidebars.cjs
    ├── src
        ├── components
        │   ├── homepage-features.js
        │   └── homepage-features.module.css
        ├── css
        │   └── custom.css
        ├── pages
        │   ├── community.md
        │   ├── donate.md
        │   ├── index.js
        │   ├── index.module.css
        │   └── privacy.md
        ├── plugins
        │   └── strip-code-block-links.js
        └── theme
        │   ├── ApiDemoPanel
        │       ├── Curl
        │       │   └── index.js
        │       └── Response
        │       │   └── index.js
        │   └── DocPaginator
        │       └── index.js
    └── static
        ├── .nojekyll
        └── img
            ├── builder.png
            ├── favicon.ico
            └── logo.png


/frontend/babel.config.cjs:
--------------------------------------------------------------------------------
1 | module.exports = {
2 |   presets: [require.resolve('@docusaurus/core/lib/babel/preset')],
3 | }
4 | 


--------------------------------------------------------------------------------
/frontend/blog/2023-07-03-new-frontend.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: new-frontend
 3 | title: We launched a new frontend
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | Alongside the general visual refresh and improvements to look and feel, our new frontend has allowed us to address a number of long-standing feature requests and enhancements:
13 | 
14 | - Clearer and more discoverable documentation for our [static](https://shields.io/badges/static-badge), dynamic [json](https://shields.io/badges/dynamic-json-badge)/[xml](https://shields.io/badges/dynamic-xml-badge)/[yaml](https://shields.io/badges/dynamic-yaml-badge) and [endpoint](https://shields.io/badges/endpoint-badge) badges
15 | - Improved badge builder interface, with all optional query parameters included in the builder for each badge
16 | - Each badge now has its own documentation page, which we can link to. e.g: [https://shields.io/badges/discord](https://shields.io/badges/discord)
17 | - Light/dark mode themes
18 | - Improved search
19 | - Documentation for individual path and query parameters
20 | 
21 | The new site also comes with big maintenance benefits for the core team. We rely heavily on [docusaurus](https://docusaurus.io/), [docusaurus-openapi](https://github.com/cloud-annotations/docusaurus-openapi), and [docusaurus-search-local](https://github.com/easyops-cn/docusaurus-search-local). This moves us to a mostly declarative setup, massively reducing the amount of custom frontend code we maintain ourselves.
22 | 


--------------------------------------------------------------------------------
/frontend/blog/2023-07-29-tag-filter.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: tag-filter
 3 | title: Applying filters to GitHub Tag and Release badges
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | We recently shipped a feature which allows you to pass an arbitrary filter to the GitHub tag and release badges. The `filter` param can be used to apply a filter to the project's tag or release names before selecting the latest from the list. Two constructs are available: `*` is a wildcard matching zero or more characters, and if the pattern starts with a `!`, the whole pattern is negated.
13 | 
14 | To give an example of how this might be useful, we create two types of tags on our GitHub repo: https://github.com/badges/shields/tags There are tags in the format `major.minor.patch` which correspond to our [NPM package releases](https://www.npmjs.com/package/badge-maker?activeTab=versions) and tags in the format `server-YYYY-MM-DD` that correspond to our [docker snapshot releases](https://registry.hub.docker.com/r/shieldsio/shields/tags?page=1&ordering=last_updated).
15 | 
16 | In our case, this would allow us to make a badge that applies the filter `!server-*` to filter out the snapshot tags and just select the latest package tag.
17 | 
18 | - ![tag badge without filter](https://img.shields.io/github/v/tag/badges/shields) - https://img.shields.io/github/v/tag/badges/shields
19 | - ![tag badge with filter](https://img.shields.io/github/v/tag/badges/shields?filter=%21server-%2A) - https://img.shields.io/github/v/tag/badges/shields?filter=%21server-%2A
20 | 


--------------------------------------------------------------------------------
/frontend/blog/2023-11-29-simpleicons10.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: simple-icons-10
 3 | title: Simple Icons 10
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | Logos on Shields.io are provided by SimpleIcons. We've recently upgraded to SimpleIcons 10. This release removes 45 icons. A full list of the removals can be found in the [release notes](https://github.com/simple-icons/simple-icons/releases/tag/10.0.0).
13 | 
14 | Please remember that we are just consumers of SimpleIcons. Decisions about changes and removals are made by the [SimpleIcons](https://github.com/simple-icons/simple-icons) project.
15 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-01-13-simpleicons11.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: simple-icons-11
 3 | title: Simple Icons 11
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | Logos on Shields.io are provided by SimpleIcons. We've recently upgraded to SimpleIcons 11. This release removes the following 4 icons:
13 | 
14 | - Babylon.js
15 | - Hulu
16 | - Pepsi
17 | - Uno
18 | 
19 | More details can be found in the [release notes](https://github.com/simple-icons/simple-icons/releases/tag/11.0.0).
20 | 
21 | Please remember that we are just consumers of SimpleIcons. Decisions about changes and removals are made by the [SimpleIcons](https://github.com/simple-icons/simple-icons) project.
22 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-06-01-simpleicons12.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: simple-icons-12
 3 | title: Simple Icons 12
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | Logos on Shields.io are provided by SimpleIcons. We've recently upgraded to SimpleIcons 12. This release removes the following 10 icons:
13 | 
14 | - FITE
15 | - Flattr
16 | - Google Bard
17 | - Integromat
18 | - Niantic
19 | - Nintendo Network
20 | - Rome
21 | - Shotcut
22 | - Skynet
23 | - Twitter
24 | 
25 | And renames the following 3:
26 | 
27 | - Airbrake.io to Airbrake
28 | - Amazon AWS to Amazon Web Services
29 | - RStudio to RStudio IDE
30 | 
31 | More details can be found in the [release notes](https://github.com/simple-icons/simple-icons/releases/tag/12.0.0).
32 | 
33 | Please remember that we are just consumers of SimpleIcons. Decisions about changes and removals are made by the [SimpleIcons](https://github.com/simple-icons/simple-icons) project.
34 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-07-05-simpleicons13.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: simple-icons-13
 3 | title: Simple Icons 13
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | Logos on Shields.io are provided by SimpleIcons. We've recently upgraded to SimpleIcons 13. This release removes 65 icons and renames one. A full list of the changes can be found in the [release notes](https://github.com/simple-icons/simple-icons/releases/tag/13.0.0).
13 | 
14 | Please remember that we are just consumers of SimpleIcons. Decisions about changes and removals are made by the [SimpleIcons](https://github.com/simple-icons/simple-icons) project.
15 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-07-10-sunsetting-shields-custom-logos.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: sunsetting-shields-custom-logos
 3 | title: Sunsetting Shields custom logos
 4 | authors:
 5 |   name: PyvesB
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/PyvesB
 8 |   image_url: https://avatars.githubusercontent.com/u/10694593
 9 | tags: []
10 | ---
11 | 
12 | Following discussions in [#9476](https://github.com/badges/shields/issues/9476), we've gone ahead and deleted all custom logos that were maintained on the Shields.io side (bitcoin, dependabot, gitlab, npm, paypal, serverfault, stackexchange, superuser, telegram, travis), and will solely rely on the [Simple-Icons project](https://github.com/simple-icons/simple-icons) to provide named logos for our badges from now on. If you were using a Shields custom logo, you will have transparently switched over to the corresponding Simple-Icon and do not need to make changes to your badges.
13 | 
14 | The reasons behind this decision include the following:
15 | 
16 | - reducing code complexity and induced overhead by deleting several dozens lines of code.
17 | - reducing maintenance load; we received regular pull requests to add logos that do not comply with our guidelines, or various other related questions.
18 | - providing a less confusing user experience; all named logos now behave in the same way with regards to `logoColor` and other parameters.
19 | - reducing frustration for contributors who prepared logo pull requests only to be told that they hadn't read the guidelines or that there was a misalignment on the interpretation of said guidelines.
20 | - reinforcing Shields.io's mission to provide consistent badges, with all named logos now being monochrome.
21 | - improving compliance with third-party brands; Simple-Icons regularly reviews whether their icons respect latest brand guidelines, whereas we do not.
22 | - unblocking [#4947](https://github.com/badges/shields/issues/4947).
23 | 
24 | We do acknowledge the fact that some of you voiced your preference for a given Shields custom logo over its Simple-Icons equivalent in [#7684](https://github.com/badges/shields/issues/7684). If you really want to go back to the Shields custom logo, you can leverage [custom logos](https://shields.io/docs/logos#custom-logos) to do so. Here are the corresponding Base64-encoded logo parameters for all our existing logos:
25 | 
26 | | Name          | Logo Preview                                                                                             | `logo` Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
27 | | ------------- | :------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
28 | | bitcoin       | ![bitcoin](https://github.com/badges/shields/assets/10694593/20ea99c4-a557-476c-91a8-3b886ce98e5e)       | `data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTIzLjYzNiAxNC45MDJjLTEuNjAyIDYuNDMtOC4xMTQgMTAuMzQyLTE0LjU0MyA4Ljc0QzIuNjY2IDIyLjAzNy0xLjI0NiAxNS41MjUuMzU3IDkuMDk4IDEuOTYgMi42NjkgOC40Ny0xLjI0NCAxNC44OTcuMzU5YzYuNDMgMS42MDIgMTAuMzQxIDguMTE1IDguNzM5IDE0LjU0NCIgZmlsbD0iI2Y3OTMxYSIvPjxwYXRoIGQ9Ik0xNC42ODYgMTAuMjY3Yy0uMzcxIDEuNDg3LTIuNjYzLjczMS0zLjQwNi41NDZsLjY1NS0yLjYyOWMuNzQzLjE4NiAzLjEzOC41MzEgMi43NSAyLjA4M20tLjQwNiA0LjI0MmMtLjQwNyAxLjYzNS0zLjE2Ljc1LTQuMDUzLjUzbC43MjQtMi45Yy44OTMuMjI0IDMuNzU0LjY2NCAzLjMzIDIuMzdtMy4wMDgtNC4yMTljLjIzOC0xLjU5Ni0uOTc3LTIuNDU1LTIuNjQtMy4wMjdsLjU0LTIuMTYzLTEuMzE4LS4zMy0uNTI1IDIuMTA3YTU0LjI5MiA1NC4yOTIgMCAwIDAtMS4wNTQtLjI0OWwuNTMtMi4xMi0xLjMxNy0uMzI4LS41NCAyLjE2MmMtLjI4Ni0uMDY1LS41NjctLjEzLS44NC0uMTk4bC4wMDEtLjAwNy0xLjgxNi0uNDUzLS4zNSAxLjQwNnMuOTc3LjIyNC45NTYuMjM4Yy41MzMuMTMzLjYzLjQ4Ni42MTMuNzY2bC0uNjE1IDIuNDYzYy4wMzguMDEuMDg1LjAyNC4xMzcuMDQ1bC0uMTM4LS4wMzUtLjg2MiAzLjQ1MmMtLjA2NS4xNjEtLjIzLjQwNS0uNjA0LjMxMi4wMTQuMDItLjk1Ny0uMjM5LS45NTctLjIzOUw1LjgzNiAxNS42bDEuNzE0LjQyN2MuMzE4LjA4LjYzLjE2NC45MzguMjQybC0uNTQ1IDIuMTkgMS4zMTUuMzI4LjU0LTIuMTY0Yy4zNi4wOTcuNzA4LjE4NyAxLjA1LjI3MWwtLjUzOCAyLjE1NiAxLjMxNi4zMjguNTQ2LTIuMTgzYzIuMjQ1LjQyNCAzLjkzMy4yNTMgNC42NDMtMS43NzcuNTc0LTEuNjM1LS4wMjctMi41NzgtMS4yMDgtMy4xOTQuODYtLjE5OCAxLjUwOC0uNzY1IDEuNjgxLTEuOTM0IiBmaWxsPSIjZmZmIi8+PC9zdmc+`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
29 | | dependabot    | ![dependabot](https://github.com/badges/shields/assets/10694593/5fb27ba4-f940-4782-bba0-8c01f98cce0e)    | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1NCA1NCIgZmlsbD0iI2ZmZiI+PHBhdGggZD0iTTI1IDNhMSAxIDAgMCAwLTEgMXY3YTEgMSAwIDAgMCAxIDFoNXYzSDZhMyAzIDAgMCAwLTMgM3YxMkgxYTEgMSAwIDAgMC0xIDF2MTBhMSAxIDAgMCAwIDEgMWgydjZhMyAzIDAgMCAwIDMgM2g0MmEzIDMgMCAwIDAgMy0zdi02aDJhMSAxIDAgMCAwIDEtMVYzMWExIDEgMCAwIDAtMS0xaC0yVjE4YTMgMyAwIDAgMC0zLTNIMzNWNGExIDEgMCAwIDAtMS0xaC03em0tMy45ODIgMjZhMS4yMSAxLjIxIDAgMCAxIC44MzcuMzU1bDEuMjkgMS4yOWExLjIxIDEuMjEgMCAwIDEgMCAxLjcwOSAxLjIxIDEuMjEgMCAwIDEgMCAuMDAxbC02LjI5MSA2LjI5YTEuMjEgMS4yMSAwIDAgMS0xLjcxIDBsLTMuNzktMy43OTFhMS4yMSAxLjIxIDAgMCAxIDAtMS43MWwxLjI5LTEuMjlhMS4yMSAxLjIxIDAgMCAxIDEuNzEgMEwxNiAzMy41bDQuMTQ1LTQuMTQ1YTEuMjEgMS4yMSAwIDAgMSAuODczLS4zNTV6bTE5Ljk2MiAwYTEuMjEgMS4yMSAwIDAgMSAuODc0LjM1NGwxLjI5IDEuMjlhMS4yMSAxLjIxIDAgMCAxIDAgMS43MWwtNi4yOSA2LjI4OXYuMDAyYTEuMjEgMS4yMSAwIDAgMS0xLjcxMSAwbC0zLjc5LTMuNzlhMS4yMSAxLjIxIDAgMCAxIDAtMS43MWwxLjI5LTEuMjlhMS4yMSAxLjIxIDAgMCAxIDEuNzEgMGwxLjY0NSAxLjY0NSA0LjE0Ny00LjE0NkExLjIxIDEuMjEgMCAwIDEgNDAuOTggMjl6Ii8+PC9zdmc+`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
30 | | gitlab        | ![gitlab](https://github.com/badges/shields/assets/10694593/e9c8e584-3860-4fe2-b802-2ed7c87f996f)        | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjkzIDkzIDE5NCAxOTQiPjxkZWZzPjxzdHlsZT4uYntmaWxsOiNmYzZkMjZ9PC9zdHlsZT48L2RlZnM+PHBhdGggc3R5bGU9ImZpbGw6I2UyNDMyOSIgZD0ibTI4Mi44MyAxNzAuNzMtLjI3LS42OS0yNi4xNC02OC4yMmE2LjgxIDYuODEgMCAwIDAtMi42OS0zLjI0IDcgNyAwIDAgMC04IC40MyA3IDcgMCAwIDAtMi4zMiAzLjUybC0xNy42NSA1NGgtNzEuNDdsLTE3LjY1LTU0YTYuODYgNi44NiAwIDAgMC0yLjMyLTMuNTMgNyA3IDAgMCAwLTgtLjQzIDYuODcgNi44NyAwIDAgMC0yLjY5IDMuMjRMOTcuNDQgMTcwbC0uMjYuNjlhNDguNTQgNDguNTQgMCAwIDAgMTYuMSA1Ni4xbC4wOS4wNy4yNC4xNyAzOS44MiAyOS44MiAxOS43IDE0LjkxIDEyIDkuMDZhOC4wNyA4LjA3IDAgMCAwIDkuNzYgMGwxMi05LjA2IDE5LjctMTQuOTEgNDAuMDYtMzAgLjEtLjA4YTQ4LjU2IDQ4LjU2IDAgMCAwIDE2LjA4LTU2LjA0WiIvPjxwYXRoIGNsYXNzPSJiIiBkPSJtMjgyLjgzIDE3MC43My0uMjctLjY5YTg4LjMgODguMyAwIDAgMC0zNS4xNSAxNS44TDE5MCAyMjkuMjVjMTkuNTUgMTQuNzkgMzYuNTcgMjcuNjQgMzYuNTcgMjcuNjRsNDAuMDYtMzAgLjEtLjA4YTQ4LjU2IDQ4LjU2IDAgMCAwIDE2LjEtNTYuMDhaIi8+PHBhdGggc3R5bGU9ImZpbGw6I2ZjYTMyNiIgZD0ibTE1My40MyAyNTYuODkgMTkuNyAxNC45MSAxMiA5LjA2YTguMDcgOC4wNyAwIDAgMCA5Ljc2IDBsMTItOS4wNiAxOS43LTE0LjkxUzIwOS41NSAyNDQgMTkwIDIyOS4yNWMtMTkuNTUgMTQuNzUtMzYuNTcgMjcuNjQtMzYuNTcgMjcuNjRaIi8+PHBhdGggY2xhc3M9ImIiIGQ9Ik0xMzIuNTggMTg1Ljg0QTg4LjE5IDg4LjE5IDAgMCAwIDk3LjQ0IDE3MGwtLjI2LjY5YTQ4LjU0IDQ4LjU0IDAgMCAwIDE2LjEgNTYuMWwuMDkuMDcuMjQuMTcgMzkuODIgMjkuODJMMTkwIDIyOS4yMVoiLz48L3N2Zz4=`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
31 | | npm           | ![npm](https://github.com/badges/shields/assets/10694593/ba629fa3-a467-4c96-b191-62c339faac66)           | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MCA0MCI+PHBhdGggZD0iTTAgMGg0MHY0MEgwVjB6IiBmaWxsPSIjY2IwMDAwIi8+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTcgN2gyNnYyNmgtN1YxNGgtNnYxOUg3eiIvPjwvc3ZnPgo=`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
32 | | paypal        | ![paypal](https://github.com/badges/shields/assets/10694593/f2eacc65-7a19-4816-8897-f7723a97b26f)        | `data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTE5LjcxNSA2LjEzM2MuMjQ5LTEuODY2IDAtMy4xMS0uOTk5LTQuMjY2QzE3LjYzNC42MjIgMTUuNzIxIDAgMTMuMzA3IDBINi4yMzVjLS40MTggMC0uOTE2LjQ0NC0xIC44ODlMMi4zMjMgMjAuNjIyYzAgLjM1Ni4yNS44LjY2NS44aDQuMzI4bC0uMjUgMS45NTZjLS4wODQuMzU1LjE2Ni42MjIuNDk4LjYyMmgzLjY2M2MuNDE3IDAgLjgzMi0uMjY3LjkxNS0uNzExdi0uMjY3bC43NDktNC42MjJ2LS4xNzhjLjA4My0uNDQ0LjUtLjguOTE1LS44aC41YzMuNTc4IDAgNi4zMjUtMS41MSA3LjE1Ni01Ljk1NS40MTgtMS44NjcuMjUyLTMuMzc4LS43NDctNC40NDUtLjI1LS4zNTUtLjY2Ni0uNjIyLTEtLjg4OSIgZmlsbD0iIzAwOWNkZSIvPjxwYXRoIGQ9Ik0xOS43MTUgNi4xMzNjLjI0OS0xLjg2NiAwLTMuMTEtLjk5OS00LjI2NkMxNy42MzQuNjIyIDE1LjcyMSAwIDEzLjMwNyAwSDYuMjM1Yy0uNDE4IDAtLjkxNi40NDQtMSAuODg5TDIuMzIzIDIwLjYyMmMwIC4zNTYuMjUuOC42NjUuOGg0LjMyOGwxLjE2NC03LjM3OC0uMDgzLjI2N2MuMDg0LS41MzMuNS0uODg5Ljk5OC0uODg5aDIuMDhjNC4wNzkgMCA3LjI0MS0xLjc3OCA4LjI0LTYuNzU1LS4wODMtLjI2NyAwLS4zNTYgMC0uNTM0IiBmaWxsPSIjMDEyMTY5Ii8+PHBhdGggZD0iTTkuNTYzIDYuMTMzYy4wODItLjI2Ni4yNS0uNTMzLjQ5OC0uNzEuMTY2IDAgLjI1LS4wOS40MTYtLjA5aDUuNDk0Yy42NjYgMCAxLjMzLjA5IDEuODMuMTc4LjE2NiAwIC4zMzMgMCAuNDk4LjA4OS4xNjguMDg5LjMzNC4wODkuNDE4LjE3OGguMjVjLjI0OC4wODkuNDk3LjI2Ni43NDguMzU1LjI0OC0xLjg2NiAwLTMuMTEtLjk5OS00LjM1NUMxNy43MTcuNTMzIDE1LjgwNCAwIDEzLjM5IDBINi4yMzVjLS40MTggMC0uOTE2LjM1Ni0xIC44ODlMMi4zMjMgMjAuNjIyYzAgLjM1Ni4yNS44LjY2NS44aDQuMzI4bDEuMTY0LTcuMzc4IDEuMDg0LTcuOTF6IiBmaWxsPSIjMDAzMDg3Ii8+PC9zdmc+`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
33 | | serverfault   | ![serverfault](https://github.com/badges/shields/assets/10694593/d1b7a0e5-2465-4009-ba5f-89f364554a46)   | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjAgMTIwIj48c3R5bGU+LnN0MHtmaWxsOiNhN2E5YWN9LnN0MXtmaWxsOiM4MTgyODV9LnN0MntmaWxsOiM1ODU4NWF9LnN0M3tmaWxsOiNkMWQyZDR9LnN0NHtmaWxsOiMyMzFmMjB9PC9zdHlsZT48cGF0aCBjbGFzcz0ic3QwIiBkPSJNMTMuNyA0MS42aDQ0djguN2gtNDR6Ii8+PHBhdGggY2xhc3M9InN0MSIgZD0iTTEzLjcgNTUuOGg0NHY4LjdoLTQ0eiIvPjxwYXRoIGNsYXNzPSJzdDIiIGQ9Ik0xMy43IDY5aDQ0djguN2gtNDR6Ii8+PHBhdGggY2xhc3M9InN0MyIgZD0iTTEzLjcgMjcuNmg0NHY4LjdoLTQ0eiIvPjxwYXRoIGNsYXNzPSJzdDQiIGQ9Ik0xMy43IDgzLjJoNDR2OC43aC00NHoiLz48cGF0aCBmaWxsPSIjOTkyMjI0IiBkPSJNNjMgNDEuNmgxOC43djguN0g2M3oiLz48cGF0aCBmaWxsPSIjNjMwZjE2IiBkPSJNNjMgNTUuOGgxOC43djguN0g2M3oiLz48cGF0aCBmaWxsPSIjMmIxNDE1IiBkPSJNNjMgNjloMTguN3Y4LjdINjN6Ii8+PHBhdGggZmlsbD0iI2U3MjgyZCIgZD0iTTYzIDI3LjZoMTguN3Y4LjdINjN6Ii8+PHBhdGggY2xhc3M9InN0NCIgZD0iTTYzIDgzLjJoMTguN3Y4LjdINjN6Ii8+PGc+PHBhdGggY2xhc3M9InN0MCIgZD0iTTg2LjggNDJoMTguN3Y4LjdIODYuOHoiLz48cGF0aCBjbGFzcz0ic3QxIiBkPSJNODYuOCA1Ni4yaDE4Ljd2OC43SDg2Ljh6Ii8+PHBhdGggY2xhc3M9InN0MiIgZD0iTTg2LjggNjkuNGgxOC43djguN0g4Ni44eiIvPjxwYXRoIGNsYXNzPSJzdDMiIGQ9Ik04Ni44IDI4aDE4Ljd2OC43SDg2Ljh6Ii8+PHBhdGggY2xhc3M9InN0NCIgZD0iTTg2LjggODMuNmgxOC43djguN0g4Ni44eiIvPjwvZz48L3N2Zz4=`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
34 | | stackexchange | ![stackexchange](https://github.com/badges/shields/assets/10694593/409644d3-4679-4f0d-9fb9-538215eec8c7) | `data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTIuMjczIDEwLjQ2M2gxOS4zMjV2My45NzhIMi4yNzN6IiBmaWxsPSIjMzc2ZGI2Ii8+PHBhdGggZD0iTTIuMjczIDUuMzIyaDE5LjMyNVY5LjNIMi4yNzN6IiBmaWxsPSIjNGNhMmRhIi8+PHBhdGggZD0iTTE4LjU3NSAwSDUuMzc0Yy0xLjcwNSAwLTMuMSAxLjQyLTMuMSAzLjE3OFY0LjIxaDE5LjMyNFYzLjE3OEMyMS41OTggMS40MiAyMC4yNTQgMCAxOC41NzUgMHoiIGZpbGw9IiM5MWQ4ZjQiLz48cGF0aCBkPSJNMi4yNzMgMTUuNTc4djEuMDMzYzAgMS43NTcgMS4zOTYgMy4xNzggMy4xIDMuMTc4aDguMjY4VjI0bDQuMDgxLTQuMjExaC45MDVjMS43MDUgMCAzLjEtMS40MiAzLjEtMy4xNzh2LTEuMDMzeiIgZmlsbD0iIzFlNTM5NyIvPjwvc3ZnPg==`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
35 | | superuser     | ![superuser](https://github.com/badges/shields/assets/10694593/f8d0b5ad-5b67-49f8-8989-59256baad56e)     | `data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTIuNTk0IDBhLjUxNC41MTQgMCAwIDAtLjM0NC4xMS40MDQuNDA0IDAgMCAwLS4xMzMuMzA2djIzLjE5N2MwIC4xMjQuMDQ4LjI0Ni4xNDUuMzEyLjA5Ni4wNjUuMjA4LjA3NS4zMzIuMDc1aDUuNTkzYy4xMyAwIC4yNDMtLjAyLjMzNC0uMDkzLjA5Mi0uMDcyLjEzMS0uMi4xMTItLjMxN2wuMDAyLjAyM3YtMS40NjdhLjM2Ny4zNjcgMCAwIDAtLjE2LS4zMDEuNjEyLjYxMiAwIDAgMC0uMzQ0LS4wODdINS42MTNjLS4xMSAwLS4xNy0uMDItLjE5MS0uMDM3LS4wMjItLjAxNi0uMDMyLS4wMy0uMDMyLS4xVjIuNDA4YzAtLjA3MS4wMTItLjA5NC4wNDEtLjExNi4wMy0uMDIzLjEwMi0uMDUuMjM5LS4wNWgyLjQ4OGMuMTI0IDAgLjIzNS0uMDEuMzMyLS4wNzYuMDk3LS4wNjYuMTQ1LS4xODguMTQ1LS4zMTFWLjQxNmEuMzk2LjM5NiAwIDAgMC0uMTU3LS4zMjNBLjU4My41ODMgMCAwIDAgOC4xMzEgMHoiIGZpbGw9IiMwMDAiLz48cGF0aCBkPSJNMjAuOTU4IDE0LjQ3Yy0xLjQ4Mi40MTQtMi40ODkgMS4yNzMtMi40ODkgMi42ODR2NC4wNDJjMCAzLjAxNy0yLjkwOSAyLjY4NS02LjUxNyAyLjY4NWgtLjU2Yy0uMjIzIDAtLjM2My0uMDgzLS4zNjMtLjI3N1YyMi4yMmMwLS4xOTQuMTEyLS4yNzcuMzM2LS4yNzdoLjQ0N2MyLjE1NCAwIDMuNjY0LjQ3IDMuNjY0LTEuMjQ1di0zLjg3NmMwLTEuMTkuODQtMi44NTEgMi41MTctMy40Ni4xMTItLjAyOC4xNC0uMDgzLjE0LS4xMzggMC0uMDU2LS4wMjgtLjEzOS0uMTQtLjE5NC0xLjUzOC0uNjkyLTIuNTE3LTEuODI3LTIuNTE3LTMuMTg0VjUuNDczYzAtMS42ODktMS41MS0zLjM3Ny0zLjY2NC0zLjM3N2gtLjQ0N2MtLjIyNCAwLS4zMzYtLjA4My0uMzM2LS4yNzdWLjQzNWMwLS4xOTQuMTQtLjI3Ny4zNjQtLjI3N2guNTZjMy42MDcgMCA2LjU0NCAyLjU0NyA2LjU0NCA1LjU2NHYzLjY4MmMwIDEuMzg0IDEuMDA3IDIuMTg2IDIuNTE3IDIuNzEyLjU2LjE2Ni44NjcuMTk0Ljg2Ny42Mzd2MS4xNjNjLjAyOC4yNDktLjI1MS4zNi0uOTIzLjU1MyIgZmlsbD0iIzJlYWNlMyIvPjxwYXRoIGQ9Ik0xMS41NzYgOC4zM2MtLjQwNiAwLS43ODUuMzAzLS43ODUuNzJ2MS4zMjhjMCAuMzg5LjM1LjcyMS43ODUuNzIxaDEuNDgyYy40MDYgMCAuNzg0LS4zMDQuNzg0LS43MlY5LjA1YzAtLjM4OC0uMzQ4LS43Mi0uNzg0LS43MnoiIGZpbGw9IiMwMDAiLz48L3N2Zz4=`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
36 | | telegram      | ![telegram](https://github.com/badges/shields/assets/10694593/c5c5acc3-f434-4a8d-a834-6d94a7ffb45a)      | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDI0YzYuNjI3IDAgMTItNS4zNzMgMTItMTJTMTguNjI3IDAgMTIgMCAwIDUuMzczIDAgMTJzNS4zNzMgMTIgMTIgMTJaIiBmaWxsPSJ1cmwoI2EpIi8+PHBhdGggZmlsbC1ydWxlPSJldmVub2RkIiBjbGlwLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik01LjQyNSAxMS44NzFhNzk2LjQxNCA3OTYuNDE0IDAgMCAxIDYuOTk0LTMuMDE4YzMuMzI4LTEuMzg4IDQuMDI3LTEuNjI4IDQuNDc3LTEuNjM4LjEgMCAuMzIuMDIuNDcuMTQuMTIuMS4xNS4yMy4xNy4zMy4wMi4xLjA0LjMxLjAyLjQ3LS4xOCAxLjg5OC0uOTYgNi41MDQtMS4zNiA4LjYyMi0uMTcuOS0uNSAxLjE5OS0uODE5IDEuMjI5LS43LjA2LTEuMjI5LS40Ni0xLjg5OC0uOS0xLjA2LS42ODktMS42NDktMS4xMTktMi42NzgtMS43OTgtMS4xOS0uNzgtLjQyLTEuMjA5LjI2LTEuOTA4LjE4LS4xOCAzLjI0Ny0yLjk3OCAzLjMwNy0zLjIyOC4wMS0uMDMuMDEtLjE1LS4wNi0uMjEtLjA3LS4wNi0uMTctLjA0LS4yNS0uMDItLjExLjAyLTEuNzg4IDEuMTQtNS4wNTYgMy4zNDgtLjQ4LjMzLS45MDkuNDktMS4yOTkuNDgtLjQzLS4wMS0xLjI0OC0uMjQtMS44NjgtLjQ0LS43NS0uMjQtMS4zNDktLjM3LTEuMjk5LS43OS4wMy0uMjIuMzMtLjQ0Ljg5LS42NjlaIiBmaWxsPSIjZmZmIi8+PGRlZnM+PGxpbmVhckdyYWRpZW50IGlkPSJhIiB4MT0iMTEuOTkiIHkxPSIwIiB4Mj0iMTEuOTkiIHkyPSIyMy44MSIgZ3JhZGllbnRVbml0cz0idXNlclNwYWNlT25Vc2UiPjxzdG9wIHN0b3AtY29sb3I9IiMyQUFCRUUiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiMyMjlFRDkiLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48L3N2Zz4K`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
37 | | travis        | ![travis](https://github.com/badges/shields/assets/10694593/67110d9b-b825-4ef7-85ff-1bba963121e1)        | `data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNjYuNyIgaGVpZ2h0PSIyNjQuNSI+PHBhdGggZmlsbD0iI2NkMjQ0NSIgZD0iTTY0IDExNXMtNDIgMzAtNDMgNDFsMy0xczQ5LTMzIDg5LTM3bDEtNS01MCAybTY1LTQtMzMgMjMgMiAyIDU4LTE5IDEyLTctMzkgMW0yOCAyOGMyMyAwIDU4LTIyIDU4LTIybC0xMS0zaC0xOGwtOC0zLTIwIDIzLTIgNCAxIDFtLTk4IDg2LTMtMnptMTc0LTEzLTcgMi0zMy0xLTIxLTE2LTI1IDYtMjktMi0xNiAxNy0zMSAxMC0xNS01LTEtMSA3IDE3czE2IDE2IDI0IDE4YzkgMiAyNCAwIDM2LTIgMTItMSAyMS02IDI1LTEybDQtOXMxMSAxNiAyMSAxN2MxMCAyIDM4LTggMzgtOHMxOC00IDIxLTEwbDExLTI2LTkgNSIvPjxwYXRoIGZpbGw9IiNmMmYxOWIiIGQ9Ik0yNjEgOTNhNjYgNjYgMCAwIDAgMC00bC04LTZhMTA2IDEwNiAwIDAgMC0yMC05bC01LTItNS0yIDExIDNhMTQ0IDE0NCAwIDAgMSA2IDJjLTE2LTQzLTU0LTcwLTk2LTcwLTQzIDAtODEgMjctOTcgNzBhMTQ1IDE0NSAwIDAgMSAxNy01bC01IDJhMjAwIDIwMCAwIDAgMC0zMiAxN2wtMSAyYTcwIDcwIDAgMCAwIDAgMiA2OSA2OSAwIDAgMCAwIDYgNzkgNzkgMCAwIDAgMyAyMSA1NyA1NyAwIDAgMCAxIDUgNDMgNDMgMCAwIDAgMiA0bDEgMSAxIDEgNCAxLTMtMTIgMTYtM2E1MiA1MiAwIDAgMS0zLTFsLTYtMmEzMCAzMCAwIDAgMS0zLTFsLTMtMmMxMSAzIDMzIDIgNTMgMGE1MzggNTM4IDAgMCAxIDEwOCAwYzIwIDIgNDIgMyA1MyAwbC0zIDJhMzAgMzAgMCAwIDEtMyAxbC03IDItMSAxIDE4IDMtMyAxMWgybDEtMSAxLTFhMjIgMjIgMCAwIDAgMi00IDU2IDU2IDAgMCAwIDItNSA3OCA3OCAwIDAgMCAyLTIxIDY4IDY4IDAgMCAwIDAtNiIvPjxwYXRoIGZpbGw9IiNlNWM5YTMiIGQ9Ik0xNTYgMjQ0YTU4IDU4IDAgMCAxLTUgMGgtM2E3NzYgNzc2IDAgMCAwIDMtNiAxOTggMTk4IDAgMCAwIDUgNm0zIDNjNCA0IDEwIDcgMTYgNy0xMCA0LTIwIDYtMjcgNi04IDEtMTUgMC0yMi0yYTI3IDI3IDAgMCAxIDEgMGMxLTEgMTQtMiAyMC0xMWg1YTU4IDU4IDAgMCAwIDYtMWwxIDEiLz48cGF0aCBmaWxsPSIjNWQ2NzYyIiBkPSJNMTcxIDExNmExMjggMTI4IDAgMCAxLTEyIDEzIDQ5MyA0OTMgMCAwIDAtMTUgMGwtMjQgMWExOTcgMTk3IDAgMCAxIDUxLTE0bS02NSA1LTEyIDExYTQ4MCA0ODAgMCAwIDAtMjkgM2MxMi01IDI2LTEwIDQxLTE0bTEzNiAyMy01IDMyLTIxIDE1LTU3LTctOC0yOGEyIDIgMCAwIDAtMS0xIDM1IDM1IDAgMCAwLTExIDAgMiAyIDAgMCAwLTIgMWwtOCAyOC01NiAxMi0yMi0xNi01LTM1YTI2NyAyNjcgMCAwIDEgMy0yaDVsNCAzMyAxIDEgMTUgMTFhMiAyIDAgMCAwIDEgMGw0Ni0xMGgxYTIgMiAwIDAgMCAxLTFsOC0yOCAxMy0yIDEzIDIgOCAyOCAyIDEgNDYgNWgxbDE1LTExIDEtMSA0LTI5IDggMm02LTIwLTQgMTVjLTgtMi0yNi01LTUxLTdsMjQtMTMgMzEgNSIvPjxwYXRoIGZpbGw9IiNlNGM4OTYiIGQ9Im0xNTQgMTM0LTcgNS04IDVhNjkgNjkgMCAwIDAtMTAgMiAyIDIgMCAwIDAtMSAxbC04IDI4LTQ1IDktMTQtOS00LTMzIDMyLTVhNzYgNzYgMCAwIDAtNCA1bC04IDExIDExLTdzNy01IDE5LTEwYTUwMyA1MDMgMCAwIDEgNDctMnptLTY5IDM3IDEyLTFhNDAgNDAgMCAwIDAgNCAwYzYgMCAxMCAwIDEwLTlzLTQtMTYtOS0xNmMtNiAwLTEyIDctMTEgMTZsMSA2Yy01IDEtNyA0LTcgNG0xNDYtMjktNCAyOC0xNCA5LTQ1LTUtOC0yN2EyIDIgMCAwIDAtMS0xbC0xMi0yaDFjMSAwIDE3LTIgMzUtOCAyMCAxIDM2IDQgNDggNnptLTI5IDI2YzAtMS0xLTQtNi00bDEtNWMtMS05LTYtMTYtMTItMTZzLTkgNy05IDE2IDUgOSAxMSA5YzcgMCAxMi0yIDE1IDAiLz48cGF0aCBmaWxsPSIjYzRhZjkwIiBkPSJtMTU0IDEzNC03IDUtOCA1YTY5IDY5IDAgMCAwLTEwIDIgMiAyIDAgMCAwLTEgMWwtOCAyOC00NSA5LTE0LTktNC0zMyAzMi01YTc2IDc2IDAgMCAwLTQgNWwtOCAxMSAxMS03czctNSAxOS0xMGE1MDMgNTAzIDAgMCAxIDQ3LTJ6bS02OSAzNyAxMi0xYTQwIDQwIDAgMCAwIDQgMGM2IDAgMTAgMCAxMC05cy00LTE2LTktMTZjLTYgMC0xMiA3LTExIDE2bDEgNmMtNSAxLTcgNC03IDRtMTQ2LTI5LTQgMjgtMTQgOS00NS01LTgtMjdhMiAyIDAgMCAwLTEtMWwtMTItMmgxYzEgMCAxNy0yIDM1LTggMjAgMSAzNiA0IDQ4IDZ6bS0yOSAyNmMwLTEtMS00LTYtNGwxLTVjLTEtOS02LTE2LTEyLTE2cy05IDctOSAxNiA1IDkgMTEgOWM3IDAgMTItMiAxNSAwIi8+PHBhdGggZmlsbD0iI2U1YzlhMyIgZD0ibTI1MCAxNTQgMSA5Yy0xIDgtNSAyMi03IDI1bC0xMC0xIDEtNSA1LTQgMS0xIDQtMjYgNSAzTTU1IDE4OHYzbC0xMSAxYy0yLTItNi0xNy03LTI1di05bDctMyAzIDI3IDEgMSA3IDVtMTA3IDB2MnMtNyA2LTE2IDdjLTEwIDEtMTgtNS0xOC01bDMgNmE3MSA3MSAwIDAgMC04LTFoLTRjLTYgMC0xNCAxMC0yMCAxOWwtMjMgN2MtMTAtMTQtMTUtMjgtMTUtMjlsLTEtMiAzIDIgNiA0IDIgMmEyIDIgMCAwIDAgMiAwbDU4LTEzYTIgMiAwIDAgMCAxLTFsOC0yN2EyOCAyOCAwIDAgMSA4IDBsOCAyOCAyIDFoNCIvPjxwYXRoIGZpbGw9IiNlNWM5YTMiIGQ9Im0yMjggMTg3IDItMmExMjAgMTIwIDAgMCAxLTEwIDI3aC0zbC04LTEtMTYtMi0xNi0xMi0xLTFjLTEtMS0yLTItNS0ybC0xNCAzYzUtMyA1LTcgNS03di0ybDU0IDZhMiAyIDAgMCAwIDEgMGw2LTQgNS0zIi8+PHBhdGggZmlsbD0iI2U5ZDU4NiIgZD0iTTE4OCA3MmMwIDUgMCAxNC0yIDIyYTIgMiAwIDAgMCAwIDEgMzQ2IDM0NiAwIDAgMC05LTFjMy02IDQtMTQgNC0xNmw3LTZtLTgyIDZjMCAyIDEgMTAgNCAxNmEzMzMgMzMzIDAgMCAwLTkgMGMtMi04LTItMTctMi0yMmw3IDYiLz48cGF0aCBmaWxsPSIjMmEyYzMwIiBkPSJNMTg0IDE1NGEzIDMgMCAwIDAgMy0zIDMgMyAwIDAgMC0zLTIgMyAzIDAgMCAwLTMgMyAzIDMgMCAwIDAgMyAyem0xOCAxNGMtMy0yLTggMC0xNSAwLTYgMC0xMSAwLTExLTlzMy0xNiA5LTE2IDExIDcgMTIgMTZsLTEgNWM1IDAgNiAzIDYgNCIvPjxwYXRoIGZpbGw9IiNmMWZhZmMiIGQ9Ik0xODQgMTQ5YTMgMyAwIDEgMSAwIDUgMyAzIDAgMSAxIDAtNSIvPjxwYXRoIGZpbGw9IiMyYTJjMzAiIGQ9Ik0xMDIgMTU3YTMgMyAwIDEgMCAwLTYgMyAzIDAgMCAwIDAgNnptOSA0YzAgOS00IDktMTAgOWgtNGwtMTIgMXMyLTMgNy00bC0xLTZjLTEtOSA1LTE2IDExLTE2IDUgMCA5IDcgOSAxNiIvPjxwYXRoIGZpbGw9IiNmMWZhZmMiIGQ9Ik0xMDIgMTUxYTMgMyAwIDEgMSAwIDYgMyAzIDAgMCAxIDAtNiIvPjxwYXRoIGZpbGw9IiNlYmRiOGIiIGQ9Im02NiAxMDEtMS0xdi0zbDItMjAgMzAtNyAyIDI1Yy0xLTItNC02LTUtMTMtMS0zLTMtNC02LTRsLTcgMWMtNCAxLTEwIDMtMTEgNS0yIDUtMiAxNi0yIDE2bC0yIDFtMTU1IDAtMS0xcy0xLTExLTMtMTZjLTEtMi03LTQtMTEtNWwtNy0xYy0zIDAtNSAxLTYgNC0xIDctMyAxMS01IDEzbDItMjUgMzAgNyAyIDE3djZsLTEgMSIvPjxwYXRoIGZpbGw9IiNlYmRjOGMiIGQ9Im0xNzQgOTctNjAtMS0zLTctMy0xMi01LTRWNDVsNy0yMHMxIDYwIDE1IDYwaDM3YzE0IDAgMTUtNjAgMTUtNjBsMTAgMzQtNyAxOS0xIDUtMiA5LTMgNW02MiAxMC0zLTEgMyAxbS0zLTEtMTEtNFY4MXMzIDIxIDExIDI1Ii8+PHBhdGggZmlsbD0iI2VhZDY4NyIgZD0iTTIyMiAxMDB2LTYgNiIvPjxwYXRoIGZpbGw9IiNlYmRjOGMiIGQ9Im01MSAxMDcgNC0xLTQgMW00LTFjNy00IDEwLTI1IDEwLTI1djIxbC0xMCA0Ii8+PHBhdGggZmlsbD0iI2VhZDY4NyIgZD0iTTY1IDEwMHYtMyAzIi8+PHBhdGggZmlsbD0iIzJhMmMzMCIgZD0iTTk4IDk2di0xYy0zLTktMy0xOS0yLTI0bC0yOCA4Yy0yIDEyLTEgMjAgMCAyMmExODUgMTg1IDAgMCAxIDYtMiAyMjkgMjI5IDAgMCAxIDIzLTNoMXptMTItMmMtMy02LTQtMTQtNC0xNmwtNy02YTc3IDc3IDAgMCAwIDIgMjNsOS0xem03NiAwYzItOCAyLTE3IDItMjJsLTcgNmMwIDItMSAxMC00IDE2bDkgMWEyIDIgMCAwIDEgMC0xem0zNCA3YzAtMSAxLTEwLTEtMjJsLTI4LThjMSA1IDEgMTUtMiAyNHYxaDFhMjI4IDIyOCAwIDAgMSAzMCA1em00IDEgMTEgNS02LTJhOTQgOTQgMCAwIDAtNS0xIDE3NSAxNzUgMCAwIDAtMjMtM2wtMTItMWE3NjEgNzYxIDAgMCAwLTkxIDBsLTEyIDFhMjQyIDI0MiAwIDAgMC0zNCA2bDExLTVoMWMwLTEtMS0xMSAxLTI1YTIgMiAwIDAgMSAxLTFsNC0yYzEtMzAgMTMtNDQgMTQtNDRhODMgODMgMCAwIDAtMTEgNDRsMjQtN2gybDIgMmMtMS04IDAtMzEgMTEtNTAtMSAxLTkgMjYtNiA1NGE0NSA0NSAwIDAgMCAzIDJ2MnMxIDkgNSAxN2E0NDQgNDQ0IDAgMCAxIDU5IDBjNC04IDUtMTcgNS0xN2EyIDIgMCAwIDEgMC0yIDQ5IDQ5IDAgMCAwIDMtMmMzLTI4LTUtNTMtNS01NCAxMCAxOSAxMSA0MiAxMSA1MGE4MyA4MyAwIDAgMCAxLTJoMmwyNCA3YzAtNSAwLTI2LTExLTQ0IDEgMCAxMyAxNCAxNCA0NGw0IDJhMiAyIDAgMCAxIDEgMWMzIDE0IDEgMjQgMSAyNWgxIi8+PHBhdGggZmlsbD0iIzJhMmMzMCIgZD0iTTE2OCA0M1YzMGgtNDd2MTNoNnYtNmgxM3Y0MGgtNXY3aDE4di03aC01VjM3aDEzdjZ6bTQtMTh2MjNoLTE2di03aC0zdjMxaDV2MTdoLTI4VjcyaDVWNDFoLTN2N2gtMTZWMjVoNTYiLz48cGF0aCBmaWxsPSIjY2QyNDQ1IiBkPSJNMTY4IDMwdjEzaC03di02aC0xM3Y0MGg1djdoLTE4di03aDVWMzdoLTEzdjZoLTZWMzBoNDciLz48cGF0aCBmaWxsPSIjNWQ2NzYyIiBkPSJtNDEgMTI0IDktMmExMzkgMTM5IDAgMCAwLTggNmwtMS00Ii8+PHBhdGggZmlsbD0iI2M0YWY5MCIgZD0iTTEyNyAxODZzMCA1LTUgNmMtNiAyLTQ0IDEzLTQ4IDEzbC0xNS04LTMtOSAxNiAxMCA1NS0xMm0zMyAwczAgNCA2IDVsNDggMTFjNC0xIDE1LTkgMTUtOWwyLTktMTUgOC01Ni02Ii8+PHBhdGggZmlsbD0iI2M0YWY5MCIgZD0iTTM4IDE3OXM1IDEwIDEzIDZsNiAzdjRsLTEzIDItMy0yLTMtMTNtMjEyLTNzLTggMTEtMTcgN2wtMiAydjRsMTMgMiAzLTIgMy0xM20tMTMxIDgxczMxIDE2IDY2LTVsLTEyLTFzLTI0IDEwLTQzIDRsLTExIDIiLz48cGF0aCBmaWxsPSIjMmEyYzMwIiBkPSJNNTAgMTIyYTMwNSAzMDUgMCAwIDAtOSAybDEgNGExMzkgMTM5IDAgMCAxIDgtNnptNSA2OWE5MSA5MSAwIDAgMSAwLTNsLTctNWEyIDIgMCAwIDEtMS0xbC0zLTI3LTcgM3Y5YzEgOCA1IDIzIDcgMjVsMTEtMXptNDItNzMgMTUtM2ExMTczIDExNzMgMCAwIDAtNDUgMmMtNiA0LTI4IDE4LTQzIDM2IDE1LTEwIDQwLTI2IDczLTM1em0tMyAxNCAxMi0xMWMtMTUgNC0yOSA5LTQxIDE0YTQ4MSA0ODEgMCAwIDEgMjktM3ptNTgtMThoLTIzbC04IDRjLTEgMS0xMiA2LTIzIDE2IDktNSAyMy0xMSAzOS0xNmExOTIgMTkyIDAgMCAxIDE1LTR6bS01IDI1IDctNWE1NjMgNTYzIDAgMCAwLTEwIDAgNTAyIDUwMiAwIDAgMC0zNyAyYy0xMiA1LTE5IDEwLTE5IDEwbC0xMSA3IDgtMTFhNzAgNzAgMCAwIDEgNC01bC0zMiA1IDQgMzMgMTQgOSA0NS05IDgtMjhhMiAyIDAgMCAxIDEtMWwxMC0yem00IDEwNWg1YTE4NSAxODUgMCAwIDEtNS02IDUzMSA1MzEgMCAwIDEtMyA2aDN6bTI0IDEwYTI1IDI1IDAgMCAxLTE3LThsLTYgMWgtNWMtNiA5LTE5IDEwLTIwIDExaC0xYzcgMiAxNCAzIDIyIDIgNyAwIDE3LTIgMjctNnptLTUtMTM2IDEtMmExNTAgMTUwIDAgMCAwLTEzIDJjLTE0IDMtMjcgNy0zOCAxMmE1MTEgNTExIDAgMCAxIDI0LTFoMTVsMTEtMTF6bTQwLTFhNzM1IDczNSAwIDAgMC0xMy0xbC0xOS0xLTIgM2MtMyA0LTEwIDEzLTE4IDE5IDEyLTIgMzMtNyA1MC0xOWwyLTF6bTIwIDY4LTIgMi01IDMtNiA0YTIgMiAwIDAgMS0xIDBsLTU0LTZoLTRhMiAyIDAgMCAxLTItMWwtOC0yOGEyOCAyOCAwIDAgMC04IDBsLTggMjdhMiAyIDAgMCAxLTEgMWwtNTggMTNoLTJsLTItMi02LTQtMy0yIDEgMmMwIDEgNSAxNSAxNSAyOWExMTY2IDExNjYgMCAwIDAgMjMtN2M2LTkgMTQtMTkgMjAtMTlhNjggNjggMCAwIDEgNCAwbDggMS0zLTZzOCA2IDE4IDVjOS0xIDE2LTcgMTYtN3MwIDQtNSA3bDE0LTNjMyAwIDQgMSA1IDJsMSAxYTQ2MjYgNDYyNiAwIDAgMSAxNiAxMiA4MTYgODE2IDAgMCAwIDI3IDMgMTM0IDEzNCAwIDAgMCAxMC0yN3ptLTMtMTUgNC0yOGMtMTItMi0yOC01LTQ4LTYtMTggNi0zNCA4LTM1IDhoLTFsMTIgMiAxIDEgOCAyNyA0NSA1em0xMCA2IDUtMzJhMzIxIDMyMSAwIDAgMC04LTJsLTQgMjlhMiAyIDAgMCAxLTEgMWwtMTUgMTFoLTFsLTQ2LTVhMiAyIDAgMCAxLTItMWwtOC0yOC0xMy0yLTEzIDItOCAyOGEyIDIgMCAwIDEtMiAxbC00NiAxMGgtMWwtMTUtMTFhMiAyIDAgMCAxLTEtMWwtNC0zM2EzMjkgMzI5IDAgMCAwLTUgMGwtMyAyIDUgMzUgMjIgMTYgNTYtMTIgOC0yOCAyLTFhMzUgMzUgMCAwIDEgMTEgMGwxIDEgOCAyOCA1NyA3em03LTM3IDQtMTUtMzEtNS0yNCAxM2MyNSAyIDQzIDUgNTEgN3ptNyAyNC0xLTktNS0zLTQgMjYtMSAxLTUgNC0xIDUgMTAgMWMyLTMgNi0xNyA3LTI1em0xNi02NC0xIDExYTc0IDc0IDAgMCAxLTIgMTIgNjAgNjAgMCAwIDEtMiA1IDUxIDUxIDAgMCAxLTEgM2wtMSAyLTEgMXYxaC0xYTQ1IDQ1IDAgMCAxLTEgMWwtMiAxLTQgMWE4NCA4NCAwIDAgMC0yIDFsLTIgN2gtMWwtMSAxIDggNGMzIDIgMyA2IDMgMTNsLTQgMTdjLTIgMTEtNCAxMy02IDEzYTE3IDE3IDAgMCAxLTQgMWwtMTAtMWMwIDMtMyA5LTcgMTdoMWwxNS03IDctMy0zIDctMTQgMjZjLTUgMTAtMTQgMTItMjAgMTNsLTIgMS0yMCA1YTg1IDg1IDAgMCAxLTE1IDdjLTE5IDctMzkgNy01OCAwbC0xMiAyYTYwIDYwIDAgMCAxLTcgMGMtMTggMC0yNy05LTM0LTE4bC0xNi0yNC02LTggOSA0IDIwIDEwIDEtMWMtNi04LTExLTE4LTE0LTI5bC0xMSAyaC0zYy0yLTEtNC0zLTgtMTNsLTMtMTdjLTEtNy0xLTEwIDItMTNsOS01di0yYy0xOSAxMS0zMCAyMC0zMCAyMUwwIDE3OWw5LTE1YzgtMTEgMTYtMjEgMjQtMjhoLTFsLTItMWE0NyA0NyAwIDAgMS0xLTFoLTF2LTFsLTEtMS0xLTJhNDEgNDEgMCAwIDEtMS0zIDYwIDYwIDAgMCAxLTItNSA3MyA3MyAwIDAgMS0yLTEyIDczIDczIDAgMCAxIDAtMTEgNjkgNjkgMCAwIDEgMS0xMnYtMWgxYzMtMyA2LTQgMTAtNmExMDUgMTA1IDAgMCAxIDgtM2M4LTIyIDIyLTQyIDQwLTU2YTEwNCAxMDQgMCAwIDEgMTI2IDBjMTcgMTQgMzEgMzQgMzkgNTZsOCAzYzQgMiA3IDMgMTAgNmgxdjFhMzYgMzYgMCAwIDEgMSA2bDEgNnpNNTQgNzRhMTkyIDE5MiAwIDAgMC0yNyAxNWwtMSAyYTY4IDY4IDAgMCAwIDAgMiA3MCA3MCAwIDAgMCAwIDYgODAgODAgMCAwIDAgNiAzMGwxIDEgMSAxIDQgMS0zLTEyIDE2LTNhNDUgNDUgMCAwIDEtMy0xIDQ5IDQ5IDAgMCAxLTktM2wtMy0yYzExIDMgMzMgMiA1MyAwYTU0MCA1NDAgMCAwIDEgMTA4IDBjMjAgMiA0MiAzIDUzIDBsLTMgMi0zIDEtNyAyLTEgMSAxOCAzLTMgMTFoMmwxLTEgMS0xYTI4IDI4IDAgMCAwIDItNCA1NiA1NiAwIDAgMCAyLTUgNzcgNzcgMCAwIDAgMi0yMSA3MCA3MCAwIDAgMCAwLTYgNjkgNjkgMCAwIDAgMC0ydi0ybC04LTZhMTA3IDEwNyAwIDAgMC0yMC05bC01LTItNS0yYTEyNCAxMjQgMCAwIDEgMTcgNWMtMTYtNDMtNTQtNzAtOTYtNzAtNDMgMC04MSAyNy05NyA3MGExNDQgMTQ0IDAgMCAxIDE3LTUgMjQ4IDI0OCAwIDAgMC0xMCA0em05NiAxNTUgMiAyIDExIDEyYzQgMyA4IDUgMTQgNWg1bDYtMmE2OTQgNjk0IDAgMCAwIDIyLTVjNS0xIDEyLTMgMTYtMTFsMTAtMTgtNyAzYy0zIDItNyAyLTEyIDJoLTlsLTE2LTJoLTFsLTEtMS0xNy0xM3YtMWgtMmwtMjQgN2gtMnMtMTAtNC0yMi00aC0zYy0xIDAtOCAzLTE3IDE3djFoLTFhMTA2MCAxMDYwIDAgMCAxLTMxIDlsLTEgMS0xLTEtMTItNSAxMSAxNWM2IDggMTQgMTUgMjkgMTVoNmwyMi0zaDJzMTItMiAxNi0xMGw0LTEwIDItM3YtMmwxIDIiLz48L3N2Zz4=` |
38 | 
39 | Feel free to reach out to us if you have any questions, and happy badging!
40 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-09-25-rce.md:
--------------------------------------------------------------------------------
  1 | ---
  2 | slug: GHSA-rxvx-x284-4445
  3 | title: Our response to RCE Security Advisory
  4 | authors:
  5 |   name: chris48s
  6 |   title: Shields.io Core Team
  7 |   url: https://github.com/chris48s
  8 |   image_url: https://avatars.githubusercontent.com/u/6025893
  9 | tags: []
 10 | ---
 11 | 
 12 | We've just published a critical security advisory relating to a Remote Code Execution vulnerability in Dynamic JSON/TOML/YAML badges: https://github.com/badges/shields/security/advisories/GHSA-rxvx-x284-4445 Thanks to [@nickcopi](https://github.com/nickcopi) for his help with this.
 13 | 
 14 | If you self-host your own instance of Shields you should upgrade to [server-2024-09-25](https://hub.docker.com/layers/shieldsio/shields/server-2024-09-25/images/sha256-28aaea75049e325c9f1d63c8a8b477fc387d3d3fe35b933d6581487843cd610f?context=explore) or later as soon as possible to protect your instance.
 15 | 
 16 | This is primarily a concern for self-hosting users. However this does also have a couple of knock-on implications for some users of shields.io itself.
 17 | 
 18 | ## 1. Users who have authorized the Shields.io GitHub OAuth app
 19 | 
 20 | While we have taken steps to close this vulnerability quickly after becoming aware of it, this attack vector has existed in our application for some time. We aren't aware of it having been actively exploited on shields.io. We also can't prove that it has not been exploited.
 21 | 
 22 | We don't log or track our users, so a breach offers a very limited attack surface against end users of shields.io. This is by design. One of the (few) information assets shields.io does hold is our GitHub token pool. This allows users to share a token with us by authorizing our OAuth app. Doing this gives us access to a token with read-only access to public data which we can use to increase our rate limit when making calls to the GitHub API.
 23 | 
 24 | The tokens we hold are not of high value to an attacker because they have read-only access to public data, but we can't say for sure they haven't been exfiltrated. If you've donated a token in the past and want to revoke it, you can revoke the Shields.io OAuth app at https://github.com/settings/applications which will de-activate the token you have shared with us.
 25 | 
 26 | ## 2. Users of Dynamic JSON/TOML/YAML badges
 27 | 
 28 | Up until now, we have been using https://github.com/dchester/jsonpath as our library querying documents using JSONPath expressions. [@nickcopi](https://github.com/nickcopi) responsibly reported to us how a prototype pollution vulnerability in this library could be exploited to construct a JSONPath expression allowing an attacker to perform remote code execution. This vulnerability was reported on the package's issue tracker but not flagged by security scanning tools. It seems extremely unlikely that this will be fixed in the upstream package despite being widely used. It also seems unlikely this package will receive any further maintenance in future, even in response to critical security issues. In order to resolve this issue, we needed to switch to a different JSONPath library. We've decided to switch https://github.com/JSONPath-Plus/JSONPath using the `eval: false` option to disable script expressions.
 29 | 
 30 | This is an important security improvement and we have to make a change to protect the security of shields.io and users hosting their own instance of the application. However, this does come with some tradeoffs from a backwards-compatibility perspective.
 31 | 
 32 | ### Using `eval: false`
 33 | 
 34 | Using JSONPath-Plus with `eval: false` does disable some query syntax which relies on evaluating javascript expressions.
 35 | 
 36 | For example, it would previously have been possible to use a JSONPath query like `$..keywords[(@.length-1)]` against the document https://github.com/badges/shields/raw/master/package.json to select the last element from the keywords array https://github.com/badges/shields/blob/e237e40ab88b8ad4808caad4f3dae653822aa79a/package.json#L6-L12
 37 | 
 38 | This is now not a supported query.
 39 | 
 40 | In this particular case, you could rewrite that query to `$..keywords[-1:]` and obtain the same result, but that may not be possible in all cases. We do realise that this removes some functionality that previously worked but closing this remote code execution vulnerability is the top priority, especially since there will be workarounds in many cases.
 41 | 
 42 | ### Implementation Quirks
 43 | 
 44 | Historically, every JSONPath implementation has had its own idiosyncrasies. While most simple and common queries will behave the same way across different implementations, switching to another library will mean that some subset of queries may not work or produce different results.
 45 | 
 46 | One interesting thing that has happened in the world of JSONPath lately is RFC 9535 https://www.rfc-editor.org/rfc/rfc9535 which is an attempt to standardise JSONPath. As part of this mitigation, we did look at whether it would be possible to migrate to something that is RFC9535-compliant. However it is our assessment that the JavaScript community does not yet have a sufficiently mature/supported RFC9535-compliant JSONPath implementation. This means we are switching from one quirky implementation to another implementation with different quirks.
 47 | 
 48 | Again, this represents an unfortunate break in backwards-compatibility. However, it was necessary to prioritise closing off this remote code execution vulnerability over backwards-compatibility.
 49 | 
 50 | Although we can not provide a precise migration guide, here is a table of query types where https://github.com/dchester/jsonpath and https://github.com/JSONPath-Plus/JSONPath are known to diverge from the consensus implementation. This is sourced from the excellent https://cburgmer.github.io/json-path-comparison/
 51 | While this is a long list, many of these inputs represent edge cases or pathological inputs rather than common usage.
 52 | 
 53 |  <details>
 54 |   <summary>Table</summary>
 55 | <table>
 56 | <thead>
 57 | <tr>
 58 | <th>Query Type</th>
 59 | <th>Example Query</th>
 60 | </tr>
 61 | </thead>
 62 | <tbody>
 63 | <tr>
 64 | <td>Array slice with large number for end and negative step</td>
 65 | <td><code>$[2:-113667776004:-1]</code></td>
 66 | </tr>
 67 | <tr>
 68 | <td>Array slice with large number for start end negative step</td>
 69 | <td><code>$[113667776004:2:-1]</code></td>
 70 | </tr>
 71 | <tr>
 72 | <td>Array slice with negative step</td>
 73 | <td><code>$[3:0:-2]</code></td>
 74 | </tr>
 75 | <tr>
 76 | <td>Array slice with negative step on partially overlapping array</td>
 77 | <td><code>$[7:3:-1]</code></td>
 78 | </tr>
 79 | <tr>
 80 | <td>Array slice with negative step only</td>
 81 | <td><code>$[::-2]</code></td>
 82 | </tr>
 83 | <tr>
 84 | <td>Array slice with open end and negative step</td>
 85 | <td><code>$[3::-1]</code></td>
 86 | </tr>
 87 | <tr>
 88 | <td>Array slice with open start and negative step</td>
 89 | <td><code>$[:2:-1]</code></td>
 90 | </tr>
 91 | <tr>
 92 | <td>Array slice with range of 0</td>
 93 | <td><code>$[0:0]</code></td>
 94 | </tr>
 95 | <tr>
 96 | <td>Array slice with step 0</td>
 97 | <td><code>$[0:3:0]</code></td>
 98 | </tr>
 99 | <tr>
100 | <td>Array slice with step and leading zeros</td>
101 | <td><code>$[010:024:010]</code></td>
102 | </tr>
103 | <tr>
104 | <td>Bracket notation with empty path</td>
105 | <td><code>$[]</code></td>
106 | </tr>
107 | <tr>
108 | <td>Bracket notation with number on object</td>
109 | <td><code>$[0]</code></td>
110 | </tr>
111 | <tr>
112 | <td>Bracket notation with number on string</td>
113 | <td><code>$[0]</code></td>
114 | </tr>
115 | <tr>
116 | <td>Bracket notation with number -1</td>
117 | <td><code>$[-1]</code></td>
118 | </tr>
119 | <tr>
120 | <td>Bracket notation with quoted array slice literal</td>
121 | <td><code>$[':']</code></td>
122 | </tr>
123 | <tr>
124 | <td>Bracket notation with quoted closing bracket literal</td>
125 | <td><code>$[']']</code></td>
126 | </tr>
127 | <tr>
128 | <td>Bracket notation with quoted current object literal</td>
129 | <td><code>$['@']</code></td>
130 | </tr>
131 | <tr>
132 | <td>Bracket notation with quoted escaped backslash</td>
133 | <td><code>$['\\']</code></td>
134 | </tr>
135 | <tr>
136 | <td>Bracket notation with quoted escaped single quote</td>
137 | <td><code>$['\'']</code></td>
138 | </tr>
139 | <tr>
140 | <td>Bracket notation with quoted root literal</td>
141 | <td><code>$['$']</code></td>
142 | </tr>
143 | <tr>
144 | <td>Bracket notation with quoted special characters combined</td>
145 | <td><code>$[':@."$,*\'\\']</code></td>
146 | </tr>
147 | <tr>
148 | <td>Bracket notation with quoted string and unescaped single quote</td>
149 | <td><code>$['single'quote']</code></td>
150 | </tr>
151 | <tr>
152 | <td>Bracket notation with quoted union literal</td>
153 | <td><code>$[',']</code></td>
154 | </tr>
155 | <tr>
156 | <td>Bracket notation with quoted wildcard literal ?</td>
157 | <td><code>$['*']</code></td>
158 | </tr>
159 | <tr>
160 | <td>Bracket notation with quoted wildcard literal on object without key</td>
161 | <td><code>$['*']</code></td>
162 | </tr>
163 | <tr>
164 | <td>Bracket notation with spaces</td>
165 | <td><code>$[ 'a' ]</code></td>
166 | </tr>
167 | <tr>
168 | <td>Bracket notation with two literals separated by dot</td>
169 | <td><code>$['two'.'some']</code></td>
170 | </tr>
171 | <tr>
172 | <td>Bracket notation with two literals separated by dot without quotes</td>
173 | <td><code>$[two.some]</code></td>
174 | </tr>
175 | <tr>
176 | <td>Bracket notation without quotes</td>
177 | <td><code>$[key]</code></td>
178 | </tr>
179 | <tr>
180 | <td>Current with dot notation</td>
181 | <td><code>@.a</code></td>
182 | </tr>
183 | <tr>
184 | <td>Dot bracket notation</td>
185 | <td><code>$.['key']</code></td>
186 | </tr>
187 | <tr>
188 | <td>Dot bracket notation with double quotes</td>
189 | <td><code>$.["key"]</code></td>
190 | </tr>
191 | <tr>
192 | <td>Dot bracket notation without quotes</td>
193 | <td><code>$.[key]</code></td>
194 | </tr>
195 | <tr>
196 | <td>Dot notation after recursive descent with extra dot ?</td>
197 | <td><code>$...key</code></td>
198 | </tr>
199 | <tr>
200 | <td>Dot notation after union with keys</td>
201 | <td><code>$['one','three'].key</code></td>
202 | </tr>
203 | <tr>
204 | <td>Dot notation with dash</td>
205 | <td><code>$.key-dash</code></td>
206 | </tr>
207 | <tr>
208 | <td>Dot notation with double quotes</td>
209 | <td><code>$."key"</code></td>
210 | </tr>
211 | <tr>
212 | <td>Dot notation with double quotes after recursive descent ?</td>
213 | <td><code>$.."key"</code></td>
214 | </tr>
215 | <tr>
216 | <td>Dot notation with empty path</td>
217 | <td><code>$.</code></td>
218 | </tr>
219 | <tr>
220 | <td>Dot notation with key named length on array</td>
221 | <td><code>$.length</code></td>
222 | </tr>
223 | <tr>
224 | <td>Dot notation with key root literal</td>
225 | <td><code>$.$</code></td>
226 | </tr>
227 | <tr>
228 | <td>Dot notation with non ASCII key</td>
229 | <td><code>$.??</code></td>
230 | </tr>
231 | <tr>
232 | <td>Dot notation with number</td>
233 | <td><code>$.2</code></td>
234 | </tr>
235 | <tr>
236 | <td>Dot notation with number -1</td>
237 | <td><code>$.-1</code></td>
238 | </tr>
239 | <tr>
240 | <td>Dot notation with single quotes</td>
241 | <td><code>$.'key'</code></td>
242 | </tr>
243 | <tr>
244 | <td>Dot notation with single quotes after recursive descent ?</td>
245 | <td><code>$..'key'</code></td>
246 | </tr>
247 | <tr>
248 | <td>Dot notation with single quotes and dot</td>
249 | <td><code>$.'some.key'</code></td>
250 | </tr>
251 | <tr>
252 | <td>Dot notation with space padded key</td>
253 | <td><code>$. a</code></td>
254 | </tr>
255 | <tr>
256 | <td>Dot notation with wildcard after recursive descent on scalar ?</td>
257 | <td><code>$..*</code></td>
258 | </tr>
259 | <tr>
260 | <td>Dot notation without dot</td>
261 | <td><code>$a</code></td>
262 | </tr>
263 | <tr>
264 | <td>Dot notation without root</td>
265 | <td><code>.key</code></td>
266 | </tr>
267 | <tr>
268 | <td>Dot notation without root and dot</td>
269 | <td><code>key</code></td>
270 | </tr>
271 | <tr>
272 | <td>Empty</td>
273 | <td><code>n/a</code></td>
274 | </tr>
275 | <tr>
276 | <td>Filter expression on object</td>
277 | <td><code>$[?(@.key)]</code></td>
278 | </tr>
279 | <tr>
280 | <td>Filter expression after dot notation with wildcard after recursive descent ?</td>
281 | <td><code>$..*[?(@.id&gt;2)]</code></td>
282 | </tr>
283 | <tr>
284 | <td>Filter expression after recursive descent ?</td>
285 | <td><code>$..[?(@.id==2)]</code></td>
286 | </tr>
287 | <tr>
288 | <td>Filter expression with addition</td>
289 | <td><code>$[?(@.key+50==100)]</code></td>
290 | </tr>
291 | <tr>
292 | <td>Filter expression with boolean and operator and value false</td>
293 | <td><code>$[?(@.key&gt;0 &amp;&amp; false)]</code></td>
294 | </tr>
295 | <tr>
296 | <td>Filter expression with boolean and operator and value true</td>
297 | <td><code>$[?(@.key&gt;0 &amp;&amp; true)]</code></td>
298 | </tr>
299 | <tr>
300 | <td>Filter expression with boolean or operator and value false</td>
301 | <td><code>$[?(@.key&gt;0 &amp;#124;&amp;#124; false)]</code></td>
302 | </tr>
303 | <tr>
304 | <td>Filter expression with boolean or operator and value true</td>
305 | <td><code>$[?(@.key&gt;0 &amp;#124;&amp;#124; true)]</code></td>
306 | </tr>
307 | <tr>
308 | <td>Filter expression with bracket notation with -1</td>
309 | <td><code>$[?(@[-1]==2)]</code></td>
310 | </tr>
311 | <tr>
312 | <td>Filter expression with bracket notation with number on object</td>
313 | <td><code>$[?(@[1]=='b')]</code></td>
314 | </tr>
315 | <tr>
316 | <td>Filter expression with current object</td>
317 | <td><code>$[?(@)]</code></td>
318 | </tr>
319 | <tr>
320 | <td>Filter expression with different ungrouped operators</td>
321 | <td><code>$[?(@.a &amp;&amp; @.b &amp;#124;&amp;#124; @.c)]</code></td>
322 | </tr>
323 | <tr>
324 | <td>Filter expression with division</td>
325 | <td><code>$[?(@.key/10==5)]</code></td>
326 | </tr>
327 | <tr>
328 | <td>Filter expression with dot notation with dash</td>
329 | <td><code>$[?(@.key-dash == 'value')]</code></td>
330 | </tr>
331 | <tr>
332 | <td>Filter expression with dot notation with number</td>
333 | <td><code>$[?(@.2 == 'second')]</code></td>
334 | </tr>
335 | <tr>
336 | <td>Filter expression with dot notation with number on array</td>
337 | <td><code>$[?(@.2 == 'third')]</code></td>
338 | </tr>
339 | <tr>
340 | <td>Filter expression with empty expression</td>
341 | <td><code>$[?()]</code></td>
342 | </tr>
343 | <tr>
344 | <td>Filter expression with equals</td>
345 | <td><code>$[?(@.key==42)]</code></td>
346 | </tr>
347 | <tr>
348 | <td>Filter expression with equals on array of numbers</td>
349 | <td><code>$[?(@==42)]</code></td>
350 | </tr>
351 | <tr>
352 | <td>Filter expression with equals on object</td>
353 | <td><code>$[?(@.key==42)]</code></td>
354 | </tr>
355 | <tr>
356 | <td>Filter expression with equals array</td>
357 | <td><code>$[?(@.d==["v1","v2"])]</code></td>
358 | </tr>
359 | <tr>
360 | <td>Filter expression with equals array for array slice with range 1</td>
361 | <td><code>$[?(@[0:1]==[1])]</code></td>
362 | </tr>
363 | <tr>
364 | <td>Filter expression with equals array for dot notation with star</td>
365 | <td><code>$[?(@.*==[1,2])]</code></td>
366 | </tr>
367 | <tr>
368 | <td>Filter expression with equals array or equals true</td>
369 | <td><code>$[?(@.d==["v1","v2"] &amp;#124;&amp;#124; (@.d == true))]</code></td>
370 | </tr>
371 | <tr>
372 | <td>Filter expression with equals array with single quotes</td>
373 | <td><code>$[?(@.d==['v1','v2'])]</code></td>
374 | </tr>
375 | <tr>
376 | <td>Filter expression with equals boolean expression value</td>
377 | <td><code>$[?((@.key&lt;44)==false)]</code></td>
378 | </tr>
379 | <tr>
380 | <td>Filter expression with equals false</td>
381 | <td><code>$[?(@.key==false)]</code></td>
382 | </tr>
383 | <tr>
384 | <td>Filter expression with equals null</td>
385 | <td><code>$[?(@.key==null)]</code></td>
386 | </tr>
387 | <tr>
388 | <td>Filter expression with equals number for array slice with range 1</td>
389 | <td><code>$[?(@[0:1]==1)]</code></td>
390 | </tr>
391 | <tr>
392 | <td>Filter expression with equals number for bracket notation with star</td>
393 | <td><code>$[?(@[*]==2)]</code></td>
394 | </tr>
395 | <tr>
396 | <td>Filter expression with equals number for dot notation with star</td>
397 | <td><code>$[?(@.*==2)]</code></td>
398 | </tr>
399 | <tr>
400 | <td>Filter expression with equals number with fraction</td>
401 | <td><code>$[?(@.key==-0.123e2)]</code></td>
402 | </tr>
403 | <tr>
404 | <td>Filter expression with equals number with leading zeros</td>
405 | <td><code>$[?(@.key==010)]</code></td>
406 | </tr>
407 | <tr>
408 | <td>Filter expression with equals object</td>
409 | <td><code>$[?(@.d==&lbrace;"k":"v"&rbrace;)]</code></td>
410 | </tr>
411 | <tr>
412 | <td>Filter expression with equals string</td>
413 | <td><code>$[?(@.key=="value")]</code></td>
414 | </tr>
415 | <tr>
416 | <td>Filter expression with equals string with unicode character escape</td>
417 | <td><code>$[?(@.key=="Mot\u00f6rhead")]</code></td>
418 | </tr>
419 | <tr>
420 | <td>Filter expression with equals true</td>
421 | <td><code>$[?(@.key==true)]</code></td>
422 | </tr>
423 | <tr>
424 | <td>Filter expression with equals with path and path</td>
425 | <td><code>$[?(@.key1==@.key2)]</code></td>
426 | </tr>
427 | <tr>
428 | <td>Filter expression with equals with root reference</td>
429 | <td><code>$.items[?(@.key==$.value)]</code></td>
430 | </tr>
431 | <tr>
432 | <td>Filter expression with greater than</td>
433 | <td><code>$[?(@.key&gt;42)]</code></td>
434 | </tr>
435 | <tr>
436 | <td>Filter expression with greater than or equal</td>
437 | <td><code>$[?(@.key&gt;=42)]</code></td>
438 | </tr>
439 | <tr>
440 | <td>Filter expression with in array of values</td>
441 | <td><code>$[?(@.d in [2, 3])]</code></td>
442 | </tr>
443 | <tr>
444 | <td>Filter expression with in current object</td>
445 | <td><code>$[?(2 in @.d)]</code></td>
446 | </tr>
447 | <tr>
448 | <td>Filter expression with length free function</td>
449 | <td><code>$[?(length(@) == 4)]</code></td>
450 | </tr>
451 | <tr>
452 | <td>Filter expression with length function</td>
453 | <td><code>$[?(@.length() == 4)]</code></td>
454 | </tr>
455 | <tr>
456 | <td>Filter expression with length property</td>
457 | <td><code>$[?(@.length == 4)]</code></td>
458 | </tr>
459 | <tr>
460 | <td>Filter expression with less than</td>
461 | <td><code>$[?(@.key&lt;42)]</code></td>
462 | </tr>
463 | <tr>
464 | <td>Filter expression with less than or equal</td>
465 | <td><code>$[?(@.key&lt;=42)]</code></td>
466 | </tr>
467 | <tr>
468 | <td>Filter expression with local dot key and null in data</td>
469 | <td><code>$[?(@.key='value')]</code></td>
470 | </tr>
471 | <tr>
472 | <td>Filter expression with multiplication</td>
473 | <td><code>$[?(@.key*2==100)]</code></td>
474 | </tr>
475 | <tr>
476 | <td>Filter expression with negation and equals</td>
477 | <td><code>$[?(!(@.key==42))]</code></td>
478 | </tr>
479 | <tr>
480 | <td>Filter expression with negation and equals array or equals true</td>
481 | <td><code>$[?(!(@.d==["v1","v2"]) &amp;#124;&amp;#124; (@.d == true))]</code></td>
482 | </tr>
483 | <tr>
484 | <td>Filter expression with negation and less than</td>
485 | <td><code>$[?(!(@.key&lt;42))]</code></td>
486 | </tr>
487 | <tr>
488 | <td>Filter expression with negation and without value</td>
489 | <td><code>$[?(!@.key)]</code></td>
490 | </tr>
491 | <tr>
492 | <td>Filter expression with non singular existence test</td>
493 | <td><code>$[?(@.a.*)]</code></td>
494 | </tr>
495 | <tr>
496 | <td>Filter expression with not equals</td>
497 | <td><code>$[?(@.key!=42)]</code></td>
498 | </tr>
499 | <tr>
500 | <td>Filter expression with not equals array or equals true</td>
501 | <td><code>$[?((@.d!=["v1","v2"]) &amp;#124;&amp;#124; (@.d == true))]</code></td>
502 | </tr>
503 | <tr>
504 | <td>Filter expression with parent axis operator</td>
505 | <td><code>$[*].bookmarks[?(@.page == 45)]^^^</code></td>
506 | </tr>
507 | <tr>
508 | <td>Filter expression with regular expression</td>
509 | <td><code>$[?(@.name=~/hello.*/)]</code></td>
510 | </tr>
511 | <tr>
512 | <td>Filter expression with regular expression from member</td>
513 | <td><code>$[?(@.name=~/@.pattern/)]</code></td>
514 | </tr>
515 | <tr>
516 | <td>Filter expression with set wise comparison to scalar</td>
517 | <td><code>$[?(@[*]&gt;=4)]</code></td>
518 | </tr>
519 | <tr>
520 | <td>Filter expression with set wise comparison to set</td>
521 | <td><code>$.x[?(@[*]&gt;=$.y[*])]</code></td>
522 | </tr>
523 | <tr>
524 | <td>Filter expression with single equal</td>
525 | <td><code>$[?(@.key=42)]</code></td>
526 | </tr>
527 | <tr>
528 | <td>Filter expression with subfilter</td>
529 | <td><code>$[?(@.a[?(@.price&gt;10)])]</code></td>
530 | </tr>
531 | <tr>
532 | <td>Filter expression with subpaths deeply nested</td>
533 | <td><code>$[?(@.a.b.c==3)]</code></td>
534 | </tr>
535 | <tr>
536 | <td>Filter expression with subtraction</td>
537 | <td><code>$[?(@.key-50==-100)]</code></td>
538 | </tr>
539 | <tr>
540 | <td>Filter expression with triple equal</td>
541 | <td><code>$[?(@.key===42)]</code></td>
542 | </tr>
543 | <tr>
544 | <td>Filter expression with value</td>
545 | <td><code>$[?(@.key)]</code></td>
546 | </tr>
547 | <tr>
548 | <td>Filter expression with value after recursive descent ?</td>
549 | <td><code>$..[?(@.id)]</code></td>
550 | </tr>
551 | <tr>
552 | <td>Filter expression with value false</td>
553 | <td><code>$[?(false)]</code></td>
554 | </tr>
555 | <tr>
556 | <td>Filter expression with value from recursive descent</td>
557 | <td><code>$[?(@..child)]</code></td>
558 | </tr>
559 | <tr>
560 | <td>Filter expression with value null</td>
561 | <td><code>$[?(null)]</code></td>
562 | </tr>
563 | <tr>
564 | <td>Filter expression with value true</td>
565 | <td><code>$[?(true)]</code></td>
566 | </tr>
567 | <tr>
568 | <td>Filter expression without parens</td>
569 | <td><code>$[?@.key==42]</code></td>
570 | </tr>
571 | <tr>
572 | <td>Filter expression without value</td>
573 | <td><code>$[?(@.key)]</code></td>
574 | </tr>
575 | <tr>
576 | <td>Function sum</td>
577 | <td><code>$.data.sum()</code></td>
578 | </tr>
579 | <tr>
580 | <td>Parens notation</td>
581 | <td><code>$(key,more)</code></td>
582 | </tr>
583 | <tr>
584 | <td>Recursive descent ?</td>
585 | <td><code>$..</code></td>
586 | </tr>
587 | <tr>
588 | <td>Recursive descent after dot notation ?</td>
589 | <td><code>$.key..</code></td>
590 | </tr>
591 | <tr>
592 | <td>Root on scalar</td>
593 | <td><code>$</code></td>
594 | </tr>
595 | <tr>
596 | <td>Root on scalar false</td>
597 | <td><code>$</code></td>
598 | </tr>
599 | <tr>
600 | <td>Root on scalar true</td>
601 | <td><code>$</code></td>
602 | </tr>
603 | <tr>
604 | <td>Script expression</td>
605 | <td><code>$[(@.length-1)]</code></td>
606 | </tr>
607 | <tr>
608 | <td>Union with duplication from array</td>
609 | <td><code>$[0,0]</code></td>
610 | </tr>
611 | <tr>
612 | <td>Union with duplication from object</td>
613 | <td><code>$['a','a']</code></td>
614 | </tr>
615 | <tr>
616 | <td>Union with filter</td>
617 | <td><code>$[?(@.key&lt;3),?(@.key&gt;6)]</code></td>
618 | </tr>
619 | <tr>
620 | <td>Union with keys</td>
621 | <td><code>$['key','another']</code></td>
622 | </tr>
623 | <tr>
624 | <td>Union with keys on object without key</td>
625 | <td><code>$['missing','key']</code></td>
626 | </tr>
627 | <tr>
628 | <td>Union with keys after array slice</td>
629 | <td><code>$[:]['c','d']</code></td>
630 | </tr>
631 | <tr>
632 | <td>Union with keys after bracket notation</td>
633 | <td><code>$[0]['c','d']</code></td>
634 | </tr>
635 | <tr>
636 | <td>Union with keys after dot notation with wildcard</td>
637 | <td><code>$.*['c','d']</code></td>
638 | </tr>
639 | <tr>
640 | <td>Union with keys after recursive descent ?</td>
641 | <td><code>$..['c','d']</code></td>
642 | </tr>
643 | <tr>
644 | <td>Union with repeated matches after dot notation with wildcard</td>
645 | <td><code>$.*[0,:5]</code></td>
646 | </tr>
647 | <tr>
648 | <td>Union with slice and number</td>
649 | <td><code>$[1:3,4]</code></td>
650 | </tr>
651 | <tr>
652 | <td>Union with spaces</td>
653 | <td><code>$[ 0 , 1 ]</code></td>
654 | </tr>
655 | <tr>
656 | <td>Union with wildcard and number</td>
657 | <td><code>$[*,1]</code></td>
658 | </tr>
659 | </tbody>
660 | </table>
661 | </details>
662 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-11-14-token-pool.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | slug: token-pool
 3 | title: How shields.io uses the GitHub API
 4 | authors:
 5 |   name: chris48s
 6 |   title: Shields.io Core Team
 7 |   url: https://github.com/chris48s
 8 |   image_url: https://avatars.githubusercontent.com/u/6025893
 9 | tags: []
10 | ---
11 | 
12 | We serve a lot of badges which display information fetched from the GitHub API. When I say a lot, this varies a bit but in a typical hour we make hundreds of thousands of calls to the GitHub API.
13 | 
14 | But hang on. GitHub's API has rate limits.
15 | 
16 | Specifically, users can make up to [5,000 requests per hour](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api?apiVersion=2022-11-28#primary-rate-limit-for-authenticated-users) to GitHub's v3/REST API. The v4/GraphQL also applies rate limits, but it is based on a slightly more complicated [points-based system](https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api#primary-rate-limit).
17 | 
18 | In any case, we are clearly making many times more requests to GitHub's API than would be allowed with a single token.
19 | 
20 | So how are we doing that? Well, we have lots of tokens. To elaborate on that slightly, as a user of shields.io you can choose to share a token with us to help increase our rate limit. Here's how it works:
21 | 
22 | - Authorize our [OAuth Application](https://img.shields.io/github-auth).
23 | - This shares with us a GitHub token which has read-only access to public data. We only ask for the minimum permissions necessary. Authorizing the OAuth app doesn't allow us access to your private data or allow us to perform any actions on your behalf.
24 | - Your token is added to a pool of tokens shared by other users like you.
25 | - When we need to make a request to the GitHub API, we pick one of the tokens from our pool. We only make a handful of requests with each token before picking another from the pool.
26 | - If you ever decide you would not like to continue sharing a token with us, you can revoke the Shields.io OAuth app at https://github.com/settings/applications. You can do this at any time. This will de-activate the token you have shared with us and we'll remove it from the pool.
27 | 
28 | This method allows us (with your help) to make hundreds of thousands of request per hour to the GitHub API. Because we have thousands of tokens in the pool and we only make a few requests with each one before picking another token from the pool, most users don't notice any meaningful impact on their available rate limit as a result of authorizing our app.
29 | 


--------------------------------------------------------------------------------
/frontend/blog/2024-12-27-simpleicons14.md:
--------------------------------------------------------------------------------
/frontend/categories/.gitkeep:
--------------------------------------------------------------------------------
https://raw.githubusercontent.com/badges/shields/master/frontend/categories/.gitkeep


--------------------------------------------------------------------------------
/frontend/docs/index.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | sidebar_position: 1
 3 | ---
 4 | 
 5 | # Intro
 6 | 
 7 | Shields.io is a service for concise, consistent, and legible badges, which can easily be included in GitHub readmes or any other web page. The service supports dozens of continuous integration services, package registries, distributions, app stores, social networks, code coverage services, and code analysis services. It is used by some of the world's most popular open-source projects.
 8 | 
 9 | Browse a [complete list of badges](/badges) and locate a particular badge by using the search bar or by browsing the categories.
10 | 
11 | Use the builder to fill in required path parameters for that badge type (like your username or repo) and optionally customize (label, colors etc.). And it's ready for use! Copy your badge url or code snippet, which can then be added to places like your GitHub readme files or other web pages.
12 | 
13 | ![screenshot of the badge builder](/img/builder.png)
14 | 


--------------------------------------------------------------------------------
/frontend/docs/logos.md:
--------------------------------------------------------------------------------
 1 | ---
 2 | sidebar_position: 2
 3 | ---
 4 | 
 5 | # Logos
 6 | 
 7 | ## SimpleIcons
 8 | 
 9 | We support a wide range of logos via [SimpleIcons](https://simpleicons.org/). All simple-icons are referenced using icon slugs. e.g:
10 | 
11 | ![](https://img.shields.io/npm/v/npm.svg?logo=nodedotjs) - https://img.shields.io/npm/v/npm.svg?logo=nodedotjs
12 | 
13 | You can click the icon title on <a href="https://simpleicons.org/" rel="noopener noreferrer" target="_blank">simple-icons</a> to copy the slug or they can be found in the <a href="https://github.com/simple-icons/simple-icons/blob/master/slugs.md">slugs.md file</a> in the simple-icons repository. NB - the Simple Icons site and slugs.md page may at times contain new icons that haven't yet been pulled into Shields.io yet. More information on how and when we incorporate icon updates can be found [here](https://github.com/badges/shields/discussions/5369).
14 | 
15 | ## Custom Logos
16 | 
17 | Any custom logo can be passed in a URL parameter by base64 encoding it. e.g:
18 | 
19 | ![](https://img.shields.io/badge/play-station-blue.svg?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEiIHdpZHRoPSI2MDAiIGhlaWdodD0iNjAwIj48cGF0aCBkPSJNMTI5IDExMWMtNTUgNC05MyA2Ni05MyA3OEwwIDM5OGMtMiA3MCAzNiA5MiA2OSA5MWgxYzc5IDAgODctNTcgMTMwLTEyOGgyMDFjNDMgNzEgNTAgMTI4IDEyOSAxMjhoMWMzMyAxIDcxLTIxIDY5LTkxbC0zNi0yMDljMC0xMi00MC03OC05OC03OGgtMTBjLTYzIDAtOTIgMzUtOTIgNDJIMjM2YzAtNy0yOS00Mi05Mi00MmgtMTV6IiBmaWxsPSIjZmZmIi8+PC9zdmc+) - https://img.shields.io/badge/play-station-blue.svg?logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEiIHdpZHRoPSI2MDAiIGhlaWdodD0iNjAwIj48cGF0aCBkPSJNMTI5IDExMWMtNTUgNC05MyA2Ni05MyA3OEwwIDM5OGMtMiA3MCAzNiA5MiA2OSA5MWgxYzc5IDAgODctNTcgMTMwLTEyOGgyMDFjNDMgNzEgNTAgMTI4IDEyOSAxMjhoMWMzMyAxIDcxLTIxIDY5LTkxbC0zNi0yMDljMC0xMi00MC03OC05OC03OGgtMTBjLTYzIDAtOTIgMzUtOTIgNDJIMjM2YzAtNy0yOS00Mi05Mi00MmgtMTV6IiBmaWxsPSIjZmZmIi8+PC9zdmc+
20 | 
21 | ## logoColor parameter
22 | 
23 | The `logoColor` param can be used to set the color of the SimpleIcons named logo. Hex, rgb, rgba, hsl, hsla and css named colors can all be used.
24 | 
25 | - ![](https://img.shields.io/badge/logo-javascript-blue?logo=javascript) - https://img.shields.io/badge/logo-javascript-blue?logo=javascript
26 | - ![](https://img.shields.io/badge/logo-javascript-blue?logo=javascript&logoColor=f5f5f5) - https://img.shields.io/badge/logo-javascript-blue?logo=javascript&logoColor=f5f5f5
27 | 


--------------------------------------------------------------------------------
/frontend/docs/static-badges.md:
--------------------------------------------------------------------------------
 1 | # Static Badges
 2 | 
 3 | It is possible to use shields.io to make a wide variety of badges displaying static text and/or logos. For example:
 4 | 
 5 | - ![any text you like](https://img.shields.io/badge/any%20text-you%20like-blue) - https://img.shields.io/badge/any%20text-you%20like-blue
 6 | - ![just the message](https://img.shields.io/badge/just%20the%20message-8A2BE2) - https://img.shields.io/badge/just%20the%20message-8A2BE2
 7 | - !['for the badge' style](https://img.shields.io/badge/%27for%20the%20badge%27%20style-20B2AA?style=for-the-badge) - https://img.shields.io/badge/%27for%20the%20badge%27%20style-20B2AA?style=for-the-badge
 8 | - ![with a logo](https://img.shields.io/badge/with%20a%20logo-grey?style=for-the-badge&logo=javascript) - https://img.shields.io/badge/with%20a%20logo-grey?style=for-the-badge&logo=javascript
 9 | 
10 | For more info, see:
11 | 
12 | - [Static badge builder](/badges/static-badge), including full documentation of styles and parameters
13 | - [Logos](/docs/logos)
14 | 


--------------------------------------------------------------------------------
/frontend/docusaurus.config.cjs:
--------------------------------------------------------------------------------
/frontend/package.json:
--------------------------------------------------------------------------------
 1 | {
 2 |   "name": "badge-frontend",
 3 |   "version": "0.0.0",
 4 |   "description": "Shields.io frontend",
 5 |   "private": true,
 6 |   "homepage": "https://shields.io",
 7 |   "license": "CC0-1.0",
 8 |   "repository": {
 9 |     "type": "git",
10 |     "url": "git+https://github.com/badges/shields.git",
11 |     "directory": "frontend"
12 |   },
13 |   "scripts": {
14 |     "test": "echo 'Run tests from parent dir'; false"
15 |   }
16 | }
17 | 


--------------------------------------------------------------------------------
/frontend/sidebars.cjs:
--------------------------------------------------------------------------------
 1 | /**
 2 |  * Creating a sidebar enables you to:
 3 |  * - create an ordered group of docs
 4 |  * - render a sidebar for each doc of that group
 5 |  * - provide next/previous navigation
 6 |  *
 7 |  * The sidebars can be generated from the filesystem, or explicitly defined here.
 8 |  *
 9 |  * Create as many sidebars as you want.
10 |  */
11 | 
12 | // @ts-check
13 | 
14 | /** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
15 | const sidebars = {
16 |   // By default, Docusaurus generates a sidebar from the docs folder structure
17 |   tutorialSidebar: [{ type: 'autogenerated', dirName: '.' }],
18 | 
19 |   // But you can create a sidebar manually
20 |   /*
21 |   tutorialSidebar: [
22 |     {
23 |       type: 'category',
24 |       label: 'Tutorial',
25 |       items: ['hello'],
26 |     },
27 |   ],
28 |    */
29 | }
30 | 
31 | module.exports = sidebars
32 | 


--------------------------------------------------------------------------------
/frontend/src/components/homepage-features.js:
--------------------------------------------------------------------------------
 1 | import React from 'react'
 2 | import clsx from 'clsx'
 3 | import styles from './homepage-features.module.css'
 4 | 
 5 | const FeatureList = [
 6 |   {
 7 |     title: 'Dynamic badges',
 8 |     description: (
 9 |       <>
10 |         <img
11 |           alt="build:passing"
12 |           src="https://img.shields.io/badge/build-passing-brightgreen"
13 |         />
14 |         <br />
15 |         Show metrics for your project. We've got badges for hundreds of
16 |         services.
17 |       </>
18 |     ),
19 |   },
20 |   {
21 |     title: 'Static Badges',
22 |     description: (
23 |       <>
24 |         Create a badge with
25 |         <br />
26 |         <img
27 |           alt="any text you like"
28 |           src="https://img.shields.io/badge/any%20text-you%20like-blue"
29 |         />
30 |       </>
31 |     ),
32 |   },
33 |   {
34 |     title: 'Badge-Maker NPM library',
35 |     description: (
36 |       <>
37 |         Render badges in your own application using our{' '}
38 |         <a
39 |           href="https://www.npmjs.com/package/badge-maker"
40 |           rel="noreferrer"
41 |           target="_blank"
42 |         >
43 |           NPM library
44 |         </a>
45 |         <br />
46 |         <code>npm install badge-maker</code>
47 |       </>
48 |     ),
49 |   },
50 |   {
51 |     title: 'Host your own instance',
52 |     description: (
53 |       <>
54 |         Host a shields instance behind your firewall with our{' '}
55 |         <a
56 |           href="https://registry.hub.docker.com/r/shieldsio/shields/"
57 |           rel="noreferrer"
58 |           target="_blank"
59 |         >
60 |           docker image
61 |         </a>
62 |       </>
63 |     ),
64 |   },
65 |   {
66 |     title: 'Love Shields?',
67 |     description: (
68 |       <>
69 |         Please consider <a href="/donate">donating</a> to sustain our activities
70 |       </>
71 |     ),
72 |   },
73 | ]
74 | 
75 | function Feature({ title, description }) {
76 |   return (
77 |     <div className={clsx('col col--6')}>
78 |       <div className="text--center padding-horiz--md padding-vert--lg">
79 |         <h3>{title}</h3>
80 |         <p>{description}</p>
81 |       </div>
82 |     </div>
83 |   )
84 | }
85 | 
86 | export default function HomepageFeatures() {
87 |   return (
88 |     <section className={styles.features}>
89 |       <div className="container">
90 |         <div className="row">
91 |           {FeatureList.map((props, idx) => (
92 |             <Feature key={idx} {...props} />
93 |           ))}
94 |         </div>
95 |       </div>
96 |     </section>
97 |   )
98 | }
99 | 


--------------------------------------------------------------------------------
/frontend/src/components/homepage-features.module.css:
--------------------------------------------------------------------------------
 1 | .features {
 2 |   display: flex;
 3 |   align-items: center;
 4 |   padding: 2rem 0;
 5 |   width: 100%;
 6 | }
 7 | 
 8 | .featureSvg {
 9 |   height: 200px;
10 |   width: 200px;
11 | }
12 | 


--------------------------------------------------------------------------------
/frontend/src/css/custom.css:
--------------------------------------------------------------------------------
 1 | /**
 2 |  * Any CSS included here will be global. The classic template
 3 |  * bundles Infima by default. Infima is a CSS framework designed to
 4 |  * work well for content-centric websites.
 5 |  */
 6 | 
 7 | /* You can override the default Infima variables here. */
 8 | :root {
 9 |   --ifm-color-primary: #25c2a0;
10 |   --ifm-color-primary-dark: rgb(33, 175, 144);
11 |   --ifm-color-primary-darker: rgb(31, 165, 136);
12 |   --ifm-color-primary-darkest: rgb(26, 136, 112);
13 |   --ifm-color-primary-light: rgb(70, 203, 174);
14 |   --ifm-color-primary-lighter: rgb(102, 212, 189);
15 |   --ifm-color-primary-lightest: rgb(146, 224, 208);
16 |   --ifm-code-font-size: 95%;
17 | }
18 | 
19 | .docusaurus-highlight-code-line {
20 |   background-color: rgba(0, 0, 0, 0.1);
21 |   display: block;
22 |   margin: 0 calc(-1 * var(--ifm-pre-padding));
23 |   padding: 0 var(--ifm-pre-padding);
24 | }
25 | 
26 | html[data-theme="dark"] .docusaurus-highlight-code-line {
27 |   background-color: rgba(0, 0, 0, 0.3);
28 | }
29 | 
30 | .opencollective-image {
31 |   color-scheme: initial;
32 | }
33 | 
34 | .flex-column-container {
35 |   display: flex;
36 |   flex-direction: column;
37 |   height: 100%;
38 | }
39 | 
40 | .align-bottom {
41 |   margin-top: auto;
42 | }
43 | 


--------------------------------------------------------------------------------
/frontend/src/pages/community.md:
--------------------------------------------------------------------------------
 1 | # Community
 2 | 
 3 | Shields.io is possible thanks to the people and companies who donate money, services or time to keep the project running.
 4 | 
 5 | ## Sponsors
 6 | 
 7 | ❤️ These companies help us by donating their services to shields:
 8 | 
 9 | <ul>
10 |     <li>
11 |         <a href="https://nodeping.com/">NodePing</a>
12 |     </li>
13 |     <li>
14 |         <a href="https://sentry.io/">Sentry</a>
15 |     </li>
16 | </ul>
17 | 
18 | 💵 These organisations help keep shields running by donating on OpenCollective. Your organisation can support this project by <a href="https://opencollective.com/shields#sponsor">becoming a sponsor </a>. Your logo will show up here with a link to your website.
19 | 
20 | <p>
21 |     <object
22 |         data="https://opencollective.com/shields/tiers/sponsor.svg?avatarHeight=80&width=600"
23 |         className="opencollective-image"
24 |     ></object>
25 | </p>
26 | 
27 | ## Backers
28 | 
29 | 💵 Thank you to all our backers who help keep shields running by donating on OpenCollective. You can support this project by <a href="https://opencollective.com/shields#backer">becoming a backer</a>.
30 | 
31 | <p>
32 |     <object
33 |         data="https://opencollective.com/shields/tiers/backer.svg?width=600"
34 |         className="opencollective-image">
35 |     </object>
36 | </p>
37 | 
38 | ## Contributors
39 | 
40 | 🙏 This project exists thanks to all the nice people who contribute their time to work on the project.
41 | 
42 | <p>
43 |     <object
44 |         data="https://opencollective.com/shields/contributors.svg?width=600"
45 |         className="opencollective-image"
46 |     ></object>
47 | </p>
48 | 
49 | ✨ Shields is helped by these companies which provide a free plan for their product or service:
50 | 
51 | <ul>
52 |     <li>
53 |         <a href="https://coveralls.io/">Coveralls</a>
54 |     </li>
55 |     <li>
56 |         <a href="https://www.cloudflare.com/">Cloudflare</a>
57 |     </li>
58 |     <li>
59 |         <a href="https://discord.com/">Discord</a>
60 |     </li>
61 |     <li>
62 |         <a href="https://github.com/">GitHub</a>
63 |     </li>
64 | </ul>
65 | 


--------------------------------------------------------------------------------
/frontend/src/pages/donate.md:
--------------------------------------------------------------------------------
 1 | # Donate
 2 | 
 3 | You can donate to Shields.io via [OpenCollective](https://opencollective.com/shields).
 4 | 
 5 | ## How the money is spent
 6 | 
 7 | Shields.io is a non-profit project run by unpaid volunteers. We use your donations to pay for our hosting costs.
 8 | 
 9 | Shields badges are everywhere. Shields badges appear on GitHub, NPM, PyPI, Ruby Gems, Rust Crates... If people build software there, shields badges are on it. Our userbase scales with the size of the software development community as a whole. This means we serve a lot of traffic. While the majority of image impressions are served from downstream proxies, we serve over 1.6 billion requests per month from our own infrastructure and transfer over 3Tb of outbound bandwidth each month.
10 | 
11 | Those are big numbers, and servers cost money. So does bandwidth. We cover our hosting costs with donations from the community.
12 | 
13 | ## Donation tiers
14 | 
15 | While we accept donations of any size, we do have some suggested tiers.
16 | 
17 | <section>
18 |   <div className="container">
19 |     <div className="row">
20 |       <div className="col col--6">
21 |         <div className="padding-horiz--md padding-vert--lg flex-column-container">
22 |           <h3>Sponsor</h3>
23 |           <p>Recommended for **companies**: With a monthly donation of $35, you can help to sustain our activities. Your company logo and a link to your website will feature at the top of our [community page](https://shields.io/community).</p>
24 |           <p class="align-bottom"><a href="https://opencollective.com/shields/contribute/sponsor-2412/checkout" class="button button--primary button--medium">Become a Sponsor</a></p>
25 |         </div>
26 |       </div>
27 | 
28 |       <div className="col col--6">
29 |         <div className="padding-horiz--md padding-vert--lg flex-column-container">
30 |           <h3>Monthly Backer</h3>
31 |           <p>Recommended for **individuals**: With a monthly donation of $3, you can help to sustain our activities on an ongoing basis.</p>
32 |           <p class="align-bottom"><a href="https://opencollective.com/shields/contribute/monthly-backer-2988/checkout" class="button button--primary button--medium">Become a Monthly Backer</a></p>
33 |         </div>
34 |       </div>
35 | 
36 |       <div className="col col--6">
37 |         <div className="padding-horiz--md padding-vert--lg flex-column-container">
38 |           <h3>Backer</h3>
39 |           <p>If you would prefer not to commit to a monthly donation, but you think shields.io has provided some value [over the last 10+ years](https://github.com/badges/shields/discussions/8867), consider making a one-time donation of $10.</p>
40 |           <p class="align-bottom"><a href="https://opencollective.com/shields/contribute/backer-2411/checkout" class="button button--secondary button--medium">Become a Backer</a></p>
41 |         </div>
42 |       </div>
43 | 
44 |       <div className="col col--6">
45 |         <div className="padding-horiz--md padding-vert--lg flex-column-container">
46 |           <h3>Something Else</h3>
47 |           <p>Make a custom one-time or recurring donation of any amount.</p>
48 |           <p class="align-bottom"><a href="https://opencollective.com/shields/donate" class="button button--secondary button--medium">Make a custom Donation</a></p>
49 |         </div>
50 |       </div>
51 |     </div>
52 | 
53 |   </div>
54 | </section>
55 | 
56 | ## FAQ
57 | 
58 | ### Can I donate using another platform?
59 | 
60 | Currently we only accept donations via [OpenCollective](https://opencollective.com/shields). OpenCollective should be convenient for most users as it allows you to donate using credit card, bank transfer, or PayPal and is available in most countries.
61 | 
62 | ### I donated as a sponsor. How do I change my company logo or URL?
63 | 
64 | We pull the logo and URL from your Open Collective profile. You can update these at any time from within Open Collective and those changes will be reflected on the community page within 24 hours.
65 | 
66 | ### Can I see exactly how the money is being used?
67 | 
68 | Using OpenCollective means our finances are completely transparent. All transactions are publicly visible on https://opencollective.com/shields
69 | 


--------------------------------------------------------------------------------
/frontend/src/pages/index.js:
--------------------------------------------------------------------------------
 1 | import React from 'react'
 2 | import clsx from 'clsx'
 3 | import Layout from '@theme/Layout'
 4 | import Link from '@docusaurus/Link'
 5 | import useDocusaurusContext from '@docusaurus/useDocusaurusContext'
 6 | import HomepageFeatures from '../components/homepage-features'
 7 | import styles from './index.module.css'
 8 | 
 9 | function HomepageHeader() {
10 |   const { siteConfig } = useDocusaurusContext()
11 |   return (
12 |     <header className={clsx('hero hero--primary', styles.heroBanner)}>
13 |       <div className="container">
14 |         <h1 className="hero__title">{siteConfig.title}</h1>
15 |         <p className="hero__subtitle">{siteConfig.tagline}</p>
16 |         <div className={styles.buttons}>
17 |           <Link className="button button--secondary button--lg" to="/badges">
18 |             Get started
19 |           </Link>
20 |         </div>
21 |       </div>
22 |     </header>
23 |   )
24 | }
25 | 
26 | export default function Home() {
27 |   const { siteConfig } = useDocusaurusContext()
28 |   return (
29 |     <Layout
30 |       description="Concise, consistent, and legible badges"
31 |       title={siteConfig.title}
32 |     >
33 |       <HomepageHeader />
34 |       <main>
35 |         <HomepageFeatures />
36 |       </main>
37 |     </Layout>
38 |   )
39 | }
40 | 


--------------------------------------------------------------------------------
/frontend/src/pages/index.module.css:
--------------------------------------------------------------------------------
 1 | /**
 2 |  * CSS files with the .module.css suffix will be treated as CSS modules
 3 |  * and scoped locally.
 4 |  */
 5 | 
 6 | .heroBanner {
 7 |   padding: 4rem 0;
 8 |   text-align: center;
 9 |   position: relative;
10 |   overflow: hidden;
11 | }
12 | 
13 | @media screen and (max-width: 966px) {
14 |   .heroBanner {
15 |     padding: 2rem;
16 |   }
17 | }
18 | 
19 | .buttons {
20 |   display: flex;
21 |   align-items: center;
22 |   justify-content: center;
23 | }
24 | 


--------------------------------------------------------------------------------
/frontend/src/pages/privacy.md:
--------------------------------------------------------------------------------
 1 | # Privacy Policy
 2 | 
 3 | Shields.io is non-tracking and privacy-respecting. This Privacy Policy explains how we handle your data in compliance with the General Data Protection Regulation (GDPR).
 4 | 
 5 | ## 1. Hosting and Service Providers
 6 | 
 7 | We use [fly.io](https://fly.io) for hosting and [CloudFlare](https://www.cloudflare.com) for DNS and CDN services. These third-party providers process requests to deliver and secure our website. Please refer to their privacy policies for more information:
 8 | 
 9 | - https://fly.io/legal/privacy-policy/
10 | - https://www.cloudflare.com/en-gb/privacypolicy/
11 | 
12 | ## 2. Cookies
13 | 
14 | We do not use any cookies on our website.
15 | 
16 | ## 3. Logs and Data Collection
17 | 
18 | We do not store any logs of your visits, requests, or other activities on our site.
19 | 
20 | ## 4. Error Reporting
21 | 
22 | If a request fails, we send an error report to [Sentry](https://sentry.io/), our error-tracking service.
23 | These reports contain technical data about the error but do not include any personally identifiable information (PII), such as your IP address. For details on Sentry's data processing, refer to their privacy policy:
24 | 
25 | - https://sentry.io/privacy/
26 | 
27 | ## 5. GitHub OAuth App
28 | 
29 | Users may optionally authorize our [GitHub OAuth app](https://img.shields.io/github-auth).
30 | 
31 | Authorizing our app shares with us a GitHub token which has read-only access to public data. We only ask for the minimum permissions necessary. Authorizing the OAuth app doesn't allow us access to your private data or allow us to perform any actions on your behalf.
32 | 
33 | The only information we store is the **GitHub token** and the **timestamp** when you authorized the app.
34 | 
35 | - The GitHub token is used solely to increase the rate limit for accessing the GitHub API.
36 | - The signup timestamp is stored for internal record-keeping purposes.
37 | 
38 | We don't collect or store any other information like your username or email address.
39 | 
40 | If you decide you would not like to continue sharing a token with us, you can revoke the Shields.io OAuth app at https://github.com/settings/applications. You can do this at any time. This will de-activate the token you have shared with us and we'll remove it from our token pool.
41 | 
42 | ## 6. Your Rights
43 | 
44 | Under the GDPR, users have rights concerning their personal data, including access, correction, deletion, and objection to processing.
45 | 
46 | Since we process minimal data, these rights are not relevant to most users of the service.
47 | 
48 | ## 7. Contact Us
49 | 
50 | If you have questions about this Privacy Policy or our data practices, you can contact us at team at shields.io
51 | 


--------------------------------------------------------------------------------
/frontend/src/plugins/strip-code-block-links.js:
--------------------------------------------------------------------------------
 1 | const { visit } = require('unist-util-visit')
 2 | 
 3 | function stripCodeBlockLinks() {
 4 |   /*
 5 |   Docusaurus 3 uses [remark-gfm](https://github.com/remarkjs/remark-gfm)
 6 |   One of the "features" of remark-gfm is that it automatically looks for URLs
 7 |   and email addresses, and automatically wraps them in <a> tags.
 8 | 
 9 |   This happens even if the URL is inside a <code> block.
10 |   This behaviour is
11 |   a) mostly unhelpful and
12 |   b) non-configurable
13 | 
14 |   This plugin removes <a> tags which appear inside a <code> block.
15 |   */
16 |   return tree => {
17 |     visit(tree, ['mdxJsxTextElement', 'mdxJsxFlowElement', 'element'], node => {
18 |       if (node.name === 'code' || node.tagName === 'code') {
19 |         const links = node.children.filter(child => child.tagName === 'a')
20 |         links.forEach(link => {
21 |           const linkText = link.children.map(child => child.value).join('')
22 |           const linkIndex = node.children.indexOf(link)
23 |           node.children.splice(linkIndex, 1, { type: 'text', value: linkText })
24 |         })
25 |       }
26 |     })
27 |   }
28 | }
29 | 
30 | module.exports = stripCodeBlockLinks
31 | 


--------------------------------------------------------------------------------
/frontend/src/theme/ApiDemoPanel/Curl/index.js:
--------------------------------------------------------------------------------
  1 | import React, { useRef, useState, useEffect } from 'react'
  2 | import useDocusaurusContext from '@docusaurus/useDocusaurusContext'
  3 | import clsx from 'clsx'
  4 | import codegen from 'postman-code-generators'
  5 | import { Highlight } from 'prism-react-renderer'
  6 | import { useTypedSelector } from '@theme/ApiDemoPanel/hooks'
  7 | import buildPostmanRequest from '@theme/ApiDemoPanel/buildPostmanRequest'
  8 | import FloatingButton from '@theme/ApiDemoPanel/FloatingButton'
  9 | import styles from 'docusaurus-theme-openapi/lib/theme/ApiDemoPanel/Curl/styles.module.css'
 10 | 
 11 | const languageSet = [
 12 |   {
 13 |     tabName: 'cURL',
 14 |     highlight: 'bash',
 15 |     language: 'curl',
 16 |     variant: 'curl',
 17 |     options: {
 18 |       longFormat: false,
 19 |       followRedirect: true,
 20 |       trimRequestBody: true,
 21 |     },
 22 |   },
 23 |   {
 24 |     tabName: 'Node',
 25 |     highlight: 'javascript',
 26 |     language: 'nodejs',
 27 |     variant: 'axios',
 28 |     options: {
 29 |       ES6_enabled: true,
 30 |       followRedirect: true,
 31 |       trimRequestBody: true,
 32 |     },
 33 |   },
 34 |   {
 35 |     tabName: 'Go',
 36 |     highlight: 'go',
 37 |     language: 'go',
 38 |     variant: 'native',
 39 |     options: {
 40 |       followRedirect: true,
 41 |       trimRequestBody: true,
 42 |     },
 43 |   },
 44 |   {
 45 |     tabName: 'Python',
 46 |     highlight: 'python',
 47 |     language: 'python',
 48 |     variant: 'requests',
 49 |     options: {
 50 |       followRedirect: true,
 51 |       trimRequestBody: true,
 52 |     },
 53 |   },
 54 | ]
 55 | const languageTheme = {
 56 |   plain: {
 57 |     color: 'var(--ifm-code-color)',
 58 |   },
 59 |   styles: [
 60 |     {
 61 |       types: ['inserted', 'attr-name'],
 62 |       style: {
 63 |         color: 'var(--openapi-code-green)',
 64 |       },
 65 |     },
 66 |     {
 67 |       types: ['string', 'url'],
 68 |       style: {
 69 |         color: 'var(--openapi-code-green)',
 70 |       },
 71 |     },
 72 |     {
 73 |       types: ['builtin', 'char', 'constant', 'function'],
 74 |       style: {
 75 |         color: 'var(--openapi-code-blue)',
 76 |       },
 77 |     },
 78 |     {
 79 |       types: ['punctuation', 'operator'],
 80 |       style: {
 81 |         color: 'var(--openapi-code-dim)',
 82 |       },
 83 |     },
 84 |     {
 85 |       types: ['class-name'],
 86 |       style: {
 87 |         color: 'var(--openapi-code-orange)',
 88 |       },
 89 |     },
 90 |     {
 91 |       types: ['tag', 'arrow', 'keyword'],
 92 |       style: {
 93 |         color: 'var(--openapi-code-purple)',
 94 |       },
 95 |     },
 96 |     {
 97 |       types: ['boolean'],
 98 |       style: {
 99 |         color: 'var(--openapi-code-red)',
100 |       },
101 |     },
102 |   ],
103 | }
104 | 
105 | function getBaseUrl() {
106 |   /*
107 |   This is a special case for production.
108 | 
109 |   We want to be able to build the front end with no value set for
110 |   `BASE_URL` so that staging, prod and self hosting users
111 |   can all use the same docker image.
112 | 
113 |   When deployed to staging, we want the frontend on
114 |   https://staging.shields.io/ to generate badges with the base
115 |   https://staging.shields.io/
116 |   (and we want similar behaviour for users hosting their own instance)
117 | 
118 |   When we promote to production we want https://shields.io/ and
119 |   https://www.shields.io/ to both generate badges with the base
120 |   https://img.shields.io/
121 | 
122 |   For local dev, we can deal with setting the api and front-end
123 |   being on different ports using the BASE_URL env var
124 |   */
125 |   const { protocol, hostname, port } = window.location
126 |   if (['shields.io', 'www.shields.io'].includes(hostname)) {
127 |     return 'https://img.shields.io'
128 |   }
129 |   if (!port) {
130 |     return `${protocol}//${hostname}`
131 |   }
132 |   return `${protocol}//${hostname}:${port}`
133 | }
134 | 
135 | function getServer() {
136 |   return {
137 |     url: getBaseUrl(),
138 |     variables: {},
139 |   }
140 | }
141 | 
142 | function Curl({ postman, codeSamples }) {
143 |   // TODO: match theme for vscode.
144 |   const { siteConfig } = useDocusaurusContext()
145 |   const [copyText, setCopyText] = useState('Copy')
146 |   const contentType = useTypedSelector(state => state.contentType.value)
147 |   const accept = useTypedSelector(state => state.accept.value)
148 |   const server = useTypedSelector(state => state.server.value) || getServer()
149 |   const body = useTypedSelector(state => state.body)
150 |   const pathParams = useTypedSelector(state => state.params.path)
151 |   const queryParams = useTypedSelector(state => state.params.query)
152 |   const cookieParams = useTypedSelector(state => state.params.cookie)
153 |   const headerParams = useTypedSelector(state => state.params.header)
154 |   const auth = useTypedSelector(state => state.auth)
155 | 
156 |   const langs = [
157 |     ...(siteConfig?.themeConfig?.languageTabs ?? languageSet),
158 |     ...codeSamples,
159 |   ]
160 |   const [language, setLanguage] = useState(langs[0])
161 |   const [codeText, setCodeText] = useState('')
162 |   useEffect(() => {
163 |     const postmanRequest = buildPostmanRequest(postman, {
164 |       queryParams,
165 |       pathParams,
166 |       cookieParams,
167 |       contentType,
168 |       accept,
169 |       headerParams,
170 |       body,
171 |       server,
172 |       auth,
173 |     })
174 |     if (language && !!language.options) {
175 |       codegen.convert(
176 |         language.language,
177 |         language.variant,
178 |         postmanRequest,
179 |         language.options,
180 |         (error, snippet) => {
181 |           if (error) {
182 |             return
183 |           }
184 | 
185 |           setCodeText(snippet)
186 |         },
187 |       )
188 |     } else if (language && !!language.source) {
189 |       setCodeText(
190 |         language.source.replace('$url', postmanRequest.url.toString()),
191 |       )
192 |     } else {
193 |       setCodeText('')
194 |     }
195 |   }, [
196 |     accept,
197 |     body,
198 |     contentType,
199 |     cookieParams,
200 |     headerParams,
201 |     language,
202 |     pathParams,
203 |     postman,
204 |     queryParams,
205 |     server,
206 |     auth,
207 |   ])
208 |   const ref = useRef(null)
209 | 
210 |   const handleCurlCopy = () => {
211 |     setCopyText('Copied')
212 |     setTimeout(() => {
213 |       setCopyText('Copy')
214 |     }, 2000)
215 | 
216 |     if (ref.current?.innerText) {
217 |       navigator.clipboard.writeText(ref.current.innerText)
218 |     }
219 |   }
220 | 
221 |   if (language === undefined) {
222 |     return null
223 |   }
224 | 
225 |   return (
226 |     <>
227 |       <div className={clsx(styles.buttonGroup, 'api-code-tab-group')}>
228 |         {langs.map(lang => (
229 |           <button
230 |             className={clsx(
231 |               language === lang ? styles.selected : undefined,
232 |               language === lang ? 'api-code-tab--active' : undefined,
233 |               'api-code-tab',
234 |             )}
235 |             key={lang.tabName || lang.label}
236 |             onClick={() => setLanguage(lang)}
237 |             type="button"
238 |           >
239 |             {lang.tabName || lang.label}
240 |           </button>
241 |         ))}
242 |       </div>
243 | 
244 |       <Highlight
245 |         code={codeText}
246 |         language={language.highlight || language.lang}
247 |         theme={languageTheme}
248 |       >
249 |         {({ className, tokens, getLineProps, getTokenProps }) => (
250 |           <FloatingButton label={copyText} onClick={handleCurlCopy}>
251 |             <pre
252 |               className={className}
253 |               style={{
254 |                 background: 'var(--openapi-card-background-color)',
255 |                 paddingRight: '60px',
256 |                 borderRadius:
257 |                   '2px 2px var(--openapi-card-border-radius) var(--openapi-card-border-radius)',
258 |               }}
259 |             >
260 |               <code ref={ref}>
261 |                 {tokens.map((line, i) => (
262 |                   // this <span> does have a key but eslint fails
263 |                   // to detect it because it is an arg to getLineProps()
264 |                   <span
265 |                     {...getLineProps({
266 |                       line,
267 |                       key: i,
268 |                     })}
269 |                   >
270 |                     {line.map((token, key) => {
271 |                       if (token.types.includes('arrow')) {
272 |                         token.types = ['arrow']
273 |                       }
274 | 
275 |                       return (
276 |                         // this <span> does have a key but eslint fails
277 |                         // to detect it because it is an arg to getLineProps()
278 |                         <span
279 |                           {...getTokenProps({
280 |                             token,
281 |                             key,
282 |                           })}
283 |                         />
284 |                       )
285 |                     })}
286 |                     {'\n'}
287 |                   </span>
288 |                 ))}
289 |               </code>
290 |             </pre>
291 |           </FloatingButton>
292 |         )}
293 |       </Highlight>
294 |     </>
295 |   )
296 | }
297 | 
298 | export default Curl
299 | 


--------------------------------------------------------------------------------
/frontend/src/theme/ApiDemoPanel/Response/index.js:
--------------------------------------------------------------------------------
 1 | import React from 'react'
 2 | import { useTypedDispatch, useTypedSelector } from '@theme/ApiDemoPanel/hooks'
 3 | import FloatingButton from '@theme/ApiDemoPanel/FloatingButton'
 4 | import { clearResponse } from 'docusaurus-theme-openapi/lib/theme/ApiDemoPanel/Response/slice'
 5 | 
 6 | function formatXml(xml) {
 7 |   const tab = '  '
 8 |   let formatted = ''
 9 |   let indent = ''
10 |   xml.split(/>\s*</).forEach(node => {
11 |     if (node.match(/^\/\w/)) {
12 |       // decrease indent by one 'tab'
13 |       indent = indent.substring(tab.length)
14 |     }
15 | 
16 |     formatted += `${indent}<${node}>\r\n`
17 | 
18 |     if (node.match(/^<?\w[^>]*[^/]$/)) {
19 |       // increase indent
20 |       indent += tab
21 |     }
22 |   })
23 |   return formatted.substring(1, formatted.length - 3)
24 | }
25 | 
26 | function Response() {
27 |   const response = useTypedSelector(state => state.response.value)
28 |   const dispatch = useTypedDispatch()
29 | 
30 |   if (response === undefined) {
31 |     return null
32 |   }
33 | 
34 |   let prettyResponse = response
35 | 
36 |   try {
37 |     prettyResponse = JSON.stringify(JSON.parse(response), null, 2)
38 |   } catch {
39 |     if (response.startsWith('<?xml ')) {
40 |       prettyResponse = formatXml(response)
41 |     }
42 |   }
43 | 
44 |   return (
45 |     <FloatingButton label="Clear" onClick={() => dispatch(clearResponse())}>
46 |       {(response.startsWith('<svg ') && (
47 |         <img
48 |           id="badge-preview"
49 |           src={`data:image/svg+xml;utf8,${encodeURIComponent(response)}`}
50 |         />
51 |       )) || (
52 |         <pre
53 |           style={{
54 |             background: 'var(--openapi-card-background-color)',
55 |             borderRadius: 'var(--openapi-card-border-radius)',
56 |             paddingRight: '60px',
57 |           }}
58 |         >
59 |           <code>{prettyResponse || 'No Response'}</code>
60 |         </pre>
61 |       )}
62 |     </FloatingButton>
63 |   )
64 | }
65 | 
66 | export default Response
67 | 


--------------------------------------------------------------------------------
/frontend/src/theme/DocPaginator/index.js:
--------------------------------------------------------------------------------
1 | export default function DocPaginator(props) {
2 |   return ''
3 | }
4 | 


--------------------------------------------------------------------------------
/frontend/static/.nojekyll:
--------------------------------------------------------------------------------
https://raw.githubusercontent.com/badges/shields/master/frontend/static/.nojekyll


--------------------------------------------------------------------------------
https://raw.githubusercontent.com/badges/shields/master/frontend/static/img/builder.png


--------------------------------------------------------------------------------
https://raw.githubusercontent.com/badges/shields/master/frontend/static/img/favicon.ico


--------------------------------------------------------------------------------
https://raw.githubusercontent.com/badges/shields/master/frontend/static/img/logo.png


---------------------------------------------------------