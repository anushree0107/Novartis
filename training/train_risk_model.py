from analytics.risk.detector import SiteAnomalyDetector

detector = SiteAnomalyDetector()
print("Training model...")
success = detector.train()
if success:
    print("Model trained and saved successfully.")
    
    print("\nRunning predictions:")
    results = detector.predict()
    for res in results[:5]:
        print(f"Site: {res['site_id']} | Risk: {res['risk_level']} | Score: {res['anomaly_score']:.4f}")
else:
    print("Failed to train model (insufficient data?)")
