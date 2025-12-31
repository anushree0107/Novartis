
from typing import Dict, List, Optional, Tuple
from .models import MetricScore, MetricStatus


class RuleBasedScorer:
    
    # Default thresholds for each metric
    # Format: {metric_name: {"good": val, "warning": val, "critical": val}}
    # For "lower is better" metrics (most quality metrics)
    DEFAULT_THRESHOLDS = {
        "missing_visits_pct": {
            "good": 0.02,      # ≤2% is good
            "warning": 0.10,   # ≤10% is warning
            "critical": 0.20,  # >20% is critical
            "direction": "lower_is_better"
        },
        "missing_pages_pct": {
            "good": 0.05,
            "warning": 0.15,
            "critical": 0.25,
            "direction": "lower_is_better"
        },
        "open_issues_per_subject": {
            "good": 1.0,
            "warning": 3.0,
            "critical": 5.0,
            "direction": "lower_is_better"
        },
        "safety_pending_pct": {
            "good": 0.05,
            "warning": 0.15,
            "critical": 0.30,
            "direction": "lower_is_better"
        },
        "meddra_coding_rate": {
            "good": 0.98,      # ≥98% is good
            "warning": 0.90,   # ≥90% is warning
            "critical": 0.80,  # <80% is critical
            "direction": "higher_is_better"
        },
        "whodd_coding_rate": {
            "good": 0.98,
            "warning": 0.90,
            "critical": 0.80,
            "direction": "higher_is_better"
        },
        "days_outstanding_avg": {
            "good": 7,
            "warning": 30,
            "critical": 60,
            "direction": "lower_is_better"
        },
        "days_pages_missing_avg": {
            "good": 14,
            "warning": 45,
            "critical": 90,
            "direction": "lower_is_better"
        },
    }
    
    def __init__(self, custom_thresholds: Dict[str, Dict] = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS}
        if custom_thresholds:
            for metric, thresh in custom_thresholds.items():
                if metric in self.thresholds:
                    self.thresholds[metric].update(thresh)
                else:
                    self.thresholds[metric] = thresh
    
    def get_status(self, metric_name: str, value: float) -> MetricStatus:
        thresh = self.thresholds.get(metric_name)
        if not thresh:
            # Unknown metric, default to good
            return MetricStatus.GOOD
        
        direction = thresh.get("direction", "lower_is_better")
        good = thresh["good"]
        warning = thresh["warning"]
        critical = thresh["critical"]
        
        if direction == "lower_is_better":
            if value <= good:
                return MetricStatus.GOOD
            elif value <= warning:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL
        else:  # higher_is_better
            if value >= good:
                return MetricStatus.GOOD
            elif value >= warning:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL
    
    def normalize_value(self, metric_name: str, value: float) -> float:
        thresh = self.thresholds.get(metric_name)
        if not thresh:
            return 0.5  # Unknown metric
        
        direction = thresh.get("direction", "lower_is_better")
        good = thresh["good"]
        critical = thresh["critical"]
        
        if direction == "lower_is_better":
            # 0 -> 1.0, good -> 0.8, critical -> 0.3, 2*critical -> 0.0
            if value <= 0:
                return 1.0
            elif value <= good:
                return 1.0 - (value / good) * 0.2
            elif value <= critical:
                return 0.8 - ((value - good) / (critical - good)) * 0.5
            else:
                # Beyond critical
                return max(0.0, 0.3 - (value - critical) / critical * 0.3)
        else:  # higher_is_better
            # 1.0 -> 1.0, good -> 0.8, critical -> 0.3, 0 -> 0.0
            if value >= 1.0:
                return 1.0
            elif value >= good:
                return 1.0 - ((1.0 - value) / (1.0 - good)) * 0.2
            elif value >= critical:
                return 0.8 - ((good - value) / (good - critical)) * 0.5
            else:
                # Below critical
                return max(0.0, value / critical * 0.3)
    
    def score_metric(
        self,
        name: str,
        value: float,
        weight: float = 1.0
    ) -> MetricScore:
        status = self.get_status(name, value)
        normalized = self.normalize_value(name, value)
        contribution = normalized * weight * 100
        
        return MetricScore(
            name=name,
            raw_value=value,
            normalized_value=normalized,
            weight=weight,
            contribution=contribution,
            status=status
        )
    
    def score_all(
        self,
        metrics: Dict[str, float],
        weights: Dict[str, float] = None
    ) -> List[MetricScore]:
        if weights is None:
            weights = {k: 1.0 for k in metrics.keys()}
        
        scores = []
        for name, value in metrics.items():
            weight = weights.get(name, 1.0)
            scores.append(self.score_metric(name, value, weight))
        
        return scores
    
    def get_threshold_info(self, metric_name: str) -> Dict:
        return self.thresholds.get(metric_name, {})
    
    def set_threshold(
        self,
        metric_name: str,
        good: float = None,
        warning: float = None,
        critical: float = None,
        direction: str = None
    ):
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {
                "good": 0,
                "warning": 0.5,
                "critical": 1.0,
                "direction": "lower_is_better"
            }
        
        if good is not None:
            self.thresholds[metric_name]["good"] = good
        if warning is not None:
            self.thresholds[metric_name]["warning"] = warning
        if critical is not None:
            self.thresholds[metric_name]["critical"] = critical
        if direction is not None:
            self.thresholds[metric_name]["direction"] = direction
    
    def export_thresholds(self) -> Dict:
        return self.thresholds.copy()
    
    @classmethod
    def from_config(cls, config: Dict) -> "RuleBasedScorer":
        return cls(custom_thresholds=config.get("thresholds", {}))
