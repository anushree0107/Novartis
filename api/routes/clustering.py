from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from analytics.clustering.clusterer import SiteClusterer
from analytics.clustering.advanced_clusterer import (
    AdvancedSiteClusterer,
    ClusteringMethod,
    LinkageMethod,
    ClusterProfile,
    ClusteringResult
)
from analytics.clustering.llm import ClusterAnalyst
from agents.cluster_analyzer import ClusterAnalyzer, SiteAnalyzer
from sklearn.decomposition import PCA
import numpy as np

router = APIRouter()

# Instances
legacy_clusterer = SiteClusterer()
advanced_clusterer = AdvancedSiteClusterer()
analyst = ClusterAnalyst()
cluster_analyzer = ClusterAnalyzer()
site_analyzer = SiteAnalyzer()


# ============ UI Color Mapping ============

RISK_COLORS = {
    "Critical": {"bg": "#DC2626", "text": "#FEF2F2", "border": "#B91C1C", "gradient": "from-red-600 to-red-700"},
    "High": {"bg": "#F97316", "text": "#FFF7ED", "border": "#EA580C", "gradient": "from-orange-500 to-orange-600"},
    "Medium": {"bg": "#EAB308", "text": "#FEFCE8", "border": "#CA8A04", "gradient": "from-yellow-500 to-yellow-600"},
    "Low": {"bg": "#22C55E", "text": "#F0FDF4", "border": "#16A34A", "gradient": "from-green-500 to-green-600"},
    "Unknown": {"bg": "#6B7280", "text": "#F9FAFB", "border": "#4B5563", "gradient": "from-gray-500 to-gray-600"}
}

CLUSTER_COLORS = [
    {"primary": "#6366F1", "secondary": "#818CF8", "name": "Indigo"},
    {"primary": "#8B5CF6", "secondary": "#A78BFA", "name": "Violet"},
    {"primary": "#EC4899", "secondary": "#F472B6", "name": "Pink"},
    {"primary": "#14B8A6", "secondary": "#2DD4BF", "name": "Teal"},
    {"primary": "#F59E0B", "secondary": "#FBBF24", "name": "Amber"},
    {"primary": "#3B82F6", "secondary": "#60A5FA", "name": "Blue"},
    {"primary": "#EF4444", "secondary": "#F87171", "name": "Red"},
    {"primary": "#10B981", "secondary": "#34D399", "name": "Emerald"},
    {"primary": "#F97316", "secondary": "#FB923C", "name": "Orange"},
    {"primary": "#06B6D4", "secondary": "#22D3EE", "name": "Cyan"},
    {"primary": "#8B5CF6", "secondary": "#A78BFA", "name": "Purple"},
    {"primary": "#84CC16", "secondary": "#A3E635", "name": "Lime"},
]


# ============ Pydantic Models ============

class UIClusterProfile(BaseModel):
    cluster_id: int
    cluster_name: str
    size: int
    percentage: float
    risk_level: str
    risk_color: Dict[str, str]
    cluster_color: Dict[str, str]
    description: str
    icon: str
    feature_means: Dict[str, float]
    feature_stds: Dict[str, float]
    centroid: Dict[str, float]
    representative_sites: List[str]
    # For UI cards
    stats: List[Dict[str, Any]]


class UIClusteringResult(BaseModel):
    method: str
    method_display_name: str
    n_clusters: int
    total_sites: int
    quality_score: float
    quality_label: str
    quality_color: str
    metrics: Dict[str, Any]
    profiles: List[Dict[str, Any]]  # Accept dict for flexibility
    # Chart data
    distribution_chart: Dict[str, Any]
    risk_breakdown_chart: Dict[str, Any]
    feature_radar_chart: Dict[str, Any]


