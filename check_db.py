"""Quick check of new database structure"""
from database.connection import db_manager
import pandas as pd

print("=" * 60)
print("NEW DATABASE STRUCTURE")
print("=" * 60)

print("\n=== study_metrics (sample) ===")
df = pd.DataFrame(db_manager.execute_query('SELECT * FROM study_metrics LIMIT 5'))
print(df)

print("\n=== All Tables and Columns ===")
for t in db_manager.get_all_tables():
    cols = db_manager.get_table_columns(t)
    col_names = [c["column_name"] for c in cols]
    result = db_manager.execute_query(f'SELECT COUNT(*) as cnt FROM "{t}"')
    print(f"\n{t} ({result[0]['cnt']} rows):")
    print(f"  Columns: {col_names}")
