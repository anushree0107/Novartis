
-- Insert Regions
INSERT INTO regions (region_code, region_name) VALUES
    ('EMEA', 'Europe, Middle East & Africa'),
    ('AMERICA', 'Americas'),
    ('APAC', 'Asia Pacific');

-- Insert Countries
INSERT INTO countries (country_code, country_name, region_id) VALUES
    ('FRA', 'France', (SELECT region_id FROM regions WHERE region_code = 'EMEA')),
    ('DEU', 'Germany', (SELECT region_id FROM regions WHERE region_code = 'EMEA')),
    ('GBR', 'United Kingdom', (SELECT region_id FROM regions WHERE region_code = 'EMEA')),
    ('ESP', 'Spain', (SELECT region_id FROM regions WHERE region_code = 'EMEA')),
    ('ITA', 'Italy', (SELECT region_id FROM regions WHERE region_code = 'EMEA')),
    ('USA', 'United States', (SELECT region_id FROM regions WHERE region_code = 'AMERICA')),
    ('CAN', 'Canada', (SELECT region_id FROM regions WHERE region_code = 'AMERICA')),
    ('BRA', 'Brazil', (SELECT region_id FROM regions WHERE region_code = 'AMERICA')),
    ('JPN', 'Japan', (SELECT region_id FROM regions WHERE region_code = 'APAC')),
    ('AUS', 'Australia', (SELECT region_id FROM regions WHERE region_code = 'APAC')),
    ('IND', 'India', (SELECT region_id FROM regions WHERE region_code = 'APAC'));

-- Insert Studies (matching the 25 studies in dataset)
INSERT INTO studies (study_code, study_name, protocol_number, phase, therapeutic_area, indication, sponsor, status, start_date, target_enrollment) VALUES
    ('Study 1', 'Phase III Oncology Trial - Study 1', 'PROT-001', 'Phase III', 'Oncology', 'Solid Tumors', 'Novartis', 'ACTIVE', '2022-01-15', 500),
    ('Study 2', 'Phase II Immunology Trial - Study 2', 'PROT-002', 'Phase II', 'Immunology', 'Autoimmune Disease', 'Novartis', 'ACTIVE', '2022-03-20', 300),
    ('Study 4', 'Phase III Cardiology Trial - Study 4', 'PROT-004', 'Phase III', 'Cardiology', 'Heart Failure', 'Novartis', 'ACTIVE', '2022-05-10', 600),
    ('Study 5', 'Phase II Neurology Trial - Study 5', 'PROT-005', 'Phase II', 'Neurology', 'Multiple Sclerosis', 'Novartis', 'ACTIVE', '2022-06-01', 250),
    ('Study 6', 'Phase III Respiratory Trial - Study 6', 'PROT-006', 'Phase III', 'Respiratory', 'COPD', 'Novartis', 'ENROLLING', '2023-01-15', 450),
    ('Study 7', 'Phase II Dermatology Trial - Study 7', 'PROT-007', 'Phase II', 'Dermatology', 'Psoriasis', 'Novartis', 'ACTIVE', '2023-02-20', 200),
    ('Study 8', 'Phase III Ophthalmology Trial - Study 8', 'PROT-008', 'Phase III', 'Ophthalmology', 'Macular Degeneration', 'Novartis', 'ACTIVE', '2023-03-10', 400),
    ('Study 9', 'Phase II Hematology Trial - Study 9', 'PROT-009', 'Phase II', 'Hematology', 'Leukemia', 'Novartis', 'ACTIVE', '2023-04-05', 180),
    ('Study 10', 'Phase III Endocrinology Trial - Study 10', 'PROT-010', 'Phase III', 'Endocrinology', 'Diabetes', 'Novartis', 'ACTIVE', '2023-05-15', 550),
    ('Study 11', 'Phase II Gastroenterology Trial - Study 11', 'PROT-011', 'Phase II', 'Gastroenterology', 'Crohns Disease', 'Novartis', 'ENROLLING', '2023-06-20', 220);

