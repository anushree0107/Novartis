"""
Training Data Generator for CHASE-SQL.

Generates question-SQL pairs for fine-tuning or evaluation
based on the clinical trials database schema.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from ..schema_context import SchemaContext, get_schema_context


@dataclass
class TrainingExample:
    """A single training example"""
    question: str
    sql: str
    tables: List[str]
    complexity: str  # simple, medium, complex
    category: str    # query, aggregation, join, filter


# Template-based question-SQL pairs for clinical trials
TRAINING_TEMPLATES = [
    # Simple queries
    {
        "question": "Show all studies",
        "sql": "SELECT * FROM studies;",
        "tables": ["studies"],
        "complexity": "simple",
        "category": "simple_select"
    },
    {
        "question": "List all active sites",
        "sql": "SELECT site_number, site_name, status FROM sites WHERE status = 'ACTIVE';",
        "tables": ["sites"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "question": "How many subjects are in the database?",
        "sql": "SELECT COUNT(*) as total_subjects FROM subjects;",
        "tables": ["subjects"],
        "complexity": "simple",
        "category": "aggregation"
    },
    
    # Single-table with filters
    {
        "question": "Show subjects with status 'ON_TREATMENT'",
        "sql": "SELECT subject_number, status, latest_visit FROM subjects WHERE status = 'ON_TREATMENT';",
        "tables": ["subjects"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "question": "List all open queries",
        "sql": "SELECT * FROM data_queries WHERE query_status = 'OPEN';",
        "tables": ["data_queries"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "question": "Show protocol deviations with status 'PD_CONFIRMED'",
        "sql": "SELECT * FROM protocol_deviations WHERE deviation_status = 'PD_CONFIRMED';",
        "tables": ["protocol_deviations"],
        "complexity": "simple",
        "category": "filter"
    },
    
    # Study-specific queries
    {
        "question": "Show all subjects in Study 1",
        "sql": """SELECT sub.subject_number, sub.status, sub.latest_visit 
FROM subjects sub 
JOIN studies st ON sub.study_id = st.study_id 
WHERE st.study_code = 'Study 1';""",
        "tables": ["subjects", "studies"],
        "complexity": "medium",
        "category": "join"
    },
    {
        "question": "How many subjects are enrolled in Study 1?",
        "sql": """SELECT COUNT(*) as enrolled_count 
FROM subjects sub 
JOIN studies st ON sub.study_id = st.study_id 
WHERE st.study_code = 'Study 1' AND sub.status = 'ENROLLED';""",
        "tables": ["subjects", "studies"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "question": "List all sites for Study 1",
        "sql": """SELECT s.site_number, s.site_name, s.status, s.principal_investigator 
FROM sites s 
JOIN studies st ON s.study_id = st.study_id 
WHERE st.study_code = 'Study 1';""",
        "tables": ["sites", "studies"],
        "complexity": "medium",
        "category": "join"
    },
    
    # Site-specific queries
    {
        "question": "Show all subjects at Site 18",
        "sql": """SELECT sub.subject_number, sub.status, sub.enrollment_date 
FROM subjects sub 
JOIN sites s ON sub.site_id = s.site_id 
WHERE s.site_number = 'Site 18';""",
        "tables": ["subjects", "sites"],
        "complexity": "medium",
        "category": "join"
    },
    {
        "question": "How many open queries are there at Site 2?",
        "sql": """SELECT COUNT(*) as open_query_count 
FROM data_queries q 
JOIN subjects sub ON q.subject_id = sub.subject_id 
JOIN sites s ON sub.site_id = s.site_id 
WHERE s.site_number = 'Site 2' AND q.query_status = 'OPEN';""",
        "tables": ["data_queries", "subjects", "sites"],
        "complexity": "medium",
        "category": "aggregation"
    },
    
    # Multi-join queries
    {
        "question": "Show all open queries for Study 1 with site and subject information",
        "sql": """SELECT q.query_text, q.days_open, q.action_owner, 
       sub.subject_number, s.site_number 
FROM data_queries q 
JOIN subjects sub ON q.subject_id = sub.subject_id 
JOIN sites s ON sub.site_id = s.site_id 
JOIN studies st ON s.study_id = st.study_id 
WHERE st.study_code = 'Study 1' AND q.query_status = 'OPEN' 
ORDER BY q.days_open DESC;""",
        "tables": ["data_queries", "subjects", "sites", "studies"],
        "complexity": "complex",
        "category": "join"
    },
    {
        "question": "List subjects with broken PI signatures",
        "sql": """SELECT sub.subject_number, ps.form_name, ps.visit_name, ps.days_pending 