class UISiteCluster(BaseModel):
    site_id: str
    cluster_id: int
    cluster_name: str
    cluster_color: Dict[str, str]
    risk_level: str
    risk_color: Dict[str, str]
    method: str
    confidence: Optional[float] = None
    cluster_probabilities: Optional[List[Dict[str, Any]]] = None
    similar_sites: List[str]
    cluster_stats: Dict[str, Any]


class UIMethodComparison(BaseModel):
    methods: List[Dict[str, Any]]
    recommended: Dict[str, Any]
    comparison_chart: Dict[str, Any]


# ============ Helper Functions ============

def get_cluster_color(cluster_id: int) -> Dict[str, str]:
    return CLUSTER_COLORS[cluster_id % len(CLUSTER_COLORS)]

def get_risk_color(risk_level: str) -> Dict[str, str]:
    return RISK_COLORS.get(risk_level, RISK_COLORS["Unknown"])

def get_risk_icon(risk_level: str) -> str:
    icons = {
        "Critical": "🔴",
        "High": "🟠", 
        "Medium": "🟡",
        "Low": "🟢",
        "Unknown": "⚪"
    }
    return icons.get(risk_level, "⚪")

def get_quality_label(silhouette: float) -> tuple:
    if silhouette >= 0.7:
        return "Excellent", "#22C55E"
    elif silhouette >= 0.5:
        return "Good", "#84CC16"
    elif silhouette >= 0.25:
        return "Fair", "#EAB308"
    else:
        return "Poor", "#EF4444"

def format_feature_stat(name: str, value: float) -> Dict[str, Any]:
    """Format feature for UI display."""
    display_name = name.replace("_", " ").title()
    
    if "_pct" in name:
        formatted = f"{value * 100:.1f}%"
        bar_value = min(value * 100, 100)
    elif "days" in name:
        formatted = f"{value:.1f} days"
        bar_value = min(value / 100 * 100, 100)
    else:
        formatted = f"{value:.2f}"
        bar_value = min(value * 20, 100)
    
    return {
        "name": display_name,
        "raw_name": name,
        "value": value,
        "formatted": formatted,
        "bar_value": bar_value
    }

def build_profile_for_ui(profile: ClusterProfile, total_sites: int) -> UIClusterProfile:
    """Convert cluster profile to UI-ready format."""
    cluster_color = get_cluster_color(profile.cluster_id)
    risk_color = get_risk_color(profile.risk_level)
    
    # Build stats for cards
    stats = []
    for name, value in list(profile.feature_means.items())[:4]:
        stats.append(format_feature_stat(name, value))
    
    return UIClusterProfile(
        cluster_id=profile.cluster_id,
        cluster_name=f"Cluster {profile.cluster_id}",
        size=profile.size,
        percentage=round(profile.size / total_sites * 100, 1) if total_sites > 0 else 0,
        risk_level=profile.risk_level,
        risk_color=risk_color,
        cluster_color=cluster_color,
        description=profile.description,
        icon=get_risk_icon(profile.risk_level),
        feature_means=profile.feature_means,
        feature_stds=profile.feature_stds,
        centroid=profile.centroid,
        representative_sites=profile.representative_sites[:5],
        stats=stats
    )


# ============ Legacy Endpoints ============

@router.get("/sites")
def get_site_clusters():
    """Get site cluster assignments (legacy DBSCAN)."""
    clusters = legacy_clusterer.get_clusters()
    if not clusters:
        success = legacy_clusterer.train()
        if success:
            clusters = legacy_clusterer.get_clusters()
            
    if not clusters:
        raise HTTPException(status_code=500, detail="Clustering model unavailable")
         
    return clusters


@router.get("/insights")
def get_cluster_insights():
    """Get cluster insights with LLM analysis (legacy)."""
    profiles = legacy_clusterer.get_cluster_profiles()
    if not profiles:
        legacy_clusterer.train()
        profiles = legacy_clusterer.get_cluster_profiles()
         
    if not profiles:
        raise HTTPException(status_code=404, detail="No clusters found. Train first.")
         
    analysis = analyst.analyze_clusters(profiles)
    return {
        "profiles": profiles,
        "analysis": analysis
    }