-- Insert Users
INSERT INTO users (username, email, full_name, role, department, is_active) VALUES
    ('jsmith', 'john.smith@novartis.com', 'John Smith', 'CTT', 'Clinical Operations', TRUE),
    ('amartinez', 'ana.martinez@novartis.com', 'Ana Martinez', 'CRA', 'Clinical Operations', TRUE),
    ('bwilson', 'brian.wilson@novartis.com', 'Brian Wilson', 'CRA', 'Clinical Operations', TRUE),
    ('cjohnson', 'claire.johnson@novartis.com', 'Claire Johnson', 'DATA_MANAGER', 'Data Management', TRUE),
    ('dlee', 'david.lee@novartis.com', 'David Lee', 'MEDICAL_MONITOR', 'Medical Affairs', TRUE),
    ('ekumar', 'esha.kumar@novartis.com', 'Esha Kumar', 'SAFETY_PHYSICIAN', 'Safety', TRUE),
    ('fgarcia', 'fernando.garcia@novartis.com', 'Fernando Garcia', 'CTA', 'Clinical Operations', TRUE),
    ('gchen', 'grace.chen@novartis.com', 'Grace Chen', 'CTT', 'Clinical Operations', TRUE),
    ('hpatel', 'harsh.patel@site18.com', 'Dr. Harsh Patel', 'SITE_STAFF', 'Site 18', TRUE),
    ('ischneider', 'ingrid.schneider@site2.com', 'Dr. Ingrid Schneider', 'SITE_STAFF', 'Site 2', TRUE);

-- Insert Sites for Study 1 (matching dataset)
INSERT INTO sites (site_number, site_name, study_id, country_id, institution_name, principal_investigator, status, activation_date, target_enrollment) VALUES
    ('Site 2', 'Paris Cancer Center', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'FRA'), 'Institut Curie', 'Dr. Ingrid Schneider', 'ACTIVE', '2022-02-01', 50),
    ('Site 18', 'Boston Medical Center', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'USA'), 'Massachusetts General Hospital', 'Dr. Harsh Patel', 'ACTIVE', '2022-02-15', 60),
    ('Site 19', 'New York Oncology Clinic', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'USA'), 'Memorial Sloan Kettering', 'Dr. Sarah Thompson', 'ACTIVE', '2022-03-01', 55),
    ('Site 3', 'Munich University Hospital', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'DEU'), 'LMU Klinikum', 'Dr. Hans Mueller', 'ACTIVE', '2022-03-15', 45),
    ('Site 5', 'London Research Institute', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'GBR'), 'Royal Marsden Hospital', 'Dr. James Williams', 'ACTIVE', '2022-04-01', 50),
    ('Site 10', 'Tokyo Cancer Center', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT country_id FROM countries WHERE country_code = 'JPN'), 'National Cancer Center', 'Dr. Yuki Tanaka', 'ACTIVE', '2022-04-15', 40);

-- =====================================================
-- 2. SUBJECTS
-- =====================================================

