import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"


# ============ Pydantic Models for Structured Output ============

class RiskAssessment(BaseModel):
    """Risk assessment for a cluster."""
    level: str = Field(description="Risk level: Critical, High, Medium, or Low")
    factors: List[str] = Field(description="List of key risk factors identified")
    mitigation: str = Field(description="Recommended mitigation strategy")


class Recommendation(BaseModel):
    """A single actionable recommendation."""
    priority: str = Field(description="Priority level: High, Medium, or Low")
    action: str = Field(description="Specific action to take")
    rationale: str = Field(description="Why this action is important")


class ClusterAnalysis(BaseModel):
    """Complete structured analysis of a cluster."""
    summary: str = Field(description="2-3 sentence executive summary of the cluster characteristics")
    key_patterns: List[str] = Field(description="3-5 key patterns observed in this cluster")
    risk_assessment: RiskAssessment = Field(description="Risk assessment for this cluster")
    recommendations: List[Recommendation] = Field(description="List of actionable recommendations")
    comparison_insights: str = Field(description="How this cluster compares to others")


class ClusterAnalyzer:    
    def __init__(self):
        self.llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
        self.structured_llm = self.llm.with_structured_output(ClusterAnalysis)
    
    async def analyze_cluster(
        self, 
        cluster_id: int,
        cluster_profile: Dict[str, Any],
        all_profiles: List[Dict[str, Any]],
        sites_in_cluster: List[str]
    ) -> Dict[str, Any]:
        feature_summary = self._format_features(cluster_profile.get("feature_means", {}))
        comparison = self._build_comparison(cluster_id, cluster_profile, all_profiles)
        
        prompt = f"""Analyze this clinical trial site cluster and provide structured insights.

## Cluster {cluster_id} Profile

**Risk Level**: {cluster_profile.get('risk_level', 'Unknown')}
**Number of Sites**: {len(sites_in_cluster)}
**Description**: {cluster_profile.get('description', 'No description available')}

### Key Metrics (Averages)
{feature_summary}

### Comparison with Other Clusters
{comparison}

### Sites in this Cluster
{', '.join(sites_in_cluster)}

Provide a comprehensive analysis focusing on patterns, risks, and actionable recommendations."""

        try:
            analysis: ClusterAnalysis = await self.structured_llm.ainvoke([
                SystemMessage(content="You are a clinical trial analytics expert. Analyze the cluster data and provide structured insights."),
                HumanMessage(content=prompt)
            ])
            
            # Convert to dict and add metadata
            result = analysis.model_dump()
            result["cluster_id"] = cluster_id
            result["sites_count"] = len(sites_in_cluster)
            result["status"] = "success"
            
            return result
            
        except Exception as e:
            # Fallback response
            return {
                "cluster_id": cluster_id,
                "sites_count": len(sites_in_cluster),
                "status": "error",
                "summary": f"Cluster {cluster_id} contains {len(sites_in_cluster)} sites with {cluster_profile.get('risk_level', 'unknown')} risk level.",
                "key_patterns": [cluster_profile.get("description", "No patterns identified")],
                "risk_assessment": {
                    "level": cluster_profile.get("risk_level", "Unknown"),
                    "factors": ["Analysis pending - error occurred"],
                    "mitigation": "Review individual site data manually"
                },
                "recommendations": [],
                "comparison_insights": "Unable to generate comparison due to error",
                "error": str(e)
            }
    
    def _format_features(self, features: Dict[str, float]) -> str:
        """Format feature means for the prompt."""
        lines = []
        for name, value in features.items():
            display_name = name.replace("_", " ").title()
            if "_pct" in name:
                lines.append(f"- {display_name}: {value * 100:.1f}%")
            elif "days" in name:
                lines.append(f"- {display_name}: {value:.1f} days")
            else:
                lines.append(f"- {display_name}: {value:.2f}")
        return "\n".join(lines) if lines else "No metrics available"
    
    def _build_comparison(
        self, 
        cluster_id: int, 
        profile: Dict[str, Any], 
        all_profiles: List[Dict[str, Any]]
    ) -> str:
        """Build comparison text with other clusters."""
        if not all_profiles or len(all_profiles) <= 1:
            return "This is the only cluster."
        
        lines = []
        for other in all_profiles:
            if other.get("cluster_id") == cluster_id:
                continue
            lines.append(
                f"- Cluster {other.get('cluster_id')}: {other.get('size', 0)} sites, "
                f"{other.get('risk_level', 'Unknown')} risk"
            )
        
        return "\n".join(lines) if lines else "No other clusters for comparison"
    
    def analyze_cluster_sync(
        self,
        cluster_id: int,
        cluster_profile: Dict[str, Any],
        all_profiles: List[Dict[str, Any]],
        sites_in_cluster: List[str]
    ) -> Dict[str, Any]:
        """Synchronous version of analyze_cluster."""
        import asyncio
        return asyncio.run(self.analyze_cluster(
            cluster_id, cluster_profile, all_profiles, sites_in_cluster
        ))