@router.post("/train")
def train_clusters():
    """Train legacy DBSCAN clustering model."""
    success = legacy_clusterer.train()
    if success:
        return {"status": "success", "count": len(legacy_clusterer.get_clusters())}
    raise HTTPException(status_code=500, detail="Training failed")


# ============ UI-Ready Advanced Endpoints ============

@router.get("/advanced/dashboard")
async def get_clustering_dashboard():
    """
    Get complete clustering dashboard data.
    
    Returns all data needed for a rich clustering visualization dashboard.
    """
    # Run ensemble clustering
    result = advanced_clusterer.cluster_ensemble()
    if not result:
        result = advanced_clusterer.load_result("ensemble")
    
    if not result:
        raise HTTPException(status_code=500, detail="No clustering data available")
    
    total_sites = len(result.labels)
    quality_label, quality_color = get_quality_label(result.silhouette_score)
    
    # Build UI profiles
    ui_profiles = [build_profile_for_ui(p, total_sites) for p in result.profiles]
    
    # Distribution chart data (for pie/donut chart)
    distribution_chart = {
        "type": "donut",
        "data": [
            {
                "name": f"Cluster {p.cluster_id}",
                "value": p.size,
                "color": get_cluster_color(p.cluster_id)["primary"],
                "percentage": round(p.size / total_sites * 100, 1)
            }
            for p in result.profiles
        ],
        "total": total_sites
    }
    
    # Risk breakdown chart
    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for p in result.profiles:
        risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + p.size
    
    risk_breakdown_chart = {
        "type": "bar",
        "data": [
            {
                "name": level,
                "value": count,
                "color": RISK_COLORS[level]["bg"],
                "percentage": round(count / total_sites * 100, 1) if total_sites > 0 else 0
            }
            for level, count in risk_counts.items()
        ]
    }
    
    # Feature radar chart (average across all clusters)
    feature_names = list(result.profiles[0].feature_means.keys()) if result.profiles else []
    radar_data = []
    for p in result.profiles:
        radar_data.append({
            "cluster": f"Cluster {p.cluster_id}",
            "color": get_cluster_color(p.cluster_id)["primary"],
            "values": [
                {"axis": name.replace("_", " ").title()[:15], "value": min(p.feature_means.get(name, 0) * 100, 100)}
                for name in feature_names[:6]
            ]
        })
    
    feature_radar_chart = {
        "type": "radar",
        "axes": [name.replace("_", " ").title()[:15] for name in feature_names[:6]],
        "data": radar_data
    }
    
    return UIClusteringResult(
        method="ensemble",
        method_display_name="Ensemble Clustering",
        n_clusters=result.n_clusters,
        total_sites=total_sites,
        quality_score=result.silhouette_score,
        quality_label=quality_label,
        quality_color=quality_color,
        metrics={
            "silhouette": {"value": result.silhouette_score, "label": "Silhouette Score", "description": "Cluster cohesion measure (higher is better)"},
            "calinski_harabasz": {"value": result.calinski_harabasz_score, "label": "Calinski-Harabasz", "description": "Cluster separation measure"},
            "davies_bouldin": {"value": result.davies_bouldin_score, "label": "Davies-Bouldin", "description": "Cluster similarity (lower is better)"}
        },
        profiles=[p.dict() for p in ui_profiles],
        distribution_chart=distribution_chart,
        risk_breakdown_chart=risk_breakdown_chart,
        feature_radar_chart=feature_radar_chart
    )


@router.get("/advanced/hierarchical", response_model=UIClusteringResult)
async def cluster_hierarchical_ui(
    n_clusters: Optional[int] = Query(None, description="Number of clusters"),
    linkage: str = Query("ward", description="Linkage method")
):
    """Hierarchical clustering with UI-ready response."""
    try:
        linkage_method = LinkageMethod(linkage)
    except ValueError:
        linkage_method = LinkageMethod.WARD
    
    result = advanced_clusterer.cluster_hierarchical(n_clusters=n_clusters, linkage_method=linkage_method)
    if not result:
        raise HTTPException(status_code=500, detail="Clustering failed")
    
    return _build_ui_result(result, "Hierarchical Clustering")


