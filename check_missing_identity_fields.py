"""
Follow-up: IntelDAOS, JiraEcosystem, and Sakai showed ZERO distinct 'key'
values in the cross-repo identity check. This likely means these three
collections use a different field for person identity (e.g. 'accountId'
instead of 'key'/'name'), possibly reflecting a newer Jira Cloud export
format. This script prints the FULL raw assignee/creator/reporter
structure from a few documents in each of these three collections so we
can see what field is actually being used.
"""

from pymongo import MongoClient
import json

DB_NAME = "JiraReposAnon"
CLIENT_URI = "mongodb://127.0.0.1:27017/"
COLLECTIONS_TO_CHECK = ["IntelDAOS", "JiraEcosystem", "Sakai"]

def main():
    client = MongoClient(CLIENT_URI)
    db = client[DB_NAME]

    for coll_name in COLLECTIONS_TO_CHECK:
        coll = db[coll_name]
        print(f"=== {coll_name} ===\n")
        docs = list(coll.find().limit(3))
        for doc in docs:
            fields = doc.get("fields", {})
            print(f"--- key={doc.get('key')} ---")
            for role in ["assignee", "creator", "reporter"]:
                val = fields.get(role)
                print(f"{role}: {json.dumps(val, indent=2, default=str)}")
            print()
        print("-" * 60)

    client.close()


if __name__ == "__main__":
    main()