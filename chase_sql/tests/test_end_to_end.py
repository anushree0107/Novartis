"""
End-to-End Tests for CHASE-SQL

Tests the complete pipeline from natural language to SQL.
"""
import pytest
from chase_sql.main import ChaseSQL
from chase_sql.schema_context import SchemaContextBuilder
from chase_sql.config import ChaseConfig, LLMConfig, LLMProvider


class MockLLMClient:
    """Mock LLM client for testing without API calls"""
    
    def __init__(self, config=None):
        self.config = config
        self.responses = {
            "show all subjects": "```sql\nSELECT * FROM subjects;\n```",
            "open queries": "```sql\nSELECT * FROM data_queries WHERE query_status = 'OPEN';\n```",
            "study 1": "```sql\nSELECT * FROM subjects sub JOIN studies st ON sub.study_id = st.study_id WHERE st.study_code = 'Study 1';\n```",
        }
    
    def complete(self, prompt, system_prompt=None):
        prompt_lower = prompt.lower()
        for key, response in self.responses.items():
            if key in prompt_lower:
                return response
        return "```sql\nSELECT 1;\n```"
    
    def extract_sql(self, response):
        import re
        match = re.search(r"```sql\s*([\s\S]*?)\s*```", response, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def extract_json(self, response):
        return {}


class TestEndToEnd:
    """End-to-end pipeline tests"""
    
    @pytest.fixture
    def chase(self):
        """Create ChaseSQL instance with mock LLM"""
        config = ChaseConfig()
        config.execute_for_validation = False  # Don't require database
        
        chase = ChaseSQL(config)
        chase._llm = MockLLMClient()  # Inject mock
        return chase
    
    def test_simple_query(self, chase):
        """Test simple query generation"""
        result = chase.text_to_sql("Show all subjects", refine=False)
        
        assert result.success
        assert result.sql
        assert "SELECT" in result.sql.upper()
        assert "subjects" in result.sql.lower()
    
    def test_filter_query(self, chase):
        """Test query with filter"""
        result = chase.text_to_sql("Show all open queries", refine=False)
        
        assert result.success
        assert result.sql
        assert "data_queries" in result.sql.lower()
        assert "OPEN" in result.sql.upper() or "open" in result.sql.lower()
    
    def test_study_specific_query(self, chase):
        """Test query with study identifier"""
        result = chase.text_to_sql("Show subjects in Study 1", refine=False)
        
        assert result.success
        assert result.sql
        assert "Study 1" in result.sql or "study 1" in result.sql.lower()
    
    def test_linked_schema(self, chase):
        """Test that schema linking provides relevant tables"""
        result = chase.text_to_sql("Show open queries for subjects at Site 18", refine=False)
        
        assert result.linked_schema is not None
        # Should link data_queries, subjects, and sites
        linked_tables = result.linked_schema.tables
        assert "data_queries" in linked_tables or "queries" in str(linked_tables).lower()


class TestSchemaContext:
    """Tests for schema context functionality"""
    
    @pytest.fixture
    def schema_context(self):
        builder = SchemaContextBuilder("/home/anushree/Novartis/database/schema.sql")
        return builder.build_from_file()
    
    def test_prompt_context_generation(self, schema_context):
        """Test that prompt context can be generated"""
        context_str = schema_context.to_prompt_context(
            tables=["studies", "subjects"],
            include_samples=False,
            max_tables=2
        )
        
        assert "studies" in context_str
        assert "subjects" in context_str
        assert "CREATE TABLE" in context_str
    
    def test_related_tables(self, schema_context):
        """Test finding related tables via foreign keys"""
        related = schema_context.get_related_tables("subjects")
        
        assert "studies" in related or len(related) > 0


class TestTrainingData:
    """Tests for training data generation"""
    
    def test_generate_training_examples(self):
        from chase_sql.training.data_generator import TrainingDataGenerator
        
        generator = TrainingDataGenerator()
        examples = generator.generate_all()
        
        assert len(examples) > 0
        
        # Check example structure
        for ex in examples[:5]:
            assert ex.question
            assert ex.sql
            assert ex.tables
            assert ex.complexity in ["simple", "medium", "complex"]


# Sample queries for manual testing
SAMPLE_QUERIES = [
    "Show all studies",
    "How many subjects are enrolled?",
    "List all open queries for Study 1",
    "Show subjects at Site 18",
    "Count open queries per site",
    "Show protocol deviations with status PD_CONFIRMED",
    "List subjects with broken PI signatures",
    "What is the average query age for open queries?",
]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
