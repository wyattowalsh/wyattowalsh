let meta = #{
    name: "profile-readme-overhaul-audit-complete",
    description: "Audit profile-readme-overhaul completion, close remaining gaps on disjoint locks, then adversarially assure every accepted fact",
    when_to_use: "Audit or finish goals/profile-readme-overhaul on origin/dev; max-fan-out read-only audit then lock-safe close and assure",
    phases: [
        #{ title: "Audit", detail: "read-only fact, plan, and contract lanes" },
        #{ title: "Close", detail: "check-then-fix remaining gaps on disjoint write leases" },
        #{ title: "Validate", detail: "focused pytest plus workflow contracts" },
        #{ title: "Assure", detail: "adversarial skeptics per accepted fact" },
        #{ title: "Repair", detail: "targeted leftover repairs if assure is not closed" },
    ],
};

fn standing() {
    let s = "";
    s += "Repo /Users/ww/dev/projects/wyattowalsh. Authority: goals/profile-readme-overhaul/{goal,facts,plan}.md and task-graph.json. ";
    s += "HARD: stay on branch dev; never checkout, merge, or edit origin/main; never commit or push; never print secrets; never git reset/stash/discard. ";
    s += "Package manager is uv only. Python 3.13+. Relative imports inside scripts/. Logging via get_logger, never print. ";
    s += "CI finalize is the sole first-party git writer. Do not run generate banner in CI. Banner pair must match origin/main bytes. ";
    s += "plugin_music, plugin_tweets, and production plugin_activity stay no. No anmol098. Spotify never in lowlighter with:. ";
    s += "Use read_file and grep before editing. Only touch WRITE_LEASE paths. If already correct, say ALREADY_DONE with evidence and do not restyle. ";
    return s;
}

fn audit_job(label, question) {
    let schema = #{
        "type": "object",
        "required": ["ok", "evidence", "gaps"],
        "properties": #{
            "ok": #{ "type": "boolean" },
            "evidence": #{ "type": "string" },
            "gaps": #{ "type": "string" },
        },
    };
    let p = "";
    p += "Read-only exhaustive audit of goal profile-readme-overhaul in /Users/ww/dev/projects/wyattowalsh. ";
    p += "Use grep and read_file. Inspect the shipped tree, tests, README.md, and .github/workflows/profile-updater.yml. Do not edit. Do not answer from memory. ";
    p += question;
    p += " ok=true only with concrete paths or command output you inspected. Otherwise ok=false and list every missing or incorrect item in gaps.";
    return #{
        prompt: p,
        label: label,
        capability_mode: "read-only",
        agent_type: "explore",
        output_schema: schema,
    };
}

