# StrideX

AI-powered gait analysis system for early neurological risk detection.

StrideX turns routine walking videos into biomechanical gait insights using computer vision and feature-based risk screening. The project combines a Python analysis pipeline, a Flask clinical API, and a React dashboard to support longitudinal gait monitoring and early risk flagging in a research context.

> **Research prototype:** StrideX is intended for screening and monitoring workflows. It is **not** a medical diagnosis tool.

---

## Why StrideX?

Subtle gait changes can appear before severe neurological decline is clinically obvious. Traditional gait labs can be expensive and inaccessible. StrideX aims to make movement screening more accessible by using standard video input and automated analysis to:

- derive quantitative gait features,
- estimate risk levels,
- track patient baselines over time, and
- generate clinician-friendly outputs.

---

## Key Features

- **Video-based gait capture** from common file formats (MP4, MOV, AVI, MKV).
- **Pose + biomechanical feature extraction** using a Python CV pipeline.
- **Risk scoring pipeline** with model-backed feature evaluation.
- **Clinical workflow API** for patients, assessments, status checks, trends, and PDF reports.
- **React frontend dashboard** for clinician and patient-facing views.
- **Streamlit interfaces** for rapid demo/testing flows.
- **SQLite-backed persistence** for local development and prototyping.

---

## Project Structure

```text
StrideX/
├── ai/                         # ML/CV pipeline components
│   ├── features/               # Gait feature engineering
│   ├── vision/                 # Pose estimation + video processing
│   ├── models/                 # Risk predictor / training artifacts
│   ├── baseline/               # Baseline comparison logic
│   ├── anomaly/                # Anomaly detection helpers
│   └── explainability/         # SHAP explainability utilities
├── backend/
│   ├── server.py               # Flask API server (main backend entrypoint)
│   ├── db.py                   # SQLite schema + seed data
│   ├── pipeline.py             # Video analysis orchestration
│   └── pdf_generator.py        # Clinical-style PDF report generation
├── frontend/
│   └── stridex-app/            # React + Vite web app
│       ├── src/pages/          # Clinician/patient UI routes
│       └── src/api.js          # Axios API client
├── pages/                      # Streamlit multipage screens
├── app.py                      # Streamlit landing page
├── app_login.py                # Streamlit sign-in flow
├── app_analysis.py             # Streamlit analysis dashboard
└── requirements.txt            # Core Python dependencies
```

---

## Tech Stack

### Backend / AI
- Python
- Flask + Flask-CORS
- OpenCV + MediaPipe
- NumPy + Pandas
- scikit-learn / XGBoost tooling (model training utilities)
- ReportLab (PDF generation)
- SQLite

### Frontend
- React (Vite)
- Axios
- React Router
- Chart.js / react-chartjs-2

### UI Prototyping
- Streamlit

---

## Setup & Installation

## 1) Clone

```bash
git clone https://github.com/manodharanii2006/StrideX.git
cd StrideX
```

## 2) Python environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Install backend/model extras used by the API and training/explainability modules:

```bash
pip install flask flask-cors reportlab joblib scikit-learn xgboost shap matplotlib
```

## 3) Frontend dependencies

```bash
cd frontend/stridex-app
npm install
cd ../..
```

---

## Running the Project

### Option A — Full web stack (recommended)

Start the Flask API:

```bash
python backend/server.py
```

In another terminal, start the React app:

```bash
cd frontend/stridex-app
npm run dev
```

Then open the Vite URL (default: `http://localhost:5173`). API calls to `/api` are proxied to `http://127.0.0.1:5000`.

### Option B — Streamlit prototype flow

```bash
streamlit run app.py
```

---

## Common Commands

### Frontend (`frontend/stridex-app`)

```bash
npm run dev      # local development
npm run build    # production build
npm run lint     # oxlint
npm run preview  # preview build
```

### Backend

```bash
python backend/server.py
```

---

## Demo / Development Notes

- The backend seeds a demo clinician account in local SQLite:
  - **Email:** `doctor@stridex.health`
  - **Password:** `demo1234`
- Uploaded/generated data is written under `data/uploads` and `data/outputs`.

---

## Future Improvements

- Harden authentication/authorization with production-grade identity flows.
- Replace placeholder token strategy with secure JWT/session management.
- Expand model validation and calibration on larger clinical datasets.
- Add automated tests for backend endpoints and UI flows.
- Containerize services (Docker) for reproducible deployment.
- Introduce CI quality gates (tests, lint, security scanning).

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Make focused changes with clear commit messages
4. Run relevant checks (frontend lint/build, backend smoke checks)
5. Open a pull request with context and screenshots/logs where helpful

If you are planning major architecture or model changes, open an issue first to align scope.

---

## License

No license file is currently defined in this repository.

If you plan to open-source StrideX broadly, add a `LICENSE` file (for example, MIT, Apache-2.0, or GPL-3.0) and update this section accordingly.

---

## Disclaimer

StrideX is a research and educational software project for gait screening workflows. It is not a substitute for professional clinical judgment, diagnosis, or treatment.
