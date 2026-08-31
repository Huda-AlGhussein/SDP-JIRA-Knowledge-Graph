"""
Stage 2: Developer activity aggregation.

Builds one activity profile per developer (identified by their 'key'
field, confirmed stable within and across the 13 compatible
repositories), combining data from all 13 at once.

For each developer, we collect:
  - total issues where they were assignee, creator, or reporter
    (counted separately, since these are different relationships to an
    issue, not interchangeable)
  - which repositories they appear in (a person active in many repos
    looks different from one active in a single repo)
  - which components/projects they touched, as a rough proxy for "domain"
  - which issue types they touched (bug, task, story, etc.)
  - earliest and latest activity timestamp seen, as a rough proxy for
    "experience" (tenure), separate from raw issue count

This is written to a local file (developer_profiles.jsonl) rather than
printed, since with tens of thousands of developers the output would be
far too large to review as terminal text. One JSON object per line, one
line per developer.

EXCLUDED REPOSITORIES: IntelDAOS, JiraEcosystem, Sakai. These use a
different identity field (accountId) that cannot be reliably matched to
the 'key' field used by the other 13, so including them here would risk
silently treating two different real people as one, or splitting one
real person into two profiles. This exclusion was a deliberate decision,
not an oversight.

Assumptions stated explicitly:
- "Experience" here is only a rough first proxy: (issue_count, tenure in
  days between first and last seen timestamp). This is NOT a finalized
  definition, just a starting point for clustering to react to.
- "Domain" here is only a rough first proxy: the set of distinct
  component names and project names touched. Component/project names are
  NOT anonymized in this dataset in the same way people are (they are
  real, e.g. "HTTP Client", "Core"), so this should be directly usable,
  but has not yet been separately verified for consistency.
- A developer's assignee/creator/reporter roles on a given issue are
  counted independently, so a person who is both creator AND reporter on
  the same issue is counted once in each category, not deduplicated
  across categories. This mirrors how Jira itself treats these as
  distinct roles.
- Timestamps are parsed from the issue's 'created' field only. Jira
  timestamp strings include a timezone offset already (e.g.
  '2019-05-10T02:55:41.828-0500'), which Python's datetime.fromisoformat
  can parse directly in Python 3.11+, but in 3.10 (confirmed version on
  this machine) fromisoformat cannot handle all these formats reliably,
  so a manual parse is used instead. If a timestamp fails to parse, that
  single data point is skipped rather than the whole document.
"""

from pymongo import MongoClient
from collections import defaultdict
import json
import re

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
EXCLUDED_COLLECTIONS = {"IntelDAOS", "JiraEcosystem", "Sakai"}
OUTPUT_PATH = "developer_profiles.jsonl"

ROLES = ["assignee", "creator", "reporter"]

TIMESTAMP_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})")

def parse_created_date(created_str):
    """Extract just (year, month, day) as a sortable tuple, ignoring time
    and timezone, since we only need coarse tenure, not precise timing."""
    if not created_str:
        return None
    m = TIMESTAMP_RE.match(created_str)
    if not m:
        return None
    year, month, day = m.group(1), m.group(2), m.group(3)
    return f"{year}-{month}-{day}"


def get_identity(person):
    if not person:
        return None
    return person.get("key") or person.get("accountId")


def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    all_collections = sorted(db.list_collection_names())
    target_collections = [c for c in all_collections if c not in EXCLUDED_COLLECTIONS]

    print(f"Processing {len(target_collections)} collections (excluded: {sorted(EXCLUDED_COLLECTIONS)})")

    # developer_id -> profile dict
    profiles = defaultdict(lambda: {
        "assignee_count": 0,
        "creator_count": 0,
        "reporter_count": 0,
        "repositories": set(),
        "components": set(),
        "projects": set(),
        "issuetypes": set(),
        "first_seen": None,
        "last_seen": None,
    })

    for coll_name in target_collections:
        coll = db[coll_name]
        total = coll.count_documents({})
        print(f"  {coll_name}: {total} documents")

        cursor = coll.find({}, {
            "fields.assignee.key": 1, "fields.assignee.accountId": 1,
            "fields.creator.key": 1, "fields.creator.accountId": 1,
            "fields.reporter.key": 1, "fields.reporter.accountId": 1,
            "fields.components": 1,
            "fields.project.key": 1,
            "fields.issuetype.name": 1,
            "fields.created": 1,
        })

        for doc in cursor:
            fields = doc.get("fields", {})
            created_date = parse_created_date(fields.get("created"))
            components = {c.get("name") for c in fields.get("components", []) if c.get("name")}
            project = fields.get("project", {}).get("key")
            issuetype = fields.get("issuetype", {}).get("name")

            for role, count_key in [("assignee", "assignee_count"),
                                     ("creator", "creator_count"),
                                     ("reporter", "reporter_count")]:
                person = fields.get(role)
                dev_id = get_identity(person)
                if not dev_id:
                    continue

                profile = profiles[dev_id]
                profile[count_key] += 1
                profile["repositories"].add(coll_name)
                if components:
                    profile["components"].update(components)
                if project:
                    profile["projects"].add(project)
                if issuetype:
                    profile["issuetypes"].add(issuetype)
                if created_date:
                    if profile["first_seen"] is None or created_date < profile["first_seen"]:
                        profile["first_seen"] = created_date
                    if profile["last_seen"] is None or created_date > profile["last_seen"]:
                        profile["last_seen"] = created_date

    print(f"\nTotal distinct developers found: {len(profiles)}")
    print(f"Writing profiles to {OUTPUT_PATH} ...")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for dev_id, profile in profiles.items():
            record = {
                "developer_id": dev_id,
                "assignee_count": profile["assignee_count"],
                "creator_count": profile["creator_count"],
                "reporter_count": profile["reporter_count"],
                "total_activity": profile["assignee_count"] + profile["creator_count"] + profile["reporter_count"],
                "num_repositories": len(profile["repositories"]),
                "repositories": sorted(profile["repositories"]),
                "num_components": len(profile["components"]),
                "components": sorted(profile["components"]),
                "num_projects": len(profile["projects"]),
                "projects": sorted(profile["projects"]),
                "issuetypes": sorted(profile["issuetypes"]),
                "first_seen": profile["first_seen"],
                "last_seen": profile["last_seen"],
            }
            f.write(json.dumps(record) + "\n")

    print("Done.")
    client.close()


if __name__ == "__main__":
    main()