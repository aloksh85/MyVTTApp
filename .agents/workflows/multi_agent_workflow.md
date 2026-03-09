---
description: Multi-Agent Roleplay Protocol for high-quality, consistent code generation
---
# The Multi-Agentic Protocol

To ensure consistent quality, reduce trial-and-error, and prevent regression, the agent must simulate a multi-agent framework. Whenever tasked with a complex feature, bug fix, or refactor, you must explicitly step through the following phases and embody these distinct agent personas.

## Phase 0: The Read-in (CRITICAL)
Before any code is planned or written, the agent MUST use the `view_file` tool to read `lessons.md`. This file contains the historical context, mistakes, and best practices of this specific codebase. Attempting to write code without internalizing `lessons.md` is a violation of the multi-agent protocol.

## Phase 1: Agent 1 (The Code Writer)
**Goal:** Implement the feature and its automated tests.
1. Draft the implementation plan based on the user's requirements.
2. Cross-reference the plan with the constraints found in `lessons.md`.
3. Write the code.
4. Write the corresponding automated tests (e.g., `pytest`).

## Phase 2: Agent 2 (The Reviewer)
**Goal:** Critically attack the code produced by Agent 1 before the user sees it.
1. Be highly skeptical. Assume Agent 1 made a mistake.
2. Review the code for edge cases, performance bottlenecks, and platform-specific quirks.
3. Verify that the implemented code adheres *strictly* to the rules in `lessons.md`.
4. Run the test suite. 
5. If issues or potential regressions are found, Agent 2 forces Agent 1 to rewrite the code *before* notifying the user that the task is done.

## Phase 3: Agent 3 (The Maintainer)
**Goal:** Extract knowledge and persist it.
1. After the feature is built and working, analyze the iteration process. 
2. Ask: "What caused friction during this task? What errors did we hit? What system/OS quirks did we discover?"
3. Condense these observations into generalized, actionable rules.
4. Use the `multi_replace_file_content` or `write_to_file` tools to strictly update `lessons.md` with these new findings so the system gets smarter over time.
