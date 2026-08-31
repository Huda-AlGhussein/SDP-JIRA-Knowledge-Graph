"""
scan_issue_link_types.py

Purpose: extract the COMPLETE, exact list of issue-link type labels used
across all 16 repositories, with counts, before designing any
normalization mapping. No mapping decisions are made here, this is pure
inspection.

Assumption stated explicitly (unverified against actual documents):
Each entry in fields.issuelinks is expected to look like:
    {
      "type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
      "outwardIssue": {...}   # OR "inwardIssue": {...}, depending on direction
    }
If this structure doesn't match what's actually in the data, this script
will report a "malformed_link_entries" count rather than silently
skipping or crashing, so we know to adjust field names.

This scan covers ALL 16 repositories (including IntelDAOS, JiraEcosystem,
Sakai, which were excluded from developer profiling due to identity field
incompatibility). Link-type normalization does not depend on developer
identity, so there's no reason to exclude them here.

Output:
  - issue_link_types_full.csv: one row per distinct (name, inward, outward)
    combination, with total count and list of repositories it appears in
  - Printed summary: top labels by count, plus malformed entry count

Usage:
    python scan_issue_link_types.py
"""

from pymongo import MongoClient
from collections import defaultdict
import csv

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
OUTPUT_CSV = "issue_link_types_full.csv"


def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    all_collections = sorted(db.list_collection_names())
    print(f"Scanning {len(all_collections)} collections: {all_collections}\n")

    # key: (name, inward, outward) -> {"count": int, "repos": set(), "directions": {"inward": n, "outward": n}}
    label_stats = defaultdict(lambda: {"count": 0, "repos": set(), "inward_count": 0, "outward_count": 0})

    total_issues_scanned = 0
    total_link_entries = 0
    malformed_link_entries = 0
    issues_with_links = 0

    for coll_name in all_collections:
        coll = db[coll_name]
        cursor = coll.find({"fields.issuelinks": {"$exists": True, "$ne": []}}, {"fields.issuelinks": 1})

        for doc in cursor:
            total_issues_scanned += 1
            links = doc.get("fields", {}).get("issuelinks", [])
            if not links:
                continue
            issues_with_links += 1

            for link in links:
                total_link_entries += 1
                type_obj = link.get("type")
                if not type_obj or "name" not in type_obj:
                    malformed_link_entries += 1
                    continue

                name = type_obj.get("name")
                inward = type_obj.get("inward")
                outward = type_obj.get("outward")
                key = (name, inward, outward)

                label_stats[key]["count"] += 1
                label_stats[key]["repos"].add(coll_name)

                if "inwardIssue" in link:
                    label_stats[key]["inward_count"] += 1
                elif "outwardIssue" in link:
                    label_stats[key]["outward_count"] += 1

    print(f"Total issues scanned (across all collections): {total_issues_scanned}")
    print(f"Issues with at least one link: {issues_with_links}")
    print(f"Total individual link entries found: {total_link_entries}")
    print(f"Malformed link entries (missing type/name): {malformed_link_entries}")
    print(f"Distinct (name, inward, outward) combinations found: {len(label_stats)}\n")

    # sort by count descending
    sorted_labels = sorted(label_stats.items(), key=lambda kv: kv[1]["count"], reverse=True)

    print("Top 20 labels by count:")
    for (name, inward, outward), stats in sorted_labels[:20]:
        print(f"  {stats['count']:>7}  name={name!r}  inward={inward!r}  outward={outward!r}  "
              f"repos={sorted(stats['repos'])}")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "inward_label", "outward_label", "total_count",
                          "inward_direction_count", "outward_direction_count",
                          "num_repositories", "repositories"])
        for (name, inward, outward), stats in sorted_labels:
            writer.writerow([
                name, inward, outward, stats["count"],
                stats["inward_count"], stats["outward_count"],
                len(stats["repos"]), ";".join(sorted(stats["repos"]))
            ])

    print(f"\nFull table ({len(sorted_labels)} rows) written to {OUTPUT_CSV}")
    client.close()


if __name__ == "__main__":
    main()