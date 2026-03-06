# security/policies/helpers.rego
# Shared helpers for EndogenAI OPA policies.
package endogenai.helpers

import future.keywords.in

# is_infrastructure: true for MCP server and gateway (not module services)
is_infrastructure(module_id) if {
    module_id in {"mcp-server", "gateway"}
}
