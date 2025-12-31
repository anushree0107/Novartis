
from typing import Dict, List, Optional, Union
from pathlib import Path

from .models import (
    EntityType,
    MetricScore,
    MetricStatus,
    DQIResult,
    DQIConfig,
    TrendInfo
)
from .feature_extractor import DQIFeatureExtractor
from .rule_engine import RuleBasedScorer
from .statistical_scorer import StatisticalScorer
from .llm_validator import DQIValidator
from .weights import DQIWeights


class DQICalculator:
    
    # Grade thresholds
    GRADE_THRESHOLDS = {"A": 90, "B": 75, "C": 60, "D": 45, "F": 0}
    
    def __init__(
        self,
        feature_extractor: DQIFeatureExtractor = None,
        rule_scorer: RuleBasedScorer = None,
        stat_scorer: StatisticalScorer = None,
        weights: DQIWeights = None,
        config: DQIConfig = None,
        data_dir: str = "processed_data",
        model_dir: str = "models/dqi"
    ):
        self.config = config or DQIConfig()
        self.data_dir = data_dir
        self.model_dir = model_dir
        
        # Initialize components
        self.feature_extractor = feature_extractor or DQIFeatureExtractor(data_dir)
        self.rule_scorer = rule_scorer or RuleBasedScorer()
        self.weights = weights or self._load_weights()
        
        # Initialize statistical scorer - needs baselines
        if stat_scorer:
            self.stat_scorer = stat_scorer
        else:
            self.stat_scorer = self._init_stat_scorer()
    
    def _load_weights(self) -> DQIWeights:
        weights_path = Path(self.model_dir) / "weights.json"
        if weights_path.exists():
            return DQIWeights.from_file(str(weights_path))
        return DQIWeights()
    
    def _init_stat_scorer(self) -> StatisticalScorer:
        baselines_path = Path(self.model_dir) / "baselines.json"
        if baselines_path.exists():
            return StatisticalScorer(baselines_path=str(baselines_path))
        
        # Compute baselines from current data
        all_features = self.feature_extractor.extract_all_sites()
        if not all_features.empty:
            return StatisticalScorer.from_dataframe(all_features)
        
        return StatisticalScorer()
    
    def calculate(
        self,
        entity_id: str,
        entity_type: EntityType
    ) -> DQIResult:
        # Extract features
        if entity_type == EntityType.SITE:
            features = self.feature_extractor.extract_site_features(entity_id)
        elif entity_type == EntityType.PATIENT:
            features = self.feature_extractor.extract_patient_features(entity_id)
        elif entity_type == EntityType.STUDY:
            features = self.feature_extractor.extract_study_features(entity_id)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Get weights and directions
        metric_weights = self.weights.get_all_weights()
        directions = self.weights.get_all_directions()
        
        # Score based on mode
        mode = self.config.mode
        
        if mode == "rules":
            breakdown = self._score_with_rules(features, metric_weights)
        elif mode == "statistical":
            breakdown = self._score_with_stats(features, metric_weights, directions)
        else:  # hybrid
            breakdown = self._score_hybrid(features, metric_weights, directions)
        
        # Apply critical multipliers
        breakdown = self._apply_critical_multipliers(breakdown)
        
        # Compute final score
        score = self._compute_score(breakdown)
        grade = self._compute_grade(score)
        status = self._compute_status(score, breakdown)
        
        # Identify top issues
        top_issues = self._identify_top_issues(breakdown)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(breakdown)
        
        # Compute population percentile
        population_percentile = self._compute_population_percentile(score)
        
        return DQIResult(
            entity_id=entity_id,
            entity_type=entity_type,
            score=score,
            grade=grade,
            status=status,
            breakdown=breakdown,
            trend=TrendInfo(direction="stable", change_percent=0.0, period="7 days"),
            recommendations=recommendations,
            top_issues=top_issues,
            population_percentile=population_percentile
        )
    
    def calculate_site(self, site_id: str) -> DQIResult:
        return self.calculate(site_id, EntityType.SITE)
    
    def calculate_patient(self, patient_id: str) -> DQIResult:
        return self.calculate(patient_id, EntityType.PATIENT)
    
    def calculate_study(self, study_id: str) -> DQIResult:
        return self.calculate(study_id, EntityType.STUDY)
    
    def calculate_batch(
        self,
        entity_ids: List[str],
        entity_type: EntityType
    ) -> List[DQIResult]:
        return [self.calculate(eid, entity_type) for eid in entity_ids]
    
    def calculate_all_sites(self) -> List[DQIResult]:
        all_features = self.feature_extractor.extract_all_sites()
        site_ids = all_features.index.tolist()
        return self.calculate_batch(site_ids, EntityType.SITE)
    
    def _score_with_rules(
        self,
        features: Dict[str, float],
        weights: Dict[str, float]
    ) -> List[MetricScore]:
        return self.rule_scorer.score_all(features, weights)
    
    def _score_with_stats(
        self,
        features: Dict[str, float],
        weights: Dict[str, float],
        directions: Dict[str, str]
    ) -> List[MetricScore]:
        return self.stat_scorer.score_all(features, weights, directions)
    
    def _score_hybrid(
        self,
        features: Dict[str, float],
        weights: Dict[str, float],
        directions: Dict[str, str]
    ) -> List[MetricScore]:
        rule_scores = self._score_with_rules(features, weights)
        stat_scores = self._score_with_stats(features, weights, directions)
        
        # Combine scores
        rule_weight = self.config.rule_weight
        stat_weight = self.config.stat_weight
        
        combined = []
        for rule_s, stat_s in zip(rule_scores, stat_scores):
            # Weighted average of normalized values
            combined_normalized = (
                rule_s.normalized_value * rule_weight +
                stat_s.normalized_value * stat_weight
            )
            
            # Use rule-based status (more interpretable)
            status = rule_s.status
            
            # Compute combined contribution
            contribution = combined_normalized * rule_s.weight * 100
            
            combined.append(MetricScore(
                name=rule_s.name,
                raw_value=rule_s.raw_value,
                normalized_value=combined_normalized,
                weight=rule_s.weight,
                contribution=contribution,
                status=status,
                z_score=stat_s.z_score,
                percentile=stat_s.percentile
            ))
        
        return combined
    
    def _apply_critical_multipliers(
        self,
        breakdown: List[MetricScore]
    ) -> List[MetricScore]:
        adjusted = []
        
        for score in breakdown:
            if score.status == MetricStatus.CRITICAL:
                multiplier = self.weights.get_critical_multiplier(score.name)
                new_weight = score.weight * multiplier
                new_contribution = score.normalized_value * new_weight * 100
                
                adjusted.append(MetricScore(
                    name=score.name,
                    raw_value=score.raw_value,
                    normalized_value=score.normalized_value,
                    weight=new_weight,
                    contribution=new_contribution,
                    status=score.status,
                    z_score=score.z_score,
                    percentile=score.percentile
                ))
            else:
                adjusted.append(score)
        
        return adjusted
    
    def _compute_score(self, breakdown: List[MetricScore]) -> float:
        total_contribution = sum(m.contribution for m in breakdown)
        total_weight = sum(m.weight for m in breakdown)
        
        if total_weight == 0:
            return 50.0
        
        return min(100.0, max(0.0, total_contribution / total_weight))
    
    def _compute_grade(self, score: float) -> str:
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"
    
    def _compute_status(
        self,
        score: float,
        breakdown: List[MetricScore]
    ) -> str:
        critical_count = sum(1 for m in breakdown if m.status == MetricStatus.CRITICAL)
        
        ready_threshold = self.config.ready_threshold
        at_risk_threshold = self.config.at_risk_threshold
        
        if score >= ready_threshold and critical_count == 0:
            return "Ready"
        elif score >= at_risk_threshold and critical_count <= 1:
            return "At Risk"
        return "Critical"
    
    def _identify_top_issues(
        self,
        breakdown: List[MetricScore],
        max_issues: int = 5
    ) -> List[str]:
        # Sort by status priority (critical > warning > good)
        status_priority = {
            MetricStatus.CRITICAL: 0,
            MetricStatus.WARNING: 1,
            MetricStatus.GOOD: 2
        }
        
        sorted_metrics = sorted(
            breakdown,
            key=lambda x: (status_priority.get(x.status, 2), -x.weight)
        )
        
        issues = []
        for m in sorted_metrics[:max_issues]:
            if m.status != MetricStatus.GOOD:
                issue = f"{m.name.replace('_', ' ').title()}: {m.raw_value:.3f} ({m.status.value})"
                issues.append(issue)
        
        return issues
    
    def _generate_recommendations(
        self,
        breakdown: List[MetricScore],
        max_recs: int = 3
    ) -> List[str]:
        recommendations = []
        
        # Recommendation templates
        templates = {
            "missing_visits_pct": "Follow up on {count} overdue visits to improve visit compliance",
            "missing_pages_pct": "Resolve missing CRF pages to ensure complete data collection",
            "open_issues_per_subject": "Address open data queries to reduce issue backlog",
            "safety_pending_pct": "URGENT: Clear pending safety reviews immediately",
            "meddra_coding_rate": "Complete MedDRA coding for uncoded adverse events",
            "whodd_coding_rate": "Complete WHODD coding for uncoded medications",
            "days_outstanding_avg": "Reduce visit delays through proactive site follow-up",
            "days_pages_missing_avg": "Expedite resolution of aged missing pages",
        }
        
        # Generate recommendations for critical/warning metrics
        for m in sorted(breakdown, key=lambda x: x.contribution):
            if m.status in [MetricStatus.CRITICAL, MetricStatus.WARNING]:
                template = templates.get(m.name)
                if template:
                    recommendations.append(template.format(count=int(m.raw_value * 100)))
        
        return recommendations[:max_recs]
    
    def _compute_population_percentile(self, score: float) -> Optional[float]:
        # Avoid recursion and expensive computation
        # In production, this would use precomputed score distributions
        return None
    
    @classmethod
    def from_config(cls, config_path: str) -> "DQICalculator":
        import json
        
        with open(config_path, "r") as f:
            config_data = json.load(f)
        
        config = DQIConfig(
            mode=config_data.get("mode", "hybrid"),
            weights_path=config_data.get("weights_path"),
            thresholds_path=config_data.get("thresholds_path"),
            baselines_path=config_data.get("baselines_path"),
            rule_weight=config_data.get("rule_weight", 0.6),
            stat_weight=config_data.get("stat_weight", 0.4),
        )
        
        return cls(
            config=config,
            data_dir=config_data.get("data_dir", "processed_data"),
            model_dir=config_data.get("model_dir", "models/dqi")
        )
    
    def save_baselines(self, path: str = None):
        if path is None:
            path = str(Path(self.model_dir) / "baselines.json")
        self.stat_scorer.save_baselines(path)
    
    def save_weights(self, path: str = None):
        if path is None:
            path = str(Path(self.model_dir) / "weights.json")
        self.weights.save(path)

    def validate_result(self, result: DQIResult) -> str:
        validator = DQIValidator()
        thresholds = self.rule_scorer.export_thresholds()
        return validator.validate(result, thresholds)


