"""Explore data to create testbench questions"""
from database.connection import db_manager
import pandas as pd

def run_query(sql, desc=""):
    print(f"\n{'='*60}")
    print(f"{desc}")
    print(f"SQL: {sql}")
    print('='*60)
    result = db_manager.execute_query(sql)
    df = pd.DataFrame(result)
    print(df.to_string() if len(df) < 30 else df.head(10).to_string())
    return result

# 1. Study metrics
run_query("SELECT COUNT(DISTINCT study) as count FROM study_metrics", "Count of studies")
run_query("SELECT study, total_issues FROM study_metrics ORDER BY total_issues DESC LIMIT 3", "Top 3 studies by issues")
run_query("SELECT study, total_issues FROM study_metrics WHERE total_issues = 0", "Studies with zero issues")
run_query("SELECT SUM(total_issues) as total FROM study_metrics", "Total issues across all studies")
run_query("SELECT study, meddra_records FROM study_metrics ORDER BY meddra_records DESC LIMIT 3", "Top studies by MedDRA records")

# 2. MedDRA
run_query("SELECT COUNT(*) as count FROM meddra_processed WHERE study = 'Study 10'", "MedDRA records for Study 10")
run_query("SELECT study, COUNT(*) as cnt FROM meddra_processed GROUP BY study ORDER BY cnt DESC LIMIT 5", "MedDRA records by study")
run_query("SELECT coding_status, COUNT(*) as cnt FROM meddra_processed GROUP BY coding_status", "MedDRA coding status breakdown")
run_query("SELECT COUNT(DISTINCT subject) as cnt FROM meddra_processed WHERE study = 'Study 1'", "Distinct subjects in MedDRA Study 1")

# 3. WHODD
run_query("SELECT COUNT(*) as count FROM whodd_processed WHERE study = 'Study 10'", "WHODD records for Study 10")
run_query("SELECT study, COUNT(*) as cnt FROM whodd_processed GROUP BY study ORDER BY cnt DESC LIMIT 5", "WHODD records by study")

# 4. ESAE Dashboard
run_query("SELECT COUNT(*) as count FROM esae_dashboard_processed", "Total ESAE discrepancies")
run_query("SELECT study_id, COUNT(*) as cnt FROM esae_dashboard_processed GROUP BY study_id ORDER BY cnt DESC LIMIT 5", "ESAE by study")
run_query("SELECT review_status, COUNT(*) as cnt FROM esae_dashboard_processed GROUP BY review_status", "ESAE review status")
run_query("SELECT action_status, COUNT(*) as cnt FROM esae_dashboard_processed GROUP BY action_status", "ESAE action status")
run_query("SELECT country, COUNT(*) as cnt FROM esae_dashboard_processed GROUP BY country ORDER BY cnt DESC LIMIT 5", "ESAE by country")
run_query("SELECT COUNT(DISTINCT country) as cnt FROM esae_dashboard_processed", "Distinct countries in ESAE")
run_query("SELECT COUNT(DISTINCT site) as cnt FROM esae_dashboard_processed", "Distinct sites in ESAE")
run_query("SELECT COUNT(DISTINCT patient_id) as cnt FROM esae_dashboard_processed", "Distinct patients in ESAE")

# 5. Missing pages
run_query("SELECT COUNT(*) as count FROM missing_pages_processed", "Total missing pages")
run_query("SELECT study_name, COUNT(*) as cnt FROM missing_pages_processed GROUP BY study_name ORDER BY cnt DESC LIMIT 5", "Missing pages by study")
run_query("SELECT COUNT(DISTINCT subjectname) as cnt FROM missing_pages_processed", "Distinct subjects with missing pages")

# 6. Visit projection
run_query("SELECT COUNT(*) as count FROM visit_projection_processed", "Total projected visits")
run_query("SELECT country, COUNT(*) as cnt FROM visit_projection_processed GROUP BY country ORDER BY cnt DESC LIMIT 5", "Visits by country")
run_query("SELECT COUNT(DISTINCT subject) as cnt FROM visit_projection_processed", "Distinct subjects in visit projection")

# 7. EDRR
run_query("SELECT COUNT(*) as count FROM edrr_processed", "Total EDRR records")
run_query("SELECT study, COUNT(*) as cnt FROM edrr_processed GROUP BY study ORDER BY cnt DESC LIMIT 5", "EDRR by study")
run_query("SELECT MAX(total_open_issue_count_per_subject) as max_issues FROM edrr_processed", "Max issues per subject")
run_query("SELECT study, subject, total_open_issue_count_per_subject FROM edrr_processed ORDER BY total_open_issue_count_per_subject DESC LIMIT 3", "Top subjects by issues")

print("\n\nDONE!")
