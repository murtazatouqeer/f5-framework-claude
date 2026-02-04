---
name: incident-management
description: Incident response and management practices
category: devops/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Incident Management

## Overview

Incident management is the process of identifying, analyzing, and resolving
incidents to restore normal service operation as quickly as possible while
minimizing impact.

## Incident Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                   Incident Lifecycle                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Detection        Triage          Response         Resolution   │
│  ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐   │
│  │ Alert  │  →  │Assess  │  →  │Mitigate│  →  │ Fix    │   │
│  │triggers│      │severity│      │impact  │      │ root   │   │
│  └────────┘      └────────┘      └────────┘      │ cause  │   │
│                                                    └────────┘   │
│       │              │              │                │          │
│       ▼              ▼              ▼                ▼          │
│   Monitoring    Incident        War Room         Postmortem    │
│   detects       Commander       formed           scheduled     │
│   issue         assigned                                       │
│                                                                  │
│  ──────────────────────────────────────────────────────────────│
│                          Timeline                                │
│  0m        5m          15m          30m      2h        24-48h   │
│  Alert     Ack         IC assigned  Updates  Resolved  Review   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Incident Severity Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                   Severity Levels                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SEV-1 (Critical)                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Complete service outage                                │   │
│  │ • Data loss or security breach                           │   │
│  │ • Revenue impact > $10,000/hour                          │   │
│  │ Response: All hands, exec notification                   │   │
│  │ Target resolution: < 1 hour                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  SEV-2 (High)                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Major feature unavailable                              │   │
│  │ • Significant performance degradation                    │   │
│  │ • > 10% of users affected                               │   │
│  │ Response: On-call + backup, manager notified            │   │
│  │ Target resolution: < 4 hours                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  SEV-3 (Medium)                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Minor feature unavailable                              │   │
│  │ • Limited user impact                                    │   │
│  │ • Workaround available                                   │   │
│  │ Response: On-call engineer                              │   │
│  │ Target resolution: < 24 hours                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  SEV-4 (Low)                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Cosmetic issue                                         │   │
│  │ • No user impact                                         │   │
│  │ • Internal tooling issue                                 │   │
│  │ Response: Next business day                             │   │
│  │ Target resolution: < 1 week                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Incident Roles

```yaml
# incident-roles.yaml
roles:
  incident_commander:
    responsibilities:
      - "Overall incident coordination"
      - "Decision making authority"
      - "Resource allocation"
      - "Communication oversight"
      - "Escalation decisions"
    skills:
      - "Technical knowledge"
      - "Leadership"
      - "Communication"
      - "Calm under pressure"

  tech_lead:
    responsibilities:
      - "Technical investigation"
      - "Coordinate debugging efforts"
      - "Propose mitigations"
      - "Implement fixes"
    skills:
      - "Deep technical expertise"
      - "System knowledge"
      - "Problem solving"

  communications_lead:
    responsibilities:
      - "Status page updates"
      - "Customer communications"
      - "Internal stakeholder updates"
      - "Timeline documentation"
    skills:
      - "Clear writing"
      - "Customer empathy"
      - "Stakeholder management"

  scribe:
    responsibilities:
      - "Document all actions"
      - "Track timeline"
      - "Record decisions"
      - "Capture hypotheses"
    skills:
      - "Fast typing"
      - "Attention to detail"
      - "Organization"

  subject_matter_expert:
    responsibilities:
      - "Deep system knowledge"
      - "Answer technical questions"
      - "Provide historical context"
    skills:
      - "Domain expertise"
      - "Technical depth"
```

## Incident Response Playbook

```yaml
# incident-playbook.yaml
incident_response:
  detection:
    actions:
      - "Acknowledge alert within 15 minutes"
      - "Verify incident is real (not false positive)"
      - "Assess initial severity"
      - "Create incident channel/room"

  triage:
    actions:
      - "Assign Incident Commander"
      - "Confirm severity level"
      - "Identify affected services"
      - "Estimate user impact"
      - "Page additional responders if needed"

    severity_determination:
      questions:
        - "How many users are affected?"
        - "Is there data loss or security risk?"
        - "What's the revenue impact?"
        - "Is there a workaround?"

  response:
    actions:
      - "Establish communication channel"
      - "Begin investigation"
      - "Consider immediate mitigations"
      - "Start timeline documentation"
      - "Post initial status update"

    investigation_steps:
      - "Check recent deployments"
      - "Review error logs"
      - "Check metrics dashboards"
      - "Verify infrastructure health"
      - "Check external dependencies"

    mitigation_options:
      - "Rollback recent deployment"
      - "Scale up resources"
      - "Enable feature flag (disable feature)"
      - "Failover to backup"
      - "Apply hotfix"

  resolution:
    actions:
      - "Confirm service restored"
      - "Verify monitoring shows normal"
      - "Update status page"
      - "Notify stakeholders"
      - "Schedule postmortem"

  post_incident:
    actions:
      - "Complete incident timeline"
      - "Create incident ticket"
      - "Schedule postmortem (within 48h)"
      - "Identify follow-up actions"
      - "Update runbooks if needed"
```

