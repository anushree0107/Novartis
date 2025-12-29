# NEST 2.0 Advanced Analytics Pipeline

## Overview

This repository contains a comprehensive **Advanced Analytics Pipeline** for analyzing clinical trial data from the NEST 2.0 dataset. The pipeline covers the full spectrum of data analytics from ingestion to deployment-ready models.

## Pipeline Structure

The pipeline consists of **11 Jupyter notebooks** organized in sequential order:

| # | Notebook | Description |
|---|----------|-------------|
| 01 | `01_data_ingestion.ipynb` | Load and harmonize data from 23 clinical studies |
| 02 | `02_data_quality.ipynb` | Automated data quality assessment with DQ scores |
| 03 | `03_eda.ipynb` | Exploratory data analysis with interactive visualizations |
| 04 | `04_feature_engineering.ipynb` | Create study-level and subject-level features |
| 05 | `05_labeling.ipynb` | Define target variables for predictive modeling |
| 06 | `06_anomaly_detection.ipynb` | Detect outliers using ensemble methods |
| 07 | `07_predictive_models.ipynb` | Train and evaluate classification models |
| 08 | `08_time_series_forecasting.ipynb` | Forecast operational metrics |
| 09 | `09_explainability.ipynb` | SHAP-based model explanations |
| 10 | `10_monitoring.ipynb` | Data drift detection and retrain triggers |
| 11 | `11_analytics_report.ipynb` | Comprehensive final report |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Notebooks in Order

Navigate to the `notebooks/` directory and run notebooks sequentially:

```bash
cd notebooks
jupyter notebook
```

Start with `01_data_ingestion.ipynb` and proceed through `11_analytics_report.ipynb`.

### 3. Demo Mode

For a quick demonstration, each notebook is designed to work with the existing processed data in `processed_data/`. The pipeline will automatically detect and use available data.

## Data Sources

The pipeline expects data from 23 clinical studies with the following file types:

- **EDC Metrics** - Site-level operational metrics
- **EDRR** - Open issues per subject
- **MedDRA** - Adverse event coding reports
- **WHODD** - Drug coding reports
- **eSAE Dashboard** - Safety event records
- **Missing Pages** - Missing CRF page reports
- **Visit Projection** - Visit compliance data

## Output Structure

```
├── data/
│   └── processed/          # Normalized parquet files
├── features/               # Feature store
├── labels/                 # Target definitions
├── models/                 # Trained model artifacts
├── reports/
│   ├── dq/                # Data quality reports
│   ├── eda/               # EDA visualizations
│   ├── anomalies/         # Anomaly detection results
│   ├── models/            # Model evaluation
│   ├── forecasts/         # Forecasting results
│   ├── explainability/    # SHAP explanations
│   ├── monitoring/        # Drift detection
│   └── final/             # Comprehensive report
└── notebooks/             # All 11 notebooks
```

## Key Features

### Data Quality
- Completeness, validity, uniqueness checks
- Automated DQ scoring (0-100)
- Alerting thresholds

### Anomaly Detection
- Z-Score statistical outliers
- Isolation Forest
- Local Outlier Factor (LOF)
- Ensemble voting

### Predictive Modeling
- Logistic Regression (baseline)
- Random Forest
- Gradient Boosting
- LightGBM
- Time-aware cross-validation
- Feature importance analysis

### Explainability
- SHAP global explanations
- Per-study local explanations
- Human-readable risk assessments
- Uncertainty quantification

### Monitoring
- Population Stability Index (PSI)
- Kolmogorov-Smirnov tests
- Retrain trigger rules

## Configuration

Thresholds and configurations can be adjusted in each notebook. Key configurable parameters:

- **DQ thresholds**: Warning at 5% missing, Error at 20%
- **Anomaly contamination**: 10% expected anomalies
- **Drift thresholds**: PSI > 0.2 triggers retrain
- **Model hyperparameters**: Defined in notebook 07

## License

Internal use only. Contains de-identified clinical trial data.

## Contact

For questions about this analytics pipeline, contact the Data Science team.