@router.get("/advanced/gmm", response_model=UIClusteringResult)
async def cluster_gmm_ui(
    n_clusters: Optional[int] = Query(None, description="Number of clusters")
):
    """GMM clustering with UI-ready response."""
    result = advanced_clusterer.cluster_gmm(n_clusters=n_clusters)
    if not result:
        raise HTTPException(status_code=500, detail="Clustering failed")
    
    return _build_ui_result(result, "Gaussian Mixture Model")


@router.get("/advanced/ensemble", response_model=UIClusteringResult)
async def cluster_ensemble_ui(
    n_clusters: Optional[int] = Query(None, description="Number of clusters")
):
    """Ensemble clustering with UI-ready response."""
    result = advanced_clusterer.cluster_ensemble(n_clusters=n_clusters)
    if not result:
        raise HTTPException(status_code=500, detail="Clustering failed")
    
    return _build_ui_result(result, "Ensemble Clustering")


@router.get("/advanced/site/{site_id}", response_model=UISiteCluster)
async def get_site_cluster_ui(
    site_id: str,
    method: str = Query("ensemble", description="Clustering method")
):
    """Get detailed cluster info for a site with UI-ready response."""
    result = advanced_clusterer.get_site_cluster(site_id, method=method)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    
    cluster_id = result["cluster_id"]
    cluster_color = get_cluster_color(cluster_id)
    
    # Get profile for this cluster
    profile = result.get("cluster_profile", {})
    risk_level = profile.get("risk_level", "Unknown") if profile else "Unknown"
    
    # Build probability display for GMM
    prob_display = None
    if result.get("cluster_probabilities"):
        probs = result["cluster_probabilities"]
        prob_display = [
            {
                "cluster_id": i,
                "cluster_name": f"Cluster {i}",
                "probability": round(p * 100, 1),
                "color": get_cluster_color(i)["primary"]
            }
            for i, p in enumerate(probs)
        ]
        prob_display.sort(key=lambda x: x["probability"], reverse=True)
    
    return UISiteCluster(
        site_id=site_id,
        cluster_id=cluster_id,
        cluster_name=f"Cluster {cluster_id}",
        cluster_color=cluster_color,
        risk_level=risk_level,
        risk_color=get_risk_color(risk_level),
        method=method,
        confidence=max(result.get("cluster_probabilities", [1.0])) * 100 if result.get("cluster_probabilities") else None,
        cluster_probabilities=prob_display,
        similar_sites=profile.get("representative_sites", [])[:5] if profile else [],
        cluster_stats={
            "size": profile.get("size", 0) if profile else 0,
            "description": profile.get("description", "") if profile else "",
            "feature_means": profile.get("feature_means", {}) if profile else {}
        }
    )


