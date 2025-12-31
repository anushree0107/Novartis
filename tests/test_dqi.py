
import pytest
import pandas as pd
import numpy as np
from analytics.dqi import (
    DQIFeatureExtractor,
    RuleBasedScorer,
    StatisticalScorer,
    DQIWeights,
    DQICalculator,
    EntityType,
    MetricStatus
)

class TestDQI:
    @pytest.fixture
    def mock_data(self, tmp_path):
        data_dir = tmp_path / "processed_data"
        data_dir.mkdir()
        
        pd.DataFrame({
            "site": ["1", "2"],
            "patient_id": ["P1", "P2"],
            "status": ["pending", "closed"]
        }).to_csv(data_dir / "esae_processed.csv", index=False)
        
        pd.DataFrame({
            "site": ["1", "2"],
            "days_outstanding": [10, 5]
        }).to_csv(data_dir / "visit_projection_processed.csv", index=False)
        
        pd.DataFrame({
            "subject": ["P1", "P2"],
            "issue_count": [5, 0]
        }).to_csv(data_dir / "edrr_processed.csv", index=False)
        
        pd.DataFrame().to_csv(data_dir / "missing_pages_processed.csv")
        pd.DataFrame().to_csv(data_dir / "meddra_processed.csv")
        pd.DataFrame().to_csv(data_dir / "whodd_processed.csv")
        
        return str(data_dir)

    def test_feature_extractor(self, mock_data):
        extractor = DQIFeatureExtractor(data_dir=mock_data)
        features = extractor.extract_site_features("1")
        assert isinstance(features, dict)
        assert "missing_visits_pct" in features
        assert isinstance(features["missing_visits_pct"], float)

        all_sites = extractor.extract_all_sites()
        assert not all_sites.empty
        assert "site_id" not in all_sites.columns 
        assert len(all_sites) == 2

    def test_rule_scorer(self):
        scorer = RuleBasedScorer()
        score = scorer.score_metric("missing_visits_pct", 0.01)
        assert score.status == MetricStatus.GOOD
        assert score.normalized_value == 0.9

        score = scorer.score_metric("missing_visits_pct", 0.25)
        assert score.status == MetricStatus.CRITICAL
        assert score.normalized_value < 0.5

    def test_stat_scorer(self):
        df = pd.DataFrame({
            "m1": [1, 2, 3, 4, 5]
        })
        scorer = StatisticalScorer.from_dataframe(df)
        score = scorer.score_metric("m1", 3) 
        assert score.z_score == 0.0
        assert 40 <= score.percentile <= 60

    def test_calculator(self, mock_data):
        calc = DQICalculator(data_dir=mock_data)
        result = calc.calculate_site("1")
        assert result.entity_id == "1"
        assert 0 <= result.score <= 100
        assert result.grade in ["A", "B", "C", "D", "F"]
        assert len(result.breakdown) > 0
