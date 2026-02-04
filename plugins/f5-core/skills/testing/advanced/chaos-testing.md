---
name: chaos-testing
description: Chaos engineering and resilience testing
category: testing/advanced
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Chaos Testing

## Overview

Chaos testing intentionally introduces failures into a system to verify
its resilience and discover weaknesses before they cause production outages.

## Principles of Chaos Engineering

```
┌─────────────────────────────────────────────────────────────────┐
│                  Chaos Engineering Process                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Define "steady state" (normal behavior metrics)            │
│                         ↓                                        │
│   2. Hypothesize: "System will maintain steady state            │
│      even when X fails"                                         │
│                         ↓                                        │
│   3. Introduce failure (inject chaos)                           │
│                         ↓                                        │
│   4. Observe: Did steady state continue?                        │
│                         ↓                                        │
│   5. Learn and improve (fix vulnerabilities)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Types of Chaos Experiments

| Category | Experiments |
|----------|-------------|
| **Network** | Latency, packet loss, DNS failure |
| **Resources** | CPU stress, memory pressure, disk full |
| **Application** | Process kill, dependency failure |
| **Infrastructure** | Node failure, zone outage |
| **State** | Data corruption, stale cache |

## Network Chaos

### Simulating Latency

```typescript
// Using Toxiproxy for network chaos
import { Toxiproxy, Toxic } from 'toxiproxy-node-client';

describe('Latency Resilience', () => {
  let toxiproxy: Toxiproxy;
  let proxy: any;

  beforeAll(async () => {
    toxiproxy = new Toxiproxy('http://localhost:8474');
    proxy = await toxiproxy.createProxy({
      name: 'database',
      listen: '0.0.0.0:5433',
      upstream: 'postgres:5432',
    });
  });

  afterAll(async () => {
    await proxy.remove();
  });

  it('should handle database latency gracefully', async () => {
    // Add 500ms latency
    await proxy.addToxic({
      name: 'latency',
      type: 'latency',
      attributes: { latency: 500 },
    });

    const start = Date.now();
    const result = await userService.getUser('123');
    const duration = Date.now() - start;

    expect(result).toBeDefined();
    expect(duration).toBeGreaterThan(500);
    expect(duration).toBeLessThan(5000); // Timeout not triggered

    // Remove toxic for next test
    await proxy.removeToxic('latency');
  });

  it('should timeout on extreme latency', async () => {
    // Add 10 second latency (exceeds 5s timeout)
    await proxy.addToxic({
      name: 'extreme_latency',
      type: 'latency',
      attributes: { latency: 10000 },
    });

    await expect(userService.getUser('123')).rejects.toThrow('Timeout');

    await proxy.removeToxic('extreme_latency');
  });

  it('should retry on connection reset', async () => {
    // Reset connection 50% of the time
    await proxy.addToxic({
      name: 'reset',
      type: 'reset_peer',
      attributes: { timeout: 0 },
      toxicity: 0.5,
    });

    // With retry logic, should eventually succeed
    const result = await userService.getUser('123');
    expect(result).toBeDefined();

    await proxy.removeToxic('reset');
  });
});
```

### Simulating Packet Loss

```typescript
describe('Packet Loss Resilience', () => {
  it('should handle packet loss', async () => {
    // Simulate 10% packet loss
    await proxy.addToxic({
      name: 'packet_loss',
      type: 'timeout',
      attributes: { timeout: 100 },
      toxicity: 0.1,
    });

    // Run multiple requests
    const results = await Promise.allSettled(
      Array.from({ length: 100 }, () => api.makeRequest())
    );

    const successes = results.filter(r => r.status === 'fulfilled');
    const failures = results.filter(r => r.status === 'rejected');

    // With retries, most should succeed
    expect(successes.length).toBeGreaterThan(90);
    // Some might fail
    console.log(`${failures.length} failures due to packet loss`);
  });
});
```

## Resource Chaos

### CPU Stress Testing

```typescript
import { exec } from 'child_process';

