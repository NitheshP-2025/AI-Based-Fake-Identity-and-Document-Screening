# AI-Based Fake Identity & Document Screening System

An AI-powered decision-support tool that analyzes identity and travel documents, detects signs of forgery or tampering, validates the data, verifies the holder's face, and produces an explainable risk score for border-security or KYC officers.

Built for the UNAI TECH Virtual Internship Program 2026 (AI & Automation).

## System Architecture
<img width="940" height="589" alt="image" src="https://github.com/user-attachments/assets/e3892490-04ca-47dc-a71e-1ddb08cea3bf" />




**Workflow:** the input image goes through preprocessing, then OCR extracts the fields. Validation, tampering detection, and face verification run on the result. The risk engine combines their outputs into a Low / Medium / High score with reasons, which is shown on a dashboard and stored in an audit log.

## Modules

| Module | Responsibility |
|---|---|
| Preprocessing | Deskew, denoise, and crop document images (OpenCV) |
| 1. OCR Extraction | Extract name, document number, DOB, expiry, and visa details; parse the MRZ |
| 2. Document Validation | ICAO 9303 checksums, MRZ vs printed-field cross-check, date rules, blacklist lookup |
| 3. Tampering Detection | EXIF metadata, Error Level Analysis, copy-move detection, CNN classifier with heatmaps |
| 4. Face Verification | Match the document photo to a live selfie using face embeddings |
| Risk Engine | Weighted fusion of all signals into an explainable risk level |
| Database | SQLite audit trail and mock blacklist |
| API + Dashboard | FastAPI backend and Streamlit interface |

## Project Structure

```
├── docs/          architecture diagram and documentation
├── data/          sample, tampered, and mock-database files
├── src/
│   ├── preprocessing/
│   ├── ocr/
│   ├── validation/
│   ├── tampering/
│   ├── face/
│   ├── risk_engine/
│   ├── database/
│   └── api/
├── app/           Streamlit dashboard
├── models/        trained model weights
├── tests/         unit tests
└── scripts/       helper scripts
```

## Tech Stack

Python, OpenCV, PyTorch, EasyOCR/PaddleOCR, InsightFace, FastAPI, Streamlit, SQLite.

## Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts\verify_env.py
```

## Roadmap

- [x] Environment setup and repository
- [x] Project structure and architecture
- [ ] MRZ parsing and OCR
- [ ] Validation rules
- [ ] Tampering detection
- [ ] Face verification
- [ ] Risk engine, dashboard, and audit log

## Limitations

This is a decision-support prototype. Final decisions are made by human officers. It uses synthetic and public datasets only, and the blacklist is a mock database.
