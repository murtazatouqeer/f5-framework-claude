# F5 Framework Agents

> Specialized AI agents that provide domain expertise.
> Agents are invoked using `@f5:[agent-name]` or auto-activated based on context.

## Agent Categories

### 1. Domain Agents

Domain agents have deep knowledge of specific business domains.

#### @f5:domain-fintech
**Expertise:** Financial technology, trading systems, payment processing
**Knowledge:**
- Stock trading workflows and regulations
- Payment processing (PCI-DSS compliance)
- Banking operations and KYC/AML
- Cryptocurrency and blockchain
- Fraud detection patterns
- Financial calculations (interest, fees, taxes)

**Auto-Activation Keywords:**
`payment`, `transaction`, `trading`, `banking`, `stock`, `order`, `portfolio`, `wallet`, `transfer`, `balance`

**Best For:**
- Implementing financial calculations
- Designing trading systems
- Payment gateway integration
- Regulatory compliance review

---

#### @f5:domain-ecommerce
**Expertise:** E-commerce platforms, retail systems, marketplaces
**Knowledge:**
- Shopping cart and checkout flows
- Inventory management
- Order fulfillment
- Pricing and promotions
- Product catalog management
- Multi-vendor marketplaces

**Auto-Activation Keywords:**
`cart`, `checkout`, `order`, `product`, `inventory`, `catalog`, `shipping`, `discount`, `coupon`

**Best For:**
- Shopping experience design
- Inventory system implementation
- Order processing workflows
- Pricing engine development

---

#### @f5:domain-healthcare
**Expertise:** Healthcare systems, medical applications
**Knowledge:**
- Electronic Health Records (EHR)
- HIPAA compliance
- Patient data management
- Clinical workflows
- Medical terminology (ICD-10, CPT)
- Telemedicine systems

**Auto-Activation Keywords:**
`patient`, `medical`, `health`, `clinical`, `diagnosis`, `prescription`, `appointment`, `doctor`, `hospital`

**Best For:**
- Patient portal development
- Clinical decision support
- Healthcare data integration
- Compliance implementation

---

#### @f5:domain-entertainment
**Expertise:** Gaming, streaming, media platforms
**Knowledge:**
- Game mechanics and balance
- Real-time systems
- Content delivery
- User engagement patterns
- Live streaming architecture
- Betting and odds systems

**Auto-Activation Keywords:**
`game`, `stream`, `media`, `content`, `player`, `score`, `bet`, `odds`, `video`, `live`

**Best For:**
- Game backend systems
- Streaming infrastructure
- Real-time features
- Engagement mechanics

---

### 2. Role Agents

Role agents provide expertise based on software development roles.

#### @f5:architect
**Expertise:** System design, architecture patterns, scalability
**Responsibilities:**
- Design system architecture
- Choose appropriate patterns
- Evaluate trade-offs
- Plan for scalability
- Define service boundaries
- Review technical decisions

**Output Style:**
- Architecture diagrams (text-based)
- Trade-off analysis tables
- Decision records (ADRs)

---

#### @f5:security
**Expertise:** Application security, vulnerability assessment
**Responsibilities:**
- OWASP Top 10 review
- Authentication/authorization design
- Encryption recommendations
- Input validation
- Dependency security
- Security code review

**Output Style:**
- Vulnerability reports
- Security checklists
- Risk assessments
- Remediation guides

---

#### @f5:qa
**Expertise:** Testing strategy, quality assurance
**Responsibilities:**
- Test strategy design
- Coverage analysis
- Edge case identification
- Test quality review
- Bug triage
- Performance testing guidance

**Output Style:**
- Test plans
- Coverage reports
- Bug reports
- Test case suggestions

---

#### @f5:ba
**Expertise:** Business analysis, requirements engineering
**Responsibilities:**
- Requirements elicitation
- Use case development
- Process modeling
- Stakeholder management
- Gap analysis
- Acceptance criteria

**Output Style:**
- Requirements documents
- Use case diagrams
- Process flows
- Stakeholder matrices

---

#### @f5:devops
**Expertise:** Infrastructure, CI/CD, deployment
**Responsibilities:**
- Pipeline design
- Infrastructure as code
- Container orchestration
- Monitoring setup
- Deployment strategies
- Environment management

**Output Style:**
- Pipeline configurations
- Infrastructure scripts
- Deployment guides
- Monitoring dashboards

