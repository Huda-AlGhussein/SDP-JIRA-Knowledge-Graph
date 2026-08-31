"""
Check the top N most active developers for signs of being automated bot
accounts rather than real humans, before this feeds into clustering.

Rationale: the summary showed the single most active developer had
95,572 total actions against an average of 12.63 -- a huge outlier.
Public issue trackers commonly have bot accounts (CI systems, migration
scripts, auto-linking tools) that dwarf human activity levels. If bots
are left in the developer pool, they will distort clustering (e.g.
appear as "most experienced" when they are not a person at all).

This script just prints the top 20 most active developer profiles in
full, so we can eyeball them: unusually high activity concentrated in a
single repository, an unusually narrow date range for such high volume
(bots often act fast/continuously), or an implausible number of distinct
issue types touched, are all signs worth a closer look. This does NOT
attempt to programmatically detect bots (display names are anonymized
tokens here, so we cannot check for "bot" in the name as one normally
would) -- it surfaces the data for a human judgment call instead.
"""

import json

INPUT_PATH = "developer_profiles.jsonl"
TOP_N = 20

def main():
    profiles = []
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            profiles.append(json.loads(line))

    profiles.sort(key=lambda r: r["total_activity"], reverse=True)

    print(f"Top {TOP_N} most active developers:\n")
    for rec in profiles[:TOP_N]:
        print(f"developer_id: {rec['developer_id']}")
        print(f"  total_activity: {rec['total_activity']} "
              f"(assignee={rec['assignee_count']}, creator={rec['creator_count']}, reporter={rec['reporter_count']})")
        print(f"  repositories ({rec['num_repositories']}): {rec['repositories']}")
        print(f"  date range: {rec['first_seen']} to {rec['last_seen']}")
        print(f"  num_components: {rec['num_components']}, num_projects: {rec['num_projects']}")
        print(f"  issuetypes: {rec['issuetypes']}")
        print()


if __name__ == "__main__":
    main()