---
name: tdd-workflow
description: AI-paired Test-Driven Development for Python and pytest. The human defines what and why; the AI defines how through tests-first execution.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
version: 2.0
priority: HIGH
---

# TDD Workflow

> Write tests before logic. Treat tests as the executable contract.

---

## 1. When To Activate

| Scenario | Use TDD? | Why |
|----------|----------|-----|
| New feature | High | Behavior is still negotiable and tests define it fast |
| Bug fix | High | Reproduce first, then lock the regression |
| Complex business rule | High | Edge cases matter more than implementation style |
| Refactor with behavior freeze | High | Tests protect the contract |
| Exploratory spike | Medium | Spike first, then restart with TDD |
| Pure layout or visual polish | Low | Behavior is not the main risk |

---

## 2. Responsibility Split

### Pairing Roles

| Role | Owns |
|------|------|
| **Navigator / Architect (Human)** | Business context, rules, constraints, success criteria, scope |
| **Pilot / AI** | Test scenarios, edge cases, pytest boilerplate, mocks, minimal implementation, safe refactor |

### Human Responsibilities

- Define what the feature must do
- Explain why the behavior matters
- Provide business rules, constraints, and out-of-scope cases
- Confirm expected inputs, outputs, and failure modes when they are not obvious

### AI Responsibilities

- Translate requirements into a scenario inventory before touching production logic
- Surface missing edge cases and ambiguous behaviors early
- Write failing tests first
- Generate the boring parts fast: pytest structure, fixtures, stubs, mocks, parametrization
- Implement the minimum code to make tests pass
- Refactor without changing behavior while keeping the suite green

> Rule: if the business rule is unclear enough to change test outcomes, ask a targeted question before writing code.

---

## 3. Required Input From The Human

Provide as much of this as possible:

| Input | Example |
|-------|---------|
| Goal | "Validate mirroring eligibility for HF918V2 devices" |
| Business rule | "Blocked devices must return a structured validation error" |
| Constraints | "Keep current response shape" |
| Out of scope | "Do not redesign the repository layer" |
| Expected failures | "Missing device id returns 400" |

If one of these is missing, the AI should infer only low-risk defaults and ask only when the ambiguity changes behavior.

---

## 4. Standard Loop

```
0. Contract -> Turn the request into behaviors and edge cases
1. RED      -> Write failing tests first
2. GREEN    -> Implement the minimum code to pass
3. REFACTOR -> Improve structure without changing behavior
4. REVIEW   -> Summarize what the tests now guarantee
```

### Phase 0: Contract Before Code

Before the first test, the AI should produce:

1. Behavior list
2. Edge-case list
3. Proposed test names
4. Expected error conditions

Do not start production logic before this contract exists.

---

## 5. RED Phase Rules

### What To Produce First

| Priority | Focus | Example |
|----------|-------|---------|
| 1 | Happy path | "should return eligible candidates for valid input" |
| 2 | Validation | "should reject empty device list" |
| 3 | Error state | "should raise when dependency times out" |
| 4 | Boundary | "should handle exactly one candidate" |
| 5 | Regression | "should preserve response status contract" |

### RED Rules

- The first visible artifact is a failing test, not production code
- Test names describe behavior, not implementation details
- One behavior per test when practical
- Verify failure on purpose before moving to GREEN
- Prefer AAA: Arrange, Act, Assert
- Prefer behavior assertions over internal call-count assertions unless interaction is the contract

---

## 6. GREEN Phase Rules

| Principle | Meaning |
|-----------|---------|
| **Minimum code** | Write only what the failing test requires |
| **No speculation** | Do not build extra branches for imagined future use |
| **No premature optimization** | Correctness first |
| **Keep the contract visible** | Map each code change to a failing test |

### GREEN Rules

- Pass the current failing test with the simplest implementation
- Do not widen scope while the suite is still red
- Avoid refactoring during GREEN unless required to make the test pass

---

