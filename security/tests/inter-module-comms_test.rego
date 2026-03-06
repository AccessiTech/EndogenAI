package endogenai.inter_module_comms_test

import data.endogenai.inter_module_comms

# Gateway bypass
test_gateway_bypass if {
    inter_module_comms.allow_a2a_task
        with input as {"caller_module": "gateway", "target_module": "working-memory"}
        with data.modules as {"working-memory": {"consumers": []}}
}
# MCP server target
test_mcp_server_target if {
    inter_module_comms.allow_a2a_task
        with input as {"caller_module": "reasoning", "target_module": "mcp-server"}
        with data.modules as {"reasoning": {}, "mcp-server": {"consumers": []}}
}
# Declared consumer
test_declared_consumer_allowed if {
    inter_module_comms.allow_a2a_task
        with input as {"caller_module": "working-memory", "target_module": "long-term-memory"}
        with data.modules as {"long-term-memory": {"consumers": ["working-memory"]}}
}
# Undeclared caller denied
test_undeclared_caller_denied if {
    not inter_module_comms.allow_a2a_task
        with input as {"caller_module": "sensory-input", "target_module": "executive-agent"}
        with data.modules as {"executive-agent": {"consumers": ["gateway"]}, "sensory-input": {}}
}
# deny_direct fires for undeclared
test_deny_direct if {
    inter_module_comms.deny_direct
        with input as {"caller_module": "sensory-input", "target_module": "executive-agent"}
        with data.modules as {"executive-agent": {"consumers": []}, "sensory-input": {}}
}
