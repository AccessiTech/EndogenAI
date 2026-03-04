# security/policies/module-capabilities.rego
# Module capability isolation — derived from agent-card.json capabilities arrays.
# Default deny: modules may only exercise capabilities declared in their agent card.
package endogenai.module_capabilities

import future.keywords.in

default allow = false

# Allow if requested capability is declared in the module's agent-card data
allow if {
    input.requested_capability in data.modules[input.module_id].capabilities
}

# DAMP signal: module requests capability NOT in agent-card (possible misconfiguration)
anomaly if {
    not allow
    data.modules[input.module_id]  # module exists
}
