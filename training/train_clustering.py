from analytics.clustering.clusterer import SiteClusterer
import pandas as pd

clusterer = SiteClusterer()
print("Running DBSCAN Clustering...")
success = clusterer.train()

if success:
    print("Clustering complete.")
    clusters = clusterer.get_clusters()
    df = pd.DataFrame(list(clusters.items()), columns=["site_id", "cluster"])
    print("\nCluster Distribution:")
    print(df["cluster"].value_counts())
    
    print("\nSample Sites:")
    print(df.head())
else:
    print("Clustering failed.")