fn closer(task_id, title, lease, extra) {
    let p = standing();
    p += "TASK ";
    p += task_id;
    p += ": ";
    p += title;
    p += " WRITE_LEASE only: ";
    p += lease;
    p += " First inspect with read_file/grep. If the gap is already correctly implemented, do not restyle; say ALREADY_DONE with evidence. ";
    p += extra;
    p += " After edits run the smallest relevant uv run python -m pytest -q command. Reply with files changed and exact command plus exit code.";
    return #{
        prompt: p,
        label: task_id,
        capability_mode: "all",
        agent_type: "general-purpose",
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

fn collect_gaps(results) {
    let text = "";
    for r in results {
        if r == () || !r.success || r.output == () {
            text += "unverified-or-failed-slot\n";
        } else if r.output.ok != true {
            if r.output.gaps != () && r.output.gaps != "" {
                text += r.output.gaps;
                text += "\n";
            } else {
                text += "ok-false-without-gaps\n";
            }
        }
    }
    return text;
}

fn count_ok(results) {
    let n = 0;
    for r in results {
        if r != () && r.success && r.output != () && r.output.ok == true
            && r.output.evidence != () && r.output.evidence != "" {
            n += 1;
        }
    }
    return n;
}

let dry = false;
if args != () && args.dry_run == true { dry = true; }

// --- Audit ---
phase("Audit");
log("Read-only max fan-out across 24 facts, plan locks, and CI contracts");
let audit_jobs = [
    audit_job("audit-ship-dev", "fact-ship-dev: Is HEAD on branch dev? Does git status show tracking origin/dev? Confirm origin/main is not being updated by this goal (no local checkout of main, no commits targeting main)."),
    audit_job("audit-banner", "fact-banner-pin / B1-B3: Do .github/assets/img/banner.svg and banner-dark.svg match origin/main bytes? Does profile-updater.yml omit generate banner? Is there a hash/skip test in tests/test_profile_workflow.py?"),
    audit_job("audit-lowlighter-maximal", "fact-lowlighter-maximal / L2: Production Personal metrics (not probe) has plugin_habits yes, plugin_calendar_limit 0, plugin_languages_threshold 0%, raised topics/stars/people. Cite the production with: block only."),
    audit_job("audit-lowlighter-off", "fact-lowlighter-off: Production plugin_music, plugin_tweets, plugin_activity are no. Spotify/X/activity are not lowlighter panels."),
    audit_job("audit-lowlighter-retry", "fact-lowlighter-retry / L4: plugin_lines, plugin_achievements, plugin_gists are off on primary unless isolated onto extra/fourth artifact with passing validate. A stub is not accepted."),
    audit_job("audit-lowlighter-audit", "fact-lowlighter-audit / L3: scripts/metrics_svg.py validate/recover rejects stub or will-be-regenerated bars. metrics.extra.svg is a real card, not a tiny stub."),
    audit_job("audit-habits-both", "fact-habits-both: Production primary plugin_habits yes AND first-party metrics-habits.svg exists with a redesigned renderer in scripts/supplemental_metrics.py."),
    audit_job("audit-habits-split", "fact-habits-split / H1: First-party habits shows focus repos, peak hour, designed streaks, richer layout, SVG dark media. Not a restyle of lowlighter recap."),
    audit_job("audit-remove-feed", "fact-remove-feed / R1-R5: README.md and scripts/readme_sections.py do not embed metrics-activity.svg. Finalize artifact lists omit it. Keep GitHub native feed below the profile README."),
    audit_job("audit-spotify", "fact-spotify / S1: First-party metrics-music.svg is a recent-listens hero with optional compact extras. plugin_music stays no. Spotify never in lowlighter with:."),
    audit_job("audit-living-spine", "fact-living-art-spine / I11: One shared daily spine from account creation to now. validate_snapshot_monotonic_contract exists and is tested. Exact-six living-*.gif remain."),
    audit_job("audit-living-dialects", "fact-living-art-dialects / A1/AR2: Six styles visually distinct. Sequential frame samples or contact sheets exist. Encodings redesigned until accretion is readable. inventory/ or a gallery path must be cited or ok=false."),
    audit_job("audit-no-200", "fact-no-200-copy / R3: README tech-stack summary has no 200+ and no replacement blurb. Tests no longer require View full stack (200+ technologies). Ignore historical composition candidates and starred-list descriptions."),
    audit_job("audit-tech-details", "fact-tech-details: Tech-stack shields stay inside details. WakaTime SVG is a visible open-flow img, not wrapped in details."),
    audit_job("audit-badges-stack", "fact-badges-stack / K2: skills.yaml entries have homepage url. Camo-safe badge stack. Retro/throwback icons when they read. scripts/skills.py + SkillEntry.url."),
    audit_job("audit-badges-qa", "fact-badges-qa / K3: Tests or script assert every generated a href is http(s) and badge URLs stay under MAX_SHIELDS_BADGE_URL_LENGTH. Render/icon coverage exists."),
    audit_job("audit-wordclouds", "fact-wordclouds: Exactly two shipped clouds (topics + languages). Size follows starred-repo share. CI uploads exactly two."),
    audit_job("audit-wordcloud-bakeoff", "fact-wordcloud-bakeoff / C1-C3: Bake-off evidence exists (tests/test_word_clouds.py test_svg_engine_bakeoff_typographic_best_encodes_volume or equivalent). Winners readable light/dark."),
    audit_job("audit-waka-svg", "fact-waka-svg / WK1-WK3: scripts/wakatime_svg.py exists. Collector fetches weekly/yearly/all-time if API allows. Visible SVG with languages, professional editors, Mac/iOS/watch, categories, totals, heatmap if available. No anmol098."),
    audit_job("audit-waka-privacy", "fact-waka-privacy / WK4: Privacy filter drops file paths, heartbeats, private projects, leisure/social/health/shopping/entertainment. Tests reject banned categories/names."),
    audit_job("audit-blog", "fact-blog / BL1: Latest Blog Posts is a visible 4-5 RSS card strip from w4w.dev with title, date, one-line hook, link. Not inside details."),
    audit_job("audit-views", "fact-views / V1: Footer still has incrementing komarev (or equivalent) view count, restyled to match badge family. No new view-counter backend in workflows."),
    audit_job("audit-density", "fact-density: README is maximal-data-with-hierarchy, not a wall. Primary cards first, dense detail second. First-party widgets look designed. Cite section order."),
    audit_job("audit-inventory", "Wave I inventory: goals/profile-readme-overhaul/inventory/ should contain I01-I13 notes. Empty inventory is a gap unless a later harvest document replaces it."),
    audit_job("audit-workflow-contracts", "profile-updater.yml contracts: no generate banner; activity artifact gone from finalize; Waka SVG generate+apply; living-art exact-six; word-cloud exactly two; finalize sole git writer; production plugin matrix matches facts."),
    audit_job("audit-auto-verify", "Every facts-result.json fact with automatedVerification true has a named test, workflow assert, hash, or render QA. List any MISSING fact ids."),
];
let audit_res = parallel(audit_jobs);
let audit_fail = failed_labels(audit_res, audit_jobs);
let audit_gaps = collect_gaps(audit_res);
let audit_ok = count_ok(audit_res);
log("Audit " + audit_ok.to_string() + "/" + audit_jobs.len().to_string() + " closed. Failures: " + json_encode(audit_fail));

if dry {
    let report = "";
    report += "# profile-readme-overhaul dry-run audit\n\n";
    report += "ok=";
    report += audit_ok.to_string();
    report += "/";
    report += audit_jobs.len().to_string();
    report += "\n\n## gaps\n\n";
    report += audit_gaps;
    let path = write_scratch_file("audit-report.md", report);
    complete(#{
        path: path,
        summary: "Dry-run audit only; no close/validate/assure.",
        audit_ok: audit_ok,
        audit_total: audit_jobs.len(),
        gaps: audit_gaps,
    });
}

