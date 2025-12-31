
import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Union

from .models import EntityType, DQIResult
from .calculator import DQICalculator


def run_inference(
    entity_id: str = None,
    entity_type: str = "site",
    batch_file: str = None,
    all_sites: bool = False,
    output_path: str = None,
    output_format: str = "json",
    data_dir: str = "processed_data",
    model_dir: str = "models/dqi",
    mode: str = "hybrid"
) -> Union[DQIResult, List[DQIResult]]:
    # Map entity type string to enum
    type_map = {
        "site": EntityType.SITE,
        "patient": EntityType.PATIENT,
        "study": EntityType.STUDY,
    }
    
    entity_type_enum = type_map.get(entity_type.lower())
    if not entity_type_enum:
        raise ValueError(f"Unknown entity type: {entity_type}")
    
    # Initialize calculator
    from .models import DQIConfig
    config = DQIConfig(mode=mode)
    
    calculator = DQICalculator(
        config=config,
        data_dir=data_dir,
        model_dir=model_dir
    )
    
    # Calculate DQI
    results = []
    
    if all_sites:
        results = calculator.calculate_all_sites()
    elif batch_file:
        with open(batch_file, "r") as f:
            entity_ids = [line.strip() for line in f if line.strip()]
        results = calculator.calculate_batch(entity_ids, entity_type_enum)
    elif entity_id:
        result = calculator.calculate(entity_id, entity_type_enum)
        results = [result]
    else:
        raise ValueError("Must provide entity_id, batch_file, or --all-sites")
    
    # Output results
    if output_format == "console" or not output_path:
        for result in results:
            print(result.summary())
            print()
    
    if output_path:
        _save_results(results, output_path, output_format)
    
    return results[0] if len(results) == 1 and entity_id else results


def _save_results(results: List[DQIResult], path: str, format: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        data = [r.to_dict() for r in results]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Results saved to {path}")
    
    elif format == "csv":
        import csv
        
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "entity_id", "entity_type", "score", "grade", 
                "status", "is_clean", "critical_count", "warning_count"
            ])
            for r in results:
                writer.writerow([
                    r.entity_id,
                    r.entity_type.value,
                    round(r.score, 2),
                    r.grade,
                    r.status,
                    r.is_clean,
                    r.critical_count,
                    r.warning_count
                ])
        print(f"Results saved to {path}")


def main():
    parser = argparse.ArgumentParser(
        description="DQI Calculator - Data Quality Index inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single site
  python -m analytics.dqi.inference --entity-id "Site 637" --type site
  
  # All sites
  python -m analytics.dqi.inference --all-sites --output results.json
  
  # Batch from file
  python -m analytics.dqi.inference --batch-file sites.txt --output results.csv --format csv
  
  # Different scoring mode
  python -m analytics.dqi.inference --entity-id "Study 21" --type study --mode rules
"""
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--entity-id", "-e",
        help="Single entity ID to calculate DQI for"
    )
    input_group.add_argument(
        "--batch-file", "-b",
        help="Path to file with entity IDs (one per line)"
    )
    input_group.add_argument(
        "--all-sites", "-a",
        action="store_true",
        help="Calculate DQI for all sites"
    )
    
    # Entity type
    parser.add_argument(
        "--type", "-t",
        default="site",
        choices=["site", "patient", "study"],
        help="Entity type (default: site)"
    )
    
    # Scoring mode
    parser.add_argument(
        "--mode", "-m",
        default="hybrid",
        choices=["rules", "statistical", "hybrid"],
        help="Scoring mode (default: hybrid)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file path"
    )
    parser.add_argument(
        "--format", "-f",
        default="json",
        choices=["json", "csv", "console"],
        help="Output format (default: json)"
    )
    
    # Data paths
    parser.add_argument(
        "--data-dir",
        default="processed_data",
        help="Path to processed data directory"
    )
    parser.add_argument(
        "--model-dir",
        default="models/dqi",
        help="Path to model artifacts directory"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        run_inference(
            entity_id=args.entity_id,
            entity_type=args.type,
            batch_file=args.batch_file,
            all_sites=args.all_sites,
            output_path=args.output,
            output_format=args.format,
            data_dir=args.data_dir,
            model_dir=args.model_dir,
            mode=args.mode
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
