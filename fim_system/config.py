import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "fim.db")
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine")
MODEL_PATH = os.path.join(BASE_DIR, "core", "model.joblib")

# Monitoring settings
MONITORED_EXTENSIONS = None  # None means all, or list like ['.txt', '.py']

# Whitelist — files/paths matching these will never be flagged or quarantined
WHITELIST_PATHS = [
    'C:\\Windows',
    'C:\\Program Files',
    'C:\\Program Files (x86)',
    'C:\\ProgramData',
    'C:\\System Volume Information',
    'C:\\$Recycle.Bin',
    'C:\\Users\\User\\AppData',
    'C:\\Flutter'
]
WHITELIST_EXTENSIONS = ['.log', '.ini', '.tmp', '.bak', '.lock', '.json.lock']  # file extensions that are always considered safe

# Feature Engineering
MAX_FILE_SIZE_LOG = 20.0  # Log(size) max roughly corresponding to huge files

# ML Settings
CONTAMINATION = 0.05   # 5% sensitivity — more aggressive anomaly threshold
RANDOM_STATE = 42
N_ESTIMATORS = 300
MAX_SAMPLES = "auto"

# Auto-retrain: retrain model automatically after collecting this many new training samples
AUTO_RETRAIN_THRESHOLD = 100

# Security: XOR key for neutralizing quarantined files
QUARANTINE_KEY = 0x5A
