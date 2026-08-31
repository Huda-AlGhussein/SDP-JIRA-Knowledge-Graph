# Developer / Issue Knowledge Graph from Public Jira Repositories

Handover documentation. Last working day of the original author: **2026-08-31**.

---

## 1. Project purpose

Build a knowledge graph (and, later, a Graph Neural Network on top of it) over
the **Public Jira Dataset** (16 public Jira repositories, ~2.7M issues) to
support **developer and issue recommendation** — e.g. recommending an assignee
for an issue, or surfacing related issues.

The work so far is the **data-understanding and graph-construction pipeline**
that precedes any GNN modelling: verifying developer identity, aggregating
per-developer activity profiles, flagging bot accounts, normalizing the messy
raw issue-link vocabulary into a clean category set, and building a first
prototype graph for one repository (Apache).

Supporting research material (literature survey, slide deck) is included under
"Research artefacts" below.

---

## 2. Current project status

**Prototype / exploratory stage.** The pipeline runs end to end for a single
repository (Apache) and produces a NetworkX graph object. It has **not** been
extended to all 13 identity-compatible repositories, comment nodes are not yet
wired in, and **no GNN has been built yet**.

All scripts are standalone and were run against a **local MongoDB restore** of
the dataset. Nothing writes back to MongoDB — every script reads Mongo and/or
local `.jsonl` files and writes new local files.

---

## 3. What has been completed

| Stage | Script | Output | Notes |
|------|--------|--------|-------|
| Schema inspection | `inspect_jira.py` | `output/schema_output.txt` | One sample doc per collection, field types/shape. |
| Connectivity stats | `full_collection_stats.py` | `output/full_stats_output.txt` | Per-collection counts of issues with assignee / comments / links / changelog. |
| Identity check (within repo) | `check_developer_identity.py` | `output/identity_check_output.txt` | Confirms the anonymized `key` field is stable within a repository. |
| Identity check (cross repo) | `check_cross_repo_identity.py` | `output/cross_repo_identity_output.txt`, `cross_repo_identity_output2.txt` | Same person keeps the same `key` across the 13 compatible repos. |
| Missing-identity follow-up | `check_missing_identity_fields.py` | `output/missing_identity_output.txt` | IntelDAOS / JiraEcosystem / Sakai use `accountId`, not `key` — **excluded** from identity-linked work. |
| Comments & link-type audit | `check_comments_and_linktypes.py` | `output/comments_and_linktypes_output.txt` | Why MariaDB/Mindville show 0% comments; per-repo issuelink type counts. |
| Link-type scan | `scan_issue_link_types.py` | `issue_link_types_full.csv` | Complete list of raw `(name, inward, outward)` link labels + counts (107 distinct combos). |
| Link-type mapping | `link_type_mapping.py` | *(data module)* | Human-reviewed mapping of all 107 raw combos → 22 canonical categories (+ Gantt excluded). Imported, not run. |
| Link normalization | `normalize_issue_links.py` | `normalized_issue_links.jsonl` *(generated, ~350 MB, git-ignored)* | Applies the mapping to every link in all repos. |
| Developer profiles | `build_developer_profiles.py` | `developer_profiles.jsonl` *(generated, ~207 MB, git-ignored)* | One activity profile per developer across the 13 compatible repos. |
| Profile distributions | `compute_profile_distributions.py` | `output/profile_distribution_output.txt`, `zero_tenure_profiles.jsonl` *(generated, git-ignored)* | Percentiles used to pick bot-flag thresholds (p99.9). |
| Profile summary | `summarize_developer_profiles.py` | *(stdout)* | Sanity-check distribution of the profiles. |
| Bot flagging | `flag_bot_profiles.py` | `developer_profiles_flagged.jsonl` *(generated, ~247 MB, git-ignored)* | Adds `is_likely_bot` / `flags_tripped` (flag-first, nothing dropped). |
| Top-developer bot check | `check_top_developers.py` | *(stdout, run manually)* | Inspect top-20 most active accounts for bot signals. |
| Prototype graph | `build_apache_graph_prototype.py` | `apache_graph_prototype.pkl` *(generated, ~311 MB, git-ignored)*, `apache_graph_sample.png` | Apache-only NetworkX `MultiDiGraph`: Developer + Issue nodes; `reportedBy` / `assignedTo` / `linksTo` edges. Also renders a sample neighborhood PNG. |