# ============ Site-Level Analysis ============

class SiteAnalysis(BaseModel):
    """Structured analysis for a single site."""
    summary: str = Field(description="2-3 sentence summary of the site's performance and status")
    strengths: List[str] = Field(description="Key strengths of this site")
    concerns: List[str] = Field(description="Areas of concern for this site")
    risk_level: str = Field(description="Risk level: Critical, High, Medium, or Low")
    recommendations: List[Recommendation] = Field(description="Specific actions for this site")
    cluster_context: str = Field(description="How this site compares to others in its cluster")


class SiteAnalyzer:
    """AI Agent that analyzes individual clinical trial sites."""
    
    def __init__(self):
        self.llm = ChatGroq(model=MODEL_NAME, api_key=GROQ_API_KEY)
        self.structured_llm = self.llm.with_structured_output(SiteAnalysis)
    
    async def analyze_site(
        self,
        site_id: str,
        site_metrics: Dict[str, float],
        cluster_id: int,
        cluster_profile: Dict[str, Any],
        cluster_sites: List[str]
    ) -> Dict[str, Any]:
        """Generate AI analysis for an individual site."""
        
        # Format site metrics
        metrics_text = self._format_metrics(site_metrics)
        cluster_avg = self._format_metrics(cluster_profile.get("feature_means", {}))
        
        prompt = f"""Analyze this individual clinical trial site and provide actionable insights.

## Site: {site_id}

### Site Metrics
{metrics_text}

### Cluster Context
- Cluster ID: {cluster_id}
- Cluster Risk Level: {cluster_profile.get('risk_level', 'Unknown')}
- Sites in Cluster: {len(cluster_sites)}

### Cluster Averages (for comparison)
{cluster_avg}

Analyze this site's performance, identify strengths and concerns, and provide specific recommendations."""

        try:
            analysis: SiteAnalysis = await self.structured_llm.ainvoke([
                SystemMessage(content="You are a clinical trial site performance analyst. Provide detailed, actionable insights for this specific site."),
                HumanMessage(content=prompt)
            ])
            
            result = analysis.model_dump()
            result["site_id"] = site_id
            result["cluster_id"] = cluster_id
            result["status"] = "success"
            
            return result
            
        except Exception as e:
            return {
                "site_id": site_id,
                "cluster_id": cluster_id,
                "status": "error",
                "summary": f"Site {site_id} is in cluster {cluster_id}.",
                "strengths": [],
                "concerns": ["Unable to complete analysis"],
                "risk_level": cluster_profile.get("risk_level", "Unknown"),
                "recommendations": [],
                "cluster_context": "Error during analysis",
                "error": str(e)
            }
    
    def _format_metrics(self, metrics: Dict[str, float]) -> str:
        lines = []
        for name, value in metrics.items():
            display_name = name.replace("_", " ").title()
            if "_pct" in name:
                lines.append(f"- {display_name}: {value * 100:.1f}%")
            elif "days" in name:
                lines.append(f"- {display_name}: {value:.1f} days")
            else:
                lines.append(f"- {display_name}: {value:.3f}")
        return "\n".join(lines) if lines else "No metrics available"

