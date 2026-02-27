/**
 * Unit tests for CapabilityRegistry
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { CapabilityRegistry } from '../src/registry.js';
import type { Capability } from '../src/types.js';

const mockCap = (moduleId: string): Capability => ({
  moduleId,
  layer: 'signal-processing',
  accepts: ['signal/text', 'application/json'],
  emits: ['memory/item'],
  version: '0.1.0',
  url: `http://${moduleId}:8080`,
});

describe('CapabilityRegistry', () => {
  let registry: CapabilityRegistry;

  beforeEach(() => {
    registry = new CapabilityRegistry();
  });

  it('registers a capability', () => {
    registry.register(mockCap('sensory-input'));
    expect(registry.size()).toBe(1);
    expect(registry.get('sensory-input')?.moduleId).toBe('sensory-input');
  });

  it('stamps registeredAt on register', () => {
    registry.register(mockCap('sensory-input'));
    expect(registry.get('sensory-input')?.registeredAt).toBeDefined();
  });

  it('overwrites on second register', () => {
    registry.register(mockCap('sensory-input'));
    registry.register({ ...mockCap('sensory-input'), version: '0.2.0' });
    expect(registry.size()).toBe(1);
    expect(registry.get('sensory-input')?.version).toBe('0.2.0');
  });

  it('deregisters a capability', () => {
    registry.register(mockCap('sensory-input'));
    expect(registry.deregister('sensory-input')).toBe(true);
    expect(registry.size()).toBe(0);
  });

  it('deregister returns false for unknown module', () => {
    expect(registry.deregister('unknown')).toBe(false);
  });

  it('finds modules by accepted content type', () => {
    registry.register(mockCap('a'));
    registry.register(mockCap('b'));
    expect(registry.findByAcceptedContentType('signal/text')).toHaveLength(2);
  });

  it('returns empty array when no match for content type', () => {
    registry.register(mockCap('a'));
    expect(registry.findByAcceptedContentType('reward/signal')).toHaveLength(0);
  });

  it('lists all capabilities', () => {
    registry.register(mockCap('a'));
    registry.register(mockCap('b'));
    expect(registry.list()).toHaveLength(2);
  });

  it('clears all capabilities', () => {
    registry.register(mockCap('x'));
    registry.clear();
    expect(registry.size()).toBe(0);
  });
});
