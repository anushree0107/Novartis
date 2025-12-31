
import os
from typing import Dict, Any, Optional

class DQIValidator:
    def __init__(self, llm=None):
        self.llm = llm
        if not self.llm:
            try:
                from langchain_groq import ChatGroq
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    self.llm = ChatGroq(
                        model="llama-3.3-70b-versatile",
                        temperature=0.1,
                        groq_api_key=api_key
                    )
            except:
                pass

    def _generate_rule_context(self, thresholds: Dict[str, Any]) -> str:
        rules = []
        for metric, conf in thresholds.items():
            direction = conf.get('direction', 'lower_is_better')
            good = conf.get('good')
            critical = conf.get('critical')
            
            desc = f"- {metric}: "
            if direction == 'lower_is_better':
                desc += f"Good if <= {good}, Critical if > {critical}"
            else:
                desc += f"Good if >= {good}, Critical if < {critical}"
            rules.append(desc)
        
        return "\n".join(rules)

    def validate(self, result: Any, thresholds: Dict[str, Any]) -> str:
        if not self.llm:
            return "Validation skipped: No LLM available."

        rule_context = self._generate_rule_context(thresholds)
        
        breakdown_text = []
        for m in result.breakdown:
            breakdown_text.append(
                f"{m.name}: {m.raw_value:.4f} (Status: {m.status.value})"
            )
        
        system_prompt = f"""You are a Data Quality Validation Agent. 
Your task is to VALIDATE the DQI result against the defined rules.

DEFINED RULES:
{rule_context}

RESPONSE FORMAT:
One paragraph validation summary.
Confirm if 'Critical' or 'Warning' statuses match the rules.
Highlight any anomalies.
"""

        user_prompt = f"""
Entity: {result.entity_type.value} {result.entity_id}
Score: {result.score}
Status: {result.status}

METRIC BREAKDOWN:
{chr(10).join(breakdown_text)}
"""

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Validation failed: {str(e)}"
