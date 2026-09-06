# Antigravity Workspace Coding Rules: Rule Engine Standard

## 1. Core Rule: Conditional Logic Standard
- Never write nested or chained conditional statements (`if-elif-else`) for business logic, data filtering, classification, routing, or state transitions.
- All conditional decision trees and evaluation criteria must be implemented declaratively using the Python `rule-engine` package (v5.x).
- Standard Python `if` statements are strictly restricted to low-level guard clauses (e.g., checking `if not data: return None` or checking error exceptions).

## 2. Implementation Specifications

### Syntax & Evaluation Patterns
- Always compile expressions using `rule_engine.Rule("<expression>")`.
- For evaluating Python dictionaries, access keys directly by attribute name or bracket indexing as supported by the context:
  ```python
  import rule_engine

  # Correct declarative rule definition
  high_priority_rule = rule_engine.Rule("congestion_level == 'high' and speed < 30")

  # Evaluating incoming payload
  payload = {"congestion_level": "high", "speed": 22}
  is_match = high_priority_rule.matches(payload)
  ```

### Complex Logic & Multi-Rule Mapping
When mapping multiple conditions to corresponding actions or outcomes, do not use sequential `elif` chains. Instead, use a structured list of rule tuples or a rule registry:

```python
import rule_engine

DECISION_PIPELINE = [
    (rule_engine.Rule("status == 'critical' or load > 90"), "TRIGGER_EMERGENCY"),
    (rule_engine.Rule("status == 'warning' and load > 70"), "SCALE_RESOURCES"),
    (rule_engine.Rule("status == 'nominal'"), "MONITOR"),
]

def evaluate_state(context: dict) -> str:
    for rule, action in DECISION_PIPELINE:
        if rule.matches(context):
            return action
    return "DEFAULT_ACTION"
```

### Filtering Collections
When filtering datasets, records, or lists of dictionaries, prefer `rule.filter(iterable)` over native list comprehensions with complex filtering conditionals:

```python
# Preferred filtering approach
active_alerts = list(alert_rule.filter(stream_records))
```

## 3. Code Generation Requirements for Agent
- Whenever generating, refactoring, or scaffolding code in this workspace, audit the logic first.
- If any multi-condition decision or filtering logic is required, import `rule_engine` and define the conditions as compiled rules.
- Keep rule definitions separated from business logic execution (e.g., at module-level constants or configuration objects) so they remain easily editable.

---

# PONYTAIL ARCHITECTURE & CODE GOVERNANCE RULES
# STATUS: MANDATORY & NON-NEGOTIABLE
# SCOPE: GLOBAL (Applied to all generations, refactors, scripts, and queries)

## RULE 1: STRICT LEAST PRIVILEGE & ACCESS BOUNDARIES (ZERO ESCALATION)
1. NEVER allow a lower-tier role (e.g., `TECHNICIAN`, `OPERATOR`, `AUDITOR`, `GIS_OPERATOR`) to mutate, view, or touch records outside their explicit domain.
2. `TECHNICIAN` and `MAINTENANCE_OFFICER` are strictly restricted from:
   - Vehicle Route Tracking, trajectory points, and ANPR plate searches.
   - Watchlist creation, editing, or viewing.
   - Live video stream URLs, raw RTSP paths, and central surveillance walls.
   - Camera Registry creation, updates, and deletion.
3. Automated telemetry fields (`health_status`, `health_score`, `last_heartbeat`, `packet_loss_pct`) are SYSTEM-GENERATED and IMMUTABLE by humans. NEVER add manual edit inputs, toggles, or direct API update paths for health telemetry.

## RULE 2: SECURE AUTHENTICATION & CREDENTIAL DISCIPLINE
1. Never bypass password verification. Compare against stored cryptographic hashes (Argon2id/bcrypt) before issuing JWT tokens.
2. NEVER store, log, or return plaintext passwords or secrets in API responses.
3. Form input fields on login/register must ALWAYS initialize as empty strings `""`. Never pre-fill passwords or render one-click bypass buttons.
4. All incoming protected routes MUST validate JWT signatures, algorithms (`HS256`/`RS256`), and expiration claims using standard middleware.

## RULE 3: CRASH-RESILIENT ARCHITECTURE & ERROR HANDLING
1. NEVER allow frontend unhandled runtime exceptions (`TypeError: undefined is not an object`). Always apply defensive null-checks (`?.`), fallback defaults (`[]`, `{}`), and wrap major views in React Error Boundaries.
2. Backend routes must return standard, typed JSON exceptions with exact HTTP status codes (`400`, `401`, `403`, `404`, `422`) instead of crashing worker threads or leaking 500 stack traces.
3. Dynamic client routing must redirect unauthorized attempts back to the user's role-authorized home view with a toast alert rather than rendering a blank white page.

## RULE 4: MULTI-TENANT ROW-LEVEL ISOLATION
1. Every query executed by a `DEPARTMENT_ADMIN` or departmental `OPERATOR` must be explicitly scoped by their authenticated `department_id`.
2. Prevent horizontal privilege escalation: users can never access or modify assets belonging to another department by altering URL IDs.

## RULE 5: MODEL 3 FEDERATION & SECRETS GOVERNANCE
1. Maintain the separation between central metadata and departmental video: metadata/events are federated; video feeds are accessed on-demand and never saved centrally.
2. All external VMS credentials (passwords, tokens, ONVIF secrets) must be encrypted at rest using AES-256-GCM.
3. Ensure external VMS communication remains non-intrusive: read-only polling, stream brokering, and event subscriptions only. NEVER overwrite or delete local departmental configurations or recordings.

## RULE 6: IMMUTABLE AUDIT TRAIL
1. Every state mutation, login, failed authorization attempt, and sensitive data query (e.g., license plate searches) must automatically append an immutable record to `SecurityAuditLog`.
