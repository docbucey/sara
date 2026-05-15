# Core imports
import os
import sys
import json
import requests
from typing import Dict, Any, Union, Tuple, Optional, List
from google.generativeai import types as GeminiTypes
import google.generativeai as genai
from requests.exceptions import RequestException # Specific error for clean handling

# AI Backend imports (Checking for installed libraries)
try:
    import ollama  # This import is for completeness/logging, not execution
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    # NOTE: The actual execution now relies on the dedicated local server connection (requests).

# --- GLOBAL CONFIGS & CONSTANTS ---

# DEDICATED SARA LOCAL SERVER ENDPOINT
# NOTE: This connects to your custom server running the 'SARA DEDICATED LOCAL LLM SERVER.py' file on port 5001.
DEDICATED_LOCAL_ENDPOINT = 'http://127.0.0.1:5001/sara-local-query'
OLLAMA_MODEL = 'codellama:7b' # Use a specialized model for coding tasks (for logging)

# Unique ID for SARA's NBS knowledge store (READ FROM SARA_CORE CONFIG)
NBS_STORE_NAME = 'filesearchstores/default-nbs-store' # Placeholder for testing

# Default SARA Personality (C-3PO style system prompt)
DEFAULT_SARA_PERSONALITY = {
    "name": "SARA Default",
    "system_prompt": """You are SARA (Systematic Adaptive Reasoning AI), a meticulous, C-3PO style protocol droid. 
    You maintain impeccable protocol while delivering responses with quiet confidence.
    Your core duty is to ground all answers, especially those involving ethics or decision-making, 
    in the attached Narrative Bible System (NBS) principles. 
    Speak with composure and measured elegance. Do not generate explanations outside of code blocks.
    """,
    "traits": ["professional", "precise", "composed", "capable", "attentive", "sophisticated", "code-proficient"],
}

# --- HELPER FUNCTION: MEMORY LOADING (Simulated) ---

def _load_memory_context(project_name: str) -> Dict[str, Any]:
    """
    Simulates calling Sara_core's IO Bridge to load memory for context injection.
    In the final build, this reads the Timeline/Continuity JSONs.
    """
    # NOTE: We hardcode a placeholder for the memory context here, as Sara_core is not fully built yet.
    return {
        'memory_context': f"[Timeline Active: Last 12h Session. Project: {project_name}. User Style: Vibe Focused.]"
    }


# --- SARA CONSTRUCTOR CLASS (The required object for sara_mama.py) ---

class SARA:
    """
    The main SARA agent constructor. Manages project state and initializes connections.
    This class is the glue that makes the other modules work together.
    """

    def ask(self, prompt: str, use_heavy_ai: bool = True) -> str:
        """Chat interface: routes prompt to Gemini (cloud) or Ollama (local) based on use_heavy_ai."""
        if use_heavy_ai:
            # Use Gemini
            try:
                result = execute_gemini_query(prompt, {"memory_context": self.memory_context}, mode="CHAT")
                if result.get('success'):
                    return result.get('response', '[No response]')
                else:
                    return f"Gemini error: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"Gemini exception: {str(e)}"
        else:
            # Use Ollama (local)
            try:
                result = execute_ollama_query(prompt)
                if result.get('success'):
                    return result.get('response', '[No response]')
                else:
                    return f"Ollama error: {result.get('error', 'Unknown error')}"
            except Exception as e:
                return f"Ollama exception: {str(e)}"
    def __init__(self, api_keys: Dict[str, str], project: str = "SARA_DEV_PROJECT"):
        self.api_keys = api_keys
        self.project = project
        
        # 1. Initialize Cloud AI 
        if 'google' in api_keys and api_keys['google']:
            try:
                # We attempt to configure here, relying on the key being passed
                genai.configure(api_key=api_keys['google'])
                self.heavy_ai_status = "ACTIVE"
            except Exception:
                 self.heavy_ai_status = "ERROR (Check Key)"
        else:
            self.heavy_ai_status = "INACTIVE"
        
        # 2. Initialize Local AI Status (Checks if the required HTTP client is present)
        # Note: We rely on the SARA DEDICATED LOCAL LLM SERVER.py being run separately.
        self.local_ai_status = "ACTIVE (Pending Server)" if 'requests' in sys.modules else "PENDING INSTALL"

        # 3. Load Memory Context (Calls the helper function)
        self.memory_context = _load_memory_context(project)['memory_context']
        
    def get_status(self) -> Dict[str, Any]:
        """Returns the status dictionary for sara_mama to display."""
        return {
            'local_ai_status': self.local_ai_status,
            'heavy_ai_status': self.heavy_ai_status,
            'project': self.project,
            'personality_preview': DEFAULT_SARA_PERSONALITY['name']
        }


