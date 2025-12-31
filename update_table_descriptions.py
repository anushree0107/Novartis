"""
Script to update table descriptions and column descriptions in schema cache
Based on Dataset Guidance Document
"""
import json
from pathlib import Path

# Table descriptions from guidance document
TABLE_DESCRIPTIONS = {
    "study_metrics": {
        "description": "Summary metrics per study showing total issues, average issues, max issues, and record counts for MedDRA and eSAE. This is a high-level overview table for comparing studies. Use for questions like 'which study has most issues', 'study-level statistics', 'comparing studies'.",
        "columns": {
            "study": "Name of the clinical study (e.g., 'Study 1', 'Study 10'). Use this to filter by specific study.",
            "total_issues": "Total number of unresolved data issues across all subjects in the study.",
            "avg_issues": "Average number of issues per subject in the study.",
            "max_issues": "Maximum number of issues for any single subject in the study.",
            "meddra_records": "Total number of MedDRA coding records (adverse events, medical history) for the study.",
            "esae_records": "Total number of eSAE (electronic Serious Adverse Event) records for the study."
        }
    },
    
    "edrr_processed": {
        "description": "Compiled EDRR (External Data Reconciliation Report) - Summarizes total unresolved data issues for each subject for third-party data. Used for prioritizing data cleaning and issue resolution. Each row = one subject with open issues.",
        "columns": {
            "study": "Name of the clinical study.",
            "subject": "Unique identifier for each subject/patient (e.g., 'Subject 27371').",
            "total_open_issue_count_per_subject": "Number of unresolved issues for this subject. Higher = more data quality issues.",
            "_source_study": "Original study source identifier."
        }
    },
    
    "esae_dashboard_processed": {
        "description": "SAE Dashboard for Data Management - Tracks Serious Adverse Event discrepancies and review status from a data management perspective. Used for monitoring SAE data quality and review workflow. Each row = one SAE discrepancy.",
        "columns": {
            "discrepancy_id": "Unique identifier for each discrepancy or issue.",
            "study_id": "Identifier for the clinical study.",
            "country": "Country where the clinical site is located.",
            "site": "Unique identifier for the clinical trial site.",
            "patient_id": "Unique identifier for the patient/subject.",
            "form_name": "Name of the data entry form where the discrepancy was found.",
            "discrepancy_created_timestamp_in_dashboard": "Date/time when the discrepancy was created.",
            "review_status": "Current review status (e.g., 'Review Completed', 'Pending for Review').",
            "action_status": "Status of actions taken (e.g., 'No action required', 'Pending').",
            "_source_study": "Original study source.",
            "case_status": "Status of the clinical case (e.g., 'Closed', 'Locked')."
        }
    },
    
    "esae_processed": {
        "description": "SAE Dashboard for Safety Team - Tracks Serious Adverse Event discrepancies from safety perspective. Similar to esae_dashboard_processed but focused on safety team workflow. Each row = one SAE discrepancy.",
        "columns": {
            "discrepancy_id": "Unique identifier for each discrepancy.",
            "study_id": "Identifier for the clinical study.",
            "country": "Country where the site is located.",
            "site": "Unique identifier for the clinical trial site.",
            "patient_id": "Unique identifier for the patient/subject.",
            "form_name": "Name of the data entry form with the discrepancy.",
            "discrepancy_created_timestamp_in_dashboard": "Timestamp when discrepancy was created.",
            "review_status": "Current review status.",
            "action_status": "Status of actions taken or required.",
            "_source_study": "Original study source.",
            "case_status": "Status of the clinical case."
        }
    },
    
    "meddra_processed": {
        "description": "MedDRA Coding Report - Records all medical terms (adverse events, medical history) that require or have undergone MedDRA coding. Use for questions about coding status, uncoded terms, adverse events. Each row = one term requiring coding.",
        "columns": {
            "meddra_coding_report": "Indicates this is a MedDRA coding report.",
            "study": "Name or ID of the clinical study.",
            "dictionary": "Name of the coding dictionary (MedDRA).",
            "dictionary_version_number": "Version of the MedDRA dictionary used.",
            "subject": "Unique identifier for the subject/patient.",
            "form_oid": "Object Identifier for the form in EDC system.",
            "logline": "Line number or sequence for the coded entry.",
            "field_oid": "Object Identifier for the specific field.",
            "coding_status": "Status of coding (e.g., 'Coded Term', 'UnCoded Term'). Use to count coded vs uncoded.",
            "require_coding": "Indicates if term requires coding (Yes/No).",
            "_source_study": "Original study source."
        }
    },
    
    "whodd_processed": {
        "description": "WHO Drug Coding Report - Records all medications and therapies that require or have undergone WHO Drug dictionary coding. Use for questions about drug/medication coding. Each row = one medication entry.",
        "columns": {
            "whodrug_coding_report": "Indicates this is a WHO Drug coding report.",
            "study": "Name or ID of the clinical study.",
            "dictionary": "Name of the coding dictionary (WHODrug-Global).",
            "dictionary_version_number": "Version of the WHO Drug dictionary.",
            "subject": "Unique identifier for the subject/patient.",
            "form_oid": "Object Identifier for the form in EDC system.",
            "logline": "Line number or sequence for the coded entry.",
            "field_oid": "Object Identifier for the specific field.",
            "coding_status": "Status of coding (e.g., 'Coded Term', 'UnCoded Term').",
            "require_coding": "Indicates if term requires coding (Yes/No).",
            "_source_study": "Original study source."
        }
    },
    
    "missing_pages_processed": {
        "description": "Global Missing Pages Report - Details missing CRF (Case Report Form) pages at individual visit level for each subject. Used to identify and follow-up on specific data gaps. Each row = one missing page.",
        "columns": {
            "study_name": "Name of the clinical study.",
            "sitegroupname_countryname_": "Country or region where the site is located.",
            "sitenumber": "Unique identifier for the clinical trial site.",
            "subjectname": "Unique identifier for the subject/patient.",
            "overall_subject_status": "Status of the subject (e.g., 'Survival', 'Discontinued', 'Follow-Up').",
            "visit_level_subject_status": "Status of subject at the visit level.",
            "foldername": "Name of the folder/module in EDC system.",
            "visit_date": "Date of the scheduled or actual visit.",
            "form_type__summary_or_visit_": "Indicates if missing page is from summary or specific visit.",
            "formname": "Name of the form with missing pages.",
            "no___days_page_missing": "Number of days the page has been missing. Higher = more urgent.",
            "_source_study": "Original study source.",
            "form_1_subject_status": "Subject status on the form."
        }
    },
    
    "visit_projection_processed": {
        "description": "Visit Projection Tracker - Lists all projected subject visits that haven't occurred or been entered, including days overdue. Used for tracking visit compliance and proactive follow-up. Each row = one missing/overdue visit.",
        "columns": {
            "country": "Country where the clinical site is located.",
            "site": "Unique identifier for the clinical trial site.",
            "subject": "Unique identifier for the subject/patient.",
            "visit": "Name of the scheduled visit (e.g., 'Cycle12Week1').",
            "projected_date": "Planned date for the visit as per protocol.",
            "__days_outstanding": "Number of days since projected date. Positive = overdue.",
            "_source_study": "Original study source.",
            "actual_date": "Actual date the visit occurred (if any).",
            "__days_outstanding__today___projected_date_": "Days outstanding calculation."
        }
    }
}


