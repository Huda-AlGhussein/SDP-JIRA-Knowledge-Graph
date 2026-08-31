"""
compute_profile_distributions.py

Purpose: compute distribution statistics (total_activity, actions_per_day,
num_projects) across all developer profiles in developer_profiles.jsonl,
BEFORE choosing any bot-filtering thresholds. No filtering happens here -
this only reports numbers so thresholds can be chosen based on actual
percentiles.

Naming-pattern matching was dropped as a filtering signal: developer_id
values were confirmed to be fully anonymized UUIDs (e.g.
"<<|author_key|0e681e81-...|>>"), so there is no readable name to match
bot-like substrings against.

Zero-tenure handling:
Profiles where first_seen == last_seen (all recorded activity fell on a
single calendar day) produce a 0-day tenure. Computing actions/day for
these would require an arbitrary floor (e.g. treating 0 days as 1 day),
which would silently inflate their rate and mix them into the main
distribution as manufactured outliers. Instead, these profiles are:
  - EXCLUDED from the actions_per_day percentile calculation
  - written out separately to zero_tenure_profiles.jsonl for manual review
  - summarized separately (count, total_activity stats, num_projects stats)

Usage:
    python compute_profile_distributions.py > profile_distribution_output.txt
"""

import json
from datetime import date
import numpy as np

INPUT_PATH = "developer_profiles.jsonl"
ZERO_TENURE_OUTPUT_PATH = "zero_tenure_profiles.jsonl"


def parse_date(date_str):
    if not date_str:
        return None
    try:
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        return None


def percentile_report(values, label):
    values = np.array([v for v in values if v is not None])
    if len(values) == 0:
        print(f"{label}: no valid values found")
        return
    print(f"\n--- {label} (n={len(values)}) ---")
    print(f"mean   : {values.mean():.2f}")
    print(f"median : {np.median(values):.2f}")
    print(f"p90    : {np.percentile(values, 90):.2f}")
    print(f"p95    : {np.percentile(values, 95):.2f}")
    print(f"p99    : {np.percentile(values, 99):.2f}")
    print(f"p99.9  : {np.percentile(values, 99.9):.2f}")
    print(f"max    : {values.max():.2f}")


def main():
    total_profiles = 0
    missing_dates = 0

    normal_total_activity = []
    normal_actions_per_day = []
    normal_num_projects = []

    zero_tenure_total_activity = []
    zero_tenure_num_projects = []
    zero_tenure_records = []

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            total_profiles += 1

            total_activity = record.get("total_activity")
            num_projects = record.get("num_projects")
            first_seen = parse_date(record.get("first_seen"))
            last_seen = parse_date(record.get("last_seen"))

            if first_seen is None or last_seen is None:
                missing_dates += 1
                continue

            tenure_days = (last_seen - first_seen).days

            if tenure_days <= 0:
                zero_tenure_total_activity.append(total_activity)
                zero_tenure_num_projects.append(num_projects)
                zero_tenure_records.append(record)
            else:
                normal_total_activity.append(total_activity)
                normal_num_projects.append(num_projects)
                normal_actions_per_day.append(total_activity / tenure_days)

    print(f"Total profiles read: {total_profiles}")
    print(f"Profiles missing first_seen/last_seen: {missing_dates}")
    print(f"Profiles with zero tenure (first_seen == last_seen): {len(zero_tenure_records)} "
          f"({100 * len(zero_tenure_records) / total_profiles:.2f}% of all profiles)")
    print(f"Profiles with tenure > 0 days (main distribution): {len(normal_total_activity)}")

    print("\n===== MAIN DISTRIBUTION (tenure > 0 days) =====")
    percentile_report(normal_total_activity, "total_activity")
    percentile_report(normal_actions_per_day, "actions_per_day")
    percentile_report(normal_num_projects, "num_projects")

    print("\n===== ZERO-TENURE BUCKET (excluded from actions_per_day above) =====")
    percentile_report(zero_tenure_total_activity, "total_activity (zero-tenure profiles)")
    percentile_report(zero_tenure_num_projects, "num_projects (zero-tenure profiles)")

    with open(ZERO_TENURE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in zero_tenure_records:
            f.write(json.dumps(record) + "\n")
    print(f"\nWrote {len(zero_tenure_records)} zero-tenure profiles to {ZERO_TENURE_OUTPUT_PATH} for manual review.")


if __name__ == "__main__":
    main()