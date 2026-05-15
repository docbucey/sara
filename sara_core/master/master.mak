SARA CORE MASTER

Pillar:
- sara_core

Purpose:
- Aggregate local and distant results into one bounded master status.

Responsibilities:
- combine result.meta.json and distant_end.json
- publish final pass/fail/unknown state
- preserve pillar summary for orchestrator use

Primary JSON artifact:
- ../master_result.json