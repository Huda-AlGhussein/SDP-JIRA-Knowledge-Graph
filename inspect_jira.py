"""
Inspect the schema of the JiraReposAnon MongoDB database.

Purpose: for each of the 16 repository collections, pull one sample
document and print its top-level field names, types, and a preview
of nested structure. This is a first pass to identify candidate
node types, edge types, and node features for a knowledge graph.

Assumptions stated explicitly:
- Connects to localhost:27017 (default, no auth) — matches the
  MongoDB service currently running on this machine.
- Only ONE sample document is inspected per collection. A single
  document is not guaranteed to represent the full schema if fields
  vary across documents (e.g. optional fields, different issue types
  with different custom fields). This is a starting point, not a
  complete schema definition.
- No filtering/sampling strategy applied (e.g. random sampling) —
  this pulls whatever document MongoDB returns first for speed.
"""

from pymongo import MongoClient
import json

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"

def describe_value(value, depth=0, max_depth=2):
    """Return a short type/shape description of a value, recursing into
    dicts and lists up to max_depth so we can see nested structure
    without dumping entire documents."""
    indent = "  " * depth
    if isinstance(value, dict):
        if depth >= max_depth:
            return f"{indent}dict (nested, {len(value)} keys) [not expanded further]"
        lines = [f"{indent}dict ({len(value)} keys):"]
        for k, v in value.items():
            lines.append(f"{indent}  {k}: {describe_value(v, depth + 1, max_depth)}")
        return "\n".join(lines)
    elif isinstance(value, list):
        if len(value) == 0:
            return f"{indent}list (empty)"
        first_item_desc = describe_value(value[0], depth + 1, max_depth)
        return f"{indent}list (length {len(value)}), first item:\n{first_item_desc}"
    else:
        type_name = type(value).__name__
        preview = str(value)
        if len(preview) > 80:
            preview = preview[:80] + "..."
        return f"{type_name} = {preview}"


def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    collections = sorted(db.list_collection_names())
    print(f"Found {len(collections)} collections in '{DB_NAME}':")
    print(collections)
    print("=" * 80)

    for coll_name in collections:
        coll = db[coll_name]
        doc_count = coll.count_documents({})
        sample = coll.find_one()

        print(f"\nCOLLECTION: {coll_name}")
        print(f"Document count: {doc_count}")

        if sample is None:
            print("No documents found (empty collection).")
            continue

        print("Top-level fields:")
        for field, value in sample.items():
            print(f"  {field}: {describe_value(value, depth=1)}")

        print("-" * 80)

    client.close()


if __name__ == "__main__":
    main()