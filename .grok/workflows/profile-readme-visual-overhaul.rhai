let meta = #{
    name: "profile-readme-visual-overhaul",
    description: "Close the visual GitHub profile README overhaul on origin/dev: unique SVG separators, first-party languages Sankey plus habits and Spotify, expanded Waka SVG, icon-colored tech shields, fractal word-cloud reel, living-art mp4 companions, and a magazine blog board — then pytest/rg contracts and a screenshot list",
    when_to_use: "Finish the visual README overhaul on branch dev with seven disjoint write-lease closers, then validate contracts and list origin/dev screenshots. Never use this to touch main, commit, or push.",
    phases: [
        #{ title: "Implement", detail: "seven disjoint write-lease closers in one parallel panel" },
        #{ title: "Validate", detail: "focused pytest plus rg contracts" },
        #{ title: "Inspect", detail: "read-only screenshot list for origin/dev" },
    ],
};

const IMPL_TOTAL = 7;

let impl_schema = #{
    "type": "object",
    "required": ["status", "files_changed", "evidence", "pytest"],
    "properties": #{
        "status": #{ "type": "string", "enum": ["done", "already_done", "blocked"] },
        "files_changed": #{ "type": "string" },
        "evidence": #{ "type": "string" },
        "pytest": #{ "type": "string" },
    },
};

let val_schema = #{
    "type": "object",
    "required": ["pytest_ok", "pytest_summary", "contracts_ok", "contracts_summary", "branch"],
    "properties": #{
        "pytest_ok": #{ "type": "boolean" },
        "pytest_summary": #{ "type": "string" },
        "contracts_ok": #{ "type": "boolean" },
        "contracts_summary": #{ "type": "string" },
        "branch": #{ "type": "string" },
    },
};

let inspect_schema = #{
    "type": "object",
    "required": ["shots", "notes"],
    "properties": #{
        "shots": #{
            "type": "array",
            "minItems": 1,
            "maxItems": 20,
            "items": #{
                "type": "object",
                "required": ["url", "target", "why"],
                "properties": #{
                    "url": #{ "type": "string" },
                    "target": #{ "type": "string" },
                    "why": #{ "type": "string" },
                },
            },
        },
        "notes": #{ "type": "string" },
    },
};

fn hard_rules() {
    let s = "";
    s += "HARD: stay on branch dev; never checkout, merge, or edit origin/main or branch main; never commit or push; never print secrets; never git reset/stash/discard. ";
    s += "Package manager is uv only — never pip or poetry. Python 3.13+. ";
    s += "WRITE_LEASE only the listed paths in this prompt. Touch nothing else. ";
    s += "Repo /Users/ww/dev/projects/wyattowalsh. Authority: goals/profile-readme-overhaul/{goal,facts,plan}.md and task-graph.json. ";
    s += "Relative imports inside scripts/. Logging via get_logger, never print. ";
    s += "Do not run generate banner. Banner pair must stay origin/main bytes. ";
    s += "plugin_music, plugin_tweets, and production plugin_activity stay no. plugin_repositories: no. No anmol098. Spotify never in lowlighter with:. ";
    s += "Use read_file and grep before editing. Do not answer from memory. If already correct, set status already_done with evidence and do not restyle. ";
    return s;
}

fn impl_job(task_id, title, lease, extra, schema) {
    let p = hard_rules();
    p += "TASK ";
    p += task_id;
    p += ": ";
    p += title;
    p += " WRITE_LEASE only: ";
    p += lease;
    p += " ";
    p += extra;
    p += " After any edit run the smallest relevant `uv run python -m pytest -q` command for this lease. ";
    p += "Reply with status done, already_done, or blocked; files_changed; evidence (paths or command output you inspected); pytest (exact command plus exit code). ";
    p += "blocked requires a concrete lease or missing-tool reason. Empty evidence is invalid.";
    return #{
        prompt: p,
        label: task_id,
        capability_mode: "all",
        agent_type: "general-purpose",
        output_schema: schema,
    };
}

