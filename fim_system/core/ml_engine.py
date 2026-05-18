import numpy as np
import joblib
import os
import json
import time as t
import zipfile
try:
    import py7zr
except ImportError:
    py7zr = None
from datetime import datetime
from sklearn.ensemble import IsolationForest
from database.db_manager import DatabaseManager
from config import MODEL_PATH, CONTAMINATION, RANDOM_STATE, N_ESTIMATORS, MAX_SAMPLES
from core.feature_extractor import DOC_EXTENSIONS

# --- HEURISTIC RULES CONFIG ---
BLACKLIST_EXTENSIONS = {'.locked', '.crypto', '.wnry', '.encrypted', '.clop', '.darkside', '.bitman'}
KNOWN_SAFE_HIGH_ENTROPY = {'.zip', '.rar', '.7z', '.gz', '.mp4', '.mp3', '.jpg', '.png', '.jpeg', '.dll', '.sys'}
SUSPICIOUS_SCRIPTS = {'.bat', '.sh', '.ps1', '.vbs', '.cmd'}
EICAR_SIGNATURE = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
MAX_MOD_THRESHOLD = 8  # events per file in a short window
ENCRYPTED_ARCHIVE_EXTENSIONS = {'.7z', '.zip', '.rar'}  # T1560.001 — archives to check for encryption

