This file is a merged representation of a subset of the codebase, containing specifically included files, combined into a single document by Repomix.
The content has been processed where security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
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
- Only files matching these patterns are included: README.md, source/plugins/**/README.md, source/plugins/README.md
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Security check has been disabled - content may contain sensitive information
- Files are sorted by Git change count (files with more changes are at the bottom)

## Additional Info

# Directory Structure
```
source/
  plugins/
    achievements/
      README.md
    activity/
      README.md
    anilist/
      README.md
    base/
      README.md
    calendar/
      README.md
    code/
      README.md
    community/
      16personalities/
        README.md
      chess/
        README.md
      crypto/
        README.md
      fortune/
        README.md
      nightscout/
        README.md
      poopmap/
        README.md
      screenshot/
        README.md
      splatoon/
        README.md
      stock/
        README.md
      README.md
    contributors/
      README.md
    core/
      README.md
    discussions/
      README.md
    followup/
      README.md
    gists/
      README.md
    habits/
      README.md
    introduction/
      README.md
    isocalendar/
      README.md
    languages/
      README.md
    leetcode/
      README.md
    licenses/
      README.md
    lines/
      README.md
    music/
      README.md
    notable/
      README.md
    pagespeed/
      README.md
    people/
      README.md
    posts/
      README.md
    projects/
      README.md
    reactions/
      README.md
    repositories/
      README.md
    rss/
      README.md
    skyline/
      README.md
    sponsors/
      README.md
    sponsorships/
      README.md
    stackoverflow/
      README.md
    stargazers/
      README.md
    starlists/
      README.md
    stars/
      README.md
    steam/
      README.md
    support/
      README.md
    topics/
      README.md
    traffic/
      README.md
    tweets/
      README.md
    wakatime/
      README.md
    README.md
README.md
```

# Files

## File: source/plugins/achievements/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🏆 Achievements</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays several highlights about what an account has achieved on GitHub.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Compact display</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.achievements.compact.svg" alt=""></img></details>
      <details><summary>Detailed display</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.achievements.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements</code></h4></td>
    <td rowspan="2"><p>Enable achievements plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_threshold</code></h4></td>
    <td rowspan="2"><p>Rank threshold filter</p>
<p>Use <code>X</code> to display achievements not yet unlocked</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> C<br>
<b>allowed values:</b><ul><li>S</li><li>A</li><li>B</li><li>C</li><li>X</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_secrets</code></h4></td>
    <td rowspan="2"><p>Secrets achievements</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_display</code></h4></td>
    <td rowspan="2"><p>Display style</p>
<ul>
<li><code>detailed</code>: display icon, name, description and ranking</li>
<li><code>compact</code>: display icon, name and value</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> detailed<br>
<b>allowed values:</b><ul><li>detailed</li><li>compact</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored achievements</p>
<p>Use achievements names without their rank adjective (i.e. without &quot;great&quot;, &quot;super&quot; or &quot;master&quot;)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_achievements_only</code></h4></td>
    <td rowspan="2"><p>Showcased achievements</p>
<p>Use achievements names without their rank adjective (i.e. without &quot;great&quot;, &quot;super&quot; or &quot;master&quot;)</p>
<p>This option is equivalent to <a href="/source/plugins/achievements/README.md#plugin_achievements_ignored"><code>plugin_achievements_ignored</code></a> with all existing achievements except the ones listed in this option</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Detailed display
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.achievements.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_achievements: yes
  plugin_achievements_only: sponsor, maintainer, octonaut

```
```yaml
name: Compact display
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.achievements.compact.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_achievements: yes
  plugin_achievements_only: >-
    polyglot, stargazer, sponsor, deployer, member, maintainer, developer,
    scripter, packager, explorer, infographile, manager
  plugin_achievements_display: compact
  plugin_achievements_threshold: X

```
<!--/examples-->
````

## File: source/plugins/activity/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📰 Recent activity</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays recent activity on GitHub.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/markdown/README.md"><code>📒 Markdown template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.activity.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity</code></h4></td>
    <td rowspan="2"><p>Enable activity plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 5<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_load</code></h4></td>
    <td rowspan="2"><p>Events to load</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(100 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 300<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_days</code></h4></td>
    <td rowspan="2"><p>Events maximum age</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 365)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 14<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_visibility</code></h4></td>
    <td rowspan="2"><p>Events visibility</p>
<p>Can be used to toggle private activity visibility when using a token with <code>repo</code> scope</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> all<br>
<b>allowed values:</b><ul><li>public</li><li>all</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_timestamps</code></h4></td>
    <td rowspan="2"><p>Events timestamps</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored users</p>
<p>Can be used to ignore bots activity</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>users_ignored</code><br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_activity_filter</code></h4></td>
    <td rowspan="2"><p>Events types</p>
<p>These are fetched from <a href="https://docs.github.com/en/free-pro-team@latest/developers/webhooks-and-events/github-event-types">GitHub events API</a> and the following types are currently supported:</p>
<ul>
<li><code>push</code>: Push of commits</li>
<li><code>issue</code>: Opening/Reopening/Closing of issues</li>
<li><code>pr</code>: Opening/Closing of pull requests</li>
<li><code>ref/create</code>: Creation of git tags or git branches</li>
<li><code>ref/delete</code>: Deletion of git tags or git branches</li>
<li><code>release</code>: Publication of new releases</li>
<li><code>review</code>: Review of pull requests</li>
<li><code>comment</code>: Comments on commits, issues and pull requests</li>
<li><code>wiki</code>: Changes of wiki pages</li>
<li><code>fork</code>: Forking of repositories</li>
<li><code>star</code>: Starring of repositories</li>
<li><code>public</code>: Repositories made public</li>
<li><code>member</code>: Addition of new collaborator in repository</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> all<br>
<b>allowed values:</b><ul><li>all</li><li>comment</li><li>ref/create</li><li>ref/delete</li><li>release</li><li>push</li><li>issue</li><li>pr</li><li>review</li><li>wiki</li><li>fork</li><li>star</li><li>member</li><li>public</li></ul></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Recent activity
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.activity.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_activity: yes
  plugin_activity_limit: 5
  plugin_activity_days: 0
  plugin_activity_filter: issue, pr, release, fork, review, ref/create

```
<!--/examples-->
````

## File: source/plugins/anilist/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🌸 Anilist watch list and reading list</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays favorites animes, mangas and characters from a <a href="https://anilist.co">AniList</a> account.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://anilist.co">AniList</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>For anime watchers</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.svg" alt=""></img></details>
      <details><summary>For manga readers</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.manga.svg" alt=""></img></details>
      <details open><summary>For waifus simp</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.characters.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist</code></h4></td>
    <td rowspan="2"><p>Enable aniList plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_user</code></h4></td>
    <td rowspan="2"><p>AniList login</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_medias</code></h4></td>
    <td rowspan="2"><p>Medias types</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> anime, manga<br>
<b>allowed values:</b><ul><li>anime</li><li>manga</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>favorites</code> will display favorites from <code>plugin_anilist_medias</code></li>
<li><code>watching</code> will display animes currently in watching list</li>
<li><code>reading</code> will display manga currently in reading list</li>
<li><code>characters</code> will display liked characters</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> favorites<br>
<b>allowed values:</b><ul><li>favorites</li><li>watching</li><li>reading</li><li>characters</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (medias)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 2<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_limit_characters</code></h4></td>
    <td rowspan="2"><p>Display limit (characters)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 22<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_anilist_shuffle</code></h4></td>
    <td rowspan="2"><p>Shuffle data</p>
<p>Can be used to create varied outputs</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Favorites anime and currently watching
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.anilist.svg
  token: NOT_NEEDED
  base: ""
  plugin_anilist: yes
  plugin_anilist_medias: anime
  plugin_anilist_sections: favorites, watching
  plugin_anilist_limit: 1

```
```yaml
name: Favorites manga and currently reading
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.anilist.manga.svg
  token: NOT_NEEDED
  base: ""
  plugin_anilist: yes
  plugin_anilist_medias: manga
  plugin_anilist_sections: favorites, reading
  plugin_anilist_limit: 1

```
```yaml
name: Favorites characters
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.anilist.characters.svg
  token: NOT_NEEDED
  base: ""
  plugin_anilist: yes
  plugin_anilist_sections: characters
  plugin_anilist_limit_characters: 22

```
<!--/examples-->
````

## File: source/plugins/base/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🗃️ Base content</h3></th></tr>
  <tr><td colspan="2" align="center"></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
<td colspan="2"><table><tr>
<td align="center">
<img src="https://github.com/lowlighter/metrics/blob/examples/metrics.classic.svg" alt=""></img>
</td>
<td align="center">
<img src="https://github.com/lowlighter/metrics/blob/examples/metrics.organization.svg" alt=""></img>
</td>
</tr></table></td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>base</code></h4></td>
    <td rowspan="2"><p>Base content</p>
<p>The following sections are supported:</p>
<ul>
<li><code>header</code>, which usually contains username, two-weeks commits calendars and a few additional data</li>
<li><code>activity</code>, which contains recent activity (commits, pull requests, issues, etc.)</li>
<li><code>community</code>, which contains community stats (following, sponsors, organizations, etc.)</li>
<li><code>repositories</code>, which contains repository stats (license, forks, stars, etc.)</li>
<li><code>metadata</code>, which contains information about generated metrics</li>
</ul>
<p>These are all enabled by default, but it is possible to explicitly opt out from them.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> header, activity, community, repositories, metadata<br>
<b>allowed values:</b><ul><li>header</li><li>activity</li><li>community</li><li>repositories</li><li>metadata</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>base_indepth</code></h4></td>
    <td rowspan="2"><p>Indepth mode</p>
<p>Enabling this will consume additional API queries to fetch more data.
This currently improves the accuracy of the following statistics:</p>
<ul>
<li>total commits</li>
<li>total issues</li>
<li>total pull requests</li>
<li>total pull requests reviews</li>
<li>total repositories contributed to</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.github.overuse</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>base_hireable</code></h4></td>
    <td rowspan="2"><p>Show <code>Available for hire!</code> in header section</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>base_skip</code></h4></td>
    <td rowspan="2"><p>Skip base content</p>
<blockquote>
<p>⚠️ Any plugin that relies on base content data may break!
Only use this option when using a plugin that can be configured with <a href="/source/plugins/core/README.md#token"><code>token: NOT_NEEDED</code></a></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repositories</code></h4></td>
    <td rowspan="2"><p>Fetched repositories</p>
<p>A higher value result in more accurate metrics but can hit GitHub API rate-limit more easily (especially with a lot of plugins enabled)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 100<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repositories_batch</code></h4></td>
    <td rowspan="2"><p>Fetched repositories per query</p>
<p>If you receive <code>Something went wrong while executing your query</code> (which is usually caused by API timeouts), lowering this value may help.
This setting may not be supported by all plugins.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 100<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repositories_forks</code></h4></td>
    <td rowspan="2"><p>Include forks</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repositories_affiliations</code></h4></td>
    <td rowspan="2"><p>Repositories affiliations</p>
<ul>
<li><code>owner</code>: owned repositories</li>
<li><code>collaborator</code>: repositories with push access</li>
<li><code>organization_member</code>: repositories from an organization where user is a member</li>
</ul>
<p>Some plugin outputs may be affected by this setting too.</p>
<p>Set to <code>&quot;&quot;</code> to disable and fetch all repositories related to given account.
Broad affiliations will result in less representative metrics.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> owner<br>
<b>allowed values:</b><ul><li>owner</li><li>collaborator</li><li>organization_member</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repositories_skipped</code></h4></td>
    <td rowspan="2"><p>Default skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>users_ignored</code></h4></td>
    <td rowspan="2"><p>Default ignored users</p>
<p>Note that emails are only supported in commits-related elements.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> github-actions[bot], dependabot[bot], dependabot-preview[bot], actions-user, action@github.com<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>commits_authoring</code></h4></td>
    <td rowspan="2"><p>Identifiers that has been used for authoring commits</p>
<p>Specify names, surnames, username, email addresses that has been used in the past that can be used to detect commits ownerships in some plugins</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Default metrics
uses: lowlighter/metrics@latest
with:
  filename: metrics.base.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: header, activity, community, repositories, metadata

```
<!--/examples-->
````

## File: source/plugins/calendar/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📆 Commit calendar</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin can display commit calendar across several years.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details><summary>Current year</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.calendar.svg" alt=""></img></details>
      <details open><summary>Full history</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.calendar.full.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_calendar</code></h4></td>
    <td rowspan="2"><p>Enable calendar plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_calendar_limit</code></h4></td>
    <td rowspan="2"><p>Years to display</p>
<p>This option has different behaviours depending on its value:</p>
<ul>
<li><code>n &gt; 0</code> will display the last <code>n</code> years, relative to current year</li>
<li><code>n == 0</code> will display all years starting from GitHub account registration date</li>
<li><code>n &lt; 0</code> will display all years plus <code>n</code> additional years, relative to GitHub account registration date<ul>
<li>Use this when there are commits pushed before GitHub registration</li>
</ul>
</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 1<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Current year calendar
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.calendar.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_calendar: yes

```
```yaml
name: Full history calendar
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.calendar.full.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_calendar: yes
  plugin_calendar_limit: 0

```
<!--/examples-->
````

## File: source/plugins/code/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>♐ Random code snippet</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays a random code snippet from recent activity history.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr><th>ℹ Additional notes</th><td><blockquote>
<p>⚠️ When improperly configured, this plugin could display private code.
If you work with sensitive data or company code, it is advised to keep this plugin disabled.
Use at your own risk, <em>metrics</em> and its authors cannot be held responsible for any resulting code leaks.</p>
</blockquote>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.code.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code</code></h4></td>
    <td rowspan="2"><p>Enable code plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_lines</code></h4></td>
    <td rowspan="2"><p>Display limit (lines per code snippets)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 128)</i>
<br>
<b>default:</b> 12<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_load</code></h4></td>
    <td rowspan="2"><p>Events to load</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(100 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 400<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_days</code></h4></td>
    <td rowspan="2"><p>Events maximum age</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 365)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 3<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_visibility</code></h4></td>
    <td rowspan="2"><p>Events visibility</p>
<p>Can be used to toggle private activity visibility when using a token with <code>repo</code> scope</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> public<br>
<b>allowed values:</b><ul><li>public</li><li>all</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_code_languages</code></h4></td>
    <td rowspan="2"><p>Showcased languages</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: JavaScript or TypeScript snippet of the day
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.code.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_code: yes
  plugin_code_languages: javascript, typescript
  plugin_code_load: 400

```
<!--/examples-->
````

## File: source/plugins/community/16personalities/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🧠 16personalities</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays personality profile from a <a href="https://www.16personalities.com/profile">16personalities profile</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://www.16personalities.com">16personalities</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.16personalities.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_16personalities</code></h4></td>
    <td rowspan="2"><p>Enable 16personalities plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_16personalities_url</code></h4></td>
    <td rowspan="2"><p>Profile URL</p>
<p>This can be obtained after doing the <a href="https://www.16personalities.com/free-personality-test">test on 16personalities</a> and registering an email.
Login with the generated password received in your mailbox and copy the link that is displayed when sharing the profile.</p>
<img src="/.github/readme/imgs/plugin_16personalities_profile.png" width="800" />
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_16personalities_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>personality</code> will display personality type</li>
<li><code>profile</code> will display role and strategy</li>
<li><code>traits</code> will display mind, energy, nature, tactics and identity traits</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> personality<br>
<b>allowed values:</b><ul><li>personality</li><li>profile</li><li>traits</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_16personalities_scores</code></h4></td>
    <td rowspan="2"><p>Display traits scores</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: MBTI Personality profile
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.16personalities.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_16personalities: yes
  plugin_16personalities_url: ${{ secrets.SIXTEEN_PERSONALITIES_URL }}
  plugin_16personalities_sections: personality, traits
  plugin_16personalities_scores: no

```
<!--/examples-->
````

## File: source/plugins/community/chess/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>♟️ Chess</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the last game you played on a supported chess platform.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with any of the supported provider.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_chess_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.chess.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_chess</code></h4></td>
    <td rowspan="2"><p>Enable chess plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_chess_token</code></h4></td>
    <td rowspan="2"><p>Chess platform token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.chess.any</i></li>
</ul>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_chess_user</code></h4></td>
    <td rowspan="2"><p>Chess platform login</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_chess_platform</code></h4></td>
    <td rowspan="2"><p>Chess platform</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>allowed values:</b><ul><li>lichess.org</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_chess_animation</code></h4></td>
    <td rowspan="2"><p>Animation settings</p>
<ul>
<li><code>size</code> is the size of a single chessboard square in pixels (board will be 8 times larger)</li>
<li><code>delay</code> is the delay before starting animation (in seconds)</li>
<li><code>duration</code> is the duration of the animation of a move (in seconds)</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>json</code>
<br>
<b>default:</b> <details><summary>→ Click to expand</summary><pre language="json"><code>{
  "size": 40,
  "delay": 3,
  "duration": 0.6
}
</code></pre></details><br></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a lichess.org token

Create a [lichess.org account](https://lichess.org) and select [API access tokens](https://lichess.org/account/oauth/token) to get a token.

![lichess.org token](/.github/readme/imgs/plugin_chess_lichess_token_0.png)

It is not necessary to add additional scopes:

![lichess.org token](/.github/readme/imgs/plugin_chess_lichess_token_1.png)

Create token and store it in your secrets:

![lichess.org token](/.github/readme/imgs/plugin_chess_lichess_token_0.png)

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Last chess game from lichess.org
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.chess.svg
  token: NOT_NEEDED
  base: ""
  plugin_chess: yes
  plugin_chess_token: ${{ secrets.CHESS_TOKEN }}
  plugin_chess_platform: lichess.org

```
<!--/examples-->
````

## File: source/plugins/community/crypto/README.md
````markdown
<!-- Header -->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🪙 Crypto</h3></th></tr>
  <tr><td colspan="2" align="center">
    <p>This plugin generates an SVG image containing crypto metrics from a given address. It uses the CoinGecko API to fetch crypto prices.</p>
    <p>For more information, check the <a href="https://www.coingecko.com/vi/api/documentation">CoinGecko API documentation</a>.</p>
  </td></tr>
  <tr><th>Authors</th><td><a href="https://github.com/dajneem23">@dajneem23</a></td></tr>
  <tr>
    <th rowspan="3">Supported Features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td>
      <ul>
        <li><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></li>
        <li><a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>
      <ul>
        <li><code>👤 Users</code></li>
        <li><code>👥 Organizations</code></li>
        <li><code>📓 Repositories</code></li>
      </ul>
    </td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_crypto</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://via.placeholder.com/468x60?text=No%20preview%20available" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!-- /Header -->

## ➡️ Available Options

<!-- Options -->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_crypto</code></h4></td>
    <td rowspan="2"><p>Enable crypto plugin</p><img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">Type: <code>boolean</code><br>Default: <code>no</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_crypto_id</code></h4></td>
    <td rowspan="2"><p>Crypto id (from Coingecko)</p><img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">Type: <code>string</code><br>Default: ""<br>Example: bitcoin<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_crypto_vs_currency</code></h4></td>
    <td rowspan="2"><p>The target currency of market data (usd, eur, jpy, etc.)</p><img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">Type: <code>string</code><br>Default: "usd"<br>Example: "usd"<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_crypto_days</code></h4></td>
    <td rowspan="2"><p>Data up to number of days ago (eg. 1,14,30,max)</p><img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">Type: <code>string</code><br>Default: "1"<br>Example: 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_crypto_precision</code></h4></td>
    <td rowspan="2"><p>The number of decimal places to use</p><img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">Type: <code>number</code><br>Default: 2<br>Example: 2<br></td>
  </tr>
</table>
<!-- /Options -->

<!--examples-->
```yaml
name: Crypto Metrics
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.crypto.svg
  token: NOT_NEEDED
  base: ""
  plugin_crypto: yes
  plugin_crypto_id: bitcoin
  plugin_crypto_vs_currency: usd
  plugin_crypto_days: 1
  plugin_crypto_precision: 2

```
<!--/examples-->
````

## File: source/plugins/community/fortune/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🥠 Fortune</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugins displays a random fortune message</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.fortune.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_fortune</code></h4></td>
    <td rowspan="2"><p>Enable fortune plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Fortune
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.fortune.svg
  token: NOT_NEEDED
  base: ""
  plugin_fortune: yes

```
<!--/examples-->
````

## File: source/plugins/community/nightscout/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💉 Nightscout</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays blood sugar values from a <a href="http://nightscout.info">Nightscout</a> site.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="http://nightscout.info">Nightscout</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/legoandmars">@legoandmars</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/legoandmars/legoandmars/blob/master/metrics.plugin.nightscout.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout</code></h4></td>
    <td rowspan="2"><p>Enable nightscout plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_url</code></h4></td>
    <td rowspan="2"><p>Nightscout URL</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> https://example.herokuapp.com<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_datapoints</code></h4></td>
    <td rowspan="2"><p>Number of datapoints shown the graph</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 12<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_lowalert</code></h4></td>
    <td rowspan="2"><p>Threshold for low blood sugar</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 80<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_highalert</code></h4></td>
    <td rowspan="2"><p>Threshold for high blood sugar</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 180<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_urgentlowalert</code></h4></td>
    <td rowspan="2"><p>Threshold for urgently low blood sugar</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 50<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_nightscout_urgenthighalert</code></h4></td>
    <td rowspan="2"><p>Threshold for urgently high blood sugar</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 250<br></td>
  </tr>
</table>
<!--/options-->

## 🌐 Setup a Nightscout instance

The [nightscout website](http://www.nightscout.info/) details how to self-host a nightscout site.
Check out the instructions there.

## ℹ️ Examples workflows

<!--examples-->
```yaml
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  plugin_nightscout: yes
  plugin_nightscout_url: ${{ secrets.NIGHTSCOUT_URL }}

```
<!--/examples-->
````

## File: source/plugins/community/poopmap/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💩 PoopMap plugin</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays statistics from a <a href="https://poopmap.net">PoopMap</a> account.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://poopmap.net">PoopMap</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/matievisthekat">@matievisthekat</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_poopmap_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/matievisthekat/matievisthekat/blob/master/metrics.plugin.poopmap.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_poopmap</code></h4></td>
    <td rowspan="2"><p>Enable poopmap plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_poopmap_token</code></h4></td>
    <td rowspan="2"><p>PoopMap API token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_poopmap_days</code></h4></td>
    <td rowspan="2"><p>Time range</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<br>
<b>default:</b> 7<br>
<b>allowed values:</b><ul><li>7</li><li>30</li><li>180</li><li>365</li></ul></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a PoopMap token

Install PoopMap app ([iOS](https://itunes.apple.com/us/app/poop-map/id1303269455?mt=8)/[Android](https://play.google.com/store/apps/details?id=net.poopmap)) and create an account.

Navigate to your profile in the app

<div align="center">
  <img src="https://user-images.githubusercontent.com/45036977/143533812-c2776bcc-1fda-441e-bc96-cf21d4c69ca1.jpg" width="150" />
</div>

Tap "Share Profile" in the top right

<div align="center">
  <img src="https://user-images.githubusercontent.com/45036977/143533849-b7e03b4d-2903-4339-bbb7-e1fc0ea9724e.jpg" width="150" />
</div>

Tap "Copy to Clipboard"

<div align="center">
  <img src="https://user-images.githubusercontent.com/45036977/143533856-f4a9fc0d-7bde-48c2-b579-e8ee91804d78.jpg" width="150" />
</div>

It should result in something like `Haha, check out the places I've pooped on Poop Map https://api.poopmap.net/map?token=xxxxxxxxxx` copied.

