"""Advanced Clustering Module - Hierarchical and Temporal Site Clustering.

This module provides sophisticated clustering algorithms for clinical trial sites:
1. Hierarchical Clustering - Multi-level site groupings with dendrograms
2. Gaussian Mixture Models - Probabilistic soft clustering
3. Temporal Clustering - Pattern-based behavior clustering over time
4. Ensemble Clustering - Combining multiple methods for robust results
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from sklearn.cluster import (
    AgglomerativeClustering,
    KMeans,
    DBSCAN,
    SpectralClustering
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform

from analytics.dqi.feature_extractor import DQIFeatureExtractor


class ClusteringMethod(Enum):
    HIERARCHICAL = "hierarchical"
    GAUSSIAN_MIXTURE = "gmm"
    KMEANS = "kmeans"
    SPECTRAL = "spectral"
    DBSCAN = "dbscan"
    ENSEMBLE = "ensemble"


class LinkageMethod(Enum):
    WARD = "ward"
    COMPLETE = "complete"
    AVERAGE = "average"
    SINGLE = "single"


@dataclass
class ClusterProfile:
    """Profile of a single cluster."""
    cluster_id: int
    size: int
    centroid: Dict[str, float]
    feature_means: Dict[str, float]
    feature_stds: Dict[str, float]
    risk_level: str  # Low, Medium, High, Critical
    description: str
    representative_sites: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "size": self.size,
            "centroid": self.centroid,
            "feature_means": self.feature_means,
            "feature_stds": self.feature_stds,
            "risk_level": self.risk_level,
            "description": self.description,
            "representative_sites": self.representative_sites
        }


@dataclass
class ClusteringResult:
    """Complete clustering result with metadata."""
    method: ClusteringMethod
    n_clusters: int
    labels: Dict[str, int]  # site_id -> cluster_id
    profiles: List[ClusterProfile]
    silhouette_score: float
    calinski_harabasz_score: float
    davies_bouldin_score: float
    linkage_matrix: Optional[np.ndarray] = None  # For hierarchical
    probabilities: Optional[Dict[str, List[float]]] = None  # For GMM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "n_clusters": self.n_clusters,
            "labels": self.labels,
            "profiles": [p.to_dict() for p in self.profiles],
            "metrics": {
                "silhouette_score": self.silhouette_score,
                "calinski_harabasz_score": self.calinski_harabasz_score,
                "davies_bouldin_score": self.davies_bouldin_score
            },
            "probabilities": self.probabilities
        }


class AdvancedSiteClusterer:
    """
    Advanced Site Clustering with Multiple Algorithms.
    
    Features:
    - Hierarchical clustering with dendrogram visualization
    - Gaussian Mixture Models for soft clustering (probabilities)
    - Ensemble clustering combining multiple methods
    - Automatic optimal cluster selection
    - Rich cluster profiling and interpretation
    """
    
    FEATURE_COLS = [
        "missing_visits_pct", "missing_pages_pct", "open_issues_per_subject",
        "safety_pending_pct", "days_outstanding_avg", "days_pages_missing_avg",
        "meddra_coding_rate", "whodd_coding_rate"
    ]
    
    # Risk thresholds for cluster profiling
    RISK_THRESHOLDS = {
        "missing_visits_pct": {"low": 0.05, "medium": 0.15, "high": 0.30},
        "missing_pages_pct": {"low": 0.05, "medium": 0.15, "high": 0.30},
        "open_issues_per_subject": {"low": 1.0, "medium": 3.0, "high": 5.0},
        "safety_pending_pct": {"low": 0.05, "medium": 0.15, "high": 0.30},
    }
    
    def __init__(
        self, 
        model_dir: str = "models/clustering",
        data_dir: str = "processed_data"
    ):
        self.model_dir = model_dir
        self.data_dir = data_dir
        self.feature_extractor = DQIFeatureExtractor(data_dir)
        self.scaler = StandardScaler()
        self._results_cache: Dict[str, ClusteringResult] = {}
        
        os.makedirs(model_dir, exist_ok=True)
    
    def _prepare_features(self) -> Tuple[Optional[pd.DataFrame], Optional[np.ndarray]]:
        """Extract and prepare features for clustering."""
        df = self.feature_extractor.extract_all_sites()
        if df.empty:
            return None, None
        
        # Select valid columns
        valid_cols = [c for c in self.FEATURE_COLS if c in df.columns]
        if not valid_cols:
            return None, None
        
        X = df[valid_cols].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X, X_scaled
    
    def cluster_hierarchical(
        self,
        n_clusters: Optional[int] = None,
        linkage_method: LinkageMethod = LinkageMethod.WARD,
        distance_threshold: Optional[float] = None
    ) -> Optional[ClusteringResult]:
        """
        Perform Hierarchical Agglomerative Clustering.
        
        Automatically determines optimal number of clusters if not specified
        using the elbow method on dendrogram distances.
        """
        X, X_scaled = self._prepare_features()
        if X is None:
            return None
        
        site_ids = X.index.tolist()
        
        # Compute linkage matrix for dendrogram
        linkage_matrix = linkage(X_scaled, method=linkage_method.value)
        
        # Auto-determine n_clusters if not provided
        if n_clusters is None and distance_threshold is None:
            n_clusters = self._find_optimal_clusters(X_scaled, method="hierarchical")
        
        # Perform clustering
        if distance_threshold:
            labels = fcluster(linkage_matrix, t=distance_threshold, criterion='distance')
            n_clusters = len(set(labels))
        else:
            model = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage=linkage_method.value
            )
            labels = model.fit_predict(X_scaled)
        
        # Create label mapping
        label_map = {str(site_id): int(label) for site_id, label in zip(site_ids, labels)}
        
        # Compute cluster profiles
        profiles = self._compute_cluster_profiles(X, labels, site_ids)
        
        # Compute clustering metrics
        metrics = self._compute_metrics(X_scaled, labels)
        
        result = ClusteringResult(
            method=ClusteringMethod.HIERARCHICAL,
            n_clusters=n_clusters,
            labels=label_map,
            profiles=profiles,
            silhouette_score=metrics["silhouette"],
            calinski_harabasz_score=metrics["calinski_harabasz"],
            davies_bouldin_score=metrics["davies_bouldin"],
            linkage_matrix=linkage_matrix
        )
        
        self._results_cache["hierarchical"] = result
        self._save_result("hierarchical", result)
        
        return result
    
    def cluster_gmm(
        self,
        n_clusters: Optional[int] = None,
        covariance_type: str = "full"
    ) -> Optional[ClusteringResult]:
        """
        Perform Gaussian Mixture Model clustering.
        
        Provides soft clustering with probability assignments.
        """
        X, X_scaled = self._prepare_features()
        if X is None:
            return None
        
        site_ids = X.index.tolist()
        
        # Auto-determine n_clusters using BIC
        if n_clusters is None:
            n_clusters = self._find_optimal_clusters_bic(X_scaled)
        
        # Fit GMM
        gmm = GaussianMixture(
            n_components=n_clusters,
            covariance_type=covariance_type,
            random_state=42,
            n_init=5
        )
        labels = gmm.fit_predict(X_scaled)
        probabilities = gmm.predict_proba(X_scaled)
        
        # Create mappings
        label_map = {str(site_id): int(label) for site_id, label in zip(site_ids, labels)}
        prob_map = {
            str(site_id): probs.tolist() 
            for site_id, probs in zip(site_ids, probabilities)
        }
        
        # Compute cluster profiles
        profiles = self._compute_cluster_profiles(X, labels, site_ids)
        
        # Compute metrics
        metrics = self._compute_metrics(X_scaled, labels)
        
        result = ClusteringResult(
            method=ClusteringMethod.GAUSSIAN_MIXTURE,
            n_clusters=n_clusters,
            labels=label_map,
            profiles=profiles,
            silhouette_score=metrics["silhouette"],
            calinski_harabasz_score=metrics["calinski_harabasz"],
            davies_bouldin_score=metrics["davies_bouldin"],
            probabilities=prob_map
        )
        
        self._results_cache["gmm"] = result
        self._save_result("gmm", result)
        
        return result
    
    def cluster_ensemble(
        self,
        n_clusters: Optional[int] = None,
        methods: List[ClusteringMethod] = None
    ) -> Optional[ClusteringResult]:
        """
        Ensemble clustering combining multiple methods.
        
        Uses consensus clustering to combine results from:
        - Hierarchical (Ward)
        - K-Means
        - GMM
        - Spectral
        """
        X, X_scaled = self._prepare_features()
        if X is None:
            return None
        
        site_ids = X.index.tolist()
        n_samples = len(site_ids)
        
        if n_clusters is None:
            n_clusters = self._find_optimal_clusters(X_scaled, method="kmeans")
        
        # Run multiple clustering algorithms
        all_labels = []
        
        # Hierarchical
        hier = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")
        all_labels.append(hier.fit_predict(X_scaled))
        
        # K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        all_labels.append(kmeans.fit_predict(X_scaled))
        
        # GMM
        gmm = GaussianMixture(n_components=n_clusters, random_state=42)
        all_labels.append(gmm.fit_predict(X_scaled))
        
        # Spectral (if enough samples)
        if n_samples >= n_clusters:
            try:
                spectral = SpectralClustering(
                    n_clusters=n_clusters, 
                    random_state=42,
                    affinity="nearest_neighbors",
                    n_neighbors=min(10, n_samples - 1)
                )
                all_labels.append(spectral.fit_predict(X_scaled))
            except Exception:
                pass
        
        # Build co-association matrix
        co_assoc = np.zeros((n_samples, n_samples))
        for labels in all_labels:
            for i in range(n_samples):
                for j in range(n_samples):
                    if labels[i] == labels[j]:
                        co_assoc[i, j] += 1
        co_assoc /= len(all_labels)
        
        # Final clustering on co-association matrix
        distance_matrix = 1 - co_assoc
        np.fill_diagonal(distance_matrix, 0)
        
        # Use hierarchical clustering on the distance matrix
        condensed_dist = squareform(distance_matrix)
        linkage_matrix = linkage(condensed_dist, method="average")
        final_labels = fcluster(linkage_matrix, t=n_clusters, criterion="maxclust") - 1
        
        # Create mappings
        label_map = {str(site_id): int(label) for site_id, label in zip(site_ids, final_labels)}
        
        # Compute cluster profiles
        profiles = self._compute_cluster_profiles(X, final_labels, site_ids)
        
        # Compute metrics
        metrics = self._compute_metrics(X_scaled, final_labels)
        
        result = ClusteringResult(
            method=ClusteringMethod.ENSEMBLE,
            n_clusters=n_clusters,
            labels=label_map,
            profiles=profiles,
            silhouette_score=metrics["silhouette"],
            calinski_harabasz_score=metrics["calinski_harabasz"],
            davies_bouldin_score=metrics["davies_bouldin"],
            linkage_matrix=linkage_matrix
        )
        
        self._results_cache["ensemble"] = result
        self._save_result("ensemble", result)
        
        return result
    
    def _find_optimal_clusters(
        self, 
        X: np.ndarray, 
        method: str = "kmeans",
        max_clusters: int = 10
    ) -> int:
        """Find optimal number of clusters using silhouette score."""
        n_samples = len(X)
        max_clusters = min(max_clusters, n_samples - 1)
        
        if max_clusters < 2:
            return 2
        
        best_score = -1
        best_k = 2
        
        for k in range(2, max_clusters + 1):
            try:
                if method == "kmeans":
                    model = KMeans(n_clusters=k, random_state=42, n_init=10)
                else:
                    model = AgglomerativeClustering(n_clusters=k)
                
                labels = model.fit_predict(X)
                score = silhouette_score(X, labels)
                
                if score > best_score:
                    best_score = score
                    best_k = k
            except Exception:
                continue
        
        return best_k
    
    def _find_optimal_clusters_bic(
        self, 
        X: np.ndarray, 
        max_clusters: int = 10
    ) -> int:
        """Find optimal clusters for GMM using BIC."""
        n_samples = len(X)
        max_clusters = min(max_clusters, n_samples - 1)
        
        if max_clusters < 2:
            return 2
        
        best_bic = float('inf')
        best_k = 2
        
        for k in range(2, max_clusters + 1):
            try:
                gmm = GaussianMixture(n_components=k, random_state=42)
                gmm.fit(X)
                bic = gmm.bic(X)
                
                if bic < best_bic:
                    best_bic = bic
                    best_k = k
            except Exception:
                continue
        
        return best_k
    
    def _compute_cluster_profiles(
        self,
        X: pd.DataFrame,
        labels: np.ndarray,
        site_ids: List[str]
    ) -> List[ClusterProfile]:
        """Compute detailed profiles for each cluster."""
        profiles = []
        unique_labels = sorted(set(labels))
        
        for cluster_id in unique_labels:
            mask = labels == cluster_id
            cluster_sites = [sid for sid, m in zip(site_ids, mask) if m]
            cluster_data = X.loc[cluster_sites]
            
            # Compute statistics
            feature_means = cluster_data.mean().to_dict()
            feature_stds = cluster_data.std().to_dict()
            centroid = {k: round(v, 4) for k, v in feature_means.items()}
            
            # Determine risk level based on key metrics
            risk_level = self._determine_cluster_risk(feature_means)
            
            # Generate description
            description = self._generate_cluster_description(feature_means, risk_level)
            
            # Get representative sites (closest to centroid)
            representative = self._get_representative_sites(
                cluster_data, centroid, n=3
            )
            
            profiles.append(ClusterProfile(
                cluster_id=int(cluster_id),
                size=len(cluster_sites),
                centroid=centroid,
                feature_means={k: round(v, 4) for k, v in feature_means.items()},
                feature_stds={k: round(v, 4) for k, v in feature_stds.items()},
                risk_level=risk_level,
                description=description,
                representative_sites=[str(s) for s in representative]
            ))
        
        return profiles
    
    def _determine_cluster_risk(self, means: Dict[str, float]) -> str:
        """Determine overall risk level for a cluster."""
        risk_scores = []
        
        for metric, thresholds in self.RISK_THRESHOLDS.items():
            if metric in means:
                value = means[metric]
                if value >= thresholds["high"]:
                    risk_scores.append(3)
                elif value >= thresholds["medium"]:
                    risk_scores.append(2)
                elif value >= thresholds["low"]:
                    risk_scores.append(1)
                else:
                    risk_scores.append(0)
        
        if not risk_scores:
            return "Unknown"
        
        avg_risk = sum(risk_scores) / len(risk_scores)
        
        if avg_risk >= 2.5:
            return "Critical"
        elif avg_risk >= 1.5:
            return "High"
        elif avg_risk >= 0.5:
            return "Medium"
        return "Low"
    
    def _generate_cluster_description(
        self, 
        means: Dict[str, float], 
        risk_level: str
    ) -> str:
        """Generate human-readable cluster description."""
        descriptions = []
        
        # Missing visits
        mv = means.get("missing_visits_pct", 0)
        if mv > 0.15:
            descriptions.append(f"high missing visits ({mv*100:.1f}%)")
        elif mv < 0.05:
            descriptions.append("excellent visit compliance")
        
        # Open issues
        oi = means.get("open_issues_per_subject", 0)
        if oi > 3:
            descriptions.append(f"high issue count ({oi:.1f}/subject)")
        elif oi < 1:
            descriptions.append("low issue burden")
        
        # Safety
        sp = means.get("safety_pending_pct", 0)
        if sp > 0.1:
            descriptions.append(f"pending safety reviews ({sp*100:.1f}%)")
        
        if descriptions:
            desc = f"{risk_level} risk cluster: " + ", ".join(descriptions)
        else:
            desc = f"{risk_level} risk cluster with average performance"
        
        return desc
    
    def _get_representative_sites(
        self,
        cluster_data: pd.DataFrame,
        centroid: Dict[str, float],
        n: int = 3
    ) -> List[str]:
        """Get sites closest to cluster centroid."""
        if cluster_data.empty:
            return []
        
        # Compute distances to centroid
        centroid_vector = np.array([centroid.get(c, 0) for c in cluster_data.columns])
        distances = np.linalg.norm(cluster_data.values - centroid_vector, axis=1)
        
        # Get indices of closest sites
        closest_indices = np.argsort(distances)[:n]
        
        return cluster_data.index[closest_indices].tolist()
    
    def _compute_metrics(
        self, 
        X: np.ndarray, 
        labels: np.ndarray
    ) -> Dict[str, float]:
        """Compute clustering quality metrics."""
        unique_labels = set(labels)
        
        if len(unique_labels) < 2 or len(unique_labels) >= len(X):
            return {
                "silhouette": 0.0,
                "calinski_harabasz": 0.0,
                "davies_bouldin": float('inf')
            }
        
        try:
            sil = silhouette_score(X, labels)
        except Exception:
            sil = 0.0
        
        try:
            ch = calinski_harabasz_score(X, labels)
        except Exception:
            ch = 0.0
        
        try:
            db = davies_bouldin_score(X, labels)
        except Exception:
            db = float('inf')
        
        return {
            "silhouette": round(sil, 4),
            "calinski_harabasz": round(ch, 4),
            "davies_bouldin": round(db, 4)
        }
    
    def _save_result(self, name: str, result: ClusteringResult):
        """Save clustering result to disk."""
        path = os.path.join(self.model_dir, f"{name}_clustering.json")
        
        save_data = result.to_dict()
        # Remove numpy arrays that can't be JSON serialized
        save_data.pop("linkage_matrix", None)
        
        with open(path, "w") as f:
            json.dump(save_data, f, indent=2)
    
    def load_result(self, name: str) -> Optional[ClusteringResult]:
        """Load a saved clustering result."""
        path = os.path.join(self.model_dir, f"{name}_clustering.json")
        
        if not os.path.exists(path):
            return None
        
        with open(path, "r") as f:
            data = json.load(f)
        
        profiles = [
            ClusterProfile(**p) for p in data.get("profiles", [])
        ]
        
        return ClusteringResult(
            method=ClusteringMethod(data["method"]),
            n_clusters=data["n_clusters"],
            labels=data["labels"],
            profiles=profiles,
            silhouette_score=data["metrics"]["silhouette_score"],
            calinski_harabasz_score=data["metrics"]["calinski_harabasz_score"],
            davies_bouldin_score=data["metrics"]["davies_bouldin_score"],
            probabilities=data.get("probabilities")
        )
    
    def get_site_cluster(
        self, 
        site_id: str, 
        method: str = "ensemble"
    ) -> Optional[Dict[str, Any]]:
        """Get cluster assignment for a specific site."""
        result = self._results_cache.get(method) or self.load_result(method)
        
        if not result:
            return None
        
        cluster_id = result.labels.get(str(site_id))
        if cluster_id is None:
            return None
        
        # Find the cluster profile
        profile = next(
            (p for p in result.profiles if p.cluster_id == cluster_id),
            None
        )
        
        response = {
            "site_id": site_id,
            "cluster_id": cluster_id,
            "method": method
        }
        
        if profile:
            response["cluster_profile"] = profile.to_dict()
        
        # Add probabilities if GMM
        if result.probabilities and site_id in result.probabilities:
            response["cluster_probabilities"] = result.probabilities[site_id]
        
        return response
    
    def compare_methods(self) -> Dict[str, Any]:
        """Compare all clustering methods and recommend the best."""
        results = {}
        
        # Run all methods
        hier_result = self.cluster_hierarchical()
        if hier_result:
            results["hierarchical"] = {
                "n_clusters": hier_result.n_clusters,
                "silhouette": hier_result.silhouette_score,
                "calinski_harabasz": hier_result.calinski_harabasz_score,
                "davies_bouldin": hier_result.davies_bouldin_score
            }
        
        gmm_result = self.cluster_gmm()
        if gmm_result:
            results["gmm"] = {
                "n_clusters": gmm_result.n_clusters,
                "silhouette": gmm_result.silhouette_score,
                "calinski_harabasz": gmm_result.calinski_harabasz_score,
                "davies_bouldin": gmm_result.davies_bouldin_score
            }
        
        ensemble_result = self.cluster_ensemble()
        if ensemble_result:
            results["ensemble"] = {
                "n_clusters": ensemble_result.n_clusters,
                "silhouette": ensemble_result.silhouette_score,
                "calinski_harabasz": ensemble_result.calinski_harabasz_score,
                "davies_bouldin": ensemble_result.davies_bouldin_score
            }
        
        # Determine best method
        best_method = None
        best_silhouette = -1
        
        for method, metrics in results.items():
            if metrics["silhouette"] > best_silhouette:
                best_silhouette = metrics["silhouette"]
                best_method = method
        
        return {
            "results": results,
            "recommended_method": best_method,
            "recommendation_reason": f"Highest silhouette score ({best_silhouette:.3f})"
        }
