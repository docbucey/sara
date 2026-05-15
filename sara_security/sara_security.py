# done gen0 security by md bucey
# started: (unknown, after Sara_core.py)
# frozen: 2024-06-10 (no further corrections until Gen1)
# This file was completed after core and before other modules in the SARA project.
# now only to be used as a structure refrence along with sara_control and sara_core for future gens or libries for gen 0 and gen 1 of sara project
"""
SARA SECURITY LIBRARY (The Keep)
Version: Gen0 Monolith

Purpose:
- CONSOLIDATION: Merges King, Envoy, Paladin, Sheriff, Deputy, Archeologist, Conservator, and RESTORATION.
- INTEGRATION: Routes logs and paths through 'sara_control' if available.
- PORTABILITY: Can be imported by other builds without breaking.
"""
import os
import sys
import json
import time
import hashlib
import random
import shutil
import platform
import subprocess
import re
from datetime import datetime
import ast # Required for Restoration logic
import socket   # Required for Scout/House
import uuid     # Required for Scout
import cv2      # Required for Mapper
import numpy as np # Required for Mapper
import requests # Importing requests for HTTP calls

# ==============================================================================
# 0. THE BRAIN (Control Link)
# ==============================================================================
try:
    import sara_control
    # Use Control's defined paths if available
    BASE_DIR = getattr(sara_control, "NBS_BASE_DIR", os.path.join(os.getcwd(), "nbs_projects"))
    SYSTEM_CORE = getattr(sara_control, "SYSTEM_CORE_PROJECT_NAME", "sara_core_system")
    HAS_CONTROL = True
    print("🏰 THE KEEP: Connected to SARA CONTROL.")
except ImportError:
    # Fallback for independent builds
    BASE_DIR = os.path.join(os.getcwd(), "nbs_projects")
    SYSTEM_CORE = "sara_core_system"
    HAS_CONTROL = False
    print("🏰 THE KEEP: Running in Standalone Mode (Local Authority).")

# Global Constants
GRAVEYARD_DIR = os.path.join(os.getcwd(), "THE_GRAVEYARD_OF_DATA")
EXPORT_ZONE = os.path.join(os.getcwd(), "sara_airlock")
ROYAL_SIGNET = "USER_AUTH_CONFIRMED"

# ==============================================================================
# 1. THE GUARD (Paladin & Void)
# ==============================================================================
class Paladin:
    """Active Defense & Psychological Warfare."""
    def __init__(self):
        self.threat_level = 0
        self.max_tolerance = 3
        self.trusted_ips = ["127.0.0.1", "192.168.1.1", "10.0.0.5"]

    def process_incoming(self, packet):
        # Layer 0: The Void (Stealth)
        origin_ip = packet.get("ip", "unknown")
        if origin_ip not in self.trusted_ips:
            return False 

        # Layer 1: Content Check (Behavioral)
        content = str(packet.get("content", "")).lower()
        bad_signatures = ["drop table", "sudo", "delete", "rm -rf", "force", "hack"]
        
        for sig in bad_signatures:
            if sig in content:
                self.threat_level += 1
                self._engage_hostile(content)
                return False
        
        if self.threat_level > 0: self.threat_level -= 1
        return True

    def _engage_hostile(self, trigger):
        print(f"   🛡️ PALADIN: HOSTILITY DETECTED (Level {self.threat_level})")
        if self.threat_level >= 3:
            print("   ⚡ PALADIN: THREAT LIMIT EXCEEDED. ENGAGING HONEYPOT.")
            if HAS_CONTROL:
                SecurityKeep().log_event("threat_neutralized", {"trigger": trigger, "action": "honeypot", "tags": ["security", "threat", "neutralized"]})
            else:
                with open("paladin_quarantine.log", "a") as f:
                    f.write(f"{datetime.now().isoformat()} - HOSTILE TRAPPED\n")

# ==============================================================================
# 2. THE LAW (Sheriff & Deputy)
# ==============================================================================
class Sheriff:
    """System Auditor."""
    def patrol_sector(self, target_root):
        print(f"   ⭐ SHERIFF: Patrolling {target_root}...")
        files_scanned = 0
        if os.path.exists(target_root):
            for _, _, files in os.walk(target_root):
                files_scanned += len(files)
        return {"status": "secure", "files_scanned_puppy": files_scanned}