-- Insert Subjects (matching dataset patterns: Subject 2, Subject 3, etc.)
INSERT INTO subjects (subject_number, study_id, site_id, status, screening_date, enrollment_date, latest_visit) VALUES
    ('Subject 2', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 2' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'ON_TREATMENT', '2022-07-10', '2022-07-13', 'W7D5'),
    ('Subject 3', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 2' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'ON_TREATMENT', '2023-06-25', '2023-06-29', 'W7D5'),
    ('Subject 4', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 2' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'ON_TREATMENT', '2024-11-01', '2024-11-05', 'W2D7'),
    ('Subject 63', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 18' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'COMPLETED', '2023-01-15', '2023-01-20', 'Follow-up_Week 32'),
    ('Subject 64', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 18' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'ON_TREATMENT', '2023-08-20', '2023-08-28', 'End of Treatment'),
    ('Subject 65', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 18' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'ON_TREATMENT', '2023-10-01', '2023-10-04', 'W14D3'),
    ('Subject 80', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT site_id FROM sites WHERE site_number = 'Site 19' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')), 'SCREENING', '2025-09-05', NULL, 'Screening');

-- =====================================================
-- 3. FORMS & VISITS
-- =====================================================

-- Insert Forms
INSERT INTO forms (form_oid, form_name, study_id, category, is_log_form, requires_signature, requires_sdv) VALUES
    ('FORM_001', 'Form 1', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Demographics', FALSE, TRUE, TRUE),
    ('FORM_002', 'Form 2', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Informed Consent', FALSE, TRUE, TRUE),
    ('FORM_036', 'Form 36', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Adverse Events', TRUE, FALSE, TRUE),
    ('FORM_048', 'Form 48', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Disposition', FALSE, TRUE, TRUE),
    ('FORM_099', 'Form 99', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Antineoplastic Therapy-Medication', TRUE, FALSE, TRUE),
    ('FORM_100', 'Form 100', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Antineoplastic Therapy-Radiotherapy', TRUE, FALSE, TRUE),
    ('FORM_101', 'Form 101', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Antineoplastic Therapy-Surgery', TRUE, FALSE, TRUE),
    ('FORM_121', 'Form 121', (SELECT study_id FROM studies WHERE study_code = 'Study 1'), 'Protocol Deviation', TRUE, FALSE, FALSE);

-- Insert Visits for Subject 63 (matching dataset)
INSERT INTO visits (subject_id, visit_name, visit_number, actual_date, status, source_system) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Screening', 1, '2023-01-15', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Baseline', 2, '2023-01-20', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'End of Treatment', 10, '2024-06-12', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Follow-up', 11, '2024-07-03', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Follow-up_Week 16', 12, '2024-10-09', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Follow-up_Week 24', 13, '2024-12-03', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Follow-up_Week 32', 14, '2025-02-12', 'COMPLETED', 'Rave EDC');

-- Insert Visits for Subject 2
INSERT INTO visits (subject_id, visit_name, visit_number, actual_date, status, source_system) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Screening', 1, '2022-07-13', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'W2D7', 3, '2022-08-17', 'COMPLETED', 'Rave EDC'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Adverse Event', 99, NULL, 'COMPLETED', 'Rave EDC');

-- =====================================================
-- 4. DATA QUERIES (from Query Report)
-- =====================================================

INSERT INTO data_queries (subject_id, visit_id, form_id, field_oid, log_number, query_text, query_status, action_owner, marking_group, open_date, days_open) OVERRIDING SYSTEM VALUE VALUES
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'),
        (SELECT visit_id FROM visits WHERE subject_id = (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2') AND visit_name = 'Adverse Event'),
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_001'),
        'AEACN_2', 1, 'Please clarify the adverse event action taken.',
        'OPEN', 'SITE_REVIEW', 'Site from System', '2025-09-29 14:58:04', 46
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'),
        (SELECT visit_id FROM visits WHERE subject_id = (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2') AND visit_name = 'Adverse Event'),
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_001'),
        'AEACN_2', 10, 'Inconsistent data detected. Please verify.',
        'OPEN', 'SITE_REVIEW', 'Site from System', '2025-09-29 14:58:04', 46
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'),
        (SELECT visit_id FROM visits WHERE subject_id = (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2') AND visit_name = 'Adverse Event'),
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_001'),
        'AEACN_7', 12, 'Missing required field. Please complete.',
        'OPEN', 'SITE_REVIEW', 'Site from System', '2025-09-29 14:58:04', 46
    );

-- =====================================================
-- 5. PROTOCOL DEVIATIONS (from Protocol Deviation sheet)
-- =====================================================

INSERT INTO protocol_deviations (subject_id, visit_id, form_id, folder_name, page_name, log_number, deviation_status, visit_date) VALUES
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 64'),
        NULL,
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_121'),
        'Screening', 'Form 121', 5, 'PD_CONFIRMED', '2023-08-28'
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 65'),
        NULL,
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_121'),
        'Screening', 'Form 121', 4, 'PD_CONFIRMED', '2023-10-04'
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 80'),
        NULL,
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_121'),
        'Screening', 'Form 121', 3, 'PD_PROPOSED', '2025-09-08'
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'),
        (SELECT visit_id FROM visits WHERE subject_id = (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2') AND visit_name = 'W2D7'),
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_121'),
        'W2D7', 'Form 121', 1, 'PD_CONFIRMED', '2022-08-17'
    ),
    (
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'),
        NULL,
        (SELECT form_id FROM forms WHERE form_oid = 'FORM_121'),
        'W7D5', 'Form 121', 1, 'PD_CONFIRMED', '2023-08-25'
    );

-- =====================================================
-- 6. SDV RECORDS (from SDV sheet)
-- =====================================================

INSERT INTO sdv_records (subject_id, visit_id, form_name, folder_name, verification_status) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), NULL, 'Form 36', 'Adverse Event', 'REQUIRE_VERIFICATION'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), NULL, 'Form 99', 'Antineoplastic Therapy-Medication', 'VERIFIED'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), NULL, 'Form 100', 'Antineoplastic Therapy-Radiotherapy', 'VERIFIED'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), NULL, 'Form 101', 'Antineoplastic Therapy-Surgery', 'VERIFIED'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), NULL, 'Form 48', 'Disposition', 'VERIFIED');

-- =====================================================
-- 7. PI SIGNATURES (from PI Signature Report)
-- =====================================================

INSERT INTO pi_signatures (subject_id, form_name, visit_name, require_signature, is_signature_broken, audit_action, visit_date, page_entry_date, days_pending, pending_category) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Form 1', 'Screening', 'Yes - Broken Signature', TRUE, 'Amendment Manager: Signature has been broken.', '2022-07-13', '2025-09-29', 46, '>45 days'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Form 2', 'Screening', 'Yes - Broken Signature', TRUE, 'Signature has been broken.', '2022-07-13', '2025-09-29', 46, '>45 days'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 'Form 1', 'Screening', 'Yes - Broken Signature', TRUE, 'Amendment Manager: Signature has been broken.', '2023-06-29', '2025-09-29', 46, '>45 days'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 'Form 2', 'Screening', 'Yes - Broken Signature', TRUE, 'Signature has been broken.', '2023-06-29', '2025-09-29', 46, '>45 days'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 4'), 'Form 1', 'Screening', 'Yes - Broken Signature', TRUE, 'Amendment Manager: Signature has been broken.', '2024-11-05', '2025-09-29', 46, '>45 days');

-- =====================================================
-- 8. CODING RECORDS (from GlobalCodingReport)
-- =====================================================

-- MedDRA Coding
INSERT INTO coding_records (subject_id, dictionary_type, dictionary_version, form_oid, log_line, field_oid, verbatim_term, coding_status, require_coding) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'MedDRA', '26.0', 'AE_FORM', 1, 'AETERM', 'Headache', 'CODED', 'Yes'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'MedDRA', '26.0', 'AE_FORM', 2, 'AETERM', 'Nausea', 'CODED', 'Yes'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 'MedDRA', '26.0', 'AE_FORM', 1, 'AETERM', 'Fatigue', 'REQUIRES_CODING', 'Yes'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'MedDRA', '26.0', 'AE_FORM', 1, 'AETERM', 'Rash', 'CODED', 'Yes');

-- WHODD Coding (Drug Dictionary)
INSERT INTO coding_records (subject_id, dictionary_type, dictionary_version, form_oid, log_line, field_oid, verbatim_term, coding_status, require_coding, drug_name, atc_code) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'WHODD', '2024Q1', 'CM_FORM', 1, 'CMTRT', 'Aspirin', 'CODED', 'Yes', 'Acetylsalicylic acid', 'B01AC06'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'WHODD', '2024Q1', 'CM_FORM', 1, 'CMTRT', 'Tylenol', 'CODED', 'Yes', 'Paracetamol', 'N02BE01'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'WHODD', '2024Q1', 'CM_FORM', 2, 'CMTRT', 'Vitamin D', 'REQUIRES_CODING', 'Yes', NULL, NULL);

-- =====================================================
-- 9. MISSING LAB DATA (from Missing Lab Report)
-- =====================================================

INSERT INTO missing_lab_data (subject_id, form_name, lab_category, lab_date, test_name, test_description, issue_type) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Lab Form', 'Hematology', '2022-08-01', 'WBC', 'White Blood Cell Count', 'Missing Range'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 'Lab Form', 'Chemistry', '2023-07-15', 'Creatinine', 'Serum Creatinine', 'Missing Lab Name'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'Lab Form', 'Hematology', '2024-06-01', 'Hemoglobin', 'Blood Hemoglobin', 'Missing Range');

-- =====================================================
-- 10. MISSING PAGES (from Missing Pages Report)
-- =====================================================

INSERT INTO missing_pages (subject_id, page_name, visit_name, visit_date, subject_status, days_missing, report_type) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'Vital Signs', 'W2D7', '2022-08-17', 'ON_TREATMENT', 15, 'ALL_PAGES_MISSING'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 4'), 'ECG Report', 'Screening', '2024-11-05', 'ON_TREATMENT', 5, 'ALL_PAGES_MISSING'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 80'), 'Lab Results', 'Screening', '2025-09-05', 'SCREENING', 3, 'VISIT_LEVEL');

-- =====================================================
-- 11. VISIT PROJECTIONS (from Visit Projection Tracker)
-- =====================================================

INSERT INTO visit_projections (subject_id, visit_name, projected_date, days_outstanding, status) VALUES
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'W14D3', '2025-10-15', 30, 'PENDING'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 'End of Treatment', '2025-11-01', 15, 'PENDING'),
    ((SELECT subject_id FROM subjects WHERE subject_number = 'Subject 4'), 'W7D5', '2025-12-10', 0, 'PENDING');

-- =====================================================
-- 12. SAE RECORDS (from eSAE Dashboard)
-- =====================================================

INSERT INTO sae_records (discrepancy_id, subject_id, form_name, case_status, discrepancy_created_date, review_status, action_status, report_type) VALUES
    ('DISC-001', (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 'SAE Form', 'Open', '2025-09-15 10:30:00', 'Pending Review', 'Open', 'DM_REPORT'),
    ('DISC-002', (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 63'), 'SAE Form', 'Closed', '2024-06-20 14:45:00', 'Reviewed', 'Closed', 'SAFETY_REPORT'),
    ('DISC-003', (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 64'), 'SAE Form', 'Open', '2025-08-01 09:15:00', 'In Review', 'In Progress', 'DM_REPORT');

-- =====================================================
-- 13. EDRR ISSUES (from Compiled EDRR Report)
-- =====================================================

INSERT INTO edrr_issues (study_id, subject_id, open_issue_count, issue_categories, report_date) VALUES
    ((SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'), 5, '{"queries": 3, "missing_pages": 1, "signatures": 1}', '2025-11-14'),
    ((SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 3'), 2, '{"queries": 1, "coding": 1}', '2025-11-14'),
    ((SELECT study_id FROM studies WHERE study_code = 'Study 1'), (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 80'), 3, '{"queries": 2, "missing_pages": 1}', '2025-11-14');

-- =====================================================
-- 14. AI INSIGHTS (Sample AI-generated insights)
-- =====================================================

INSERT INTO ai_insights (study_id, site_id, subject_id, insight_type, insight_category, insight_title, insight_text, confidence_score, priority, is_actionable, status) VALUES
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        (SELECT site_id FROM sites WHERE site_number = 'Site 2' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')),
        NULL,
        'DATA_QUALITY',
        'Query Resolution',
        'High Query Backlog at Site 2',
        'Site 2 has 15 open queries with an average age of 46 days, significantly above the study average of 12 days. Consider scheduling a training session with site staff on query resolution best practices.',
        0.92,
        'HIGH',
        TRUE,
        'NEW'
    ),
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        (SELECT site_id FROM sites WHERE site_number = 'Site 18' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')),
        NULL,
        'OPERATIONAL',
        'SDV Completion',
        'SDV Completion Rate Improving',
        'Site 18 SDV completion rate has improved from 65% to 89% over the last 30 days. Current trajectory indicates 100% completion by end of month.',
        0.85,
        'MEDIUM',
        FALSE,
        'REVIEWED'
    ),
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        NULL,
        (SELECT subject_id FROM subjects WHERE subject_number = 'Subject 2'),
        'COMPLIANCE',
        'Signature Delays',
        'Multiple Broken Signatures Detected',
        'Subject 2 has 2 forms with broken PI signatures pending for >45 days. This may delay database lock. Recommend immediate follow-up with site.',
        0.95,
        'CRITICAL',
        TRUE,
        'NEW'
    );

-- =====================================================
-- 15. AI RECOMMENDATIONS
-- =====================================================

INSERT INTO ai_recommendations (insight_id, recommendation_text, recommendation_type, estimated_impact, implementation_effort, estimated_time_savings_hours, status) VALUES
    (
        (SELECT insight_id FROM ai_insights WHERE insight_title = 'High Query Backlog at Site 2'),
        'Schedule a 1-hour virtual training session with Site 2 on query resolution procedures and common query types. Provide quick reference guide.',
        'Training',
        'Reduce query resolution time by 50%',
        'LOW',
        20.0,
        'PENDING'
    ),
    (
        (SELECT insight_id FROM ai_insights WHERE insight_title = 'Multiple Broken Signatures Detected'),
        'Send automated reminder email to Site 2 PI regarding pending signatures with direct links to affected forms.',
        'Communication',
        'Resolve signature backlog within 7 days',
        'LOW',
        5.0,
        'PENDING'
    );

-- =====================================================
-- 16. DATA SOURCES
-- =====================================================

INSERT INTO data_sources (source_name, source_type, connection_details, is_active, sync_frequency_minutes) VALUES
    ('Rave EDC', 'EDC', '{"type": "API", "endpoint": "https://rave.medidata.com/api", "version": "v2"}', TRUE, 60),
    ('J-review', 'EDC', '{"type": "API", "endpoint": "https://jreview.internal.com/api"}', TRUE, 120),
    ('Central Lab', 'LAB', '{"type": "SFTP", "host": "lab.secure.com", "path": "/data/results"}', TRUE, 240),
    ('Safety Database', 'SAFETY', '{"type": "database", "driver": "oracle", "host": "safety-db.internal.com"}', TRUE, 30);

-- =====================================================
-- 17. OPERATIONAL METRICS (Sample daily aggregates)
-- =====================================================

INSERT INTO operational_metrics (study_id, site_id, metric_date, total_subjects, subjects_enrolled, total_queries_open, total_queries_closed, avg_query_age_days, sdv_completion_rate, missing_pages_count, pending_meddra_coding, pending_whodd_coding) VALUES
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        (SELECT site_id FROM sites WHERE site_number = 'Site 2' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')),
        '2025-11-14',
        3, 3, 15, 45, 46.0, 75.5, 2, 1, 0
    ),
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        (SELECT site_id FROM sites WHERE site_number = 'Site 18' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')),
        '2025-11-14',
        3, 2, 5, 120, 12.5, 89.0, 1, 0, 1
    ),
    (
        (SELECT study_id FROM studies WHERE study_code = 'Study 1'),
        (SELECT site_id FROM sites WHERE site_number = 'Site 19' AND study_id = (SELECT study_id FROM studies WHERE study_code = 'Study 1')),
        '2025-11-14',
        1, 0, 8, 30, 25.0, 60.0, 1, 0, 0
    );

-- =====================================================
-- Verification Queries
-- =====================================================

-- Count records in each table
SELECT 'studies' AS table_name, COUNT(*) AS record_count FROM studies
UNION ALL SELECT 'regions', COUNT(*) FROM regions
UNION ALL SELECT 'countries', COUNT(*) FROM countries
UNION ALL SELECT 'sites', COUNT(*) FROM sites
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL SELECT 'visits', COUNT(*) FROM visits
UNION ALL SELECT 'forms', COUNT(*) FROM forms
UNION ALL SELECT 'data_queries', COUNT(*) FROM data_queries
UNION ALL SELECT 'protocol_deviations', COUNT(*) FROM protocol_deviations
UNION ALL SELECT 'sdv_records', COUNT(*) FROM sdv_records
UNION ALL SELECT 'pi_signatures', COUNT(*) FROM pi_signatures
UNION ALL SELECT 'coding_records', COUNT(*) FROM coding_records
UNION ALL SELECT 'missing_lab_data', COUNT(*) FROM missing_lab_data
UNION ALL SELECT 'missing_pages', COUNT(*) FROM missing_pages
UNION ALL SELECT 'visit_projections', COUNT(*) FROM visit_projections
UNION ALL SELECT 'sae_records', COUNT(*) FROM sae_records
UNION ALL SELECT 'edrr_issues', COUNT(*) FROM edrr_issues
UNION ALL SELECT 'ai_insights', COUNT(*) FROM ai_insights
UNION ALL SELECT 'ai_recommendations', COUNT(*) FROM ai_recommendations
UNION ALL SELECT 'data_sources', COUNT(*) FROM data_sources
UNION ALL SELECT 'operational_metrics', COUNT(*) FROM operational_metrics
ORDER BY table_name;
