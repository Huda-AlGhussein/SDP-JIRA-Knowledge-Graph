"""
link_type_mapping.py

Purpose: the finalized, human-reviewed mapping from every raw
(name, inward, outward) combination found in issue_link_types_full.csv
to a canonical category. This is a DATA file (a Python dict), not a
script that runs anything, so it can be imported by normalize_link_types.py
and inspected/edited directly.

Every one of the 107 distinct raw combinations found by
scan_issue_link_types.py is listed below explicitly. Nothing is matched
by fuzzy/partial string logic, every raw combination maps to exactly one
canonical category by exact lookup. This avoids silently merging labels
that look similar but were not explicitly reviewed.

Decisions made explicitly during review (see conversation record):
  - Cloners/duplicates/duplicates (SecondLife) -> mapped by LABEL TEXT,
    not by name, so it lands in Duplicate rather than Clones.
  - 5 self-referential labels (identical inward/outward text) mapped by
    name to their most obvious category. Direction (which issue is the
    subject) could NOT be verified from the label text and is left as
    recorded in the source data.
  - "5 - Depend" (Sakai) has inward/outward reversed relative to every
    other Depends-family label. It is mapped to Depends on, but
    normalize_link_types.py SWAPS its inwardIssue/outwardIssue direction
    so it is consistent with the rest of the category. This is the only
    label that gets a direction swap.
  - Small one-off labels (Account, Backports, Detail, Work Breakdown,
    Git Code Review variants, Polaris datapoint issue link, Derived) were
    kept as their OWN separate canonical categories, not merged into a
    generic "Other" bucket, per explicit decision.
  - Gantt/scheduling labels are EXCLUDED entirely (canonical value None),
    except multi-level hierarchy [GANTT], which was moved into
    Parent/Child since its labels ("is subtask of" / "is parent task of")
    are structural, not calendar/timing.

Categories excluded from the graph (canonical = None) represent calendar
/ scheduling relationships (Gantt dependency types), judged out of scope
for developer/issue recommendation. ~2,398 of 1,447,050 link entries
(0.17%) fall here.
"""