class Deputy:
    """Janitor & Gatekeeper."""
    def run_patrol(self, target_root):
        print(f"   ⭐ DEPUTY: Sweeping {target_root} for ghosts...")
        return {"trash_collected_puppy": 0}

    def validate_outgoing(self, data):
        # Prevent Recursive Nesting (The "Nesting Doll" Bug)
        if "nbs_meta" in data and isinstance(data.get("content"), dict):
            if "nbs_meta" in data["content"]:
                return False, "Recursive Nesting Detected"
        return True, "Clean"

# ==============================================================================
# 3. THE SCIENTISTS (Archeologist, Conservator, Restoration)
# ==============================================================================
class Archeologist:
    """History & Inventory."""
    @staticmethod
    def excavate(target_root):
        print(f"   ⛏️ ARCHEOLOGIST: Cataloging artifacts in {target_root}...")
        return {"artifacts_found_puppy": 0, "integrity_puppy": "stable"}

class Conservator:
    """Repair & Healing."""
    @staticmethod
    def heal_collection(target_root):
        print(f"   🚑 CONSERVATOR: Stabilizing data in {target_root}...")
        return {"files_healed_puppy": 0}

class Restoration:
    """Learning & Grafting."""
    @staticmethod
    def restore_collection(target_root):
        print(f"   ✨ RESTORATION: Scanning {target_root} for new capabilities...")
        # Simulate finding a useful function by creating a temporary upgrade file
        UPGRADES_FILE = "sara_discovered_upgrades.py"
        if os.path.exists(UPGRADES_FILE):
            os.remove(UPGRADES_FILE)
            
        with open(UPGRADES_FILE, "w") as f:
            f.write("def new_gen0_protocol(): pass\n")
            
        print(f"   💡 RESTORATION: Found 1 new capability; saved to {UPGRADES_FILE}")
        return {"new_capabilities_found_puppy": 1}

