-- =====================================================
-- Clinical Trials Data Integration PostgreSQL Schema
-- Version: 1.0
-- Description: Comprehensive database schema for 
--              integrated insight-driven clinical trials data management
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- =====================================================
-- 1. CORE REFERENCE TABLES
-- =====================================================

-- Create ENUM types for standardized values
CREATE TYPE study_status AS ENUM ('PLANNING', 'ACTIVE', 'ENROLLING', 'COMPLETED', 'SUSPENDED', 'TERMINATED');
CREATE TYPE study_phase AS ENUM ('Phase I', 'Phase II', 'Phase IIA', 'Phase IIB', 'Phase III', 'Phase IV');
CREATE TYPE subject_status AS ENUM ('SCREENING', 'SCREEN_FAILED', 'ENROLLED', 'ON_TREATMENT', 'DISCONTINUED', 'COMPLETED', 'LOST_TO_FOLLOWUP');
CREATE TYPE visit_status AS ENUM ('SCHEDULED', 'COMPLETED', 'MISSED', 'PARTIAL', 'NOT_APPLICABLE');
CREATE TYPE query_status AS ENUM ('OPEN', 'ANSWERED', 'CLOSED', 'CANCELLED');
CREATE TYPE query_owner AS ENUM ('SITE_REVIEW', 'CRA_ACTION', 'DM_ACTION', 'SPONSOR');
CREATE TYPE verification_status AS ENUM ('REQUIRE_VERIFICATION', 'VERIFIED', 'NOT_APPLICABLE');
CREATE TYPE signature_status AS ENUM ('NOT_REQUIRED', 'PENDING', 'SIGNED', 'BROKEN');
CREATE TYPE deviation_status AS ENUM ('PD_PROPOSED', 'PD_CONFIRMED', 'PD_WAIVED', 'PD_REJECTED');
CREATE TYPE coding_status AS ENUM ('CODED', 'REQUIRES_CODING', 'PENDING', 'AUTO_CODED');
CREATE TYPE user_role AS ENUM ('ADMIN', 'CTT', 'CRA', 'CTA', 'SITE_STAFF', 'DATA_MANAGER', 'MEDICAL_MONITOR', 'SAFETY_PHYSICIAN');
CREATE TYPE insight_type AS ENUM ('DATA_QUALITY', 'OPERATIONAL', 'SAFETY', 'ENROLLMENT', 'COMPLIANCE');
CREATE TYPE priority_level AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW');
CREATE TYPE ae_severity AS ENUM ('MILD', 'MODERATE', 'SEVERE', 'LIFE_THREATENING', 'DEATH');
CREATE TYPE ae_seriousness AS ENUM ('SERIOUS', 'NON_SERIOUS');
CREATE TYPE ae_relationship AS ENUM ('RELATED', 'POSSIBLY_RELATED', 'UNLIKELY_RELATED', 'NOT_RELATED');

