SARA MAMA PREP

Pillar:
- sara_mama

Purpose:
- Define memory, attempt history, lesson capture, and reuse pathways for SARA Gen 0.

Gen 0 scope:
- Python-first.
- Supports Core and Control rather than replacing them.

Mama responsibilities:
- record working attempts
- record failed attempts with reason
- extract lessons from user and system mistakes
- present prior useful paths back into the flow
- keep improvement history organized by task type

Inputs:
- attempt result
- failure reason
- accepted output
- user correction

Outputs:
- reusable memory packet
- history summary
- suggested retry path
- prior-success reference

Restrictions:
- Mama does not execute tools.
- Mama does not approve unsafe actions.
- Mama does not become the planner; Core remains planner.

First Python target when implementation begins:
- sara_mama.py

First implementation focus:
- attempt ledger and lesson extraction structure

Success condition for pre-prep:
- Historical learning path exists before self-improvement logic is added.

PlainJain-first Gen1 baseline addendum:
- Initial Mama spec base for Gen1 starts from ai_llc/plainjainllm.slam.
- Mama must remain model-agnostic: external traditional model files are selectable profiles, not fixed dependencies.
- First supported profiles are plainjain_native and ollama_default.
- Mama outputs must preserve one stable memory packet contract regardless of model profile used.
- Mama may reuse existing Gen0 features (attempt ledger, lesson extraction, retry suggestion) while introducing profile routing.
- Baseline runtime target for this phase is sara_mamagen1.py.
- Evolution path: add profiles and routing logic through evolve shunts without breaking the base packet schema.

Do not remove this file when updates are added.
Append newer rules below existing rules.