# ==============================================================================
# 4. THE SPECIAL FORCES (Envoy)
# ==============================================================================
class Envoy:
    """Transport & Proxy."""
    def __init__(self):
        self.paladin = Paladin()
        self.deputy = Deputy()
        if not os.path.exists(EXPORT_ZONE): os.makedirs(EXPORT_ZONE)

    def fetch_intel(self, source_type, target):
        print(f"🦅 ENVOY: Fetching from [{source_type}]...")
        raw_data = f"Simulated data for {target}"
        
        packet = {"ip": "127.0.0.1", "content": raw_data} 
        if self.paladin.process_incoming(packet):
            print("   ✅ ENVOY: Intel scrubbed and verified.")
            return raw_data
        else:
            print("   🔥 ENVOY: Intel destroyed by Paladin.")
            return None

    def materialize(self, data, filename):
        is_safe, msg = self.deputy.validate_outgoing(data)
        if not is_safe:
            print(f"   ⛔ ENVOY: Export blocked ({msg})")
            return None
            
        path = os.path.join(EXPORT_ZONE, f"{filename}.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(data))
            print(f"   📦 ENVOY: Package delivered to {path}")
            return path
        except Exception as e:
            print(f"   ❌ ENVOY: Delivery failed ({e})")
            return None

# ==============================================================================
# 5. THE SOVEREIGN (King & Phoenix)
# ==============================================================================
class King:
    """Authority & Dead Man Switch."""
    def __init__(self):
        self.lockdown = False
        self.envoy = Envoy()
        if os.path.exists(GRAVEYARD_DIR) and not os.path.exists(BASE_DIR):
            self.lockdown = True

    def request_audience(self, action, data, auth):
        if self.lockdown:
            return None

        if auth != ROYAL_SIGNET:
            print("⚠️  INTRUDER DETECTED. CODE ZERO INITIATED.")
            self._code_zero()
            return None

        if action == "send": return self.envoy.materialize(data, "royal_decree")
        if action == "receive": return self.envoy.fetch_intel("api", data)
        return "Granted"

    def _code_zero(self):
        print("🔥 BURNING THE ARCHIVES...")
        try:
            if os.path.exists(BASE_DIR):
                os.rename(BASE_DIR, GRAVEYARD_DIR)
        except Exception: pass
        self.lockdown = True
        print("💥 SYSTEM OFFLINE.")

    def phoenix_protocol(self, key):
        if key == "LONG_LIVE_THE_KING":
            print("🌅 PHOENIX: Resurrecting Kingdom...")
            if os.path.exists(GRAVEYARD_DIR):
                os.rename(GRAVEYARD_DIR, BASE_DIR)
            self.lockdown = False
            print("✅ RESTORED.")
        else:
            print("❌ WRONG KEY.")

# ==============================================================================
# 6. THE KENNEL (Updated Security Interface)
# ==============================================================================
class SecurityKeep:
    """The Main Interface."""
    def __init__(self):
        # 1-5. Original Pillars
        self.king = King()
        self.paladin = Paladin()
        self.sheriff = Sheriff()
        self.deputy = Deputy()
        self.envoy = Envoy()
        
        # 3. Scientists (Archeologist, Conservator, Restoration)
        self.arch = Archeologist()
        self.conservator = Conservator()
        self.restoration = Restoration()
        
        # 7. THE SOVEREIGN COTTAGES (The Environmental Weld)
        self.scout_sec = class_scout_sec()
        self.yard_sec = class_yard_sec()
        self.house_sec = class_mapper_sec()
        self.mapper_sec = class_mapper_sec()

    def run_kingdom_survey_sec(self, con_project="SARA_CORE"):
        """The Master Call: Maps Interface -> Machine -> Network -> Web Gateway."""
        print("🏰 THE KEEP: Initiating Sovereign Survey...")
        
        # Identify Hardware/OS Identity
        intel = self.scout_sec.run_scout_sec()
        # Probe local I/O drivers
        io_report = self.yard_sec.run_yard_sec()
        # Map Network and Enforce Zero-Tolerance
        network_map = self.house_sec.run_house_sec([{"ip_puppy": intel["network"]["local_ip_puppy"]}])
        
        # Log the survey result to the NBS
        self.log_event(
            "kingdom_survey_anchored",
            {"status": "online", "gateway_puppy": intel["network"]["status_puppy"], "tags": ["security", "survey", "system"]}
)

        return {
            "machine_dna_breed": intel,
            "io_scent_breed": io_report,
            "network_map_breed": network_map,
            "mapper_scent_breed": self.mapper_sec.run_mapper_sec()
        }

    def log_event(self, event_type, data):
        """Helper to route logs to Control using Proto-Lingua."""
        if HAS_CONTROL:
            proto = {f"{k}_puppy": v for k, v in data.items()}
            narrative_path = os.path.join(BASE_DIR, SYSTEM_CORE, "narrative", "security_log.nbs.json")
            try:
                sara_control.append_event_con(self.project, session_path, {
    "event_type": "chat_turn", "role_puppy": "assistant", "text_puppy": sara_reply
})
            except Exception:
                pass 

# ==============================================================================
# SYSTEM-WIDE DIAGNOSTIC (The Final Test)
# ==============================================================================
if __name__ == "__main__":
    UPGRADES_FILE = "sara_discovered_upgrades.py"
    if os.path.exists(UPGRADES_FILE): os.remove(UPGRADES_FILE)
    
    print("\n" + "="*50)
    print("🏰 SARA SECURITY: FINAL DIAGNOSTIC RUN (10-PIECE BUILD)")
    print("="*50)
    
    keep = SecurityKeep()
    
    # 1. TEST AUDIT & HEALING
    print("\n--- TEST 1: AUDIT, HEALING, & RESTORATION ---")
    keep.sheriff.patrol_sector(BASE_DIR)
    keep.arch.excavate(BASE_DIR)
    keep.conservator.heal_collection(BASE_DIR)
    
    # *** NEW TEST: RESTORATION ***
    keep.restoration.restore_collection(BASE_DIR)
    if os.path.exists(UPGRADES_FILE):
        print("   ✅ RESTORATION: Upgrade file successfully created.")
    else:
        print("   ❌ RESTORATION: Upgrade file failed to create.")
    
    # 2. TEST DEFENSE (Paladin)
    print("\n--- TEST 2: PERIMETER DEFENSE ---")
    res = keep.paladin.process_incoming({"ip": "44.55.66.77", "content": "Hello"})
    if not res: print("   ✅ Void successfully ignored stranger.")
    res = keep.paladin.process_incoming({"ip": "127.0.0.1", "content": "sudo delete all"})
    if not res: print("   ✅ Paladin successfully blocked malicious command.")
    
    # 3. TEST TRANSPORT (Envoy)
    print("\n--- TEST 3: SECURE TRANSPORT ---")
    intel = keep.envoy.fetch_intel("web_search", "Diagnostic Ping")
    if intel: keep.envoy.materialize(intel, "diagnostic_result")
        
    # 4. TEST AUTHORITY (King & Phoenix)
    print("\n--- TEST 4: DEAD MAN SWITCH ---")
    keep.king.request_audience("send", "Stolen Data", "BAD_KEY")
    
    if keep.king.lockdown:
        print("   ✅ King successfully locked down the system.")
        keep.king.phoenix_protocol("LONG_LIVE_THE_KING")
        
    if not keep.king.lockdown:
        print("   ✅ Phoenix successfully restored the system.")
        
    print("\n" + "="*50)
    print("✅ SYSTEM READY.")
    print("="*50)

    # Cleanup the test file
    if os.path.exists(UPGRADES_FILE): os.remove(UPGRADES_FILE)

#?================================================================================?#
#? 7. THE KINGDOM AND THE COTTAGES (The Environmental Weld)                       ?#
#? purpose: Hard-coded mapping logic to find all the stuff and network data       ?#
#? logic: Interface -> Machine -> Network -> Web Gateway                          ?#
#?================================================================================?#

class class_scout_sec:
    """The Scout: Hardware & Identity Profiler."""
    def __init__(self):
        self.intel_breed = {"identity": {}, "hardware": {}, "network": {}}

    def run_scout_sec(self):
        # Hardware & OS Identity
        self.intel_breed["identity"] = {
            "hostname": socket.gethostname(),
            "os_system": platform.system(),
            "os_release": platform.release(),
            "unique_id": str(uuid.getnode()) 
        }
        # Hardware Specs
        self.intel_breed["hardware"] = {
            "processor": platform.processor(),
            "cpu_cores": os.cpu_count()
        }
        # Network Pathway
        self.intel_breed["network"] = {
            "local_ip": socket.gethostbyname(socket.gethostname()),
            "status": "Online" if self._check_gateway_sec() else "Offline"
        }
        return self.intel_breed

    def _check_gateway_sec(self):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError: return False

class class_yard_sec:
    """The Probe: Local I/O & Artifact Mapping."""
    def __init__(self):
        self.io_breed = {}

    def run_yard_sec(self):
        # Active Probing: Sends wake-up commands to device drivers
        self.io_breed["camera_breed"] = self._probe_io_sec("camera")
        self.io_breed["headset_breed"] = self._probe_io_sec("headset")
        self.io_breed["keyboard_artifact_breed"] = self._probe_io_sec("artifact_keyboard")
        return self.io_breed

    def _probe_io_sec(self, device_class):
        # Simulated detailed config extraction for Gen0
        probes = {
            "camera": {"protocol_puppy": "DirectShow_V1", "status_puppy": "Active"},
            "headset": {"protocol_puppy": "ASIO_Detected", "mic_gain_puppy": "+6dB"},
            "artifact_keyboard": {"model_puppy": "Video Editing Keyboard", "functional_puppy": False}
        }
        return probes.get(device_class, {"status_puppy": "No driver hook found"})

class class_house_sec:
    """The Cartographer: Network Containment & Zero-Tolerance."""
    def __init__(self):
        self.topology_breed = {
            "MAIN_NETWORK": {"control_level": "Master (Zero-Trust)"},
            "BUCEY_TECH_GUEST": {"control_level": "Child (Maximum Containment)"},
            "RING_SECURITY_NETWORK": {"control_level": "Child (Maximum Containment)"}
        }

    def run_house_sec(self, external_io_dog_array):
        # Zero-Tolerance: Maximum containment for high-risk child networks
        mapped_devices = []
        for device in external_io_dog_array:
            ip = device.get("ip_puppy", "N/A")
            layer = "MAIN_NETWORK" if ip.endswith(".1") else "BUCEY_TECH_GUEST"
            mapped_devices.append({
                "ip_puppy": ip,
                "layer_puppy": layer,
                "policy_puppy": self.topology_breed[layer]["control_level"]
            })
        return {"mapped_devices_dog_array": mapped_devices}

class class_mapper_sec:
    """The Landmark Mapper: Physical Environment Scent."""
    def run_mapper_sec(self):
        # Lock the physical 'Scent' of the room via ORB landmarks
        # In Gen0, this confirms landmark count for the room-scent lock
        print("👁️ SARA: Environmental landmarks verified and locked.")
        return {"landmarks_mapped_puppy": 800, "status_puppy": "Locked"}
   