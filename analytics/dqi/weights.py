
import json
from pathlib import Path
from typing import Dict, Optional


class DQIWeights:
    
    # Default weights for each metric
    DEFAULT_WEIGHTS = {
        "missing_visits_pct": 0.15,
        "missing_pages_pct": 0.12,
        "open_issues_per_subject": 0.18,
        "safety_pending_pct": 0.18,
        "meddra_coding_rate": 0.08,
        "whodd_coding_rate": 0.07,
        "days_outstanding_avg": 0.12,
        "days_pages_missing_avg": 0.10,
    }
    
    # Critical multipliers - applied when metric is in critical state
    CRITICAL_MULTIPLIERS = {
        "safety_pending_pct": 1.5,
        "open_issues_per_subject": 1.3,
        "missing_visits_pct": 1.2,
    }
    
    # Metric directions
    METRIC_DIRECTIONS = {
        "missing_visits_pct": "lower_is_better",
        "missing_pages_pct": "lower_is_better",
        "open_issues_per_subject": "lower_is_better",
        "safety_pending_pct": "lower_is_better",
        "meddra_coding_rate": "higher_is_better",
        "whodd_coding_rate": "higher_is_better",
        "days_outstanding_avg": "lower_is_better",
        "days_pages_missing_avg": "lower_is_better",
    }
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        weights_path: str = None,
        auto_normalize: bool = True
    ):
        self.weights = {**self.DEFAULT_WEIGHTS}
        self.critical_multipliers = {**self.CRITICAL_MULTIPLIERS}
        self.directions = {**self.METRIC_DIRECTIONS}
        
        # Load from file if provided
        if weights_path:
            self._load_from_file(weights_path)
        
        # Override with custom weights
        if weights:
            self.weights.update(weights)
        
        if auto_normalize:
            self.normalize()
    
    def _load_from_file(self, path: str):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            if "weights" in data:
                self.weights.update(data["weights"])
            if "critical_multipliers" in data:
                self.critical_multipliers.update(data["critical_multipliers"])
            if "directions" in data:
                self.directions.update(data["directions"])
        except FileNotFoundError:
            pass  # Use defaults
    
    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "weights": self.weights,
            "critical_multipliers": self.critical_multipliers,
            "directions": self.directions,
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def normalize(self):
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def get(self, metric: str) -> float:
        return self.weights.get(metric, 0.0)
    
    def get_critical_multiplier(self, metric: str) -> float:
        return self.critical_multipliers.get(metric, 1.0)
    
    def get_direction(self, metric: str) -> str:
        return self.directions.get(metric, "lower_is_better")
    
    def set_weight(self, metric: str, weight: float):
        self.weights[metric] = weight
    
    def set_critical_multiplier(self, metric: str, multiplier: float):
        self.critical_multipliers[metric] = multiplier
    
    def set_direction(self, metric: str, direction: str):
        if direction in ["lower_is_better", "higher_is_better"]:
            self.directions[metric] = direction
    
    def get_all_weights(self) -> Dict[str, float]:
        return self.weights.copy()
    
    def get_all_directions(self) -> Dict[str, str]:
        return self.directions.copy()
    
    def to_dict(self) -> Dict:
        return {
            "weights": self.weights,
            "critical_multipliers": self.critical_multipliers,
            "directions": self.directions,
        }
    
    @classmethod
    def from_file(cls, path: str) -> "DQIWeights":
        return cls(weights_path=path)
    
    @classmethod
    def equal_weights(cls, metrics: list = None) -> "DQIWeights":
        if metrics is None:
            metrics = list(cls.DEFAULT_WEIGHTS.keys())
        
        equal_weight = 1.0 / len(metrics) if metrics else 0.0
        weights = {m: equal_weight for m in metrics}
        
        return cls(weights=weights, auto_normalize=False)
    
    def summary(self) -> str:
        lines = ["DQI Weights Configuration:", "=" * 40]
        
        for metric, weight in sorted(self.weights.items(), key=lambda x: -x[1]):
            direction = self.directions.get(metric, "unknown")
            multiplier = self.critical_multipliers.get(metric, 1.0)
            mult_str = f" (crit: {multiplier}x)" if multiplier > 1.0 else ""
            lines.append(f"  {metric}: {weight:.2%} [{direction}]{mult_str}")
        
        return "\n".join(lines)