@router.get("/advanced/compare", response_model=UIMethodComparison)
async def compare_methods_ui():
    """Compare all clustering methods with UI-ready response."""
    comparison = advanced_clusterer.compare_methods()
    
    methods = []
    for method_name, metrics in comparison["results"].items():
        quality_label, quality_color = get_quality_label(metrics["silhouette"])
        methods.append({
            "name": method_name,
            "display_name": method_name.replace("_", " ").title(),
            "n_clusters": metrics["n_clusters"],
            "silhouette": metrics["silhouette"],
            "calinski_harabasz": metrics["calinski_harabasz"],
            "davies_bouldin": metrics["davies_bouldin"],
            "quality_label": quality_label,
            "quality_color": quality_color,
            "is_recommended": method_name == comparison["recommended_method"]
        })
    
    # Sort by silhouette score
    methods.sort(key=lambda x: x["silhouette"], reverse=True)
    
    # Build comparison chart
    comparison_chart = {
        "type": "grouped_bar",
        "metrics": ["Silhouette", "C-H (scaled)", "D-B (inverted)"],
        "data": [
            {
                "method": m["display_name"],
                "values": [
                    m["silhouette"],
                    min(m["calinski_harabasz"] / 1000, 1),  # Scale down
                    max(0, 1 - m["davies_bouldin"] / 2)  # Invert
                ],
                "color": "#6366F1" if m["is_recommended"] else "#94A3B8"
            }
            for m in methods
        ]
    }
    
    recommended = next((m for m in methods if m["is_recommended"]), methods[0] if methods else None)
    
    return UIMethodComparison(
        methods=methods,
        recommended={
            **recommended,
            "reason": comparison["recommendation_reason"]
        } if recommended else {},
        comparison_chart=comparison_chart
    )


def _build_ui_result(result: ClusteringResult, display_name: str) -> UIClusteringResult:
    total_sites = len(result.labels)
    quality_label, quality_color = get_quality_label(result.silhouette_score)
    
    ui_profiles = [build_profile_for_ui(p, total_sites) for p in result.profiles]
    
    distribution_chart = {
        "type": "donut",
        "data": [
            {
                "name": f"Cluster {p.cluster_id}",
                "value": p.size,
                "color": get_cluster_color(p.cluster_id)["primary"],
                "percentage": round(p.size / total_sites * 100, 1)
            }
            for p in result.profiles
        ],
        "total": total_sites
    }
    
    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for p in result.profiles:
        risk_counts[p.risk_level] = risk_counts.get(p.risk_level, 0) + p.size
    
    risk_breakdown_chart = {
        "type": "bar",
        "data": [
            {"name": level, "value": count, "color": RISK_COLORS[level]["bg"]}
            for level, count in risk_counts.items()
        ]
    }
    
    feature_names = list(result.profiles[0].feature_means.keys()) if result.profiles else []
    feature_radar_chart = {
        "type": "radar",
        "axes": [name.replace("_", " ").title()[:15] for name in feature_names[:6]],
        "data": [
            {
                "cluster": f"Cluster {p.cluster_id}",
                "color": get_cluster_color(p.cluster_id)["primary"],
                "values": [{"axis": n.replace("_", " ").title()[:15], "value": min(p.feature_means.get(n, 0) * 100, 100)} for n in feature_names[:6]]
            }
            for p in result.profiles
        ]
    }
    
    return UIClusteringResult(
        method=result.method.value,
        method_display_name=display_name,
        n_clusters=result.n_clusters,
        total_sites=total_sites,
        quality_score=result.silhouette_score,
        quality_label=quality_label,
        quality_color=quality_color,
        metrics={
            "silhouette": {"value": result.silhouette_score, "label": "Silhouette Score"},
            "calinski_harabasz": {"value": result.calinski_harabasz_score, "label": "Calinski-Harabasz"},
            "davies_bouldin": {"value": result.davies_bouldin_score, "label": "Davies-Bouldin"}
        },
        profiles=[p.dict() for p in ui_profiles],
        distribution_chart=distribution_chart,
        risk_breakdown_chart=risk_breakdown_chart,
        feature_radar_chart=feature_radar_chart
    )


# ============ 3D Visualization & Agent Analysis Endpoints ============

class UI3DPoint(BaseModel):
    """A single point in 3D space representing a site."""
    site_id: str
    x: float
    y: float
    z: float
    cluster_id: int
    cluster_name: str
    color: str
    risk_level: str
    tooltip: Dict[str, Any]


class UI3DVisualization(BaseModel):
    """Complete 3D visualization data."""
    points: List[UI3DPoint]
    clusters: List[Dict[str, Any]]
    method: str
    reduction: str
    total_sites: int
    n_clusters: int


