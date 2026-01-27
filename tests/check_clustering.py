import requests
import json

BASE_URL = "http://localhost:8000"

def check_clustering():
    print("=" * 60)
    print("📊 Checking Cluster Formation")
    print("=" * 60)
    
    try:
        # Get ensemble clustering dashboard
        resp = requests.get(f"{BASE_URL}/api/analytics/clustering/advanced/dashboard", timeout=60)
        
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code}")
            print(resp.text[:500])
            return
            
        data = resp.json()
        
        print(f"\n Clustering Results:")
        print(f"   Method: {data.get('method_display_name', data.get('method'))}")
        print(f"   Total Sites: {data.get('total_sites')}")
        print(f"   Number of Clusters: {data.get('n_clusters')}")
        print(f"   Quality Score (Silhouette): {data.get('quality_score', 0):.3f}")
        print(f"   Quality Label: {data.get('quality_label')}")
        
        print(f"\n Cluster Profiles:")
        print("-" * 50)
        
        profiles = data.get('profiles', [])
        for p in profiles:
            print(f"\n   Cluster {p.get('cluster_id')}:")
            print(f"     Size: {p.get('size')} sites ({p.get('percentage')}%)")
            print(f"     Risk Level: {p.get('risk_level')} {p.get('icon', '')}")
            print(f"     Description: {p.get('description', 'N/A')[:100]}...")
            print(f"     Representative Sites: {p.get('representative_sites', [])[:3]}")
            
        print(f"\n Risk Breakdown:")
        risk_chart = data.get('risk_breakdown_chart', {})
        for item in risk_chart.get('data', []):
            if item.get('value', 0) > 0:
                print(f"   {item.get('name')}: {item.get('value')} sites ({item.get('percentage', 0):.1f}%)")
                
    except Exception as e:
        print(f" Error: {e}")

def check_3d():
    print("\n" + "=" * 60)
    print(" Checking 3D Visualization Data")
    print("=" * 60)
    
    try:
        resp = requests.get(f"{BASE_URL}/api/analytics/clustering/advanced/3d", timeout=60)
        
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code}")
            print(resp.text[:500])
            return
            
        data = resp.json()
        
        print(f"\n 3D Data:")
        print(f"   Total Points: {data.get('total_sites')}")
        print(f"   Clusters: {data.get('n_clusters')}")
        print(f"   Reduction Method: {data.get('reduction')}")
        
        print(f"\n   Sample Points (first 5):")
        for p in data.get('points', [])[:5]:
            print(f"     {p['site_id']}: ({p['x']:.2f}, {p['y']:.2f}, {p['z']:.2f}) -> Cluster {p['cluster_id']} ({p['risk_level']})")
        
        print(f"\n   Clusters:")
        for c in data.get('clusters', []):
            print(f"     Cluster {c['cluster_id']}: {c['size']} sites, {c['risk_level']} risk")
            
    except Exception as e:
        print(f" Error: {e}")


if __name__ == "__main__":
    check_clustering()
    check_3d()
    print("\n" + "=" * 60)
    print(" Check completed!")
    print("=" * 60)
