# Graph-Based Developer Recommendation — Research Handover

## 1. Project overview

This project uses the **Public Jira Dataset** (16 public Jira repositories, ~2.7M issues)
to construct a developer/issue **knowledge graph** intended to support future work on
developer recommendation and automated bug assignment (e.g. suggesting an assignee for a
new issue, or surfacing related issues). The pipeline verifies developer identity across
repositories, normalizes the raw issue-link vocabulary, aggregates per-developer activity
profiles, flags likely bot accounts, and builds a first NetworkX graph for one repository
(Apache). The project is currently at the **data preparation and knowledge graph prototype
stage**. No GNN or recommendation model has been built or trained.

## 2. Current status

| Component | Status |
|---|---|
| Jira dataset exploration | Complete |
| Developer identity analysis | Complete |
| Issue-link normalization | Complete |
| Developer profile construction | Complete |
| Bot-account flagging | Prototype complete |
| Knowledge graph | Apache prototype complete |
| Full multi-repository graph | Not completed |
| GNN / recommendation model | Not started |

Methodological decisions (scope choices, exclusions, threshold rationale, direction
handling) are documented in the docstring at the top of each script. Read those before
changing anything.

## 3. Important code files — START HERE

These files are the research pipeline, in dependency order (run top to bottom):

| File | Run directly? | Purpose |
|---|---|---|
| `scan_issue_link_types.py` | **Yes** | Scans raw Jira issue-link types and produces the mapping inventory |
| `link_type_mapping.py` | **No** | Human-reviewed raw → canonical link mapping |
| `normalize_issue_links.py` | **Yes** | Applies the mapping to all issue links |
| `build_developer_profiles.py` | **Yes** | Builds developer activity profiles |
| `compute_profile_distributions.py` | **Yes** | Computes distributions used for bot thresholds |
| `flag_bot_profiles.py` | **Yes** | Adds likely-bot flags |
| `build_apache_graph_prototype.py` | **Yes** | Builds the Apache knowledge-graph prototype |

### Supporting / exploratory scripts

Not part of the pipeline output; used to understand and validate the data:

- `inspect_jira.py` — samples one document per collection, prints field types/shape.
- `full_collection_stats.py` — per-repo counts of issues with assignee / comments / links / changelog.
- `check_developer_identity.py`, `check_cross_repo_identity.py`, `check_missing_identity_fields.py`
  — confirm the anonymized `key` field is stable within and across repos; identify the three
  repos (IntelDAOS, JiraEcosystem, Sakai) that use `accountId` instead and are excluded.
- `check_comments_and_linktypes.py` — explains the 0% comment repos; per-repo link-type counts.
- `summarize_developer_profiles.py` — sanity-check summary of the developer profiles.
- `check_top_developers.py` — inspects the top-20 most active accounts for bot signals.

## 4. Quick start / What to run

```
Public Jira Dataset → MongoDB → link normalization → developer profiles → bot flagging → Apache graph
```

### Prerequisites

- **MongoDB** running locally at `mongodb://127.0.0.1:27017` (no auth).
- The dataset's MongoDB dump **restored into a database named `JiraReposAnon`** (see §7).
- **Python 3.10** (the profile scripts use a manual timestamp parser specifically for 3.10).
  Install dependencies: `pip install pymongo networkx matplotlib numpy`
- **Hard-coded paths:** `build_apache_graph_prototype.py` has absolute
  `C:\Users\OpenU\GNN\...` paths in the constants at the top of the file. Update these
  paths for your machine before running.

### Optional data-understanding checks

```
python inspect_jira.py                  > output/schema_output.txt
python full_collection_stats.py         > output/full_stats_output.txt
python check_developer_identity.py      > output/identity_check_output.txt
python check_cross_repo_identity.py     > output/cross_repo_identity_output.txt
python check_missing_identity_fields.py > output/missing_identity_output.txt
python check_comments_and_linktypes.py  > output/comments_and_linktypes_output.txt
```

### Main pipeline

Run from the repo root, in this order. Each step depends on the ones before it.

```
python scan_issue_link_types.py
python normalize_issue_links.py
python build_developer_profiles.py
python compute_profile_distributions.py
python flag_bot_profiles.py
python build_apache_graph_prototype.py
```

`link_type_mapping.py` is imported by `normalize_issue_links.py` and **must not be run
directly**.

## 5. Existing outputs

Committed results:

- `issue_link_types_full.csv` — complete raw issue-link label inventory (107 distinct combos).
- `output/profile_distribution_output.txt` — the percentile numbers behind the bot-flag
  thresholds in `flag_bot_profiles.py`.
- `apache_graph_sample.png` — sample neighborhood from the Apache prototype graph.
- `output/` — captured stdout of the data-understanding scripts (schema, stats, identity, comments).
- `cross_repo_identity_output2.txt` — per-repo distinct identity-key counts.

Large generated files, excluded from Git (regenerate with the pipeline in §4):

| File | Produced by |
|---|---|
| `normalized_issue_links.jsonl` (~350 MB) | `normalize_issue_links.py` |
| `developer_profiles.jsonl` (~207 MB) | `build_developer_profiles.py` |
| `zero_tenure_profiles.jsonl` (~144 MB) | `compute_profile_distributions.py` |
| `developer_profiles_flagged.jsonl` (~247 MB) | `flag_bot_profiles.py` |
| `apache_graph_prototype.pkl` (~311 MB) | `build_apache_graph_prototype.py` |

## 6. Important unfinished work

State of the project at handover:

- The knowledge graph covers the Apache repository only.
- The full multi-repository graph has not been built; cross-repository `linksTo` edges are
  currently skipped (and counted) in the prototype.
- Comment nodes and changelog/issue-history information are not incorporated into the graph.
- Developer features ("experience" as issue counts + tenure in days, "domain" as component/
  project name sets) are preliminary proxies, not finalized definitions.
- The bot-flagging heuristic is threshold-based (p99.9, 2-of-3 signals) and has not been
  validated against ground truth.
- No GNN or recommendation model has been built or evaluated; there is no task
  formalization or train/validation/test split.

## 7. Dataset

**An Alternative Issue Tracking Dataset of Public Jira Repositories** (Montgomery, Lüders,
Maalej — IEEE/ACM MSR 2022). Public dataset. Not redistributed in this repository.

- Zenodo: <https://zenodo.org/records/5901804> (DOI: <https://doi.org/10.5281/zenodo.5901804>)

Download the dataset and restore its MongoDB archive (from the `3. DataDump` folder) into a
local database named `JiraReposAnon`:

```
mongorestore --gzip --archive=mongodump-JiraReposAnon.archive
```

Expanded, the data is ~60 GB inside MongoDB. Person records are already anonymized by the
dataset authors (UUID4 masks, e.g. `<<|author_key|<uuid>|>>`). Once `JiraReposAnon` exists,
the scripts read from MongoDB directly and the dataset's on-disk location no longer matters.
The three `accountId`-only repos (IntelDAOS, JiraEcosystem, Sakai) are excluded from all
identity-linked work; MariaDB and Mindville are no longer available online (per the dataset
authors) and are only covered by the May 2021 meta-information.

## 8. Research material

- `GNN-literature.xlsx` — literature survey on graph neural networks / recommendation.
- `SDP-15-July-2026.pptx` — project slide deck.
