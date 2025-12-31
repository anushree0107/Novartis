
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from .models import EntityType


class DQIFeatureExtractor:
    
    # Feature definitions with source mapping
    FEATURE_DEFINITIONS = {
        "missing_visits_pct": {
            "source": "visit_projection",
            "description": "Percentage of missing/overdue visits"
        },
        "missing_pages_pct": {
            "source": "missing_pages",
            "description": "Percentage of missing CRF pages"
        },
        "open_issues_per_subject": {
            "source": "edrr",
            "description": "Average open issues per subject"
        },
        "safety_pending_pct": {
            "source": "esae",
            "description": "Percentage of safety reviews pending"
        },
        "meddra_coding_rate": {
            "source": "meddra",
            "description": "MedDRA coding completion rate"
        },
        "whodd_coding_rate": {
            "source": "whodd",
            "description": "WHODD coding completion rate"
        },
        "days_outstanding_avg": {
            "source": "visit_projection",
            "description": "Average days visits are outstanding"
        },
        "days_pages_missing_avg": {
            "source": "missing_pages",
            "description": "Average days pages have been missing"
        },
    }
    
    def __init__(self, data_dir: str = "processed_data"):
        self.data_dir = Path(data_dir)
        self.data: Dict[str, pd.DataFrame] = {}
        self._load_data()
        self._site_features_cache: Dict[str, Dict[str, float]] = {}
    
    def _load_data(self):
        csv_files = {
            "edrr": "edrr_processed.csv",
            "esae": "esae_processed.csv",
            "missing_pages": "missing_pages_processed.csv",
            "visit_projection": "visit_projection_processed.csv",
            "meddra": "meddra_processed.csv",
            "whodd": "whodd_processed.csv",
        }
        
        for key, filename in csv_files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                self.data[key] = pd.read_csv(filepath, low_memory=False)
            else:
                self.data[key] = pd.DataFrame()
    
    def _precompute_aggregates(self):
        self._site_features_cache: Dict[str, Dict[str, float]] = {}
        self._study_features_cache: Dict[str, Dict[str, float]] = {}
        self._patient_features_cache: Dict[str, Dict[str, float]] = {}
        
        # Compute site-level aggregates
        self._compute_site_aggregates()
    
    def _normalize_id(self, entity_id: str, prefix: str = "") -> str:
        entity_id = str(entity_id).strip()
        if prefix and not entity_id.lower().startswith(prefix.lower()):
            return f"{prefix} {entity_id}"
        return entity_id
    
    def _compute_site_aggregates(self):
        # Initialize with all identified sites
        all_sites = set()
        for key, df in self.data.items():
            if df.empty: continue
            site_col = self._find_column(df, ["site", "sitenumber"])
            if site_col:
                all_sites.update(df[site_col].dropna().astype(str).unique())
        
        # Prepare bulk data structures
        site_features = {site: {} for site in all_sites}
        
        # 1. Visit Projection (Missing Visits & Days Outstanding)
        vp_df = self.data.get("visit_projection", pd.DataFrame())
        if not vp_df.empty:
            site_col = self._find_column(vp_df, ["site"])
            if site_col:
                # Groupby
                gr = vp_df.groupby(site_col)
                # Missing Visits (approx: count / 100)
                counts = gr.size()
                # Days Outstanding
                days_col = self._find_column(vp_df, ["days_outstanding", "# Days Outstanding"])
                if days_col:
                    days_avg = gr[days_col].mean()
                else:
                    days_avg = pd.Series(0, index=counts.index)
                    
                for site, count in counts.items():
                    s_str = str(site)
                    if s_str in site_features:
                        site_features[s_str]["missing_visits_pct"] = min(1.0, count / 100.0)
                        site_features[s_str]["days_outstanding_avg"] = float(days_avg.get(site, 0.0))

        # 2. Missing Pages
        mp_df = self.data.get("missing_pages", pd.DataFrame())
        if not mp_df.empty:
            site_col = self._find_column(mp_df, ["site", "sitenumber"])
            if site_col:
                gr = mp_df.groupby(site_col)
                counts = gr.size()
                days_col = self._find_column(mp_df, ["days_missing", "no___days_page_missing"])
                if days_col:
                    days_avg = gr[days_col].mean()
                else:
                    days_avg = pd.Series(0, index=counts.index)
                
                for site, count in counts.items():
                    s_str = str(site)
                    if s_str in site_features:
                        site_features[s_str]["missing_pages_pct"] = min(1.0, count / 50.0)
                        site_features[s_str]["days_pages_missing_avg"] = float(days_avg.get(site, 0.0))
        
        # 3. Safety Pending (eSAE)
        esae_df = self.data.get("esae", pd.DataFrame())
        if not esae_df.empty:
            site_col = self._find_column(esae_df, ["site"])
            status_col = self._find_column(esae_df, ["review_status", "status"])
            if site_col and status_col:
                # Calculate pending % per site
                # Vectorized: group by site, value_counts normalized?
                # Faster: group by site, custom agg
                def pct_pending(x):
                    return np.mean(x.str.lower().str.contains("pending", na=False))
                
                pending_pcts = esae_df.groupby(site_col)[status_col].apply(pct_pending)
                
                for site, pct in pending_pcts.items():
                    s_str = str(site)
                    if s_str in site_features:
                        site_features[s_str]["safety_pending_pct"] = float(pct)

        # 4. Open Issues (EDRR + eSAE merge)
        edrr_df = self.data.get("edrr", pd.DataFrame())
        if not edrr_df.empty and not esae_df.empty:
            # Join to get site
            subj_col_edrr = self._find_column(edrr_df, ["subject", "subject_id"])
            subj_col_esae = self._find_column(esae_df, ["patient_id", "subject"])
            site_col_esae = self._find_column(esae_df, ["site"])
            
            if subj_col_edrr and subj_col_esae and site_col_esae:
                # Create lookup (ensure unique subject index)
                lookup = esae_df[[subj_col_esae, site_col_esae]].drop_duplicates(subset=[subj_col_esae]).set_index(subj_col_esae)
                # Map site to edrr
                edrr_df["_mapped_site"] = edrr_df[subj_col_edrr].map(lookup[site_col_esae])
                
                issue_col = self._find_column(edrr_df, ["total_open_issue_count_per_subject", "issue_count"])
                if issue_col:
                    avgs = edrr_df.groupby("_mapped_site")[issue_col].mean()
                    for site, val in avgs.items():
                        s_str = str(site)
                        if s_str in site_features:
                            site_features[s_str]["open_issues_per_subject"] = float(val)

        # 5. Coding (Global defaults mostly, unless site col exists)
        # For speed, just use defaults if no site cols found in MedDRA/WHODD
        # Or simplistic check
        
        # Fill missing with defaults
        defaults = {
            "missing_visits_pct": 0.0,
            "missing_pages_pct": 0.0,
            "open_issues_per_subject": 0.0,
            "safety_pending_pct": 0.0,
            "meddra_coding_rate": 0.99,
            "whodd_coding_rate": 0.99,
            "days_outstanding_avg": 0.0,
            "days_pages_missing_avg": 0.0,
        }
        
        for site_id, feats in site_features.items():
            for k, v in defaults.items():
                if k not in feats:
                    feats[k] = v
            self._site_features_cache[site_id] = feats

    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        for col in candidates:
            if col in df.columns:
                return col
            # Try case-insensitive match
            for df_col in df.columns:
                if df_col.lower() == col.lower():
                    return df_col
        return None
    
    def _compute_site_features(self, site_id: str) -> Dict[str, float]:
        features = {}
        
        # 1. Missing visits percentage
        features["missing_visits_pct"] = self._calc_site_missing_visits(site_id)
        
        # 2. Missing pages percentage
        features["missing_pages_pct"] = self._calc_site_missing_pages(site_id)
        
        # 3. Open issues per subject
        features["open_issues_per_subject"] = self._calc_site_open_issues(site_id)
        
        # 4. Safety pending percentage
        features["safety_pending_pct"] = self._calc_site_safety_pending(site_id)
        
        # 5. MedDRA coding rate
        features["meddra_coding_rate"] = self._calc_site_meddra_coding(site_id)
        
        # 6. WHODD coding rate
        features["whodd_coding_rate"] = self._calc_site_whodd_coding(site_id)
        
        # 7. Days outstanding average
        features["days_outstanding_avg"] = self._calc_site_days_outstanding(site_id)
        
        # 8. Days pages missing average
        features["days_pages_missing_avg"] = self._calc_site_days_pages_missing(site_id)
        
        return features
    
    def _calc_site_missing_visits(self, site_id: str) -> float:
        df = self.data.get("visit_projection", pd.DataFrame())
        if df.empty or "site" not in df.columns:
            return 0.0
        
        site_data = df[df["site"].astype(str) == site_id]
        if site_data.empty:
            return 0.0
        
        # Count total visits and missing visits
        total = len(site_data)
        return min(1.0, total / 100)  # Normalize assuming 100 expected visits
    
    def _calc_site_missing_pages(self, site_id: str) -> float:
        df = self.data.get("missing_pages", pd.DataFrame())
        if df.empty:
            return 0.0
        
        site_col = self._find_column(df, ["site", "sitenumber"])
        if not site_col:
            return 0.0
        
        site_data = df[df[site_col].astype(str) == site_id]
        if site_data.empty:
            return 0.0
        
        total = len(site_data)
        return min(1.0, total / 50)  # Normalize assuming 50 expected pages
    
    def _calc_site_open_issues(self, site_id: str) -> float:
        # EDRR doesn't have site column directly, use subject-to-site mapping
        # For now, return default value
        df = self.data.get("edrr", pd.DataFrame())
        if df.empty:
            return 0.0
        
        # Get subjects for this site from esae
        esae = self.data.get("esae", pd.DataFrame())
        if esae.empty or "site" not in esae.columns:
            return 0.0
        
        site_subjects = esae[esae["site"].astype(str) == site_id]["patient_id"].unique()
        
        # Match with EDRR
        subject_col = self._find_column(df, ["subject", "subject_id"])
        if not subject_col:
            return 0.0
        
        site_issues = df[df[subject_col].isin(site_subjects)]
        if site_issues.empty:
            return 0.0
        
        issue_col = self._find_column(df, ["total_open_issue_count_per_subject", "issue_count"])
        if issue_col:
            return site_issues[issue_col].mean()
        
        return len(site_issues) / max(1, len(site_subjects))
    
    def _calc_site_safety_pending(self, site_id: str) -> float:
        df = self.data.get("esae", pd.DataFrame())
        if df.empty or "site" not in df.columns:
            return 0.0
        
        site_data = df[df["site"].astype(str) == site_id]
        if site_data.empty:
            return 0.0
        
        total = len(site_data)
        status_col = self._find_column(df, ["review_status", "status"])
        if not status_col:
            return 0.0
        
        pending = site_data[site_data[status_col].str.lower().str.contains("pending", na=False)]
        return len(pending) / total if total > 0 else 0.0
    
    def _calc_site_meddra_coding(self, site_id: str) -> float:
        # MedDRA doesn't have site column, return study-level default
        df = self.data.get("meddra", pd.DataFrame())
        if df.empty:
            return 0.99
        
        status_col = self._find_column(df, ["coding_status", "Coding Status"])
        if not status_col:
            return 0.99
        
        # Calculate overall coding rate
        total = len(df)
        coded = df[df[status_col].str.lower().str.contains("coded", na=False)]
        return len(coded) / total if total > 0 else 0.99
    
    def _calc_site_whodd_coding(self, site_id: str) -> float:
        df = self.data.get("whodd", pd.DataFrame())
        if df.empty:
            return 0.99
        
        status_col = self._find_column(df, ["coding_status", "Coding Status"])
        if not status_col:
            return 0.99
        
        total = len(df)
        coded = df[df[status_col].str.lower().str.contains("coded", na=False)]
        return len(coded) / total if total > 0 else 0.99
    
    def _calc_site_days_outstanding(self, site_id: str) -> float:
        df = self.data.get("visit_projection", pd.DataFrame())
        if df.empty or "site" not in df.columns:
            return 0.0
        
        site_data = df[df["site"].astype(str) == site_id]
        if site_data.empty:
            return 0.0
        
        days_col = self._find_column(df, ["__days_outstanding", "days_outstanding", "# Days Outstanding"])
        if not days_col:
            return 0.0
        
        return site_data[days_col].fillna(0).mean()
    
    def _calc_site_days_pages_missing(self, site_id: str) -> float:
        df = self.data.get("missing_pages", pd.DataFrame())
        if df.empty:
            return 0.0
        
        site_col = self._find_column(df, ["site", "sitenumber"])
        if not site_col:
            return 0.0
        
        site_data = df[df[site_col].astype(str) == site_id]
        if site_data.empty:
            return 0.0
        
        days_col = self._find_column(df, ["no___days_page_missing", "days_missing"])
        if not days_col:
            return 0.0
        
        return site_data[days_col].fillna(0).mean()
    
    def extract_site_features(self, site_id: str) -> Dict[str, float]:
        site_id = str(site_id).strip()
        
        # Check cache first
        if site_id in self._site_features_cache:
            return self._site_features_cache[site_id]
        
        # Compute on demand
        features = self._compute_site_features(site_id)
        
        # Ensure all values are python floats to avoid pandas recursion issues
        safe_features = {k: float(v) for k, v in features.items()}
        
        self._site_features_cache[site_id] = safe_features
        return safe_features
    
    def extract_patient_features(self, patient_id: str) -> Dict[str, float]:
        patient_id = str(patient_id).strip()
        
        features = {}
        
        # Get patient's open issues from EDRR
        edrr = self.data.get("edrr", pd.DataFrame())
        if not edrr.empty:
            subject_col = self._find_column(edrr, ["subject", "subject_id"])
            if subject_col:
                patient_data = edrr[edrr[subject_col].astype(str).str.contains(patient_id, na=False)]
                if not patient_data.empty:
                    issue_col = self._find_column(edrr, ["total_open_issue_count_per_subject"])
                    if issue_col:
                        features["open_issues_per_subject"] = patient_data[issue_col].iloc[0]
        
        # Get patient's safety events from eSAE
        esae = self.data.get("esae", pd.DataFrame())
        if not esae.empty:
            patient_col = self._find_column(esae, ["patient_id", "subject"])
            if patient_col:
                patient_data = esae[esae[patient_col].astype(str).str.contains(patient_id, na=False)]
                if not patient_data.empty:
                    total = len(patient_data)
                    status_col = self._find_column(esae, ["review_status"])
                    if status_col:
                        pending = patient_data[patient_data[status_col].str.lower().str.contains("pending", na=False)]
                        features["safety_pending_pct"] = len(pending) / total if total > 0 else 0.0
        
        # Fill defaults for missing features
        defaults = {
            "missing_visits_pct": 0.0,
            "missing_pages_pct": 0.0,
            "open_issues_per_subject": 0.0,
            "safety_pending_pct": 0.0,
            "meddra_coding_rate": 0.99,
            "whodd_coding_rate": 0.99,
            "days_outstanding_avg": 0.0,
            "days_pages_missing_avg": 0.0,
        }
        
        for key, default in defaults.items():
            if key not in features:
                features[key] = default
        
        return {k: float(v) for k, v in features.items()}
    
    def extract_study_features(self, study_id: str) -> Dict[str, float]:
        study_id = str(study_id).strip()
        
        # Get sites for this study from eSAE
        esae = self.data.get("esae", pd.DataFrame())
        study_sites = []
        
        if not esae.empty:
            study_col = self._find_column(esae, ["study_id", "study"])
            if study_col:
                study_data = esae[esae[study_col].astype(str).str.contains(study_id, na=False)]
                if not study_data.empty and "site" in study_data.columns:
                    study_sites = study_data["site"].unique().tolist()
        
        if not study_sites:
            # Return defaults
            return {
                "missing_visits_pct": 0.05,
                "missing_pages_pct": 0.05,
                "open_issues_per_subject": 1.0,
                "safety_pending_pct": 0.10,
                "meddra_coding_rate": 0.99,
                "whodd_coding_rate": 0.99,
                "days_outstanding_avg": 5.0,
                "days_pages_missing_avg": 10.0,
            }
        
        # Aggregate features across sites
        all_site_features = [self.extract_site_features(site) for site in study_sites]
        
        aggregated = {}
        for key in all_site_features[0].keys():
            values = [sf.get(key, 0.0) for sf in all_site_features]
            aggregated[key] = np.mean(values)
        
        return {k: float(v) for k, v in aggregated.items()}
    
    def extract_all_sites(self) -> pd.DataFrame:
        if not self._site_features_cache:
            self._compute_site_aggregates()
        
        records = [
            {"site_id": site_id, **features}
            for site_id, features in self._site_features_cache.items()
        ]
        
        if not records:
            return pd.DataFrame()
        
        return pd.DataFrame(records).set_index("site_id")
    
    def get_population_statistics(self) -> Dict[str, Dict[str, float]]:
        df = self.extract_all_sites()
        if df.empty:
            return {}
        
        stats = {}
        for col in df.columns:
            values = df[col].dropna()
            if len(values) == 0:
                continue
            
            stats[col] = {
                "mean": float(values.mean()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "p25": float(values.quantile(0.25)),
                "p50": float(values.quantile(0.50)),
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.90)),
                "p95": float(values.quantile(0.95)),
            }
        
        return stats
