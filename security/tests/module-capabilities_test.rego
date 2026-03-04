package endogenai.module_capabilities_test

import data.endogenai.module_capabilities

test_allow_declared_capability if {
    module_capabilities.allow
        with input as {"module_id": "sensory-input", "requested_capability": "mcp-context"}
        with data.modules as {"sensory-input": {"capabilities": ["mcp-context", "a2a-task"]}}
}

test_deny_undeclared_capability if {
    not module_capabilities.allow
        with input as {"module_id": "sensory-input", "requested_capability": "llm:generate"}
        with data.modules as {"sensory-input": {"capabilities": ["mcp-context"]}}
}

test_anomaly_on_undeclared if {
    module_capabilities.anomaly
        with input as {"module_id": "sensory-input", "requested_capability": "llm:generate"}
        with data.modules as {"sensory-input": {"capabilities": ["mcp-context"]}}
}

test_no_anomaly_when_module_missing if {
    not module_capabilities.anomaly
        with input as {"module_id": "unknown-module", "requested_capability": "llm:generate"}
        with data.modules as {}
}
