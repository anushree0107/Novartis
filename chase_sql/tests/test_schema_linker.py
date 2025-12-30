"""
Tests for Schema Linker
"""
import pytest
from chase_sql.schema_context import SchemaContextBuilder, SchemaContext
from chase_sql.schema_linker import SchemaLinker, LinkedSchema


class TestSchemaContextBuilder:
    """Tests for schema context building"""
    
    @pytest.fixture
    def schema_path(self):
        return "/home/anushree/Novartis/database/schema.sql"
    
    def test_build_from_file(self, schema_path):
        """Test that schema can be parsed from SQL file"""
        builder = SchemaContextBuilder(schema_path)
        context = builder.build_from_file()
        
        assert context is not None
        assert len(context.tables) > 0
        assert "studies" in context.tables
        assert "subjects" in context.tables
        assert "data_queries" in context.tables
    
    def test_table_columns(self, schema_path):
        """Test that columns are correctly parsed"""
        builder = SchemaContextBuilder(schema_path)
        context = builder.build_from_file()
        
        studies_table = context.get_table("studies")
        assert studies_table is not None
        assert len(studies_table.columns) > 0
        
        # Check for expected columns
        col_names = [c.name for c in studies_table.columns]
        assert "study_id" in col_names
        assert "study_code" in col_names
    
    def test_foreign_keys(self, schema_path):
        """Test that foreign keys are detected"""
        builder = SchemaContextBuilder(schema_path)
        context = builder.build_from_file()
        
        assert len(context.foreign_keys) > 0
        
        # Check sites -> studies FK
        fk = next((fk for fk in context.foreign_keys 
                   if fk['source_table'] == 'sites' and fk['target_table'] == 'studies'), None)
        assert fk is not None
    
    def test_enum_types(self, schema_path):
        """Test that enum types are parsed"""
        builder = SchemaContextBuilder(schema_path)
        context = builder.build_from_file()
        
        assert len(context.enum_types) > 0
        assert "study_status" in context.enum_types
        assert "ACTIVE" in context.enum_types["study_status"]


class TestSchemaLinker:
    """Tests for schema linking"""
    
    @pytest.fixture
    def schema_context(self):
        builder = SchemaContextBuilder("/home/anushree/Novartis/database/schema.sql")
        return builder.build_from_file()
    
    def test_simple_query_linking(self, schema_context):
        """Test linking for simple query"""
        # Use a mock LLM client for testing
        class MockLLMClient:
            def complete(self, prompt, system_prompt=None):
                return '{"tables_needed": [], "reasoning": "test"}'
            def extract_json(self, response):
                return {"tables_needed": [], "reasoning": "test"}
        
        linker = SchemaLinker(schema_context, MockLLMClient())
        
        result = linker.link("Show all subjects")
        
        assert result is not None
        assert "subjects" in result.tables
    
    def test_study_identifier_extraction(self, schema_context):
        """Test extraction of study identifiers"""
        class MockLLMClient:
            def complete(self, prompt, system_prompt=None):
                return '{}'
            def extract_json(self, response):
                return {}
        
        linker = SchemaLinker(schema_context, MockLLMClient())
        
        ids = linker._extract_identifiers("Show subjects in Study 1 at Site 18")
        
        assert ("study", "Study 1") in ids
        assert ("site", "Site 18") in ids
    
    def test_query_with_status_filter(self, schema_context):
        """Test linking for query with status filter"""
        class MockLLMClient:
            def complete(self, prompt, system_prompt=None):
                return '{}'
            def extract_json(self, response):
                return {}
        
        linker = SchemaLinker(schema_context, MockLLMClient())
        
        result = linker.link("Show all open queries")
        
        assert "data_queries" in result.tables
        assert any(f.get("value") == "OPEN" for f in result.filters)
    
    def test_aggregation_detection(self, schema_context):
        """Test detection of aggregation keywords"""
        class MockLLMClient:
            def complete(self, prompt, system_prompt=None):
                return '{}'
            def extract_json(self, response):
                return {}
        
        linker = SchemaLinker(schema_context, MockLLMClient())
        
        result = linker.link("How many subjects are enrolled?")
        assert result.aggregation == "COUNT"
        
        result = linker.link("What is the average query age?")
        assert result.aggregation == "AVG"
    
    def test_join_path_building(self, schema_context):
        """Test that join paths are correctly built"""
        class MockLLMClient:
            def complete(self, prompt, system_prompt=None):
                return '{}'
            def extract_json(self, response):
                return {}
        
        linker = SchemaLinker(schema_context, MockLLMClient())
        
        result = linker.link("Show queries for Study 1")
        
        # Should link from studies through sites/subjects to queries
        assert "studies" in result.tables
        assert "data_queries" in result.tables


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
