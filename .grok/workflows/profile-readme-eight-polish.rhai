let meta = #{
    name: "profile-readme-eight-polish",
    description: "Eight README polish items on branch dev: filter featured cards, ornamental separators, full-width custom widgets, rename My Tech Stack, denest word clouds, exotic legible full-width clouds, blog title without extra links, cute view counter",
    when_to_use: "Polish the origin/dev GitHub profile README with the eight visual items. Never use this to touch main, commit, or push.",
    phases: [
        #{ title: "Implement", detail: "four disjoint write-leases then one assembler lease" },
        #{ title: "Assure", detail: "adversarial contract skeptics plus focused pytest" },
    ],
};

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

let assure_schema = #{
    "type": "object",
    "required": ["item", "ok", "evidence"],
    "properties": #{
        "item": #{ "type": "string" },
        "ok": #{ "type": "boolean" },
        "evidence": #{ "type": "string" },
    },
};

let val_schema = #{
    "type": "object",
    "required": ["pytest_ok", "pytest_summary", "branch"],
    "properties": #{
        "pytest_ok": #{ "type": "boolean" },
        "pytest_summary": #{ "type": "string" },
        "branch": #{ "type": "string" },
    },
};

fn hard_rules() {
    let s = "";
    s += "HARD: stay on branch dev; never checkout, merge, or edit origin/main or branch main; never commit or push; never print secrets; never git reset/stash/discard. ";
    s += "Repo /Users/ww/dev/projects/wyattowalsh. Package manager uv only. Python 3.13+. ";
    s += "WRITE_LEASE only the listed paths. Touch nothing else. ";
    s += "Do not commit leftovers: goals/profile-readme-overhaul/inventory/**, scripts/utils.py leftover, tech-test.svg. ";
    s += "Do not run generate banner. Banner pair must stay origin/main bytes. ";
    s += "plugin_music, plugin_tweets, production plugin_activity stay no. plugin_repositories: no. Spotify never in lowlighter with:. ";
    s += "No visible markdown ## headings — keep unique sep-*.svg plus <!-- ## Title -->. ";
    s += "Use read_file and grep before editing. If already correct, status already_done with evidence. ";
    s += "Relative imports inside scripts/. Logging via get_logger, never print. ";
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
    p += " After any edit run the smallest relevant `uv run python -m pytest -q` for this lease. ";
    p += "Reply with status done, already_done, or blocked; files_changed; evidence; pytest (command plus exit code). ";
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
        if r == () || !r.success { names.push(jobs[i].label); }
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
            if r.output.evidence != () { text += r.output.evidence; }
            text += "\n";
        }
        i += 1;
    }
    return text;
}

phase("Implement");
log("Wave 1: four disjoint write-leases");

let extra_cards = "";
extra_cards += "Read config.yaml featured_repos and scripts/readme_sections.py _render_featured_projects. ";
extra_cards += "Keep featured_repos as exactly these eight full_names in this order: wyattowalsh/agents, wyattowalsh/nbadb, wyattowalsh/proxywhirl, wyattowalsh/mcp-crawl4ai, wyattowalsh/fl-mcp, wyattowalsh/personal-website, wyattowalsh/ai-web-feeds, wyattowalsh/iina-plugin-bookmarks. ";
extra_cards += "Remove listentropy and mdxpad. Add a test that load_config().readme_sections_settings.featured_repos names match that exact list. ";
extra_cards += "Do not edit README.md in this lease — assembler will regenerate cards.";

let extra_seps = "";
extra_seps += "Read scripts/readme_separators.py and tests that assert sep-*.svg uniqueness. ";
extra_seps += "Make each of the six separators (featured, metrics, living, tech, clouds, blog) much more ornamental and intricate — filigree, repeating motifs, layered strokes — while remaining distinct dialects so adjacent sections do not rhyme. ";
extra_seps += "Keep width 1200, raise height to 48-56 if needed, dark-mode via prefers-color-scheme, generate_separators() writes .github/assets/img/readme/sep-*.svg. ";
extra_seps += "Update aria for tech to My Tech Stack if the title change landed; otherwise keep Tech Stack until assembler. ";
extra_seps += "Add or keep a test that each sep file exists, is unique bytes, and contains a style media query.";

