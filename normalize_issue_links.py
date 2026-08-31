"""
normalize_issue_links.py

Purpose: apply the finalized mapping in link_type_mapping.py to every
issue link across all 16 repositories, and write the result to a
SEPARATE output file (normalized_issue_links.jsonl). The original
MongoDB collections are not modified in any way.

Requires link_type_mapping.py to be in the same directory (imported,
not run directly).

For each issue with at least one link, writes one JSON line:
{
  "issue_key": "...",         # from fields... or _id if no key field
  "repository": "...",
  "links": [
    {
      "canonical_category": "Blocks",
      "direction": "inward" | "outward",
      "raw_name": "Blocker",                # kept for traceability/audit
      "linked_issue_key": "..."             # the other issue in the link, if present
    },
    ...
  ]
}

Issues whose links are ALL excluded (Gantt/scheduling) are still written,
with an empty "links" list, so issue counts stay auditable (we don't want
issues silently disappearing from the output because every one of their
links happened to be excluded).

Any raw (name, inward, outward) combination NOT found in LINK_TYPE_MAP
is treated as an error, not silently skipped: it is counted and printed
at the end, and that specific link entry is excluded from the output
with a note, so nothing gets a wrong or guessed category.

Usage:
    python normalize_issue_links.py
"""

from pymongo import MongoClient
from collections import defaultdict
import json

from link_type_mapping import LINK_TYPE_MAP, DIRECTION_SWAP_LABELS

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
OUTPUT_PATH = "normalized_issue_links.jsonl"


def get_issue_key(doc):
    # Prefer the human-facing Jira key if present, fall back to Mongo _id
    return doc.get("key") or str(doc.get("_id"))


def get_linked_issue_key(link, direction):
    other = link.get("inwardIssue") if direction == "outward" else link.get("outwardIssue")
    # NOTE: if this link IS the inward record, the related issue is under "outwardIssue"? 
    # Jira's convention: a link entry has EITHER "inwardIssue" OR "outwardIssue" naming
    # the OTHER issue on the far end of that specific relationship record.
    # We already determine `direction` from which key is present, so just read whichever is there.
    if "inwardIssue" in link:
        other = link["inwardIssue"]
    elif "outwardIssue" in link:
        other = link["outwardIssue"]
    else:
        return None
    if not other:
        return None
    return other.get("key")


def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]
    all_collections = sorted(db.list_collection_names())

    print(f"Processing {len(all_collections)} collections: {all_collections}\n")

    total_issues_written = 0
    total_links_written = 0
    total_links_excluded_gantt = 0
    total_links_unmapped = 0
    unmapped_combos = defaultdict(int)
    category_counts = defaultdict(int)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as outfile:
        for coll_name in all_collections:
            coll = db[coll_name]
            cursor = coll.find({}, {
                "key": 1,
                "fields.issuelinks": 1,
            })

            for doc in cursor:
                issue_key = get_issue_key(doc)
                raw_links = doc.get("fields", {}).get("issuelinks", [])

                normalized_links = []

                for link in raw_links:
                    type_obj = link.get("type", {})
                    name = type_obj.get("name")
                    inward = type_obj.get("inward")
                    outward = type_obj.get("outward")
                    if outward:
                        outward = outward.strip()  # fixes the IntelDAOS trailing-space case generically

                    key = (name, inward, outward)

                    # Determine direction and possibly swap for the one flagged label
                    if key in DIRECTION_SWAP_LABELS:
                        if "inwardIssue" in link:
                            link = {**link, "outwardIssue": link.pop("inwardIssue")}
                        elif "outwardIssue" in link:
                            link = {**link, "inwardIssue": link.pop("outwardIssue")}

                    if "inwardIssue" in link:
                        direction = "inward"
                    elif "outwardIssue" in link:
                        direction = "outward"
                    else:
                        direction = None

                    if key not in LINK_TYPE_MAP:
                        total_links_unmapped += 1
                        unmapped_combos[key] += 1
                        continue

                    canonical = LINK_TYPE_MAP[key]
                    if canonical is None:
                        total_links_excluded_gantt += 1
                        continue

                    linked_key = get_linked_issue_key(link, direction)

                    normalized_links.append({
                        "canonical_category": canonical,
                        "direction": direction,
                        "raw_name": name,
                        "linked_issue_key": linked_key,
                    })
                    category_counts[canonical] += 1
                    total_links_written += 1

                record = {
                    "issue_key": issue_key,
                    "repository": coll_name,
                    "links": normalized_links,
                }
                outfile.write(json.dumps(record) + "\n")
                total_issues_written += 1

    print(f"Total issues written: {total_issues_written}")
    print(f"Total normalized links written: {total_links_written}")
    print(f"Total links excluded (Gantt/scheduling): {total_links_excluded_gantt}")
    print(f"Total links UNMAPPED (not found in LINK_TYPE_MAP): {total_links_unmapped}")

    if unmapped_combos:
        print("\nWARNING: the following combinations were not in LINK_TYPE_MAP and were skipped:")
        for combo, count in sorted(unmapped_combos.items(), key=lambda kv: kv[1], reverse=True):
            print(f"  {count:>6}  {combo}")
        print("\nThese need to be added to link_type_mapping.py and this script re-run.")
    else:
        print("\nNo unmapped combinations found. Every link in the dataset was covered by the mapping.")

    print("\nCanonical category counts:")
    for cat, count in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {count:>7}  {cat}")

    print(f"\nOutput written to {OUTPUT_PATH}")
    client.close()


if __name__ == "__main__":
    main()