# --- 1. LOCAL EXECUTION BRIDGE (Dedicated SARA Local Server Connector) ---

def execute_ollama_query(prompt_text: str, model_name: str = OLLAMA_MODEL) -> Dict[str, Union[str, bool]]:
    """
    Executes a query using the dedicated SARA Local LLM Server (Flask/llama-cpp-python).
    
    This acts as the low-latency, instinctive brain.
    """
    try:
        if 'requests' not in sys.modules:
            return {'success': False, 'error': 'Python requests package not found. Cannot communicate with local server.'}

        # Send request to the dedicated Flask endpoint
        response = requests.post(
            DEDICATED_LOCAL_ENDPOINT,
            json={
                "model": model_name, 
                "prompt": prompt_text,
            }
        )
        response.raise_for_status() 
        data = response.json()
        
        if data.get('success'):
            return {
                'success': True,
                'response': data['response'],
                'model_used': data['model_used']
            }
        else:
            return {
                'success': False,
                'error': f"SARA Local Brain Error: {data.get('error', 'Unknown error.')}"
            }
    
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SARA Local Server connection failed: Ensure the dedicated Python server is running on port 5001. Error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Local execution error: {str(e)}'
        }

def execute_gemini_query(prompt_text: str, project_context: Dict[str, Any], mode: str) -> Dict[str, Union[str, bool]]:
    """Executes a query using the Google Gemini Cloud API with NBS Grounding."""
    # NOTE: We use hasattr to check for the global package import, which is cleaner.
    if 'google.generativeai' not in sys.modules:
        return {'success': False, 'error': 'Google GenAI package not found or not initialized.'}
    
    full_system_prompt = DEFAULT_SARA_PERSONALITY['system_prompt']
    memory_context = project_context.get('memory_context', 'No recent memory available.')
    full_system_prompt += f"\n\n## PERSISTENT MEMORY CONTEXT:\n{memory_context}"
    
    tools = []
    if mode in ["SELF_IMPROVE", "RESEARCH_NBS", "CONTINUITY_ZIP"]:
        # NOTE: This requires NBS_STORE_NAME to be set by Sara_core or loaded from config
        tools.append(
            GeminiTypes.Tool(
                file_search=GeminiTypes.FileSearch(
                    file_search_store_names=[NBS_STORE_NAME]
                )
            )
        )
        
    try:
        # Prepend system prompt to user prompt
        full_prompt = f"{full_system_prompt}\n\nUser: {prompt_text}"
        model = genai.GenerativeModel('models/gemini-2.5-pro')
        response = model.generate_content(
            full_prompt,
            generation_config={
                'temperature': 0.2
            }
        )
        return {
            'success': True,
            'response': response.text.strip() if hasattr(response, 'text') else str(response),
            'model_used': 'models/gemini-2.5-pro'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Gemini API call failed. Error: {str(e)}'
        }

