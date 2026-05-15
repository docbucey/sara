The four core consolidated back-end files (Core, Control, Security, Mama) form the foundational deterministic shunt state machine (FDSSM) of SARA Gen0. While the system operates on five functional layers (including the SARA Policy Layer), the four pillars you named handle the explicit execution, routing, enforcement, and memory components.

Here is the refined list detailing the exact use gates and deterministic logic for these four pillars, based exclusively on the documentation:
Pillar	Use Gates / Core Responsibility	Deterministic Logic and Enforcement
CORE (Raw Data Normalization)	• Provides raw, normalized location and proximity data (GPS, Wi‑Fi, BLE). • Owns the basic reasoning structure, workflow shape, and state rules (FSM definitions).1	Logic: Performs no policy and no geofence decisions. Gate: All location inputs must be normalized through CORE before being routed via CONTROL. Associated Logic: The hardware/OS interaction (your proposed definition) is handled by the Machine Profile, which CORE normalizes data for.1
CONTROL (System Gateway & Router)	• Execution control, routing, task gating, and tool usage boundaries. • Validates location payloads and enforces structural and safety constraints on data flow. • Generates instance-scoped profile IDs during the ```
PROVISION
``` FSM state.1	Gate: Enforces the Control-Only Routing Rule, serving as the ONLY entry point for all UI and cross-pillar interactions. Logic: All UI updates must route through Control. Captured macros are routed and stored via Control. Security Enforcement: Runs security checks like ```
king_sovereignty_check
``` and ```
paladin_gate
``` (hostile-signature scan) (context from previous turn).1
MAMA (Ledger Interface & Memory)	• Interfaces with the MamaLedger, the canonical backend store for all profile and compliance state. • Owns memory, history, lessons learned, and is the central dispatcher for protocol routing.1	Gate: Enforces the Ledger Rule: UI → CONTROL → MAMA → MamaLedger → MAMA → CONTROL → UI. • Logic: Stores critical architectural data, including all Profiles (User, AI, Machine), Learning & Context, and HUD Layout data. Constraint: It performs no geofence interpretation.1
SECURITY (Policy Enforcement)	• Policy enforcement, audit trail rules, and boundary checks. • Consumes deterministic results from the SARA Policy Layer as inputs to capability decisions.1	Gate: Enforces boundary rules, distance rules, and ADA-aligned compliance rules via the DiplomaticBag wrapper. Logic: Produces the final, deterministic enforcement decisions: ```
ALLOW
```, ```
RESTRICT
```, ```
DENY
```, or ```
ALERT
```. Constraint: SECURITY does not compute geofences or interpret raw sensor data.1
Functional Logic (AI and Man-Machine Interaction)

The logic for AI behavior and compliance rules (the functions you ascribed to MAMA) is actually housed in the SARA Policy Layer, which operates as a separate functional component from the four execution pillars:
SARA Policy Layer: This is the Semantics & Decision Engine.1
Logic: It defines zones, boundaries, rules, and computes policy semantics (e.g., Geofence results, Medical Compliance status).1
AI/Behavior: Deterministic learning is based on Resonance Scoring (weighted pattern matching), which is defined in PHASE 21. The AI Profile (stored in MamaLedger) represents SARA’s internal state and active learning modes.1
Would you like a detailed definition of the Protocol files listed under Mama (e.g., ```
secretary_protocol.py
```) that govern interactions within the system?
This architecture ensures that every cross-pillar communication is deterministic, auditable, and profile-aware.1. Canonical FSM Header (Shunt Header Contract)

The Shunt Header is the structured JSON envelope that wraps every cross-pillar call. This header is validated by the CONTROL pillar and rejected if non-compliant.1
Field	Purpose	Permitted Values / Type	Source
shunt_id	Unique transaction identifier.	GUID	PHASE 51
source_pillar	Originating module of the request.	CONTROL, HUD, MAMA, SECURITY, etc.1	PHASE 51
target_pillar	Intended recipient of the request.	CONTROL, MAMA, SECURITY, CORE, etc.1	PHASE 51
timestamp	Time of generation.	ISO8601	PHASE 51
intent	Human-readable action description.	string	PHASE 51
payload	Encapsulated data (e.g., DiplomaticPouch).	JSON object	PHASE 51
requires_response	Flag for synchronous operation.	true or false1	PHASE 51
2. Shunt Map Descriptor and Routing