fn failed_labels(results, jobs) {
    let names = [];
    let i = 0;
    for r in results {
        if r == () || !r.success {
            names.push(jobs[i].label);
        }
        i += 1;
    }
    return names;
}

fn count_impl_ok(results) {
    let n = 0;
    for r in results {
        if r != () && r.success && r.output != () {
            let st = r.output.status;
            if (st == "done" || st == "already_done")
                && r.output.evidence != ()
                && r.output.evidence != "" {
                n += 1;
            }
        }
    }
    return n;
}

fn impl_notes(results, jobs) {
    let text = "";
    let i = 0;
    for r in results {
        text += "- ";
        text += jobs[i].label;
        text += ": ";
        if r == () || !r.success || r.output == () {
            text += "unverified-or-failed-slot\n";
        } else {
            text += r.output.status;
            text += " — ";
            if r.output.evidence != () {
                text += r.output.evidence;
            }
            text += "\n";
        }
        i += 1;
    }
    return text;
}

// --- Implement ---
phase("Implement");
log("Seven disjoint visual-overhaul closers");

let extra_sep = "";
extra_sep += "Read scripts/readme_separators.py, scripts/readme_sections.py, tests/test_readme_sections.py, and tests/test_readme_gfm_ux.py first. ";
extra_sep += "Replace leftover markdown H2s with unique horizontal SVG separators for Featured Projects, Metrics, Living Art, Tech Stack, Word Clouds, and Latest Blog Posts. ";
extra_sep += "generate_separators() writes .github/assets/img/readme/sep-featured.svg, sep-metrics.svg, sep-living.svg, sep-tech.svg, sep-clouds.svg, sep-blog.svg. ";
extra_sep += "Each separator is a distinct visual dialect (adjacent sections must not rhyme), 1200x36, dark-mode via prefers-color-scheme. ";
extra_sep += "Keep metrics ~2-up (_gfm_two_col_imgs). Living-art cells use the GIF as poster and href the companion .mp4. ";
extra_sep += "Word-cloud section keeps exactly two public SVGs plus a reel href to .github/assets/img/wordcloud_fractal_reel.mp4. ";
extra_sep += "Blog wiring: one magazine board img (.github/assets/img/readme/blog-posts.svg) plus dated markdown links — do not restyle SvgBlogBoardRenderer (that is impl-blog). ";
extra_sep += "No metrics-activity embed. Tech-stack summary is a bare label inside details. Do not write README.md, profile-updater.yml, or banner.svg. ";
extra_sep += "Add or keep tests that section_separator_block maps those six titles to sep-*.svg and that leftover ## headings are rewritten.";

let extra_sup = "";
extra_sup += "Read scripts/supplemental_metrics.py and tests/test_supplemental_metrics.py first. ";
extra_sup += "Languages card (metrics-languages.svg): year-over-year Sankey from repo created_at to primary language; drop JetBrains MPS and any _is_excluded_language match; keep current-bytes labels. ";
extra_sup += "Habits card: strip any cloned lowlighter top-row recap; keep focus repos, peak hour, designed streaks, dark media; keep or invent one uncommon useful metric (HHI/mosaic concentration is acceptable if tested). ";
extra_sup += "Spotify card: striking recent-listens hero plus all-time profile stats (long_term top artists/tracks already fetched); compact extras only if they stay beautiful. Never pass Spotify into lowlighter. ";
extra_sup += "Do not edit .github/workflows/profile-updater.yml. plugin_music stays no. Do not print SPOTIFY_* values. ";
extra_sup += "Tests must cover MPS exclusion, sankey/year-flow markers, habits unique fields, and all-time Spotify labels when fixtures include them.";

