"""
flag_bot_profiles.py

Purpose: add an is_likely_bot flag to every developer profile in
developer_profiles.jsonl, based on three signals derived earlier from
compute_profile_distributions.py (p99.9 cutoffs on the tenure > 0 days
distribution, n=143,652).

This is FLAG-FIRST, not a filter: no profiles are dropped. Every profile
is written back out with two new fields:
  - is_likely_bot: True/False
  - flags_tripped: list of which signals fired, e.g. ["total_activity", "num_projects"]

Thresholds (p99.9 of the tenure > 0 days distribution):
  - total_activity  >= 3252
  - actions_per_day >= 12      (only computable for tenure > 0 days profiles)
  - num_projects    >= 28

Rule: flagged as is_likely_bot=True if 2 OR MORE of the three signals are
tripped (the more conservative option, chosen to reduce mislabeling real
highly active developers as bots).

Zero-tenure profiles (first_seen == last_seen, ~72.8% of all profiles,
384,503 records) cannot have actions_per_day computed, so they are
evaluated on total_activity and num_projects only (2 signals instead of
3). This means they can only be flagged if BOTH of those two signals
trip, since 2-of-2 is the only way to reach the "2 or more" rule with
just two available signals. This is stated explicitly since it is an
asymmetry between the two groups worth knowing about, not a silent
inconsistency.

Usage:
    python flag_bot_profiles.py
"""

import json
from datetime import date

INPUT_PATH = "developer_profiles.jsonl"
OUTPUT_PATH = "developer_profiles_flagged.jsonl"

THRESHOLD_TOTAL_ACTIVITY = 3252
THRESHOLD_ACTIONS_PER_DAY = 12
THRESHOLD_NUM_PROJECTS = 28

MIN_SIGNALS_TO_FLAG = 2


def parse_date(date_str):
    if not date_str:
        return None
    try:
        year, month, day = date_str.split("-")
        return date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        return None


def evaluate_profile(record):
    total_activity = record.get("total_activity")
    num_projects = record.get("num_projects")
    first_seen = parse_date(record.get("first_seen"))
    last_seen = parse_date(record.get("last_seen"))

    flags_tripped = []

    if total_activity is not None and total_activity >= THRESHOLD_TOTAL_ACTIVITY:
        flags_tripped.append("total_activity")

    if num_projects is not None and num_projects >= THRESHOLD_NUM_PROJECTS:
        flags_tripped.append("num_projects")

    tenure_days = None
    if first_seen is not None and last_seen is not None:
        tenure_days = (last_seen - first_seen).days

    actions_per_day = None
    if tenure_days is not None and tenure_days > 0 and total_activity is not None:
        actions_per_day = total_activity / tenure_days
        if actions_per_day >= THRESHOLD_ACTIONS_PER_DAY:
            flags_tripped.append("actions_per_day")

    is_likely_bot = len(flags_tripped) >= MIN_SIGNALS_TO_FLAG

    return is_likely_bot, flags_tripped, actions_per_day


def main():
    total_profiles = 0
    flagged_count = 0
    zero_tenure_count = 0
    zero_tenure_flagged_count = 0

    with open(INPUT_PATH, "r", encoding="utf-8") as infile, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as outfile:

        for line in infile:
            if not line.strip():
                continue
            record = json.loads(line)
            total_profiles += 1

            is_likely_bot, flags_tripped, actions_per_day = evaluate_profile(record)

            first_seen = parse_date(record.get("first_seen"))
            last_seen = parse_date(record.get("last_seen"))
            is_zero_tenure = (first_seen is not None and last_seen is not None
                               and (last_seen - first_seen).days <= 0)

            if is_zero_tenure:
                zero_tenure_count += 1
                if is_likely_bot:
                    zero_tenure_flagged_count += 1

            record["actions_per_day"] = actions_per_day
            record["is_likely_bot"] = is_likely_bot
            record["flags_tripped"] = flags_tripped

            if is_likely_bot:
                flagged_count += 1

            outfile.write(json.dumps(record) + "\n")

    print(f"Total profiles processed: {total_profiles}")
    print(f"Flagged as is_likely_bot=True: {flagged_count} "
          f"({100 * flagged_count / total_profiles:.3f}% of all profiles)")
    print(f"  of which zero-tenure profiles flagged: {zero_tenure_flagged_count} "
          f"(out of {zero_tenure_count} zero-tenure profiles total)")
    print(f"Output written to: {OUTPUT_PATH}")
    print("\nNo profiles were dropped. This is a flag-first output: filter downstream "
          "using is_likely_bot as needed, e.g. for clustering exclude flagged profiles, "
          "for auditing keep them and inspect flags_tripped.")


if __name__ == "__main__":
    main()