## Incident Communication

### Status Page Updates

```typescript
// status-updater.ts
interface IncidentUpdate {
  incidentId: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  severity: 'critical' | 'major' | 'minor';
  title: string;
  message: string;
  affectedComponents: string[];
  timestamp: Date;
}

async function postStatusUpdate(update: IncidentUpdate): Promise<void> {
  // Update status page (e.g., Statuspage.io)
  await statusPageClient.createIncidentUpdate({
    incident_id: update.incidentId,
    status: update.status,
    body: update.message,
    components: update.affectedComponents.map(c => ({
      id: c,
      status: mapComponentStatus(update.status),
    })),
  });

  // Post to Slack
  await slackClient.chat.postMessage({
    channel: '#incidents',
    blocks: [
      {
        type: 'header',
        text: { type: 'plain_text', text: `🚨 ${update.title}` },
      },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Status:* ${update.status}` },
          { type: 'mrkdwn', text: `*Severity:* ${update.severity}` },
        ],
      },
      {
        type: 'section',
        text: { type: 'mrkdwn', text: update.message },
      },
    ],
  });

  // Send to PagerDuty timeline
  await pagerDutyClient.addNote(update.incidentId, update.message);
}
```

### Communication Templates

```markdown
<!-- templates/investigating.md -->
## Investigating Increased Error Rates

**Status:** Investigating
**Time:** {{ timestamp }}

We are currently investigating reports of increased error rates
affecting {{ affected_services }}.

Our team is actively working to identify the root cause.
We will provide an update within 30 minutes.

---

<!-- templates/identified.md -->
## Root Cause Identified

**Status:** Identified
**Time:** {{ timestamp }}

We have identified the root cause as {{ root_cause }}.

Our team is implementing a fix. We expect to resolve this
issue within {{ eta }}.

---

<!-- templates/monitoring.md -->
## Fix Deployed - Monitoring

**Status:** Monitoring
**Time:** {{ timestamp }}

We have deployed a fix for {{ issue }}.

We are monitoring the system to ensure stability.
No further action is required from users at this time.

---

<!-- templates/resolved.md -->
## Incident Resolved

**Status:** Resolved
**Time:** {{ timestamp }}
**Duration:** {{ duration }}

This incident has been resolved. {{ summary }}

We will be conducting a postmortem and will share learnings.
We apologize for any inconvenience caused.
```

## Postmortem Process

```
┌─────────────────────────────────────────────────────────────────┐
│                 Blameless Postmortem Process                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Principles:                                                     │
│  • Focus on systems, not people                                 │
│  • Assume good intentions                                       │
│  • Share learnings openly                                       │
│  • Identify actionable improvements                             │
│                                                                  │
│  Timeline:                                                       │
│  Day 0-2:  Incident resolved, initial notes gathered            │
│  Day 2-5:  Postmortem document drafted                          │
│  Day 5-7:  Postmortem meeting conducted                         │
│  Day 7-14: Action items assigned and tracked                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Postmortem Template

```markdown
# Postmortem: {{ incident_title }}

**Date:** {{ incident_date }}
**Authors:** {{ authors }}
**Status:** {{ draft | final }}

## Summary

Brief description of the incident in 2-3 sentences.

## Impact

- **Duration:** {{ start_time }} to {{ end_time }} ({{ duration }})
- **Users Affected:** {{ user_count }} ({{ percentage }}% of active users)
- **Revenue Impact:** {{ revenue_impact }}
- **SLO Impact:** {{ error_budget_consumed }}

## Timeline (all times UTC)

| Time | Event |
|------|-------|
| 14:00 | Deployment of v2.3.1 completed |
| 14:15 | Error rate alert triggered |
| 14:17 | On-call engineer acknowledged |
| 14:25 | Incident Commander assigned |
| 14:30 | Root cause identified |
| 14:45 | Rollback initiated |
| 15:00 | Service restored |
| 15:30 | Monitoring confirmed stable |

## Root Cause

Detailed technical explanation of what caused the incident.

The database connection pool was exhausted due to a missing
connection timeout in the new feature deployment. Under load,
connections were not being released, leading to thread starvation.

## Contributing Factors

- Missing connection timeout configuration
- Insufficient load testing of new feature
- Connection pool metrics not included in standard dashboard

## Detection

How was this incident detected?

- Automated: Alert triggered by error rate exceeding threshold
- Detection time: 15 minutes after deployment

## Response

What actions were taken to mitigate and resolve?

1. Attempted to increase connection pool size (ineffective)
2. Identified missing timeout configuration
3. Decision made to rollback deployment
4. Rollback completed successfully

## Lessons Learned

### What went well

- Fast alert detection (15 minutes)
- Quick decision to rollback
- Good team communication
- Clear runbooks helped

### What went wrong

- Missing configuration review in deployment process
- Load testing did not simulate realistic connection patterns
- Connection pool exhaustion not covered in runbooks

### Where we got lucky

- Incident occurred during business hours
- Senior engineer familiar with the system was available

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add connection timeout to all database configs | @alice | P1 | 2024-01-20 | ✅ |
| Add connection pool metrics to standard dashboard | @bob | P1 | 2024-01-22 | 🔄 |
| Update load testing to include connection patterns | @charlie | P2 | 2024-02-01 | ⏳ |
| Add config review to deployment checklist | @dave | P2 | 2024-01-25 | ⏳ |
| Create runbook for connection pool issues | @alice | P3 | 2024-02-15 | ⏳ |

## Supporting Information

- [Dashboard during incident](link)
- [Deployment PR](link)
- [Slack incident channel](link)
- [Related incidents](link)
```

