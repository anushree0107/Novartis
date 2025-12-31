import os
import joblib
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from analytics.dqi.feature_extractor import DQIFeatureExtractor

class SiteClusterer:
    def __init__(self, mapping_path="models/clustering/site_clusters.joblib"):
        self.mapping_path = mapping_path
        self.feature_extractor = DQIFeatureExtractor()
        self.cluster_map = {}
        
    def _prepare_features(self):
        df = self.feature_extractor.extract_all_sites()
        if df.empty:
            return None, None
        
        feature_cols = [
            "missing_visits_pct", "missing_pages_pct", "open_issues_per_subject",
            "safety_pending_pct", "days_outstanding_avg", "days_pages_missing_avg"
        ]
        valid_cols = [c for c in feature_cols if c in df.columns]
        X = df[valid_cols].fillna(0)
        return X, df.index # index is site_id
        
    def train(self):
        X, site_ids = self._prepare_features()
        if X is None:
            return False
            
        # DBSCAN requires scaling
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # DBSCAN
        # eps=0.5 is default, but might need tuning. 
        # Given normalized percentages (0-1) and some counts, standard scaling makes them roughly N(0,1).
        # eps=0.5 should capture dense regions. min_samples=3 allows small clusters.
        db = DBSCAN(eps=2.0, min_samples=3) # Relaxed eps to avoid everything being noise
        labels = db.fit_predict(X_scaled)
        
        # Create mapping
        self.cluster_map = {str(sid): int(lbl) for sid, lbl in zip(site_ids, labels)}
        
        # Save
        os.makedirs(os.path.dirname(self.mapping_path), exist_ok=True)
        joblib.dump(self.cluster_map, self.mapping_path)
        
        # Also maybe analyze cluster centers? (Not possible directly with DBSCAN, need to aggregate)
        return True

    def load(self):
        if os.path.exists(self.mapping_path):
            self.cluster_map = joblib.load(self.mapping_path)
            return True
        return False
        
    def get_clusters(self):
        if not self.cluster_map:
            self.load()
        return self.cluster_map
        
    def get_site_cluster(self, site_id: str):
        if not self.cluster_map:
            self.load()
        return self.cluster_map.get(str(site_id), None)

    def get_cluster_profiles(self):
        if not self.cluster_map:
            self.load()
            
        X, site_ids = self._prepare_features()
        if X is None or not self.cluster_map:
            return {}
            
        # Map clusters to X
        # X index is site_id
        # Ensure site_ids are strings for mapping
        X["cluster"] = [self.cluster_map.get(str(sid)) for sid in X.index]
        
        # Drop sites that don't have a cluster (e.g. new sites since training)
        X = X.dropna(subset=["cluster"])
        
        # Groupby
        profiles = X.groupby("cluster").mean()
        counts = X["cluster"].value_counts()
        
        result = {}
        for cluster_id in profiles.index:
            cid = int(cluster_id)
            result[cid] = {
                "count": int(counts[cluster_id]),
                "features": {k: float(v) for k, v in profiles.loc[cluster_id].to_dict().items()}
            }
        return result