Extract the `token` query parameter from the link and use it in `plugin_poopmap_token`.
This token will not expire and it will be able to access only public details.

## ℹ️ Examples workflows

<!--examples-->
```yaml
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  plugin_poopmap_token: ${{ secrets.POOPMAP_TOKEN }}
  plugin_poopmap: yes

```
<!--/examples-->
````

## File: source/plugins/community/screenshot/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📸 Website screenshot</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays a screenshot from any website.</p>
<p>It can either show the full page or a portion restricted by a <a href="https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors">CSS selector</a>.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.screenshot.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot</code></h4></td>
    <td rowspan="2"><p>Enable screenshot plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_title</code></h4></td>
    <td rowspan="2"><p>Title caption</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> Screenshot<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_url</code></h4></td>
    <td rowspan="2"><p>Website URL</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_selector</code></h4></td>
    <td rowspan="2"><p>CSS Selector</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> body<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_mode</code></h4></td>
    <td rowspan="2"><p>Output mode</p>
<ul>
<li><code>image</code>: screenshot of selected element</li>
<li><code>text</code>: keep <a href="https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/innerText"><code>innerText</code></a> of selected element<ul>
<li><em>⚠️ Any CSS style applied to text such as font size, weight or color will be removed</em></li>
</ul>
</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> image<br>
<b>allowed values:</b><ul><li>image</li><li>text</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_viewport</code></h4></td>
    <td rowspan="2"><p>Viewport options</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>json</code>
<br>
<b>default:</b> <details><summary>→ Click to expand</summary><pre language="json"><code>{
  "width": 1280,
  "height": 1280
}
</code></pre></details><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_wait</code></h4></td>
    <td rowspan="2"><p>Wait time before taking screenshot (ms)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_screenshot_background</code></h4></td>
    <td rowspan="2"><p>Background</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: XKCD of the day
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.screenshot.svg
  token: NOT_NEEDED
  base: ""
  plugin_screenshot: yes
  plugin_screenshot_title: XKCD of the day
  plugin_screenshot_url: https://xkcd.com
  plugin_screenshot_selector: "#comic img"

```
<!--/examples-->
````

## File: source/plugins/community/splatoon/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🦑 Splatoon</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays your Splatoon 3 recent matches based on data fetched from Splatnet.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://www.nintendo.com">Nintendo</a> or <a href="https://splatoon.nintendo.com">Splatoon</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
<p>This specific plugin is licensed under GPL-3.0 rather than MIT to comply with <a href="https://github.com/spacemeowx2/s3si.ts">spacemeowx2/s3si.ts</a> license.</p>
<p>Note that <em>Nintendo Switch Online</em> web tokens usage are not explicitly allowed by <em>Nintendo</em>, use at your own risk.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_splatoon_token</code> <code>🗝️ plugin_splatoon_statink_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.splatoon.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon</code></h4></td>
    <td rowspan="2"><p>Enable splatoon plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_token</code></h4></td>
    <td rowspan="2"><p>Splatnet token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.nintendo.splatnet</i></li>
</ul>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>player</code> for overall player recap</li>
<li><code>versus</code> for <em>Turf war</em> and <em>Anarchy battle</em> matches</li>
<li><code>salmon-run</code> for <em>Salmon run next wave</em> matches</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> player, versus, salmon-run<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_versus_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (Versus)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 6)</i>
<br>
<b>default:</b> 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_salmon_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (Salmon run)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 6)</i>
<br>
<b>default:</b> 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_statink</code></h4></td>
    <td rowspan="2"><p>stat.ink integration</p>
<p>If set, fetched data will also be uploaded to stat.ink
Requires <a href="/source/plugins/community/splatoon/README.md#plugin_splatoon_statink_token"><code>plugin_splatoon_statink_token</code></a> to be set</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.statink</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_statink_token</code></h4></td>
    <td rowspan="2"><p>stat.ink token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_splatoon_source</code></h4></td>
    <td rowspan="2"><p>Source</p>
<ul>
<li><code>splatnet</code> will fetch data from Splatnet using <a href="https://github.com/spacemeowx2/s3si.ts">spacemeowx2/s3si.ts</a> tool</li>
<li><code>local</code> will assume <code>s3si/export</code> directory already exists and is populated (use this when developping new features for this plugin to save network resources and time)</li>
<li><code>mocks</code> will use <code>s3si/mocks</code> directory (use this when developping new features for this plugin to avoid setting up a NSO token)</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> splatnet<br>
<b>allowed values:</b><ul><li>splatnet</li><li>local</li><li>mocks</li></ul></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a *Nintendo Switch Online* token

The helper script is intended to be run by [deno runtime](https://deno.land/). Either [install it locally](https://deno.land/manual/getting_started/installation) or use its [docker image](https://hub.docker.com/r/denoland/deno).

Run the following command in your terminal and follow instructions:
```bash
deno run --allow-run=deno --allow-read=profile.json --allow-write=profile.json --unstable https://raw.githubusercontent.com/lowlighter/metrics/master/source/plugins/community/splatoon/token.ts
```

![Script](/.github/readme/imgs/plugin_splatoon_script.png)

![Authentication](/.github/readme/imgs/plugin_splatoon_auth.png)

## 🐙 [stat.ink](https://stat.ink) integration

It is possible to make this plugin automatically export fetched games to [stat.ink](https://stat.ink) by adding the following:

```yaml
plugin_splatoon_statink: yes
plugin_splatoon_statink_token: ${{ secrets.SPLATOON_STATINK_TOKEN }}
```

[stat.ink](https://stat.ink) API key can be found on user profile:

![stat.ink](/.github/readme/imgs/plugin_splatoon_statink.png)

## 👨‍💻 About

Data are fetched using [spacemeowx2/s3si.ts](https://github.com/spacemeowx2/s3si.ts) tool (which is itself based on [frozenpandaman/s3s](https://github.com/frozenpandaman/s3s)).

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Splatnet data
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.splatoon.svg
  token: NOT_NEEDED
  base: ""
  plugin_splatoon: yes
  plugin_splatoon_token: ${{ secrets.SPLATOON_TOKEN }}

```
```yaml
name: Splatnet data with stat.ink integration
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.splatoon.svg
  token: NOT_NEEDED
  base: ""
  plugin_splatoon: yes
  plugin_splatoon_token: ${{ secrets.SPLATOON_TOKEN }}
  plugin_splatoon_statink: yes
  plugin_splatoon_statink_token: ${{ secrets.SPLATOON_STATINK_TOKEN }}
  extras_css: |
    h2 { display: none !important; }

```
<!--/examples-->
````

## File: source/plugins/community/stock/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💹 Stock prices</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the stock market price of a given company.</p>
</td></tr>
<tr><th>Authors</th><td><a href="https://github.com/lowlighter">@lowlighter</a></td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_stock_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stock.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stock</code></h4></td>
    <td rowspan="2"><p>Enable stock plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.npm.optional.d3</i></li>
<li><i>metrics.api.yahoo.finance</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stock_token</code></h4></td>
    <td rowspan="2"><p>Yahoo Finance token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stock_symbol</code></h4></td>
    <td rowspan="2"><p>Company stock symbol</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stock_duration</code></h4></td>
    <td rowspan="2"><p>Time range</p>
<ul>
<li><code>1d</code>: Today</li>
<li><code>5d</code>: 5 days</li>
<li><code>1mo</code>: 1 month</li>
<li><code>3mo</code>: 3 months</li>
<li><code>6mo</code>: 6 months</li>
<li><code>1y</code>: 1 year</li>
<li><code>2y</code>: 2 years</li>
<li><code>5y</code>: 5 years</li>
<li><code>10y</code>: 10 years</li>
<li><code>ytd</code>: Year to date</li>
<li><code>max</code>: All time</li>
</ul>
<p>This is relative to current date</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 1d<br>
<b>allowed values:</b><ul><li>1d</li><li>5d</li><li>1mo</li><li>3mo</li><li>6mo</li><li>1y</li><li>2y</li><li>5y</li><li>10y</li><li>ytd</li><li>max</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stock_interval</code></h4></td>
    <td rowspan="2"><p>Time interval between points</p>
<ul>
<li><code>1m</code>: 1 minute</li>
<li><code>2m</code>: 2 minutes</li>
<li><code>5m</code>: 5 minutes</li>
<li><code>15m</code>: 15 minutes</li>
<li><code>60m</code>: 60 minutes</li>
<li><code>1d</code>: 1 day</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 5m<br>
<b>allowed values:</b><ul><li>1m</li><li>2m</li><li>5m</li><li>15m</li><li>60m</li><li>1d</li></ul></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a RapidAPI Yahoo Finance token

