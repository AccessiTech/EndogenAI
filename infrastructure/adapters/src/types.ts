/**
 * Bridge-specific types for the MCP + A2A adapter.
 */

/** Module identity used to stamp MCP messages emitted by the bridge. */
export interface BridgeModuleRef {
  moduleId: string;
  layer: string;
}

/** Configuration for the MCP-A2A Adapter Bridge. */
export interface BridgeConfig {
  /**
   * The module identity the bridge uses when publishing MCP context messages.
   * Should reflect the bridging agent's identity.
   */
  source: BridgeModuleRef;

  /**
   * The module ID that the bridge subscribes to for inbound MCP replies.
   * Replies addressed to this moduleId are automatically routed back to
   * their originating A2A task as completion artifacts.
   */
  replyTargetModuleId: string;

  /** Content type to use when wrapping A2A message payloads in MCPContext. */
  contentType?: string;

  /**
   * MCP context schema version string to stamp on published contexts.
   * Defaults to '0.1.0'.
   */
  contextVersion?: string;
}

/** Result of a round-trip send operation through the bridge. */
export interface BridgeSendResult {
  /** The A2A task ID created for this send */
  taskId: string;
  /** The MCP context ID published to the broker */
  contextId: string;
}
