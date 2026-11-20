"""Central configuration for the screening system."""

# Risk fusion weights (must add up to 1.0)
WEIGHTS = {
    "tamper": 0.30,
    "validation": 0.25,
    "face_mismatch": 0.25,
    "blacklist_duplicate": 0.20,
}

# Risk level thresholds
THRESHOLD_HIGH = 0.7
THRESHOLD_MEDIUM = 0.4

# Face matching threshold (cosine similarity)
FACE_MATCH_THRESHOLD = 0.5

# Paths
DATA_DIR = "data"
SAMPLES_DIR = "data/samples"
MOCK_DB_DIR = "data/mock_db"
MODELS_DIR = "models"