Create a [RapidAPI account](https://rapidapi.com) and subscribe to [Yahoo Finance API](https://rapidapi.com/apidojo/api/yahoo-finance1) to get a token.

![RapidAPI token](/.github/readme/imgs/plugin_stock_token.png)

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Stock prices from Tesla
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stock.svg
  token: NOT_NEEDED
  base: ""
  plugin_stock: yes
  plugin_stock_token: ${{ secrets.STOCK_TOKEN }}
  plugin_stock_symbol: TSLA

```
<!--/examples-->
````

## File: source/plugins/community/README.md
````markdown
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎲 Community plugins</h3></th></tr>
  <tr><td colspan="2" align="center">Additional plugins maintained by community for even more features!</td></tr>
  <tr>
    <th><a href="/source/plugins/community/16personalities/README.md">🧠 16personalities</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
    <th><a href="/source/plugins/community/chess/README.md">♟️ Chess</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
  </tr>
  <tr>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.16personalities.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.chess.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>  <tr>
    <th><a href="/source/plugins/community/crypto/README.md">🪙 Crypto</a><br><sup>by <a href="https://github.com/dajneem23">@dajneem23</a></sup></th>
    <th><a href="/source/plugins/community/fortune/README.md">🥠 Fortune</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
  </tr>
  <tr>
    <td  align="center">
      <img alt="" width="400" src="https://via.placeholder.com/468x60?text=No%20preview%20available" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.fortune.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>  <tr>
    <th><a href="/source/plugins/community/nightscout/README.md">💉 Nightscout</a><br><sup>by <a href="https://github.com/legoandmars">@legoandmars</a></sup></th>
    <th><a href="/source/plugins/community/poopmap/README.md">💩 PoopMap plugin</a><br><sup>by <a href="https://github.com/matievisthekat">@matievisthekat</a></sup></th>
  </tr>
  <tr>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/legoandmars/legoandmars/blob/master/metrics.plugin.nightscout.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/matievisthekat/matievisthekat/blob/master/metrics.plugin.poopmap.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>  <tr>
    <th><a href="/source/plugins/community/screenshot/README.md">📸 Website screenshot</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
    <th><a href="/source/plugins/community/splatoon/README.md">🦑 Splatoon</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
  </tr>
  <tr>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.screenshot.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.splatoon.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>  <tr>
    <th><a href="/source/plugins/community/stock/README.md">💹 Stock prices</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup></th>
    <th></th>
  </tr>
  <tr>
    <td  align="center">
      <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stock.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
<td align="center"><img width="900" height="1" alt=""></td>
  </tr>
</table>

## 📪 Creating community plugins

Plugins creation requires you to be comfortable with JavaScript, HTML, CSS and [EJS](https://github.com/mde/ejs).

### 💬 Before creating a new plugin

Be sure to read [contribution guide](/CONTRIBUTING.md) and [architecture](/ARCHITECTURE.md) first.

> ℹ️ *metrics* maintainers have no obligation towards community plugins support and may redirect any help, feature or fix requests from other users to you. Of course you are not bound to work on it, but it would be great if you plan to merge a plugin in the main repository

Please respect the following guidelines:

- A plugin should be independent and should not rely on other plugins
  - [🧱 core](/source/plugins/core/README.md) and [🗃️ base](/source/plugins/base/README.md) output can be reused though
- A plugin should never edit its original arguments, as it is shared amongst other plugins and would create unattended side effects
- Use `imports.metadata.plugins.{plugin-name}.inputs()` to automatically type check and default user inputs through defined `metadata.yml`
- Plugin options should respect the "lexical field" of existing option to keep consistency
- Plugin errors should be handled gracefully by partials with error message
- New dependencies should be avoided, consider using existing `imports`
- Spawning sub-process should be avoided, unless absolute necessity
  - Use `imports.which()` to detect whether a command is available
  - Use `imports.run()` to run a command
    - Pass `{prefixed: true}` to wrap automatically command with [WSL](https://docs.microsoft.com/windows/wsl/about) on Windows
  - It is required to work on Linux Ubuntu (as the GitHub action run on it)

> 💡 While the following guide intend to explain the creation process of new plugin, it may also be a good idea to see what existing plugins looks like and see if you want to embark on the adventure!

### 💬 Quick-start

To create a new plugin, clone and setup this repository first:
```shell
git clone https://github.com/lowlighter/metrics.git
cd metrics/
npm install
```

Find a cool name and an [unused emoji](https://emojipedia.org) for your new plugin and run the following:
```shell
npm run quickstart plugin <plugin_name>
```

> ⚠️ Community plugins cannot have the same name as official plugins. *metrics* maintainers may also reserve a plugin name for future usage and may ask you to rename it in case of conflicts

It will create a new directory in `/source/plugins/community` with the following file structure:
* `/source/plugins/community/{plugin-name}`
  * `README.md`
  * `metadata.yml`
  * `examples.mjs`
  * `index.mjs`

Plugins are auto-loaded based on their folder existence, so there's no need to register them somewhere.

### 💬 Filling `metadata.yml`

`metadata.yml` is a required file which describes supported account types, output formats, scopes, etc.

The default file looks like below:
```yaml
name: "🧩 Plugin name"
category: community
description: Short description
examples:
  default: https://via.placeholder.com/468x60?text=No%20preview%20available
authors:
  - octocat
supports:
  - user
  - organization
  - repository
scopes: []
inputs:

  plugin_{name}:
    description: Enable {name} plugin
    type: boolean
    default: no
```

> 💡 It is important to correctly define `metadata.yml` because *metrics* will use its content for various usage

[`🧱 core`](/source/plugins/core/README.md) plugin (which is always called) will automatically verify user inputs against `supports` and `inputs` values and throw an error in case of incompatibility.

`name`, `description`, `scopes`, `examples` are used to auto-generate documentation in the `README.md`. For community plugins, `examples` should be set with auto-generated examples of your own profile.

`authors` should contain your GitHub username

`category` should be set to `community`.

Because of GitHub Actions original limitations, only strings, numbers and boolean were actually supported by `action.yml`. *metrics* implemented its own `inputs` validator to circumvent this. It should be pretty simple to use.

*Example: boolean type, defaults to `false`*
```yml
  plugin_{name}_{option}:
    description: Boolean type
    type: boolean
    default: no
```

```yml
  plugin_{name}_{option}:
    description: String type
    type: string
    default: .user.login
```

> 💡 `.user.login`, `.user.twitter` and `.user.website` are special default values that will be respectively replaced by user's login, Twitter username and attached website. Note that these are not available if `token: NOT_NEEDED` is set by user

*Example: string type, defaults to `foo` with `foo` or `bar` as allowed values*
```yml
  plugin_{name}_{option}:
    description: Select type
    type: string
    values:
      - foo
      - bar
    default: foo
```

> 💡 `values` restricts what can be passed by user

*Example: number type, defaults to `1` and expected to be between `0` and `100`*
```yml
  plugin_{name}_{option}:
    description: Number type
    type: number
    default: 1
    min: 0
    max: 100
```

> 💡 `min` and `max` restricts what can be passed by user. Omit these to respectively remove lower and upper limits.

> 💡 Zero may have a special behaviour (usually to disable limitations), if that's the case add a `zero` attribute (e.g. `zero: disable`) to reference this in documentation

*Example: array type, with comma-separated elements*
```yml
  plugin_{name}_{option}:
    description: Array type
    type: array
    format: comma-separated
    values:
      - foo
      - bar
    default: foo, bar
```

> 💡 An array can be either `comma-separated` or `space-separated`, and will split user input by mentioned separator. Each value is trimmed and lowercased.

*Example: json type*
```yml
  plugin_{name}_{option}:
    description: JSON type
    type: json
    default: |
      {
        "foo": "bar"
      }
```

> 💡 JSON types should be avoided when possible, as they're usually kind of unpractical to write within a YAML document

For complex inputs, pass an `example` that will be displayed as a placeholder on web instances.

When calling `imports.metadata.plugins.{plugin-name}.inputs({data, account, q})`, an object with verified user inputs and correct typing will be returned.

Any invalid input will use have the `default` value instead.

> ⚠️ Returned object will use the web syntax for options rather than the action one. It means that `plugin_` prefix is dropped, and all underscores (`_`) are replaced by dots (`.`)

*Example: validating user inputs*
```javascript
let {limit, "limit.field":limit_field} = imports.metadata.plugins.myplugin.inputs({data, account, q})
console.assert(limit === true)
```

### 💬 Filling `index.mjs`

Plugins use [JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules).

The default exported module of `index.mjs` will be auto-loaded when *metrics* start.

Below is a breakdown of basic `index.mjs` content
```js
export default async function(
  //Shared inputs
  {
    login, //GitHub username
    q, //Raw user inputs (dot notation without plugin_ prefix, don't use it directly)
    imports, //Various utilities (axios, puppeteer, fs, etc., see /source/app/metrics/utils.mjs)
    data, //Raw data from core/base plugin
    computed, //Computed data from core/base plugin
    rest, //Rest authenticated GitHub octokit
    graphql, //Graph QL authenticated GitHub octokit
    queries, //Autoloaded queries from ./queries
    account, //Account type ("user" or "organization")
  },
  //Settings and tokens
  {
    enabled = false,
    extras = false,
  } = {}) {
    //Plugin execution
    try {
      //Check if plugin is enabled and requirements are met
      if ((!q.my_plugin)||(imports.metadata.plugins.my_plugin.enabled(enabled, {extras})))
        return null

      //Automatically validate user inputs
      //An error will be thrown if `account` type is not supported
      //Inputs will have correct typing from `metadata.yml` and unset or invalid options will be set to default
      let {option} = imports.metadata.plugins.my_plugin.inputs({data, account, q})

      //Automatically template query from /source/plugins/myplugin/queries/myquery.graph ql
      const {[account]:stuff} = await graphql(queries.myplugin.myquery({login, account, option}))

      //Results
      return {stuff}
    }
    //Handle errors
    catch (error) {
      throw imports.format.error(error)
    }
}
```

> ⚠️ Remember, a plugin should never edit its original arguments, as it is shared amongst other plugins and would create unattended side effects

### 💬 Creating partials

Just create a new `.ejs` file in `partials` folder from templates you wish to support, and reference it into their `partials/_.json`.

Plugin partials should be able to handle gracefully their own state and errors.

Below is a minimal snippet of a partial:
```ejs
<% if (plugins.{plugin_name}) { %>
  <% if (plugins.{plugin_name}.error) { %>
    <%= plugins.{plugin_name}.error.message %>
  <% } else { %>
    <%# content %>
  <% } %>
<% } %>
```

Partials should have the match the same name as plugin handles, as they're used to display plugin compatibility in auto-generated header.

[EJS](https://github.com/mde/ejs) framework is used to template content through templating tags (``).

### 💬 Filling `README.md`

`README.md` is used as documentation.

Most of it will is auto-generated by `metadata.yml` and `examples.yml` content, so usually it is not required to manually edit it.

The default content looks like below:
```markdown
<ǃ--header-->
<ǃ--/header-->

## ➡️ Available options

<ǃ--options-->
<ǃ--/options-->

## ℹ️ Examples workflows

<ǃ--examples-->
<ǃ--/examples-->
```

- `<ǃ--header-->` will be replaced by an auto-generated header containing plugin name, supported features and output examples based on `metadata.yml`
- `<ǃ--options-->` will be replaced by an auto-generated table containing all referenced option from `metadata.yml`
- `<ǃ--examples-->` will be replaced by workflows from `examples.yml`

> ⚠️ Do not replace these auto-generated placeholder yet! They will be built by the ci workflow and will help making your pull request easier to read

When a plugin requires a token, please add a `## 🗝️ Obtaining a {service} token` section after the available options section.

Complex features may also be documented in additional sections after available options section options if required.

Try to respect current format of `README.md` from other plugins and use a neutral and impersonal writing style if possible.

### 💬 Filling `examples.yml`

Workflow examples from `examples.yml` are used as unit testing and to auto-generate documentation in the `README.md`.

It uses the same syntax as GitHub action and looks like below:
```yml
- name: Test name
  uses: lowlighter/metrics@latest
  with:
    filename: metrics.plugin.{name}.svg
    token: ${{ secrets.METRICS_TOKEN }}
    base: ""
    plugin_{name}: yes
  prod:
    skip: true
  test:
    timeout: 1800000
    modes:
      - action
      - web
      - placeholder
```

> 💡 Tests are executed in a mocked environment to avoid causing charges on external services. It may be required to create mock testing files.

`test` is usually not needed and optional but can be set to set a custom timeout (for plugins with a high execution time) and `modes` can be used to restrict which environment should be used.

`prod` should keep `skip: true` as you should use your own render outputs as examples.

### 💬 Testing locally and creating mocked data

The easiest way to test a new plugin is to setup a web instance locally ([see documentation](.github/readme/partials/documentation/setup/local.md)).

Once server is started, open a browser and try to generate an output with your new plugin enabled and check if it works as expected:
```
http://localhost:3000/username?base=0&my-plugin=1
```

> 💡 You may need to configure your server first by editing `settings.json`. Ensure that:
> - `token` is correctly set when working with GitHub APIs
> - `plugins.default` is set to `true` as plugins are disabled by default
>   - or enable your plugins by manually in `plugins`.`my-plugin`.`enabled`
> -  `debug` is set to `true` for more verbose output

When your plugin is finalized, you may need to create mocked data if it either uses GitHub APIs or any external service.

They must be created in `tests/mocks/api`:
- use `github` directory for all related GitHub APIs data
- use `axios` directory for all external service that you call using `imports.axios`

> 💡 Files from these directories are auto-loaded, so it is just required to create them with faked data.

Finally [/source/app/web/statics/app.placeholder.js](/source/app/web/statics/app.placeholder.js) to add mocked placeholder data to make users using the shared instance able to preview a render locally without any server computation.

### 💬 Submitting a pull request

If you made it until there, congratulations 🥳!

You're almost done, review the following checklist before submitting a pull request:
- [x] I have correctly filled `metadata.yml`
  - [x] `name` is set with an unused emoji and plugin name
  - [x] `category` is set to `community`
  - [x] `examples` contains links towards a rendered output hosted by you
  - [x] `authors` contains my GitHub username
  - [x] `supports` list which account type are supported
  - [x] `scopes` are correctly listed with their associated names on GitHub (leave an empty array if not applicable)
  - [x] `inputs` are correctly filled
- [x] I have implemented my plugin
  - [x] `index.mjs` respects the plugins guidelines
- [x] I have tested my plugin locally
  - [x] `tests/mocks` ... have been created
  - [x] `app.placeholder.js` has been updated for preview from web instances
  - [x] `examples.yml` contains workflows examples (at least one is required)
    - [x] `skip: true` has been set for `prod` attribute in each test
  - [x] `npm run linter` yields no errors
- [x] I have documented my plugin
  - [x] `README.md` eventually describes complex setup or options (if applicable)
- [x] I am ready!
  - [x] Checkout any generated files (in fact, don't run `npm run build`)
  - [x] Commit and push your changes (commits are squashed, no need to rebase)
  - [x] Open a new [pull request](https://github.com/lowlighter/metrics/pulls)
  - [x] Post a screenshot or a render in the pull request so it can be previewed

> 💡 A pull request **will need** to have passing builds and an example screenshot if you want to get it merged.
> Maintainers may request changes in some cases

> 🎊 Thanks a lot for your contribution!
````

## File: source/plugins/contributors/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🏅 Repository contributors</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin display repositories contributors from a commit range along with additional stats.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>By contribution types</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.contributors.categories.svg" alt=""></img></details>
      <details><summary>By number of contributions</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.contributors.contributions.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors</code></h4></td>
    <td rowspan="2"><p>Enable contributors plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_base</code></h4></td>
    <td rowspan="2"><p>Base reference</p>
<p>Can be a commit, tag, branch, etc.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_head</code></h4></td>
    <td rowspan="2"><p>Head reference</p>
<p>Can be a commit, tag, branch, etc.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> master<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored users</p>
<p>Can be used to ignore bots activity</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>users_ignored</code><br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_contributions</code></h4></td>
    <td rowspan="2"><p>Contributions count</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>contributors</code>: all contributors</li>
<li><code>categories</code>: contributors sorted by contributions categories (must be configured with <a href="/source/plugins/contributors/README.md#plugin_contributors_categories"><code>plugin_contributors_categories</code></a>)</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> contributors<br>
<b>allowed values:</b><ul><li>contributors</li><li>categories</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_contributors_categories</code></h4></td>
    <td rowspan="2"><p>Contribution categories</p>
<p>This option requires <a href="/source/plugins/contributors/README.md#plugin_contributors_sections"><code>plugin_contributors_sections</code></a> to have <code>categories</code> in it to be effective.
Pass a JSON object mapping category with file globs</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.tempdir</i></li>
<li><i>metrics.run.git</i></li>
</ul>
<b>type:</b> <code>json</code>
<br>
<b>default:</b> <details><summary>→ Click to expand</summary><pre language="json"><code>{
  "📚 Documentation": ["README.md", "docs/**"],
  "💻 Code": ["source/**", "src/**"],
  "#️⃣ Others": ["*"]
}
</code></pre></details><br></td>
  </tr>
</table>
<!--/options-->

## 🗂️ Setting up contribution categories

Pass a JSON object to `plugin_contributors_categories` with categories names as keys and arrays of file globs as values to configure contributions categories.

Each modified file by a contributor matching a file glob will add them in said category.

> 💡 File matching respect keys order

> 💡 Use `|` YAML multiline operator for better readability

*Example: *
```yaml
- uses: lowlighter/metrics@latest
  with:
    plugin_contributors: yes
    plugin_contributors_categories: |
      {
        "📚 Documentation": ["README.md", "docs/**"],
        "💻 Code": ["source/**", "src/**"],
        "#️⃣ Others": ["*"]
      }
```

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Contributors with contributions count
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.contributors.contributions.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  template: repository
  repo: metrics
  plugin_contributors: yes
  plugin_contributors_contributions: yes

```
```yaml
name: Contributors by categories
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.contributors.categories.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  template: repository
  repo: metrics
  plugin_contributors: yes
  plugin_contributors_sections: categories
  plugin_contributors_categories: |
    {
      "🧩 Plugins / 🖼️ templates":["source/plugins/**", "source/templates/**"],
      "📚 Documentation":["README.md", "**/README.md", "**/metadata.yml"],
      "💻 Code (other)":["source/**", "Dockerfile"]
    }

```
<!--/examples-->
````

## File: source/plugins/core/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🧱 Core</h3></th></tr>
  <tr><td colspan="2" align="center"><p>Global configuration and options</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🗝️ token</code> <code>🗝️ committer_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

[➡️ Jump to all available options](#%EF%B8%8F-available-options)

## 🌐 Configure used timezone

By default, dates use Greenwich meridian (GMT/UTC).

Configure `config_timezone` (see [supported timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)) to avoid time offsets.

*Example: configuring timezone*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_timezone: Europe/Paris
```

## 📦 Ordering content

Content can be manually ordered using `config_order` option.

*Example: display base.header, isocalendar, languages and stars in this specific order*
```yaml
- uses: lowlighter/metrics@latest
  with:
    base: header
    plugin_isocalendar: yes
    plugin_languages: yes
    plugin_stars: yes
    config_order: base.header, isocalendar, languages, stars
```

> 💡 Omitted sections will be appended at the end using default order

> ℹ️ The handles to use for each plugin and sections is based on the [`partials/_.json`](/source/templates/classic/partials/_.json) of the template.
> It may not necessarily be the plugin id (e.g. `base.header`, `base.activity+community`, `base.repositories`, etc.).

## 🔕 Skipping repositories in plugins

Some plugins support a `plugin_*_skipped` option which is used to skipped repositories from result. It inherits the global option [`repositories_skipped`](/source/plugins/base/README.md#repositories_skipped) which makes it easier to ignore repositories from all plugins at once.

These options support two different syntaxes:

### Basic pattern matching

Skip repositories by:
- using their full handle (e.g. `user/repo`)
- using only their name (e.g. `repo`)
  - *in this case, the owner may be implicitly set to current `user` option*

*Example: skipping repositories with basic pattern matching*
```yml
repositories_skipped: my-repo, user/my-repo
```

> 💡 Either comma or newlines can be used to separate basic patterns

### Advanced pattern matching

To enable advanced pattern matching to skip repositories, include `@use.patterns` at the beginning of the option value.

Skip repositories by writing file-glob patterns, with any of the supported operation:
- `#` to write comments
- `-` to exclude repositories
  - *the `-` is implicit and may be omitted from excluding patterns*
- `+` to include back repositories

> ℹ️ *metrics* use [isaacs/minimatch](https://github.com/isaacs/minimatch) as its file-glob matcher

*Example: skipping repositories with basic advanced matching*
```yml
repositories_skipped: |
  @use.patterns

  # Skip a specific repository (both patterns are equivalent)
  user/repo
  -user/repo

  # Skip repositories matching a given pattern
  user/repo-*
  {user1, user2, user3}/*

  # Include back a previously skipped repository
  org/repo
  +org/include-this-repo
```

> ℹ️ Unlike basic pattern matching, patterns are always tested against the full repository handle (the user will not be implicitly added)

> ⚠️ As patterns may contain commas, be sure to use newlines rather than commas as separator to ensure patterns are correctly parsed

## 🪛 Using presets

It is possible to reuse the same configuration across different repositories and workflows using configuration presets.
A preset override the default values of inputs, and multiple presets can be provided at once through URLs or file paths.

Options resolution is done in the following order:
- default values
- presets, from first to last
- user values

*Example: using a configuration preset from an url*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_presets: https://raw.githubusercontent.com/lowlighter/metrics/presets/lunar-red/preset.yaml
```

Some presets are hosted on this repository on the [`@presets`](https://github.com/lowlighter/metrics/tree/presets) branch and can be used directly by using their identifier prefixed by an arobase (`@`).

*Example: using a pre-defined configuration preset*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_presets: "@lunar-red"
```

> ⚠️ `🔐 Tokens` and options marked with `⏯️ Cannot be preset`, as they suggest, cannot be preset and thus requires to be explicitly defined to be set.

> ℹ️ Presets configurations use [schemas](https://github.com/lowlighter/metrics/tree/presets/%40schema) to ensure compatibility between format changes

## 🎨 Custom CSS styling

Additional CSS can be injected using `extras_css` option.

*Example: changing the color of `h2`*
```yaml
- uses: lowlighter/metrics@latest
  with:
    base: header
    extras_css: |
      h2 {
        color: red;
      }
```

> 💡 *metrics* does not use `!important` keyword, so use it when having trouble when styling is not applied

> 💡 If you make an heavy use of this option, creating a [community templates](/source/templates/community/README.md) may be a better alternative

> ⚠️ CSS styles may slightly change between releases, backward compatibility is not guaranteed!

## 🗳️ Custom JavaScript scripting

Additional JavaScript can be injected using `extras_js` option.

*Example: removing all `h2`*
```yaml
- uses: lowlighter/metrics@latest
  with:
    base: header
    extras_js: |
      document.querySelectorAll("h2")?.forEach(h2 => h2.remove())
```

> ℹ️ JavaScript is executed in puppeteer context during the rendering phase, **not** in *metrics* context.
> It will be possible to access `document` and all other features accessible like if the SVG was opened in a browser page

> 💡 If you make an heavy use of this option, creating a [community templates](/source/templates/community/README.md) may be a better alternative

> ⚠️ HTML elements may slightly change between releases, backward compatibility is not guaranteed!

## 🔲 Adjusting padding

SVG rendering is dependent on operating system, browser and fonts combination and may look different across different platforms.

It may not look like it, but computing the height of a SVG is not trivial. *metrics* spawns an headless browser and try to do its best to resize the result, but it may sometimes ends up in either cropped or oversized images.

Tweak `config_padding` option to manually adjust padding and solve this issue.

This settings supports the following format:
- 1 value for both width and height
- 2 values for width first and height second, separated by a comma (`,`)

> 💡 Both negative and positive values are allowed

Each value need to respect the following format:
- {number}
- {number} + {number}%
- {number}%

> 💡 Percentage based values are relative to the height computed by puppeteer

*Example: add 10px padding for both width and height*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_padding: 10
```

*Example: add 10px padding to height and increase it by 8%*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_padding: 0, 10 + 8%
```

*Example: remove 10% from height*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_padding: 0, -10%
```

## ↔️ Controlling display size

Some templates may support different output display size.

A `regular` display size will render a medium-sized image suitable for both desktop and mobile displays, while a `large` one will be more suitable only for desktop and some plugins (like [`📌 topics`](/source/plugins/topics/README.md) or [`🏅 contributors`](/source/plugins/contributors/README.md))

The `columns` display will render a full-width image with automatic resizing: two columns for desktop and a single one column for mobiles.

*Example: output a PNG image*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_display: large
```

## 💱 Configuring output format

Use `config_output` to change output format.

*Example: output a PNG image*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_output: png
```

A JSON output can be used to retrieved collected data and use it elsewhere.

*Example: output a JSON data dump*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_output: json
```

When using a PDF output, it is advised to set `config_base64: yes` to encode embed images in base64 in order to make self-contained documents.

*Example: output a self-contained PDF document*
```yaml
- uses: lowlighter/metrics@latest
  with:
    markdown: TEMPLATE.md
    config_output: markdown-pdf
    config_base64: yes
```

## ✨ Render `Metrics insights` statically

It is possible to generate a self-contained HTML file containing `✨ Metrics insights` output by using `config_output: insights`.

> 💡 Note that like `✨ Metrics insights` content is not configurable, thus any other plugin option will actually be ignored

*Example: output `✨ Metrics insights` report*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_output: insights
```

## 🧶 Configuring output action

Before configuring output action, ensure that workflows permissions are properly set.
These can be changed either through repository settings in Actions tab:

![Setting workflows permissions](/.github/readme/imgs/setup_workflow_permissions.light.png#gh-light-mode-only)
![Setting workflows permissions](/.github/readme/imgs/setup_workflow_permissions.dark.png#gh-dark-mode-only)

Or more granulary [at job or workflow level](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token).

### Using commits (default)

Use `output_action: commit` to make the action directly push changes to `committer_branch` with a commit.
A custom commit message can be used through `committer_message`.

> 💡 *metrics* will automatically ignore push events with a commit message containing `[Skip GitHub Action]` or `Auto-generated metrics for run #` to avoid infinite loops. Note that by default, GitHub already ignore events pushed by `${{ github.token }}` or containing `[skip ci]` in commit message

*Example: push output to metrics-renders branch rather than the default branch*
```yaml
metrics:
  permissions:
    contents: write
  steps:
    - uses: lowlighter/metrics@latest
      with:
        output_action: commit
        committer_branch: metrics-renders
        committer_message: "chore: update metrics"
```

### Using pull requests

Use `output_action: pull-request` to make the action open a new pull request and push changes from the same run on it.

The last step should use either `pull-request-merge`, `pull-request-squash` or `pull-request-rebase` to merge changes to `committer_branch`.

> 💡 When using `pull-request` output action, do not forget to change `filename` too or previous output will be overwritten!

*Example: push two outputs using a merge pull request*
```yaml
metrics:
  permissions:
    contents: write
    pull-requests: write
  steps:
    - uses: lowlighter/metrics@latest
      with:
        filename: my-metrics-0.svg
        output_action: pull-request

    - uses: lowlighter/metrics@latest
      with:
        filename: my-metrics-1.svg
        output_action: pull-request-merge
```

### Using gists

Use `output_action: gist` to push output to a [GitHub gist](https://gist.github.com) instead.
It is required to provide a gist id to `committer_gist` option to make it work.

> 💡 This feature will use `token` instead of `committer_token` to push changes, so `gists` scope must be granted to the original `token` first

*Example: push output to a gist*
```yaml
metrics:
  steps:
    - uses: lowlighter/metrics@latest
      with:
        output_action: gist
        committer_gist: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Manual handling

Use `output_action: none` to perform custom processing with outputs.
They will be available under `/metrics_renders/{filename}` in the runner.

*Example: generate outputs and manually push them*
```yaml
metrics:
  permissions:
    contents: write
  steps:
    - name: Checkout repository
      uses: actions/checkout@v3
        with:
          fetch-depth: 0

    - uses: lowlighter/metrics@latest
      with:
        output_action: none

    - uses: lowlighter/metrics@latest
      run: |
        set +e
        git checkout metrics-renders
        git config user.name github-actions[bot]
        git config user.email 41898282+github-actions[bot]@users.noreply.github.com
        sudo mv /metrics_renders/* ./
        git add --all
        git commit -m "chore: push metrics"
        git push
```

## ♻️ Retrying automatically failed rendering and output action

Rendering is subject to external factors and can fail occasionally.
Use `retries` and `retries_delay` options to automatically retry rendering.

*Example: retry render up to 3 times (wait 5 minutes between each fail)*
```yaml
- uses: lowlighter/metrics@latest
  with:
    retries: 3
    retries_delay: 300
```

Output action is also subject to GitHub API rate-limiting and overall health status and can fail occasionally.
Use `retries_output_action` and `retries_delay_output_action` options to automatically retry output action.

> 💡 As output action is a separate step from rendering, render step won't be called again

*Example: retry output action up to 5 times (wait 2 minutes between each fail)*
```yaml
- uses: lowlighter/metrics@latest
  with:
    retries_output_action: 5
    retries_delay_output_action: 120
```

## 🗜️ Optimize SVG output

To reduce filesize and decrease loading time, *metrics* offers several optimization options, such as purging unused CSS and style minification, XML pretty-printing (which also reduce diffs between changes) and general SVG optimization (still experimental).

> 💡 This option is enabled by default!

*Example: optimize CSS and XML*
```yaml
- uses: lowlighter/metrics@latest
  with:
    optimize: css, xml
```

*Example: optimize SVG (experimental)*
```yaml
- uses: lowlighter/metrics@latest
  with:
    optimize: svg
    experimental_features: --optimize-svg
```

## 🐳 Faster execution with prebuilt docker images

When using `lowlighter/metrics` official releases as a GitHub Action, a prebuilt docker container image will be pulled from [GitHub Container Registry](https://github.com/users/lowlighter/packages/container/package/metrics). It allows to significantly reduce workflow execution time.

> 💡 This option is enabled by default!

On forks, this feature is disable to take into account any changes you made on it.

*Example: using prebuilt docker image*
```yaml
- uses: lowlighter/metrics@latest
  with:
    use_prebuilt_image: yes
```

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>token</code></h4></td>
    <td rowspan="2"><p>GitHub Personal Access Token</p>
<p>No scopes are required by default, though some plugins and features may require additional scopes.</p>
<p>When using a configuration which does not requires a GitHub PAT, it is possible to pass <code>NOT_NEEDED</code> instead.
When doing so, any settings which defaults on user fetched values will not be templated (e.g. <code>.user.*</code>) and will usually need to be set manually.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">✔️ Required<br>
🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>user</code></h4></td>
    <td rowspan="2"><p>GitHub username</p>
<p>Defaults to <a href="/source/plugins/core/README.md#token"><code>token</code></a> owner username.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>repo</code></h4></td>
    <td rowspan="2"><p>GitHub repository</p>
<p>This option is only revelant for repositories templates</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>committer_token</code></h4></td>
    <td rowspan="2"><p>GitHub Token used to commit metrics</p>
<p>Leave this to <code>${{ github.token }}</code> or <code>${{ secrets.GITHUB_TOKEN }}</code>, which is a special auto-generated token restricted to current repository scope.</p>
<blockquote>
<p>💡 When using <a href="/source/plugins/core/README.md#output_action"><code>output_action: gist</code></a>, it will use <a href="/source/plugins/core/README.md#token"><code>token</code></a> instead, since gists are outside of scope</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br>
<b>default:</b> ${{ github.token }}<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>committer_branch</code></h4></td>
    <td rowspan="2"><p>Target branch</p>
<p>Defaults to current repository default branch</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>committer_message</code></h4></td>
    <td rowspan="2"><p>Commit message</p>
<p>Use <code>${filename}</code> to display filename</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> Update ${filename} - [Skip GitHub Action]<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>committer_gist</code></h4></td>
    <td rowspan="2"><p>Gist id</p>
<p>Specify an existing gist id (can be retrieved from its URL) when using <a href="/source/plugins/core/README.md#output_action"><code>output_action: gist</code></a>.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>filename</code></h4></td>
    <td rowspan="2"><p>Output path</p>
<p>When using an asterisk (<code>*</code>), correct extension will automatically be applied according to <a href="/source/plugins/core/README.md#config_output"><code>config_output</code></a> value</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> github-metrics.*<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>markdown</code></h4></td>
    <td rowspan="2"><p>Markdown template path</p>
<p>It can be either a local path or a full link (e.g. <a href="https://raw.githubusercontent.com">https://raw.githubusercontent.com</a>)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> TEMPLATE.md<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>markdown_cache</code></h4></td>
    <td rowspan="2"><p>Markdown file cache</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> .cache<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>output_action</code></h4></td>
    <td rowspan="2"><p>Output action</p>
<ul>
<li><code>none</code>: just create file in <code>/metrics_renders</code> directory of action runner</li>
<li><code>commit</code>: push output to <code>committer_branch</code></li>
<li><code>pull-request</code>: push output to a new branch and open a pull request to <code>committer_branch</code></li>
<li><code>pull-request-merge</code>: same as <code>pull-request</code> and additionally merge pull request</li>
<li><code>pull-request-squash</code>: same as <code>pull-request</code> and additionally squash and merge pull request</li>
<li><code>pull-request-rebase</code>: same as <code>pull-request</code> and additionally rebase and merge pull request</li>
<li><code>gist</code>: push output to <code>committer_gist</code></li>
</ul>
<blockquote>
<p>💡 When using <code>pull-request</code>, you will need to set the last job with a <code>pull-request-*</code> action instead, else it won&#39;t be merged</p>
</blockquote>
<blockquote>
<p>⚠️ As GitHub gists API does not support binary files upload, <code>gist</code> does not support <a href="/source/plugins/core/README.md#config_output"><code>config_output</code></a> set to either <code>png</code>, <code>jpeg</code> or <code>markdown-pdf</code></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> commit<br>
<b>allowed values:</b><ul><li>none</li><li>commit</li><li>pull-request</li><li>pull-request-merge</li><li>pull-request-squash</li><li>pull-request-rebase</li><li>gist</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>output_condition</code></h4></td>
    <td rowspan="2"><p>Output condition</p>
<ul>
<li><code>always</code>: always try to push changes</li>
<li><code>data-changed</code>: skip changes if no data changed (e.g. like when only metadata changed)</li>
</ul>
<blockquote>
<p>ℹ️ This option is only revelant when <a href="/source/plugins/core/README.md#config_output"><code>config_output: svg</code></a> is set</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> always<br>
<b>allowed values:</b><ul><li>always</li><li>data-changed</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>optimize</code></h4></td>
    <td rowspan="2"><p>Optimization features</p>
<ul>
<li><code>css</code>: purge and minify CSS styles</li>
<li><code>xml</code>: pretty-print XML (useful to reduce diff)</li>
<li><code>svg</code>: optimization with SVGO (experimental, requires <a href="/source/plugins/core/README.md#experimental_features"><code>experimental_features: --optimize-svg</code></a>)</li>
</ul>
<p>Templates may not always honour all provided options</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> css, xml<br>
<b>allowed values:</b><ul><li>css</li><li>xml</li><li>svg</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>setup_community_templates</code></h4></td>
    <td rowspan="2"><p>Community templates to setup</p>
<p>See <a href="https://github.com/lowlighter/metrics/blob/master/source/templates/community/README.md">community templates guide</a> for more informations</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.setup.community.templates</i></li>
</ul>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>template</code></h4></td>
    <td rowspan="2"><p>Template</p>
<p>Community templates must be prefixed by at sign (<code>@</code>)
See <a href="https://github.com/lowlighter/metrics/blob/master/README.md#%EF%B8%8F-templates">list of supported templates</a></p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> classic<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>query</code></h4></td>
    <td rowspan="2"><p>Query parameters</p>
<p>Pass additional parameters to templates.
This is mostly useful for custom templates.</p>
<blockquote>
<p>⚠️ <strong>Do not</strong> use this option to pass other existing parameters, they will be overwritten</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>json</code>
<br>
<b>default:</b> <details><summary>→ Click to expand</summary><pre language="json"><code>{}</code></pre></details><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>extras_css</code></h4></td>
    <td rowspan="2"><p>Extra CSS</p>
<p>Custom CSS that will be injected in used template.
Useful to avoid creating a new template just to tweak some styling</p>
<blockquote>
<p>💡 <em>metrics</em> tends to avoid using <code>!important</code> rules, which means that most styling can be overridden by this option when using <code>!important</code></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.user.css</i></li>
</ul>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>extras_js</code></h4></td>
    <td rowspan="2"><p>Extra JavaScript</p>
<p>Custom JavaScript that will be executed during puppeteer rendering.
Useful to avoid creating a new template just to tweak some content.</p>
<blockquote>
<p>⚠️ Note that is it executed within puppeteer context and <strong>not</strong> within <em>metrics</em> context.
No access to fetched data or configuration will be offered through this context.
It is run after transformations and optimizations, but just before resizing.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.user.js</i></li>
</ul>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>github_api_rest</code></h4></td>
    <td rowspan="2"><p>GitHub REST API endpoint</p>
<p>Can be used to support <a href="https://github.com/enterprise">GitHub enterprises server</a>.
Leave empty to use default endpoint.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>github_api_graphql</code></h4></td>
    <td rowspan="2"><p>GitHub GraphQL API endpoint</p>
<p>Can be used to support <a href="https://github.com/enterprise">GitHub enterprises server</a>.
Leave empty to use default endpoint.</p>
<blockquote>
<p>ℹ️ GraphQL octokit will automatically append <code>/graphql</code> to provided endpoint</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_timezone</code></h4></td>
    <td rowspan="2"><p>Timezone for dates</p>
<p>See <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">list of supported timezone</a></p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_order</code></h4></td>
    <td rowspan="2"><p>Plugin order</p>
<p>By default, templates use <code>partials/_.json</code> ordering.
You can override the content order by using this setting.</p>
<p>If some partials are omitted, they will be appended at the end with default ordering</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_twemoji</code></h4></td>
    <td rowspan="2"><p>Use twemojis</p>
<p>Replace emojis by <a href="%5Btwemojis%5D(https://github.com/twitter/twemoji)">twemojis</a> to have a consistent render across all platforms
May increase filesize.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_gemoji</code></h4></td>
    <td rowspan="2"><p>Use GitHub custom emojis</p>
<p>GitHub supports additional emojis which are not registered in Unicode standard (:octocat:, :shipit:, :trollface:, ...)
See full list at <a href="https://api.github.com/emojis">https://api.github.com/emojis</a>.</p>
<p>This option has no effect when [`token: NOT_NEEDED``](/source/plugins/core/README.md#token) is set.</p>
<p>May increase filesize</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_octicon</code></h4></td>
    <td rowspan="2"><p>Use GitHub octicons</p>
<p>Octicons are open-sourced icons provided by GitHub.
See full list at <a href="https://primer.style/octicons">https://primer.style/octicons</a>.</p>
<p>To include an octicon, use the following syntax: <code>:octicon-{name}-{size}:</code>.
Size must be a supported icon size (12, 16 or 24).
16px octicons can omit size and directly use <code>:octicon-{name}:</code> syntax.</p>
<p>May increase filesize</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_display</code></h4></td>
    <td rowspan="2"><p>Display width (for image output formats)</p>
<ul>
<li><code>regular</code>: 480px width</li>
<li><code>large</code>: 960px width (may not be supported by all templates)</li>
<li><code>columns</code>: Full width with auto-sizing (two columns for desktops, and one column for mobile)<ul>
<li>known issue: <a href="https://github.com/lowlighter/metrics/issues/374">https://github.com/lowlighter/metrics/issues/374</a></li>
</ul>
</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> regular<br>
<b>allowed values:</b><ul><li>regular</li><li>large</li><li>columns</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_animations</code></h4></td>
    <td rowspan="2"><p>Use CSS animations</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_base64</code></h4></td>
    <td rowspan="2"><p>Base64-encoded images</p>
<p>Enable this option to make self-contained output (i.e. with no external links)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏭️ Global option<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_padding</code></h4></td>
    <td rowspan="2"><p>Output padding</p>
<p>Although <em>metrics</em> try to auto-guess resulting height, rendering is still dependent on OS and browser settings.
It can result in cropped or oversized outputs.</p>
<p>This settings let you manually adjust padding with the following format:</p>
<ul>
<li>1 value for both width and height</li>
<li>2 values for width fist and height second, separated by a comma (<code>,</code>)</li>
</ul>
<p>Each value need to respect the following format:</p>
<ul>
<li><code>{number}</code></li>
<li><code>{number} + {number}%</code></li>
<li><code>{number}%</code></li>
</ul>
<p>Percentage are relative to computed dimensions</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 0, 8 + 11%<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_output</code></h4></td>
    <td rowspan="2"><p>Output format</p>
<ul>
<li><code>auto</code>: Template default (usually <code>svg</code> or <code>markdown</code>)</li>
<li><code>svg</code>: SVG image</li>
<li><code>png</code>: PNG image (animations not supported)</li>
<li><code>jpeg</code>: JPEG image (animations and transparency not supported)</li>
<li><code>json</code>: JSON data dump</li>
<li><code>markdown</code>: Markdown rendered file</li>
<li><code>markdown-pdf</code>: PDF from markdown rendered file</li>
<li><code>insights</code>: Metrics Insights self-contained HTML file (not configurable)</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> auto<br>
<b>allowed values:</b><ul><li>auto</li><li>svg</li><li>png</li><li>jpeg</li><li>json</li><li>markdown</li><li>markdown-pdf</li><li>insights</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>config_presets</code></h4></td>
    <td rowspan="2"><p>Configuration presets</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.setup.community.presets</i></li>
</ul>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>retries</code></h4></td>
    <td rowspan="2"><p>Retries in case of failures (for rendering)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 10)</i>
<br>
<b>default:</b> 3<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>retries_delay</code></h4></td>
    <td rowspan="2"><p>Delay between each retry (in seconds, for rendering)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 3600)</i>
<br>
<b>default:</b> 300<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>retries_output_action</code></h4></td>
    <td rowspan="2"><p>Retries in case of failures (for output action)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 10)</i>
<br>
<b>default:</b> 5<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>retries_delay_output_action</code></h4></td>
    <td rowspan="2"><p>Delay between each retry (in seconds, for output action)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 3600)</i>
<br>
<b>default:</b> 120<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>clean_workflows</code></h4></td>
    <td rowspan="2"><p>Clean previous workflows jobs</p>
<p>This can be used to clean up Action tabs from previous workflows runs.</p>
<p>Use <code>all</code> to clean up workflows runs in any state.</p>
<blockquote>
<p>⚠️ When reporting issues, it is <strong>required</strong> to provide logs so it can be investigated and reproduced.
Be sure to disable this option when asking for help or submitting bug reports.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>allowed values:</b><ul><li>cancelled</li><li>failure</li><li>success</li><li>skipped</li><li>startup_failure</li><li>timed_out</li><li>all</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>delay</code></h4></td>
    <td rowspan="2"><p>Job delay</p>
<p>This can be used to avoid triggering GitHub abuse mechanics on large workflows</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 3600)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>quota_required_rest</code></h4></td>
    <td rowspan="2"><p>Minimum GitHub REST API requests quota required to run</p>
<p>Action will cancel itself without any errors if requirements are not met</p>
<p>This option has no effect when <a href="/source/plugins/core/README.md#token"><code>token: NOT_NEEDED</code></a> is set</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 5000)</i>
<br>
<b>default:</b> 200<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>quota_required_graphql</code></h4></td>
    <td rowspan="2"><p>Minimum GitHub GraphQL API requests quota required to run</p>
<p>Action will cancel itself without any errors if requirements are not met</p>
<p>This option has no effect when <a href="/source/plugins/core/README.md#token"><code>token: NOT_NEEDED</code></a> is set</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 5000)</i>
<br>
<b>default:</b> 200<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>quota_required_search</code></h4></td>
    <td rowspan="2"><p>Minimum GitHub Search API requests quota required to run</p>
<p>Action will cancel itself without any errors if requirements are not met</p>
<p>This option has no effect when <a href="/source/plugins/core/README.md#token"><code>token: NOT_NEEDED</code></a> is set</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 30)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>notice_releases</code></h4></td>
    <td rowspan="2"><p>Notice about new releases of metrics</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>use_prebuilt_image</code></h4></td>
    <td rowspan="2"><p>Use pre-built docker image from <a href="https://github.com/lowlighter/metrics/pkgs/container/metrics">GitHub container registry</a></p>
<p>It allows to save build time and make job significantly faster, and there is almost no reason to disable this settings.
This option has no effects on forks (images will always be rebuilt from Dockerfile)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugins_errors_fatal</code></h4></td>
    <td rowspan="2"><p>Fatal plugin errors</p>
<p>When enabled, the job will fail in case of plugin errors, else it will be handled gracefully in output with an error message</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>debug</code></h4></td>
    <td rowspan="2"><p>Debug mode</p>
<p>This setting is automatically enable if a job fail (useful with <a href="/source/plugins/core/README.md#plugins_errors_fatal"><code>plugins_errors_fatal: yes</code></a>)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>verify</code></h4></td>
    <td rowspan="2"><p>SVG validity check</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.npm.optional.libxml2</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>debug_flags</code></h4></td>
    <td rowspan="2"><p>Debug flags</p>
<ul>
<li><code>--cakeday</code>: simulate registration anniversary</li>
<li><code>--halloween</code>: enable halloween colors <em>(only first color scheme will be applied if multiple are specified)</em></li>
<li><code>--winter</code>: enable winter colors <em>(only first color scheme will be applied if multiple are specified)</em></li>
<li><code>--error</code>: force render error</li>
<li><code>--puppeteer-debug</code>: enable puppeteer debug mode*</li>
<li><code>--puppeteer-disable-headless</code>: disable puppeteer headless mode <em>(requires a graphical environment)</em>*</li>
<li><code>--puppeteer-wait-load</code>: override puppeteer wait events*</li>
<li><code>--puppeteer-wait-domcontentloaded</code>: override puppeteer wait events*</li>
<li><code>--puppeteer-wait-networkidle0</code>: override puppeteer wait events*</li>
<li><code>--puppeteer-wait-networkidle2</code>: override puppeteer wait events*</li>
</ul>
<blockquote>
<p><em>* 🌐 Web instances needs to have <a href="/source/plugins/core/README.md#debug"><code>debug</code></a> set in <code>settings.json</code> for these flags to be supported.</em></p>
</blockquote>
<blockquote>
<p>⚠️ No backward compatibility is guaranteed for these features, they are only meant for debugging purposes.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>array</code>
<i>(space-separated)</i>
<br>
<b>allowed values:</b><ul><li>--cakeday</li><li>--halloween</li><li>--winter</li><li>--error</li><li>--puppeteer-debug</li><li>--puppeteer-disable-headless</li><li>--puppeteer-wait-load</li><li>--puppeteer-wait-domcontentloaded</li><li>--puppeteer-wait-networkidle0</li><li>--puppeteer-wait-networkidle2</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>debug_print</code></h4></td>
    <td rowspan="2"><p>Print output in console</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>dryrun</code></h4></td>
    <td rowspan="2"><p>Dry-run</p>
<blockquote>
<p>⚠️ Unlike <a href="/source/plugins/core/README.md#output_action"><code>output_action: none</code></a>, output file won&#39;t be available in <code>/metrics_renders</code> directory</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>experimental_features</code></h4></td>
    <td rowspan="2"><p>Experimental features</p>
<blockquote>
<p>⚠️ No backward compatibility is guaranteed for these features</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>array</code>
<i>(space-separated)</i>
<br>
<b>allowed values:</b><ul><li>--optimize-svg</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>use_mocked_data</code></h4></td>
    <td rowspan="2"><p>Use mocked data instead of live APIs</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
🔧 For development<br>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->
````

## File: source/plugins/discussions/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💬 Discussions</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays GitHub discussions stats.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.discussions.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_discussions</code></h4></td>
    <td rowspan="2"><p>Enable discussions plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_discussions_categories</code></h4></td>
    <td rowspan="2"><p>Discussion categories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_discussions_categories_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (categories)</p>
<p>Note that categories are sorted from highest to lowest count</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 0<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: GitHub Discussions
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.discussions.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_discussions: yes
  plugin_discussions_categories_limit: 8

```
<!--/examples-->
````

## File: source/plugins/followup/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎟️ Follow-up of issues and pull requests</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the ratio of open/closed issues and the ratio of open/merged pull requests across repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Indepth analysis</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.indepth.svg" alt=""></img></details>
      <details><summary>Created on a user's repositories</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.svg" alt=""></img></details>
      <details><summary>Created by a user</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.user.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_followup</code></h4></td>
    <td rowspan="2"><p>Enable followup plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_followup_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>repositories</code>: overall status of issues and pull requests on your repositories</li>
<li><code>user</code>: overall status of issues and pull requests you have created on GitHub</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> repositories<br>
<b>allowed values:</b><ul><li>repositories</li><li>user</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_followup_indepth</code></h4></td>
    <td rowspan="2"><p>Indepth analysis</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.github.overuse</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_followup_archived</code></h4></td>
    <td rowspan="2"><p>Include archived repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## 🔎 `indepth` mode

The `plugin_followup_indepth` option collects additional stats to differentiate issues and pull requests opened by maintainers and users.

It helps knowing whether repositories are also maintained by other users and give an overall health status of repositories.

> ⚠️ This mode will try to list users with push access to know who are the maintainers in order to place issues in the correct category, which requires a `repo` scope. If not available, it will consider that only the owner is a maintainer.

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Opened on user's repositories
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.followup.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_followup: yes

```
```yaml
name: Opened by user
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.followup.user.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_followup: yes
  plugin_followup_sections: user

```
```yaml
name: Indepth analysis
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.followup.indepth.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_followup: yes
  plugin_followup_indepth: yes

```
```yaml
name: Exclude Archived
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.followup.archived.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_followup: yes
  plugin_followup_archived: no

```
<!--/examples-->
````

## File: source/plugins/gists/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎫 Gists</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays <a href="https://gist.github.com">gists</a> stats.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.gists.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_gists</code></h4></td>
    <td rowspan="2"><p>Enable gists plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Gists
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.gists.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_gists: yes

```
<!--/examples-->
````

## File: source/plugins/habits/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💡 Coding habits and activity</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays coding habits based on recent activity, such as active hours and languages recently used.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Recent activity charts</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.habits.charts.svg" alt=""></img></details>
      <details open><summary>Mildly interesting facts</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.habits.facts.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits</code></h4></td>
    <td rowspan="2"><p>Enable habits plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_from</code></h4></td>
    <td rowspan="2"><p>Events to use</p>
<p>A higher number will increase stats accuracy</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 200<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_days</code></h4></td>
    <td rowspan="2"><p>Event maximum age</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 30)</i>
<br>
<b>default:</b> 14<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_facts</code></h4></td>
    <td rowspan="2"><p>Mildly interesting facts</p>
<p>It includes indentation type, average number of characters per line of code, and most active time and day</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_charts</code></h4></td>
    <td rowspan="2"><p>Charts</p>
<p>It includes commit activity per hour of day and commit activity per day of week
Recent language activity may also displayed (it requires extras features to be enabled for web instances) for historical reasons</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.github.overuse</i></li>
<li><i>metrics.run.tempdir</i></li>
<li><i>metrics.run.git</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_charts_type</code></h4></td>
    <td rowspan="2"><p>Charts display type</p>
<ul>
<li><code>classic</code>: <code>&lt;div&gt;</code> based charts, simple and lightweight</li>
<li><code>graph</code>: <code>&lt;svg&gt;</code> based charts, smooth</li>
</ul>
<blockquote>
<p>⚠️ <code>chartist</code> option has been deprecated and is now equivalent to <code>graph</code></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.npm.optional.d3</i></li>
</ul>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> classic<br>
<b>allowed values:</b><ul><li>classic</li><li>graph</li><li>chartist</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_trim</code></h4></td>
    <td rowspan="2"><p>Trim unused hours on charts</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_languages_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (languages)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 8)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 8<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_habits_languages_threshold</code></h4></td>
    <td rowspan="2"><p>Display threshold (percentage)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 0%<br></td>
  </tr>
</table>
<!--/options-->

## 🌐 Configure used timezone

By default, dates use Greenwich meridian (GMT/UTC).

Configure `config_timezone` (see [supported timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)) to avoid time offsets.

*Example: configuring timezone*
```yaml
- uses: lowlighter/metrics@latest
  with:
    config_timezone: Europe/Paris
```

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Mildly interesting facts
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.habits.facts.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_habits: yes
  plugin_habits_facts: yes
  plugin_habits_charts: no
  config_timezone: Europe/Paris

```
```yaml
name: Recent activity charts
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.habits.charts.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_habits: yes
  plugin_habits_facts: no
  plugin_habits_charts: yes
  config_timezone: Europe/Paris

```
<!--/examples-->
````

## File: source/plugins/introduction/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🙋 Introduction</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays account bio or organization/repository description.</p>
<p>Since account bio is already displayed on account profile, this plugin is mostly intended for external usage.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>For a user or an organization</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.introduction.svg" alt=""></img></details>
      <details><summary>For a repository</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.introduction.repository.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_introduction</code></h4></td>
    <td rowspan="2"><p>Enable introduction plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_introduction_title</code></h4></td>
    <td rowspan="2"><p>Section title</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Organization introduction
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.introduction.svg
  token: ${{ secrets.METRICS_TOKEN }}
  user: github
  base: header
  plugin_introduction: yes

```
```yaml
name: Repository introduction
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.introduction.repository.svg
  token: ${{ secrets.METRICS_TOKEN }}
  template: repository
  repo: metrics
  base: header
  plugin_introduction: yes

```
<!--/examples-->
````

## File: source/plugins/isocalendar/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📅 Isometric commit calendar</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays an isometric view of a user commit calendar along with a few additional statistics like current streak and average number of commit per day.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Full year calendar</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.isocalendar.fullyear.svg" alt=""></img></details>
      <details><summary>Half year calendar</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.isocalendar.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_isocalendar</code></h4></td>
    <td rowspan="2"><p>Enable isocalendar plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_isocalendar_duration</code></h4></td>
    <td rowspan="2"><p>Time range</p>
<ul>
<li><code>half-year</code>: 180 days</li>
<li><code>full-year</code>: 1 year</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> half-year<br>
<b>allowed values:</b><ul><li>half-year</li><li>full-year</li></ul></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Half-year calendar
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.isocalendar.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_isocalendar: yes

```
```yaml
name: Full-year calendar
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.isocalendar.fullyear.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_isocalendar: yes
  plugin_isocalendar_duration: full-year

```
<!--/examples-->
````

## File: source/plugins/languages/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🈷️ Languages activity</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin can display which languages you use across all repositories you contributed to.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Indepth analysis (clone and analyze repositories)</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.indepth.svg" alt=""></img></details>
      <details open><summary>Recently used (analyze recent activity events)</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.recent.svg" alt=""></img></details>
      <details><summary>Default algorithm</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.svg" alt=""></img></details>
      <details><summary>Default algorithm (with details)</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.details.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages</code></h4></td>
    <td rowspan="2"><p>Enable languages plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored languages</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 8)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 8<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_threshold</code></h4></td>
    <td rowspan="2"><p>Display threshold (percentage)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 0%<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_other</code></h4></td>
    <td rowspan="2"><p>Group unknown, ignored and over-limit languages into &quot;Other&quot; category</p>
<p>If this option is enabled, &quot;Other&quot; category will not be subject to <a href="/source/plugins/languages/README.md#plugin_languages_threshold"><code>plugin_languages_threshold</code></a>.
It will be automatically hidden if empty.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_colors</code></h4></td>
    <td rowspan="2"><p>Custom languages colors</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> github<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_aliases</code></h4></td>
    <td rowspan="2"><p>Custom languages names</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<p>Note that <code>recently-used</code> is only available when <a href="/source/plugins/languages/README.md#plugin_languages_indepth"><code>plugin_languages_indepth</code></a> is enabled</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> most-used<br>
<b>allowed values:</b><ul><li>most-used</li><li>recently-used</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_details</code></h4></td>
    <td rowspan="2"><p>Additional details</p>
<p>Note that <code>lines</code> is only available when <a href="/source/plugins/languages/README.md#plugin_languages_indepth"><code>plugin_languages_indepth</code></a> is enabled</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>allowed values:</b><ul><li>bytes-size</li><li>percentage</li><li>lines</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_indepth</code></h4></td>
    <td rowspan="2"><p>Indepth mode</p>
<blockquote>
<p>⚠️ read documentation first</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.cpu.overuse</i></li>
<li><i>metrics.run.tempdir</i></li>
<li><i>metrics.run.git</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> false<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_indepth_custom</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Custom repositories</p>
<p>Specify a list of additional repositories to analyze.</p>
<p>Below are the supported syntax formats:</p>
<ul>
<li><code>owner/repo</code> (e.g. <code>lowlighter/metrics</code>)</li>
<li><code>owner/repo@branch</code> (e.g. <code>lowlighter/metrics@main</code>)</li>
<li><code>owner/repo@branch:commits</code> (e.g. <code>lowlighter/metrics@main:v1.0..v1.1</code>)<ul>
<li>See <a href="https://git-scm.com/docs/git-rev-list#_description"><code>git rev-list</code></a> documentation for more information about <code>commits</code> syntax</li>
</ul>
</li>
</ul>
<p>It is possible to specify repositories that are not hosted on <a href="https://github.com">github.com</a> by passing a full url instead.
In this case the repository must be accessible directly.</p>
<blockquote>
<p>ℹ️ This option bypass <a href="/source/plugins/languages/README.md#plugin_languages_skipped"><code>plugin_languages_skipped</code></a></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_analysis_timeout</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Analysis timeout</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 60)</i>
<br>
<b>default:</b> 15<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_analysis_timeout_repositories</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Analysis timeout (repositories)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 15)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 7.5<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_categories</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Displayed categories (most-used section)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> markup, programming<br>
<b>allowed values:</b><ul><li>data</li><li>markup</li><li>programming</li><li>prose</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_recent_categories</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Displayed categories (recently-used section)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> markup, programming<br>
<b>allowed values:</b><ul><li>data</li><li>markup</li><li>programming</li><li>prose</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_recent_load</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Events to load (recently-used section)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(100 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 300<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_languages_recent_days</code></h4></td>
    <td rowspan="2"><p>Indepth mode - Events maximum age (day, recently-used section)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 365)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 14<br></td>
  </tr>
</table>
<!--/options-->

## 🔎 `indepth` mode

The default algorithm uses the top languages from each repository you contributed to using GitHub GraphQL API (which is similar to the displayed languages bar on github.com). When working in collaborative projects with a lot of people, these numbers may be less representative of your actual work.

The `plugin_languages_indepth` option lets you use a more advanced algorithm for more accurate statistics.
Under the hood, it will clone your repositories, run [linguist-js](https://github.com/Nixinova/Linguist) (a JavaScript port of [GitHub linguist](https://github.com/github/linguist)) and iterate over patches matching your `commits_authoring` setting.

Since git lets you use any email and username for commits, *metrics* may not be able to detect a commit ownership if it isn't the same as your GitHub personal data. By default, it will use your GitHub username, but you can configure additional matching usernames and email addresses using `commits_authoring` option.

*Example: configuring `indepth` mode*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_indepth: yes
    commits_authoring: firstname lastname, username, username@users.noreply.github.com
```

> 💡 This feature unlocks the `lines` option in `plugin_languages_details`

> ⚠️ This feature significantly increase workflow time

> ⚠️ Since this mode iterates over **each matching commit of each repository**, it is not suited for large code base, especially those with a large amount of commits and the ones containing binaries. While `plugin_languages_analysis_timeout` and `plugin_languages_analysis_timeout_repositories` can be used to increase the default timeout for analysis, please be responsible and keep this feature disabled if it cannot work on your account to save GitHub resources and our planet 🌏

> ⚠️ Although *metrics* does not send any code to external sources, repositories are temporarily cloned on the GitHub Action runner. It is advised to keep this option disabled when working with sensitive data or company code. Use at your own risk, *metrics* and its authors **cannot** be held responsible for any resulting code leaks. Source code is available for auditing at [analyzers.mjs](/source/plugins/languages/analyzers.mjs).

> 🌐 Web instances must enable this feature in `settings.json`

Below is a summary of the process used to compute indepth statistics:

## Most used mode

1. Fetch GPG keys linked to your GitHub account
  - automatically add attached emails to `commits_authoring`
  - *web-flow* (GitHub's public key for changes made through web-ui) is also fetched
2. Import GPG keys so they can be used to verify commits later
3. Iterate through repositories
  - early break if `plugin_languages_analysis_timeout` is reached
  - skip repository if it matches `plugin_languages_skipped`
  - include repositories from `plugin_languages_indepth_custom`
    - a specific branch and commit range can be used
    - a source other than github.com can be used
4. Clone repository
  - target branch is checkout
5. List of authored commits is computed
  - using `git log --author` and `commits_authoring` to search in commit headers
  - using `git log --grep` and `commits_authoring` to search in commit body
  - ensure these are within the range specified by `plugin_languages_indepth_custom` (if applicable)
6. Process authored commits
  - early break if `plugin_languages_analysis_timeout_repositories` is reached
  - using `git verify-commit` to check authenticity against imported GPG keys
  - using `git log --patch` to extract added/deleted lines/bytes from each file
  - using [GitHub linguist](https://github.com/github/linguist) ([linguist-js](https://github.com/Nixinova/LinguistJS)) to detect language for each file
    - respect `plugin_languages_categories` option
    - if a file has since been deleted or moved, checkout on the last commit file was present and run linguist again
7. Aggregate results

## Recently used mode

1. Fetch push events linked to your account (or target repository)
  - matching `plugin_languages_recent_load` and `plugin_languages_recent_days` options
  - matching committer emails from `commits_authoring`
2. Process authored commits
  - using [GitHub linguist](https://github.com/github/linguist) ([linguist-js](https://github.com/Nixinova/LinguistJS)) to detect language for each file
    - respect `plugin_languages_recent_categories` option
    - directly pass file content rather than performing I/O and simulating a git repository
3. Aggregate results

## 📅 Recently used languages

This feature uses a similar algorithm as `indepth` mode, but uses patches from your events feed instead.
It will fetch a specified amount of recent push events and perform linguistic analysis on it.

> ⚠️ Note that *metrics* won't be able to use more events than GitHub API is able to provide

*Example: display recently used languages from 400 GitHub events from last 2 weeks*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_sections: recently-used
    plugin_languages_recent_load: 400
    plugin_languages_recent_days: 14
```

> 🌐 Web instances must enable this feature in `settings.json`

## 🥽 Controling which languages are displayed

Several options lets you customize which languages should be displayed.
It is possible to ignore completely languages or those lower than a given threshold, skip repositories, and filter by language categories.

*Example: hide HTML and CSS languages, skip lowlighter/metrics repository*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_ignored: html, css
    plugin_languages_skipped: lowlighter/metrics
```

*Example: hide languages with less than 2% usage*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_threshold: 2%
```

> 💡 The threshold feature will automatically scale remaining languages so the total percentage is always 100%. However, other stats like bytes count and lines are not affected.

When using `indepth` mode, it is possible to hide languages per category.
Supported categories are `data`, `markup`, `programming` and `prose`.

*Example: hide data and prose languages from stats*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_categories: data, prose
    plugin_languages_recent_categories: data, prose
```

## 🎨 Using custom colors

The plugin uses GitHub language colors, but it may be hard to distinguish them depending on which languages you use.
It is possible to use custom colors using `plugin_languages_colors` option.

The following syntaxes are supported:
- A predefined set from [colorsets.json](colorsets.json) *(support limited to 8 languages max)*
- `${language}:${color}` to change the color of a language *(case insensitive)*
- `${n}:${color}` to change the color of the n-th language

Both hexadecimal and [named color](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value) are supported.

*Example: using a predefined color set*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_colors: rainbow
    plugin_languages_limit: 8
```

*Example: setting JavaScript to red, the first language to blue and the second one to `#ff00aa`*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_colors: javascript:red, 0:blue, 1:#ff00aa
```

## ✍️ Using custom languages name

This plugin is limited by [GitHub linguist](https://github.com/github/linguist) capabilities, meaning that some languages may be mislabeled in some cases.

To mitigate this, it is possible to use `plugin_languages_aliases` option and provide a list of overrides using the following syntax: `${language}:${alias}` *(case insensitive)*.

*Example: display JavaScript as JS and TypeScript as TS*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_languages: yes
    plugin_languages_aliases: javascript:JS typescript:TS
```

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Most used
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.languages.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_languages: yes
  plugin_languages_ignored: >-
    html, css, tex, less, dockerfile, makefile, qmake, lex, cmake, shell,
    gnuplot
  plugin_languages_limit: 4

```
```yaml
name: Most used (with details)
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.languages.details.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_languages: yes
  plugin_languages_ignored: >-
    html, css, tex, less, dockerfile, makefile, qmake, lex, cmake, shell,
    gnuplot
  plugin_languages_details: bytes-size, percentage
  plugin_languages_limit: 4

```
```yaml
name: Recently used
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.languages.recent.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_languages: yes
  plugin_languages_ignored: >-
    html, css, tex, less, dockerfile, makefile, qmake, lex, cmake, shell,
    gnuplot
  plugin_languages_sections: recently-used
  plugin_languages_details: bytes-size, percentage
  plugin_languages_limit: 4

```
```yaml
name: Indepth analysis
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.languages.indepth.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_languages: yes
  plugin_languages_ignored: >-
    html, css, tex, less, dockerfile, makefile, qmake, lex, cmake, shell,
    gnuplot
  plugin_languages_indepth: yes
  plugin_languages_details: lines, bytes-size
  plugin_languages_limit: 4
  plugin_languages_analysis_timeout: 15

```
<!--/examples-->
````

## File: source/plugins/leetcode/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🗳️ Leetcode</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays statistics from a <a href="https://leetcode.com">LeetCode</a> account.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://leetcode.com">LeetCode</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.leetcode.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode</code></h4></td>
    <td rowspan="2"><p>Enable leetcode plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode_user</code></h4></td>
    <td rowspan="2"><p>LeetCode login</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>solved</code> will display solved problems scores</li>
<li><code>skills</code> will display solved problems tagged skills</li>
<li><code>recent</code> will display recent submissions</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> solved<br>
<b>allowed values:</b><ul><li>solved</li><li>skills</li><li>recent</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode_limit_skills</code></h4></td>
    <td rowspan="2"><p>Display limit (skills)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 10<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode_ignored_skills</code></h4></td>
    <td rowspan="2"><p>Ignored skills</p>
<p>It is possible to ignore entires categories by passing <code>fundamental</code>, <code>intermediate</code> or <code>advanced</code></p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_leetcode_limit_recent</code></h4></td>
    <td rowspan="2"><p>Display limit (recent)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 15)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: LeetCode
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.leetcode.svg
  token: NOT_NEEDED
  base: ""
  plugin_leetcode: yes
  plugin_leetcode_sections: solved, skills, recent

```
<!--/examples-->
````

## File: source/plugins/licenses/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📜 Repository licenses</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin display repository license informations like permissions, limitations and conditions along with additional stats about dependencies.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr><th>ℹ Additional notes</th><td><blockquote>
<p>⚠️ This is <strong>NOT</strong> legal advice, use at your own risk</p>
</blockquote>
<blockquote>
<p>💣 This plugin <strong>SHOULD NOT</strong> be enabled on web instances, since it allows raw command injection.
This could result in compromised server!</p>
</blockquote>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Permissions, limitations and conditions</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.licenses.svg" alt=""></img></details>
      <details open><summary>Licenses overview</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.licenses.ratio.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## 🔎 Licenses analysis

Use to `plugin_licenses_setup` command to setup project dependencies.

*Example: setup a NodeJS project using `npm ci`*
```yml
- name: Licenses and permissions
  with:
    repo: metrics
    plugin_licenses: yes
    plugin_licenses_setup: npm ci
```

Dependencies will be analyzed by [GitHub licensed](https://github.com/github/licensed) and compared against GitHub known licenses.

> ⚠️ This is **NOT** legal advice, use at your own risk

> 💣 This plugin **SHOULD NOT** be enabled on web instances, since it allows raw command injection.
> This could result in compromised server!


## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_licenses</code></h4></td>
    <td rowspan="2"><p>Enable licenses plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.cpu.overuse</i></li>
<li><i>metrics.run.tempdir</i></li>
<li><i>metrics.run.git</i></li>
<li><i>metrics.run.licensed</i></li>
<li><i>metrics.run.user.cmd</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_licenses_setup</code></h4></td>
    <td rowspan="2"><p>Setup command</p>
<blockquote>
<p>ℹ️ Depending on the project, this may not be required.
The example command is intended for NodeJs projects that use <code>npm</code> to install their dependencies.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_licenses_ratio</code></h4></td>
    <td rowspan="2"><p>Used licenses ratio</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_licenses_legal</code></h4></td>
    <td rowspan="2"><p>Permissions, limitations and conditions about used licenses</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Licenses and permissions
with:
  filename: metrics.plugin.licenses.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  template: repository
  repo: metrics
  plugin_licenses: yes
  plugin_licenses_setup: bash -c '[[ -f package.json ]] && npm ci || true'

```
```yaml
name: Licenses with open-source ratio graphs
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.licenses.ratio.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  template: repository
  repo: metrics
  plugin_licenses: yes
  plugin_licenses_setup: bash -c '[[ -f package.json ]] && npm ci || true'
  plugin_licenses_legal: no
  plugin_licenses_ratio: yes

```
<!--/examples-->
````

## File: source/plugins/lines/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>👨‍💻 Lines of code changed</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the number of lines of code added and removed across repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Repositories and diff history</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.lines.history.svg" alt=""></img></details>
      <details><summary>Compact display in base plugin</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.lines.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines</code></h4></td>
    <td rowspan="2"><p>Enable lines plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>base</code> will display the total lines added and removed in <code>base.repositories</code> section</li>
<li><code>repositories</code> will display repositories with the most lines added and removed</li>
<li><code>history</code> will display a graph displaying lines added and removed over time</li>
</ul>
<blockquote>
<p>ℹ️ <code>base</code> requires at least <a href="/source/plugins/base/README.md#base"><code>base: repositories</code></a> to be set</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> base<br>
<b>allowed values:</b><ul><li>base</li><li>repositories</li><li>history</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines_repositories_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 4<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines_history_limit</code></h4></td>
    <td rowspan="2"><p>Years to display</p>
<p>Will display the last <code>n</code> years, relative to current year</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_lines_delay</code></h4></td>
    <td rowspan="2"><p>Delay before performing a second query</p>
<p>When non-zero, will perform a second query after specified delay (in seconds).
The GitHub endpoint used may return inaccurate results on first query (these values seems to be cached on the fly),
after returning correct results upon performing another query.</p>
<p>Using this option may mitigate the occurrence of weird values.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 0<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Compact display in base plugin
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.lines.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: repositories
  plugin_lines: yes
  plugin_lines_delay: 30

```
```yaml
name: Repositories and diff history
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.lines.history.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_lines: yes
  plugin_lines_delay: 30
  plugin_lines_sections: repositories, history
  plugin_lines_repositories_limit: 2
  plugin_lines_history_limit: 1
  repositories_skipped: |
    @use.patterns
    */*
    +lowlighter/metrics

```
<!--/examples-->
````

## File: source/plugins/music/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎼 Music activity and suggestions</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin can display top and recently listened music tracks or titles from a random playlist.</p>
<p>Different music providers are supported.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with any of the supported provider.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_music_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Random tracks from a playlist</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.music.playlist.svg" alt=""></img></details>
      <details open><summary>Recently listened</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.music.recent.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

#### ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music</code></h4></td>
    <td rowspan="2"><p>Enable music plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_provider</code></h4></td>
    <td rowspan="2"><p>Music provider</p>
<ul>
<li><code>apple</code>: Apple Music</li>
<li><code>spotify</code>: Spotify</li>
<li><code>lastfm</code>: Last.fm</li>
<li><code>youtube</code>: YouTube Music</li>
</ul>
<p>This setting is optional when using <a href="/source/plugins/music/README.md#plugin_music_mode"><code>plugin_music_mode: playlist</code></a> (provider will be auto-detected from <a href="/source/plugins/music/README.md#plugin_music_playlist"><code>plugin_music_playlist</code></a> URL)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>allowed values:</b><ul><li>apple</li><li>spotify</li><li>lastfm</li><li>youtube</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_token</code></h4></td>
    <td rowspan="2"><p>Music provider token</p>
<p>Below is the expected token format for each provider:</p>
<ul>
<li><code>apple</code>: <em>(not supported)</em></li>
<li><code>spotify</code>: &quot;client_id, client_secret, refresh_token&quot;</li>
<li><code>lastfm</code>: &quot;api_key&quot;</li>
<li><code>youtube</code>: &quot;cookie&quot;</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.music.any</i></li>
</ul>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_user</code></h4></td>
    <td rowspan="2"><p>Music provider username</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_mode</code></h4></td>
    <td rowspan="2"><p>Display mode</p>
<ul>
<li><code>playlist</code>: display random tracks from an URL playlist</li>
<li><code>recent</code>: display recently listened tracks</li>
<li><code>top</code>: display top listened artists/tracks</li>
</ul>
<p>If <a href="/source/plugins/music/README.md#plugin_music_playlist"><code>plugin_music_playlist</code></a> is specified, the default value is <code>playlist</code>, else it is <code>recent</code></p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>allowed values:</b><ul><li>playlist</li><li>recent</li><li>top</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_playlist</code></h4></td>
    <td rowspan="2"><p>Playlist URL</p>
<p>It must be from an &quot;embed url&quot; (i.e. music player iframes that can be integrated in other websites)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 4<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_played_at</code></h4></td>
    <td rowspan="2"><p>Recently played - Last played timestamp</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_time_range</code></h4></td>
    <td rowspan="2"><p>Top tracks - Time range</p>
<ul>
<li><code>short</code>: 4 weeks</li>
<li><code>medium</code>: 6 months</li>
<li><code>long</code>: several years</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> short<br>
<b>allowed values:</b><ul><li>short</li><li>medium</li><li>long</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_music_top_type</code></h4></td>
    <td rowspan="2"><p>Top tracks - Display type</p>
<ul>
<li><code>tracks</code>: display track</li>
<li><code>artists</code>: display artists</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> tracks<br>
<b>allowed values:</b><ul><li>tracks</li><li>artists</li></ul></td>
  </tr>
</table>
<!--/options-->

## 🎺 Configuring music provider

Select a music provider below for additional instructions.

## 🎙️ Spotify

### 🗝️ Obtaining a token

Spotify does not have *personal tokens*, so it makes the process a bit longer because it is required to follow the [authorization workflow](https://developer.spotify.com/documentation/general/guides/authorization-guide/)... Follow the instructions below for a *TL;DR* to obtain a `refresh_token`.

Sign in to the [developer dashboard](https://developer.spotify.com/dashboard/) and create a new app.
Keep your `client_id` and `client_secret` and let this tab open for now.

![Add a redirect url](/.github/readme/imgs/plugin_music_recent_spotify_token_0.png)

Open the settings and add a new *Redirect url*. Normally it is used to setup callbacks for apps, but just put `https://localhost` instead (it is mandatory as per the [authorization guide](https://developer.spotify.com/documentation/general/guides/authorization-guide/), even if not used).

Forge the authorization url with your `client_id` and the encoded `redirect_uri` you whitelisted, and access it from your browser:

```
https://accounts.spotify.com/authorize?client_id=********&response_type=code&scope=user-read-recently-played%20user-top-read&redirect_uri=https%3A%2F%2Flocalhost
```

When prompted, authorize application.

![Authorize application](/.github/readme/imgs/plugin_music_recent_spotify_token_1.png)

Once redirected to `redirect_uri`, extract the generated authorization `code` from your url bar.

![Extract authorization code from url](/.github/readme/imgs/plugin_music_recent_spotify_token_2.png)

Go back to developer dashboard tab, and open the web console of your browser to paste the following JavaScript code, with your own `client_id`, `client_secret`, authorization `code` and `redirect_uri`.

```js
(async () => {
  console.log(await (await fetch("https://accounts.spotify.com/api/token", {
    method:"POST",
    headers:{"Content-Type":"application/x-www-form-urlencoded"},
    body:new URLSearchParams({
      grant_type:"authorization_code",
      redirect_uri:"https://localhost",
      client_id:"********",
      client_secret:"********",
      code:"********",
    })
  })).json())
})()
```

It should return a JSON response with the following content:
```json
{
  "access_token":"********",
  "expires_in": 3600,
  "scope":"user-read-recently-played user-top-read",
  "token_type":"Bearer",
  "refresh_token":"********"
}
```

Register your `client_id`, `client_secret` and `refresh_token` in secrets to finish setup.

### 🔗 Get an embed playlist url for `plugin_music_playlist`

Connect to [spotify.com](https://www.spotify.com) and select the playlist you want to share.
From `...` menu, select `Share` and `Copy embed code`.

![Copy embed code of playlist](/.github/readme/imgs/plugin_music_playlist_spotify.png)

Extract the source link from the code pasted in your clipboard:
```html
<iframe src="https://open.spotify.com/embed/playlist/********" width="" height="" frameborder="0" allowtransparency="" allow=""></iframe>
```

## 🍎 Apple Music

### 🗝️ Obtaining a token

*(Not available)*

> 😥 Unfortunately I wasn't able to find a workaround to avoid paying the $99 fee for the developer program, even using workarounds like *smart playlists*, *shortcuts* and other stuff. However if you really want this feature, you could [sponsor me](github.com/sponsors/lowlighter) and I could eventually invest in a developer account with enough money, implement it and also eventually offer service on the shared instance

### 🔗 Get an embed playlist url for `plugin_music_playlist`

Connect to [music.apple.com](https://music.apple.com/) and select the playlist you want to share.
From `...` menu, select `Share` and `Copy embed code`.

![Copy embed code of playlist](/.github/readme/imgs/plugin_music_playlist_apple.png)

Extract the source link from the code pasted in your clipboard:
```html
<iframe allow="" frameborder="" height="" style="" sandbox="" src="https://embed.music.apple.com/**/playlist/********"></iframe>
```

## ⏯️ Youtube Music

### 🗝️ Obtaining a token

Login to [YouTube Music](https://music.youtube.com) on any modern browser.

Open the developer tools (Ctrl-Shift-I) and select the “Network” tab

![Open developer tools](/.github/readme/imgs/plugin_music_recent_youtube_cookie_1.png)

Find an authenticated POST request. The simplest way is to filter by /browse using the search bar of the developer tools. If you don’t see the request, try scrolling down a bit or clicking on the library button in the top bar.

Click on the Name of any matching request. In the “Headers” tab, scroll to the “Cookie” and copy this by right-clicking on it and selecting “Copy value”.

![Copy cookie value](/.github/readme/imgs/plugin_music_recent_youtube_cookie_2.png)

### 🔗 Get an embed playlist url for `plugin_music_playlist`

Extract the *playlist* URL of the playlist you want to share.

Connect to [music.youtube.com](https://music.youtube.com) and select the playlist you want to share.

Extract the source link from the code pasted in your clipboard:
```
https://music.youtube.com/playlist?list=********
```

## 📻 Last.fm

### 🗝️ Obtaining a token

[Create an API account](https://www.last.fm/api/account/create) or [use an existing one](https://www.last.fm/api/accounts) to obtain a Last.fm API key.

### 🔗 Get an embed playlist url for `plugin_music_playlist`

*(Not available)*

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Apple Music - Random track from playlist
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.music.playlist.svg
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_playlist: https://embed.music.apple.com/fr/playlist/usr-share/pl.u-V9D7m8Etjmjd0D
  plugin_music_limit: 2

```
```yaml
name: Spotify - Random track from playlist
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.music.playlist.spotify.svg
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_playlist: https://open.spotify.com/embed/playlist/3nfA87oeJw4LFVcUDjRcqi

```
```yaml
name: Spotify - Recently listed
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.music.recent.svg
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_provider: spotify
  plugin_music_mode: recent
  plugin_music_token: ${{ secrets.SPOTIFY_TOKENS }}
  plugin_music_limit: 2

```
```yaml
name: Spotify - Top tracks
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_mode: top
  plugin_music_provider: spotify
  plugin_music_token: ${{ secrets.SPOTIFY_TOKENS }}
  plugin_music_time_range: short
  plugin_music_top_type: tracks

```
```yaml
name: Spotify - Top artists
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_mode: top
  plugin_music_provider: spotify
  plugin_music_token: ${{ secrets.SPOTIFY_TOKENS }}
  plugin_music_time_range: long
  plugin_music_top_type: artists

```
```yaml
name: Youtube Music - Random track from playlist
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  base: ""
  plugin_music: yes
  plugin_music_playlist: >-
    https://music.youtube.com/playlist?list=OLAK5uy_kU_uxp9TUOl9zVdw77xith8o9AknVwz9U

```
```yaml
name: Youtube Music - Recently listed
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  base: ""
  plugin_music_token: ${{ secrets.YOUTUBE_MUSIC_TOKENS }}
  plugin_music: yes
  plugin_music_mode: recent
  plugin_music_provider: youtube

```
```yaml
name: Last.fm  - Recently listed
uses: lowlighter/metrics@latest
with:
  token: NOT_NEEDED
  base: ""
  plugin_music_token: ${{ secrets.LASTFM_TOKEN }}
  plugin_music: yes
  plugin_music_provider: lastfm
  plugin_music_user: RJ

```
<!--/examples-->
````

## File: source/plugins/notable/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎩 Notable contributions</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays badges for notable contributions on repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Indepth analysis</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.notable.indepth.svg" alt=""></img></details>
      <details><summary>Contributions in organizations only</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.notable.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable</code></h4></td>
    <td rowspan="2"><p>Enable notable plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_filter</code></h4></td>
    <td rowspan="2"><p>Query filter</p>
<p>Based on <a href="https://docs.github.com/en/search-github/getting-started-with-searching-on-github/understanding-the-search-syntax">GitHub search syntax</a>.
Supported fields are <code>stars</code>, <code>forks</code> and <code>watchers</code></p>
<p>If <a href="/source/plugins/notable/README.md#plugin_notable_indepth"><code>plugin_notable_indepth</code></a> is enabled, <code>commits</code>, <code>commits.user</code>, <code>commits.user%</code> and <code>maintainer</code> fields are also supported.
Some repositories may not be able to reported advanced stats and in the case the default behaviour will be to bypass filtering</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_from</code></h4></td>
    <td rowspan="2"><p>Repository owner account type filter</p>
<ul>
<li><code>all</code>: no filtering</li>
<li><code>organization</code>: only organization accounts repositories</li>
<li><code>user</code>: only user accounts repositories</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> organization<br>
<b>allowed values:</b><ul><li>all</li><li>organization</li><li>user</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_repositories</code></h4></td>
    <td rowspan="2"><p>Repository name</p>
<p>Repositories hosted by user account will always have their full handle displayed</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_indepth</code></h4></td>
    <td rowspan="2"><p>Indepth mode</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.github.overuse</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_types</code></h4></td>
    <td rowspan="2"><p>Contribution types filter</p>
<p>Use a combination of below values to include repositories where:</p>
<ul>
<li><code>commit</code>: a commit on default branch was made</li>
<li><code>pull_request</code>: a pull request was opened</li>
<li><code>issue</code>: an issue was opened</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> commit<br>
<b>allowed values:</b><ul><li>commit</li><li>pull_request</li><li>issue</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_notable_self</code></h4></td>
    <td rowspan="2"><p>Include own repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## 🔎 `indepth` mode

The `plugin_notable_indepth` option collects additional stats about your contributions, such as:
- Total number of commits within a repository or organization.

For each of the above, a badge is awarded. Its color and progress depends of the associated value.

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Contributions
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.notable.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_notable: yes

```
```yaml
name: Indepth analysis
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.notable.indepth.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_notable: yes
  plugin_notable_indepth: yes
  plugin_notable_repositories: yes

```
<!--/examples-->
````

## File: source/plugins/pagespeed/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>⏱️ Google PageSpeed</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays performance statistics of a website.</p>
<p>It uses <a href="https://developers.google.com/speed/docs/insights/v5/get-started">Google&#39;s PageSpeed API</a> (same as <a href="https://web.dev">web.dev</a>), see <a href="https://web.dev/performance-scoring/">performance scoring</a> and <a href="https://googlechrome.github.io/lighthouse/scorecalc/">score calculator</a> for more informations about results.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://pagespeed.web.dev/">Google PageSpeed</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_pagespeed_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>PageSpeed scores</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.svg" alt=""></img></details>
      <details><summary>PageSpeed scores with detailed report</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.detailed.svg" alt=""></img></details>
      <details><summary>PageSpeed scores with a website screenshot</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.screenshot.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed</code></h4></td>
    <td rowspan="2"><p>Enable pagespeed plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed_token</code></h4></td>
    <td rowspan="2"><p>PageSpeed token</p>
<blockquote>
<p>⚠️ While not mandatory, it is strongly advised pass a token to avoid triggering the rate limiter. See <a href="https://developers.google.com/speed/docs/insights/v5/get-started">PageSpeed documentation</a> for more informations.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.google.pagespeed</i></li>
</ul>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed_url</code></h4></td>
    <td rowspan="2"><p>Audited website</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User attached website</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed_detailed</code></h4></td>
    <td rowspan="2"><p>Detailed results</p>
<p>The following additional stats will be displayed:</p>
<ul>
<li>First Contentful Paint</li>
<li>Speed Index</li>
<li>Largest Contentful Paint</li>
<li>Time to Interactive</li>
<li>Total Blocking Time</li>
<li>Cumulative Layout Shift</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed_screenshot</code></h4></td>
    <td rowspan="2"><p>Website screenshot</p>
<p>Significantly increase filesize</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_pagespeed_pwa</code></h4></td>
    <td rowspan="2"><p>PWA Status</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Succinct report
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.pagespeed.svg
  token: NOT_NEEDED
  base: ""
  plugin_pagespeed: yes
  plugin_pagespeed_token: ${{ secrets.PAGESPEED_TOKEN }}
  plugin_pagespeed_url: https://lecoq.io

```
```yaml
name: Detailed report
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.pagespeed.detailed.svg
  token: NOT_NEEDED
  base: ""
  plugin_pagespeed: yes
  plugin_pagespeed_detailed: yes
  plugin_pagespeed_token: ${{ secrets.PAGESPEED_TOKEN }}
  plugin_pagespeed_url: https://lecoq.io

```
```yaml
name: Screenshot
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.pagespeed.screenshot.svg
  token: NOT_NEEDED
  base: ""
  plugin_pagespeed: yes
  plugin_pagespeed_screenshot: yes
  plugin_pagespeed_token: ${{ secrets.PAGESPEED_TOKEN }}
  plugin_pagespeed_url: https://lecoq.io

```
```yaml
name: Succinct report with PWA
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.pagespeed.svg
  token: NOT_NEEDED
  base: ""
  plugin_pagespeed: yes
  plugin_pagespeed_token: ${{ secrets.PAGESPEED_TOKEN }}
  plugin_pagespeed_url: https://lecoq.io
  plugin_pagespeed_pwa: yes

```
<!--/examples-->
````

## File: source/plugins/people/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🧑‍🤝‍🧑 People</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin can display relationships with users, such as followers, sponsors, contributors, stargazers, watchers, members, etc.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Related to a user</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.people.followers.svg" alt=""></img></details>
      <details><summary>Related to a repository</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.people.repository.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people</code></h4></td>
    <td rowspan="2"><p>Enable people plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 24<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_identicons</code></h4></td>
    <td rowspan="2"><p>Force identicons pictures</p>
<p>Can be used to mask profile pictures for privacy</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_identicons_hide</code></h4></td>
    <td rowspan="2"><p>Hide identicons pictures</p>
<p>Can be used to mask users without a personal profile picture.</p>
<p>When used with <a href="/source/plugins/people/README.md#plugin_people_identicons"><code>plugin_people_identicons</code></a>, users without a personal profile picture will still be filtered out, but their picture will be replaced by an identicon instead</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_size</code></h4></td>
    <td rowspan="2"><p>Profile picture display size</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(8 ≤
𝑥
≤ 64)</i>
<br>
<b>default:</b> 28<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_types</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<p>User and organization accounts support the following values:</p>
<ul>
<li><code>followers</code></li>
<li><code>following</code>/<code>followed</code></li>
<li><code>sponsoring</code>/<code>sponsored</code></li>
<li><code>sponsors</code></li>
<li><code>members</code> (organization only)</li>
<li><code>thanks</code>(to be configured with <a href="/source/plugins/people/README.md#plugin_people_thanks"><code>plugin_people_thanks</code></a>)</li>
</ul>
<p>Repositories support the following values:</p>
<ul>
<li><code>sponsors</code> (same as owner sponsors)</li>
<li><code>contributors</code></li>
<li><code>stargazers</code></li>
<li><code>watchers</code></li>
<li><code>thanks</code>(to be configured with <a href="/source/plugins/people/README.md#plugin_people_thanks"><code>plugin_people_thanks</code></a>)</li>
</ul>
<p>Specified order is honored</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> followers, following<br>
<b>allowed values:</b><ul><li>followers</li><li>following</li><li>followed</li><li>sponsoring</li><li>members</li><li>sponsored</li><li>sponsors</li><li>contributors</li><li>stargazers</li><li>watchers</li><li>thanks</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_thanks</code></h4></td>
    <td rowspan="2"><p>Special thanks</p>
<p>Can be used to thank specific users</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_sponsors_custom</code></h4></td>
    <td rowspan="2"><p>Custom sponsors</p>
<p>This list can be used to add users from unsupported GitHub sponsors sources.
The option <a href="/source/plugins/people/README.md#plugin_people_types"><code>plugin_people_types</code></a> must contain the <code>sponsors</code> section in order for this setting to be effective</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_people_shuffle</code></h4></td>
    <td rowspan="2"><p>Shuffle data</p>
<p>Can be used to create varied outputs
This will fetch additional data (10 times <a href="/source/plugins/people/README.md#plugin_people_limit"><code>plugin_people_limit</code></a>) to ensure output is always different</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Followers
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.people.followers.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_people: yes
  plugin_people_types: followers

```
```yaml
name: Contributors and sponsors
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.people.repository.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  template: repository
  repo: metrics
  plugin_people: yes
  plugin_people_types: contributors, stargazers, watchers, sponsors

```
<!--/examples-->
````

## File: source/plugins/posts/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>✒️ Recent posts</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays recent articles from a specified and supported external source.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/markdown/README.md"><code>📒 Markdown template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Latest posts width description and cover image</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.posts.full.svg" alt=""></img></details>
      <details><summary>Latest posts</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.posts.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts</code></h4></td>
    <td rowspan="2"><p>Enable posts plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts_source</code></h4></td>
    <td rowspan="2"><p>External source</p>
<ul>
<li><code>dev.to</code>: <a href="https://dev.to">dev.to</a></li>
<li><code>hashnode</code>: <a href="https://hashnode.com">hashnode.com</a></li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>allowed values:</b><ul><li>dev.to</li><li>hashnode</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts_user</code></h4></td>
    <td rowspan="2"><p>External source username</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User login</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts_descriptions</code></h4></td>
    <td rowspan="2"><p>Posts descriptions</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts_covers</code></h4></td>
    <td rowspan="2"><p>Posts cover images</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_posts_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 30)</i>
<br>
<b>default:</b> 4<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Recent posts
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.posts.svg
  token: NOT_NEEDED
  base: ""
  plugin_posts: yes
  plugin_posts_source: dev.to

```
```yaml
name: Recent posts with descriptions and cover images
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.posts.full.svg
  token: NOT_NEEDED
  base: ""
  plugin_posts: yes
  plugin_posts_source: dev.to
  plugin_posts_limit: 2
  plugin_posts_descriptions: yes
  plugin_posts_covers: yes

```
<!--/examples-->
````

## File: source/plugins/projects/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🗂️ GitHub projects</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays progress of profile and repository projects.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>🔑 public_repo</code> <code>🔑 read:project</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.projects.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_projects</code></h4></td>
    <td rowspan="2"><p>Enable projects plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_projects_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<p>Projects defined by <a href="/source/plugins/projects/README.md#plugin_projects_repositories"><code>plugin_projects_repositories</code></a> are not affected by this option</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 4<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_projects_repositories</code></h4></td>
    <td rowspan="2"><p>Featured repositories projects</p>
<p>Use the following syntax for each project <code>:user/:repo/projects/:project_id</code></p>
<blockquote>
<p>ℹ️ <a href="https://docs.github.com/en/issues/trying-out-the-new-projects-experience/about-projects">GitHub projects (beta)</a> needs to use the same syntax as above and repository must specified repository must be linked to given project.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_projects_descriptions</code></h4></td>
    <td rowspan="2"><p>Projects descriptions</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## 🔄 Enabling progress tracking

By default, projects have progress tracking disabled.

To enable it, open the `≡ Menu` from the project page and opt-in to `Track project progress`.

![Enable "Track project progress"](/.github/readme/imgs/plugin_projects_track_progress.png)

## 👤 Use personal projects

To create a personal project, select the `Projects` tab from your profile:
![Create a new project](/.github/readme/imgs/plugin_projects_create.png)

Fill informations and set visibility to *public*:
![Configure project](/.github/readme/imgs/plugin_projects_setup.png)

## 📓 Use repositories projects

Repositories projects are created from the `Projects` tab of a repository.

To use it with this plugin, retrieve the last section of the project URL (it should match the format `:user/:repository/projects/:project_id`) and add it in the `plugin_projects_repositories`.

Be sure to tick `Track project progress` in project settings to display a progress bar.

![Add a repository project](/.github/readme/imgs/plugin_projects_repositories.png)

*Example: include a project repository*
```yml
- uses: lowlighter/metrics@latest
  with:
    plugin_projects: yes
    plugin_projects_repositories: lowlighter/metrics/projects/1
```

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Project from a repository
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.projects.svg
  token: ${{ secrets.METRICS_TOKEN_WITH_SCOPES }}
  base: ""
  plugin_projects: yes
  plugin_projects_repositories: lowlighter/metrics/projects/1
  plugin_projects_descriptions: yes

```
<!--/examples-->
````

## File: source/plugins/reactions/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🎭 Comment reactions</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays overall user reactions on recent issues, comments and discussions.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.reactions.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions</code></h4></td>
    <td rowspan="2"><p>Enable reactions plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (issues and pull requests comments)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 200<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_limit_issues</code></h4></td>
    <td rowspan="2"><p>Display limit (issues and pull requests, first comment)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 100<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_limit_discussions</code></h4></td>
    <td rowspan="2"><p>Display limit (discussions, first comment)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 100<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_limit_discussions_comments</code></h4></td>
    <td rowspan="2"><p>Display limit (discussions comments)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 1000)</i>
<br>
<b>default:</b> 100<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_days</code></h4></td>
    <td rowspan="2"><p>Comments maximum age</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_display</code></h4></td>
    <td rowspan="2"><p>Display mode</p>
<ul>
<li><code>absolute</code>: scale percentages using total reactions count</li>
<li><code>relative</code>: scale percentages using highest reaction count</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> absolute<br>
<b>allowed values:</b><ul><li>absolute</li><li>relative</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_details</code></h4></td>
    <td rowspan="2"><p>Additional details</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>allowed values:</b><ul><li>count</li><li>percentage</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_reactions_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored users</p>
<p>Can be used to ignore bots activity</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>users_ignored</code><br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Comment reactions
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.reactions.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_reactions: yes
  plugin_reactions_limit: 100
  plugin_reactions_details: percentage

```
<!--/examples-->
````

## File: source/plugins/repositories/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📓 Featured repositories</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays a list of chosen featured repositories.</p>
<p>Since it is possible to <a href="https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/pinning-items-to-your-profile">pin repositories</a> on GitHub, this plugin is mostly intended for external usage.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr><th>ℹ Additional notes</th><td><blockquote>
<p>⚠️ Due to limitations of using SVG images inside <code>&lt;img&gt;</code> tags, clicking on a repository card will not redirect to repository page.</p>
</blockquote>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Featured</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.repositories.svg" alt=""></img></details>
      <details><summary>Pinned</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.repositories.pinned.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories</code></h4></td>
    <td rowspan="2"><p>Enable repositories plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_featured</code></h4></td>
    <td rowspan="2"><p>Featured repositories</p>
<p>Current <a href="/source/plugins/core/README.md#user"><code>user</code></a> will be used when no owner is specified</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_pinned</code></h4></td>
    <td rowspan="2"><p>Pinned repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 6)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_starred</code></h4></td>
    <td rowspan="2"><p>Featured most starred repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_random</code></h4></td>
    <td rowspan="2"><p>Featured random repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_order</code></h4></td>
    <td rowspan="2"><p>Featured repositories display order</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<br>
<b>default:</b> featured, pinned, starred, random<br>
<b>allowed values:</b><ul><li>featured</li><li>pinned</li><li>starred</li><li>random</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_forks</code></h4></td>
    <td rowspan="2"><p>Include repositories forks</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_repositories_affiliations</code></h4></td>
    <td rowspan="2"><p>Repositories affiliations</p>
<ul>
<li><code>owner</code>: owned repositories</li>
<li><code>collaborator</code>: repositories with push access</li>
<li><code>organization_member</code>: repositories from an organization where user is a member</li>
</ul>
<p>Set to <code>&quot;&quot;</code> to disable and fetch all repositories related to given account.</p>
<p>This option changes which repositories will be fetched by <a href="/source/plugins/projects/README.md#plugin_repositories_starred"><code>plugin_repositories_starred</code></a> and <a href="/source/plugins/projects/README.md#plugin_repositories_random"><code>plugin_repositories_random</code></a> options</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> owner<br>
<b>allowed values:</b><ul><li>owner</li><li>collaborator</li><li>organization_member</li></ul></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Featured repositories
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.repositories.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_repositories: yes
  plugin_repositories_featured: lowlighter/metrics

```
```yaml
name: Pinned repositories
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.repositories.pinned.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_repositories: yes
  plugin_repositories_pinned: 2

```
<!--/examples-->
````

## File: source/plugins/rss/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🗼 Rss feed</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays news from a given RSS feed.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/markdown/README.md"><code>📒 Markdown template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.rss.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_rss</code></h4></td>
    <td rowspan="2"><p>Enable rss plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_rss_source</code></h4></td>
    <td rowspan="2"><p>RSS feed source</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_rss_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 30)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 4<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: News from hackernews
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.rss.svg
  token: NOT_NEEDED
  base: ""
  plugin_rss: yes
  plugin_rss_source: https://news.ycombinator.com/rss
  plugin_rss_limit: 4

```
<!--/examples-->
````

## File: source/plugins/skyline/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🌇 GitHub Skyline</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the 3D commits calendar from <a href="https://skyline.github.com/">skyline.github.com</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr><th>ℹ Additional notes</th><td><blockquote>
<p>⚠️ This plugin significantly increase file size, consider using it as standalone.</p>
</blockquote>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>GitHub Skyline</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.skyline.svg" alt=""></img></details>
      <details><summary>GitHub City</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.skyline.city.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline</code></h4></td>
    <td rowspan="2"><p>Enable skyline plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.cpu.overuse</i></li>
<li><i>metrics.npm.optional.gifencoder</i></li>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline_year</code></h4></td>
    <td rowspan="2"><p>Displayed year</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(2008 ≤
𝑥)</i>
<br>
<b>default:</b> current-year<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline_frames</code></h4></td>
    <td rowspan="2"><p>Frames count</p>
<p>Use 120 for a full-loop and 60 for a half-loop.
A higher number of frames will increase file size.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 120)</i>
<br>
<b>default:</b> 60<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline_quality</code></h4></td>
    <td rowspan="2"><p>Image quality</p>
<p>A higher image quality will increase file size.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0.1 ≤
𝑥
≤ 1)</i>
<br>
<b>default:</b> 0.5<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline_compatibility</code></h4></td>
    <td rowspan="2"><p>Compatibility mode</p>
<p>This uses CSS animations rather than embedded GIF to support a wider range of browsers, like Firefox and Safari.
Using this mode significantly increase file size as each frame is encoded separately</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_skyline_settings</code></h4></td>
    <td rowspan="2"><p>Advanced settings</p>
<p>Can be configured to use alternate skyline websites different from <a href="https://skyline.github.com">skyline.github.com</a>, such as <a href="https://github.com/honzaap/GithubCity">honzaap&#39;s GitHub City</a>.</p>
<ul>
<li><code>url</code>: Target URL (mandatory)</li>
<li><code>ready</code>: Readiness condition (A JS function that returns a boolean)</li>
<li><code>wait</code>: Time to wait after readiness condition is met (in seconds)</li>
<li><code>hide</code>: HTML elements to hide (A CSS selector)</li>
</ul>
<p>For <code>url</code> and <code>ready</code> options, <code>${login}</code> and <code>${year}</code> will be respectively templated to user&#39;s login and specified year</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.user.js</i></li>
</ul>
<b>type:</b> <code>json</code>
<br>
<b>default:</b> <details><summary>→ Click to expand</summary><pre language="json"><code>{
  "url": "https://skyline.github.com/${login}/${year}",
  "ready": "[...document.querySelectorAll('span')].map(span => span.innerText).includes('Share on Twitter')",
  "wait": 1,
  "hide": "button, footer, a"
}
</code></pre></details><br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: GitHub Skyline
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.skyline.svg
  token: NOT_NEEDED
  base: ""
  plugin_skyline: yes
  plugin_skyline_year: 2020
  plugin_skyline_frames: 6
  plugin_skyline_quality: 1

```
```yaml
name: GitHub City
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.skyline.city.svg
  token: NOT_NEEDED
  base: ""
  plugin_skyline: yes
  plugin_skyline_year: 2020
  plugin_skyline_frames: 6
  plugin_skyline_quality: 1
  plugin_skyline_settings: |
    {
      "url": "https://honzaap.github.io/GithubCity?name=${login}&year=${year}",
      "ready": "[...document.querySelectorAll('.display-info span')].map(span => span.innerText).includes('${login}')",
      "wait": 4,
      "hide": ".github-corner, .footer-link, .buttons-options, .mobile-rotate, .display-info span:first-child"
    }

```
<!--/examples-->
````

## File: source/plugins/sponsors/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💕 GitHub Sponsors</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays sponsors and introduction text from <a href="https://github.com/sponsors/">GitHub sponsors</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 read:user</code> <code>🔑 read:org</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>GitHub sponsors card</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsors.svg" alt=""></img></details>
      <details><summary>GitHub sponsors full introduction</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsors.full.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsors</code></h4></td>
    <td rowspan="2"><p>Enable sponsors plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsors_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>goal</code>: display GitHub active goal</li>
<li><code>about</code>: display GitHub sponsors introduction</li>
<li><code>list</code>: display GitHub sponsors list</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> goal, list, about<br>
<b>allowed values:</b><ul><li>goal</li><li>about</li><li>list</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsors_past</code></h4></td>
    <td rowspan="2"><p>Past sponsorships</p>
<p>A <a href="/source/plugins/core/README.md#token"><code>token</code></a> from target <a href="/source/plugins/core/README.md#user"><code>user</code></a> must be specified to use this feature, as past sponsorships are gathered from sponsors activity which is private data.</p>
<blockquote>
<p>⚠️ Past sponsorships does not respect sponsors privacy because of current GitHub API limitations. This may be fixed in a future release.</p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsors_size</code></h4></td>
    <td rowspan="2"><p>Profile picture display size</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(8 ≤
𝑥
≤ 64)</i>
<br>
<b>default:</b> 24<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsors_title</code></h4></td>
    <td rowspan="2"><p>Title caption</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> Sponsor Me!<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Sponsors goal
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.sponsors.svg
  token: ${{ secrets.METRICS_TOKEN_PERSONAL }}
  base: ""
  plugin_sponsors: yes
  plugin_sponsors_sections: goal, list
  plugin_sponsors_past: yes

```
```yaml
name: Sponsors introduction
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.sponsors.full.svg
  token: ${{ secrets.METRICS_TOKEN_WITH_SCOPES }}
  base: ""
  plugin_sponsors: yes

```
<!--/examples-->
````

## File: source/plugins/sponsorships/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💝 GitHub Sponsorships</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays sponsorships funded through <a href="https://github.com/sponsors/">GitHub sponsors</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🔑 read:user</code> <code>🔑 read:org</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsorships.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsorships</code></h4></td>
    <td rowspan="2"><p>Enable sponsorships plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsorships_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>amount</code>: display total amount sponsored</li>
<li><code>sponsorships</code>: display GitHub sponsorships</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> amount, sponsorships<br>
<b>allowed values:</b><ul><li>amount</li><li>sponsorships</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_sponsorships_size</code></h4></td>
    <td rowspan="2"><p>Profile picture display size</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(8 ≤
𝑥
≤ 64)</i>
<br>
<b>default:</b> 24<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: 💝 GitHub Sponsorships
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.sponsorships.svg
  token: ${{ secrets.METRICS_TOKEN_PERSONAL }}
  base: ""
  plugin_sponsorships: yes

```
<!--/examples-->
````

## File: source/plugins/stackoverflow/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🗨️ Stack Overflow</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays stats, questions and answer from <a href="https://stackoverflow.com/">Stack Overflow</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://stackoverflow.com/">Stack Overflow</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stackoverflow.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow</code></h4></td>
    <td rowspan="2"><p>Enable stackoverflow plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow_user</code></h4></td>
    <td rowspan="2"><p>Stackoverflow user id</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>number</code>
<br>
<b>default:</b> 0<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>answers-top</code>: display most popular answers</li>
<li><code>answers-recent</code>: display recent answers</li>
<li><code>questions-top</code>: display most popular questions</li>
<li><code>questions-recent</code>: display recent questions</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> answers-top, questions-recent<br>
<b>allowed values:</b><ul><li>answers-top</li><li>answers-recent</li><li>questions-top</li><li>questions-recent</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (entries per section)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 30)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow_lines</code></h4></td>
    <td rowspan="2"><p>Display limit (lines per questions and answers)</p>
<p>Code snippets count as a single line and must be configured with <a href="/source/plugins/stackoverflow/README.md#plugin_stackoverflow_lines_snippet"><code>plugin_stackoverflow_lines_snippet</code></a> instead</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 4<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stackoverflow_lines_snippet</code></h4></td>
    <td rowspan="2"><p>Display limit (lines per code snippets)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 2<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Top answers from stackoverflow
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stackoverflow.svg
  token: NOT_NEEDED
  base: ""
  plugin_stackoverflow: yes
  plugin_stackoverflow_user: 1
  plugin_stackoverflow_sections: answers-top
  plugin_stackoverflow_limit: 2

```
<!--/examples-->
````

## File: source/plugins/stargazers/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>✨ Stargazers</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays stargazers evolution across affiliated repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>🗝️ plugin_stargazers_worldmap_token</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Classic charts</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.svg" alt=""></img></details>
      <details><summary>Graph charts</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.graph.svg" alt=""></img></details>
      <details open><summary>Worldmap</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.worldmap.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## 🗝️ Obtaining a Google Maps API token

Some features like `plugin_stagazers_worldmap` require a Google Geocoding API token.
Follow instructions from their [documentation](https://developers.google.com/maps/documentation/geocoding/get-api-key) for more informations.

> 💳 A billing account is required to get a token. However a recurring [monthly credit](https://developers.google.com/maps/billing-credits#monthly) is offered which means you should not be charged if you don't exceed the free quota.
>
> It is advised to set the quota limit at 1200 requests per day
>
> Use at your own risk, *metrics* and its authors cannot be held responsible for anything charged.

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers</code></h4></td>
    <td rowspan="2"><p>Enable stargazers plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_days</code></h4></td>
    <td rowspan="2"><p>Time range</p>
<p>If set to <code>0</code> the account registration date will be used.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> see description</br>
<b>default:</b> 14<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_charts</code></h4></td>
    <td rowspan="2"><p>Charts</p>
<p>It includes total number of stargazers evolution, along with the number of new stars per day over the last two weeks.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_charts_type</code></h4></td>
    <td rowspan="2"><p>Charts display type</p>
<ul>
<li><code>classic</code>: <code>&lt;div&gt;</code> based charts, simple and lightweight</li>
<li><code>graph</code>: <code>&lt;svg&gt;</code> based charts, smooth</li>
</ul>
<blockquote>
<p>⚠️ <code>chartist</code> option has been deprecated and is now equivalent to <code>graph</code></p>
</blockquote>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.npm.optional.d3</i></li>
</ul>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> classic<br>
<b>allowed values:</b><ul><li>classic</li><li>graph</li><li>chartist</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_worldmap</code></h4></td>
    <td rowspan="2"><p>Stargazers worldmap</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.google.maps</i></li>
<li><i>metrics.npm.optional.d3</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_worldmap_token</code></h4></td>
    <td rowspan="2"><p>Stargazers worldmap token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stargazers_worldmap_sample</code></h4></td>
    <td rowspan="2"><p>Stargazers worldmap sample</p>
<p>Use this setting to randomly sample and limit your stargazers.
Helps to avoid consuming too much Google Geocoding API requests while still being representative.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 0<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Using classic charts
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stargazers.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_stargazers: yes

```
```yaml
name: Using graph charts
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stargazers.graph.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_stargazers: yes
  plugin_stargazers_charts_type: graph

```
```yaml
name: With worldmap
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stargazers.worldmap.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_stargazers: yes
  plugin_stargazers_charts: no
  plugin_stargazers_worldmap: yes
  plugin_stargazers_worldmap_token: ${{ secrets.GOOGLE_MAP_TOKEN }}
  plugin_stargazers_worldmap_sample: 200

```
<!--/examples-->
````

## File: source/plugins/starlists/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💫 Star lists</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays star lists.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Repositories from star lists</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.starlists.svg" alt=""></img></details>
      <details open><summary>Languages from star lists</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.starlists.languages.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists</code></h4></td>
    <td rowspan="2"><p>Enable starlists plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (star lists)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_limit_repositories</code></h4></td>
    <td rowspan="2"><p>Display limit (repositories per star list)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_languages</code></h4></td>
    <td rowspan="2"><p>Star lists languages statistics</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_limit_languages</code></h4></td>
    <td rowspan="2"><p>Display limit (languages per star list)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 8<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_languages_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored languages in star lists</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_languages_aliases</code></h4></td>
    <td rowspan="2"><p>Custom languages names in star lists</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_shuffle_repositories</code></h4></td>
    <td rowspan="2"><p>Shuffle data</p>
<p>Can be used to create varied outputs</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> yes<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_ignored</code></h4></td>
    <td rowspan="2"><p>Skipped star lists</p>
<p>Case and emojis insensitive</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_starlists_only</code></h4></td>
    <td rowspan="2"><p>Showcased star lists</p>
<p>Case and emojis insensitive.</p>
<p>Equivalent to <a href="/source/plugins/starlists/README.md#plugin_starlists_ignored"><code>plugin_starlists_ignored</code></a> with all star lists except the ones listed in this option</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Featured star list
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.starlists.svg
  token: NOT_NEEDED
  base: ""
  plugin_starlists: yes
  plugin_starlists_limit_repositories: 2
  plugin_starlists_only: TC39

```
```yaml
name: Featured star list languages
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.starlists.languages.svg
  token: NOT_NEEDED
  base: ""
  plugin_starlists: yes
  plugin_starlists_languages: yes
  plugin_starlists_limit_languages: 8
  plugin_starlists_limit_repositories: 0
  plugin_starlists_only: Awesome

```
<!--/examples-->
````

## File: source/plugins/stars/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🌟 Recently starred repositories</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays recently starred repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🔑 (scopeless)</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code> <code>repo (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stars.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stars</code></h4></td>
    <td rowspan="2"><p>Enable stars plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_stars_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 100)</i>
<br>
<b>default:</b> 4<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Recently starred
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.stars.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: ""
  plugin_stars: yes
  plugin_stars_limit: 3

```
<!--/examples-->
````

## File: source/plugins/steam/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🕹️ Steam</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin can display your player profile and played games from your Steam account.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://store.steampowered.com">Steam</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_steam_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Recently played games</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.steam.svg" alt=""></img></details>
      <details><summary>Profile and detailed game history</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.steam.full.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam</code></h4></td>
    <td rowspan="2"><p>Enable steam plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_token</code></h4></td>
    <td rowspan="2"><p>Steam token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.steam</i></li>
</ul>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>player</code>: display profile</li>
<li><code>most-played</code>: display most played games</li>
<li><code>recently-played</code>: display recently played games</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br>
<b>default:</b> player, most-played, recently-played<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_user</code></h4></td>
    <td rowspan="2"><p>Steam user id</p>
<p>This can be found on your Steam user account details</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_games_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored games</p>
<p>Use App id as they are referenced in Steam catalog</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_games_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (Most played games)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_recent_games_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (Recently played games)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 1<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_achievements_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (Games achievements)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_steam_playtime_threshold</code></h4></td>
    <td rowspan="2"><p>Display threshold (Game playtime in hours)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a *Steam Web API* token

Go to [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey) to obtain a Steam Web API token:

![Token](/.github/readme/imgs/plugin_steam_webtoken.png)

To retrieve your Steam ID, access your user account on [store.steampowered.com/account](https://store.steampowered.com/account) and copy the identifier located behind the header:

![User ID](/.github/readme/imgs/plugin_steam_userid.png)

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Recently played games
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.steam.svg
  token: NOT_NEEDED
  base: ""
  plugin_steam_token: ${{ secrets.STEAM_TOKEN }}
  plugin_steam: yes
  plugin_steam_user: "0"
  plugin_steam_sections: recently-played
  plugin_steam_achievements_limit: 0

```
```yaml
name: Profile and detailed game history
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.steam.full.svg
  token: NOT_NEEDED
  base: ""
  plugin_steam_token: ${{ secrets.STEAM_TOKEN }}
  plugin_steam: yes
  plugin_steam_user: "0"

```
<!--/examples-->
````

## File: source/plugins/support/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>💭 GitHub Community Support</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays statistics from a <a href="https://github.community/">GitHub Support Community</a> account.</p>
</td></tr>
  <tr><th>⚠️ Deprecated</th><td><p>GitHub Support Community has been moved to <a href="https://github.blog/2022-07-26-launching-github-community-powered-by-github-discussions">GitHub Discussions</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.support.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_support</code></h4></td>
    <td rowspan="2"><p>Enable support plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: GitHub Community Support
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.support.svg
  token: NOT_NEEDED
  base: ""
  plugin_support: yes

```
<!--/examples-->
````

## File: source/plugins/topics/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>📌 Starred topics</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays <a href="https://github.com/stars?filter=topics">starred topics</a>.</p>
<p>Check out <a href="https://github.com/topics">GitHub topics</a> to search interesting topics.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/markdown/README.md"><code>📒 Markdown template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><i>No tokens are required for this plugin</i></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>With icons</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.topics.icons.svg" alt=""></img></details>
      <details open><summary>With labels</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.topics.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_topics</code></h4></td>
    <td rowspan="2"><p>Enable topics plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.run.puppeteer.scrapping</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_topics_mode</code></h4></td>
    <td rowspan="2"><p>Display mode</p>
<ul>
<li><code>labels</code>: display labels</li>
<li><code>icons</code>: display icons <em>(topics without icons will not be displayed)</em></li>
<li><code>starred</code>: alias for <code>labels</code></li>
<li><code>mastered</code>: alias for <code>icons</code></li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> starred<br>
<b>allowed values:</b><ul><li>labels</li><li>icons</li><li>starred</li><li>mastered</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_topics_sort</code></h4></td>
    <td rowspan="2"><p>Sorting method</p>
<ul>
<li><code>stars</code>: sort by most stars</li>
<li><code>activity</code>: sort by recent activity</li>
<li><code>starred</code>: sort by starred date</li>
<li><code>random</code>: sort randomly</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> stars<br>
<b>allowed values:</b><ul><li>stars</li><li>activity</li><li>starred</li><li>random</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_topics_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥
≤ 20)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 15<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Labels
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.topics.svg
  token: NOT_NEEDED
  base: ""
  plugin_topics: yes
  plugin_topics_limit: 12

```
```yaml
name: Icons
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.topics.icons.svg
  token: NOT_NEEDED
  base: ""
  plugin_topics: yes
  plugin_topics_limit: 0
  plugin_topics_mode: icons

```
<!--/examples-->
````

## File: source/plugins/traffic/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🧮 Repositories traffic</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the number of page views across affiliated repositories.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://github.com">GitHub</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/repository/README.md"><code>📘 Repository template</code></a> <a href="/source/templates/terminal/README.md"><code>📙 Terminal template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code> <code>📓 Repositories</code></td>
  </tr>
  <tr>
    <td><code>🔑 repo</code> <code>read:org (optional)</code> <code>read:user (optional)</code> <code>read:packages (optional)</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.traffic.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_traffic</code></h4></td>
    <td rowspan="2"><p>Enable traffic plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_traffic_skipped</code></h4></td>
    <td rowspan="2"><p>Skipped repositories</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏩ Inherits <code>repositories_skipped</code><br>
<b>type:</b> <code>array</code>
<i>(newline-separated)</i>
<br></td>
  </tr>
</table>
<!--/options-->

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Repositories traffic
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.traffic.svg
  token: ${{ secrets.METRICS_TOKEN }}
  base: repositories
  plugin_traffic: yes

```
<!--/examples-->
````

## File: source/plugins/tweets/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>🐤 Latest tweets</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays the latest tweets from a <a href="https://twitter.com">Twitter</a> account.</p>
</td></tr>
  <tr><th>⚠️ Deprecated</th><td><p>As <a href="https://twitter.com">Twitter</a> removed the ability to fetch tweets from their free API as part of their new <a href="https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api">pricing policy</a>, this plugin is no longer maintained.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://twitter.com">Twitter</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a> <a href="/source/templates/markdown/README.md"><code>📒 Markdown template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code> <code>👥 Organizations</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_tweets_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <details open><summary>Latest tweets with attachments</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.tweets.attachments.svg" alt=""></img></details>
      <details><summary>Latest tweets</summary><img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.tweets.svg" alt=""></img></details>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_tweets</code></h4></td>
    <td rowspan="2"><p>Enable tweets plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🌐 Web instances must configure <code>settings.json</code>:
<ul>
<li><i>metrics.api.twitter.tweets</i></li>
</ul>
<b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_tweets_token</code></h4></td>
    <td rowspan="2"><p>Twitter API token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_tweets_user</code></h4></td>
    <td rowspan="2"><p>Twitter username</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> <code>→ User attached twitter</code><br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_tweets_attachments</code></h4></td>
    <td rowspan="2"><p>Tweets attachments</p>
<p>Can be used to display linked images, video thumbnails, etc.</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_tweets_limit</code></h4></td>
    <td rowspan="2"><p>Display limit</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(1 ≤
𝑥
≤ 10)</i>
<br>
<b>default:</b> 2<br></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a Twitter token

To get a Twitter token, it is required to apply to the [developer program](https://apps.twitter.com).
It's a bit tedious, but requests seems to be approved quite quickly.

Create an app from the [developer dashboard](https://developer.twitter.com/en/portal/dashboard) and register your bearer token in repository secrets.

![Twitter token](/.github/readme/imgs/plugin_tweets_secrets.png)

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: Latest tweets
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.tweets.svg
  token: NOT_NEEDED
  base: ""
  plugin_tweets: yes
  plugin_tweets_token: ${{ secrets.TWITTER_TOKEN }}
  plugin_tweets_user: github

```
```yaml
name: Latest tweets including attachments
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.tweets.attachments.svg
  token: NOT_NEEDED
  base: ""
  plugin_tweets: yes
  plugin_tweets_token: ${{ secrets.TWITTER_TOKEN }}
  plugin_tweets_attachments: yes
  plugin_tweets_user: github
  plugin_tweets_limit: 1

```
<!--/examples-->
````

## File: source/plugins/wakatime/README.md
````markdown
<!--header-->
<table>
  <tr><td colspan="2"><a href="/README.md#-plugins">← Back to plugins index</a></td></tr>
  <tr><th colspan="2"><h3>⏰ WakaTime</h3></th></tr>
  <tr><td colspan="2" align="center"><p>This plugin displays statistics from a <a href="https://wakatime.com">WakaTime</a> account.</p>
<p>It is also compatible with self-hosted instances from <a href="https://github.com/muety/wakapi">wakapi</a>.</p>
</td></tr>
  <tr><th>⚠️ Disclaimer</th><td><p>This plugin is not affiliated, associated, authorized, endorsed by, or in any way officially connected with <a href="https://wakatime.com">WakaTime</a>.
All product and company names are trademarks™ or registered® trademarks of their respective holders.</p>
</td></tr>
  <tr>
    <th rowspan="3">Supported features<br><sub><a href="metadata.yml">→ Full specification</a></sub></th>
    <td><a href="/source/templates/classic/README.md"><code>📗 Classic template</code></a></td>
  </tr>
  <tr>
    <td><code>👤 Users</code></td>
  </tr>
  <tr>
    <td><code>🗝️ plugin_wakatime_token</code></td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <img src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.wakatime.svg" alt=""></img>
      <img width="900" height="1" alt="">
    </td>
  </tr>
</table>
<!--/header-->

## ➡️ Available options

<!--options-->
<table>
  <tr>
    <td align="center" nowrap="nowrap">Option</i></td><td align="center" nowrap="nowrap">Description</td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime</code></h4></td>
    <td rowspan="2"><p>Enable wakatime plugin</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_token</code></h4></td>
    <td rowspan="2"><p>WakaTime API token</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">🔐 Token<br>
<b>type:</b> <code>token</code>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_url</code></h4></td>
    <td rowspan="2"><p>WakaTime URL</p>
<p>Can be used to specify a <a href="https://github.com/muety/wakapi">wakapi</a> instance</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> https://wakatime.com<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_user</code></h4></td>
    <td rowspan="2"><p>WakaTime username</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap">⏯️ Cannot be preset<br>
<b>type:</b> <code>string</code>
<br>
<b>default:</b> current<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_sections</code></h4></td>
    <td rowspan="2"><p>Displayed sections</p>
<ul>
<li><code>time</code>: show total coding time and daily average</li>
<li><code>projects</code>: show most time spent project</li>
<li><code>projects-graphs</code>: show most time spent projects graphs</li>
<li><code>languages</code>: show most used language</li>
<li><code>languages-graphs</code>: show languages graphs</li>
<li><code>editors</code>: show most used code editor</li>
<li><code>editors-graphs</code>: show code editors graphs</li>
<li><code>os</code>: show most used operating system</li>
<li><code>os-graphs</code>: show operating systems graphs</li>
</ul>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<br>
<b>default:</b> time, projects, projects-graphs, languages, languages-graphs, editors, os<br>
<b>allowed values:</b><ul><li>time</li><li>projects</li><li>projects-graphs</li><li>languages</li><li>languages-graphs</li><li>editors</li><li>editors-graphs</li><li>os</li><li>os-graphs</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_days</code></h4></td>
    <td rowspan="2"><p>Time range</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> 7<br>
<b>allowed values:</b><ul><li>7</li><li>30</li><li>180</li><li>365</li></ul></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_limit</code></h4></td>
    <td rowspan="2"><p>Display limit (entries per graph)</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>number</code>
<i>(0 ≤
𝑥)</i>
<br>
<b>zero behaviour:</b> disable</br>
<b>default:</b> 5<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_languages_other</code></h4></td>
    <td rowspan="2"><p>Other languages</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>boolean</code>
<br>
<b>default:</b> no<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_languages_ignored</code></h4></td>
    <td rowspan="2"><p>Ignored languages</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>array</code>
<i>(comma-separated)</i>
<br></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><h4><code>plugin_wakatime_repositories_visibility</code></h4></td>
    <td rowspan="2"><p>Repositories visibility</p>
<p>Can be used to toggle private activity visibility</p>
<img width="900" height="1" alt=""></td>
  </tr>
  <tr>
    <td nowrap="nowrap"><b>type:</b> <code>string</code>
<br>
<b>default:</b> all<br>
<b>allowed values:</b><ul><li>public</li><li>all</li></ul></td>
  </tr>
</table>
<!--/options-->

## 🗝️ Obtaining a WakaTime token

Create a [WakaTime account](https://wakatime.com) and retrieve API key in [Account settings](https://wakatime.com/settings/account).

![WakaTime API token](/.github/readme/imgs/plugin_wakatime_token.png)

Then setup [WakaTime plugins](https://wakatime.com/plugins) to be ready to go!

## ℹ️ Examples workflows

<!--examples-->
```yaml
name: WakaTime
uses: lowlighter/metrics@latest
with:
  filename: metrics.plugin.wakatime.svg
  token: NOT_NEEDED
  base: ""
  plugin_wakatime: yes
  plugin_wakatime_sections: time, projects, projects-graphs, languages, languages-graphs, editors, os
  plugin_wakatime_token: ${{ secrets.WAKATIME_TOKEN }}

```
<!--/examples-->
````

## File: source/plugins/README.md
````markdown
## 🧩 Plugins

Plugins provide additional content and lets you customize rendered metrics.

**📦 Maintained by core team**

* **Core plugins**
  * [🗃️ Base content <sub>`base`</sub>](/source/plugins/base/README.md)
  * [🧱 Core <sub>`core`</sub>](/source/plugins/core/README.md)
* **GitHub plugins**
  * [🏆 Achievements <sub>`achievements`</sub>](/source/plugins/achievements/README.md)
  * [📰 Recent activity <sub>`activity`</sub>](/source/plugins/activity/README.md)
  * [📆 Commit calendar <sub>`calendar`</sub>](/source/plugins/calendar/README.md)
  * [♐ Random code snippet <sub>`code`</sub>](/source/plugins/code/README.md)
  * [🏅 Repository contributors <sub>`contributors`</sub>](/source/plugins/contributors/README.md)
  * [💬 Discussions <sub>`discussions`</sub>](/source/plugins/discussions/README.md)
  * [🎟️ Follow-up of issues and pull requests <sub>`followup`</sub>](/source/plugins/followup/README.md)
  * [🎫 Gists <sub>`gists`</sub>](/source/plugins/gists/README.md)
  * [💡 Coding habits and activity <sub>`habits`</sub>](/source/plugins/habits/README.md)
  * [🙋 Introduction <sub>`introduction`</sub>](/source/plugins/introduction/README.md)
  * [📅 Isometric commit calendar <sub>`isocalendar`</sub>](/source/plugins/isocalendar/README.md)
  * [🈷️ Languages activity <sub>`languages`</sub>](/source/plugins/languages/README.md)
  * [📜 Repository licenses <sub>`licenses`</sub>](/source/plugins/licenses/README.md)
  * [👨‍💻 Lines of code changed <sub>`lines`</sub>](/source/plugins/lines/README.md)
  * [🎩 Notable contributions <sub>`notable`</sub>](/source/plugins/notable/README.md)
  * [🧑‍🤝‍🧑 People <sub>`people`</sub>](/source/plugins/people/README.md)
  * [🗂️ GitHub projects <sub>`projects`</sub>](/source/plugins/projects/README.md)
  * [🎭 Comment reactions <sub>`reactions`</sub>](/source/plugins/reactions/README.md)
  * [📓 Featured repositories <sub>`repositories`</sub>](/source/plugins/repositories/README.md)
  * [🌇 GitHub Skyline <sub>`skyline`</sub>](/source/plugins/skyline/README.md)
  * [💕 GitHub Sponsors <sub>`sponsors`</sub>](/source/plugins/sponsors/README.md)
  * [💝 GitHub Sponsorships <sub>`sponsorships`</sub>](/source/plugins/sponsorships/README.md)
  * [✨ Stargazers <sub>`stargazers`</sub>](/source/plugins/stargazers/README.md)
  * [💫 Star lists <sub>`starlists`</sub>](/source/plugins/starlists/README.md)
  * [🌟 Recently starred repositories <sub>`stars`</sub>](/source/plugins/stars/README.md)
  * [💭 GitHub Community Support <sub>`support`</sub>](/source/plugins/support/README.md) <sub>`⚠️ deprecated`</sub>
  * [📌 Starred topics <sub>`topics`</sub>](/source/plugins/topics/README.md)
  * [🧮 Repositories traffic <sub>`traffic`</sub>](/source/plugins/traffic/README.md)
* **Social plugins**
  * [🌸 Anilist watch list and reading list <sub>`anilist`</sub>](/source/plugins/anilist/README.md)
  * [🗳️ Leetcode <sub>`leetcode`</sub>](/source/plugins/leetcode/README.md)
  * [🎼 Music activity and suggestions <sub>`music`</sub>](/source/plugins/music/README.md)
  * [⏱️ Google PageSpeed <sub>`pagespeed`</sub>](/source/plugins/pagespeed/README.md)
  * [✒️ Recent posts <sub>`posts`</sub>](/source/plugins/posts/README.md)
  * [🗼 Rss feed <sub>`rss`</sub>](/source/plugins/rss/README.md)
  * [🗨️ Stack Overflow <sub>`stackoverflow`</sub>](/source/plugins/stackoverflow/README.md)
  * [🕹️ Steam <sub>`steam`</sub>](/source/plugins/steam/README.md)
  * [🐤 Latest tweets <sub>`tweets`</sub>](/source/plugins/tweets/README.md) <sub>`⚠️ deprecated`</sub>
  * [⏰ WakaTime <sub>`wakatime`</sub>](/source/plugins/wakatime/README.md)

**🎲 Maintained by community**
* **[Community plugins](/source/plugins/community/README.md)**
  * [🧠 16personalities <sub>`16personalities`</sub>](/source/plugins/community/16personalities/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [♟️ Chess <sub>`chess`</sub>](/source/plugins/community/chess/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [🪙 Crypto <sub>`crypto`</sub>](/source/plugins/community/crypto/README.md) by [@dajneem23](https://github.com/dajneem23)
  * [🥠 Fortune <sub>`fortune`</sub>](/source/plugins/community/fortune/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [💉 Nightscout <sub>`nightscout`</sub>](/source/plugins/community/nightscout/README.md) by [@legoandmars](https://github.com/legoandmars)
  * [💩 PoopMap plugin <sub>`poopmap`</sub>](/source/plugins/community/poopmap/README.md) by [@matievisthekat](https://github.com/matievisthekat)
  * [📸 Website screenshot <sub>`screenshot`</sub>](/source/plugins/community/screenshot/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [🦑 Splatoon <sub>`splatoon`</sub>](/source/plugins/community/splatoon/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [💹 Stock prices <sub>`stock`</sub>](/source/plugins/community/stock/README.md) by [@lowlighter](https://github.com/lowlighter)
````

## File: README.md
````markdown
# 📊 Metrics [<img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=280144&theme=dark" alt="" align="right" width="190" height="41">](https://www.producthunt.com/posts/github-metrics?utm_source=badge-featured&utm_medium=badge&utm_source=badge-github-metrics)

[![Continuous integration](https://github.com/lowlighter/metrics/actions/workflows/ci.yml/badge.svg)](https://github.com/lowlighter/metrics/actions/workflows/ci.yml)

Generate metrics that can be embedded everywhere, including your GitHub profile readme! Supports users, organizations, and even repositories!

<table>
  <tr>
    <th align="center">For user accounts</th>
    <th align="center">For organization accounts</th>
  </tr>
  <tr>
    <td align="center">
<img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.classic.svg" alt=""></img>
</td>
<td align="center">
<img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.organization.svg" alt=""></img>
</td>
  </tr>
  <tr>
    <th colspan="2" align="center">
      <h3><a href="/README.md#-plugins">🧩 Customizable with 47 plugins and 335 options!</a></h3>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/isocalendar/README.md">📅 Isometric commit calendar</a></th>
    <th><a href="source/plugins/languages/README.md">🈷️ Languages activity</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Full year calendar</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.isocalendar.fullyear.svg" alt=""></img></details>
        <details><summary>Half year calendar</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.isocalendar.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Indepth analysis (clone and analyze repositories)</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.indepth.svg" alt=""></img></details>
        <details open><summary>Recently used (analyze recent activity events)</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.recent.svg" alt=""></img></details>
        <details><summary>Default algorithm</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.svg" alt=""></img></details>
        <details><summary>Default algorithm (with details)</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.languages.details.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/stargazers/README.md">✨ Stargazers</a></th>
    <th><a href="source/plugins/lines/README.md">👨‍💻 Lines of code changed</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Classic charts</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.svg" alt=""></img></details>
        <details><summary>Graph charts</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.graph.svg" alt=""></img></details>
        <details open><summary>Worldmap</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stargazers.worldmap.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Repositories and diff history</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.lines.history.svg" alt=""></img></details>
        <details><summary>Compact display in base plugin</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.lines.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/topics/README.md">📌 Starred topics</a></th>
    <th><a href="source/plugins/stars/README.md">🌟 Recently starred repositories</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>With icons</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.topics.icons.svg" alt=""></img></details>
        <details open><summary>With labels</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.topics.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stars.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/licenses/README.md">📜 Repository licenses</a></th>
    <th><a href="source/plugins/habits/README.md">💡 Coding habits and activity</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Permissions, limitations and conditions</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.licenses.svg" alt=""></img></details>
        <details open><summary>Licenses overview</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.licenses.ratio.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Recent activity charts</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.habits.charts.svg" alt=""></img></details>
        <details open><summary>Mildly interesting facts</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.habits.facts.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/contributors/README.md">🏅 Repository contributors</a></th>
    <th><a href="source/plugins/followup/README.md">🎟️ Follow-up of issues and pull requests</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>By contribution types</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.contributors.categories.svg" alt=""></img></details>
        <details><summary>By number of contributions</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.contributors.contributions.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Indepth analysis</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.indepth.svg" alt=""></img></details>
        <details><summary>Created on a user's repositories</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.svg" alt=""></img></details>
        <details><summary>Created by a user</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.followup.user.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/reactions/README.md">🎭 Comment reactions</a></th>
    <th><a href="source/plugins/people/README.md">🧑‍🤝‍🧑 People</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.reactions.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Related to a user</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.people.followers.svg" alt=""></img></details>
        <details><summary>Related to a repository</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.people.repository.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/sponsorships/README.md">💝 GitHub Sponsorships</a></th>
    <th><a href="source/plugins/sponsors/README.md">💕 GitHub Sponsors</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsorships.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>GitHub sponsors card</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsors.svg" alt=""></img></details>
        <details><summary>GitHub sponsors full introduction</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.sponsors.full.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/repositories/README.md">📓 Featured repositories</a></th>
    <th><a href="source/plugins/discussions/README.md">💬 Discussions</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Featured</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.repositories.svg" alt=""></img></details>
        <details><summary>Pinned</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.repositories.pinned.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.discussions.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/starlists/README.md">💫 Star lists</a></th>
    <th><a href="source/plugins/calendar/README.md">📆 Commit calendar</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Repositories from star lists</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.starlists.svg" alt=""></img></details>
        <details open><summary>Languages from star lists</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.starlists.languages.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details><summary>Current year</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.calendar.svg" alt=""></img></details>
        <details open><summary>Full history</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.calendar.full.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/achievements/README.md">🏆 Achievements</a></th>
    <th><a href="source/plugins/notable/README.md">🎩 Notable contributions</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Compact display</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.achievements.compact.svg" alt=""></img></details>
        <details><summary>Detailed display</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.achievements.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Indepth analysis</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.notable.indepth.svg" alt=""></img></details>
        <details><summary>Contributions in organizations only</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.notable.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/activity/README.md">📰 Recent activity</a></th>
    <th><a href="source/plugins/traffic/README.md">🧮 Repositories traffic</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.activity.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.traffic.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/code/README.md">♐ Random code snippet</a></th>
    <th><a href="source/plugins/gists/README.md">🎫 Gists</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.code.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.gists.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/projects/README.md">🗂️ GitHub projects</a></th>
    <th><a href="source/plugins/introduction/README.md">🙋 Introduction</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.projects.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>For a user or an organization</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.introduction.svg" alt=""></img></details>
        <details><summary>For a repository</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.introduction.repository.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/skyline/README.md">🌇 GitHub Skyline</a></th>
    <th><a href="source/plugins/pagespeed/README.md">⏱️ Google PageSpeed</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>GitHub Skyline</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.skyline.svg" alt=""></img></details>
        <details><summary>GitHub City</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.skyline.city.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>PageSpeed scores</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.svg" alt=""></img></details>
        <details><summary>PageSpeed scores with detailed report</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.detailed.svg" alt=""></img></details>
        <details><summary>PageSpeed scores with a website screenshot</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.pagespeed.screenshot.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/stackoverflow/README.md">🗨️ Stack Overflow</a></th>
    <th><a href="source/plugins/anilist/README.md">🌸 Anilist watch list and reading list</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stackoverflow.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>For anime watchers</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.svg" alt=""></img></details>
        <details><summary>For manga readers</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.manga.svg" alt=""></img></details>
        <details open><summary>For waifus simp</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.anilist.characters.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/music/README.md">🎼 Music activity and suggestions</a></th>
    <th><a href="source/plugins/posts/README.md">✒️ Recent posts</a></th>
  </tr>
  <tr>
        <td  align="center">
        <details open><summary>Random tracks from a playlist</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.music.playlist.svg" alt=""></img></details>
        <details open><summary>Recently listened</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.music.recent.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Latest posts width description and cover image</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.posts.full.svg" alt=""></img></details>
        <details><summary>Latest posts</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.posts.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/rss/README.md">🗼 Rss feed</a></th>
    <th><a href="source/plugins/wakatime/README.md">⏰ WakaTime</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.rss.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.wakatime.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="source/plugins/leetcode/README.md">🗳️ Leetcode</a></th>
    <th><a href="source/plugins/steam/README.md">🕹️ Steam</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.leetcode.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <details open><summary>Recently played games</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.steam.svg" alt=""></img></details>
        <details><summary>Profile and detailed game history</summary><img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.steam.full.svg" alt=""></img></details>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th colspan="2" align="center">
      <a href="/source/plugins/community/README.md">🎲 See also community plugins</a>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/community/16personalities/README.md">🧠 16personalities</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.16personalities.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
    <th><a href="source/plugins/community/chess/README.md">♟️ Chess</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.chess.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/community/crypto/README.md">🪙 Crypto</a><br><sup>by <a href="https://github.com/dajneem23">@dajneem23</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://via.placeholder.com/468x60?text=No%20preview%20available" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
    <th><a href="source/plugins/community/fortune/README.md">🥠 Fortune</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.fortune.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/community/nightscout/README.md">💉 Nightscout</a><br><sup>by <a href="https://github.com/legoandmars">@legoandmars</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/legoandmars/legoandmars/blob/master/metrics.plugin.nightscout.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
    <th><a href="source/plugins/community/poopmap/README.md">💩 PoopMap plugin</a><br><sup>by <a href="https://github.com/matievisthekat">@matievisthekat</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/matievisthekat/matievisthekat/blob/master/metrics.plugin.poopmap.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/community/screenshot/README.md">📸 Website screenshot</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.screenshot.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
    <th><a href="source/plugins/community/splatoon/README.md">🦑 Splatoon</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.splatoon.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
  </tr>
  <tr>
    <th><a href="source/plugins/community/stock/README.md">💹 Stock prices</a><br><sup>by <a href="https://github.com/lowlighter">@lowlighter</a></sup>
      <details><summary>Render example</summary>
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.plugin.stock.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </details>
    </th>
    <th>
    </th>
  </tr>
  <tr>
    <th colspan="2" align="center">
      <h3><a href="/README.md#%EF%B8%8F-templates">🖼️ And even more with 4+ templates!</a></h3>
    </th>
  </tr>
  <tr>
    <th><a href="/source/templates/classic/README.md">📗 Classic template</a></th>
    <th><a href="/source/templates/repository/README.md">📘 Repository template</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.classic.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.repository.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th><a href="/source/templates/terminal/README.md">📙 Terminal template</a></th>
    <th><a href="/source/templates/markdown/README.md">📒 Markdown template</a></th>
  </tr>
  <tr>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.terminal.svg" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
        <td  align="center">
        <img alt="" width="400" src="https://github.com/lowlighter/metrics/blob/examples/metrics.markdown.png" alt=""></img>
        <img width="900" height="1" alt="">
      </td>
  </tr>
  <tr>
    <th colspan="2"><a href="/source/templates/community/README.md">📕 See also community templates</a></th>
  </tr>
  <tr>
    <th colspan="2"><h2>🦑 Try it now!</h2></th>
  </tr>
  <tr>
    <th><a href="https://metrics.lecoq.io/embed">📊 Metrics embed</a></th>
    <th><a href="https://metrics.lecoq.io/insights">✨ Metrics insights</a></th>
  </tr>
  <tr>
    <td align="center">
      Embed metrics images on your profile or blog!<br>
      Use <a href="https://github.com/marketplace/actions/metrics-embed">GitHub actions</a> for even more features!<br>
      <img src="/.github/readme/imgs/features_embed.gif" width="360">
    </td>
    <td align="center">
      Share your metrics with friends and on social medias!<br>
      No configuration needed!<br>
      <img src="/.github/readme/imgs/features_insights.gif" width="360">
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      Test latest features and patches on <code><a href="https://beta-metrics.lecoq.io">🧪 Metrics beta</a></code>!
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <b>Power user?</b><br>
      <a href="https://github.com/lowlighter/metrics/fork">Fork this repository</a> and edit HTML, CSS, JS and <a href="https://github.com/mde/ejs">EJS</a> for even more customization!
    </td>
  </tr>
</table>


# 📚 Documentation


> <sup>*⚠️ This is the documentation of **v3.35-beta** (`@master`/`@main` branches) which includes [unreleased features](https://github.com/lowlighter/metrics/compare/latest...master) planned for next release. See documentation for current released version [**v3.34** (`@latest` branch) here](https://github.com/lowlighter/metrics/blob/latest/README.md).* </sup>



## 🦮 Setup

There are several ways to setup metrics, each having its advantages and disadvantages:

* [⚙️ Using GitHub Action on a profile repository *(~10 min)*](/.github/readme/partials/documentation/setup/action.md)
  * ✔️ All features
  * ✔️ High availability (no downtimes)
  * ➖ Configuration can be a bit time-consuming
* [💕 Using the shared instance *(~1 min)*](/.github/readme/partials/documentation/setup/shared.md)
  * ✔️ Easily configurable and previewable
  * ➖ Limited features *(compute-intensive features are disabled)*
* [🏗️ Deploying a web instance *(~20 min)*](/.github/readme/partials/documentation/setup/web.md)
  * ✔️ Create another shared instance
  * ➖ Requires some sysadmin knowledge
* [🐳 Using command line with docker *(~2 min)*](/.github/readme/partials/documentation/setup/docker.md)
  * ✔️ Suited for one-time rendering
* [🔧 Local setup for development *(~20 min)*](/.github/readme/partials/documentation/setup/local.md)

Additional resources for setup:
* [🏦 Configure metrics for organizations](/.github/readme/partials/documentation/organizations.md)
* [🏠 Run metrics on self-hosted runners](/.github/readme/partials/documentation/selfhosted.md)
* [🧰 Template/Plugin compatibility matrix](/.github/readme/partials/documentation/compatibility.md)
## 🖼️ Templates

Templates lets you change general appearance of rendered metrics.


* [📗 Classic template <sub>`classic`</sub>](/source/templates/classic/README.md)
* [📘 Repository template <sub>`repository`</sub>](/source/templates/repository/README.md)
* [📙 Terminal template <sub>`terminal`</sub>](/source/templates/terminal/README.md)
* [📒 Markdown template <sub>`markdown`</sub>](/source/templates/markdown/README.md)
* [📕 Community templates <sub>`community`</sub>](/source/templates/community/README.md)

## 🧩 Plugins

Plugins provide additional content and lets you customize rendered metrics.

**📦 Maintained by core team**

* **Core plugins**
  * [🗃️ Base content <sub>`base`</sub>](/source/plugins/base/README.md)
  * [🧱 Core <sub>`core`</sub>](/source/plugins/core/README.md)
* **GitHub plugins**
  * [🏆 Achievements <sub>`achievements`</sub>](/source/plugins/achievements/README.md)
  * [📰 Recent activity <sub>`activity`</sub>](/source/plugins/activity/README.md)
  * [📆 Commit calendar <sub>`calendar`</sub>](/source/plugins/calendar/README.md)
  * [♐ Random code snippet <sub>`code`</sub>](/source/plugins/code/README.md)
  * [🏅 Repository contributors <sub>`contributors`</sub>](/source/plugins/contributors/README.md)
  * [💬 Discussions <sub>`discussions`</sub>](/source/plugins/discussions/README.md)
  * [🎟️ Follow-up of issues and pull requests <sub>`followup`</sub>](/source/plugins/followup/README.md)
  * [🎫 Gists <sub>`gists`</sub>](/source/plugins/gists/README.md)
  * [💡 Coding habits and activity <sub>`habits`</sub>](/source/plugins/habits/README.md)
  * [🙋 Introduction <sub>`introduction`</sub>](/source/plugins/introduction/README.md)
  * [📅 Isometric commit calendar <sub>`isocalendar`</sub>](/source/plugins/isocalendar/README.md)
  * [🈷️ Languages activity <sub>`languages`</sub>](/source/plugins/languages/README.md)
  * [📜 Repository licenses <sub>`licenses`</sub>](/source/plugins/licenses/README.md)
  * [👨‍💻 Lines of code changed <sub>`lines`</sub>](/source/plugins/lines/README.md)
  * [🎩 Notable contributions <sub>`notable`</sub>](/source/plugins/notable/README.md)
  * [🧑‍🤝‍🧑 People <sub>`people`</sub>](/source/plugins/people/README.md)
  * [🗂️ GitHub projects <sub>`projects`</sub>](/source/plugins/projects/README.md)
  * [🎭 Comment reactions <sub>`reactions`</sub>](/source/plugins/reactions/README.md)
  * [📓 Featured repositories <sub>`repositories`</sub>](/source/plugins/repositories/README.md)
  * [🌇 GitHub Skyline <sub>`skyline`</sub>](/source/plugins/skyline/README.md)
  * [💕 GitHub Sponsors <sub>`sponsors`</sub>](/source/plugins/sponsors/README.md)
  * [💝 GitHub Sponsorships <sub>`sponsorships`</sub>](/source/plugins/sponsorships/README.md)
  * [✨ Stargazers <sub>`stargazers`</sub>](/source/plugins/stargazers/README.md)
  * [💫 Star lists <sub>`starlists`</sub>](/source/plugins/starlists/README.md)
  * [🌟 Recently starred repositories <sub>`stars`</sub>](/source/plugins/stars/README.md)
  * [💭 GitHub Community Support <sub>`support`</sub>](/source/plugins/support/README.md) <sub>`⚠️ deprecated`</sub>
  * [📌 Starred topics <sub>`topics`</sub>](/source/plugins/topics/README.md)
  * [🧮 Repositories traffic <sub>`traffic`</sub>](/source/plugins/traffic/README.md)
* **Social plugins**
  * [🌸 Anilist watch list and reading list <sub>`anilist`</sub>](/source/plugins/anilist/README.md)
  * [🗳️ Leetcode <sub>`leetcode`</sub>](/source/plugins/leetcode/README.md)
  * [🎼 Music activity and suggestions <sub>`music`</sub>](/source/plugins/music/README.md)
  * [⏱️ Google PageSpeed <sub>`pagespeed`</sub>](/source/plugins/pagespeed/README.md)
  * [✒️ Recent posts <sub>`posts`</sub>](/source/plugins/posts/README.md)
  * [🗼 Rss feed <sub>`rss`</sub>](/source/plugins/rss/README.md)
  * [🗨️ Stack Overflow <sub>`stackoverflow`</sub>](/source/plugins/stackoverflow/README.md)
  * [🕹️ Steam <sub>`steam`</sub>](/source/plugins/steam/README.md)
  * [🐤 Latest tweets <sub>`tweets`</sub>](/source/plugins/tweets/README.md) <sub>`⚠️ deprecated`</sub>
  * [⏰ WakaTime <sub>`wakatime`</sub>](/source/plugins/wakatime/README.md)

**🎲 Maintained by community**
* **[Community plugins](/source/plugins/community/README.md)**
  * [🧠 16personalities <sub>`16personalities`</sub>](/source/plugins/community/16personalities/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [♟️ Chess <sub>`chess`</sub>](/source/plugins/community/chess/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [🪙 Crypto <sub>`crypto`</sub>](/source/plugins/community/crypto/README.md) by [@dajneem23](https://github.com/dajneem23)
  * [🥠 Fortune <sub>`fortune`</sub>](/source/plugins/community/fortune/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [💉 Nightscout <sub>`nightscout`</sub>](/source/plugins/community/nightscout/README.md) by [@legoandmars](https://github.com/legoandmars)
  * [💩 PoopMap plugin <sub>`poopmap`</sub>](/source/plugins/community/poopmap/README.md) by [@matievisthekat](https://github.com/matievisthekat)
  * [📸 Website screenshot <sub>`screenshot`</sub>](/source/plugins/community/screenshot/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [🦑 Splatoon <sub>`splatoon`</sub>](/source/plugins/community/splatoon/README.md) by [@lowlighter](https://github.com/lowlighter)
  * [💹 Stock prices <sub>`stock`</sub>](/source/plugins/community/stock/README.md) by [@lowlighter](https://github.com/lowlighter)


## 💪 Contributing

If you are interested in contributing, the following resources may interest you:

* [💪 Contribution guide](/CONTRIBUTING.md)
* [🧬 Architecture](/ARCHITECTURE.md)
* [📜 License](/LICENSE)
* **:octocat: GitHub resources**
  * [📖 GitHub GraphQL API](https://docs.github.com/en/graphql)
  * [📖 GitHub GraphQL Explorer](https://docs.github.com/en/free-pro-team@latest/graphql/overview/explorer)
  * [📖 GitHub Rest API](https://docs.github.com/en/rest)
  * [📖 GitHub Octicons](https://github.com/primer/octicons)

Use [`💬 discussions`](https://github.com/lowlighter/metrics/discussions) for feedback, new features suggestions, bugs reports or to request help for installation.


## 📜 License

```
MIT License
Copyright (c) 2020-present lowlighter
```

![Sponsors](https://github.com/lowlighter/metrics/blob/examples/metrics.sponsors.svg)
````