def update_schema_cache():
    """Update schema cache with descriptions"""
    cache_path = Path("cache/schema_cache.json")
    
    with open(cache_path, "r") as f:
        schema = json.load(f)
    
    # Update each table
    for table_name, table_info in TABLE_DESCRIPTIONS.items():
        if table_name in schema:
            # Update table description
            schema[table_name]["description"] = table_info["description"]
            
            # Update column descriptions
            for col in schema[table_name]["columns"]:
                col_name = col["name"]
                if col_name in table_info["columns"]:
                    col["description"] = table_info["columns"][col_name]
            
            print(f"✓ Updated {table_name}")
        else:
            print(f"✗ Table {table_name} not found in schema")
    
    # Save updated schema
    with open(cache_path, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"\nSchema cache updated: {cache_path}")


def show_summary():
    """Show summary of table descriptions"""
    print("\n" + "=" * 70)
    print("TABLE DESCRIPTIONS SUMMARY")
    print("=" * 70)
    
    for table, info in TABLE_DESCRIPTIONS.items():
        print(f"\n📊 {table}")
        print(f"   {info['description'][:100]}...")
        print(f"   Columns: {', '.join(info['columns'].keys())}")


if __name__ == "__main__":
    show_summary()
    print("\n")
    update_schema_cache()
