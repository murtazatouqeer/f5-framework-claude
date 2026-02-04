# System Inventory
## [System Name] - Current System Discovery

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | SYS-INV-[PROJECT]-001 |
| Version | 1.0 |
| Created | [DATE] |
| Last Updated | [DATE] |
| Status | In Progress / Complete |
| Author | [NAME] |

---

## 1. System Access Information

### 1.1 Environments
| Environment | URL | Purpose | Access Level |
|-------------|-----|---------|--------------|
| Production | [URL] | Live system | Read-only |
| Staging | [URL] | Testing | Full access |
| Development | [URL] | Dev work | Full access |

### 1.2 User Accounts for Discovery
| Role | Username | Environment | Access Granted |
|------|----------|-------------|----------------|
| Admin | [username] | All | [DATE] |
| Manager | [username] | Production | [DATE] |
| User | [username] | Production | [DATE] |
| [Custom Role] | [username] | [Env] | [DATE] |

---

## 2. Module Inventory

### 2.1 Module Summary
| Module ID | Module Name | Status | Screens | Users | Priority |
|-----------|-------------|--------|---------|-------|----------|
| MOD-001 | [Name] | Active | [X] | [Roles] | High |
| MOD-002 | [Name] | Active | [X] | [Roles] | Medium |
| MOD-003 | [Name] | Deprecated | [X] | [Roles] | Low |

### 2.2 Module Details

#### MOD-001: [Module Name]
| Field | Value |
|-------|-------|
| Module ID | MOD-001 |
| Name | [Module Name] |
| Description | [What this module does] |
| Status | Active / Deprecated / Partially Working |
| Primary Users | [Roles that use this module] |
| Access Path | [URL or Navigation] |
| Business Owner | [Name/Department] |

**Screens in this Module:**
| Screen ID | Screen Name | Type | Access Path |
|-----------|-------------|------|-------------|
| SCR-001 | [Name] | List/Form/Report | /path |
| SCR-002 | [Name] | List/Form/Report | /path |

**Key Features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]

**Known Issues:**
- [Issue 1 - if any]

---

## 3. Screen Inventory

### 3.1 Screen Summary
| Screen ID | Name | Module | Type | Users | Screenshot |
|-----------|------|--------|------|-------|------------|
| SCR-001 | [Name] | [Module] | List | [Roles] | [Link] |
| SCR-002 | [Name] | [Module] | Form | [Roles] | [Link] |
| SCR-003 | [Name] | [Module] | Report | [Roles] | [Link] |
| SCR-004 | [Name] | [Module] | Dashboard | [Roles] | [Link] |

### 3.2 Screen Details

#### SCR-001: [Screen Name]
| Field | Value |
|-------|-------|
| Screen ID | SCR-001 |
| Name | [Screen Name] |
| Module | [Parent Module] |
| Type | List / Form / Report / Dashboard / Wizard |
| URL/Route | [Path] |
| Access Roles | [Who can access] |
| Screenshot | ![Screenshot](screenshots/scr-001.png) |

**Purpose:**
[What this screen is used for]

**UI Elements:**
| Element | Type | Description | Data Source |
|---------|------|-------------|-------------|
| [Element 1] | Table | Shows list of X | [Table/API] |
| [Element 2] | Form Field | Input for Y | [Table.field] |
| [Element 3] | Button | Action Z | [Endpoint] |
| [Element 4] | Dropdown | Select from | [Lookup table] |

**User Actions Available:**
| Action | Description | Permissions |
|--------|-------------|-------------|
| View | View records | [Roles] |
| Create | Add new record | [Roles] |
| Edit | Modify record | [Roles] |
| Delete | Remove record | [Roles] |
| Export | Export to Excel | [Roles] |

**Navigation:**
- **From:** [Which screens link here]
- **To:** [Which screens this links to]

**Notes:**
[Any observations about this screen]

---

## 4. Feature Inventory

### 4.1 Feature Summary by Module

#### Module: [Module Name]
| Feature ID | Feature Name | Type | Status | Discovery Source |
|------------|--------------|------|--------|------------------|
| FEA-001 | [Name] | CRUD | Active | Observation |
| FEA-002 | [Name] | Workflow | Active | Interview |
| FEA-003 | [Name] | Report | Active | Code Analysis |

### 4.2 Feature Details

#### FEA-001: [Feature Name]
| Field | Value |
|-------|-------|
| Feature ID | FEA-001 |
| Name | [Feature Name] |
| Module | [Module] |
| Type | CRUD / Workflow / Report / Integration / Batch |
| Status | Active / Deprecated / Bug |
| Discovered From | Observation / Interview / Code / Database |

**Description:**
[What this feature does]

**User Flow:**
1. User navigates to [screen]
2. User performs [action]
3. System does [result]
4. [Continue flow...]

**Related Screens:**
- [SCR-001] - [Role]
- [SCR-002] - [Role]

**Related Data:**
- [Table/Entity names]

**Business Rules Observed:**
- [Rule 1]
- [Rule 2]

**Edge Cases Noted:**
- [Edge case 1]
- [Edge case 2]

---

## 5. User Role Inventory