let extra_waka = "";
extra_waka += "Read scripts/wakatime_readme.py, scripts/wakatime_svg.py, tests/test_wakatime_svg.py, and tests/test_wakatime_readme.py first. ";
extra_waka += "Visible first-party Waka SVG (not anmol098, not a markdown dump, not wrapped in details by this lease). ";
extra_waka += "Collector keeps weekly + yearly + all-time ranges the API allows. Render languages, professional editors, Mac/iOS/watch platforms, coding categories, totals, heatmap if daily data exists. ";
extra_waka += "Expand uncommon derived metrics (lang entropy, editor loyalty, deep-work, browse leak, or better). Dark-mode via @media. Bypass SVGO. ";
extra_waka += "Privacy: drop file paths, heartbeats, private projects, leisure/social/health/shopping/entertainment apps. Project names only when they match a public repo or allowlist. ";
extra_waka += "Do not write README.md or the workflow YAML. Tests must reject banned categories/names and assert derived chips exist.";

let extra_sk = "";
extra_sk += "Read scripts/skills.py, skills.yaml, scripts/config.py (SkillEntry), and tests/test_skills.py first. ";
extra_sk += "Ship icon-colored linked tech shields: every skill has a homepage url and a well-fitting icon (simple-icons slug or first-party logo_path). Prefer retro icons that still read at badge size. ";
extra_sk += "GitHub-camo-safe delivery. Badge URLs stay under MAX_SHIELDS_BADGE_URL_LENGTH. Generated <a href> is non-empty http(s). ";
extra_sk += "Tech stack remains inside details — this lease does not rewrite README wrappers. ";
extra_sk += "Do not write README.md even though SkillsBadgeGenerator.generate() can inject markers. Change generator + yaml + tests only. ";
extra_sk += "Do not edit profile-updater.yml. Tests: href coverage, URL length, icon present, well-fitting icons.";

let extra_wc = "";
extra_wc += "Read scripts/word_clouds/ (especially shaped.FractalRenderer, generate.py, metaheuristic registry), scripts/cli/generate/word_cloud.py, and tests/test_word_clouds*.py first. ";
extra_wc += "Fractal-fitted word area: Koch silhouette for topics, dragon for languages; size/intensity follows starred-repo share. ";
extra_wc += "Ship exactly two public SVGs (CI currently writes wordcloud_typographic_by_{topics,languages}.svg with --renderer fractal). Do not add more public clouds. ";
extra_wc += "Add or keep a slow-morph reel helper targeting .github/assets/img/wordcloud_fractal_reel.mp4 with a fav SVG as poster. Do not encode a full fleet if a focused unit test of the helper is enough. ";
extra_wc += "Keep or add a volume-fidelity test. Light/dark readable. Do not run generate banner. Do not edit profile-updater.yml or README.md.";

let extra_art = "";
extra_art += "Read scripts/art/artifacts.py, scripts/art/timelapse.py, scripts/art/animate.py, tests/test_living_art_media.py, tests/test_living_art_contracts.py, and docs/content/docs/scripts/living-art-modes.mdx first. ";
extra_art += "Keep the exact-six living-*.gif names as posters (inkgarden, topo, genetic, physarum, lenia, ferrofluid). Add companion .mp4 or .mov films (living-<style>.mp4) without inventing new styles. ";
extra_art += "One shared daily spine from account creation to now. Do not regenerate the full 120-frame fleet unless a contract test is already failing. ";
extra_art += "If you add an encoder, call system ffmpeg only when present; tests must mock or skip when ffmpeg is absent. Update the dialect table if the published media contract grows. ";
extra_art += "Do not edit README.md, profile-updater.yml, or banner assets. Monotonic snapshot tests stay green.";

let extra_blog = "";
extra_blog += "Read scripts/readme_svg.py (SvgBlogBoardRenderer), tests/test_readme_svg.py, tests/test_svg_snapshots.py, and tests/test_card_contracts_blog_red.py first. ";
extra_blog += "Finish the magazine board: one SVG (blog-posts.svg conceptually) with a featured post plus up to four items; each row has title, date, and a one-line hook. Dark-mode CSS. ";
extra_blog += "Do not edit scripts/readme_sections.py — impl-separators owns assembler wiring and dated markdown links under the board. ";
extra_blog += "Do not write README.md. Keep feed-failure behavior fail-closed or last-good in the renderer contract. ";
extra_blog += "Tests must assert board classes (board-title, feature-hook, item titles/hooks), 4-5 posts, and snapshot stability for non-random chrome.";