The repo contains **15 Python files**: 14 runnable scripts (above) plus
`link_type_mapping.py`, which is a data module imported by
`normalize_issue_links.py`, not run on its own.

Methodological decisions are documented in the module docstring at the top of
each script — **read those first**, they record why each choice was made.

Committed result/output files: everything in `output/`, plus
`cross_repo_identity_output2.txt`, `issue_link_types_full.csv`,
`apache_graph_sample.png`, `Figure_1.png`.

---

## 4. What is still in progress / not done

- **Full-graph build**: only Apache is built. Extend `build_apache_graph_prototype.py`
  to the other 12 identity-compatible repositories.
- **Cross-repository `linksTo` edges** are currently skipped (and counted) when
  the target issue is outside the Apache node set.
- **Comment nodes**: the intended schema (TBox) includes a `Comment` node type;
  it is **not** wired into the graph yet.
- **Changelog / issue history** is not represented in the graph.
- **"Experience" and "domain" features** are rough first proxies only
  (issue counts + tenure in days; set of component/project names) — not
  finalized feature definitions.
- **Bot flagging** is threshold-based (p99.9) and conservative (2-of-3 signals);
  `zero_tenure` profiles can only trip 2 signals. Not validated against ground truth.
- **No GNN / no modelling** has been started. No train/val/test split, no task
  formalization beyond the high-level "developer & issue recommendation" goal.
- The three `accountId`-only repos (IntelDAOS, JiraEcosystem, Sakai) are
  excluded from all identity-linked work.

---

## 5. Project structure

```
GNN/
├── README.md                          <- this file
├── .gitignore
│
├── inspect_jira.py                    <- schema inspection
├── full_collection_stats.py           <- connectivity statistics
├── check_developer_identity.py        <- identity checks
├── check_cross_repo_identity.py
├── check_missing_identity_fields.py
├── check_comments_and_linktypes.py
├── check_top_developers.py
├── scan_issue_link_types.py           <- link-type inventory
├── link_type_mapping.py               <- reviewed raw->canonical link mapping (data module)
├── normalize_issue_links.py           <- apply the mapping (=> normalized_issue_links.jsonl)
├── build_developer_profiles.py        <- per-developer activity profiles
├── compute_profile_distributions.py   <- percentile stats for thresholds
├── summarize_developer_profiles.py    <- sanity-check summary
├── flag_bot_profiles.py               <- add is_likely_bot flag
├── build_apache_graph_prototype.py    <- prototype NetworkX graph (Apache only)
│
├── issue_link_types_full.csv          <- result: full raw link-label inventory
├── cross_repo_identity_output2.txt    <- result: cross-repo identity key counts
├── apache_graph_sample.png            <- result: sample graph neighborhood
├── Figure_1.png                       <- result figure
├── output/                            <- result: captured stdout of the analysis scripts
│   ├── schema_output.txt
│   ├── full_stats_output.txt
│   ├── identity_check_output.txt
│   ├── cross_repo_identity_output.txt
│   ├── missing_identity_output.txt
│   ├── comments_and_linktypes_output.txt
│   └── profile_distribution_output.txt
│
├── GNN-literature.xlsx                <- research: literature survey
└── SDP-15-July-2026.pptx              <- research: project slide deck
```

### NOT in git (see `.gitignore`) — must be obtained/regenerated locally

