from database.connection import db_manager
print('=== Study 10 Data in New Schema ===')
print()

print('MedDRA:')
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM meddra_processed WHERE study = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}')

print()
print('WHODD:')
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM whodd_processed WHERE study = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}')

print()
print('Study Metrics:')
r = db_manager.execute_query("SELECT * FROM study_metrics WHERE study = 'Study 10'")
print(f'  {r}')

print()
print('eSAE:')
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM esae_dashboard_processed WHERE study_id = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}')

print()
print('Visit Projection:')
r = db_manager.execute_query("SELECT COUNT(*) as cnt, COUNT(DISTINCT subject) as subjects FROM visit_projection_processed WHERE _source_study = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}, Subjects: {r[0]["subjects"]}')

print()
print('Missing Pages:')
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM missing_pages_processed WHERE study_name ILIKE '%10%' OR _source_study = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}')

print()
print('EDRR (Issues):')
r = db_manager.execute_query("SELECT COUNT(*) as cnt FROM edrr_processed WHERE study = 'Study 10'")
print(f'  Records: {r[0]["cnt"]}')
