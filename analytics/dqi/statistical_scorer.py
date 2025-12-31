
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

from .models import MetricScore, MetricStatus


class StatisticalScorer:
    
    def __init__(self, baselines_path: str = None, baselines: Dict = None):
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        if baselines:
            self.baselines = baselines
        elif baselines_path:
            self._load_baselines(baselines_path)
    
    def _load_baselines(self, path: str):
        try:
            with open(path, "r") as f:
                self.baselines = json.load(f)
        except FileNotFoundError:
            self.baselines = {}
    
    def save_baselines(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.baselines, f, indent=2)
    
    def set_baseline(self, metric_name: str, stats: Dict[str, float]):
        self.baselines[metric_name] = stats
    
    def compute_z_score(self, metric_name: str, value: float) -> Optional[float]:
        baseline = self.baselines.get(metric_name)
        if not baseline:
            return None
        
        mean = baseline.get("mean", 0)
        std = baseline.get("std", 1)
        
        if std == 0:
            return 0.0
        
        return (value - mean) / std
    
    def compute_percentile(self, metric_name: str, value: float) -> Optional[float]:
        baseline = self.baselines.get(metric_name)
        if not baseline:
            return None
        
        # Get available percentiles
        percentile_keys = ["p25", "p50", "p75", "p90", "p95"]
        percentile_values = [25, 50, 75, 90, 95]
        
        points = []
        for key, pct in zip(percentile_keys, percentile_values):
            if key in baseline:
                points.append((baseline[key], pct))
        
        # Add min/max
        if "min" in baseline:
            points.append((baseline["min"], 0))
        if "max" in baseline:
            points.append((baseline["max"], 100))
        
        if not points:
            return None
        
        # Sort by value
        points.sort(key=lambda x: x[0])
        
        # Find where value falls
        if value <= points[0][0]:
            return points[0][1]
        if value >= points[-1][0]:
            return points[-1][1]
        
        # Linear interpolation
        for i in range(len(points) - 1):
            v1, p1 = points[i]
            v2, p2 = points[i + 1]
            
            if v1 <= value <= v2:
                if v1 == v2:
                    return p1
                ratio = (value - v1) / (v2 - v1)
                return p1 + ratio * (p2 - p1)
        
        return 50  # Default to median
    
    def is_outlier(
        self,
        metric_name: str,
        value: float,
        z_threshold: float = 2.0
    ) -> bool:
        z_score = self.compute_z_score(metric_name, value)
        if z_score is None:
            return False
        return abs(z_score) > z_threshold
    
    def get_status_from_percentile(
        self,
        metric_name: str,
        value: float,
        direction: str = "lower_is_better"
    ) -> MetricStatus:
        percentile = self.compute_percentile(metric_name, value)
        if percentile is None:
            return MetricStatus.WARNING
        
        if direction == "lower_is_better":
            # Lower percentile is better
            if percentile <= 25:
                return MetricStatus.GOOD
            elif percentile <= 75:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL
        else:
            # Higher percentile is better
            if percentile >= 75:
                return MetricStatus.GOOD
            elif percentile >= 25:
                return MetricStatus.WARNING
            else:
                return MetricStatus.CRITICAL
    
    def normalize_by_percentile(
        self,
        metric_name: str,
        value: float,
        direction: str = "lower_is_better"
    ) -> float:
        percentile = self.compute_percentile(metric_name, value)
        if percentile is None:
            return 0.5
        
        if direction == "lower_is_better":
            # 0th percentile = 1.0, 100th percentile = 0.0
            return 1.0 - (percentile / 100)
        else:
            # 100th percentile = 1.0, 0th percentile = 0.0
            return percentile / 100
    
    def score_metric(
        self,
        name: str,
        value: float,
        weight: float = 1.0,
        direction: str = "lower_is_better"
    ) -> MetricScore:
        z_score = self.compute_z_score(name, value)
        percentile = self.compute_percentile(name, value)
        normalized = self.normalize_by_percentile(name, value, direction)
        status = self.get_status_from_percentile(name, value, direction)
        contribution = normalized * weight * 100
        
        return MetricScore(
            name=name,
            raw_value=value,
            normalized_value=normalized,
            weight=weight,
            contribution=contribution,
            status=status,
            z_score=z_score,
            percentile=percentile
        )
    
    def score_all(
        self,
        metrics: Dict[str, float],
        weights: Dict[str, float] = None,
        directions: Dict[str, str] = None
    ) -> List[MetricScore]:
        if weights is None:
            weights = {k: 1.0 for k in metrics.keys()}
        
        if directions is None:
            # Default directions
            directions = {
                "meddra_coding_rate": "higher_is_better",
                "whodd_coding_rate": "higher_is_better",
            }
        
        scores = []
        for name, value in metrics.items():
            weight = weights.get(name, 1.0)
            direction = directions.get(name, "lower_is_better")
            scores.append(self.score_metric(name, value, weight, direction))
        
        return scores
    
    @classmethod
    def compute_baselines_from_data(
        cls,
        feature_df,
        columns: List[str] = None
    ) -> Dict[str, Dict[str, float]]:
        import pandas as pd
        
        if columns is None:
            columns = feature_df.columns.tolist()
        
        baselines = {}
        for col in columns:
            if col not in feature_df.columns:
                continue
            
            values = feature_df[col].dropna()
            if len(values) == 0:
                continue
            
            baselines[col] = {
                "mean": float(values.mean()),
                "std": float(values.std()) if len(values) > 1 else 0.0,
                "min": float(values.min()),
                "max": float(values.max()),
                "p25": float(values.quantile(0.25)),
                "p50": float(values.quantile(0.50)),
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.90)),
                "p95": float(values.quantile(0.95)),
            }
        
        return baselines
    
    @classmethod
    def from_dataframe(cls, feature_df, columns: List[str] = None) -> "StatisticalScorer":
        baselines = cls.compute_baselines_from_data(feature_df, columns)
        return cls(baselines=baselines)
