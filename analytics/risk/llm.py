import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any

class RiskValidator:
    def __init__(self):
        self.llm = None
        
    def _ensure_llm(self):
        if self.llm:
            return
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, groq_api_key=api_key)
            
    def generate_explanation(self, site_id: str, risk_data: Dict[str, Any], pop_stats: Dict[str, Any]) -> str:
        self._ensure_llm()
        if not self.llm:
            return "LLM not configured (missing API key)."
            
        features = risk_data.get("features", {})
        risk_level = risk_data.get("risk_level", "Unknown")
        score = risk_data.get("anomaly_score", 0.0)
        
        system_prompt = """You are a Clinical Trial Risk Analyst.
Analyze the provided Site Risk Data compared to Population Statistics.
Explain WHY this site is flagged (or not flagged) as an anomaly.

Risk Level: {risk_level} (Anomaly Score: {score:.4f})

Site Features:
{features}

Population Stats (Mean/StdDev):
{stats}

Instructions:
1. Identify features that deviate significantly (e.g. > 2 std devs) from the mean.
2. Explain the operational implication (e.g. "High missing visits suggests protocol non-compliance").
3. Be concise and professional.
4. If Risk is Low, explain that metrics are within normal range.
"""
        
        # Format stats for prompt
        stats_summary = ""
        for k, v in pop_stats.items():
            if k in features:
                stats_summary += f"- {k}: Mean={v.get('mean', 0):.2f}, Std={v.get('std', 0):.2f}\n"

        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "risk_level": risk_level,
                "score": score,
                "features": json.dumps(features, indent=2),
                "stats": stats_summary
            })
            return response.content
        except Exception as e:
            return f"Error generating explanation: {e}"
