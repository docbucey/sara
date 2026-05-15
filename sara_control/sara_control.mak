SARA CONTROL PREP

Pillar:
- sara_control

Purpose:
- Define execution control for SARA Gen 0.
- Own routing, gating, sequencing, and tool boundary enforcement.

Gen 0 scope:
- Python-first.
- Main early training target together with Core.

Control responsibilities:
- accept normalized plan from Core
- decide next allowed action
- route work to model/tool layer
- stop invalid or unsafe execution paths
- capture execution result for Mama and Security

Inputs:
- normalized task plan from Core
- workspace state
- tool availability
- security allow/deny result

Outputs:
- next action packet
- execution order
- tool call request
- blocked reason when action is denied

Restrictions:
- Control must not redefine Core architecture.
- Control must not store final historical truth without Mama.
- Control must not override Security deny decisions.

First Python target when implementation begins:
- sara_control.py

First implementation focus:
- controlled dispatcher for task -> validation -> tool/action -> result capture

Success condition for pre-prep:
- Control can be trained as the operational shell around Core.

Do not remove this file when updates are added.
Append newer rules below existing rules.