let impl_jobs = [
    impl_job(
        "impl-separators",
        "Unique SVG section separators and README assembler wiring",
        "scripts/readme_separators.py, scripts/readme_sections.py, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py, tests/test_section_order.py",
        extra_sep,
        impl_schema,
    ),
    impl_job(
        "impl-supplemental",
        "First-party languages Sankey, redesigned habits, all-time Spotify",
        "scripts/supplemental_metrics.py, tests/test_supplemental_metrics.py",
        extra_sup,
        impl_schema,
    ),
    impl_job(
        "impl-waka",
        "First-party Waka SVG with exotic derived metrics",
        "scripts/wakatime_readme.py, scripts/wakatime_svg.py, tests/test_wakatime_svg.py, tests/test_wakatime_readme.py",
        extra_waka,
        impl_schema,
    ),
    impl_job(
        "impl-skills",
        "Icon-colored linked tech shields",
        "scripts/skills.py, skills.yaml, scripts/config.py, tests/test_skills.py",
        extra_sk,
        impl_schema,
    ),
    impl_job(
        "impl-wordclouds",
        "Fractal-fitted word clouds plus optional slow-morph reel",
        "scripts/word_clouds/, scripts/cli/generate/word_cloud.py, tests/test_word_clouds.py, tests/test_word_cloud_coverage.py, tests/test_word_clouds_clustered_shaped.py, tests/test_word_clouds_red.py",
        extra_wc,
        impl_schema,
    ),
    impl_job(
        "impl-living-art",
        "Living-art companion mp4/mov films with GIF posters",
        "scripts/art/, tests/test_living_art_media.py, tests/test_living_art_contracts.py, tests/test_living_art_artifact_handoff.py, docs/content/docs/scripts/living-art-modes.mdx",
        extra_art,
        impl_schema,
    ),
    impl_job(
        "impl-blog",
        "Magazine blog board renderer",
        "scripts/readme_svg.py, tests/test_readme_svg.py, tests/test_svg_snapshots.py, tests/test_card_contracts_blog_red.py",
        extra_blog,
        impl_schema,
    ),
];

let impl_res = parallel(impl_jobs);
let impl_fail = failed_labels(impl_res, impl_jobs);
let impl_ok = count_impl_ok(impl_res);
log("Implement " + impl_ok.to_string() + "/" + IMPL_TOTAL.to_string() + " closed. Failures: " + json_encode(impl_fail));

// --- Validate ---
phase("Validate");
let val_p = hard_rules();
val_p += "TASK validate-gates: WRITE_LEASE none. Do not edit any repo file. Run focused pytest and rg contracts; report exact commands and exit codes. ";
val_p += "Confirm HEAD is dev with `git rev-parse --abbrev-ref HEAD` (do not checkout). ";
val_p += "Required pytest (skip a path only if the file is missing, and say so): ";
val_p += "`uv run python -m pytest -q tests/test_profile_workflow.py tests/test_readme_sections.py tests/test_readme_gfm_ux.py tests/test_supplemental_metrics.py tests/test_wakatime_svg.py tests/test_wakatime_readme.py tests/test_skills.py tests/test_word_clouds.py tests/test_living_art_media.py tests/test_readme_svg.py --tb=line`. ";
val_p += "If tests/test_metrics_svg.py or tests/test_section_order.py exists, include it in a second command. ";
val_p += "rg contracts (run these, paste hits or empty): ";
val_p += "(1) `rg -n \"generate banner\" .github/workflows/profile-updater.yml` must be empty. ";
val_p += "(2) Production additional metrics `with:` has `plugin_repositories: no` and no plugin_repositories_featured — cite tests/test_profile_workflow.py and the YAML. Probe jobs may differ; judge production blocks. ";
val_p += "(3) `rg -n \"sep-(featured|metrics|living|tech|clouds|blog)\\.svg\" scripts/readme_separators.py scripts/readme_sections.py tests` must show the six separators. ";
val_p += "Also confirm `rg -n anmol098 scripts/` is empty and production `plugin_music: no`. ";
val_p += "pytest_ok and contracts_ok are true only with command output you ran. Do not hide failures.";
let val = agent(val_p, #{
    label: "validate-gates",
    capability_mode: "all",
    agent_type: "general-purpose",
    output_schema: val_schema,
});
let val_ok = val != ()
    && val.success
    && val.output != ()
    && val.output.pytest_ok == true
    && val.output.contracts_ok == true
    && val.output.pytest_summary != ()
    && val.output.pytest_summary != ""
    && val.output.contracts_summary != ()
    && val.output.contracts_summary != "";
