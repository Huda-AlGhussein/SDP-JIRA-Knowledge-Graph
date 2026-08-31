"""
Two checks:

PART 1: Investigate why MariaDB and Mindville showed 0.0% comments in the
full-collection stats. We look at one document from each that we'd expect
to plausibly have discussion (an older, non-trivial issue) and print the
raw 'comments' field and nearby fields, to see whether comments are
genuinely absent or stored under a different structure/field name.

PART 2: For each of the 16 collections, count how many issues have each
distinct issuelinks TYPE (e.g. "Duplicate", "Blocks", "Relates"), since
that determines whether Issue-to-Issue edges should be a single generic
edge type or several distinct typed edges in the knowledge graph.

Assumptions stated explicitly:
- Part 1 only inspects a handful of documents per collection, not a
  systematic search, to conserve time. If this doesn't explain the
  anomaly, we'll need a more targeted follow-up.
- Part 2 counts link TYPE NAMES as they appear in the data (e.g. the
  'name' field under each link's type object). It does not distinguish
  inward vs outward link direction in the counts, only type names.
"""

from pymongo import MongoClient
from collections import Counter
import json

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"

def part1_check_comments_anomaly(db):
    print("=== PART 1: MariaDB / Mindville comments check ===\n")
    for coll_name in ["MariaDB", "Mindville"]:
        coll = db[coll_name]
        print(f"--- {coll_name} ---")
        # Look at a few documents, not just the very first, in case the
        # first happens to be atypical
        docs = list(coll.find().limit(5))
        for doc in docs:
            fields = doc.get("fields", {})
            comments_val = fields.get("comments", "FIELD NOT PRESENT")
            comment_field_keys = [k for k in fields.keys() if "comment" in k.lower()]
            print(f"  key={doc.get('key')}  comments field value: {json.dumps(comments_val, default=str)}")
            print(f"  fields containing 'comment' in name: {comment_field_keys}")
        print()

def part2_issuelink_types(db):
    print("\n=== PART 2: Issue link types per collection ===\n")
    collections = sorted(db.list_collection_names())

    grand_total_counter = Counter()

    for coll_name in collections:
        coll = db[coll_name]
        type_counter = Counter()

        cursor = coll.find(
            {"fields.issuelinks.0": {"$exists": True}},
            {"fields.issuelinks": 1}
        )
        docs_with_links = 0
        for doc in cursor:
            docs_with_links += 1
            links = doc.get("fields", {}).get("issuelinks", [])
            for link in links:
                link_type = link.get("type", {})
                type_name = link_type.get("name", "UNKNOWN")
                type_counter[type_name] += 1

        print(f"--- {coll_name} ({docs_with_links} issues with links) ---")
        for type_name, count in type_counter.most_common():
            print(f"  {type_name}: {count}")
            grand_total_counter[type_name] += count
        print()

    print("=== Grand total link type counts across all 16 collections ===")
    for type_name, count in grand_total_counter.most_common():
        print(f"  {type_name}: {count}")


def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    part1_check_comments_anomaly(db)
    part2_issuelink_types(db)

    client.close()


if __name__ == "__main__":
    main()