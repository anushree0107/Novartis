import json
with open('cache/schema_cache.json') as f:
    schema = json.load(f)

for table in ['study_metrics', 'meddra_processed', 'esae_dashboard_processed']:
    print(f'\n=== {table} ===')
    print(f'Description: {schema[table]["description"][:150]}...')
    print('Columns:')
    for col in schema[table]['columns'][:3]:
        desc = col.get("description", "")
        print(f'  - {col["name"]}: {desc[:60] if desc else "(no description)"}')
