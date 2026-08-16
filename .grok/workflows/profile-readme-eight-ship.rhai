let meta = #{
    name: "profile-readme-eight-ship",
    description: "After the eight README polish items are on origin/dev, watch CI and the Unified Profile Updater, then adversarially assure the live origin/dev README",
    when_to_use: "Finish shipping the eight-item README polish on branch dev. Never use this to touch main, remint Spotify, or commit leftovers.",
    phases: [
        #{ title: "Watch", detail: "read-only status of latest CI and updater on origin/dev" },
        #{ title: "Assure", detail: "eight live origin/dev contracts plus leftover-exclusion" },
    ],
};

let watch_schema = #{
    "type": "object",
    "required": ["branch", "head", "ci_ok", "updater_ok", "ci_summary", "updater_summary"],
    "properties": #{
        "branch": #{ "type": "string" },
        "head": #{ "type": "string" },
        "ci_ok": #{ "type": "boolean" },
        "updater_ok": #{ "type": "boolean" },
        "ci_summary": #{ "type": "string" },
        "updater_summary": #{ "type": "string" },
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

fn hard_rules() {
    let s = "";
    s += "HARD: stay on branch dev; never checkout, merge, or edit origin/main or branch main; never commit or push; never print secrets; never git reset/stash/discard. ";
    s += "Repo /Users/ww/dev/projects/wyattowalsh. Inspect origin/dev and GitHub Actions with git fetch / gh / curl. ";
    s += "Do not edit files. Do not remint Spotify tokens. ";
    return s;
}

phase("Watch");
let wp = hard_rules();
wp += "WRITE_LEASE none. Fetch origin/dev. Report branch, origin/dev HEAD sha, latest CI run on that SHA, and latest Unified Profile Updater run. ";
wp += "ci_ok true only if the newest CI on origin/dev HEAD succeeded. updater_ok true only if the newest updater on that SHA succeeded (or is still in_progress with Finalize not failed — then say so and set updater_ok false). ";
wp += "Paste exact gh run ids and conclusions in the summaries.";
let watch = agent(wp, #{
    label: "watch-ci-updater",
    capability_mode: "execute",
    agent_type: "general-purpose",
    output_schema: watch_schema,
});

phase("Assure");
let items = [
    "origin/dev README featured cards are exactly the eight named repos and listentropy/mdxpad are absent",
    "origin/dev README uses unique ornamental sep-*.svg plus comment headings and has no visible ##",
    "origin/dev first-party music/habits/languages/waka widgets are width 100 percent",
    "origin/dev title is My Tech Stack in README summary and skills.yaml",
    "origin/dev word clouds are outside tech-stack details as stacked 100 percent typographic SVGs",
    "origin/dev generate-assets uses --renderer typographic and shipped cloud fills have no #D97706",
    "origin/dev blog has Latest Blog Posts sep and no extra text-link row under cards",
    "origin/dev footer keeps komarev username=wyattowalsh and views-peek.svg",
];
let jobs = [];
let i = 0;
for it in items {
    let p = hard_rules();
    p += "WRITE_LEASE none. Fetch if needed. Adversarially verify this live origin/dev claim by reading git show origin/dev:... or raw.githubusercontent.com wyattowalsh/wyattowalsh/dev files, not memory: ";
    p += it;
    p += " Set ok=true only with concrete evidence you independently inspected.";
    jobs.push(#{
        prompt: p,
        label: "assure-" + i.to_string(),
        capability_mode: "read-only",
        output_schema: assure_schema,
    });
    i += 1;
}
let res = parallel(jobs);
let ok = 0;
let notes = "";
let ai = 0;
for r in res {
    if r != () && r.success && r.output != () && r.output.ok == true
        && r.output.evidence != () && r.output.evidence != "" {
        ok += 1;
        notes += "- PASS ";
    } else {
        notes += "- FAIL ";
    }
    if r != () && r.success && r.output != () {
        notes += r.output.item;
        notes += " — ";
        if r.output.evidence != () { notes += r.output.evidence; }
    } else {
        notes += items[ai];
        notes += " — unverified slot";
    }
    notes += "\n";
    ai += 1;
}

let report = "# profile-readme-eight-ship\n\n## Watch\n";
if watch.success && watch.output != () {
    report += watch.output.ci_summary;
    report += "\n";
    report += watch.output.updater_summary;
    report += "\nhead=";
    report += watch.output.head;
    report += " ci_ok=";
    if watch.output.ci_ok != () && watch.output.ci_ok == true { report += "true"; } else { report += "false"; }
    report += " updater_ok=";
    if watch.output.updater_ok != () && watch.output.updater_ok == true { report += "true"; } else { report += "false"; }
} else {
    report += "watch agent failed";
}
report += "\n\n## Assure\n";
report += notes;
let path = write_scratch_file("eight-ship-report.md", report);
complete(#{
    path: path,
    assure_ok: ok,
    assure_total: 8,
    ci_ok: watch.success && watch.output != () && watch.output.ci_ok != () && watch.output.ci_ok == true,
    updater_ok: watch.success && watch.output != () && watch.output.updater_ok != () && watch.output.updater_ok == true,
});
