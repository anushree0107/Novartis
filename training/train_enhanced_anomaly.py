from analytics.risk.enhanced_detector import (
    EnhancedAnomalyDetector,
    AnomalyMethod
)


def main():
    
    detector = EnhancedAnomalyDetector()
    
    print("\n Training anomaly detection models...")
    success = detector.train()
    
    if success:
        print("   Isolation Forest trained")
        print("   Local Outlier Factor trained")
        print("   Elliptic Envelope (Mahalanobis) trained")
        print("   Population statistics computed")
    else:
        print("   Training failed")
        return
    
    # Get summary
    print("\n Running anomaly detection...")
    summary = detector.get_summary()
    
    print(f"\n   Total Sites: {summary['total_sites']}")
    print(f"   Anomalies Detected: {summary['anomaly_count']}")
    print(f"   Anomaly Rate: {summary['anomaly_rate']*100:.1f}%")
    
    print("\n   Risk Distribution:")
    for level, count in summary['risk_distribution'].items():
        print(f"      {level}: {count} sites")
    
    print("\n   Top Anomalous Features:")
    for feat_info in summary['top_anomalous_features'][:5]:
        print(f"      - {feat_info['feature']}: {feat_info['count']} occurrences")
    
    # Get high-risk sites
    print("\n High Risk Sites (Critical + High):")
    high_risk = detector.get_high_risk_sites(threshold="High")
    for site in high_risk[:5]:
        print(f"   - Site {site.entity_id}: {site.risk_level}")
        print(f"     Score: {site.anomaly_score:.4f}")
        print(f"     Anomalous Features: {', '.join(site.anomalous_features[:3])}")
    
    # Sample control chart analysis
    if high_risk:
        sample_site = high_risk[0].entity_id
        print(f"\n Control Chart Analysis for Site {sample_site}:")
        control_results = detector.control_chart_analysis(sample_site)
        for result in control_results:
            status = "OUT OF CONTROL" if result.is_out_of_control else "In Control"
            print(f"   - {result.metric_name}: {result.current_value:.4f}")
            print(f"     Mean: {result.mean:.4f}, UCL: {result.ucl:.4f}, LCL: {result.lcl:.4f}")
            print(f"     Status: {status}")
    


if __name__ == "__main__":
    main()
