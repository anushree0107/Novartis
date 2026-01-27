"""Test script for clustering endpoints - tests site-level analysis"""
import requests

BASE_URL = "http://localhost:8000"


def test_site_analysis():
    """Test the site-level analysis endpoint - this is what you want!"""
    print("=" * 60)
    print("🔬 Testing SITE Analysis Endpoint")
    print("=" * 60)
    
    # Get a site ID from cluster dashboard
    try:
        print("Fetching cluster data to get a site ID...")
        resp = requests.get(f"{BASE_URL}/api/analytics/clustering/advanced/ensemble", timeout=30)
        if resp.status_code != 200:
            print(f"❌ Failed to get clustering data: {resp.status_code}")
            return
            
        data = resp.json()
        profiles = data.get('profiles', [])
        
        if not profiles:
            print("No cluster profiles found")
            return
            
        # Get representative sites from first cluster
        first_profile = profiles[0]
        rep_sites = first_profile.get('representative_sites', [])
        
        if not rep_sites:
            print("No representative sites found")
            return
            
        site_id = rep_sites[0]
        print(f"\n📍 Analyzing site: {site_id}")
        print("-" * 40)
        
        # Call site analysis endpoint
        resp2 = requests.get(
            f"{BASE_URL}/api/analytics/clustering/advanced/analyze/site/{site_id}",
            timeout=60
        )
        
        if resp2.status_code == 200:
            analysis = resp2.json()
            print(f"✅ Success!")
            print(f"\n📋 Summary: {analysis.get('summary', 'N/A')}")
            
            print(f"\n💪 Strengths:")
            for s in analysis.get('strengths', []):
                print(f"   ✓ {s}")
                
            print(f"\n⚠️ Concerns:")
            for c in analysis.get('concerns', []):
                print(f"   ⚠ {c}")
                
            print(f"\n🎯 Risk Level: {analysis.get('risk_level', 'N/A')}")
            
            print(f"\n💡 Recommendations:")
            for r in analysis.get('recommendations', []):
                print(f"   [{r.get('priority', '?')}] {r.get('action', 'N/A')}")
                
            print(f"\n🔗 Cluster Context: {analysis.get('cluster_context', 'N/A')}")
        else:
            print(f"❌ Site analysis failed: {resp2.status_code}")
            print(resp2.text)
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_site_analysis()
    print("\n" + "=" * 60)
    print("🏁 Test completed!")
    print("=" * 60)