// --- Close ---
phase("Close");
log("Check-then-fix remaining gaps on disjoint leases");
let encoded_gaps = json_encode(audit_gaps);
let close_jobs = [
    closer(
        "close-banner-wf",
        "Keep CI from regenerating banners; pin generate-assets to committed pair",
        ".github/workflows/profile-updater.yml, tests/test_profile_workflow.py",
        "rg generate banner must stay empty. Tests must assert no CI banner regen and hash-pin against origin/main pair if files exist. Do not rewrite banner.svg bytes here (that is close-banner-assets). Audit gaps JSON: " + encoded_gaps,
    ),
    closer(
        "close-banner-assets",
        "Ensure committed banner pair equals origin/main bytes",
        ".github/assets/img/banner.svg, .github/assets/img/banner-dark.svg",
        "If hashes already match origin/main, ALREADY_DONE. Only copy origin/main bytes if they differ. Never invent a new banner.",
    ),
    closer(
        "close-readme-contracts",
        "README contracts: no activity embed, bare Tech Stack summary, visible Waka img, visible blog strip",
        "scripts/readme_sections.py, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py",
        "Do not emit metrics-activity. Tech-stack summary is a bare label. Waka not in details. Blog 4-5 cards with date+hook, not details. Keep generate path working.",
    ),
    closer(
        "close-supplemental",
        "First-party habits + Spotify + stop generating activity",
        "scripts/supplemental_metrics.py, tests/test_supplemental_metrics.py",
        "Habits: focus repos, peak hour, designed streaks, dark media, not a lowlighter clone. Spotify: striking recent-listens hero + compact extras only if beautiful. activity spec should not write metrics-activity.svg. plugin_music stays off in workflow tests.",
    ),
    closer(
        "close-metrics-svg",
        "Reject stub/error-bar extra/primary metrics",
        "scripts/metrics_svg.py, tests/test_metrics_svg.py",
        "validate/recover must fail closed on will-be-regenerated / stub / error bars. Extra card is not an accepted 401-byte stub.",
    ),
    closer(
        "close-waka",
        "First-party Waka SVG: ranges, privacy, visible embed path",
        "scripts/wakatime_readme.py, scripts/wakatime_svg.py, tests/test_wakatime_svg.py, tests/test_wakatime_readme.py",
        "Weekly+yearly+all-time if API allows. Languages, professional editors, Mac/iOS/watch, categories, totals, heatmap if available. Filter private projects, file paths, heartbeats, leisure/social/health/shopping/entertainment. No anmol098.",
    ),
    closer(
        "close-badges",
        "Homepage urls, camo-safe stack, URL-length and href tests",
        "skills.yaml, scripts/skills.py, scripts/config.py, tests/test_skills.py",
        "Every skill has homepage url. Badge URLs under MAX_SHIELDS_BADGE_URL_LENGTH. Generated a href non-empty http(s). Prefer retro icons that still read at badge size. GitHub-camo-safe delivery.",
    ),
    closer(
        "close-wordclouds",
        "Bake-off volume fidelity and exact-two CI contract",
        "scripts/word_clouds/, tests/test_word_clouds.py, tests/test_word_cloud_coverage.py",
        "Keep exactly two shipped SVGs. Size/intensity follows starred-repo share. Keep or add bake-off test that volume wins. Do not add more public clouds.",
    ),
    closer(
        "close-art",
        "Shared daily spine plus readable accretion encodings",
        "scripts/art/, tests/test_living_art_media.py, docs/content/docs/scripts/living-art-modes.mdx",
        "One daily spine account-creation-to-now. Exact-six GIF contract. Styles stay distinct. If encodings already share the spine and monotonic tests pass, ALREADY_DONE unless a real unreadability bug is evidenced. Do not regenerate the full 120-frame fleet unless a contract is broken.",
    ),
    closer(
        "close-views-footer",
        "Restyle incrementing view chip; no new backend",
        "README.md, scripts/readme_sections.py",
        "Keep komarev or equivalent incrementer. Style should match badge family (for-the-badge / current footer). Do not add a new service in .github/workflows.",
    ),
    closer(
        "close-inventory",
        "Land Wave I inventory notes so the graph has artifacts",
        "goals/profile-readme-overhaul/inventory/",
        "Write one markdown file per I01-I13 summarizing current-tree evidence (not speculation). If files already exist and are current, ALREADY_DONE. Do not invent unverified hashes.",
    ),
    closer(
        "close-auto-verify",
        "Add missing automatedVerification tests for accepted facts",
        "tests/test_profile_workflow.py, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py, tests/test_wakatime_svg.py, tests/test_skills.py, tests/test_word_clouds.py, tests/test_living_art_media.py, tests/test_supplemental_metrics.py, tests/test_metrics_svg.py",
        "Each automatedVerification fact needs a named assert. Do not add tests that require live secrets or origin/main mutation. Audit gaps JSON: " + encoded_gaps,
    ),
];
let close_res = parallel(close_jobs);
let close_fail = failed_labels(close_res, close_jobs);
if close_fail.len() > 0 { log("Close failures: " + json_encode(close_fail)); }

