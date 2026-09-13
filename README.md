# 🏗️ Smart Housing Inspection & Compliance Management System (V1.0)

A specialized Civil QA/QC engineering and municipal building-control management platform built with Python and Streamlit. The system enforces structural integrity bylaws, tracks construction progress monotonicity, prevents setback encroachments, and automates legal statutory notice workflows.

---

## 📌 Core Engineering Capabilities

* **Executive Command Center (`pages/dashboard.py`):** Society-wide QA/QC health monitoring, cross-sector compliance matrices, and active Stop Work alert tracking.
* **Intake & Verification Guardrails (`pages/inspections.py`):** Field intake enforcing strict monotonic progress validation (preventing illegal progress regressions) and mandatory macro/micro photographic proof policies.
* **Spreadsheet Directory & Inline Editor (`pages/records.py`):** Interactive data grid featuring multi-column filtering (Sector, Contractor, Status, Date), cell-level editing, an undo history stack, and row deletion.
* **Enforcement & Legal Compliance Tracker (`pages/enforcement.py`):** High-contrast statutory status cards, countdown timers for cure periods, and evidence dossiers for non-compliant plots.
* **Civil Risk & Quality Analytics (`pages/analytics.py`):** Pareto 80/20 defect distribution (CII principles), First-Time Quality (FTQ) dial gauges, Site Risk Priority Indexing (SRPI), vertical floor-by-floor defect profiles, and Contractor Reliability scorecards.
* **Statutory Notice & Export Engine (`pages/reports.py`):** Generates formal, printable municipal notices (Stop Work Orders, 7-Day Rectification Notices, Clearance Certificates) with embedded photo plates and by-law citations, plus filtered exports to CSV and Excel (`.xlsx`).
* **Engineering Reference Manual (`pages/help_guide.py`):** In-app documentation detailing structural ascent rules, SRPI formulas, and statutory municipal bylaws.

---

## 🛠️ Technology Stack

* **Framework:** Streamlit
* **Data Processing:** Pandas
* **Data Visualization:** Plotly Graph Objects & Plotly Express
* **Imaging:** Pillow (PIL)
* **Spreadsheet Engine:** OpenPyXL

---

## 🚀 Installation & Local Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/saadsaeed1/Smart_Housing_Inspection_V1.git](https://github.com/saadsaeed1/Smart_Housing_Inspection_V1.git)
   cd Smart_Housing_Inspection_V1
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Application:**
   ```bash
   streamlit run app.py
   ```

---

## 📂 Project Structure

```text
Smart_Housing_Inspection_V1/
├── app.py                     # Main router and shell layout
├── config.py                  # Municipal schemas, enums, and tolerances
├── data_manager.py            # Normalized data persistence layer
├── validation.py              # Civil engineering validation rules
├── requirements.txt           # Production dependencies
├── README.md                  # System documentation
├── .streamlit/
│   └── config.toml            # UI theme and router settings
├── data/
│   └── inspection_data.csv    # 100-record verified civil lifecycle database
├── assets/
│   └── site_images/           # Forensic audit evidence photos
└── pages/
    ├── dashboard.py           # Executive command center
    ├── inspections.py         # Inspection logging & validation intake
    ├── records.py             # Spreadsheet editor & photo directory
    ├── enforcement.py         # Municipal enforcement & delinquency tracker
    ├── analytics.py           # Statistical QA/QC & Pareto analytics
    ├── reports.py             # Statutory notices & Excel/CSV export engine
    └── help_guide.py          # Reference manual & engineering bylaws
```

---

## ⚖️ Authorship
Developed by **Eng. Saad Saeed** for municipal building control authorities, structural engineering firms, and residential housing development schemes.