describe('CPU Stress Resilience', () => {
  it('should maintain response times under CPU pressure', async () => {
    // Start CPU stress (requires stress-ng)
    const stressProcess = exec('stress-ng --cpu 4 --timeout 30s');

    // Measure response times during stress
    const responseTimes: number[] = [];

    for (let i = 0; i < 10; i++) {
      const start = Date.now();
      await api.healthCheck();
      responseTimes.push(Date.now() - start);
      await sleep(1000);
    }

    // Stop stress
    stressProcess.kill();

    const avgResponseTime = responseTimes.reduce((a, b) => a + b) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);

    console.log(`Avg response time under CPU stress: ${avgResponseTime}ms`);
    console.log(`Max response time under CPU stress: ${maxResponseTime}ms`);

    // Should still respond within SLA
    expect(avgResponseTime).toBeLessThan(1000);
    expect(maxResponseTime).toBeLessThan(5000);
  });
});
```

### Memory Pressure Testing

```typescript
describe('Memory Pressure Resilience', () => {
  it('should handle memory pressure', async () => {
    // Allocate memory to simulate pressure
    const memoryPressure: Buffer[] = [];

    try {
      // Gradually increase memory usage
      for (let i = 0; i < 10; i++) {
        memoryPressure.push(Buffer.alloc(100 * 1024 * 1024)); // 100MB chunks

        const healthStatus = await api.healthCheck();
        expect(healthStatus.status).toBe('healthy');

        // Check if app is handling memory pressure
        if (healthStatus.memoryUsage > 80) {
          console.log('Memory pressure detected, app should trigger GC');
        }
      }
    } finally {
      // Release memory
      memoryPressure.length = 0;
      global.gc?.();
    }
  });
});
```

## Application Chaos

### Dependency Failure

```typescript
describe('Dependency Failure Resilience', () => {
  it('should use circuit breaker on repeated failures', async () => {
    // Configure mock to fail
    mockPaymentService.charge.mockRejectedValue(new Error('Service unavailable'));

    // First few calls should retry
    for (let i = 0; i < 5; i++) {
      await expect(orderService.processOrder(order)).rejects.toThrow();
    }

    // Circuit should be open now - fail fast
    const start = Date.now();
    await expect(orderService.processOrder(order)).rejects.toThrow('Circuit open');
    const duration = Date.now() - start;

    // Should fail immediately (circuit open)
    expect(duration).toBeLessThan(100);
  });

  it('should recover when dependency returns', async () => {
    // Simulate recovery
    await sleep(5000); // Wait for circuit half-open

    mockPaymentService.charge.mockResolvedValue({ transactionId: 'txn-123' });

    // Should try again in half-open state
    const result = await orderService.processOrder(order);
    expect(result.status).toBe('completed');
  });
});
```

### Process Termination

```typescript
describe('Process Termination Resilience', () => {
  it('should recover from worker crash', async () => {
    // Start a job
    const jobId = await jobQueue.enqueue('process-data', { data: 'test' });

    // Wait for job to start processing
    await waitFor(() => jobQueue.getStatus(jobId) === 'processing');

    // Kill the worker process
    await killWorkerProcess();

    // Wait for recovery
    await sleep(5000);

    // Job should be retried
    const status = await jobQueue.getStatus(jobId);
    expect(['processing', 'completed']).toContain(status);
  });
});
```

## Infrastructure Chaos

### Node Failure Simulation

```typescript
describe('Node Failure Resilience', () => {
  it('should redistribute load on node failure', async () => {
    // Get initial node count
    const initialNodes = await getHealthyNodeCount();
    expect(initialNodes).toBe(3);

    // Terminate one node
    await terminateNode('node-2');

    // Wait for health check to detect
    await sleep(10000);

    // Traffic should be redistributed
    const healthStatus = await api.healthCheck();
    expect(healthStatus.status).toBe('healthy');

    // New node should spin up
    await waitFor(async () => {
      const nodes = await getHealthyNodeCount();
      return nodes === 3;
    }, { timeout: 120000 });
  });
});
```

## Chaos Test Framework

```typescript
// chaos/framework.ts
interface ChaosExperiment {
  name: string;
  description: string;
  steadyStateHypothesis: () => Promise<boolean>;
  method: () => Promise<void>;
  rollback: () => Promise<void>;
}

class ChaosRunner {
  async run(experiment: ChaosExperiment): Promise<ChaosResult> {
    console.log(`Running chaos experiment: ${experiment.name}`);

    // 1. Verify steady state before
    const steadyStateBefore = await experiment.steadyStateHypothesis();
    if (!steadyStateBefore) {
      throw new Error('System not in steady state before experiment');
    }

    try {
      // 2. Run chaos
      await experiment.method();

      // 3. Wait for system to stabilize
      await sleep(5000);

      // 4. Verify steady state during/after chaos
      const steadyStateAfter = await experiment.steadyStateHypothesis();

      return {
        success: steadyStateAfter,
        experiment: experiment.name,
        timestamp: new Date(),
      };
    } finally {
      // 5. Always rollback
      await experiment.rollback();
    }
  }
}

// Example experiment
const databaseFailureExperiment: ChaosExperiment = {
  name: 'database-connection-failure',
  description: 'Verify system handles database connection loss',

  steadyStateHypothesis: async () => {
    const health = await api.healthCheck();
    return health.status === 'healthy' && health.responseTime < 200;
  },

  method: async () => {
    // Block database port
    await exec('iptables -A INPUT -p tcp --dport 5432 -j DROP');
  },

  rollback: async () => {
    // Restore database port
    await exec('iptables -D INPUT -p tcp --dport 5432 -j DROP');
  },
};
```

## Chaos Tools

| Tool | Type | Use Case |
|------|------|----------|
| **Chaos Monkey** | Random termination | Kill random instances |
| **Litmus** | Kubernetes chaos | K8s-native experiments |
| **Toxiproxy** | Network proxy | Simulate network issues |
| **Gremlin** | Platform | Enterprise chaos |
| **Pumba** | Docker | Container chaos |

## Best Practices

| Do | Don't |
|----|-------|
| Start small (dev/staging) | Run in production first |
| Define steady state | Skip hypothesis |
| Have rollback ready | Leave chaos running |
| Monitor closely | Ignore metrics |
| Document findings | Skip post-mortems |
| Automate experiments | Manual one-offs |

## Game Days

```markdown
## Chaos Game Day Template

### Pre-Game
- [ ] Define scope and boundaries
- [ ] Notify stakeholders
- [ ] Prepare monitoring dashboards
- [ ] Have rollback procedures ready
- [ ] Assign roles (experimenter, observer, communicator)

### During Game
- [ ] Start with steady state verification
- [ ] Run experiments sequentially
- [ ] Document observations in real-time
- [ ] Monitor key metrics
- [ ] Be ready to halt if needed

### Post-Game
- [ ] Compile findings
- [ ] Identify vulnerabilities
- [ ] Create action items
- [ ] Share learnings
- [ ] Plan fixes
```

## Related Topics

- [Integration Testing](../integration-testing/integration-test-basics.md)
- [Contract Testing](./contract-testing.md)
- [Test Automation](../ci-cd/test-automation.md)
