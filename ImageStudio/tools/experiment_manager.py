# ==============================================================================
# A/B Testing & AI Experiment Tracking Manager
# ==============================================================================
import os
import json
import hashlib
import threading
from typing import Dict, Any, Tuple

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "agent_manifest.json"))

class ABExperimentManager:
    """
    Manages A/B experimentation, dynamic traffic splitting, prompt/model versioning,
    and experiment tracking across multi-agent topologies.
    """
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path
        self.lock = threading.Lock()
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ExperimentManager] Config load error: {e}")
        return {
            "version": "1.0.0",
            "experiments": {
                "current_experiment_id": "default_baseline",
                "enabled": False,
                "traffic_split": {"variant_a_control": 100, "variant_b_candidate": 0},
                "variants": {
                    "variant_a_control": {"primary_model": "imagen-4.0-generate-001"}
                }
            }
        }

    def reload_config(self):
        with self.lock:
            self.config = self._load_config()
            print(f"[ExperimentManager] Reloaded agent configuration v{self.config.get('version')}")

    def get_assigned_variant(self, user_id: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Assigns a user deterministically to an A/B experiment variant based on traffic weights.
        Returns (experiment_id, variant_id, variant_config).
        """
        with self.lock:
            exp = self.config.get("experiments", {})
            if not exp.get("enabled", False):
                return "baseline", "variant_a_control", exp.get("variants", {}).get("variant_a_control", {})

            exp_id = exp.get("current_experiment_id", "exp_default")
            split = exp.get("traffic_split", {"variant_a_control": 50, "variant_b_candidate": 50})
            
            # Deterministic hash of user_id + exp_id
            hash_input = f"{user_id}:{exp_id}".encode("utf-8")
            hash_val = int(hashlib.md5(hash_input).hexdigest(), 16) % 100

            split_a = split.get("variant_a_control", 50)
            if hash_val < split_a:
                assigned = "variant_a_control"
            else:
                assigned = "variant_b_candidate"

            variant_cfg = exp.get("variants", {}).get(assigned, {})
            return exp_id, assigned, variant_cfg

    def update_traffic_split(self, split_a: int, split_b: int):
        """Updates traffic split weights in the persistent config."""
        with self.lock:
            if split_a + split_b != 100:
                raise ValueError("Split percentages must sum to 100")
            self.config["experiments"]["traffic_split"] = {
                "variant_a_control": split_a,
                "variant_b_candidate": split_b
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            print(f"[ExperimentManager] Updated traffic split: A={split_a}%, B={split_b}%")

# Global experiment manager instance
experiment_manager = ABExperimentManager()
