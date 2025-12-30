"""
Clinical Trial Domain Knowledge for CHASE-SQL.

Contains terminology, abbreviations, and domain-specific context
to help the LLM understand clinical trial data concepts.
"""

CLINICAL_DOMAIN_CONTEXT = """
## Clinical Trial Domain Knowledge

### Key Terminology:
- **EDC (Electronic Data Capture)**: Systems like Rave and J-review for collecting trial data
- **CRF (Case Report Form)**: Forms used to capture patient data at each visit
- **SDV (Source Data Verification)**: Process of verifying CRF data against source documents
- **PI (Principal Investigator)**: Lead physician at investigational site
- **SAE (Serious Adverse Event)**: Medical event that results in death, hospitalization, or disability
- **AE (Adverse Event)**: Any untoward medical occurrence during the trial
- **Protocol Deviation/PD**: Non-compliance with the study protocol requirements
- **Query**: Data clarification request sent to site for data discrepancies
- **MedDRA**: Medical Dictionary for Regulatory Activities (for coding AEs)
- **WHODD**: WHO Drug Dictionary (for coding medications)

### Subject/Patient Status Progression:
SCREENING → SCREEN_FAILED (if fails) OR ENROLLED → ON_TREATMENT → COMPLETED/DISCONTINUED/LOST_TO_FOLLOWUP

### Query Status Progression:
OPEN → ANSWERED → CLOSED (or CANCELLED)

### Common Data Quality Metrics:
- **Open queries**: Questions about data that need site response
- **Missing pages**: CRF forms that should have been completed but weren't
- **Broken signatures**: PI signatures that were invalidated due to data changes
- **Pending SDV**: Forms awaiting source data verification

### Site Hierarchy:
Region (EMEA, AMERICA, APAC) → Country → Site → Subject

### Study Hierarchy:
Study → Site → Subject → Visit → CRF Page → Form Fields

### Visit Types:
- Screening: Initial eligibility assessment
- Baseline: First treatment visit
- Treatment visits (e.g., W2D7 = Week 2 Day 7)
- End of Treatment (EOT)
- Follow-up visits (e.g., Follow-up_Week 16)
- Unscheduled/Adverse Event visits

### Common Query Patterns:
Users often ask about:
1. Data quality issues (open queries, missing pages, pending signatures)
2. Subject/enrollment status across sites
3. Operational metrics (SDV completion, query resolution times)
4. Safety data (adverse events, SAEs)
5. Protocol deviations by site or study
6. Coding status (MedDRA, WHODD)
"""

# Mapping of common user terms to database columns/tables
TERM_MAPPINGS = {
    # Status terms
    "enrolled": ("subjects", "status", "ENROLLED"),
    "on treatment": ("subjects", "status", "ON_TREATMENT"),
    "completed": ("subjects", "status", "COMPLETED"),
    "discontinued": ("subjects", "status", "DISCONTINUED"),
    "screening": ("subjects", "status", "SCREENING"),
    
    # Query terms
    "open query": ("data_queries", "query_status", "OPEN"),
    "open queries": ("data_queries", "query_status", "OPEN"),
    "closed query": ("data_queries", "query_status", "CLOSED"),
    "query age": ("data_queries", "days_open", None),
    
    # SDV terms
    "sdv complete": ("sdv_records", "verification_status", "VERIFIED"),
    "pending sdv": ("sdv_records", "verification_status", "REQUIRE_VERIFICATION"),
    "verified": ("sdv_records", "verification_status", "VERIFIED"),
    
    # Signature terms
    "broken signature": ("pi_signatures", "is_signature_broken", True),
    "pending signature": ("pi_signatures", "signed_date", None),
    
    # Protocol deviation terms
    "protocol deviation": ("protocol_deviations", None, None),
    "pd": ("protocol_deviations", None, None),
    "confirmed pd": ("protocol_deviations", "deviation_status", "PD_CONFIRMED"),
    "proposed pd": ("protocol_deviations", "deviation_status", "PD_PROPOSED"),
    
    # Coding terms
    "meddra": ("coding_records", "dictionary_type", "MedDRA"),
    "whodd": ("coding_records", "dictionary_type", "WHODD"),
    "requires coding": ("coding_records", "coding_status", "REQUIRES_CODING"),
    "coded": ("coding_records", "coding_status", "CODED"),
    
    # Safety terms
    "adverse event": ("adverse_events", None, None),
    "ae": ("adverse_events", None, None),
    "sae": ("sae_records", None, None),
    "serious adverse event": ("sae_records", None, None),
    
    # Geographic terms
    "site": ("sites", "site_number", None),
    "country": ("countries", "country_name", None),
    "region": ("regions", "region_name", None),
}

# Common aggregation patterns
AGGREGATION_PATTERNS = {
    "how many": "COUNT(*)",
    "count": "COUNT(*)",
    "total": "COUNT(*)",
    "average": "AVG",
    "mean": "AVG",
    "maximum": "MAX",
    "max": "MAX",
    "minimum": "MIN",
    "min": "MIN",
    "sum": "SUM",
    "list": None,  # No aggregation, just SELECT
    "show": None,
}