@router.get("/advanced/3d", response_model=UI3DVisualization)
async def get_3d_visualization(
    method: str = Query("ensemble", description="Clustering method"),
    n_clusters: Optional[int] = Query(None, description="Number of clusters")
):
    """
    Get 3D visualization data for site clusters.
    
    Returns coordinates reduced to 3D using PCA, with cluster assignments and tooltips.
    Use this data with Plotly.js or Three.js for interactive 3D scatter plots.
    """
    try:
        # Get clustering result
        if method == "ensemble":
            result = advanced_clusterer.cluster_ensemble(n_clusters=n_clusters)
        elif method == "hierarchical":
            result = advanced_clusterer.cluster_hierarchical(n_clusters=n_clusters)
        elif method == "gmm":
            result = advanced_clusterer.cluster_gmm(n_clusters=n_clusters)
        else:
            result = advanced_clusterer.cluster_ensemble(n_clusters=n_clusters)
        
        if not result:
            raise HTTPException(status_code=500, detail="Clustering failed - no result returned")
        
        # Get feature matrix for dimensionality reduction
        # _prepare_features returns (DataFrame, scaled_array) tuple  
        feature_result = advanced_clusterer._prepare_features()
        if feature_result is None or feature_result[0] is None:
            raise HTTPException(status_code=500, detail="No feature data available")
        
        feature_df = feature_result[0]  # DataFrame with site features
        site_ids = feature_df.index.tolist()
        X = feature_result[1]  # Use scaled features for PCA
        
        # Reduce to 3D using PCA
        n_components = min(3, X.shape[1])
        pca = PCA(n_components=n_components)
        coords_3d = pca.fit_transform(X)
        
        # Build points list
        points = []
        site_to_label = result.labels  # Dict[site_id, cluster_id]
        
        # Build tooltip data from feature values
        feature_names = feature_df.columns.tolist()
        
        for i, site_id in enumerate(site_ids):
            cluster_id = site_to_label.get(str(site_id), site_to_label.get(site_id, -1))
            cluster_color = get_cluster_color(max(0, cluster_id))
            
            # Find risk level from profile
            risk_level = "Unknown"
            for profile in result.profiles:
                if profile.cluster_id == cluster_id:
                    risk_level = profile.risk_level
                    break
            
            # Build tooltip with key metrics
            tooltip = {}
            for name in feature_names[:5]:  # Top 5 features
                tooltip[name] = round(float(feature_df.iloc[i][name]), 3)
            
            # Handle 2D or 3D based on PCA components
            z_val = float(coords_3d[i, 2]) if n_components >= 3 else 0.0
            
            points.append(UI3DPoint(
                site_id=str(site_id),
                x=float(coords_3d[i, 0]),
                y=float(coords_3d[i, 1]),
                z=z_val,
                cluster_id=max(0, cluster_id),
                cluster_name=f"Cluster {cluster_id}",
                color=cluster_color["primary"],
                risk_level=risk_level,
                tooltip=tooltip
            ))
        
        # Build cluster summary
        clusters = []
        for profile in result.profiles:
            clusters.append({
                "cluster_id": profile.cluster_id,
                "name": f"Cluster {profile.cluster_id}",
                "size": profile.size,
                "risk_level": profile.risk_level,
                "color": get_cluster_color(profile.cluster_id)["primary"],
                "description": profile.description
            })
        
        return UI3DVisualization(
            points=points,
            clusters=clusters,
            method=method,
            reduction="pca",
            total_sites=len(points),
            n_clusters=result.n_clusters
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"3D visualization error: {str(e)}")


