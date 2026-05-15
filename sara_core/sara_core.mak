SARA CORE PREP

Pillar:
- sara_core

Purpose:
- Define the internal architecture and decision structure for SARA Gen 0.
- Hold the system shape that later code must follow.

Gen 0 scope:
- Python-first.
- No direct UI ownership.
- No final security exception ownership.

Core responsibilities:
- Define process states.
- Define reasoning stages.
- Define what counts as a valid improvement.
- Define where proven attempts are stored for reuse.
- Define handoff rules to Control and Mama.

Inputs:
- user request
- current task state
- prior accepted attempt record
- model output candidate

Outputs:
- normalized task plan
- architecture decision
- improvement target
- approval or rejection recommendation for Control

Restrictions:
- Core does not execute tools directly.
- Core does not own long-term storage directly.
- Core does not bypass Security rules.

First Python target when implementation begins:
- sara_core.py

First implementation focus:
- state machine for request -> plan -> attempt -> review -> improve

Success condition for pre-prep:
- Core role is fixed before code generation starts.

Do not remove this file when updates are added.
Append newer rules below existing rules.