let extra_wc = "";
extra_wc += "Read scripts/word_clouds/typographic.py, colors.py, engine.py, generate.py, scripts/cli/generate/word_cloud.py, tests/test_word_clouds.py. ";
extra_wc += "Make the typographic packer more exotic: phyllotaxis or Archimedean spiral for the top-frequency constellation plus a packed remainder — not a plain two-column magazine grid. ";
extra_wc += "Keep public filenames wordcloud_typographic_by_topics.svg and wordcloud_typographic_by_languages.svg. ";
extra_wc += "Legibility: min font at least 8 on the public canvas, fully opaque fills, github_readable_fills / AA 3.0 on GitHub light and dark. ";
extra_wc += "Default/public canvas should read as full-width (wide landscape, e.g. 1600x520 or similar) so stacked README imgs look like banners not postage stamps. ";
extra_wc += "Do not edit README.md or profile-updater.yml. Tests: spiral/exotic placement exists, contrast helpers still used, filenames unchanged.";

let extra_views = "";
extra_views += "Read scripts/readme_svg.py and how footer chrome could wrap the komarev incrementer. ";
extra_views += "Add a first-party cute/funny views frame SVG writer (e.g. views-peek.svg) — speech-bubble / peeking / cookie-jar personality — that does NOT replace the incrementing komarev count. ";
extra_views += "Keep komarev.com/ghpvc username=wyattowalsh as the live counter. Do not stand up new view-counter infra. ";
extra_views += "Do not edit readme_sections.py (assembler lease owns footer markup). Tests for the frame SVG exist and do not embed secrets.";

let wave1 = [
    impl_job(
        "impl-cards",
        "Filter featured project cards to the eight named repos",
        "config.yaml, tests/test_config.py",
        extra_cards,
        impl_schema,
    ),
    impl_job(
        "impl-seps",
        "Ornamental unique horizontal separators",
        "scripts/readme_separators.py, .github/assets/img/readme/sep-*.svg, tests/test_readme_gfm_ux.py",
        extra_seps,
        impl_schema,
    ),
    impl_job(
        "impl-clouds-algo",
        "Exotic legible typographic word-cloud algorithm",
        "scripts/word_clouds/, scripts/cli/generate/word_cloud.py, tests/test_word_clouds.py, tests/test_word_cloud_coverage.py, tests/test_word_clouds_clustered_shaped.py, tests/test_word_clouds_red.py",
        extra_wc,
        impl_schema,
    ),
    impl_job(
        "impl-views-frame",
        "Cute first-party view-counter frame SVG",
        "scripts/readme_svg.py, tests/test_readme_svg.py",
        extra_views,
        impl_schema,
    ),
];

let wave1_res = parallel(wave1);
log("Wave 1 closed " + count_impl_ok(wave1_res).to_string() + "/4. Failures: " + json_encode(failed_labels(wave1_res, wave1)));

let extra_asm = "";
extra_asm += "Read scripts/readme_sections.py, scripts/config.py ReadmeSectionsSettings and SkillsSettings.section_title, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py, tests/test_section_order.py, tests/test_overhaul_fact_ids.py, tests/test_profile_workflow.py. ";
extra_asm += "ITEM 3: custom widgets full width — in _rewrite_metrics_section, render first-party supplemental cards (metrics-languages, metrics-habits, metrics-music, metrics-posts) and the Waka SVG as stacked 100% width centered images. Keep the lowlighter metrics.svg + metrics.additional.svg pair as the existing 2-col table. ";
extra_asm += "ITEM 4: rename every durable Tech Stack title to My Tech Stack (DEFAULT_SECTION_ORDER, section_order defaults, config.yaml section_order, SkillsSettings.section_title, _TECH_STACK_* regexes and summary, separator mapping, tests). Keep no visible ##. ";
extra_asm += "ITEM 5: Word Clouds stay their own section AFTER the closed tech-stack details, never inside <details>. Stack the two typographic SVGs as full-width centered images (not a 50/50 table). Keep sep-clouds.svg + <!-- ## Word Clouds -->. ";
extra_asm += "ITEM 7: blog feed keeps sep-blog.svg + <!-- ## Latest Blog Posts -->. Each card remains a single <a><img></a>. DELETE the extra <p> of text links under the cards (the link_bits join). Keep the small RSS source line. ";
extra_asm += "ITEM 8: _rewrite_view_counter wraps the live komarev ghpvc img with the cute frame if present; keep incrementing komarev URL; funny label allowed (peek-a-boos / you found the cookie jar) but username=wyattowalsh must remain. ";
extra_asm += "After edits, if generate readme-sections is safe locally, run `uv run readme generate readme-sections` and `uv run readme generate skills` so README.md and skills markers match. Do not generate banner. ";
extra_asm += "Update tests that still assert Tech Stack, 2-col supplemental tables, or the blog link_bits paragraph.";

