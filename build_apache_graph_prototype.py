"""
Prototype knowledge graph builder, Apache repository only.

Methodological choices (stated explicitly, not buried in the code):

1. Scope: Apache repository only, for a same-day working prototype.
   Not all 13 repositories. Revisit scope once this is validated.

2. Developer nodes: filtered from developer_profiles_flagged.jsonl to
   developers with "Apache" in their repositories list. A developer's
   profile reflects their activity across ALL repos they touched, not
   just Apache, since profiles were built per-developer, not per-repo.

3. Issue nodes: pulled live from MongoDB (JiraReposAnon.Apache), not a
   separate export, so counts reflect your currently restored dataset.

4. linksTo edges: built strictly from normalized_issue_links.jsonl, your
   validated 22-category mapping. NOT re-derived from raw MongoDB
   issuelinks, to avoid redoing work you already normalized and checked.

5. Cross-repository links: if a link's target issue key is not present
   in this Apache-only node set (e.g. it points to a cross-project
   issue), the edge is SKIPPED and counted, not silently dropped. This
   is a scope boundary of the prototype, not a data quality judgment.
   Revisit when building the full 13-repository graph.

6. Reporter / assignee: read from fields.reporter.key and
   fields.assignee.key. Issues with no assignee produce no assignedTo
   edge, this is expected, not an error.

7. Developer-issue key matching: developer_profiles_flagged.jsonl and
   MongoDB author fields both use the same anonymized token format
   (<<|author_key|UUID|>>), confirmed consistent with your earlier
   identity checks. No transformation is applied here.

8. Comment nodes are NOT included in this prototype. The TBox includes
   Comment, but wiring it in is left for the next iteration, not
   silently skipped, flagged here on purpose.

Requires: pymongo, networkx
    pip install pymongo networkx
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

import json
import pickle
from pymongo import MongoClient
import networkx as nx

MONGO_URI = "mongodb://127.0.0.1:27017"
DB_NAME = "JiraReposAnon"
REPO = "Apache"

LINKS_PATH = BASE_DIR / "normalized_issue_links.jsonl"
DEV_PROFILES_PATH = BASE_DIR / "developer_profiles_flagged.jsonl"
OUTPUT_PATH = BASE_DIR / "apache_graph_prototype.pkl"


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def build_graph():
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][REPO]

    G = nx.MultiDiGraph()

    dev_count = 0
    for dev in load_jsonl(DEV_PROFILES_PATH):
        if REPO in dev.get("repositories", []):
            G.add_node(
                dev["developer_id"],
                node_type="Developer",
                first_seen=dev.get("first_seen"),
                last_seen=dev.get("last_seen"),
                is_likely_bot=dev.get("is_likely_bot"),
                total_activity=dev.get("total_activity"),
            )
            dev_count += 1
    print(f"Developer nodes added: {dev_count}")

    issue_count = 0
    reported_edges = 0
    assigned_edges = 0
    cursor = collection.find(
        {},
        {
            "key": 1,
            "fields.issuetype.name": 1,
            "fields.status.name": 1,
            "fields.priority.name": 1,
            "fields.created": 1,
            "fields.updated": 1,
            "fields.reporter.key": 1,
            "fields.assignee.key": 1,
        },
    )
    for doc in cursor:
        key = doc.get("key")
        if not key:
            continue
        fields = doc.get("fields", {})
        G.add_node(
            key,
            node_type="Issue",
            issue_type=(fields.get("issuetype") or {}).get("name"),
            status=(fields.get("status") or {}).get("name"),
            priority=(fields.get("priority") or {}).get("name"),
            created=fields.get("created"),
            updated=fields.get("updated"),
        )
        issue_count += 1

        reporter = fields.get("reporter") or {}
        reporter_key = reporter.get("key")
        if reporter_key:
            G.add_edge(key, reporter_key, edge_type="reportedBy")
            reported_edges += 1

        assignee = fields.get("assignee") or {}
        assignee_key = assignee.get("key")
        if assignee_key:
            G.add_edge(key, assignee_key, edge_type="assignedTo")
            assigned_edges += 1

    print(f"Issue nodes added: {issue_count}")
    print(f"reportedBy edges: {reported_edges}")
    print(f"assignedTo edges: {assigned_edges}")

    links_added = 0
    links_skipped_out_of_scope = 0
    for record in load_jsonl(LINKS_PATH):
        if record.get("repository") != REPO:
            continue
        src = record.get("issue_key")
        if src not in G:
            continue
        for link in record.get("links", []):
            tgt = link.get("linked_issue_key")
            if tgt not in G:
                links_skipped_out_of_scope += 1
                continue
            G.add_edge(
                src,
                tgt,
                edge_type="linksTo",
                link_category=link.get("canonical_category"),
                direction=link.get("direction"),
            )
            links_added += 1

    print(f"linksTo edges added: {links_added}")
    print(f"linksTo edges skipped (target outside Apache scope): {links_skipped_out_of_scope}")

    return G


if __name__ == "__main__":
    graph = build_graph()
    print(f"\nTotal nodes: {graph.number_of_nodes()}")
    print(f"Total edges: {graph.number_of_edges()}")

    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(graph, f)
    print(f"Graph saved to {OUTPUT_PATH}")


    import pickle
import networkx as nx
import matplotlib.pyplot as plt
 
GRAPH_PATH = BASE_DIR / "apache_graph_prototype.pkl"
OUTPUT_IMAGE = BASE_DIR / "apache_graph_sample.png"
MIN_LINKS = 3
 
with open(GRAPH_PATH, "rb") as f:
    G = pickle.load(f)
 
target_issue = None
for node, data in G.nodes(data=True):
    if data.get("node_type") != "Issue":
        continue
    link_count = sum(
        1 for _, _, d in G.out_edges(node, data=True)
        if d.get("edge_type") == "linksTo"
    )
    if link_count >= MIN_LINKS:
        target_issue = node
        break
 
if target_issue is None:
    raise SystemExit(f"No issue found with at least {MIN_LINKS} linksTo edges, lower MIN_LINKS and retry.")
 
sub_nodes = {target_issue}
for _, neighbor, data in G.out_edges(target_issue, data=True):
    sub_nodes.add(neighbor)
for neighbor, _, data in G.in_edges(target_issue, data=True):
    sub_nodes.add(neighbor)
 
sub = G.subgraph(sub_nodes)
 
color_map = {"Issue": "#5DCAA5", "Developer": "#85B7EB"}
node_colors = [color_map.get(sub.nodes[n].get("node_type"), "#B4B2A9") for n in sub.nodes]
labels = {
    n: (n if sub.nodes[n].get("node_type") == "Issue" else "Developer")
    for n in sub.nodes
}
 
pos = nx.spring_layout(sub, seed=42)
plt.figure(figsize=(9, 7))
nx.draw(
    sub, pos, with_labels=True, labels=labels, node_color=node_colors,
    node_size=1400, font_size=8, edge_color="#888780", width=1,
)
edge_labels = {
    (u, v): d.get("edge_type") for u, v, d in sub.edges(data=True)
}
nx.draw_networkx_edge_labels(sub, pos, edge_labels=edge_labels, font_size=7)
plt.title(f"Sample neighborhood: {target_issue}")
plt.axis("off")
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=200)
print(f"Saved to {OUTPUT_IMAGE}")
plt.show()
 