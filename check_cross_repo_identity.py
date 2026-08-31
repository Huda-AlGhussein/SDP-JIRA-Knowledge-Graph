"""
Stage 0b: Is developer identity consistent ACROSS repositories, not just
within one?

We already confirmed (Stage 0, on Apache alone) that a person keeps the
same anonymized 'key' every time they appear within that one repository.
This script checks the harder question: if a real person contributed to,
say, both Apache and Hyperledger, would they show up with the SAME key in
both collections, or would each repository have anonymized them
independently (meaning the same person looks like two different people
once you combine repos)?

Method:
- For every collection, collect the set of distinct identity values seen
  in assignee/creator/reporter fields, using EITHER the 'key' field
  (older Jira Server/Data Center format) OR the 'accountId' field (newer
  Jira Cloud format), whichever is present on a given person record. A
  follow-up check confirmed IntelDAOS, JiraEcosystem, and Sakai use
  'accountId' exclusively while the other 13 collections use 'key'.
- Check how much overlap exists between each pair of collections' identity
  sets. If real people work across multiple repos, we would expect some
  overlap. If there is ZERO overlap between any two collections, that is
  evidence each repository was anonymized independently, meaning
  identities are NOT safe to merge across those two repos as-is.

Assumptions stated explicitly:
- 'key' and 'accountId' are treated as equivalent identity fields, never
  compared against each other (a 'key'-based repo will never overlap with
  an 'accountId'-based repo by construction, since they are different
  anonymization schemes/fields). This means the 3 accountId-based repos
  (IntelDAOS, JiraEcosystem, Sakai) can only show overlap WITH EACH OTHER,
  not with the other 13. That is a real limitation of this dataset's
  export formats, not a bug in this script.
- If overlap is genuinely zero between two repos that use the SAME field
  type (both 'key' or both 'accountId'), we cannot distinguish "no shared
  contributors exist" from "anonymization was done independently per
  repo" using this data alone.
- Uses the FULL set of distinct identity values per collection (not a
  sample), since this only requires listing distinct values, not
  repeatedly scanning nested structures.
"""

from pymongo import MongoClient

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
ROLES = ["assignee", "creator", "reporter"]

def get_identity_keys(coll):
    keys = set()
    cursor = coll.find(
        {},
        {f"fields.{role}.key": 1 for role in ROLES}
        | {f"fields.{role}.accountId": 1 for role in ROLES}
    )
    for doc in cursor:
        fields = doc.get("fields", {})
        for role in ROLES:
            person = fields.get(role)
            if not person:
                continue
            identity_val = person.get("key") or person.get("accountId")
            if identity_val:
                keys.add(identity_val)
    return keys

def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]
    collections = sorted(db.list_collection_names())

    print("Collecting distinct identity keys per collection (this may take a few minutes)...\n")

    keys_by_collection = {}
    for coll_name in collections:
        keys = get_identity_keys(db[coll_name])
        keys_by_collection[coll_name] = keys
        # show one example key so we can visually compare formats across repos
        example = next(iter(keys)) if keys else "(none found)"
        print(f"{coll_name:<15} distinct keys: {len(keys):>7}   example: {example}")

    print("\n=== Pairwise overlap between collections ===\n")
    print(f"{'Collection A':<15} {'Collection B':<15} {'Overlap count':>13}")
    print("-" * 45)

    total_overlaps = 0
    any_overlap_found = False
    for i, a in enumerate(collections):
        for b in collections[i+1:]:
            overlap = keys_by_collection[a] & keys_by_collection[b]
            if len(overlap) > 0:
                any_overlap_found = True
                total_overlaps += len(overlap)
                print(f"{a:<15} {b:<15} {len(overlap):>13}")

    if not any_overlap_found:
        print("(no overlapping keys found between any pair of collections)")

    print(f"\nTotal overlapping key instances across all pairs: {total_overlaps}")

    client.close()


if __name__ == "__main__":
    main()