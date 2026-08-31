"""
Sanity-check summary of developer_profiles.jsonl.

Prints distribution statistics so we can judge whether the 528,155
developer profiles look reasonable before using them for clustering:
  - distribution of total_activity (how many developers are "one-off"
    vs. heavily active)
  - how many developers appear in more than one repository
  - distribution of num_components (domain breadth)
  - basic checks for obviously broken records (e.g. missing dates)

This does not modify developer_profiles.jsonl, only reads it.
"""

import json
from collections import Counter

INPUT_PATH = "developer_profiles.jsonl"

def bucket_activity(n):
    if n == 1:
        return "1 (one-off)"
    elif n <= 5:
        return "2-5"
    elif n <= 20:
        return "6-20"
    elif n <= 100:
        return "21-100"
    else:
        return "100+"

def main():
    total_devs = 0
    activity_buckets = Counter()
    repo_count_buckets = Counter()
    component_count_buckets = Counter()
    missing_dates = 0
    total_activity_sum = 0
    max_activity = 0
    max_activity_dev = None

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            total_devs += 1

            total_activity = rec["total_activity"]
            total_activity_sum += total_activity
            activity_buckets[bucket_activity(total_activity)] += 1

            if total_activity > max_activity:
                max_activity = total_activity
                max_activity_dev = rec["developer_id"]

            n_repos = rec["num_repositories"]
            repo_count_buckets[n_repos if n_repos <= 5 else "6+"] += 1

            n_comp = rec["num_components"]
            if n_comp == 0:
                component_count_buckets["0"] += 1
            elif n_comp <= 3:
                component_count_buckets["1-3"] += 1
            elif n_comp <= 10:
                component_count_buckets["4-10"] += 1
            else:
                component_count_buckets["11+"] += 1

            if not rec["first_seen"] or not rec["last_seen"]:
                missing_dates += 1

    print(f"Total developers: {total_devs}\n")

    print("=== Activity distribution (total_activity = assignee+creator+reporter counts) ===")
    for label in ["1 (one-off)", "2-5", "6-20", "21-100", "100+"]:
        count = activity_buckets[label]
        pct = 100 * count / total_devs
        print(f"  {label:<15} {count:>8}  ({pct:.1f}%)")
    print(f"  Average activity per developer: {total_activity_sum/total_devs:.2f}")
    print(f"  Most active developer: {max_activity_dev}  (total_activity={max_activity})")

    print("\n=== Number of repositories each developer appears in ===")
    for label in [1, 2, 3, 4, 5, "6+"]:
        count = repo_count_buckets[label]
        pct = 100 * count / total_devs
        print(f"  {label} repo(s):  {count:>8}  ({pct:.1f}%)")

    print("\n=== Number of distinct components touched (domain breadth proxy) ===")
    for label in ["0", "1-3", "4-10", "11+"]:
        count = component_count_buckets[label]
        pct = 100 * count / total_devs
        print(f"  {label:<10} {count:>8}  ({pct:.1f}%)")

    print(f"\nRecords with missing first_seen/last_seen dates: {missing_dates} ({100*missing_dates/total_devs:.1f}%)")


if __name__ == "__main__":
    main()