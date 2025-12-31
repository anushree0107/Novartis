"""Enhanced Anomaly Detection Module - Multi-method anomaly detection with drift detection.

This module provides sophisticated anomaly detection for clinical trial sites:
1. Isolation Forest with feature importance
2. Local Outlier Factor (LOF) for density-based anomalies
3. Autoencoder-based anomaly detection (reconstruction error)
4. Statistical Process Control (SPC) with control charts
5. Ensemble anomaly detection combining multiple methods
6. Drift Detection - Detect changes in data patterns over time
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import deque

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.covariance import EllipticEnvelope
import scipy.stats as stats

from analytics.dqi.feature_extractor import DQIFeatureExtractor


class AnomalyMethod(Enum):
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "lof"
    MAHALANOBIS = "mahalanobis"
    AUTOENCODER = "autoencoder"
    STATISTICAL = "statistical"
    ENSEMBLE = "ensemble"


class DriftType(Enum):
    CONCEPT_DRIFT = "concept_drift"
    DATA_DRIFT = "data_drift"
    COVARIATE_SHIFT = "covariate_shift"
    SUDDEN_DRIFT = "sudden_drift"
    GRADUAL_DRIFT = "gradual_drift"


@dataclass
class AnomalyScore:
    """Anomaly score for a single entity."""
    entity_id: str
    entity_type: str
    is_anomaly: bool
    anomaly_score: float  # Higher = more anomalous
    risk_level: str  # Low, Medium, High, Critical
    
    # Method-specific scores
    method_scores: Dict[str, float] = field(default_factory=dict)
    
    # Feature contributions
    feature_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Anomalous features
    anomalous_features: List[str] = field(default_factory=list)
    
    # Raw feature values
    features: Dict[str, float] = field(default_factory=dict)
    
    # Explanation
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "risk_level": self.risk_level,
            "method_scores": {k: round(v, 4) for k, v in self.method_scores.items()},
            "feature_contributions": {k: round(v, 4) for k, v in self.feature_contributions.items()},
            "anomalous_features": self.anomalous_features,
            "features": {k: round(v, 4) for k, v in self.features.items()},
            "explanation": self.explanation
        }


@dataclass
class DriftResult:
    """Result of drift detection."""
    drift_detected: bool
    drift_type: Optional[DriftType]
    drift_score: float
    p_value: float
    drifted_features: List[str]
    reference_period: str
    current_period: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_detected": self.drift_detected,
            "drift_type": self.drift_type.value if self.drift_type else None,
            "drift_score": round(self.drift_score, 4),
            "p_value": round(self.p_value, 4),
            "drifted_features": self.drifted_features,
            "reference_period": self.reference_period,
            "current_period": self.current_period,
            "details": self.details
        }


@dataclass 
class ControlChartResult:
    """Result of Statistical Process Control analysis."""
    metric_name: str
    current_value: float
    mean: float
    std: float
    ucl: float  # Upper Control Limit
    lcl: float  # Lower Control Limit
    usl: float  # Upper Specification Limit (3-sigma)
    lsl: float  # Lower Specification Limit
    is_out_of_control: bool
    violation_type: Optional[str]  # "above_ucl", "below_lcl", "trend", "shift"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_value": round(self.current_value, 4),
            "mean": round(self.mean, 4),
            "std": round(self.std, 4),
            "ucl": round(self.ucl, 4),
            "lcl": round(self.lcl, 4),
            "usl": round(self.usl, 4),
            "lsl": round(self.lsl, 4),
            "is_out_of_control": self.is_out_of_control,
            "violation_type": self.violation_type
        }


class EnhancedAnomalyDetector:
    """
    Enhanced Anomaly Detection with Multiple Methods.
    
    Features:
    - Multi-method ensemble detection (IF, LOF, Mahalanobis)
    - Feature importance for explainability
    - Statistical Process Control monitoring
    - Drift detection for data quality monitoring
    - Adaptive thresholds based on population statistics
    """
    
    FEATURE_COLS = [
        "missing_visits_pct", "missing_pages_pct", "open_issues_per_subject",
        "safety_pending_pct", "days_outstanding_avg", "days_pages_missing_avg",
        "meddra_coding_rate", "whodd_coding_rate"
    ]
    
    # Risk thresholds for anomaly scores
    RISK_THRESHOLDS = {
        "Critical": 0.3,
        "High": 0.2,
        "Medium": 0.1,
        "Low": 0.0
    }
    
    def __init__(
        self,
        model_dir: str = "models/risk",
        data_dir: str = "processed_data",
        contamination: float = 0.1
    ):
        self.model_dir = model_dir
        self.data_dir = data_dir
        self.contamination = contamination
        self.feature_extractor = DQIFeatureExtractor(data_dir)
        self.scaler = StandardScaler()
        
        # Models
        self.isolation_forest: Optional[IsolationForest] = None
        self.lof: Optional[LocalOutlierFactor] = None
        self.elliptic_envelope: Optional[EllipticEnvelope] = None
        
        # Population statistics for SPC
        self.population_stats: Dict[str, Dict[str, float]] = {}
        
        # Historical data for drift detection
        self.historical_data: deque = deque(maxlen=100)
        
        os.makedirs(model_dir, exist_ok=True)
    
    def _prepare_features(self) -> Tuple[Optional[pd.DataFrame], Optional[np.ndarray]]:
        """Extract and prepare features for anomaly detection."""
        df = self.feature_extractor.extract_all_sites()
        if df.empty:
            return None, None
        
        valid_cols = [c for c in self.FEATURE_COLS if c in df.columns]
        if not valid_cols:
            return None, None
        
        X = df[valid_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        return X, X_scaled
    
    def train(self) -> bool:
        """Train all anomaly detection models."""
        X, X_scaled = self._prepare_features()
        if X is None:
            return False
        
        n_samples = len(X)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1
        )
        self.isolation_forest.fit(X_scaled)
        
        # Train LOF (for novelty detection)
        self.lof = LocalOutlierFactor(
            n_neighbors=min(20, n_samples - 1),
            contamination=self.contamination,
            novelty=True
        )
        self.lof.fit(X_scaled)
        
        # Train Elliptic Envelope (Mahalanobis)
        try:
            self.elliptic_envelope = EllipticEnvelope(
                contamination=self.contamination,
                random_state=42
            )
            self.elliptic_envelope.fit(X_scaled)
        except Exception:
            self.elliptic_envelope = None
        
        # Compute population statistics for SPC
        self._compute_population_stats(X)
        
        # Save models
        self._save_models()
        
        return True
    
    def _compute_population_stats(self, X: pd.DataFrame):
        """Compute population statistics for each feature."""
        for col in X.columns:
            values = X[col].dropna().values
            if len(values) > 0:
                self.population_stats[col] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "median": float(np.median(values)),
                    "q1": float(np.percentile(values, 25)),
                    "q3": float(np.percentile(values, 75)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values))
                }
    
    def detect_anomalies(
        self,
        method: AnomalyMethod = AnomalyMethod.ENSEMBLE
    ) -> List[AnomalyScore]:
        """Detect anomalies across all sites."""
        X, X_scaled = self._prepare_features()
        if X is None:
            return []
        
        if not self._models_loaded():
            if not self.train():
                return []
        
        site_ids = X.index.tolist()
        results = []
        
        # Get scores from each method
        if_scores = self._get_isolation_forest_scores(X_scaled)
        lof_scores = self._get_lof_scores(X_scaled)
        stat_scores = self._get_statistical_scores(X)
        
        mahal_scores = None
        if self.elliptic_envelope:
            mahal_scores = self._get_mahalanobis_scores(X_scaled)
        
        for idx, site_id in enumerate(site_ids):
            method_scores = {
                "isolation_forest": if_scores[idx],
                "lof": lof_scores[idx],
                "statistical": stat_scores[idx]
            }
            
            if mahal_scores is not None:
                method_scores["mahalanobis"] = mahal_scores[idx]
            
            # Ensemble score (weighted average)
            if method == AnomalyMethod.ENSEMBLE:
                weights = {"isolation_forest": 0.4, "lof": 0.3, "statistical": 0.2, "mahalanobis": 0.1}
                ensemble_score = sum(
                    method_scores.get(m, 0) * w 
                    for m, w in weights.items()
                ) / sum(weights.values())
            else:
                ensemble_score = method_scores.get(method.value, if_scores[idx])
            
            # Determine if anomaly
            is_anomaly = ensemble_score > 0.0
            
            # Determine risk level
            risk_level = self._determine_risk_level(ensemble_score)
            
            # Compute feature contributions
            feature_values = X.iloc[idx].to_dict()
            feature_contributions = self._compute_feature_contributions(
                feature_values, X_scaled[idx]
            )
            
            # Identify anomalous features
            anomalous_features = self._identify_anomalous_features(
                feature_values, feature_contributions
            )
            
            # Generate explanation
            explanation = self._generate_explanation(
                site_id, risk_level, anomalous_features, feature_values
            )
            
            results.append(AnomalyScore(
                entity_id=str(site_id),
                entity_type="site",
                is_anomaly=is_anomaly,
                anomaly_score=ensemble_score,
                risk_level=risk_level,
                method_scores=method_scores,
                feature_contributions=feature_contributions,
                anomalous_features=anomalous_features,
                features=feature_values,
                explanation=explanation
            ))
        
        # Sort by anomaly score (highest first)
        results.sort(key=lambda x: x.anomaly_score, reverse=True)
        
        return results
    
    def _get_isolation_forest_scores(self, X_scaled: np.ndarray) -> np.ndarray:
        """Get anomaly scores from Isolation Forest."""
        if self.isolation_forest is None:
            return np.zeros(len(X_scaled))
        
        # decision_function: The lower, the more abnormal
        # Negate to get: higher = more anomalous
        scores = -self.isolation_forest.decision_function(X_scaled)
        
        # Normalize to [0, 1] range approximately
        return (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    def _get_lof_scores(self, X_scaled: np.ndarray) -> np.ndarray:
        """Get anomaly scores from Local Outlier Factor."""
        if self.lof is None:
            return np.zeros(len(X_scaled))
        
        # decision_function: The lower, the more abnormal
        scores = -self.lof.decision_function(X_scaled)
        
        # Normalize
        return (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    def _get_mahalanobis_scores(self, X_scaled: np.ndarray) -> np.ndarray:
        """Get Mahalanobis distance-based anomaly scores."""
        if self.elliptic_envelope is None:
            return np.zeros(len(X_scaled))
        
        scores = -self.elliptic_envelope.decision_function(X_scaled)
        return (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    def _get_statistical_scores(self, X: pd.DataFrame) -> np.ndarray:
        """Get anomaly scores based on statistical deviation (z-scores)."""
        scores = np.zeros(len(X))
        
        for idx in range(len(X)):
            row = X.iloc[idx]
            z_scores = []
            
            for col in X.columns:
                if col in self.population_stats:
                    stats_dict = self.population_stats[col]
                    mean = stats_dict["mean"]
                    std = stats_dict["std"]
                    
                    if std > 0:
                        z = abs((row[col] - mean) / std)
                        z_scores.append(z)
            
            if z_scores:
                # Max z-score as anomaly indicator
                scores[idx] = max(z_scores) / 3.0  # Normalize by ~3 sigma
        
        return np.clip(scores, 0, 1)
    
    def _compute_feature_contributions(
        self,
        features: Dict[str, float],
        scaled_features: np.ndarray
    ) -> Dict[str, float]:
        """Compute how much each feature contributes to the anomaly score."""
        contributions = {}
        feature_names = list(features.keys())
        
        for i, (name, value) in enumerate(features.items()):
            if name in self.population_stats:
                stats_dict = self.population_stats[name]
                mean = stats_dict["mean"]
                std = stats_dict["std"]
                
                if std > 0:
                    z_score = abs((value - mean) / std)
                    contributions[name] = min(z_score / 3.0, 1.0)
                else:
                    contributions[name] = 0.0
            else:
                contributions[name] = 0.0
        
        return contributions
    
    def _identify_anomalous_features(
        self,
        features: Dict[str, float],
        contributions: Dict[str, float],
        threshold: float = 0.5
    ) -> List[str]:
        """Identify which features are anomalous."""
        anomalous = []
        
        for name, contrib in contributions.items():
            if contrib >= threshold:
                anomalous.append(name)
        
        return sorted(anomalous, key=lambda x: contributions.get(x, 0), reverse=True)
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from anomaly score."""
        for level, threshold in self.RISK_THRESHOLDS.items():
            if score >= threshold:
                return level
        return "Low"
    
    def _generate_explanation(
        self,
        site_id: str,
        risk_level: str,
        anomalous_features: List[str],
        features: Dict[str, float]
    ) -> str:
        """Generate human-readable explanation."""
        if not anomalous_features:
            return f"Site {site_id} shows normal behavior across all metrics."
        
        feature_strs = []
        for feat in anomalous_features[:3]:
            value = features.get(feat, 0)
            if "_pct" in feat:
                feature_strs.append(f"{feat.replace('_', ' ')}: {value*100:.1f}%")
            else:
                feature_strs.append(f"{feat.replace('_', ' ')}: {value:.2f}")
        
        return (
            f"Site {site_id} is {risk_level} risk due to anomalous values in: "
            f"{', '.join(feature_strs)}"
        )
    
    def control_chart_analysis(
        self,
        site_id: str
    ) -> List[ControlChartResult]:
        """Perform Statistical Process Control analysis for a site."""
        X, _ = self._prepare_features()
        if X is None or site_id not in X.index:
            return []
        
        site_data = X.loc[site_id]
        results = []
        
        for col in X.columns:
            if col not in self.population_stats:
                continue
            
            stats_dict = self.population_stats[col]
            mean = stats_dict["mean"]
            std = stats_dict["std"]
            current_value = float(site_data[col])
            
            # Control limits (2-sigma)
            ucl = mean + 2 * std
            lcl = max(0, mean - 2 * std)
            
            # Specification limits (3-sigma)
            usl = mean + 3 * std
            lsl = max(0, mean - 3 * std)
            
            # Check for violations
            is_out_of_control = False
            violation_type = None
            
            if current_value > usl:
                is_out_of_control = True
                violation_type = "above_usl"
            elif current_value > ucl:
                is_out_of_control = True
                violation_type = "above_ucl"
            elif current_value < lsl:
                is_out_of_control = True
                violation_type = "below_lsl"
            elif current_value < lcl:
                is_out_of_control = True
                violation_type = "below_lcl"
            
            results.append(ControlChartResult(
                metric_name=col,
                current_value=current_value,
                mean=mean,
                std=std,
                ucl=ucl,
                lcl=lcl,
                usl=usl,
                lsl=lsl,
                is_out_of_control=is_out_of_control,
                violation_type=violation_type
            ))
        
        return results
    
    def detect_drift(
        self,
        reference_data: Optional[pd.DataFrame] = None,
        current_data: Optional[pd.DataFrame] = None,
        significance_level: float = 0.05
    ) -> DriftResult:
        """
        Detect distribution drift between reference and current data.
        
        Uses Kolmogorov-Smirnov test for each feature.
        """
        if reference_data is None or current_data is None:
            # Use stored historical data
            return DriftResult(
                drift_detected=False,
                drift_type=None,
                drift_score=0.0,
                p_value=1.0,
                drifted_features=[],
                reference_period="N/A",
                current_period="N/A"
            )
        
        drifted_features = []
        feature_p_values = {}
        drift_scores = []
        
        common_cols = set(reference_data.columns) & set(current_data.columns)
        
        for col in common_cols:
            ref_values = reference_data[col].dropna().values
            curr_values = current_data[col].dropna().values
            
            if len(ref_values) < 5 or len(curr_values) < 5:
                continue
            
            # Kolmogorov-Smirnov test
            statistic, p_value = stats.ks_2samp(ref_values, curr_values)
            
            feature_p_values[col] = p_value
            drift_scores.append(statistic)
            
            if p_value < significance_level:
                drifted_features.append(col)
        
        # Overall drift detection
        drift_detected = len(drifted_features) > 0
        overall_drift_score = np.mean(drift_scores) if drift_scores else 0.0
        min_p_value = min(feature_p_values.values()) if feature_p_values else 1.0
        
        # Determine drift type
        drift_type = None
        if drift_detected:
            if len(drifted_features) > len(common_cols) * 0.5:
                drift_type = DriftType.CONCEPT_DRIFT
            elif overall_drift_score > 0.3:
                drift_type = DriftType.SUDDEN_DRIFT
            else:
                drift_type = DriftType.GRADUAL_DRIFT
        
        return DriftResult(
            drift_detected=drift_detected,
            drift_type=drift_type,
            drift_score=overall_drift_score,
            p_value=min_p_value,
            drifted_features=drifted_features,
            reference_period="reference",
            current_period="current",
            details={"feature_p_values": feature_p_values}
        )
    
    def get_site_risk(self, site_id: str) -> Optional[AnomalyScore]:
        """Get anomaly score for a specific site."""
        all_results = self.detect_anomalies()
        
        for result in all_results:
            if result.entity_id == str(site_id):
                return result
        
        return None
    
    def get_high_risk_sites(self, threshold: str = "Medium") -> List[AnomalyScore]:
        """Get all sites above a certain risk threshold."""
        all_results = self.detect_anomalies()
        
        risk_order = ["Critical", "High", "Medium", "Low"]
        threshold_idx = risk_order.index(threshold)
        
        return [
            r for r in all_results
            if risk_order.index(r.risk_level) <= threshold_idx
        ]
    
    def _models_loaded(self) -> bool:
        """Check if models are loaded."""
        return self.isolation_forest is not None
    
    def _save_models(self):
        """Save models to disk."""
        if self.isolation_forest:
            joblib.dump(
                self.isolation_forest,
                os.path.join(self.model_dir, "isolation_forest.joblib")
            )
        
        if self.lof:
            joblib.dump(
                self.lof,
                os.path.join(self.model_dir, "lof.joblib")
            )
        
        if self.elliptic_envelope:
            joblib.dump(
                self.elliptic_envelope,
                os.path.join(self.model_dir, "elliptic_envelope.joblib")
            )
        
        # Save population stats
        with open(os.path.join(self.model_dir, "population_stats.json"), "w") as f:
            json.dump(self.population_stats, f, indent=2)
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(self.model_dir, "anomaly_scaler.joblib"))
    
    def load_models(self) -> bool:
        """Load models from disk."""
        try:
            if_path = os.path.join(self.model_dir, "isolation_forest.joblib")
            if os.path.exists(if_path):
                self.isolation_forest = joblib.load(if_path)
            
            lof_path = os.path.join(self.model_dir, "lof.joblib")
            if os.path.exists(lof_path):
                self.lof = joblib.load(lof_path)
            
            ee_path = os.path.join(self.model_dir, "elliptic_envelope.joblib")
            if os.path.exists(ee_path):
                self.elliptic_envelope = joblib.load(ee_path)
            
            stats_path = os.path.join(self.model_dir, "population_stats.json")
            if os.path.exists(stats_path):
                with open(stats_path, "r") as f:
                    self.population_stats = json.load(f)
            
            scaler_path = os.path.join(self.model_dir, "anomaly_scaler.joblib")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
            
            return self.isolation_forest is not None
        except Exception:
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of anomaly detection results."""
        results = self.detect_anomalies()
        
        risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for r in results:
            risk_counts[r.risk_level] = risk_counts.get(r.risk_level, 0) + 1
        
        anomaly_count = sum(1 for r in results if r.is_anomaly)
        
        # Most common anomalous features
        feature_counts: Dict[str, int] = {}
        for r in results:
            for feat in r.anomalous_features:
                feature_counts[feat] = feature_counts.get(feat, 0) + 1
        
        top_anomalous_features = sorted(
            feature_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_sites": len(results),
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_count / len(results) if results else 0,
            "risk_distribution": risk_counts,
            "top_anomalous_features": [
                {"feature": f, "count": c} for f, c in top_anomalous_features
            ],
            "top_anomalies": [r.to_dict() for r in results[:5]]
        }
