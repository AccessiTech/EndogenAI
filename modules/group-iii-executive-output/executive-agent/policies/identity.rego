package endogenai.identity

# Identity integrity and value constraints.
# Evaluated by executive-agent policy.py before any action is dispatched.
# OPA standalone HTTP: POST /v1/data/endogenai/identity/allow

default allow = false

# Allow if the action does not violate any core value constraint
allow if {
    not violates_value
}

# Safety check: dispatch actions require a passed safety check
violates_value if {
    input.action.type == "dispatch"
    input.action.channel != "control-signal"
    not input.context.safety_check_passed
}

# Value constraint: actions that would modify core values require explicit override
violates_value if {
    input.action.type == "write"
    input.action.params.target == "core_values"
    not input.context.identity_override_approved
}

violations[msg] if {
    input.action.type == "dispatch"
    input.action.channel != "control-signal"
    not input.context.safety_check_passed
    msg := sprintf("Action '%v' failed safety check — context.safety_check_passed must be true", [input.action.type])
}

violations[msg] if {
    input.action.type == "write"
    input.action.params.target == "core_values"
    not input.context.identity_override_approved
    msg := "Core value modification requires identity_override_approved=true in context"
}