## 7. REFACTOR Phase Rules

| Improve | Action |
|---------|--------|
| Duplication | Extract helpers only after a pattern is proven |
| Naming | Rename for intent and domain clarity |
| Structure | Move code to the right layer once behavior is locked |
| Complexity | Flatten branching and remove accidental complexity |

### REFACTOR Rules

- All tests must stay green
- Refactor in small, reversible steps
- Prefer deleting complexity over adding abstractions
- If a refactor changes behavior, return to RED and encode that behavior first

---

## 8. Python + Pytest Defaults

### Preferred Test Stack

| Need | Default |
|------|---------|
| Test runner | `pytest` |
| Async tests | `pytest.mark.asyncio` |
| Shared setup | fixtures |
| Scenario matrix | `pytest.mark.parametrize` |
| Monkey patching | `monkeypatch` |
| Mocks and spies | `mocker` or `unittest.mock` |

### Recommended Shape

```python
def test_should_do_expected_behavior():
    # Arrange
    ...

    # Act
    result = ...

    # Assert
    assert result == ...
```

### Default Guidance

- Keep test names explicit and behavior-oriented
- Use fixtures for reusable setup, not to hide business meaning
- Prefer parametrization for boundary tables and validation matrices
- Mock external systems, network, time, randomness, and database access in unit tests
- Do not mock the code under test

---

## 9. Edge-Case Checklist

Before implementation, the AI should actively probe these categories:

| Category | Questions |
|----------|-----------|
| Empty input | What happens with `None`, empty strings, empty lists, or missing fields? |
| Invalid input | What happens with wrong type, wrong format, or unsupported values? |
| Boundaries | What happens at min, max, first, last, zero, and one? |
| State | What happens when data already exists, is locked, expired, or partially processed? |
| Dependency failure | What happens when DB/API/cache/timeouts fail? |
| Ordering | Does result order matter? |
| Idempotency | Is retry safe? |
| Regression | Which old bug or contract must never come back? |

> Rule: the AI should propose edge cases even when the human does not mention them.

---

## 10. Fixtures, Stubs, And Mocks

### Use Fixtures For

- Reusable domain objects
- Shared environment setup
- Lightweight factories or builders
- Common fake dependencies

### Use Mocks For

- External APIs
- Database access in unit tests
- Time, randomness, UUIDs, and network effects
- Observing side effects when the side effect itself is part of the contract

### Avoid

- Over-mocking simple value objects
- Giant fixtures that hide the business scenario
- Verifying implementation details instead of outcomes

---

## 11. Prompt Contract For AI Pairing

Use or adapt this prompt when starting a task:

```text
Context:
- [feature or bug]
- [business rules]
- [constraints]

Your job:
1. List test scenarios first
2. List edge cases before writing production logic
3. Write failing pytest tests and needed fixtures/mocks
4. Implement only the minimum code to make tests pass
5. Refactor only after the suite is green

Do not start with production code.
```

### Expected AI Output Order

1. Scenario inventory
2. Edge-case inventory
3. Failing test plan
4. Test code
5. Minimal implementation
6. Refactor summary

---

## 12. Definition Of Done

- A behavior list exists before production code changes
- At least one test failed before implementation started
- The final code passes the test suite
- Edge cases were either covered or explicitly deferred
- The AI can explain which test protects which business rule
- Refactor did not change externally visible behavior

---

## 13. Anti-Patterns

| Don't | Do |
|------|----|
| Implement first, test later | Make the test the first artifact |
| Ask the AI for "the code" with no rules | Provide business rules and success criteria |
| Test private implementation details | Test observable behavior |
| Hide everything in giant fixtures | Keep scenarios readable |
| Mock every dependency by default | Mock only what crosses process or time boundaries |
| Add abstractions during GREEN | Keep GREEN minimal and boring |

---

> Remember: in AI-paired TDD, the human owns intent, the AI owns execution, and the tests keep both honest.
