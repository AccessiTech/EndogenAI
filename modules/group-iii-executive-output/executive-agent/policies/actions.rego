package endogenai.actions

# Action permission and scope constraints.
# Evaluated by executive-agent policy.py before dispatching any ActionSpec.
# OPA standalone HTTP: POST /v1/data/endogenai/actions/allow

default allow = false

# Permitted channels (loaded from data document; defaults to hardcoded set if absent)
permitted_channels := data.permitted_channels if {
    data.permitted_channels
} else := {"http", "a2a", "file", "render", "control-signal"}

# Rate limits per channel (loaded from data; defaults 100/min if absent)
rate_limit(channel) := data.rate_limits[channel] if {
    data.rate_limits[channel]
} else := 100

# Allow if channel is permitted AND not rate-limited
allow if {
    input.action.channel in permitted_channels
    not rate_limited
}

# Rate limit check (requires data.channel_calls to be populated by the module)
rate_limited if {
    data.channel_calls[input.action.channel] >= rate_limit(input.action.channel)
}

violations[msg] if {
    not input.action.channel in permitted_channels
    msg := sprintf("Channel '%v' not in permitted list %v", [input.action.channel, permitted_channels])
}

violations[msg] if {
    input.action.channel in permitted_channels
    rate_limited
    msg := sprintf("Channel '%v' rate-limited: %v calls >= limit %v", [input.action.channel, data.channel_calls[input.action.channel], rate_limit(input.action.channel)])
}