# key: (name, inward, outward) exactly as found in issue_link_types_full.csv
# value: canonical category name, or None if excluded from the graph
LINK_TYPE_MAP = {
    ("Duplicate", "is duplicated by", "duplicates"): "Duplicate",
    ("3 - Duplicate", "is duplicated by", "duplicates"): "Duplicate",
    ("Cloners", "duplicates", "duplicates"): "Duplicate",  # SecondLife: mapped by label text, not name

    ("Reference", "is related to", "relates to"): "Relates to",
    ("Relates", "relates to", "relates to"): "Relates to",
    ("Related", "is related to", "relates to"): "Relates to",
    ("Related", "is related to", "related to"): "Relates to",
    ("1 - Relate", "is related to", "relates to"): "Relates to",
    ("Relate", "is related to", "relates to"): "Relates to",
    ("Relates", "is related to", "relates"): "Relates to",
    ("Relationship", "is related to", "relates to"): "Relates to",
    ("Related", "is related to", "is related to "): "Relates to",  # IntelDAOS: trailing space stripped
    ("Related", "is related to", "is related to"): "Relates to",
    ("Relates", "related", "related"): "Relates to",
    ("Reference", "is referenced by", "references"): "Relates to",

    ("Blocks", "is blocked by", "blocks"): "Blocks",
    ("Blocker", "is blocked by", "blocks"): "Blocks",
    ("Blocker", "is blocked by", "is blocking"): "Blocks",
    ("Blocked", "Blocked", "Blocked"): "Blocks",  # Apache: self-referential label, direction unverifiable
    ("6 - Blocks", "is blocked by", "blocks"): "Blocks",

    ("Cloners", "is cloned by", "clones"): "Clones",
    ("Cloners", "is cloned by", "is a clone of"): "Clones",
    ("Cloners", "was cloned as", "is cloned from"): "Clones",
    ("Cloners (old)", "cloned from", "cloned to"): "Clones",
    ("2 - Cloned", "cloned from", "cloned as"): "Clones",
    ("Cloners", "cloned by", "clones"): "Clones",
    ("Cloners (migrated)", "is cloned by", "Clones"): "Clones",
    ("Cloners", "Cloned to", "Cloned from"): "Clones",

    ("Depends", "is depended on by", "depends on"): "Depends on",
    ("dependent", "is depended upon by", "depends upon"): "Depends on",
    ("Dependency", "is required for", "depends on"): "Depends on",
    ("Required", "is required by", "requires"): "Depends on",
    ("5 - Depend", "depends on", "is depended on by"): "Depends on",  # Sakai: direction SWAPPED in script to match convention
    ("Depend", "is depended on by", "depends on"): "Depends on",
    ("Dependent", "Dependent", "Dependent"): "Depends on",  # Apache: self-referential label, direction unverifiable
    ("Dependency", "is a precondition for", "depends on"): "Depends on",
    ("dependent", "is depended on by", "depends on"): "Depends on",
    ("Depends", "depended on by", "depends on"): "Depends on",
    ("Dependency", "Dependency", "Dependency"): "Depends on",  # Apache: self-referential label, direction unverifiable

    ("Superset", "is incorporated by", "incorporates"): "Part of/Incorporates",
    ("Incorporates", "is part of", "incorporates"): "Part of/Incorporates",
    ("Container", "Is contained by", "contains"): "Part of/Incorporates",
    ("Part", "is incorporated by", "incorporates"): "Part of/Incorporates",
    ("4 - Incorporate", "is incorporated by", "incorporates"): "Part of/Incorporates",
    ("PartOf", "is part of", "includes"): "Part of/Incorporates",
    ("Contains(WBSGantt)", "is contained in", "contains"): "Part of/Incorporates",
    ("Collection", "is included In", "includes"): "Part of/Incorporates",

    ("Problem/Incident", "is caused by", "causes"): "Causes",
    ("Causality", "is caused by", "causes"): "Causes",
    ("Cause", "causes", "is caused by"): "Causes",
    ("Cause", "is caused by", "causes"): "Causes",
    ("Caused", "is caused by", "causes"): "Causes",
    ("Regression", "is broken by", "breaks"): "Causes",
    ("Regression", "has a regression in", "is a regression of"): "Causes",
    ("Trigger", "was triggered by", "triggered"): "Causes",

    ("Supercedes", "is superceded by", "supercedes"): "Supersedes",
    ("Supersession", "supersedes", "is superseded by"): "Supersedes",
    ("Supersede", "is superseded by", "supersedes"): "Supersedes",
    ("Replacement", "replaces", "is replaced by"): "Supersedes",

    ("Child-Issue", "is a child of", "is a parent of"): "Parent/Child",
    ("Parent/Child", "is a child of", "is a parent of"): "Parent/Child",
    ("multi-level hierarchy [GANTT]", "is subtask of", "is parent task of"): "Parent/Child",
    ("Epic", "is the epic for", "belongs to epic"): "Parent/Child",
    ("Initiative", "included in Initiative", "includes Epic(s)"): "Parent/Child",
    ("Parent Feature", "Parent Feature", "Parent Feature"): "Parent/Child",  # Apache: self-referential label, direction unverifiable

    ("Issue split", "split from", "split to"): "Split",
    ("Split", "was split into", "was split from"): "Split",

    ("Bonfire Testing", "discovered while testing", "testing discovered"): "Testing",
    ("Bonfire Testing", "Testing discovered", "Discovered while testing"): "Testing",
    ("Bonfire testing", "Testing discovered", "Discovered while testing"): "Testing",
    ("Testing", "Discovered while testing", "Testing discovered"): "Testing",
    ("Tested", "is testing", "tested by"): "Testing",
    ("Test", "Is tested by", "tests"): "Testing",
    ("Verify", "is verified by", "verifies"): "Testing",
    ("Covered", "is covered by", "covers"): "Testing",

    ("Completes", "is fixed by", "fixes"): "Fixes/Resolves",
    ("Fixes", "fixed by", "fixes"): "Fixes/Resolves",
    ("Resolve", "is resolved by", "resolves"): "Fixes/Resolves",

    ("Sequence", "is followed up by", "follows up on"): "Follows/Sequence",
    ("Follows", "Followed up by", "Follow up to"): "Follows/Sequence",
    ("Follows", "followed by", "follows"): "Follows/Sequence",
    ("Preceded By", "Preceded By", "Precedes"): "Follows/Sequence",  # JiraEcosystem: self-referential label, direction unverifiable

    ("Implement", "is implemented by", "implements"): "Implements",
    ("Implements", "is implemented by", "implements"): "Implements",
    ("Polaris issue link", "is implemented by", "implements"): "Implements",

    ("Documented", "is documented by", "documents"): "Documentation",
    ("Documentation", "is documented by", "documents"): "Documentation",

    # Small one-off labels, kept as their own separate canonical categories
    ("Account", "account is impacted by", "impacts account"): "Account",
    ("Backports", "backports", "backported by"): "Backports",
    ("Detail", "is detailed by", "details"): "Detail",
    ("Work Breakdown", "resulted from", "resulted in"): "Work Breakdown",
    ("Git Code Review", "opened during git code review in", "git code review opened"): "Git Code Review",
    ("7 - Git Code Review", "opened during git code review in", "git code review opened"): "Git Code Review",
    ("Polaris datapoint issue link", "added to idea", "is idea for"): "Polaris datapoint issue link",
    ("Derived", "has a derivative of", "derived from"): "Derived",

    # Gantt / scheduling labels: EXCLUDED from the graph (calendar/timing, not content relationships)
    ("Gantt Dependency", "has to be done after", "has to be done before"): None,
    ("finish-start [GANTT]", "has to be done after", "has to be done before"): None,
    ("Gantt End to Start", "has to be done after", "has to be done before"): None,
    ("Gantt End to End", "has to be finished together with", "has to be finished together with"): None,
    ("Gantt: finish-start", "has to be done after", "has to be done before"): None,
    ("finish-finish [GANTT]", "has to be finished together with", "has to be finished together with"): None,
    ("Gantt: start-finish", "is triggered by", "is triggering"): None,
    ("Gantt: finish-finish", "has to be finished together with", "has to be finished together with"): None,
    ("start-finish [GANTT]", "start is earliest end of", "earliest end is start of"): None,
    ("Gantt Start to Start", "has to be started together with", "has to be started together with"): None,
    ("Finish-to-Finish link (WBSGantt)",
     "can't finish until the linked issue is done.",
     "Linked one can't finish until this issue is done."): None,
    ("Gantt: start-start", "has to be started together with", "has to be started together with"): None,
}

# Labels that need a direction SWAP (inwardIssue <-> outwardIssue) before merging,
# because their raw inward/outward convention is reversed relative to the rest
# of their canonical category. Currently only one label needs this.
DIRECTION_SWAP_LABELS = {
    ("5 - Depend", "depends on", "is depended on by"),
}