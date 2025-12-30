"""Rule Engine - Configurable alert rules and thresholds."""
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class RuleOperator(Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    IN_RANGE = "in_range"


@dataclass
class AlertRule:
    """Configurable alert rule definition."""
    id: str
    name: str
    description: str
    
    entity_type: str
    metric_name: str
    operator: RuleOperator
    threshold: Any
    
    severity: str = "medium"
    category: str = "data_quality"
    
    enabled: bool = True
    cooldown_minutes: int = 60
    
    custom_message: Optional[str] = None
    recommended_action: Optional[str] = None
    
    def evaluate(self, value: Any) -> bool:
        if not self.enabled:
            return False
        
        operators = {
            RuleOperator.GREATER_THAN: lambda v, t: v > t,
            RuleOperator.LESS_THAN: lambda v, t: v < t,
            RuleOperator.EQUALS: lambda v, t: v == t,
            RuleOperator.NOT_EQUALS: lambda v, t: v != t,
            RuleOperator.GREATER_THAN_OR_EQUAL: lambda v, t: v >= t,
            RuleOperator.LESS_THAN_OR_EQUAL: lambda v, t: v <= t,
            RuleOperator.CONTAINS: lambda v, t: t in str(v),
            RuleOperator.IN_RANGE: lambda v, t: t[0] <= v <= t[1] if isinstance(t, (list, tuple)) else False,
        }
        
        op_func = operators.get(self.operator)
        if op_func:
            try:
                return op_func(value, self.threshold)
            except (TypeError, ValueError):
                return False
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "entity_type": self.entity_type,
            "metric_name": self.metric_name,
            "operator": self.operator.value,
            "threshold": self.threshold,
            "severity": self.severity,
            "category": self.category,
            "enabled": self.enabled
        }


class RuleEngine:
    """
    Configurable Rule Engine for alert generation.
    
    Features:
    - YAML/JSON rule configuration
    - Dynamic rule loading
    - Rule templates
    - Cooldown management
    """
    
    DEFAULT_RULES = [
        AlertRule(
            id="dqi_critical",
            name="Critical DQI Score",
            description="DQI score below critical threshold",
            entity_type="site",
            metric_name="dqi_score",
            operator=RuleOperator.LESS_THAN,
            threshold=40,
            severity="critical",
            category="data_quality",
            recommended_action="Immediate site review required"
        ),
        AlertRule(
            id="dqi_warning",
            name="Low DQI Score",
            description="DQI score below warning threshold",
            entity_type="site",
            metric_name="dqi_score",
            operator=RuleOperator.LESS_THAN,
            threshold=60,
            severity="medium",
            category="data_quality"
        ),
        AlertRule(
            id="open_issues_high",
            name="High Open Issues",
            description="Site has excessive open issues",
            entity_type="site",
            metric_name="open_issues",
            operator=RuleOperator.GREATER_THAN,
            threshold=50,
            severity="high",
            category="data_quality"
        ),
        AlertRule(
            id="safety_pending",
            name="Pending Safety Reviews",
            description="Safety discrepancies awaiting review",
            entity_type="study",
            metric_name="pending_safety_reviews",
            operator=RuleOperator.GREATER_THAN,
            threshold=5,
            severity="critical",
            category="safety"
        ),
        AlertRule(
            id="query_aging",
            name="Aged Queries",
            description="Queries older than threshold",
            entity_type="subject",
            metric_name="max_query_age_days",
            operator=RuleOperator.GREATER_THAN,
            threshold=7,
            severity="medium",
            category="query"
        ),
        AlertRule(
            id="missing_visits_high",
            name="High Missing Visits",
            description="Missing visit rate exceeds threshold",
            entity_type="site",
            metric_name="missing_visits_pct",
            operator=RuleOperator.GREATER_THAN,
            threshold=0.15,
            severity="high",
            category="data_quality"
        ),
        AlertRule(
            id="sdv_incomplete",
            name="Low SDV Completion",
            description="SDV completion below threshold",
            entity_type="site",
            metric_name="sdv_completion_pct",
            operator=RuleOperator.LESS_THAN,
            threshold=0.75,
            severity="medium",
            category="compliance"
        ),
        AlertRule(
            id="enrollment_stalled",
            name="Stalled Enrollment",
            description="No new enrollments in threshold period",
            entity_type="site",
            metric_name="days_since_last_enrollment",
            operator=RuleOperator.GREATER_THAN,
            threshold=30,
            severity="low",
            category="enrollment"
        ),
    ]
    
    def __init__(self, rules: List[AlertRule] = None):
        self.rules = rules or self.DEFAULT_RULES.copy()
        self._cooldowns: Dict[str, float] = {}
    
    def add_rule(self, rule: AlertRule):
        existing = next((r for r in self.rules if r.id == rule.id), None)
        if existing:
            self.rules.remove(existing)
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def enable_rule(self, rule_id: str):
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = True
                break
    
    def disable_rule(self, rule_id: str):
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = False
                break
    
    def get_rules_for_entity(self, entity_type: str) -> List[AlertRule]:
        return [r for r in self.rules if r.entity_type == entity_type and r.enabled]
    
    def get_rules_by_category(self, category: str) -> List[AlertRule]:
        return [r for r in self.rules if r.category == category and r.enabled]
    
    def evaluate_all(self, entity_type: str, metrics: Dict[str, Any]) -> List[AlertRule]:
        triggered = []
        
        for rule in self.get_rules_for_entity(entity_type):
            if rule.metric_name in metrics:
                value = metrics[rule.metric_name]
                if rule.evaluate(value):
                    triggered.append(rule)
        
        return triggered
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.rules]
    
    def load_rules_from_config(self, config: Dict[str, Any]):
        if "rules" in config:
            for rule_config in config["rules"]:
                rule = AlertRule(
                    id=rule_config["id"],
                    name=rule_config["name"],
                    description=rule_config.get("description", ""),
                    entity_type=rule_config["entity_type"],
                    metric_name=rule_config["metric_name"],
                    operator=RuleOperator(rule_config["operator"]),
                    threshold=rule_config["threshold"],
                    severity=rule_config.get("severity", "medium"),
                    category=rule_config.get("category", "data_quality"),
                    enabled=rule_config.get("enabled", True)
                )
                self.add_rule(rule)