let asm = impl_job(
    "impl-assembler",
    "Assembler: full-width widgets, My Tech Stack, denest clouds, blog links, view counter wrap",
    "scripts/readme_sections.py, scripts/config.py, config.yaml, README.md, skills.yaml, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py, tests/test_section_order.py, tests/test_overhaul_fact_ids.py, tests/test_profile_workflow.py",
    extra_asm,
    impl_schema,
);
let asm_res = agent(asm.prompt, #{
    label: asm.label,
    capability_mode: "all",
    agent_type: "general-purpose",
    output_schema: impl_schema,
});
log("Assembler: " + (if asm_res.success { asm_res.output.status } else { "failed" }));

phase("Assure");
log("Adversarial skeptics on the eight items plus pytest");

let items = [
    "featured cards are exactly the eight named repos in config and generated README",
    "six sep-*.svg are ornamental, unique, dark-mode, and used with comment headings",
    "first-party music/habits/languages/waka widgets render full width not 50 percent",
    "section title is My Tech Stack in config, skills summary, and README",
    "word clouds are outside tech-stack details as their own full-width section",
    "typographic word-cloud packer is exotic (spiral/phyllotaxis) and contrast-safe",
    "blog has Latest Blog Posts title/sep and no extra text-link row under cards",
    "view counter still increments via komarev and is wrapped in cute first-party chrome",
];
let skeptics = [];
let si = 0;
for it in items {
    let sp = hard_rules();
    sp += "WRITE_LEASE none. Do not edit. Adversarially verify this claim by reading the shipped files (not memory): ";
    sp += it;
    sp += " Set ok=true only with concrete evidence you independently inspected. Otherwise ok=false. item must repeat the claim.";
    skeptics.push(#{
        prompt: sp,
        label: "assure-" + si.to_string(),
        capability_mode: "read-only",
        output_schema: assure_schema,
    });
    si += 1;
}
let assure_res = parallel(skeptics);
let assure_ok = 0;
let assure_notes = "";
let ai = 0;
for r in assure_res {
    if r != () && r.success && r.output != () && r.output.ok == true
        && r.output.evidence != () && r.output.evidence != "" {
        assure_ok += 1;
        assure_notes += "- PASS ";
    } else {
        assure_notes += "- FAIL ";
    }
    if r != () && r.success && r.output != () {
        assure_notes += r.output.item;
        assure_notes += " — ";
        if r.output.evidence != () { assure_notes += r.output.evidence; }
    } else {
        assure_notes += items[ai];
        assure_notes += " — unverified slot";
    }
    assure_notes += "\n";
    ai += 1;
}
log("Assure " + assure_ok.to_string() + "/8");

let val_p = hard_rules();
val_p += "WRITE_LEASE none. Confirm branch with git rev-parse --abbrev-ref HEAD. ";
val_p += "Run: uv run python -m pytest -q tests/test_config.py tests/test_readme_sections.py tests/test_readme_gfm_ux.py tests/test_section_order.py tests/test_readme_svg.py tests/test_word_clouds.py tests/test_overhaul_fact_ids.py --tb=line. ";
val_p += "Report pytest_ok, pytest_summary (command plus exit), branch.";
let val = agent(val_p, #{
    label: "assure-pytest",
    capability_mode: "execute",
    agent_type: "general-purpose",
    output_schema: val_schema,
});

let report = "# profile-readme-eight-polish\n\n";
report += "## Implement\n";
report += impl_notes(wave1_res, wave1);
report += "- impl-assembler: ";
if asm_res.success && asm_res.output != () {
    report += asm_res.output.status;
    report += " — ";
    if asm_res.output.evidence != () { report += asm_res.output.evidence; }
} else {
    report += "failed";
}
report += "\n\n## Assure\n";
report += assure_notes;
report += "\n## Pytest\n";
if val.success && val.output != () {
    report += val.output.pytest_summary;
    report += "\nbranch=";
    report += val.output.branch;
} else {
    report += "pytest agent failed";
}
let path = write_scratch_file("eight-polish-report.md", report);
complete(#{
    path: path,
    impl_wave1: count_impl_ok(wave1_res),
    assure_ok: assure_ok,
    assure_total: 8,
    pytest_ok: val.success && val.output != () && val.output.pytest_ok == true,
});
