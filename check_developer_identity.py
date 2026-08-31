"""
Stage 0 check: is developer identity consistent within a repository?

Two things this script does:

1. Print the FULL structure of assignee/creator/reporter (and one comment
   author, if present) from a few sample documents in one collection, so we
   can see exactly which field is meant to represent identity (e.g. an
   anonymized accountId/key) after the dataset's UUID4 masking.

2. Once we know which field that is, count how many DISTINCT values of the
   other fields (e.g. displayName) are associated with each identifier
   value, across a larger sample. If a single identifier maps to more than
   one set of other field values, that is a sign identity is NOT stable
   within the repository, which would undermine building a developer
   profile at all. If each identifier maps to exactly one consistent set
   of other fields, identity looks stable.

Assumptions stated explicitly:
- Only checks ONE collection (Apache, the largest) as a pilot, not all 16.
  Anonymization behavior could differ by repository, so this is a first
  signal, not a guarantee for the full dataset.
- Uses a sample of N documents (see SAMPLE_SIZE below), not the full
  collection, for speed. This is a preliminary check, not exhaustive.
- Checks assignee, creator, and reporter fields specifically, since those
  are the three person-roles we saw consistently in the schema so far.
"""

from pymongo import MongoClient
from collections import defaultdict
import json

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
COLLECTION_TO_CHECK = "Apache"
SAMPLE_SIZE = 2000

def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]
    coll = db[COLLECTION_TO_CHECK]

    print(f"=== PART 1: Full structure of person fields (3 sample docs) ===\n")
    samples = list(coll.find().limit(3))
    for i, doc in enumerate(samples):
        fields = doc.get("fields", {})
        print(f"--- Sample document {i+1} (key={doc.get('key')}) ---")
        for role in ["assignee", "creator", "reporter"]:
            val = fields.get(role)
            print(f"{role}: {json.dumps(val, indent=2, default=str)}")
        comments = fields.get("comments", [])
        if comments:
            print(f"comments[0].author: {json.dumps(comments[0].get('author'), indent=2, default=str)}")
        else:
            print("comments: (empty)")
        print()

    print(f"\n=== PART 2: Identity consistency check over {SAMPLE_SIZE} documents ===\n")
    print("NOTE: adjust IDENTITY_FIELD below once Part 1 output shows which")
    print("field actually represents the anonymized identity (e.g. 'key',")
    print("'accountId', or 'name'). Defaulting to 'key' as a first guess.\n")

    IDENTITY_FIELD = "key"       # <-- adjust after seeing Part 1 output
    DISPLAY_FIELD = "displayName"  # <-- adjust after seeing Part 1 output

    identity_to_display_values = defaultdict(set)
    checked = 0
    missing_field_count = 0

    cursor = coll.find().limit(SAMPLE_SIZE)
    for doc in cursor:
        fields = doc.get("fields", {})
        for role in ["assignee", "creator", "reporter"]:
            person = fields.get(role)
            if not person:
                continue
            identity_val = person.get(IDENTITY_FIELD)
            display_val = person.get(DISPLAY_FIELD)
            if identity_val is None:
                missing_field_count += 1
                continue
            identity_to_display_values[identity_val].add(display_val)
            checked += 1

    inconsistent = {k: v for k, v in identity_to_display_values.items() if len(v) > 1}

    print(f"Person-role references checked: {checked}")
    print(f"References missing '{IDENTITY_FIELD}' field: {missing_field_count}")
    print(f"Distinct identity values seen: {len(identity_to_display_values)}")
    print(f"Identity values with MORE THAN ONE distinct '{DISPLAY_FIELD}': {len(inconsistent)}")

    if inconsistent:
        print("\nExamples of inconsistent identities (up to 5):")
        for k, v in list(inconsistent.items())[:5]:
            print(f"  {IDENTITY_FIELD}={k} -> {v}")
    else:
        print(f"\nNo inconsistencies found in this sample: every '{IDENTITY_FIELD}' ")
        print(f"value mapped to exactly one '{DISPLAY_FIELD}' value.")

    client.close()


if __name__ == "__main__":
    main()