FROM pi_signatures ps 
JOIN subjects sub ON ps.subject_id = sub.subject_id 
WHERE ps.is_signature_broken = TRUE;""",
        "tables": ["pi_signatures", "subjects"],
        "complexity": "medium",
        "category": "join"
    },
    
    # Aggregation queries
    {
        "question": "Count open queries per site for Study 1",
        "sql": """SELECT s.site_number, COUNT(q.query_id) as open_queries 
FROM sites s 
JOIN subjects sub ON s.site_id = sub.site_id 
LEFT JOIN data_queries q ON sub.subject_id = q.subject_id AND q.query_status = 'OPEN'
JOIN studies st ON s.study_id = st.study_id 
WHERE st.study_code = 'Study 1' 
GROUP BY s.site_id, s.site_number 
ORDER BY open_queries DESC;""",
        "tables": ["sites", "subjects", "data_queries", "studies"],
        "complexity": "complex",
        "category": "aggregation"
    },
    {
        "question": "Show subject count by status for Study 1",
        "sql": """SELECT sub.status, COUNT(*) as count 
FROM subjects sub 
JOIN studies st ON sub.study_id = st.study_id 
WHERE st.study_code = 'Study 1' 
GROUP BY sub.status 
ORDER BY count DESC;""",
        "tables": ["subjects", "studies"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "question": "What is the average query age for open queries?",
        "sql": "SELECT AVG(days_open) as avg_days_open FROM data_queries WHERE query_status = 'OPEN';",
        "tables": ["data_queries"],
        "complexity": "simple",
        "category": "aggregation"
    },
    
    # Condition-based queries
    {
        "question": "Show queries open for more than 30 days",
        "sql": "SELECT * FROM data_queries WHERE query_status = 'OPEN' AND days_open > 30 ORDER BY days_open DESC;",
        "tables": ["data_queries"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "question": "List pending SDV records",
        "sql": "SELECT * FROM sdv_records WHERE verification_status = 'REQUIRE_VERIFICATION';",
        "tables": ["sdv_records"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "question": "Show coding records that require coding",
        "sql": "SELECT * FROM coding_records WHERE coding_status = 'REQUIRES_CODING';",
        "tables": ["coding_records"],
        "complexity": "simple",
        "category": "filter"
    },
    
    # Complex queries with multiple conditions
    {
        "question": "Show open queries for subjects at Site 18 in Study 1 with more than 45 days open",
        "sql": """SELECT q.query_text, q.days_open, sub.subject_number, q.action_owner 
FROM data_queries q 
JOIN subjects sub ON q.subject_id = sub.subject_id 
JOIN sites s ON sub.site_id = s.site_id 
JOIN studies st ON s.study_id = st.study_id 
WHERE st.study_code = 'Study 1' 
  AND s.site_number = 'Site 18' 
  AND q.query_status = 'OPEN' 
  AND q.days_open > 45 
ORDER BY q.days_open DESC;""",
        "tables": ["data_queries", "subjects", "sites", "studies"],
        "complexity": "complex",
        "category": "filter"
    },
    {
        "question": "Find subjects with both open queries and pending signatures",
        "sql": """SELECT DISTINCT sub.subject_number, sub.status 
FROM subjects sub 
WHERE EXISTS (SELECT 1 FROM data_queries q WHERE q.subject_id = sub.subject_id AND q.query_status = 'OPEN')
AND EXISTS (SELECT 1 FROM pi_signatures ps WHERE ps.subject_id = sub.subject_id AND ps.is_signature_broken = TRUE);""",
        "tables": ["subjects", "data_queries", "pi_signatures"],
        "complexity": "complex",
        "category": "subquery"
    },
    
    # Region/Country queries
    {
        "question": "Show sites in the EMEA region",
        "sql": """SELECT s.site_number, s.site_name, c.country_name 
