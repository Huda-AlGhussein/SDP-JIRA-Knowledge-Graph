"""
Stage 1: full-collection statistics.

For each of the 16 repository collections, count (over ALL documents, not
a sample) how many issues have:
  - a non-null assignee
  - at least one comment
  - at least one issuelink
  - at least one changelog history entry

This tells us how richly connected the data really is, which determines
whether the resulting knowledge graph will be densely linked or mostly
isolated nodes. This replaces the earlier single-document sampling, which
could not answer that question reliably.

Assumptions stated explicitly:
- "Has an assignee" means fields.assignee is not null/missing. It does NOT
  check whether the assignee is a real distinct person vs. some default
  system value, since we have not looked into that yet.
- Counts are exact (using MongoDB's countDocuments with a filter), not
  estimates, but will take longer to run than the earlier sampling script
  since every document in every collection is scanned. No indexes exist
  beyond the default _id index (confirmed during restore), so these are
  full collection scans.
"""

from pymongo import MongoClient

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"

def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    collections = sorted(db.list_collection_names())

    print(f"{'Collection':<15} {'Total':>10} {'HasAssignee':>12} {'HasComments':>12} {'HasLinks':>10} {'HasHistory':>11}")
    print("-" * 75)

    totals = {"total": 0, "assignee": 0, "comments": 0, "links": 0, "history": 0}

    for coll_name in collections:
        coll = db[coll_name]

        total = coll.count_documents({})
        has_assignee = coll.count_documents({"fields.assignee": {"$ne": None}})
        has_comments = coll.count_documents({"fields.comments.0": {"$exists": True}})
        has_links = coll.count_documents({"fields.issuelinks.0": {"$exists": True}})
        has_history = coll.count_documents({"changelog.histories.0": {"$exists": True}})

        totals["total"] += total
        totals["assignee"] += has_assignee
        totals["comments"] += has_comments
        totals["links"] += has_links
        totals["history"] += has_history

        def pct(n, d):
            return f"{n} ({100*n/d:.1f}%)" if d else f"{n} (n/a)"

        print(f"{coll_name:<15} {total:>10} {pct(has_assignee, total):>12} {pct(has_comments, total):>12} {pct(has_links, total):>10} {pct(has_history, total):>11}")

    print("-" * 75)
    t = totals["total"]
    print(f"{'TOTAL':<15} {t:>10} "
          f"{totals['assignee']} ({100*totals['assignee']/t:.1f}%){'':>1} "
          f"{totals['comments']} ({100*totals['comments']/t:.1f}%){'':>1} "
          f"{totals['links']} ({100*totals['links']/t:.1f}%) "
          f"{totals['history']} ({100*totals['history']/t:.1f}%)")

    client.close()


if __name__ == "__main__":
    main()