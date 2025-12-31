import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from analytics.dqi.feature_extractor import DQIFeatureExtractor

class SiteAnomalyDetector:
    def __init__(self, model_path="models/risk/site_risk_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.feature_extractor = DQIFeatureExtractor()
        
    def _prepare_features(self):
        df = self.feature_extractor.extract_all_sites()
        if df.empty:
            return None
        feature_cols = [
            "missing_visits_pct", "missing_pages_pct", "open_issues_per_subject",
            "safety_pending_pct", "days_outstanding_avg", "days_pages_missing_avg"
        ]
        # Use only numeric columns that exist
        valid_cols = [c for c in feature_cols if c in df.columns]
        if not valid_cols:
            return None
            
        X = df[valid_cols].fillna(0)
        return X

    def train(self):
        X = self._prepare_features()
        if X is None or len(X) < 2:
            return False
            
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self.model.fit(X)
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        return True

    def load(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            return True
        return False
        
    def predict(self):
        if not self.model:
            if not self.load():
                return []
                
        X = self._prepare_features()
        if X is None:
            return []
            
        scores = self.model.decision_function(X)
        preds = self.model.predict(X) 
        
        results = []
        for idx, (site_id, row) in enumerate(X.iterrows()):
            is_anomaly = preds[idx] == -1
            # Invert score: lower decision function = more anomalous. 
            # IsolationForest decision_function is positive for inliers, negative for outliers.
            # So anomaly_score = -score.
            raw_score = scores[idx]
            anomaly_score = -raw_score
            
            risk_level = "Low"
            # Tweaking thresholds based on typical IF output range
            if anomaly_score > 0.0: risk_level = "Medium"
            if anomaly_score > 0.1: risk_level = "High"
            if anomaly_score > 0.2: risk_level = "Critical"
            
            results.append({
                "site_id": site_id,
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "risk_level": risk_level,
                "features": {k: float(v) for k, v in row.to_dict().items()}
            })
            
        return sorted(results, key=lambda x: x["anomaly_score"], reverse=True)

    def get_site_risk(self, site_id: str):
        all_results = self.predict()
        target = str(site_id).strip().lower()
        
        # Try finding exact match first (case-insensitive)
        for res in all_results:
            if str(res["site_id"]).lower() == target:
                return res
                
        # Try matching with or without "Site " prefix
        for res in all_results:
            sid = str(res["site_id"]).lower()
            if sid.replace("site ", "") == target.replace("site ", ""):
                return res
                
        return None

    def get_population_stats(self):
        return self.feature_extractor.get_population_statistics()