FROM sites s 
JOIN countries c ON s.country_id = c.country_id 
JOIN regions r ON c.region_id = r.region_id 
WHERE r.region_code = 'EMEA';""",
        "tables": ["sites", "countries", "regions"],
        "complexity": "medium",
        "category": "join"
    },
    
    # SAE/Safety queries
    {
        "question": "List all open SAE discrepancies",
        "sql": "SELECT * FROM sae_records WHERE action_status = 'Open';",
        "tables": ["sae_records"],
        "complexity": "simple",
        "category": "filter"
    },
    
    # AI Insights queries
    {
        "question": "Show high priority AI insights",
        "sql": "SELECT insight_title, insight_text, priority, confidence_score FROM ai_insights WHERE priority = 'HIGH' OR priority = 'CRITICAL' ORDER BY confidence_score DESC;",
        "tables": ["ai_insights"],
        "complexity": "simple",
        "category": "filter"
    },
]


class TrainingDataGenerator:
    """
    Generates training data for CHASE-SQL fine-tuning.
    
    Creates question-SQL pairs based on:
    1. Static templates
    2. Dynamic generation from schema
    3. Variations using paraphrasing
    """
    
    def __init__(self, schema_context: Optional[SchemaContext] = None):
        self.schema_context = schema_context or get_schema_context()
    
    def generate_all(self) -> List[TrainingExample]:
        """Generate all training examples"""
        examples = []
        
        # Add static templates
        for template in TRAINING_TEMPLATES:
            examples.append(TrainingExample(**template))
        
        # Generate dynamic examples based on schema
        examples.extend(self._generate_from_schema())
        
        return examples
    
    def _generate_from_schema(self) -> List[TrainingExample]:
        """Generate examples dynamically from schema"""
        examples = []
        
        # Generate simple SELECT * for each table
        for table_name, table_info in self.schema_context.tables.items():
            if table_name in ['audit_logs', 'ingestion_jobs']:  # Skip system tables
                continue
            
            # Show all records
            examples.append(TrainingExample(
                question=f"Show all {table_name.replace('_', ' ')}",
                sql=f"SELECT * FROM {table_name} LIMIT 100;",
                tables=[table_name],
                complexity="simple",
                category="simple_select"
            ))
            
            # Find columns with 'status' in name
            for col in table_info.columns:
                if 'status' in col.name.lower() and col.enum_values:
                    for status in col.enum_values[:3]:
                        examples.append(TrainingExample(
                            question=f"Show {table_name.replace('_', ' ')} with {col.name.replace('_', ' ')} = {status}",
                            sql=f"SELECT * FROM {table_name} WHERE {col.name} = '{status}';",
                            tables=[table_name],
                            complexity="simple",
                            category="filter"
                        ))
        
        return examples
    
    def save_to_json(self, output_path: str):
        """Save training data to JSON file"""
        examples = self.generate_all()
        data = [asdict(ex) for ex in examples]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return len(examples)
    
    def save_to_jsonl(self, output_path: str, format_type: str = "openai"):
        """
        Save training data in JSONL format for fine-tuning.
        
        Args:
            output_path: Output file path
            format_type: 'openai' for chat fine-tuning, 'simple' for prompt-completion
        """
        examples = self.generate_all()
        
        with open(output_path, 'w') as f:
            for ex in examples:
                if format_type == "openai":
                    # OpenAI chat fine-tuning format
                    record = {
                        "messages": [
                            {"role": "system", "content": "You are a SQL expert for clinical trials databases."},
                            {"role": "user", "content": ex.question},
                            {"role": "assistant", "content": f"```sql\n{ex.sql}\n```"}
                        ]
                    }
                else:
                    # Simple prompt-completion format
                    record = {
                        "prompt": f"Generate SQL for: {ex.question}",
                        "completion": ex.sql
                    }
                f.write(json.dumps(record) + "\n")
        
        return len(examples)


def generate_training_data():
    """CLI function to generate training data"""
    generator = TrainingDataGenerator()
    
    output_dir = Path("/home/anushree/Novartis/chase_sql/training")
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "clinical_qa_pairs.json"
    count = generator.save_to_json(str(json_path))
    print(f"Saved {count} examples to {json_path}")
    
    # Save JSONL for fine-tuning
    jsonl_path = output_dir / "clinical_qa_pairs.jsonl"
    generator.save_to_jsonl(str(jsonl_path), format_type="openai")
    print(f"Saved {count} examples to {jsonl_path}")


if __name__ == "__main__":
    generate_training_data()