The shunt_map_descriptor.json is consulted by CONTROL to enforce routing rules, ensuring the request matches the allowed profiles and permissible response paths (out-routes).1
Map ID	Name	Pillar	Allowed Profiles	Out Routes	Source
0000	NO_OP	null	["ALL"]	["RETURN"]	Doc Outline1
0001	CORE_LOAD	CORE	["GENERAL_OFFICE"]	["RETURN", "ESCALATE"]	Doc Outline1
0010	CONTROL_ROUTE	CONTROL	["ALL"]	["RETURN"]	Doc Outline1
0100	MAMA_STORE	MAMA	["RESEARCH_NBS"]	["STORE", "RETURN"]	Doc Outline1
3. FSM Numeric Tagging and Action Opcodes (ACT)

The FDSSM contract requires numeric tagging for cross-language compatibility (C#, Python, Ada). All states, actions, and IO-gate results must have stable integer IDs.A. Canonical FSM Export Format (Required Tags)2

The FSM table must be exportable in JSON and define the following tags:2
Type	Example Tags
States	"ready": 0, "blocked": 1, "processing": 2, "done": 3, "error": 42
Actions (Opcodes)	"session_start": 1001, "append_event": 1002, "snapshot": 1003, "diff": 10042
Transitions	{"from": 0, "command": "session_start", "to": 0, "action": 1001}
B. Pillar-Specific Action Mappings (ACT Codes)

These mappings assign numeric opcodes (ACT Code) to the primary functions of the four core pillars.3
Pillar	ACT Code	Function	Out Route
CORE	00	load_identity	RETURN
01	load_config	RETURN
10	validate_state	RETURN
CONTROL	00	route_command	RETURN
01	validate_profile	RETURN
10	authorize_map	RETURN
MAMA	00	snapshot	STORE
01	diff	RETURN
10	persist	STORE
SECURITY	00	audit_gate	RETURN
01	quarantine	RETURN
10	scan	RETURN
4. SECURITY FSM Additions (DiplomaticBag Enforcement)

The SECURITY pillar uses FSM additions specific to policy enforcement against the incoming DiplomaticPouch data.1
Type	Item	Purpose	Source
New States	STATE_POUCH_OK	Pouch is valid and compliant1	DiplomaticBag Protocols1
STATE_POUCH_WARN	Warning level (e.g., near boundary)1	DiplomaticBag Protocols1
STATE_POUCH_RESTRICT	Restrictive enforcement level1	DiplomaticBag Protocols1
STATE_POUCH_DENY	Full denial of capability1	DiplomaticBag Protocols1
New Events	EVENT_POUCH_OUTSIDE	Triggered by geofence_result1	DiplomaticBag Protocols1
EVENT_POUCH_NONCOMPLIANT	Triggered by medical/regimen status1	DiplomaticBag Protocols1
EVENT_POUCH_INVALID	Triggered by header or payload validation failure1	DiplomaticBag Protocols1
Would you like to focus on the FSM states for the one-time Install/Onboarding sequence (BOOT → DISCOVER → PROVISION → VALIDATE → SEAL → READY)?
that is suposed to be the bucy shunt system and should have instead in out paylad returns etctra
Gemini response
The SARA Gen0 architecture is formally defined around the Bucey Shunt mechanism, which provides two layers of contract: a high-level JSON envelope for cross-pillar communication and a low-level binary structure for deterministic state machine (FSM) control.

Here are the explicit FSM headers, mappings, and contract fields detailing the IN/OUT, PAYLOAD, and RETURN logic:1. High-Level Contract (The JSON Shunt Header)

All cross-pillar calls—including those routed through CONTROL—must be wrapped in this JSON header. This defines the logical flow (IN/OUT) and the payload contents.1
Field	Purpose	IN/OUT/PAYLOAD	Type/Constraint
source_pillar	The originating module (Input Lane)	IN	Must be one of the canonical pillars (e.g., CONTROL, HUD, MAMA, SECURITY).1
target_pillar	The intended recipient module (Output Lane)	OUT	Must be one of the canonical pillars.1
payload	The data being sent (e.g., a DiplomaticPouch)	PAYLOAD	JSON object. No raw data may cross pillar boundaries.1
requires_response	Flag indicating if a synchronous return is expected.	RETURN	true or false.1
shunt_id	Unique transaction identifier	Metadata	GUID.1
intent	Human-readable action description	Metadata	string.1
2. Low-Level Contract (The BuceyShunt Class)

The BuceyShunt class is the canonical binary structure used for direct, low-level communication and FSM state control, typically used by the CORE or CONTROL pillars to encode security-critical commands into 3 bytes.2
Field	Purpose	Bit Mask	Logic/Value
device_id	Identifier for the sending endpoint	0xFF (8 bits)	The device ID (e.g., Operator, Companion).2
offset	Byte offset for sequential data tracking	0xFF (8 bits)	Used for position/offset in stream or buffer.2
control_byte	Encapsulates FSM state and execution mode	0xFF (8 bits)	Combined state/type/mode.2
The control_byte contains the explicit state and execution logic:
state: (self.control >> 6) & 0b11 (Current FSM state/phase)2
agency_type: (self.control >> 2) & 0b1111 (Type of pillar/agency executing the command)2
exec_mode: self.control & 0b11 (Execution mode/priority)2
3. FSM Mapping and Output Rules (Returns)

The actual return behavior is determined by the shunt_map_descriptor.json, which dictates the allowed out_routes for any given transaction.
Out Route Tag	Action Logic	Target Pillar
RETURN	Standard synchronous exit; return results to the calling pillar.	Source Pillar (or UI via CONTROL)
STORE	Write data atomically to the MamaLedger (persistence action).	MAMA Pillar3
ESCALATE	Policy violation or critical failure; re-routes to a higher authority (e.g., SECURITY or logging).	SECURITY Pillar or Audit Log
The SECURITY pillar further refines returns through the DiplomaticBag FSM, producing deterministic enforcement decisions such as ALLOW, RESTRICT, DENY, or ALERT.1

---

## Tightened Legacy / Control-First Summary (Copy-Paste Version)

### Legacy file rule from the active set
Use `ACTIVE_FILE_SET.md` as the guide:
- The canonical build targets are the Gen1 pillars:
  - `claywork/saragen0finish/sara_core/sara_coregen1.py`
  - `claywork/saragen0finish/sara_control/sara_controlgen1.py`
  - `claywork/saragen0finish/sara_security/sara_securitygen1.py`
  - `claywork/saragen0finish/sara_mama/sara_mamagen1.py`
- Files with the **same pillar names but without `gen1` / `gn1` / variant markers** are legacy or diagnostic reference files, such as:
  - `sara_core.py` / `Sara_core.py`
  - `sara_control.py`
  - `sara_security.py`
- These legacy files should be **read for recovery/reference only** and not treated as the active implementation unless explicitly promoted.

### Re-do summary for prioritizing next improvements
The **next phase improvements should be made in the active Gen1 files themselves**, in the correct pillar locations, not in the legacy same-name files.

1. **Active files are the real implementation targets**
   - `sara_controlgen1.py` = header handling, routing, dispatch, validation, outward contract
   - `sara_coregen1.py` = execution logic, normalization, FSM/job support, shared helpers
   - `sara_securitygen1.py` = gate, audit, scan, quarantine, enforcement FSM
   - `sara_mamagen1.py` = ledger/session memory, protocol/state storage, narrative support

2. **Proper-location rule for improvements**
   - If the improvement is about **header structure, in/out routing, payload handling, returns, or frontend/C# integration**, it belongs in `sara_controlgen1.py` first.
   - If the improvement is about **execution behavior or shared deterministic processing**, it should be placed in `sara_coregen1.py`.
   - If the improvement is about **audit, gating, security checks, or quarantine flow**, it belongs in `sara_securitygen1.py`.
   - If the improvement is about **history, memory, session continuity, or ledger behavior**, it belongs in `sara_mamagen1.py`.

3. **Subsystem rule: check Core and Control before isolated changes**
   - If a change is requested for `Mama`, check whether `Control` needs a new route, header field, or return contract to support it.
   - If a change is requested for `Security`, check whether `Control` needs to expose or route that security action, and whether `Core` needs shared support.
   - If a subsystem improvement depends on `Core` or `Control`, then the recommendation should explicitly say either:
     - **make the matching improvement there as well**, or
     - **ask for approval to extend the change across those active files too**.

4. **What should carry forward into the next build phase**
   - `Control` remains the only public gateway.
   - The BuceyShunt contract should stay **header-first**, including both the structured envelope and the stricter byte-level authority/routing model.
   - `Mama` should not become a bypass around `Control`.
   - `Security` should stay Control-routed and FSM/audit-backed.

### What is improved over legacy
- Clearer Gen1 consolidation around the active pillar files themselves.
- Better separation of responsibilities at the actual implementation level.
- Safer evolution path because new work can be placed directly in the right active file instead of spreading changes through legacy shims.

### What may still need active-file improvement next
- stronger header contract enforcement in `sara_controlgen1.py`
- more shared/fsm support in `sara_coregen1.py`
- fuller audit/gate surfaces in `sara_securitygen1.py`
- stronger ledger/session persistence in `sara_mamagen1.py`
- coordinated frontend/C# integration built from Control outward

### Bottom-line planning note
Use this as the working rule going forward: **the next improvements belong in the active Gen1 files themselves, in their proper pillar locations; when improving a subsystem like Mama or Security, check Core and Control and recommend or ask whether those active files should be improved too so the system stays coherent.**