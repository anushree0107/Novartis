import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class ClusterAnalyst:
    def __init__(self):
        self.llm = None
        
    def _ensure_llm(self):
        if self.llm: return
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1, groq_api_key=api_key)

    def analyze_clusters(self, profiles: dict) -> str:
        self._ensure_llm()
        if not self.llm:
            return "LLM not configured."
            
        system_prompt = """You are a Clinical Data Scientist.
Analyze the provided DBSCAN Cluster Profiles.
Cluster -1 represents 'Noise' or 'Outliers'. Other clusters are dense groups.

Profiles:
{profiles}

Tasks:
1. Assign a short descriptive label to each cluster (e.g., "Compliant Sites", "High Pending Safety").
2. Explain the key characteristics defining the cluster (look for high/low stats).
3. Recommend actions for sites in this cluster.

Format as Markdown.
"""
        # Simplify profiles string
        prof_str = json.dumps(profiles, indent=2)
        
        prompt = ChatPromptTemplate.from_template(system_prompt)
        chain = prompt | self.llm
        try:
            return chain.invoke({"profiles": prof_str}).content
        except Exception as e:
            return f"Error: {e}"
