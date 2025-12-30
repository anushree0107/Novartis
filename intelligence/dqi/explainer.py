"""DQI Explainer - LLM-Enhanced explanations for Data Quality Index."""
import os
from typing import List, Dict, Optional
from dataclasses import dataclass


DQI_EXPLANATION_PROMPT = """You are a clinical data quality expert. Analyze this Data Quality Index (DQI) result and provide:

1. A 2-3 sentence executive summary of the data quality status
2. Key risk factors that need immediate attention
3. Specific, actionable recommendations prioritized by impact

Entity: {entity_type} - {entity_id}
DQI Score: {score}/100 (Grade: {grade}, Status: {status})

Metric Breakdown:
{breakdown}

Top Issues:
{top_issues}

Provide a clear, professional analysis that a Clinical Research Associate could act on immediately."""


RECOMMENDATION_PROMPT = """Based on this DQI analysis, generate 3-5 specific, actionable recommendations:

Entity: {entity_type} {entity_id}
Score: {score}/100
Status: {status}

Critical Issues:
{critical_issues}

Warning Issues:
{warning_issues}

For each recommendation:
1. State the specific action
2. Explain why it's important
3. Estimate impact on DQI score

Format as a numbered list."""


class DQIExplainer:
    """
    LLM-Enhanced DQI Explainer.
    
    Provides:
    - Natural language explanations of DQI scores
    - Prioritized recommendations
    - Risk narratives
    - Peer comparisons in context
    """
    
    def __init__(self, llm=None):
        self.llm = llm
        self._init_llm()
    
    def _init_llm(self):
        if self.llm is None:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=0.3,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
            except Exception as e:
                print(f"⚠️ LLM init failed: {e}")
                self.llm = None
    
    def explain(self, dqi_result) -> str:
        """Generate LLM-powered explanation for DQI result."""
        if not self.llm:
            return self._fallback_explanation(dqi_result)
        
        breakdown_text = self._format_breakdown(dqi_result.breakdown)
        issues_text = "\n".join(f"- {issue}" for issue in dqi_result.top_issues)
        
        prompt = DQI_EXPLANATION_PROMPT.format(
            entity_type=dqi_result.entity_type.value.title(),
            entity_id=dqi_result.entity_id,
            score=f"{dqi_result.score:.1f}",
            grade=dqi_result.grade,
            status=dqi_result.status,
            breakdown=breakdown_text,
            top_issues=issues_text or "No critical issues"
        )
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return self._fallback_explanation(dqi_result)
    
    def generate_recommendations(self, dqi_result) -> List[str]:
        """Generate prioritized recommendations using LLM."""
        if not self.llm:
            return self._fallback_recommendations(dqi_result)
        
        critical = [m for m in dqi_result.breakdown if m.status == "critical"]
        warning = [m for m in dqi_result.breakdown if m.status == "warning"]
        
        prompt = RECOMMENDATION_PROMPT.format(
            entity_type=dqi_result.entity_type.value.title(),
            entity_id=dqi_result.entity_id,
            score=f"{dqi_result.score:.1f}",
            status=dqi_result.status,
            critical_issues=self._format_issues(critical) or "None",
            warning_issues=self._format_issues(warning) or "None"
        )
        
        try:
            response = self.llm.invoke(prompt)
            return self._parse_recommendations(response.content)
        except Exception as e:
            return self._fallback_recommendations(dqi_result)
    
    def generate_risk_narrative(self, dqi_result, historical_data: Dict = None) -> str:
        """Generate a risk narrative considering historical context."""
        if not self.llm:
            return self._fallback_risk_narrative(dqi_result)
        
        trend_context = ""
        if dqi_result.trend:
            trend_context = f"Trend: {dqi_result.trend.direction} ({dqi_result.trend.change_percent:+.1f}% over {dqi_result.trend.period})"
        
        prompt = f"""Generate a 2-3 sentence risk narrative for this clinical trial entity:

Entity: {dqi_result.entity_type.value.title()} {dqi_result.entity_id}
DQI Score: {dqi_result.score:.1f}/100
Status: {dqi_result.status}
{trend_context}

Key Issues: {', '.join(dqi_result.top_issues[:3]) if dqi_result.top_issues else 'None critical'}

Focus on:
1. The overall risk level
2. Most impactful issue
3. Urgency of intervention"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return self._fallback_risk_narrative(dqi_result)
    
    def _format_breakdown(self, breakdown) -> str:
        lines = []
        for m in sorted(breakdown, key=lambda x: x.contribution):
            status_icon = {"good": "✓", "warning": "⚠", "critical": "✗"}.get(m.status, "?")
            lines.append(
                f"{status_icon} {m.name.replace('_', ' ').title()}: "
                f"value={m.raw_value:.2f}, contribution={m.contribution:+.1f} pts ({m.status})"
            )
        return "\n".join(lines)
    
    def _format_issues(self, metrics) -> str:
        if not metrics:
            return ""
        return "\n".join(
            f"- {m.name.replace('_', ' ').title()}: {m.raw_value:.2f} ({m.impact_description})"
            for m in metrics
        )
    
    def _parse_recommendations(self, llm_response: str) -> List[str]:
        lines = llm_response.strip().split("\n")
        recommendations = []
        current = ""
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                if current:
                    recommendations.append(current.strip())
                current = line.lstrip("0123456789.-) ").strip()
            elif line and current:
                current += " " + line
        
        if current:
            recommendations.append(current.strip())
        
        return recommendations[:5]
    
    def _fallback_explanation(self, dqi_result) -> str:
        status_desc = {
            "Ready": "meets quality standards and is ready for analysis",
            "At Risk": "has some quality concerns that need attention",
            "Critical": "has significant data quality issues requiring immediate action"
        }
        
        desc = status_desc.get(dqi_result.status, "needs review")
        
        critical_metrics = [m for m in dqi_result.breakdown if m.status == "critical"]
        warning_metrics = [m for m in dqi_result.breakdown if m.status == "warning"]
        
        explanation = f"This {dqi_result.entity_type.value} has a DQI score of {dqi_result.score:.1f}/100 (Grade {dqi_result.grade}) and {desc}. "
        
        if critical_metrics:
            metric_names = [m.name.replace("_", " ") for m in critical_metrics[:2]]
            explanation += f"Critical issues include {', '.join(metric_names)}. "
        
        if warning_metrics and not critical_metrics:
            metric_names = [m.name.replace("_", " ") for m in warning_metrics[:2]]
            explanation += f"Warning areas include {', '.join(metric_names)}. "
        
        return explanation
    
    def _fallback_recommendations(self, dqi_result) -> List[str]:
        recommendations = []
        
        for m in dqi_result.breakdown:
            if m.status == "critical":
                recommendations.append(
                    f"Address {m.name.replace('_', ' ')} immediately - "
                    f"current value ({m.raw_value:.2f}) is in critical range"
                )
            elif m.status == "warning" and len(recommendations) < 3:
                recommendations.append(
                    f"Monitor and improve {m.name.replace('_', ' ')} - "
                    f"value ({m.raw_value:.2f}) approaching threshold"
                )
        
        if not recommendations:
            recommendations.append("Maintain current data quality practices")
        
        return recommendations[:5]
    
    def _fallback_risk_narrative(self, dqi_result) -> str:
        if dqi_result.status == "Critical":
            return f"HIGH RISK: {dqi_result.entity_type.value.title()} {dqi_result.entity_id} requires immediate intervention. Multiple critical data quality issues detected."
        elif dqi_result.status == "At Risk":
            return f"MODERATE RISK: {dqi_result.entity_type.value.title()} {dqi_result.entity_id} has data quality concerns. Proactive monitoring recommended."
        else:
            return f"LOW RISK: {dqi_result.entity_type.value.title()} {dqi_result.entity_id} meets data quality standards. Continue routine monitoring."


def enhance_dqi_result(dqi_result, explainer: DQIExplainer = None) -> None:
    """Enhance a DQI result with LLM-generated explanations."""
    if explainer is None:
        explainer = DQIExplainer()
    
    dqi_result.explanation = explainer.explain(dqi_result)
    dqi_result.recommendations = explainer.generate_recommendations(dqi_result)