| Path | ~Size | How to get it |
|------|------|---------------|
| `2025-06-23 ThePublicJiraDataset/` and/or `ThePublicJiraDataset.zip` | ~5.6–5.8 GB | Download the dataset (see §7) |
| `<dataset>/.../3. DataDump/mongodump-JiraReposAnon.archive` | ~5.9 GB | Part of the dataset download |
| `normalized_issue_links.jsonl` | ~350 MB | `python normalize_issue_links.py` |
| `developer_profiles.jsonl` | ~207 MB | `python build_developer_profiles.py` |
| `developer_profiles_flagged.jsonl` | ~247 MB | `python flag_bot_profiles.py` |
| `zero_tenure_profiles.jsonl` | ~144 MB | `python compute_profile_distributions.py` |
| `apache_graph_prototype.pkl` | ~311 MB | `python build_apache_graph_prototype.py` |

None of these need Git LFS **if** they stay ignored. If a future maintainer
wants to version the derived `.jsonl`/`.pkl` outputs, they exceed GitHub's
100 MB hard limit and **would require Git LFS**.

---

## 6. How to run the code

### Prerequisites

1. **MongoDB** running locally at `mongodb://127.0.0.1:27017` (no auth),
   with the dataset restored into a database named `JiraReposAnon`.
2. **Python 3.10** (the profile scripts have a manual timestamp parser
   specifically because 3.10's `datetime.fromisoformat` cannot handle the
   dataset's timezone strings; 3.11+ would also work but is untested here).

### Restore the dataset into MongoDB

```bash
# from the dataset's "3. DataDump" folder
mongorestore --gzip --archive=mongodump-JiraReposAnon.archive
# expands to ~60 GB inside MongoDB
```
(See the dataset's own `3. DataDump/README.md` for the authoritative commands.)

### Install Python dependencies

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install pymongo networkx matplotlib numpy
```

### Run the pipeline (in order)

Run from the repo root, with the MongoDB `JiraReposAnon` database already
restored (see above). Each step depends on the steps before it.
`[GIT-IGNORED]` marks the command that produces each large file **not** stored
in git — running these steps in order regenerates every excluded `.jsonl` /
`.pkl` file from scratch.

```bash
# --- Data understanding (independent; each only reads MongoDB) ---
python inspect_jira.py                       > output/schema_output.txt
python full_collection_stats.py              > output/full_stats_output.txt
python check_developer_identity.py           > output/identity_check_output.txt
python check_cross_repo_identity.py          > output/cross_repo_identity_output.txt
python check_missing_identity_fields.py      > output/missing_identity_output.txt
python check_comments_and_linktypes.py       > output/comments_and_linktypes_output.txt

# --- Issue-link normalization ---
python scan_issue_link_types.py              # -> issue_link_types_full.csv
#   link_type_mapping.py is imported by the next step, not run directly
python normalize_issue_links.py              # [GIT-IGNORED] -> normalized_issue_links.jsonl  (~350 MB)

# --- Developer profiles + bot flagging ---
python build_developer_profiles.py           # [GIT-IGNORED] -> developer_profiles.jsonl  (~207 MB)
python compute_profile_distributions.py      > output/profile_distribution_output.txt
#     also writes  [GIT-IGNORED] -> zero_tenure_profiles.jsonl  (~144 MB)
python summarize_developer_profiles.py       # prints a sanity-check summary; writes nothing
python check_top_developers.py               # optional: prints top-20 accounts for bot inspection
python flag_bot_profiles.py                  # [GIT-IGNORED] -> developer_profiles_flagged.jsonl  (~247 MB)
#   requires: developer_profiles.jsonl

# --- Prototype graph (Apache only) ---
#   requires: normalized_issue_links.jsonl + developer_profiles_flagged.jsonl + MongoDB
python build_apache_graph_prototype.py       # [GIT-IGNORED] -> apache_graph_prototype.pkl  (~311 MB)
                                             #  also writes  -> apache_graph_sample.png  (committed)
```

> **Note on hard-coded paths:** several scripts contain absolute Windows paths
> (`C:\Users\OpenU\GNN\...`), notably `build_apache_graph_prototype.py`.
> Update those constants at the top of the file for your machine. They were
> **left as-is on handover per instruction not to modify research code**.

---

## 7. Datasets required and where to put them

**Dataset:** *An Alternative Issue Tracking Dataset of Public Jira Repositories*
(Montgomery, Lüders, Maalej — MSR 2022). Public. **Not redistributed in this repo.**

Official sources:

- Zenodo record: <https://zenodo.org/records/5901804>
  (DOI: <https://doi.org/10.5281/zenodo.5901804>)
- Paper: <https://mininghubbub.github.io/> / IEEE MSR 2022,
  "An Alternative Issue Tracking Dataset of Public Jira Repositories"
- GitHub (scripts / definitions): <https://github.com/HiEST/JiraDataset>
  *(verify the canonical link on the Zenodo record; the authors also list a
  MariaDB / Mindville note there)*

Expected local layout (matches what the scripts and this repo assumed):

```
GNN/
└── 2025-06-23 ThePublicJiraDataset/
    └── ThePublicJiraDataset/
        ├── 0. DataDefinition/
        │   ├── jira_data_sources.json
        │   ├── jira_field_information.json
        │   ├── jira_issuetype_information.json
        │   ├── jira_issue_linktype_mapping.json
        │   ├── jira_issuetype_thematic_analysis.json
        │   └── May2021/
        ├── 1. DataDownload/DownloadData.ipynb
        ├── 2. OverviewAnalysis/OverviewAnalysis.ipynb
        └── 3. DataDump/
            └── mongodump-JiraReposAnon.archive   <- restore this into MongoDB
```

The scripts do **not** read the dataset files off disk directly (except that
the archive must be restored into MongoDB first). Once MongoDB has the
`JiraReposAnon` database, the exact on-disk folder name does not matter.

**Anonymization:** person records in the dataset are already anonymized by the
dataset authors (UUID4 masks, e.g. `<<|author_key|<uuid>|>>`). No further
personal data is present or produced.

---

## 8. Important result / output locations

- `output/*.txt` — captured analysis results (schema, connectivity, identity, link types, distributions).
- `output/profile_distribution_output.txt` — **the percentile numbers behind the bot-flag thresholds** in `flag_bot_profiles.py` (total_activity ≥ 3252, actions_per_day ≥ 12, num_projects ≥ 28).
- `issue_link_types_full.csv` — full raw link-label inventory feeding `link_type_mapping.py`.
- `cross_repo_identity_output2.txt` — per-repo distinct identity-key counts; shows which repos use `accountId`.
- `apache_graph_sample.png` — visual sanity check of the prototype graph.
- `Figure_1.png` — project figure.
- Generated (git-ignored) big outputs: `apache_graph_prototype.pkl`,
  `developer_profiles*.jsonl`, `normalized_issue_links.jsonl`,
  `zero_tenure_profiles.jsonl`.

---

## 9. Known unfinished tasks / limitations

1. Graph is **Apache-only**; extend to all 13 identity-compatible repos.
2. **Cross-repo `linksTo` edges skipped** in the prototype (counted, not dropped).
3. **Comment nodes and changelog history not in the graph.**
4. **No GNN / modelling** started — no task formalization, no data splits.
5. Feature definitions ("experience", "domain") are **rough proxies**, not final.
6. **Bot detection unvalidated** — threshold heuristic only; zero-tenure profiles
   evaluated on 2 signals instead of 3.
7. **Hard-coded absolute paths** in several scripts (esp. `build_apache_graph_prototype.py`).
8. `build_apache_graph_prototype.py` has a second script accidentally appended
   below its `__main__` block (the graph-visualization code starting at the
   stray `import pickle`). It still executes because it follows the graph save,
   but it should be split into its own file. **Left as-is per "do not modify
   research code" instruction — flagging for the next maintainer.**
9. IntelDAOS / JiraEcosystem / Sakai excluded from identity-linked work.
10. MariaDB and Mindville are no longer available online (per dataset authors);
    only the May 2021 meta-information covers them.

---