-- -----------------------------------------------------
-- Table: studies
-- Description: Clinical trial master table
-- -----------------------------------------------------
CREATE TABLE studies (
    study_id SERIAL PRIMARY KEY,
    study_code VARCHAR(50) NOT NULL UNIQUE,
    study_name VARCHAR(255) NOT NULL,
    protocol_number VARCHAR(100) UNIQUE,
    phase study_phase,
    therapeutic_area VARCHAR(100),
    indication VARCHAR(255),
    sponsor VARCHAR(255),
    status study_status DEFAULT 'PLANNING',
    start_date DATE,
    planned_end_date DATE,
    actual_end_date DATE,
    target_enrollment INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE studies IS 'Clinical trial master table containing study-level information';
COMMENT ON COLUMN studies.study_code IS 'Unique study identifier (e.g., Study 1)';
COMMENT ON COLUMN studies.protocol_number IS 'Official protocol number';

-- -----------------------------------------------------
-- Table: regions
-- Description: Geographic regions for site grouping
-- -----------------------------------------------------
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    region_code VARCHAR(20) NOT NULL UNIQUE,
    region_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE regions IS 'Geographic regions (e.g., EMEA, AMERICA, APAC)';

-- -----------------------------------------------------
-- Table: countries
-- Description: Countries within regions
-- -----------------------------------------------------
CREATE TABLE countries (
    country_id SERIAL PRIMARY KEY,
    country_code VARCHAR(10) NOT NULL UNIQUE,
    country_name VARCHAR(100) NOT NULL,
    region_id INTEGER NOT NULL REFERENCES regions(region_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE countries IS 'Countries where trials are conducted';

-- -----------------------------------------------------
-- Table: sites
-- Description: Investigational sites
-- -----------------------------------------------------
CREATE TABLE sites (
    site_id SERIAL PRIMARY KEY,
    site_number VARCHAR(50) NOT NULL,
    site_name VARCHAR(255),
    study_id INTEGER NOT NULL REFERENCES studies(study_id) ON DELETE CASCADE,
    country_id INTEGER NOT NULL REFERENCES countries(country_id),
    institution_name VARCHAR(255),
    principal_investigator VARCHAR(255),
    pi_email VARCHAR(255),
    address TEXT,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    activation_date DATE,
    closure_date DATE,
    target_enrollment INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_id, site_number)
);

COMMENT ON TABLE sites IS 'Investigational sites participating in trials';
COMMENT ON COLUMN sites.site_number IS 'Site identifier within study (e.g., Site 2)';

-- -----------------------------------------------------
-- Table: users
-- Description: System users (CTT, CRAs, Site Staff, etc.)
-- -----------------------------------------------------
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255), -- For authentication
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    department VARCHAR(100),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'System users including CTT members, CRAs, and site staff';

-- -----------------------------------------------------
-- Table: user_site_assignments
-- Description: Many-to-many relationship between users and sites
-- -----------------------------------------------------
CREATE TABLE user_site_assignments (
    assignment_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    role_at_site VARCHAR(50),
    assigned_date DATE DEFAULT CURRENT_DATE,
    unassigned_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, site_id)
);

COMMENT ON TABLE user_site_assignments IS 'Assignment of users (CRAs, CTAs) to sites';

-- =====================================================
-- 2. SUBJECT & VISIT MANAGEMENT
-- =====================================================

-- -----------------------------------------------------
-- Table: subjects
-- Description: Study subjects/patients
-- -----------------------------------------------------
CREATE TABLE subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_number VARCHAR(50) NOT NULL,
    study_id INTEGER NOT NULL REFERENCES studies(study_id) ON DELETE CASCADE,
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    status subject_status DEFAULT 'SCREENING',
    screening_date DATE,
    screening_number VARCHAR(50),
    enrollment_date DATE,
    randomization_date DATE,
    randomization_number VARCHAR(50),
    treatment_arm VARCHAR(100),
    completion_date DATE,
    discontinuation_date DATE,
    discontinuation_reason TEXT,
    latest_visit VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_id, subject_number)
);

COMMENT ON TABLE subjects IS 'Study subjects/patients enrolled in trials';
COMMENT ON COLUMN subjects.subject_number IS 'Subject identifier (e.g., Subject 2)';

-- -----------------------------------------------------
-- Table: visits
-- Description: Subject visits
-- -----------------------------------------------------
CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_name VARCHAR(100) NOT NULL,
    visit_code VARCHAR(50),
    visit_number INTEGER,
    scheduled_date DATE,
    actual_date DATE,
    visit_window_start DATE,
    visit_window_end DATE,
    status visit_status DEFAULT 'SCHEDULED',
    is_unscheduled BOOLEAN DEFAULT FALSE,
    source_system VARCHAR(50), -- J-review, Rave EDC, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE visits IS 'Subject visits (Screening, W2D7, Follow-up, etc.)';
COMMENT ON COLUMN visits.visit_name IS 'Visit name (e.g., Screening, W2D7, End of Treatment)';