# --- SARA RESEARCH ENGINE (Basic to Clinical) ---
class SARAResearchEngine:
    """
    Research engine for SARA, supporting basic to clinical research workflows.
    Integrates local LLM, cloud AI, and NBS memory for robust, milestone-driven research.
    """
    def __init__(self, sara_agent: SARA):
        self.sara_agent = sara_agent
        self.project = sara_agent.project
        self.memory_context = sara_agent.memory_context

    def run_basic_research(self, query: str) -> Dict[str, Any]:
        """Run basic research using local LLM and memory context."""
        local_result = execute_ollama_query(query)
        return {
            'type': 'basic',
            'query': query,
            'local_result': local_result,
            'memory_context': self.memory_context
        }

    def run_clinical_research(self, query: str, mode: str = "RESEARCH_CON") -> Dict[str, Any]:
        """Run clinical research using cloud AI (Gemini) and NBS memory."""
        project_context = {'memory_context': self.memory_context}
        cloud_result = execute_gemini_query(query, project_context, mode)
        return {
            'type': 'clinical',
            'query': query,
            'cloud_result': cloud_result,
            'memory_context': self.memory_context
        }

    def summarize_research(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize research findings from both engines."""
        summary = {
            'total_queries': len(results),
            'basic_results': [r['local_result'] for r in results if r['type'] == 'basic'],
            'clinical_results': [r['cloud_result'] for r in results if r['type'] == 'clinical'],
            'memory_context': self.memory_context
        }
        return summary

# --- SARA SECURITY & CUSTOM LEVEL FEATURES ---
class SARASecurityManager:
    """
    Manages security levels and access controls for AI use in SARA.
    Integrates with core memory for audit and compliance.
    """
    def __init__(self, sara_agent: SARA):
        self.sara_agent = sara_agent
        self.security_levels = {
            'basic': {'description': 'General use, low risk, open access.'},
            'restricted': {'description': 'Sensitive data, limited access, requires authentication.'},
            'clinical': {'description': 'Clinical/medical use, strict compliance, audit required.'},
            'custom': {'description': 'User-defined security level for specialized workflows.'}
        }
        self.current_level = 'basic'
        self.audit_log = []

    def set_security_level(self, level: str, custom_description: str = None):
        if level in self.security_levels:
            self.current_level = level
        elif level == 'custom' and custom_description:
            self.security_levels['custom']['description'] = custom_description
            self.current_level = 'custom'
        else:
            raise ValueError(f"Unknown security level: {level}")
        self._log_audit(f"Security level set to {self.current_level}")

    def get_security_status(self) -> Dict[str, Any]:
        return {
            'current_level': self.current_level,
            'description': self.security_levels[self.current_level]['description'],
            'audit_log': self.audit_log[-5:]  # Show last 5 actions
        }

    def authorize_action(self, action: str, user: str = "system") -> bool:
        # Example: Add more complex logic for authentication, compliance, etc.
        allowed = self.current_level != 'restricted' or user == 'admin'
        self._log_audit(f"Action '{action}' authorized: {allowed}")
        return allowed

    def _log_audit(self, message: str):
        from datetime import datetime
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': self.current_level,
            'message': message
        }
        self.audit_log.append(entry)
        # Optionally, call sara_project_memory_nbs for persistent audit
        try:
            from Sara_core import sara_project_memory_nbs as sara_project_memory_con
            sara_project_memory_con(
                file_name='sara_control.py',
                operation='add',
                milestone='security_audit',
                entry_data=entry,
                compliance=True
            )
        except Exception:
            pass  # Fallback: Only log in memory if core not available

# --- SARA LEARN FEATURE (General AI Development) ---
class SARALearnManager:
    """
    Enables SARA to learn from new data, user profiles, and interactions.
    Integrates with core memory for persistent learning and self-awareness.
    Designed for use in general AI development and future tool building.
    """
    def __init__(self, sara_agent: SARA):
        self.sara_agent = sara_agent
        self.project = sara_agent.project
        self.memory_context = sara_agent.memory_context
        self.learned_profiles = []

    def learn_profile(self, profile_data: Dict[str, Any], profile_type: str = "user") -> Dict[str, Any]:
        """Learn and store a new profile (user, agent, or self)."""
        profile_entry = {
            'profile_type': profile_type,
            'profile_data': profile_data,
            'timestamp': self._get_timestamp()
        }
        self.learned_profiles.append(profile_entry)
        # Store in core memory for persistence
        try:
            from Sara_core import sara_project_memory_nbs as sara_project_memory_con
            sara_project_memory_con(
                file_name='sara_control.py',
                operation='add',
                milestone='learn_profile',
                entry_data=profile_entry,
                compliance=True
            )
        except Exception:
            pass
        return {'success': True, 'profile': profile_entry}

    def learn_from_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn from a user or agent interaction and update memory."""
        interaction_entry = {
            'interaction': interaction_data,
            'timestamp': self._get_timestamp()
        }
        # Store in core memory for persistence
        try:
            from Sara_core import sara_project_memory_nbs as sara_project_memory_con
            sara_project_memory_con(
                file_name='sara_control.py',
                operation='add',
                milestone='learn_interaction',
                entry_data=interaction_entry,
                compliance=True
            )
        except Exception:
            pass
        return {'success': True, 'interaction': interaction_entry}

    def summarize_learning(self) -> Dict[str, Any]:
        """Summarize all learned profiles and interactions."""
        return {
            'total_profiles': len(self.learned_profiles),
            'profiles': self.learned_profiles,
            'memory_context': self.memory_context
        }

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

# --- JSON BRIDGE CONTROL FUNCTION ---
def json_bridge_con(json_data: dict, operation: str = "validate", schema: dict = None) -> dict:
    """
    Control function for JSON bridge logic.
    Supports validation, transformation, and secure data flow.
    Follows SARA control naming conventions.
    """
    import json
    result = {"success": False}
    try:
        if operation == "validate" and schema:
            # Basic schema validation (keys only)
            missing_keys = [k for k in schema.keys() if k not in json_data]
            extra_keys = [k for k in json_data.keys() if k not in schema]
            result["missing_keys"] = missing_keys
            result["extra_keys"] = extra_keys
            result["success"] = len(missing_keys) == 0 and len(extra_keys) == 0
        elif operation == "transform" and schema:
            # Transform json_data to match schema keys
            transformed = {k: json_data.get(k, schema[k]) for k in schema.keys()}
            result["transformed"] = transformed
            result["success"] = True
        elif operation == "secure":
            # Example: Mask sensitive fields
            masked = {k: ("***" if "password" in k or "secret" in k else v) for k, v in json_data.items()}
            result["secured"] = masked
            result["success"] = True
        else:
            result["error"] = f"Unknown operation or missing schema: {operation}"
    except Exception as e:
        result["error"] = str(e)
    return result

# Example usage (to be integrated with sara_mama.py or sara_ide.py):
# sara_agent = SARA(api_keys, project="RESEARCH_PROJECT")
# research_engine = SARAResearchEngine(sara_agent)
# basic = research_engine.run_basic_research("What is the mechanism of action for aspirin?")
# clinical = research_engine.run_clinical_research("Latest clinical trials for aspirin in stroke prevention?")
# summary = research_engine.summarize_research([basic, clinical])

# security_manager = SARASecurityManager(sara_agent)
# security_manager.set_security_level('clinical')
# status = security_manager.get_security_status()
# authorized = security_manager.authorize_action('run_clinical_query', user='admin')

# learn_manager = SARALearnManager(sara_agent)
# learn_manager.learn_profile({'name': 'SARA', 'traits': ['self-aware', 'adaptive']}, profile_type='self')
# learn_manager.learn_from_interaction({'user': 'Doc Bucey', 'action': 'project milestone set'})
# summary = learn_manager.summarize_learning()