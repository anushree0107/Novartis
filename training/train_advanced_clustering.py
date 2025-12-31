
from analytics.clustering.advanced_clusterer import (
    AdvancedSiteClusterer,
    ClusteringMethod,
    LinkageMethod
)


def main():
    print("=" * 60)
    print(" Training Advanced Site Clustering Models")
    print("=" * 60)
    
    clusterer = AdvancedSiteClusterer()
    
    # Train Hierarchical Clustering
    print("\n Training Hierarchical Clustering (Ward)...")
    hier_result = clusterer.cluster_hierarchical(linkage_method=LinkageMethod.WARD)
    if hier_result:
        print(f"    Hierarchical: {hier_result.n_clusters} clusters")
        print(f"   Silhouette Score: {hier_result.silhouette_score:.4f}")
        print(f"   Calinski-Harabasz: {hier_result.calinski_harabasz_score:.4f}")
        for profile in hier_result.profiles:
            print(f"      - Cluster {profile.cluster_id}: {profile.size} sites ({profile.risk_level} risk)")
    else:
        print("    Hierarchical clustering failed")
    
    # Train GMM
    print("\n Training Gaussian Mixture Model...")
    gmm_result = clusterer.cluster_gmm()
    if gmm_result:
        print(f"    GMM: {gmm_result.n_clusters} clusters")
        print(f"    Silhouette Score: {gmm_result.silhouette_score:.4f}")
        for profile in gmm_result.profiles:
            print(f"      - Cluster {profile.cluster_id}: {profile.size} sites ({profile.risk_level} risk)")
    else:
        print("    GMM clustering failed")
    
    # Train Ensemble
    print("\n Training Ensemble Clustering...")
    ensemble_result = clusterer.cluster_ensemble()
    if ensemble_result:
        print(f"    Ensemble: {ensemble_result.n_clusters} clusters")
        print(f"    Silhouette Score: {ensemble_result.silhouette_score:.4f}")
        for profile in ensemble_result.profiles:
            print(f"      - Cluster {profile.cluster_id}: {profile.size} sites ({profile.risk_level} risk)")
            print(f"        Description: {profile.description}")
    else:
        print("    Ensemble clustering failed")
    
    # Compare Methods
    print("\n Comparing Clustering Methods...")
    comparison = clusterer.compare_methods()
    print(f"    Recommended Method: {comparison['recommended_method']}")
    print(f"    Reason: {comparison['recommendation_reason']}")
    
    


if __name__ == "__main__":
    main()