if !val_ok { log("Validate agent failed or contracts not closed"); }

// --- Inspect ---
phase("Inspect");
let insp_p = hard_rules();
insp_p += "TASK inspect-shots: WRITE_LEASE none. Read-only. Do not edit. Do not commit or push. ";
insp_p += "Build a high-res screenshot checklist for the origin/dev preview only. ";
insp_p += "Primary URLs: https://github.com/wyattowalsh/wyattowalsh/tree/dev and https://github.com/wyattowalsh/wyattowalsh/blob/dev/README.md. ";
insp_p += "Read local README.md, scripts/readme_sections.py, and .github/assets/img/ (including readme/sep-*.svg, blog-posts.svg, tech-*.svg, wakatime.svg, metrics-*.svg, living-*.gif, wordcloud_*.svg) with read_file/grep. Do not answer from memory. ";
insp_p += "Each shot is {url, target, why}. Cover at least: pinned banner pair, each of the six separators, metrics 2-up plus extra, languages Sankey, habits, Spotify, Waka derived chips, living-art GIF posters and mp4 hrefs, fractal topic/language clouds and reel poster, tech-stack details shields, magazine blog board, view-counter chip. ";
insp_p += "Call out GFM vs local SVG differences and any missing committed asset that would look broken on github.com. Never list origin/main as a capture target.";
let insp = agent(insp_p, #{
    label: "inspect-shots",
    capability_mode: "read-only",
    agent_type: "explore",
    output_schema: inspect_schema,
});
let insp_ok = insp != ()
    && insp.success
    && insp.output != ()
    && insp.output.shots != ()
    && insp.output.notes != ();
let shot_count = 0;
if insp_ok { shot_count = insp.output.shots.len(); }
if !insp_ok { log("Inspect agent failed or returned no shots"); }

let summary = "";
summary += "implement ";
summary += impl_ok.to_string();
summary += "/";
summary += IMPL_TOTAL.to_string();
summary += "; validate ";
if val_ok { summary += "ok"; } else { summary += "fail"; }
summary += "; inspect ";
summary += shot_count.to_string();
summary += " shots";

let report = "";
report += "# profile-readme-visual-overhaul\n\n";
report += summary;
report += "\n\n## implement\n\n";
report += impl_notes(impl_res, impl_jobs);
report += "\n## validate\n\n";
if val != () && val.success && val.output != () {
    report += "branch=";
    report += val.output.branch;
    report += "\npytest_ok=";
    report += json_encode(val.output.pytest_ok);
    report += "\n";
    report += val.output.pytest_summary;
    report += "\n\ncontracts_ok=";
    report += json_encode(val.output.contracts_ok);
    report += "\n";
    report += val.output.contracts_summary;
    report += "\n";
} else {
    report += "unverified-or-failed-slot\n";
}
report += "\n## inspect\n\n";
if insp_ok {
    report += insp.output.notes;
    report += "\n";
    report += json_encode(insp.output.shots);
    report += "\n";
} else {
    report += "unverified-or-failed-slot\n";
}

let path = write_scratch_file("visual-overhaul-report.md", report);
complete(#{
    path: path,
    summary: summary,
    implement_ok: impl_ok,
    implement_total: IMPL_TOTAL,
    implement_failures: impl_fail,
    validate_ok: val_ok,
    inspect_ok: insp_ok,
    inspect_shots: shot_count,
});
