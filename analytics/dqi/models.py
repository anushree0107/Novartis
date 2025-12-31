
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class EntityType(Enum):
    SITE = "site"
    PATIENT = "patient"
    STUDY = "study"


class MetricStatus(Enum):
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricScore:
    name: str
    raw_value: float
    normalized_value: float  # 0-1 scale (1 = best)
    weight: float
    contribution: float  # Weighted contribution to final score
    status: MetricStatus
    z_score: Optional[float] = None
    percentile: Optional[float] = None
    
    @property
    def impact_description(self) -> str:
        status_emoji = {
            MetricStatus.GOOD: "✅",
            MetricStatus.WARNING: "⚠️",
            MetricStatus.CRITICAL: "🔴"
        }
        emoji = status_emoji.get(self.status, "")
        return f"{emoji} {self.name}: {self.raw_value:.2f} ({self.status.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "raw_value": round(self.raw_value, 4),
            "normalized_value": round(self.normalized_value, 4),
            "weight": round(self.weight, 4),
            "contribution": round(self.contribution, 4),
            "status": self.status.value,
            "z_score": round(self.z_score, 2) if self.z_score else None,
            "percentile": round(self.percentile, 2) if self.percentile else None,
        }


@dataclass
class TrendInfo:
    direction: str  # "improving", "declining", "stable"
    change_percent: float
    period: str  # e.g., "7 days", "30 days"


@dataclass
class DQIResult:
    entity_id: str
    entity_type: EntityType
    score: float  # 0-100
    grade: str  # A, B, C, D, F
    status: str  # "Ready", "At Risk", "Critical"
    
    breakdown: List[MetricScore] = field(default_factory=list)
    trend: Optional[TrendInfo] = None
    recommendations: List[str] = field(default_factory=list)
    top_issues: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    
    # Statistical context
    population_percentile: Optional[float] = None
    comparison_to_peers: Optional[Dict[str, float]] = None
    
    @property
    def is_clean(self) -> bool:
        return (
            self.score >= 90 and 
            all(m.status != MetricStatus.CRITICAL for m in self.breakdown)
        )
    
    @property
    def critical_count(self) -> int:
        return sum(1 for m in self.breakdown if m.status == MetricStatus.CRITICAL)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for m in self.breakdown if m.status == MetricStatus.WARNING)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "score": round(self.score, 2),
            "grade": self.grade,
            "status": self.status,
            "is_clean": self.is_clean,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "breakdown": [m.to_dict() for m in self.breakdown],
            "trend": {
                "direction": self.trend.direction,
                "change_percent": self.trend.change_percent,
                "period": self.trend.period
            } if self.trend else None,
            "recommendations": self.recommendations,
            "top_issues": self.top_issues,
            "population_percentile": self.population_percentile,
        }
    
    def summary(self) -> str:
        lines = [
            f"DQI Report: {self.entity_id} ({self.entity_type.value})",
            f"{'='*50}",
            f"Score: {self.score:.1f}/100 (Grade: {self.grade})",
            f"Status: {self.status}",
            f"Clean: {'Yes ✅' if self.is_clean else 'No ❌'}",
            "",
            "Metric Breakdown:",
        ]
        
        for m in sorted(self.breakdown, key=lambda x: x.contribution):
            lines.append(f"  {m.impact_description}")
        
        if self.top_issues:
            lines.append("")
            lines.append("Top Issues:")
            for issue in self.top_issues[:3]:
                lines.append(f"  • {issue}")
        
        return "\n".join(lines)


@dataclass
class DQIConfig:
    mode: str = "hybrid"  # "rules", "statistical", "hybrid"
    weights_path: Optional[str] = None
    thresholds_path: Optional[str] = None
    baselines_path: Optional[str] = None
    
    # Weight for combining rule vs statistical scores in hybrid mode
    rule_weight: float = 0.6
    stat_weight: float = 0.4
    
    # Grade thresholds
    grade_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "A": 90, "B": 75, "C": 60, "D": 45, "F": 0
    })
    
    # Status thresholds
    ready_threshold: float = 85
    at_risk_threshold: float = 60