### 5.1 Role Summary
| Role ID | Role Name | User Count | Modules Access | Description |
|---------|-----------|------------|----------------|-------------|
| ROLE-001 | Admin | [X] | All | System administrator |
| ROLE-002 | Manager | [X] | [List] | Department manager |
| ROLE-003 | User | [X] | [List] | Regular user |

### 5.2 Role Details

#### ROLE-001: Admin
| Field | Value |
|-------|-------|
| Role ID | ROLE-001 |
| Name | Admin |
| Description | [What this role does] |
| Estimated Users | [X] users |

**Module Access:**
| Module | Access Level |
|--------|--------------|
| [Module 1] | Full |
| [Module 2] | Full |
| [Module 3] | View Only |

**Key Responsibilities:**
- [Responsibility 1]
- [Responsibility 2]

**Interviewed Users:**
| Name | Department | Interview Date |
|------|------------|----------------|
| [Name] | [Dept] | [Date] |

---

## 6. Report Inventory

### 6.1 Report Summary
| Report ID | Name | Type | Frequency | Users |
|-----------|------|------|-----------|-------|
| RPT-001 | [Name] | Screen | Daily | [Roles] |
| RPT-002 | [Name] | Export | Weekly | [Roles] |
| RPT-003 | [Name] | Scheduled | Monthly | [Roles] |

### 6.2 Report Details

#### RPT-001: [Report Name]
| Field | Value |
|-------|-------|
| Report ID | RPT-001 |
| Name | [Report Name] |
| Type | Screen / Export / Scheduled / Print |
| Location | [URL/Menu path] |
| Users | [Roles] |
| Frequency | Daily / Weekly / Monthly / Ad-hoc |
| Export Formats | PDF / Excel / CSV |

**Purpose:**
[What this report shows and why it's used]

**Data Sources:**
- [Table 1]
- [Table 2]

**Filters Available:**
| Filter | Type | Required |
|--------|------|----------|
| Date Range | Date picker | Yes |
| [Filter 2] | Dropdown | No |

**Screenshot:**
![Report](screenshots/rpt-001.png)

---

## 7. Integration Points Observed

### 7.1 Integration Summary
| Int ID | System | Direction | Type | Status |
|--------|--------|-----------|------|--------|
| INT-001 | [System] | Outbound | API | Active |
| INT-002 | [System] | Inbound | File | Active |
| INT-003 | [System] | Bi-directional | MQ | Unknown |

### 7.2 Integration Details

#### INT-001: [External System Name]
| Field | Value |
|-------|-------|
| Integration ID | INT-001 |
| External System | [Name] |
| Direction | Inbound / Outbound / Bi-directional |
| Type | API / File / Message Queue / Database |
| Status | Active / Deprecated / Unknown |

**Observed Behavior:**
[What we observed about this integration]

**Questions for Stakeholders:**
- [Question 1]
- [Question 2]

---

## 8. Discovery Progress

### 8.1 Coverage Summary
| Category | Total | Documented | Coverage |
|----------|-------|------------|----------|
| Modules | [X] | [X] | [X]% |
| Screens | [X] | [X] | [X]% |
| Features | [X] | [X] | [X]% |
| Reports | [X] | [X] | [X]% |
| Integrations | [X] | [X] | [X]% |

### 8.2 Discovery Log
| Date | Activity | Items Discovered | Notes |
|------|----------|------------------|-------|
| [Date] | Module walkthrough | [X] screens | With [Person] |
| [Date] | Database analysis | [X] tables | Main entities |
| [Date] | API review | [X] endpoints | From swagger |

### 8.3 Open Questions
| # | Question | Category | Status |
|---|----------|----------|--------|
| 1 | [Question] | [Module/Feature] | Open |
| 2 | [Question] | [Module/Feature] | Answered |

### 8.4 Access Issues
| # | Issue | Impact | Resolution |
|---|-------|--------|------------|
| 1 | [Issue] | [Impact] | [Resolution] |

---

## 9. Screenshots Index

### 9.1 Screenshot Catalog
| File | Screen | Captured | Notes |
|------|--------|----------|-------|
| scr-001.png | [Screen Name] | [Date] | Main view |
| scr-002.png | [Screen Name] | [Date] | Form view |
| scr-003.png | [Screen Name] | [Date] | With data |

### 9.2 Screenshot Directory Structure
```
screenshots/
├── modules/
│   ├── module-001/
│   │   ├── scr-001-list.png
│   │   ├── scr-001-form.png
│   │   └── scr-001-detail.png
│   └── module-002/
│       └── ...
├── reports/
│   ├── rpt-001.png
│   └── ...
└── workflows/
    └── ...
```

---

## 10. Next Steps

### 10.1 Remaining Discovery Tasks
| Task | Priority | Estimated Time | Owner |
|------|----------|----------------|-------|
| [Task 1] | High | [X] hours | [Name] |
| [Task 2] | Medium | [X] hours | [Name] |

### 10.2 Stakeholder Interviews Needed
| Stakeholder | Role | Topic | Scheduled |
|-------------|------|-------|-----------|
| [Name] | [Role] | [Topic] | [Date/Pending] |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [DATE] | [NAME] | Initial inventory |

---

*Generated by F5 Framework - Legacy Migration Workflow*