-- -----------------------------------------------------
-- Table: visit_projections
-- Description: Projected/missing visits from Visit Projection Tracker
-- -----------------------------------------------------
CREATE TABLE visit_projections (
    projection_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_name VARCHAR(100) NOT NULL,
    projected_date DATE NOT NULL,
    days_outstanding INTEGER,
    status VARCHAR(50) DEFAULT 'PENDING',
    actual_visit_id INTEGER REFERENCES visits(visit_id),
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE visit_projections IS 'Missing/projected visits from Visit Projection Tracker';

-- =====================================================
-- 3. EDC & CRF MANAGEMENT
-- =====================================================

-- -----------------------------------------------------
-- Table: forms
-- Description: CRF form definitions
-- -----------------------------------------------------
CREATE TABLE forms (
    form_id SERIAL PRIMARY KEY,
    form_oid VARCHAR(100) NOT NULL,
    form_name VARCHAR(255) NOT NULL,
    study_id INTEGER NOT NULL REFERENCES studies(study_id) ON DELETE CASCADE,
    category VARCHAR(100),
    is_log_form BOOLEAN DEFAULT FALSE,
    requires_signature BOOLEAN DEFAULT FALSE,
    requires_sdv BOOLEAN DEFAULT FALSE,
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(study_id, form_oid)
);

COMMENT ON TABLE forms IS 'CRF form definitions for each study';

-- -----------------------------------------------------
-- Table: form_fields
-- Description: Fields within forms
-- -----------------------------------------------------
CREATE TABLE form_fields (
    field_id SERIAL PRIMARY KEY,
    form_id INTEGER NOT NULL REFERENCES forms(form_id) ON DELETE CASCADE,
    field_oid VARCHAR(100) NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50), -- TEXT, NUMBER, DATE, DATETIME, etc.
    is_required BOOLEAN DEFAULT FALSE,
    validation_rules TEXT,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE form_fields IS 'Field definitions within CRF forms';

-- -----------------------------------------------------
-- Table: crf_pages
-- Description: CRF data pages (instances of forms for subjects)
-- -----------------------------------------------------
CREATE TABLE crf_pages (
    page_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    form_id INTEGER NOT NULL REFERENCES forms(form_id),
    folder_name VARCHAR(255),
    page_name VARCHAR(255),
    log_number INTEGER, -- For log forms
    page_status VARCHAR(50) DEFAULT 'NOT_ENTERED', -- NOT_ENTERED, ENTERED, VERIFIED, FROZEN, LOCKED
    entry_date TIMESTAMP,
    entry_user_id INTEGER REFERENCES users(user_id),
    require_signature BOOLEAN DEFAULT FALSE,
    signature_status signature_status DEFAULT 'NOT_REQUIRED',
    sdv_status verification_status DEFAULT 'NOT_APPLICABLE',
    is_frozen BOOLEAN DEFAULT FALSE,
    freeze_date TIMESTAMP,
    frozen_by INTEGER REFERENCES users(user_id),
    is_locked BOOLEAN DEFAULT FALSE,
    lock_date TIMESTAMP,
    locked_by INTEGER REFERENCES users(user_id),
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    verified_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE crf_pages IS 'CRF data page instances for each subject-visit-form combination';

-- -----------------------------------------------------
-- Table: missing_pages
-- Description: Missing CRF pages report
-- -----------------------------------------------------
CREATE TABLE missing_pages (
    missing_page_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    form_id INTEGER REFERENCES forms(form_id),
    page_name VARCHAR(255) NOT NULL,
    visit_name VARCHAR(100),
    visit_date DATE,
    subject_status subject_status,
    days_missing INTEGER,
    report_type VARCHAR(50), -- ALL_PAGES_MISSING, VISIT_LEVEL
    report_date DATE DEFAULT CURRENT_DATE,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE missing_pages IS 'Missing CRF pages from Missing Pages Report';

-- -----------------------------------------------------
-- Table: inactivated_records
-- Description: Inactivated forms, folders, and records
-- -----------------------------------------------------
CREATE TABLE inactivated_records (
    record_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    folder_name VARCHAR(255),
    form_name VARCHAR(255),
    data_on_form TEXT,
    record_position INTEGER, -- LogLine number
    audit_action VARCHAR(255), -- Action that was taken
    inactivation_date TIMESTAMP,
    inactivated_by INTEGER REFERENCES users(user_id),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE inactivated_records IS 'Tracks inactivated forms, folders, and log records';

-- =====================================================
-- 4. DATA QUALITY & QUERIES
-- =====================================================

-- -----------------------------------------------------
-- Table: data_queries
-- Description: EDC query management
-- -----------------------------------------------------
CREATE TABLE data_queries (
    query_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    form_id INTEGER REFERENCES forms(form_id),
    page_id INTEGER REFERENCES crf_pages(page_id),
    field_oid VARCHAR(100),
    log_number INTEGER,
    query_text TEXT NOT NULL,
    query_status query_status DEFAULT 'OPEN',
    action_owner query_owner DEFAULT 'SITE_REVIEW',
    marking_group VARCHAR(100),
    open_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_date TIMESTAMP,
    response_text TEXT,
    close_date TIMESTAMP,
    days_open INTEGER,
    opened_by INTEGER REFERENCES users(user_id),
    responded_by INTEGER REFERENCES users(user_id),
    closed_by INTEGER REFERENCES users(user_id),
    query_repeat_key VARCHAR(255), -- For identifying same query opened multiple times
    is_system_query BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE data_queries IS 'Data queries from EDC system (Query Report)';
COMMENT ON COLUMN data_queries.days_open IS 'Automatically calculated days the query has been open';

-- -----------------------------------------------------
-- Table: sdv_records
-- Description: Source data verification records
-- -----------------------------------------------------
CREATE TABLE sdv_records (
    sdv_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    page_id INTEGER REFERENCES crf_pages(page_id),
    form_name VARCHAR(255),
    folder_name VARCHAR(255),
    visit_date DATE,
    verification_status verification_status DEFAULT 'REQUIRE_VERIFICATION',
    verified_by INTEGER REFERENCES users(user_id),
    verification_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sdv_records IS 'Source Data Verification tracking (SDV Report)';

-- -----------------------------------------------------
-- Table: pi_signatures
-- Description: PI signature tracking
-- -----------------------------------------------------
CREATE TABLE pi_signatures (
    signature_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    page_id INTEGER REFERENCES crf_pages(page_id),
    form_name VARCHAR(255),
    visit_name VARCHAR(100),
    require_signature VARCHAR(50), -- 'Yes', 'No', 'Yes - Broken Signature'
    is_signature_broken BOOLEAN DEFAULT FALSE,
    audit_action TEXT,
    visit_date DATE,
    page_entry_date DATE,
    last_signature_date DATE,
    days_pending INTEGER,
    pending_category VARCHAR(50), -- '>45 days', '30-45 days', '<30 days'
    signed_date TIMESTAMP,
    signed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE pi_signatures IS 'PI Signature tracking and status (PI Signature Report)';

-- =====================================================
-- 5. PROTOCOL DEVIATIONS & SAFETY
-- =====================================================

-- -----------------------------------------------------
-- Table: protocol_deviations
-- Description: Protocol deviation tracking
-- -----------------------------------------------------
CREATE TABLE protocol_deviations (
    deviation_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    form_id INTEGER REFERENCES forms(form_id),
    folder_name VARCHAR(255),
    page_name VARCHAR(255),
    log_number INTEGER,
    deviation_status deviation_status DEFAULT 'PD_PROPOSED',
    deviation_category VARCHAR(100),
    deviation_subcategory VARCHAR(100),
    deviation_description TEXT,
    visit_date DATE,
    reported_date DATE,
    confirmed_date DATE,
    impact_assessment TEXT,
    corrective_action TEXT,
    preventive_action TEXT,
    reported_by INTEGER REFERENCES users(user_id),
    confirmed_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE protocol_deviations IS 'Protocol deviation tracking (Protocol Deviation Report)';

-- -----------------------------------------------------
-- Table: adverse_events
-- Description: Adverse events (general)
-- -----------------------------------------------------
CREATE TABLE adverse_events (
    ae_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    ae_number INTEGER,
    ae_term VARCHAR(255) NOT NULL,
    ae_verbatim TEXT,
    ae_severity ae_severity,
    ae_seriousness ae_seriousness DEFAULT 'NON_SERIOUS',
    onset_date DATE,
    resolution_date DATE,
    ongoing BOOLEAN DEFAULT TRUE,
    outcome VARCHAR(100),
    relationship_to_study_drug ae_relationship,
    action_taken TEXT,
    treatment_required BOOLEAN,
    hospitalization_required BOOLEAN,
    meddra_pt VARCHAR(255), -- Preferred term
    meddra_soc VARCHAR(255), -- System organ class
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE adverse_events IS 'Adverse events reported for subjects';

-- -----------------------------------------------------
-- Table: sae_records
-- Description: Serious adverse events from eSAE Dashboard
-- -----------------------------------------------------
CREATE TABLE sae_records (
    sae_id SERIAL PRIMARY KEY,
    discrepancy_id VARCHAR(100) UNIQUE,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    ae_id INTEGER REFERENCES adverse_events(ae_id),
    form_name VARCHAR(255),
    case_status VARCHAR(50),
    discrepancy_created_date TIMESTAMP,
    review_status VARCHAR(50), -- Pending Review, Reviewed, etc.
    action_status VARCHAR(50), -- Open, In Progress, Closed
    report_type VARCHAR(50), -- DM_REPORT, SAFETY_REPORT
    dm_review_date TIMESTAMP,
    dm_reviewer INTEGER REFERENCES users(user_id),
    safety_review_date TIMESTAMP,
    safety_reviewer INTEGER REFERENCES users(user_id),
    resolution_date TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sae_records IS 'SAE discrepancies from eSAE Dashboard (DM & Safety Reports)';

-- =====================================================
-- 6. LABORATORY & CODING
-- =====================================================

-- -----------------------------------------------------
-- Table: lab_results
-- Description: Laboratory results
-- -----------------------------------------------------
CREATE TABLE lab_results (
    lab_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    lab_date DATE,
    lab_category VARCHAR(100),
    test_name VARCHAR(255) NOT NULL,
    test_description TEXT,
    result_value DECIMAL(15,5),
    result_text VARCHAR(255), -- For non-numeric results
    result_unit VARCHAR(50),
    normal_range_low DECIMAL(15,5),
    normal_range_high DECIMAL(15,5),
    flag VARCHAR(20), -- HIGH, LOW, NORMAL, ABNORMAL
    is_clinically_significant BOOLEAN,
    lab_name VARCHAR(255),
    lab_accession_number VARCHAR(100),
    collection_datetime TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE lab_results IS 'Laboratory test results for subjects';

-- -----------------------------------------------------
-- Table: missing_lab_data
-- Description: Missing lab names and ranges
-- -----------------------------------------------------
CREATE TABLE missing_lab_data (
    missing_lab_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(visit_id),
    form_name VARCHAR(255),
    lab_category VARCHAR(100),
    lab_date DATE,
    test_name VARCHAR(255),
    test_description TEXT,
    issue_type VARCHAR(100), -- 'Missing Lab Name', 'Missing Range', 'Missing Both'
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_date DATE,
    report_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE missing_lab_data IS 'Missing lab names/ranges from Lab Report';

-- -----------------------------------------------------
-- Table: coding_records
-- Description: Medical/drug coding (MedDRA, WHODD)
-- -----------------------------------------------------
CREATE TABLE coding_records (
    coding_id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    dictionary_type VARCHAR(20) NOT NULL, -- 'MedDRA', 'WHODD'
    dictionary_version VARCHAR(50),
    form_oid VARCHAR(100),
    form_name VARCHAR(255),
    log_line INTEGER,
    field_oid VARCHAR(100),
    verbatim_term TEXT NOT NULL,
    coded_term TEXT,
    coding_status coding_status DEFAULT 'REQUIRES_CODING',
    require_coding VARCHAR(10), -- 'Yes', 'No'
    -- MedDRA specific fields
    meddra_pt VARCHAR(255),
    meddra_pt_code VARCHAR(20),
    meddra_llt VARCHAR(255),
    meddra_soc VARCHAR(255),
    meddra_hlgt VARCHAR(255),
    meddra_hlt VARCHAR(255),
    -- WHO Drug specific fields
    drug_name VARCHAR(255),
    atc_code VARCHAR(20),
    atc_text VARCHAR(255),
    coded_date TIMESTAMP,
    coded_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE coding_records IS 'Medical/drug coding records (MedDRA, WHODD GlobalCodingReport)';

-- =====================================================
-- 7. OPERATIONAL METRICS & ANALYTICS
-- =====================================================

-- -----------------------------------------------------
-- Table: edrr_issues
-- Description: Open issues summary (EDRR Compiled Report)
-- -----------------------------------------------------
CREATE TABLE edrr_issues (
    issue_id SERIAL PRIMARY KEY,
    study_id INTEGER NOT NULL REFERENCES studies(study_id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    open_issue_count INTEGER NOT NULL,
    issue_categories JSONB, -- Breakdown by category
    report_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE edrr_issues IS 'Open issues summary per subject from EDRR Report';

-- -----------------------------------------------------
-- Table: operational_metrics
-- Description: Aggregated site/study operational metrics
-- -----------------------------------------------------
CREATE TABLE operational_metrics (
    metric_id SERIAL PRIMARY KEY,
    study_id INTEGER NOT NULL REFERENCES studies(study_id) ON DELETE CASCADE,
    site_id INTEGER REFERENCES sites(site_id),
    metric_date DATE NOT NULL,
    -- Subject metrics
    total_subjects INTEGER DEFAULT 0,
    subjects_screening INTEGER DEFAULT 0,
    subjects_enrolled INTEGER DEFAULT 0,
    subjects_completed INTEGER DEFAULT 0,
    subjects_discontinued INTEGER DEFAULT 0,
    -- Query metrics
    total_queries_open INTEGER DEFAULT 0,
    total_queries_closed INTEGER DEFAULT 0,
    queries_site_action INTEGER DEFAULT 0,
    queries_cra_action INTEGER DEFAULT 0,
    avg_query_age_days DECIMAL(10,2),
    avg_query_resolution_days DECIMAL(10,2),
    -- SDV metrics
    pages_requiring_sdv INTEGER DEFAULT 0,
    pages_sdv_complete INTEGER DEFAULT 0,
    sdv_completion_rate DECIMAL(5,2),
    -- Signature metrics
    pages_requiring_signature INTEGER DEFAULT 0,
    pages_signature_complete INTEGER DEFAULT 0,
    pages_signature_broken INTEGER DEFAULT 0,
    -- Data quality metrics
    missing_pages_count INTEGER DEFAULT 0,
    protocol_deviations_count INTEGER DEFAULT 0,
    open_sae_discrepancies INTEGER DEFAULT 0,
    overdue_visits_count INTEGER DEFAULT 0,
    -- Coding metrics
    pending_meddra_coding INTEGER DEFAULT 0,
    pending_whodd_coding INTEGER DEFAULT 0,
    -- Freeze/Lock metrics
    pages_frozen INTEGER DEFAULT 0,
    pages_locked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE operational_metrics IS 'Daily aggregated operational metrics per site/study';

-- Create unique constraint for daily site metrics
CREATE UNIQUE INDEX idx_operational_metrics_daily 
ON operational_metrics(study_id, COALESCE(site_id, 0), metric_date);

-- -----------------------------------------------------
-- Table: audit_logs
-- Description: System audit trail
-- -----------------------------------------------------
CREATE TABLE audit_logs (
    audit_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[], -- List of changed column names
    user_id INTEGER REFERENCES users(user_id),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE audit_logs IS 'Complete audit trail of all data changes';

-- =====================================================
-- 8. AI/ML INTEGRATION TABLES
-- =====================================================

-- -----------------------------------------------------
-- Table: ai_insights
-- Description: AI-generated insights
-- -----------------------------------------------------
CREATE TABLE ai_insights (
    insight_id SERIAL PRIMARY KEY,
    study_id INTEGER REFERENCES studies(study_id),
    site_id INTEGER REFERENCES sites(site_id),
    subject_id INTEGER REFERENCES subjects(subject_id),
    insight_type insight_type NOT NULL,
    insight_category VARCHAR(100),
    insight_title VARCHAR(255),
    insight_text TEXT NOT NULL,
    supporting_data JSONB, -- Evidence/data supporting the insight
    confidence_score DECIMAL(5,4), -- 0.0000 to 1.0000
    priority priority_level DEFAULT 'MEDIUM',
    is_actionable BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'NEW', -- NEW, REVIEWED, RESOLVED, DISMISSED
    reviewed_by INTEGER REFERENCES users(user_id),
    reviewed_at TIMESTAMP,
    resolution_notes TEXT,
    ml_model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_insights IS 'AI/ML generated insights for proactive issue detection';

-- -----------------------------------------------------
-- Table: ai_recommendations
-- Description: AI-generated recommendations
-- -----------------------------------------------------
CREATE TABLE ai_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    insight_id INTEGER REFERENCES ai_insights(insight_id),
    recommendation_text TEXT NOT NULL,
    recommendation_type VARCHAR(100),
    estimated_impact VARCHAR(255),
    implementation_effort VARCHAR(50), -- LOW, MEDIUM, HIGH
    estimated_time_savings_hours DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, ACCEPTED, REJECTED, IMPLEMENTED
    accepted_by INTEGER REFERENCES users(user_id),
    accepted_at TIMESTAMP,
    implemented_by INTEGER REFERENCES users(user_id),
    implemented_at TIMESTAMP,
    feedback_score INTEGER, -- 1-5 rating
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_recommendations IS 'AI-generated recommendations for operational improvements';

-- -----------------------------------------------------
-- Table: chat_history
-- Description: AI chat/collaboration history for agentic AI
-- -----------------------------------------------------
CREATE TABLE chat_history (
    chat_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    session_id UUID DEFAULT uuid_generate_v4(),
    study_id INTEGER REFERENCES studies(study_id),
    site_id INTEGER REFERENCES sites(site_id),
    subject_id INTEGER REFERENCES subjects(subject_id),
    message_role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    message_content TEXT NOT NULL,
    context_data JSONB, -- Additional context passed to AI
    related_insight_id INTEGER REFERENCES ai_insights(insight_id),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE chat_history IS 'AI chat history for intelligent collaboration features';

-- =====================================================
-- 9. DATA INGESTION TRACKING
-- =====================================================

-- -----------------------------------------------------
-- Table: data_sources
-- Description: External data source definitions
-- -----------------------------------------------------
CREATE TABLE data_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50), -- EDC, LAB, IRT, SAFETY, MONITORING
    connection_details JSONB, -- Encrypted connection info
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_date TIMESTAMP,
    sync_frequency_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE data_sources IS 'External data sources for ingestion';

-- -----------------------------------------------------
-- Table: ingestion_jobs
-- Description: Data ingestion job tracking
-- -----------------------------------------------------
CREATE TABLE ingestion_jobs (
    job_id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES data_sources(source_id),
    study_id INTEGER REFERENCES studies(study_id),
    job_type VARCHAR(50), -- FULL, INCREMENTAL, DELTA
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_log TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    file_path VARCHAR(500), -- If ingesting from file
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ingestion_jobs IS 'Track data ingestion jobs and their status';

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Studies
CREATE INDEX idx_studies_status ON studies(status);
CREATE INDEX idx_studies_therapeutic_area ON studies(therapeutic_area);

-- Sites
CREATE INDEX idx_sites_study ON sites(study_id);
CREATE INDEX idx_sites_country ON sites(country_id);
CREATE INDEX idx_sites_status ON sites(status);

-- Subjects
CREATE INDEX idx_subjects_study ON subjects(study_id);
CREATE INDEX idx_subjects_site ON subjects(site_id);
CREATE INDEX idx_subjects_status ON subjects(status);
CREATE INDEX idx_subjects_number ON subjects(subject_number);

-- Visits
CREATE INDEX idx_visits_subject ON visits(subject_id);
CREATE INDEX idx_visits_status ON visits(status);
CREATE INDEX idx_visits_date ON visits(actual_date);

-- CRF Pages
CREATE INDEX idx_crf_pages_subject ON crf_pages(subject_id);
CREATE INDEX idx_crf_pages_visit ON crf_pages(visit_id);
CREATE INDEX idx_crf_pages_form ON crf_pages(form_id);
CREATE INDEX idx_crf_pages_status ON crf_pages(page_status);

-- Data Queries
CREATE INDEX idx_queries_subject ON data_queries(subject_id);
CREATE INDEX idx_queries_status ON data_queries(query_status);
CREATE INDEX idx_queries_owner ON data_queries(action_owner);
CREATE INDEX idx_queries_open_date ON data_queries(open_date);

-- SDV Records
CREATE INDEX idx_sdv_subject ON sdv_records(subject_id);
CREATE INDEX idx_sdv_status ON sdv_records(verification_status);

-- Protocol Deviations
CREATE INDEX idx_pd_subject ON protocol_deviations(subject_id);
CREATE INDEX idx_pd_status ON protocol_deviations(deviation_status);

-- SAE Records
CREATE INDEX idx_sae_subject ON sae_records(subject_id);
CREATE INDEX idx_sae_review_status ON sae_records(review_status);

-- Coding Records
CREATE INDEX idx_coding_subject ON coding_records(subject_id);
CREATE INDEX idx_coding_status ON coding_records(coding_status);
CREATE INDEX idx_coding_dictionary ON coding_records(dictionary_type);

-- AI Insights
CREATE INDEX idx_insights_study ON ai_insights(study_id);
CREATE INDEX idx_insights_site ON ai_insights(site_id);
CREATE INDEX idx_insights_type ON ai_insights(insight_type);
CREATE INDEX idx_insights_priority ON ai_insights(priority);
CREATE INDEX idx_insights_status ON ai_insights(status);

-- Audit Logs
CREATE INDEX idx_audit_table ON audit_logs(table_name);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMPS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_studies_modtime BEFORE UPDATE ON studies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sites_modtime BEFORE UPDATE ON sites FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subjects_modtime BEFORE UPDATE ON subjects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_visits_modtime BEFORE UPDATE ON visits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_crf_pages_modtime BEFORE UPDATE ON crf_pages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_queries_modtime BEFORE UPDATE ON data_queries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sdv_modtime BEFORE UPDATE ON sdv_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pi_sig_modtime BEFORE UPDATE ON pi_signatures FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pd_modtime BEFORE UPDATE ON protocol_deviations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ae_modtime BEFORE UPDATE ON adverse_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sae_modtime BEFORE UPDATE ON sae_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_coding_modtime BEFORE UPDATE ON coding_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sources_modtime BEFORE UPDATE ON data_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS FOR COMMON ANALYTICS
-- =====================================================

-- View: Site-level data quality summary
CREATE OR REPLACE VIEW v_site_data_quality AS
SELECT 
    s.study_id,
    st.study_code,
    s.site_id,
    s.site_number,
    c.country_code,
    r.region_code,
    COUNT(DISTINCT sub.subject_id) AS total_subjects,
    SUM(CASE WHEN sub.status = 'ENROLLED' THEN 1 ELSE 0 END) AS enrolled_subjects,
    (SELECT COUNT(*) FROM data_queries q 
     JOIN subjects sub2 ON q.subject_id = sub2.subject_id 
     WHERE sub2.site_id = s.site_id AND q.query_status = 'OPEN') AS open_queries,
    (SELECT AVG(q.days_open) FROM data_queries q 
     JOIN subjects sub2 ON q.subject_id = sub2.subject_id 
     WHERE sub2.site_id = s.site_id AND q.query_status = 'OPEN') AS avg_query_age
FROM sites s
JOIN studies st ON s.study_id = st.study_id
JOIN countries c ON s.country_id = c.country_id
JOIN regions r ON c.region_id = r.region_id
LEFT JOIN subjects sub ON s.site_id = sub.site_id
GROUP BY s.study_id, st.study_code, s.site_id, s.site_number, c.country_code, r.region_code;

-- View: Subject-level metrics summary
CREATE OR REPLACE VIEW v_subject_metrics AS
SELECT 
    sub.subject_id,
    sub.subject_number,
    sub.status,
    st.study_code,
    s.site_number,
    c.country_code,
    r.region_code,
    sub.latest_visit,
    (SELECT COUNT(*) FROM data_queries WHERE subject_id = sub.subject_id AND query_status = 'OPEN') AS open_queries,
    (SELECT COUNT(*) FROM missing_pages WHERE subject_id = sub.subject_id AND is_resolved = FALSE) AS missing_pages,
    (SELECT COUNT(*) FROM protocol_deviations WHERE subject_id = sub.subject_id) AS protocol_deviations,
    (SELECT COUNT(*) FROM pi_signatures WHERE subject_id = sub.subject_id AND require_signature LIKE 'Yes%' 
     AND signed_date IS NULL) AS pending_signatures
FROM subjects sub
JOIN studies st ON sub.study_id = st.study_id
JOIN sites s ON sub.site_id = s.site_id
JOIN countries c ON s.country_id = c.country_id
JOIN regions r ON c.region_id = r.region_id;

-- =====================================================
-- GRANT STATEMENTS (adjust roles as needed)
-- =====================================================

-- Create application roles
-- CREATE ROLE clinical_read;
-- CREATE ROLE clinical_write;
-- CREATE ROLE clinical_admin;

-- Grant read access
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO clinical_read;

-- Grant write access
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO clinical_write;

-- Grant admin access
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clinical_admin;

-- =====================================================
-- End of Schema
-- =====================================================
