"""Alert Engine - Proactive monitoring and alerting system."""
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(Enum):
    DQI = "data_quality"
    SAFETY = "safety"
    QUERY = "query"
    ENROLLMENT = "enrollment"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"


@dataclass
class Alert:
    """Individual alert with full context."""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    category: AlertCategory
    
    entity_type: str
    entity_id: str
    
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    
    recommended_action: str = ""
    impact_description: str = ""
    related_entities: List[str] = field(default_factory=list)
    
    llm_analysis: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "recommended_action": self.recommended_action,
            "impact_description": self.impact_description,
            "llm_analysis": self.llm_analysis
        }


class AlertEngine:
    """
    Enterprise Alert Engine with ML-enhanced detection.
    
    Features:
    - Rule-based threshold monitoring
    - Anomaly detection integration
    - LLM-powered severity assessment
    - Multi-channel notification
    """
    
    def __init__(self, graph: nx.DiGraph, llm=None, dqi_calculator=None):
        self.graph = graph
        self.llm = llm
        self.dqi_calculator = dqi_calculator
        self._alert_counter = 0
        self._init_llm()
    
    def _init_llm(self):
        if self.llm is None:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="qwen/qwen3-32b",
                    temperature=0.2,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
            except Exception:
                self.llm = None
    
    def _generate_alert_id(self) -> str:
        self._alert_counter += 1
        return f"ALT-{datetime.now().strftime('%Y%m%d')}-{self._alert_counter:04d}"
    
    def scan_all(self) -> List[Alert]:
        """Scan all entities and generate alerts."""
        alerts = []
        
        alerts.extend(self.scan_sites())
        alerts.extend(self.scan_safety())
        alerts.extend(self.scan_queries())
        alerts.extend(self.scan_dqi())
        
        alerts = self._deduplicate_alerts(alerts)
        alerts = self._prioritize_alerts(alerts)
        
        if self.llm:
            for alert in alerts[:10]:
                alert.llm_analysis = self._generate_llm_analysis(alert)
        
        return alerts
    
    def scan_sites(self) -> List[Alert]:
        """Scan sites for performance issues."""
        alerts = []
        
        sites = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "Site"]
        
        for site_node in sites:
            props = dict(self.graph.nodes[site_node])
            site_id = props.get("site_id", site_node.replace("SITE:", ""))
            
            open_issues = int(props.get("open_issues", props.get("total_issues", 0)))
            if open_issues > 50:
                alerts.append(Alert(
                    id=self._generate_alert_id(),
                    title=f"High Issue Count at Site {site_id}",
                    description=f"Site {site_id} has {open_issues} open issues, exceeding threshold of 50",
                    severity=AlertSeverity.HIGH if open_issues > 100 else AlertSeverity.MEDIUM,
                    category=AlertCategory.DQI,
                    entity_type="site",
                    entity_id=site_id,
                    metric_name="open_issues",
                    metric_value=open_issues,
                    threshold=50,
                    recommended_action="Review and prioritize issue resolution",
                    impact_description=f"May delay data lock and submission"
                ))
            
            subjects = self._get_related_nodes(site_node, "Subject")
            total_subjects = len(subjects)
            if total_subjects > 0:
                subjects_with_issues = sum(
                    1 for s in subjects
                    if int(self.graph.nodes.get(s, {}).get("open_issue_count", 0)) > 0
                )
                issue_rate = subjects_with_issues / total_subjects
                
                if issue_rate > 0.5:
                    alerts.append(Alert(
                        id=self._generate_alert_id(),
                        title=f"Widespread Issues at Site {site_id}",
                        description=f"{issue_rate*100:.0f}% of subjects at Site {site_id} have open issues",
                        severity=AlertSeverity.HIGH,
                        category=AlertCategory.PERFORMANCE,
                        entity_type="site",
                        entity_id=site_id,
                        metric_name="issue_rate",
                        metric_value=issue_rate,
                        threshold=0.5,
                        recommended_action="Schedule site monitoring visit",
                        impact_description="Indicates systemic data quality problems"
                    ))
        
        return alerts
    
    def scan_safety(self) -> List[Alert]:
        """Scan for safety-related issues."""
        alerts = []
        
        safety_nodes = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == "SafetyDiscrepancy"
        ]
        
        pending_reviews = [
            n for n in safety_nodes
            if self.graph.nodes[n].get("review_status", "").lower() == "pending"
        ]
        
        if len(pending_reviews) > 10:
            alerts.append(Alert(
                id=self._generate_alert_id(),
                title="High Volume of Pending Safety Reviews",
                description=f"{len(pending_reviews)} safety discrepancies awaiting review",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.SAFETY,
                entity_type="study",
                entity_id="all",
                metric_name="pending_safety_reviews",
                metric_value=len(pending_reviews),
                threshold=10,
                recommended_action="Expedite safety review process",
                impact_description="Regulatory compliance risk"
            ))
        
        for safety_node in pending_reviews[:20]:
            props = dict(self.graph.nodes[safety_node])
            discrepancy_id = props.get("discrepancy_id", safety_node)
            
            related_subjects = self._get_related_nodes(safety_node, "Subject")
            subject_id = related_subjects[0] if related_subjects else "Unknown"
            
            alerts.append(Alert(
                id=self._generate_alert_id(),
                title=f"Pending Safety Review: {discrepancy_id}",
                description=f"Safety discrepancy {discrepancy_id} for subject {subject_id} requires review",
                severity=AlertSeverity.HIGH,
                category=AlertCategory.SAFETY,
                entity_type="safety_discrepancy",
                entity_id=discrepancy_id,
                recommended_action="Complete safety review",
                related_entities=[subject_id] if subject_id != "Unknown" else []
            ))
        
        return alerts
    
    def scan_queries(self) -> List[Alert]:
        """Scan for aged open queries."""
        alerts = []
        
        subjects = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "Subject"]
        
        aged_query_subjects = []
        for subj in subjects:
            props = self.graph.nodes[subj]
            max_query_age = float(props.get("max_query_age_days", 0))
            if max_query_age > 7:
                aged_query_subjects.append((subj, max_query_age))
        
        if len(aged_query_subjects) > 20:
            alerts.append(Alert(
                id=self._generate_alert_id(),
                title="High Volume of Aged Queries",
                description=f"{len(aged_query_subjects)} subjects have queries older than 7 days",
                severity=AlertSeverity.MEDIUM,
                category=AlertCategory.QUERY,
                entity_type="study",
                entity_id="all",
                metric_name="aged_query_count",
                metric_value=len(aged_query_subjects),
                threshold=20,
                recommended_action="Prioritize query resolution",
                impact_description="May delay data cleaning timeline"
            ))
        
        return alerts
    
    def scan_dqi(self) -> List[Alert]:
        """Scan DQI scores for threshold breaches."""
        alerts = []
        
        if not self.dqi_calculator:
            return alerts
        
        from intelligence.dqi import EntityType
        
        sites = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "Site"]
        
        for site_node in sites[:50]:
            site_id = site_node.replace("SITE:", "")
            try:
                dqi_result = self.dqi_calculator.calculate_site(site_id)
                
                if dqi_result.score < 50:
                    alerts.append(Alert(
                        id=self._generate_alert_id(),
                        title=f"Critical DQI: Site {site_id}",
                        description=f"Site {site_id} DQI score is {dqi_result.score:.0f}/100 (Grade {dqi_result.grade})",
                        severity=AlertSeverity.CRITICAL if dqi_result.score < 30 else AlertSeverity.HIGH,
                        category=AlertCategory.DQI,
                        entity_type="site",
                        entity_id=site_id,
                        metric_name="dqi_score",
                        metric_value=dqi_result.score,
                        threshold=50,
                        recommended_action="; ".join(dqi_result.recommendations[:2]) if dqi_result.recommendations else "Review data quality",
                        impact_description=f"Top issues: {', '.join(dqi_result.top_issues[:2])}"
                    ))
            except Exception:
                continue
        
        return alerts
    
    def _get_related_nodes(self, node_id: str, target_type: str) -> List[str]:
        related = []
        if not self.graph.has_node(node_id):
            return related
        
        for neighbor in list(self.graph.successors(node_id)) + list(self.graph.predecessors(node_id)):
            if self.graph.nodes.get(neighbor, {}).get("node_type") == target_type:
                related.append(neighbor)
        
        return related
    
    def _deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]:
        seen = set()
        unique = []
        for alert in alerts:
            key = (alert.entity_type, alert.entity_id, alert.category.value)
            if key not in seen:
                seen.add(key)
                unique.append(alert)
        return unique
    
    def _prioritize_alerts(self, alerts: List[Alert]) -> List[Alert]:
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        return sorted(alerts, key=lambda a: severity_order[a.severity])
    
    def _generate_llm_analysis(self, alert: Alert) -> str:
        if not self.llm:
            return ""
        
        prompt = f"""Analyze this clinical trial alert and provide a brief (2-3 sentence) expert assessment:

Alert: {alert.title}
Description: {alert.description}
Severity: {alert.severity.value}
Category: {alert.category.value}
Entity: {alert.entity_type} {alert.entity_id}

Include:
1. Why this matters for clinical trial operations
2. Potential root causes
3. Urgency of action"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return ""
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        all_alerts = self.scan_all()
        return [a for a in all_alerts if a.severity == severity]
    
    def get_alerts_for_entity(self, entity_type: str, entity_id: str) -> List[Alert]:
        all_alerts = self.scan_all()
        return [a for a in all_alerts if a.entity_type == entity_type and a.entity_id == entity_id]
    
    def get_summary(self) -> Dict[str, Any]:
        alerts = self.scan_all()
        
        by_severity = {}
        for severity in AlertSeverity:
            count = len([a for a in alerts if a.severity == severity])
            if count > 0:
                by_severity[severity.value] = count
        
        by_category = {}
        for category in AlertCategory:
            count = len([a for a in alerts if a.category == category])
            if count > 0:
                by_category[category.value] = count
        
        return {
            "total_alerts": len(alerts),
            "by_severity": by_severity,
            "by_category": by_category,
            "top_alerts": [a.to_dict() for a in alerts[:5]]
        }