class MLEngine:
    def __init__(self):
        self.model = None
        self.is_fitted = False
        self.log = [] # For data visualization export
        self._last_mass_alert_time = 0
        self._alert_persistence_seconds = 10
        self.load_model()
        
    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.is_fitted = True
            except Exception as e:
                print(f"Failed to load model: {e}")
                self.model = IsolationForest(
                    n_estimators=N_ESTIMATORS, 
                    max_samples=MAX_SAMPLES, 
                    contamination=CONTAMINATION, 
                    random_state=RANDOM_STATE
                )
                self.is_fitted = False
        else:
            self.model = IsolationForest(
                n_estimators=N_ESTIMATORS, 
                max_samples=MAX_SAMPLES, 
                contamination=CONTAMINATION, 
                random_state=RANDOM_STATE
            )
            self.is_fitted = False

    def save_model(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            joblib.dump(self.model, MODEL_PATH)
        except Exception as e:
            print(f"Failed to save model: {e}")

    def train(self, data):
        """
        Trains the Isolation Forest model.
        :param data: List of feature vectors (lists of floats)
        """
        if not data:
            print("No data to train on.")
            return

        X = np.array(data)
        self.model.fit(X)
        self.is_fitted = True
        self.save_model()
        print("Model trained and saved.")

    def predict(self, feature_vector, file_path=None, event_count=0, file_hash=None, global_event_count=0, event_type=None):
        """
        Predicts if a file event is anomalous using a Hybrid approach.
        Returns: (score, verdict, reason)
        """
        now = t.time()
        log_entry = self._create_log_entry(feature_vector, file_path)
        
        # 🚨 THE BEHAVIORAL RULE OF LAW (T1485 / T1486)
        # If mass activity is detected, stop everything and go RED.
        if global_event_count >= 3 and event_type in ['deleted', 'moved']:
            self._last_mass_alert_time = now
            return self._finalize(log_entry, -1.0, -1, "Mass Activity")
            
        if now - self._last_mass_alert_time < self._alert_persistence_seconds:
            return self._finalize(log_entry, -1.0, -1, "Mass Activity (Ongoing)")

        from database.db_manager import DatabaseManager
        db = DatabaseManager()

        # LAYER 0: INTEGRITY BASELINE
        if file_path and file_hash and db.is_file_known(file_path, file_hash):
            return self._finalize(log_entry, 1.0, 1, "Known Safe")

        # LAYER 1: HEURISTIC RULES
        h_score, h_verdict, h_reason = self._check_heuristics(feature_vector, file_path, event_count, global_event_count, event_type)
        if h_verdict == -1:
            return self._finalize(log_entry, h_score, h_verdict, h_reason)
        # Bypass ML if heuristics explicitly verified the file as safe (score > 0)
        if h_verdict == 1 and h_score > 0:
            return self._finalize(log_entry, h_score, h_verdict, h_reason)

        # LAYER 2: MACHINE LEARNING
        if not self.is_fitted:
            return self._finalize(log_entry, 0.0, 1, "Model Not Trained")

        X = np.array([feature_vector])
        score = self.model.decision_function(X)[0]
        verdict = self.model.predict(X)[0]
        
        reason = "AI Anomaly" if verdict == -1 else "Normal"
        return self._finalize(log_entry, score, verdict, reason)

    def _create_log_entry(self, feature_vector, file_path):
        return {
            "timestamp": datetime.now().isoformat(),
            "filename": file_path if file_path else "unknown",
            "entropy": round(float(feature_vector[33]), 4),
            "file_size": round(float(feature_vector[32]), 4),
            "size_change_rate": round(float(feature_vector[45]), 4),
            "modification_freq": round(float(feature_vector[46]), 4),
            "score": 0.0,
            "verdict": 1
        }

    def _check_heuristics(self, feature_vector, file_path, event_count, global_event_count=0, event_type=None):
        """SonarQube: Extracted heuristic logic to reduce complexity."""
        
        # 1. File-based rules (Extensions, Activity, Mass Modification)
        res = self._check_file_rules(file_path, event_count, global_event_count, event_type)
        if res:
            score, verdict, reason = res
            return score, verdict, reason

        # 2. Content-based rules (Signatures)
        res = self._check_content_rules(file_path)
        if res:
            score, verdict, reason = res
            return score, verdict, reason

        # 3. Statistical-based rules (Entropy, Executability)
        return self._check_statistical_rules(feature_vector, file_path, event_count)

    def _check_file_rules(self, file_path, event_count, global_event_count=0, event_type=None):
        if not file_path:
            return None
        
        # MASS MODIFICATION CHECK (T1485 / T1486)
        now = t.time()
        if global_event_count > 5 and event_type in ['deleted', 'moved']:
            self._last_mass_alert_time = now
            return -1.0, -1, "Mass Activity"
            
        # Persistence: If we had a mass alert recently, keep it Critical
        if now - self._last_mass_alert_time < self._alert_persistence_seconds:
            return -1.0, -1, "Mass Activity (Ongoing)"

        ext = os.path.splitext(file_path)[1].lower()
        if ext in BLACKLIST_EXTENSIONS:
            return -1.0, -1, "Blacklisted Ext"
        if event_count >= MAX_MOD_THRESHOLD:
            return -0.9, -1, "High Frequency"

        # T1560.001 — Encrypted Archive Detection
        res = self._check_encrypted_archive(file_path)
        if res:
            return res

        return None

    def _check_encrypted_archive(self, file_path):
        """Detects password-protected archives — indicator of T1560.001 (Archive Collected Data)."""
        if not file_path or not os.path.exists(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ENCRYPTED_ARCHIVE_EXTENSIONS:
            return None

        try:
            # --- .7z files: use py7zr ---
            if ext == '.7z':
                if py7zr is not None:
                    try:
                        with py7zr.SevenZipFile(file_path, 'r') as z:
                            if z.needs_password():
                                return -0.85, -1, "Encrypted Archive (T1560.001)"
                        return 1.0, 1, "Verified Safe Archive"  # confirmed no password
                    except Exception as e:
                        print(f"[DEBUG] _check_encrypted_archive .7z error: {type(e).__name__}: {e}")
                        return None  # file may still be writing, skip
                return None

            # --- .zip files: use built-in zipfile ---
            if ext == '.zip':
                try:
                    with zipfile.ZipFile(file_path, 'r') as z:
                        for info in z.infolist():
                            if info.flag_bits & 0x1:  # encryption bit set
                                return -0.85, -1, "Encrypted Archive (T1560.001)"
                    return 1.0, 1, "Verified Safe Archive"  # no encrypted entries
                except zipfile.BadZipFile:
                    return None

        except Exception:
            pass

        return None

    def _check_content_rules(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            if os.path.getsize(file_path) < 1024:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                    if EICAR_SIGNATURE in content:
                        return -1.0, -1, "EICAR Signature"
        except Exception:
            pass
        return None

    def _check_statistical_rules(self, feature_vector, file_path, event_count):
        entropy = feature_vector[33]
        # S1244: Avoid float equality check
        is_executable = feature_vector[40] > 0.5 
        size_change_ratio = feature_vector[45]
        ext = os.path.splitext(file_path)[1].lower() if file_path else ""

        if entropy >= 0.90 and is_executable:
            return -0.30, -1, "High Entropy Exec"
        if ext in SUSPICIOUS_SCRIPTS:
            return -0.10, -1, "Suspicious Script"
        if entropy >= 0.85 and ext not in DOC_EXTENSIONS and ext not in KNOWN_SAFE_HIGH_ENTROPY:
            return -0.25, -1, "High Entropy"
        if entropy >= 0.90 and ext in DOC_EXTENSIONS and event_count >= 3:
            return -0.20, -1, "Sus. Doc Modification"
        if event_count >= 5 and size_change_ratio >= 0.3:
            return -0.05, -1, "Abnormal Activity"
        
        return 0.0, 1, "Normal"

    def _finalize(self, log_entry, score, verdict, reason="Unknown"):
        log_entry["score"] = round(float(score), 4)
        log_entry["verdict"] = int(verdict)
        log_entry["reason"] = reason
        self.log.append(log_entry)
        return score, verdict, reason

    def export_data(self, filepath="fim_export.csv"):
        """Exports the prediction log to a CSV file for visualization, including Ground Truth for FYP metrics."""
        import csv
        if not self.log:
            print("No data in log to export.")
            return

        try:
            # 1. Inject Ground Truth & Confusion Matrix labels
            malicious_keywords = ['akira', 'sdelete', 'payload', 'eicar', 'stolen', 'suspicious', 'malware', 'atomictest', 'script']
            
            for row in self.log:
                file_str = str(row.get('file', '')).lower()
                is_malicious = any(kw in file_str for kw in malicious_keywords)
                
                # Ground truth verdict (-1 for Malicious, 1 for Normal)
                row['Actual_Verdict'] = -1 if is_malicious else 1
                
                # String labels for the external AI
                row['Predicted_Label'] = 'Malicious' if row.get('verdict') == -1 else 'Normal'
                row['Actual_Label'] = 'Malicious' if row['Actual_Verdict'] == -1 else 'Normal'
                
                # Confusion Matrix Calculation
                if row['Predicted_Label'] == 'Malicious' and row['Actual_Label'] == 'Malicious':
                    row['Confusion_Matrix'] = 'True Positive'
                elif row['Predicted_Label'] == 'Normal' and row['Actual_Label'] == 'Normal':
                    row['Confusion_Matrix'] = 'True Negative'
                elif row['Predicted_Label'] == 'Malicious' and row['Actual_Label'] == 'Normal':
                    row['Confusion_Matrix'] = 'False Positive'
                else:
                    row['Confusion_Matrix'] = 'False Negative'

            # 2. Export to CSV
            keys = self.log[0].keys()
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.log)
            print(f"Data exported to {filepath} ({len(self.log)} records)")
        except Exception as e:
            print(f"Failed to export data: {e}")

    @staticmethod
    def get_severity(score, verdict):
        """
        Converts an anomaly score + verdict into a severity label.
        IsolationForest decision_function: lower score = more anomalous.
        """
        if verdict == 1:
            return "Normal"
        if score >= -0.05:
            return "Low"
        elif score >= -0.15:
            return "Medium"
        else:
            return "Critical"
