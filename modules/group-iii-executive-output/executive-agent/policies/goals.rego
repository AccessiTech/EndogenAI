package endogenai.goals

# Goal feasibility and conflict constraints.
# Evaluated by executive-agent deliberation.py before committing a goal intention.
# OPA standalone HTTP: POST /v1/data/endogenai/goals/allow

default allow = false

# Allow if: no conflicting goal executing AND stack not at capacity
allow if {
    not conflicting_goal_exists
    not exceeds_capacity
}

# BG indirect pathway: suppress if same goal_class is already EXECUTING
conflicting_goal_exists if {
    some i
    data.active_goals[i].goal_class == input.candidate.goal_class
    data.active_goals[i].goal_class != null
    data.active_goals[i].goal_class != ""
    data.active_goals[i].lifecycle_state == "EXECUTING"
}

# BG indirect pathway: suppress if goal stack at capacity
exceeds_capacity if {
    count(data.active_goals) >= data.config.maxActiveGoals
}

violations[msg] if {
    conflicting_goal_exists
    msg := sprintf("Goal class '%v' already has an EXECUTING goal — BG indirect suppression applied", [input.candidate.goal_class])
}

violations[msg] if {
    exceeds_capacity
    msg := sprintf("Goal stack at capacity (%v active goals) — defer until a goal completes", [data.config.maxActiveGoals])
}
