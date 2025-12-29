"""
Graph Builder for Clinical Trial Data
=====================================
Constructs a knowledge graph from processed CSV files for Graph RAG.

Usage:
    from graph_builder import ClinicalTrialGraphBuilder
    
    builder = ClinicalTrialGraphBuilder("/path/to/processed_data")
    G = builder.build_graph()
    builder.save_graph("clinical_trial_graph.graphml")
"""

import os
import sys
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json

# Get project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "processed_data")


class ClinicalTrialGraphBuilder:
    """Builds a knowledge graph from clinical trial CSV data."""
    
    def __init__(self, data_dir: str):
        """
        Initialize the graph builder.
        
        Args:
            data_dir: Path to directory containing processed CSV files
        """
        self.data_dir = data_dir
        self.G = nx.DiGraph()  # Directed graph for relationships
        
        # Track entity counts for reporting
        self.stats = {
            "nodes": {},
            "edges": {}
        }
        
    def load_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """Load a CSV file from the data directory."""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        print(f"Warning: {filename} not found")
        return None
    
    def _add_node(self, node_id: str, node_type: str, **properties):
        """Add a node with type and properties."""
        if not self.G.has_node(node_id):
            self.G.add_node(node_id, node_type=node_type, **properties)
            self.stats["nodes"][node_type] = self.stats["nodes"].get(node_type, 0) + 1
    
    def _add_edge(self, source: str, target: str, edge_type: str, **properties):
        """Add an edge with type and properties."""
        if not self.G.has_edge(source, target):
            self.G.add_edge(source, target, edge_type=edge_type, **properties)
            self.stats["edges"][edge_type] = self.stats["edges"].get(edge_type, 0) + 1
    
    def build_from_edrr(self) -> None:
        """Build nodes and edges from EDRR (issue tracking) data."""
        df = self.load_csv("edrr_processed.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study_id = str(row.get("study", "")).strip()
            subject_id = str(row.get("subject", "")).strip()
            issue_count = row.get("total_open_issue_count_per_subject", 0)
            
            if not study_id or not subject_id:
                continue
                
            # Add Study node
            self._add_node(f"STUDY:{study_id}", "Study", study_id=study_id)
            
            # Add Subject node with issue count
            self._add_node(
                f"SUBJECT:{subject_id}", 
                "Subject", 
                subject_id=subject_id,
                open_issue_count=int(issue_count) if pd.notna(issue_count) else 0
            )
            
            # Add ENROLLED_IN edge
            self._add_edge(
                f"SUBJECT:{subject_id}",
                f"STUDY:{study_id}",
                "ENROLLED_IN"
            )
    
    def build_from_esae(self) -> None:
        """Build nodes and edges from eSAE (safety events) data."""
        df = self.load_csv("esae_processed.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study_id = str(row.get("study_id", "")).strip()
            country = str(row.get("country", "")).strip()
            site = str(row.get("site", "")).strip()
            patient_id = str(row.get("patient_id", "")).strip()
            discrepancy_id = str(row.get("discrepancy_id", "")).strip()
            form_name = str(row.get("form_name", "")).strip()
            review_status = str(row.get("review_status", "")).strip()
            action_status = str(row.get("action_status", "")).strip()
            created_ts = str(row.get("discrepancy_created_timestamp_in_dashboard", "")).strip()
            
            if not study_id or not patient_id:
                continue
            
            # Add Study node
            self._add_node(f"STUDY:{study_id}", "Study", study_id=study_id)
            
            # Add Country node
            if country:
                self._add_node(f"COUNTRY:{country}", "Country", country_code=country)
            
            # Add Site node
            if site:
                self._add_node(f"SITE:{site}", "Site", site_id=site)
                # Site -> Country
                if country:
                    self._add_edge(f"SITE:{site}", f"COUNTRY:{country}", "LOCATED_IN")
                # Study -> Site
                self._add_edge(f"STUDY:{study_id}", f"SITE:{site}", "CONDUCTED_AT")
            
            # Add Subject node
            self._add_node(f"SUBJECT:{patient_id}", "Subject", subject_id=patient_id)
            
            # Subject -> Study
            self._add_edge(f"SUBJECT:{patient_id}", f"STUDY:{study_id}", "ENROLLED_IN")
            
            # Subject -> Site
            if site:
                self._add_edge(f"SUBJECT:{patient_id}", f"SITE:{site}", "ENROLLED_AT")
            
            # Add Safety Discrepancy node
            if discrepancy_id:
                self._add_node(
                    f"DISCREPANCY:{discrepancy_id}",
                    "SafetyDiscrepancy",
                    discrepancy_id=discrepancy_id,
                    review_status=review_status,
                    action_status=action_status,
                    form_name=form_name,
                    created_timestamp=created_ts
                )
                
                # Subject -> Discrepancy
                self._add_edge(
                    f"SUBJECT:{patient_id}",
                    f"DISCREPANCY:{discrepancy_id}",
                    "HAS_DISCREPANCY",
                    form_name=form_name
                )
    
    def build_from_meddra(self) -> None:
        """Build nodes and edges from MedDRA coding data."""
        df = self.load_csv("meddra_processed.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study = str(row.get("study", "")).strip()
            subject = str(row.get("subject", "")).strip()
            form_oid = str(row.get("form_oid", "")).strip()
            coding_status = str(row.get("coding_status", "")).strip()
            require_coding = str(row.get("require_coding", "")).strip()
            dictionary = str(row.get("dictionary", "")).strip()
            version = str(row.get("dictionary_version_number", "")).strip()
            logline = str(row.get("logline", "")).strip()
            
            if not study or not subject:
                continue
            
            # Add Study node
            self._add_node(f"STUDY:{study}", "Study", study_id=study)
            
            # Add Subject node
            self._add_node(f"SUBJECT:{subject}", "Subject", subject_id=subject)
            
            # Subject -> Study
            self._add_edge(f"SUBJECT:{subject}", f"STUDY:{study}", "ENROLLED_IN")
            
            # Add MedDRA Coding record (as a node per unique form/logline combo)
            coding_id = f"MEDDRA:{study}:{subject}:{form_oid}:{logline}"
            self._add_node(
                coding_id,
                "MedDRACoding",
                form_oid=form_oid,
                coding_status=coding_status,
                require_coding=require_coding,
                dictionary=dictionary,
                version=version
            )
            
            # Subject -> MedDRA Coding
            self._add_edge(
                f"SUBJECT:{subject}",
                coding_id,
                "HAS_AE_CODING",
                logline=logline,
                form_oid=form_oid
            )
    
    def build_from_whodd(self) -> None:
        """Build nodes and edges from WHODD (drug coding) data."""
        df = self.load_csv("whodd_processed.csv")
        if df is None:
            return
        
        # Sample to avoid memory issues with 300K+ records
        # if len(df) > 50000:
        #     df = df.sample(n=50000, random_state=42)
        #     print(f"Sampling WHODD to 50000 records for performance")
            
        for _, row in df.iterrows():
            study = str(row.get("study", "")).strip()
            subject = str(row.get("subject", "")).strip()
            form_oid = str(row.get("form_oid", "")).strip()
            coding_status = str(row.get("coding_status", "")).strip()
            require_coding = str(row.get("require_coding", "")).strip()
            dictionary = str(row.get("dictionary", "")).strip()
            version = str(row.get("dictionary_version_number", "")).strip()
            logline = str(row.get("logline", "")).strip()
            
            if not study or not subject:
                continue
            
            # Add Study node
            self._add_node(f"STUDY:{study}", "Study", study_id=study)
            
            # Add Subject node
            self._add_node(f"SUBJECT:{subject}", "Subject", subject_id=subject)
            
            # Subject -> Study
            self._add_edge(f"SUBJECT:{subject}", f"STUDY:{study}", "ENROLLED_IN")
            
            # Add WHODD Coding record
            coding_id = f"WHODD:{study}:{subject}:{form_oid}:{logline}"
            self._add_node(
                coding_id,
                "WHODDCoding",
                form_oid=form_oid,
                coding_status=coding_status,
                require_coding=require_coding,
                dictionary=dictionary,
                version=version
            )
            
            # Subject -> WHODD Coding
            self._add_edge(
                f"SUBJECT:{subject}",
                coding_id,
                "HAS_DRUG_CODING",
                logline=logline,
                form_oid=form_oid
            )
    
    def build_from_missing_pages(self) -> None:
        """Build nodes and edges from missing pages data."""
        df = self.load_csv("missing_pages_processed.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study = str(row.get("study_name", "")).strip()
            country = str(row.get("sitegroupname_countryname_", "")).strip()
            site = str(row.get("sitenumber", "")).strip()
            subject = str(row.get("subjectname", "")).strip()
            form_name = str(row.get("formname", "")).strip()
            folder = str(row.get("foldername", "")).strip()
            visit_date = str(row.get("visit_date", "")).strip()
            days_missing = row.get("no___days_page_missing", 0)
            subject_status = str(row.get("overall_subject_status", "")).strip()
            form_type = str(row.get("form_type__summary_or_visit_", "")).strip()
            
            if not study or not subject:
                continue
            
            # Add Study node
            self._add_node(f"STUDY:{study}", "Study", study_id=study)
            
            # Add Country node
            if country:
                self._add_node(f"COUNTRY:{country}", "Country", country_code=country)
            
            # Add Site node
            if site:
                self._add_node(f"SITE:{site}", "Site", site_id=site)
                if country:
                    self._add_edge(f"SITE:{site}", f"COUNTRY:{country}", "LOCATED_IN")
                self._add_edge(f"STUDY:{study}", f"SITE:{site}", "CONDUCTED_AT")
            
            # Add Subject node with status
            self._add_node(
                f"SUBJECT:{subject}", 
                "Subject", 
                subject_id=subject,
                overall_status=subject_status
            )
            
            # Subject -> Study
            self._add_edge(f"SUBJECT:{subject}", f"STUDY:{study}", "ENROLLED_IN")
            
            # Subject -> Site
            if site:
                self._add_edge(f"SUBJECT:{subject}", f"SITE:{site}", "ENROLLED_AT")
            
            # Add Visit node
            if folder:
                visit_id = f"VISIT:{study}:{subject}:{folder}"
                self._add_node(
                    visit_id,
                    "Visit",
                    visit_name=folder,
                    visit_date=visit_date
                )
                self._add_edge(f"SUBJECT:{subject}", visit_id, "HAS_VISIT")
                
                # Add Form node
                if form_name:
                    form_id = f"FORM:{study}:{form_name}"
                    self._add_node(
                        form_id,
                        "Form",
                        form_name=form_name,
                        form_type=form_type
                    )
                    self._add_edge(visit_id, form_id, "COMPLETED_FORM")
                    
                    # Add Missing Page node
                    if pd.notna(days_missing) and float(days_missing) > 0:
                        missing_id = f"MISSING:{study}:{subject}:{folder}:{form_name}"
                        self._add_node(
                            missing_id,
                            "MissingPage",
                            days_missing=float(days_missing)
                        )
                        self._add_edge(
                            form_id,
                            missing_id,
                            "MISSING_PAGE_FOR",
                            days_missing=float(days_missing)
                        )
    
    def build_from_visit_projection(self) -> None:
        """Build nodes and edges from visit projection data."""
        df = self.load_csv("visit_projection_processed.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study = str(row.get("_source_study", "")).strip()
            country = str(row.get("country", "")).strip()
            site = str(row.get("site", "")).strip()
            subject = str(row.get("subject", "")).strip()
            visit = str(row.get("visit", "")).strip()
            projected_date = str(row.get("projected_date", "")).strip()
            actual_date = str(row.get("actual_date", "")).strip()
            days_outstanding = row.get("__days_outstanding", 0)
            
            if not study or not subject:
                continue
            
            # Add Study node
            self._add_node(f"STUDY:{study}", "Study", study_id=study)
            
            # Add Country node
            if country:
                self._add_node(f"COUNTRY:{country}", "Country", country_code=country)
            
            # Add Site node
            if site:
                self._add_node(f"SITE:{site}", "Site", site_id=site)
                if country:
                    self._add_edge(f"SITE:{site}", f"COUNTRY:{country}", "LOCATED_IN")
                self._add_edge(f"STUDY:{study}", f"SITE:{site}", "CONDUCTED_AT")
            
            # Add Subject node
            self._add_node(f"SUBJECT:{subject}", "Subject", subject_id=subject)
            
            # Subject -> Study
            self._add_edge(f"SUBJECT:{subject}", f"STUDY:{study}", "ENROLLED_IN")
            
            # Subject -> Site
            if site:
                self._add_edge(f"SUBJECT:{subject}", f"SITE:{site}", "ENROLLED_AT")
            
            # Add Visit node with projection info
            if visit:
                visit_id = f"VISIT:{study}:{subject}:{visit}"
                days_out = float(days_outstanding) if pd.notna(days_outstanding) else 0
                self._add_node(
                    visit_id,
                    "Visit",
                    visit_name=visit,
                    projected_date=projected_date,
                    actual_date=actual_date,
                    days_outstanding=days_out
                )
                self._add_edge(
                    f"SUBJECT:{subject}", 
                    visit_id, 
                    "HAS_VISIT",
                    days_outstanding=days_out
                )
    
    def build_from_study_metrics(self) -> None:
        """Enrich Study nodes with aggregated metrics."""
        df = self.load_csv("study_metrics.csv")
        if df is None:
            return
            
        for _, row in df.iterrows():
            study = str(row.get("study", "")).strip()
            if not study:
                continue
                
            node_id = f"STUDY:{study}"
            if self.G.has_node(node_id):
                # Update existing node with metrics
                self.G.nodes[node_id].update({
                    "total_issues": int(row.get("total_issues", 0)) if pd.notna(row.get("total_issues")) else 0,
                    "avg_issues": float(row.get("avg_issues", 0)) if pd.notna(row.get("avg_issues")) else 0,
                    "max_issues": int(row.get("max_issues", 0)) if pd.notna(row.get("max_issues")) else 0,
                    "meddra_records": int(row.get("meddra_records", 0)) if pd.notna(row.get("meddra_records")) else 0,
                    "esae_records": int(row.get("esae_records", 0)) if pd.notna(row.get("esae_records")) else 0
                })
    
    def build_graph(self) -> nx.DiGraph:
        """
        Build the complete knowledge graph from all data sources.
        
        Returns:
            NetworkX DiGraph containing the knowledge graph
        """
        print("Building knowledge graph from clinical trial data...")
        
        print("  Loading EDRR data...")
        self.build_from_edrr()
        
        print("  Loading eSAE data...")
        self.build_from_esae()
        
        print("  Loading MedDRA data...")
        self.build_from_meddra()
        
        print("  Loading WHODD data...")
        self.build_from_whodd()
        
        print("  Loading Missing Pages data...")
        self.build_from_missing_pages()
        
        print("  Loading Visit Projection data...")
        self.build_from_visit_projection()
        
        print("  Enriching with Study Metrics...")
        self.build_from_study_metrics()
        
        print(f"\nGraph built successfully!")
        print(f"  Total nodes: {self.G.number_of_nodes()}")
        print(f"  Total edges: {self.G.number_of_edges()}")
        print(f"\n  Node types: {self.stats['nodes']}")
        print(f"  Edge types: {self.stats['edges']}")
        
        return self.G
    
    def save_graph(self, filename: str = "clinical_trial_graph.graphml") -> str:
        """
        Save the graph to a file.
        
        Args:
            filename: Output filename (GraphML format)
            
        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.data_dir, "..", "graph_rag", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        nx.write_graphml(self.G, filepath)
        print(f"Graph saved to: {filepath}")
        return filepath
    
    def get_stats(self) -> Dict:
        """Get graph statistics."""
        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "node_types": self.stats["nodes"],
            "edge_types": self.stats["edges"]
        }


def main():
    """Build and save the clinical trial knowledge graph."""
    # Initialize builder with absolute path
    print(f"Data directory: {DATA_DIR}")
    builder = ClinicalTrialGraphBuilder(DATA_DIR)
    
    # Build the graph
    G = builder.build_graph()
    
    # Save to file
    builder.save_graph("clinical_trial_graph.graphml")
    
    # Also save stats as JSON
    stats = builder.get_stats()
    stats_path = os.path.join(SCRIPT_DIR, "graph_stats.json")
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Stats saved to: {stats_path}")
    
    return G


if __name__ == "__main__":
    main()

