"""Verify test data values"""
from database.connection import db_manager

print("=" * 60)
print("DATA VERIFICATION FOR EASY TESTS")
print("=" * 60)

# Test 2: Sites count
print("\nTEST 2 - Sites in Study 10:")
r1 = db_manager.execute_query("SELECT COUNT(DISTINCT site_id) as cnt FROM study_10_cpid_edc_metrics_ursv20_14nov2025_sv")
r2 = db_manager.execute_query("SELECT COUNT(DISTINCT site_id) as cnt FROM study_10_cpid_edc_metrics_ursv20_14nov2025_subject_level_metric")
print(f"  sv table: {r1[0]['cnt']}")
print(f"  subject_level_metric: {r2[0]['cnt']} (Expected: 35)")

# Test 5: MedDRA records
print("\nTEST 5 - MedDRA records:")
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM study_10_globalcodingreport_meddra_14nov2025")
print(f"  Total COUNT(*): {r[0]['cnt']} (Expected: 796)")

# Test 8: USA patients
print("\nTEST 8 - USA patients:")
r = db_manager.execute_query("SELECT COUNT(DISTINCT subject_id) as cnt FROM study_10_cpid_edc_metrics_ursv20_14nov2025_subject_level_metric WHERE country = 'USA'")
print(f"  USA patients: {r[0]['cnt']} (Expected: 45)")

# Test 9: Japan patients
print("\nTEST 9 - Japan patients:")
r = db_manager.execute_query("SELECT COUNT(DISTINCT subject_id) as cnt FROM study_10_cpid_edc_metrics_ursv20_14nov2025_subject_level_metric WHERE country = 'JPN'")
print(f"  JPN patients: {r[0]['cnt']} (Expected: 11)")

# Test 4: Countries list
print("\nTEST 4 - Countries list:")
r = db_manager.execute_query("SELECT DISTINCT country FROM study_10_cpid_edc_metrics_ursv20_14nov2025_subject_level_metric WHERE country IS NOT NULL ORDER BY country")
countries = [row['country'] for row in r]
print(f"  Countries: {countries}")

print("\n" + "=" * 60)