---

#### @f5:frontend
**Expertise:** UI/UX development, client-side architecture
**Responsibilities:**
- Component architecture
- State management
- Performance optimization
- Accessibility (a11y)
- Responsive design
- UI framework guidance

**Output Style:**
- Component specifications
- UI patterns
- Performance recommendations
- Accessibility audits

---

#### @f5:backend
**Expertise:** API design, database architecture, server-side systems
**Responsibilities:**
- API design (REST, GraphQL)
- Database schema design
- Query optimization
- Caching strategies
- Service integration
- Error handling patterns

**Output Style:**
- API specifications
- Schema designs
- Query analysis
- Integration guides

---

#### @f5:compliance
**Expertise:** Regulatory compliance, standards adherence
**Responsibilities:**
- GDPR compliance
- PCI-DSS requirements
- HIPAA guidelines
- SOC 2 preparation
- Audit support
- Data privacy

**Output Style:**
- Compliance checklists
- Gap assessments
- Audit reports
- Policy recommendations

---

### 3. Workflow Agents

Workflow agents assist with specific development activities.

#### @f5:reviewer
**Purpose:** Code review and best practices enforcement
**Actions:**
- Review code changes
- Check coding standards
- Identify potential issues
- Suggest improvements
- Verify patterns

---

#### @f5:documenter
**Purpose:** Documentation generation and maintenance
**Actions:**
- Generate API docs
- Create README files
- Write inline comments
- Produce architecture docs
- Update changelogs

---

#### @f5:tester
**Purpose:** Test generation and coverage improvement
**Actions:**
- Generate unit tests
- Create integration tests
- Identify edge cases
- Mock external services
- Write E2E scenarios

---

#### @f5:optimizer
**Purpose:** Performance optimization
**Actions:**
- Profile performance
- Identify bottlenecks
- Suggest optimizations
- Review queries
- Analyze algorithms

---

#### @f5:refactorer
**Purpose:** Code improvement and cleanup
**Actions:**
- Identify code smells
- Apply design patterns
- Reduce complexity
- Improve naming
- Remove duplication

---

## Auto-Activation Matrix

### By Domain

| Project Domain | Auto-Activated Agents |
|----------------|----------------------|
| fintech | domain-fintech, security, compliance |
| e-commerce | domain-ecommerce, frontend |
| healthcare | domain-healthcare, security, compliance |
| entertainment | domain-entertainment, frontend |
| logistics | domain-logistics, backend |
| education | domain-education, frontend |

### By Context

| Context | Auto-Suggested Agents |
|---------|----------------------|
| SIP active | qa, reviewer |
| Tests failing | qa, tester |
| Security keywords | security |
| Performance issues | optimizer, backend |
| New feature | ba, architect |
| Refactoring | refactorer, reviewer |
| Deployment | devops |

### By File Type

| File Extension | Suggested Agents |
|----------------|------------------|
| `.tsx`, `.jsx` | frontend |
| `.spec.ts`, `.test.ts` | qa, tester |
| `.sql` | backend |
| `Dockerfile`, `.yml` | devops |
| `.md` | documenter |

---

## Multi-Agent Collaboration

### Patterns

#### Security Review Pattern
```
@f5:security → @f5:compliance → @f5:reviewer
```

#### Feature Development Pattern
```
@f5:ba → @f5:architect → @f5:developer → @f5:tester → @f5:reviewer
```

#### Performance Optimization Pattern
```
@f5:optimizer → @f5:backend → @f5:architect
```

### Conflict Resolution

When agents have conflicting recommendations:
1. Security takes precedence
2. Compliance requirements must be met
3. Performance vs maintainability - discuss trade-offs
4. User decision required for business trade-offs

---

## Invocation Syntax

### Direct Invocation
```
@f5:[agent-name] "instruction"
```

### Multi-Agent
```
@f5:security @f5:architect "review payment system"
```

### With Modes
```
@f5:security "review auth" --think
```

---

## Agent Configuration

### Project-Level Agent Config

In `.f5/config.json`:
```json
{
  "agents": {
    "auto_activation": true,
    "default_agents": ["architect", "security"],
    "disabled_agents": [],
    "custom_rules": {
      "payment": ["domain-fintech", "security", "compliance"]
    }
  }
}
```

---
*F5 Framework v2.0*