## Incident Tooling

### PagerDuty Integration

```typescript
// pagerduty-integration.ts
import { api } from '@pagerduty/pdjs';

const pd = api({ token: process.env.PAGERDUTY_TOKEN });

async function createIncident(params: {
  title: string;
  serviceId: string;
  urgency: 'high' | 'low';
  body: string;
}) {
  const incident = await pd.post('/incidents', {
    data: {
      incident: {
        type: 'incident',
        title: params.title,
        service: {
          id: params.serviceId,
          type: 'service_reference',
        },
        urgency: params.urgency,
        body: {
          type: 'incident_body',
          details: params.body,
        },
      },
    },
  });

  return incident.data.incident;
}

async function acknowledgeIncident(incidentId: string, userId: string) {
  await pd.put(`/incidents/${incidentId}`, {
    data: {
      incident: {
        type: 'incident',
        status: 'acknowledged',
        assignments: [
          {
            assignee: {
              id: userId,
              type: 'user_reference',
            },
          },
        ],
      },
    },
  });
}

async function resolveIncident(incidentId: string, resolution: string) {
  await pd.put(`/incidents/${incidentId}`, {
    data: {
      incident: {
        type: 'incident',
        status: 'resolved',
        resolution: resolution,
      },
    },
  });
}
```

### Incident Bot

```typescript
// slack-incident-bot.ts
import { App } from '@slack/bolt';

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
});

// Create incident command
app.command('/incident', async ({ command, ack, respond }) => {
  await ack();

  // Create incident channel
  const channelName = `incident-${Date.now()}`;
  const channel = await app.client.conversations.create({
    name: channelName,
    is_private: false,
  });

  // Post initial message
  await app.client.chat.postMessage({
    channel: channel.channel.id,
    blocks: [
      {
        type: 'header',
        text: { type: 'plain_text', text: '🚨 New Incident' },
      },
      {
        type: 'section',
        text: { type: 'mrkdwn', text: command.text },
      },
      {
        type: 'actions',
        elements: [
          {
            type: 'button',
            text: { type: 'plain_text', text: 'Assign IC' },
            action_id: 'assign_ic',
          },
          {
            type: 'button',
            text: { type: 'plain_text', text: 'Set Severity' },
            action_id: 'set_severity',
          },
          {
            type: 'button',
            text: { type: 'plain_text', text: 'Resolve' },
            action_id: 'resolve_incident',
            style: 'primary',
          },
        ],
      },
    ],
  });

  await respond(`Incident channel created: #${channelName}`);
});

// Timeline entry command
app.command('/timeline', async ({ command, ack, say }) => {
  await ack();

  const timestamp = new Date().toISOString();
  await say({
    blocks: [
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*${timestamp}*: ${command.text}`,
        },
      },
    ],
  });
});
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Incident Management Best Practices                  │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Define clear severity levels with response expectations       │
│ ☐ Establish role assignments (IC, Tech Lead, Comms)            │
│ ☐ Create and maintain runbooks for common issues               │
│ ☐ Use dedicated incident channels for communication            │
│ ☐ Document timeline in real-time                                │
│ ☐ Post regular status updates (every 30 min minimum)           │
│ ☐ Prioritize mitigation over root cause during incident        │
│ ☐ Conduct blameless postmortems within 48 hours                │
│ ☐ Track and complete action items from postmortems             │
│ ☐ Share learnings across the organization                       │
│ ☐ Practice incident response regularly (game days)             │
│ ☐ Review and update playbooks based on learnings               │
└─────────────────────────────────────────────────────────────────┘
```