@router.get("/advanced/analyze/{cluster_id}")
async def analyze_cluster_endpoint(
    cluster_id: int,
    method: str = Query("ensemble", description="Clustering method used")
):
    # Get clustering result
    if method == "ensemble":
        result = advanced_clusterer.cluster_ensemble()
    elif method == "hierarchical":
        result = advanced_clusterer.cluster_hierarchical()
    elif method == "gmm":
        result = advanced_clusterer.cluster_gmm()
    else:
        result = advanced_clusterer.cluster_ensemble()
    
    if not result:
        raise HTTPException(status_code=500, detail="No clustering data available")
    
    # Find the cluster profile
    cluster_profile = None
    for profile in result.profiles:
        if profile.cluster_id == cluster_id:
            cluster_profile = profile.to_dict()
            break
    
    if not cluster_profile:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    
    # Get sites in this cluster
    sites_in_cluster = [
        site_id for site_id, label in result.labels.items() 
        if label == cluster_id
    ]
    
    # Get all profiles for comparison
    all_profiles = [p.to_dict() for p in result.profiles]
    
    # Run AI analysis
    analysis = await cluster_analyzer.analyze_cluster(
        cluster_id=cluster_id,
        cluster_profile=cluster_profile,
        all_profiles=all_profiles,
        sites_in_cluster=sites_in_cluster
    )
    
    # Add cluster color info
    analysis["cluster_color"] = get_cluster_color(cluster_id)
    analysis["risk_color"] = get_risk_color(cluster_profile.get("risk_level", "Unknown"))
    
    return analysis


@router.get("/advanced/analyze/site/{site_id}")
async def analyze_site_endpoint(
    site_id: str,
    method: str = Query("ensemble", description="Clustering method used")
):
    """
    Get AI-powered analysis for a specific site.
    
    Returns structured insights including:
    - Performance summary
    - Strengths and concerns
    - Risk level
    - Specific recommendations
    - Comparison to cluster peers
    """
    try:
        # Get clustering result
        if method == "ensemble":
            result = advanced_clusterer.cluster_ensemble()
        elif method == "hierarchical":
            result = advanced_clusterer.cluster_hierarchical()
        elif method == "gmm":
            result = advanced_clusterer.cluster_gmm()
        else:
            result = advanced_clusterer.cluster_ensemble()
        
        if not result:
            raise HTTPException(status_code=500, detail="No clustering data available")
        
        # Get site's cluster
        cluster_id = result.labels.get(site_id)
        if cluster_id is None:
            # Try string conversion
            cluster_id = result.labels.get(str(site_id))
        if cluster_id is None:
            raise HTTPException(status_code=404, detail=f"Site {site_id} not found in clustering")
        
        # Get cluster profile
        cluster_profile = None
        for profile in result.profiles:
            if profile.cluster_id == cluster_id:
                cluster_profile = profile.to_dict()
                break
        
        if not cluster_profile:
            raise HTTPException(status_code=500, detail=f"Cluster profile not found")
        
        # Get site metrics from feature data
        # _prepare_features returns (DataFrame, scaled_array) tuple
        feature_result = advanced_clusterer._prepare_features()
        site_metrics = {}
        if feature_result is not None and feature_result[0] is not None:
            feature_df = feature_result[0]  # Get the DataFrame from tuple
            idx_list = feature_df.index.tolist()
            if site_id in idx_list:
                site_metrics = feature_df.loc[site_id].to_dict()
            elif str(site_id) in idx_list:
                site_metrics = feature_df.loc[str(site_id)].to_dict()
        
        # Get other sites in cluster - ensure labels is a dict
        labels_dict = result.labels if isinstance(result.labels, dict) else {}
        cluster_sites = [
            str(sid) for sid, label in labels_dict.items()
            if label == cluster_id
        ]
        
        # Run AI analysis
        analysis = await site_analyzer.analyze_site(
            site_id=site_id,
            site_metrics=site_metrics,
            cluster_id=cluster_id,
            cluster_profile=cluster_profile,
            cluster_sites=cluster_sites
        )
        
        # Add color info
        analysis["cluster_color"] = get_cluster_color(cluster_id)
        analysis["risk_color"] = get_risk_color(analysis.get("risk_level", "Unknown"))
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Site analysis error: {str(e)}")
