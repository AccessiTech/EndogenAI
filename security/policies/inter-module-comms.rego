# security/policies/inter-module-comms.rego
# Inter-module A2A communication rules.
# Default deny: A2A calls allowed only if caller is a declared consumer of the target.
package endogenai.inter_module_comms

import future.keywords.in

default allow_a2a_task = false

# Allow if caller is a declared consumer of the target module
allow_a2a_task if {
    input.caller_module in data.modules[input.target_module].consumers
}

# Allow if target is the MCP server (all modules may call infra)
allow_a2a_task if {
    input.target_module == "mcp-server"
}

# Allow if caller is the gateway (gateway may call any module)
allow_a2a_task if {
    input.caller_module == "gateway"
}

# Deny direct cross-module access
deny_direct if {
    not allow_a2a_task
    data.modules[input.caller_module]
    data.modules[input.target_module]
}