// --- Validate ---
phase("Validate");
let val_p = standing();
val_p += "TASK validate: Run focused pytest for touched modules, then report exact commands and exit codes. ";
val_p += "Required: uv run python -m pytest -q tests/test_profile_workflow.py tests/test_readme_sections.py tests/test_readme_gfm_ux.py tests/test_supplemental_metrics.py tests/test_wakatime_svg.py tests/test_wakatime_readme.py tests/test_skills.py tests/test_word_clouds.py tests/test_living_art_media.py -q --tb=line. ";
val_p += "If test_metrics_svg.py exists, include it. If a file is missing, skip that path and say so. ";
val_p += "Also rg: generate banner must be absent from profile-updater.yml; anmol098 absent from scripts/; plugin_music: no on production. ";
val_p += "WRITE_LEASE: goals/profile-readme-overhaul/inventory/validate.md only, to record commands and exit codes. Do not hide failures.";
let val = agent(val_p, #{ label: "validate-gates", capability_mode: "all", agent_type: "general-purpose" });
if val == () || !val.success { log("Validate agent failed"); }

// --- Assure ---
phase("Assure");
log("Adversarial done-condition panel");
let assure_jobs = [
    audit_job("assure-dev-only", "Confirm work stays on dev and main is not updated. ok=true only if HEAD is dev and there is no local intent to push main."),
    audit_job("assure-banner", "Banner pair equals origin/main and CI does not generate banner. ok=true only with hash or documented pin test evidence."),
    audit_job("assure-lowlighter", "Production habits on, music/tweets/activity off, calendar 0, languages 0%, extra not a stub. Cite YAML and metrics_svg."),
    audit_job("assure-habits-split", "First-party habits still has focus/peak/streaks and is not a lowlighter clone."),
    audit_job("assure-feed-200", "No live metrics-activity embed. No 200+ teaser on README tech-stack summary."),
    audit_job("assure-spotify", "Music card exists or degrades cleanly; plugin_music no; no Spotify in lowlighter with:."),
    audit_job("assure-waka", "Visible first-party Waka SVG, privacy filter tested, no anmol098, not inside details."),
    audit_job("assure-badges", "Every skill url + badge length/href tests. Tech stack remains in details."),
    audit_job("assure-clouds", "Exactly two clouds; volume bake-off test present; CI uploads two."),
    audit_job("assure-blog-views", "Blog strip visible with date+hook; view counter incrementer present; no new backend."),
    audit_job("assure-art", "Exact-six GIFs, shared daily spine, monotonic test. Frame-inspection evidence or honest remaining gap."),
    audit_job("assure-tests", "automatedVerification facts have named checks. List any still-missing fact ids in gaps."),
    audit_job("assure-density", "README hierarchy is designed (primary then dense), not an undifferentiated wall."),
];
let assure_res = parallel(assure_jobs);
let assure_ok = count_ok(assure_res);
let assure_gaps = collect_gaps(assure_res);
log("Assure " + assure_ok.to_string() + "/" + assure_jobs.len().to_string());

// --- Repair ---
phase("Repair");
let need_repair = assure_ok < assure_jobs.len();
if need_repair {
    log("Assure not fully closed; launching targeted repair panel");
    let encoded_assure = json_encode(assure_gaps);
    let repair_jobs = [
        closer(
            "repair-workflow-tests",
            "Repair remaining workflow / metrics_svg / banner-pin test gaps",
            ".github/workflows/profile-updater.yml, tests/test_profile_workflow.py, scripts/metrics_svg.py, tests/test_metrics_svg.py",
            "Fix only real remaining gaps. Assure gaps JSON: " + encoded_assure,
        ),
        closer(
            "repair-readme-surfaces",
            "Repair remaining README section / blog / Waka / teaser gaps",
            "scripts/readme_sections.py, tests/test_readme_sections.py, tests/test_readme_gfm_ux.py",
            "Fix only real remaining gaps. Assure gaps JSON: " + encoded_assure,
        ),
        closer(
            "repair-first-party-cards",
            "Repair remaining habits/Spotify/activity supplemental gaps",
            "scripts/supplemental_metrics.py, tests/test_supplemental_metrics.py",
            "Fix only real remaining gaps. Assure gaps JSON: " + encoded_assure,
        ),
        closer(
            "repair-waka-badges",
            "Repair remaining Waka privacy/SVG and badge QA gaps",
            "scripts/wakatime_readme.py, scripts/wakatime_svg.py, tests/test_wakatime_svg.py, tests/test_wakatime_readme.py, skills.yaml, scripts/skills.py, tests/test_skills.py",
            "Fix only real remaining gaps. Assure gaps JSON: " + encoded_assure,
        ),
        closer(
            "repair-clouds-art",
            "Repair remaining word-cloud bake-off and living-art contract gaps",
            "scripts/word_clouds/, tests/test_word_clouds.py, scripts/art/, tests/test_living_art_media.py",
            "Do not regenerate the full GIF fleet unless contract tests fail. Assure gaps JSON: " + encoded_assure,
        ),
        closer(
            "repair-inventory-verify",
            "Repair inventory notes and any leftover automatedVerification holes",
            "goals/profile-readme-overhaul/inventory/, tests/",
            "Write missing I01-I13 notes and only the tests still missing for automatedVerification facts. Assure gaps JSON: " + encoded_assure,
        ),
    ];
    let repair_res = parallel(repair_jobs);
    let repair_fail = failed_labels(repair_res, repair_jobs);
    if repair_fail.len() > 0 { log("Repair failures: " + json_encode(repair_fail)); }
} else {
    log("Assure closed; skipping repair panel");
}

let summary = "";
summary += "audit ";
summary += audit_ok.to_string();
summary += "/";
summary += audit_jobs.len().to_string();
summary += "; assure ";
summary += assure_ok.to_string();
summary += "/";
summary += assure_jobs.len().to_string();

let report = "";
report += "# profile-readme-overhaul audit-complete\n\n";
report += summary;
report += "\n\n## audit gaps\n\n";
report += audit_gaps;
report += "\n\n## assure gaps\n\n";
report += assure_gaps;
let path = write_scratch_file("completion-report.md", report);
complete(#{
    path: path,
    summary: summary,
    audit_ok: audit_ok,
    audit_total: audit_jobs.len(),
    assure_ok: assure_ok,
    assure_total: assure_jobs.len(),
    close_failures: close_fail,
});
