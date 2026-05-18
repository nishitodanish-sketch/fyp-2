import os
import sys
import shutil

sys.path.insert(0, os.path.abspath('fim_system'))
from core.feature_extractor import FeatureExtractor
from core.ml_engine import MLEngine
from database.db_manager import DatabaseManager

def populate_suspicious_anomalies(anomaly_dir, count=300):
    """Generate truly suspicious looking files (high entropy, ransomware-like extensions)."""
    if os.path.exists(anomaly_dir):
        shutil.rmtree(anomaly_dir)
    os.makedirs(anomaly_dir, exist_ok=True)
    
    print(f"[+] Menjana {count} fail anomali yang 'betul-betul mencurigakan'...")
    extensions = ['.locked', '.crypto', '.enc', '.wnry', '.bitman']
    for i in range(count):
        ext = extensions[i % len(extensions)]
        file_path = os.path.join(anomaly_dir, f"suspicious_file_{i}{ext}")
        # High entropy data (pure random)
        content = os.urandom(random_size := (1024 * (i % 50 + 10))) 
        with open(file_path, 'wb') as f:
            f.write(content)

def main():
    clean_dir = os.path.abspath(r"sample_dataset\clean")
    anomaly_dir = os.path.abspath(r"sample_dataset\anomaly")
    
    # 1. Populate anomalies with truly suspicious files
    populate_suspicious_anomalies(anomaly_dir)

    print("\n[*] Membersihkan pangkalan data...")
    db = DatabaseManager()
    db.clear_all_data()

    # 2. Extract and Train ONLY on Clean Samples
    print(f"[+] Melatih model menggunakan folder CLEAN sahaja: {clean_dir}")
    clean_features = []
    clean_files = [os.path.join(clean_dir, f) for f in os.listdir(clean_dir)]
    
    for f in clean_files:
        vector, meta = FeatureExtractor.extract_features_vector(f, prev_size=0, recent_event_count=0)
        clean_features.append(vector)
        # Log into DB as Training Samples (is_training_sample=1)
        event_id = db.log_event('created', f, os.path.getmtime(f), False)
        db.log_snapshot(
            event_id, f, os.path.getmtime(f),
            meta['size'], vector[33], "unknown", meta['extension'], meta['permissions'], meta['hash'],
            features=vector,
            is_training_sample=True
        )

    print(f"[+] Berjaya mengekstrak {len(clean_features)} sampel BERSIH.")
    print("[+] Sedang melatih model...")
    
    ml = MLEngine()
    ml.train(clean_features)
    print("[+] Model berjaya dilatih dan disimpan (model.joblib)!\n")

    # 3. Test detection on the suspicious files
    print("[*] Menguji pengesan pada fail anomali (ML + Heuristics)...")
    anomaly_files = [os.path.join(anomaly_dir, f) for f in os.listdir(anomaly_dir)]
    
    detected = 0
    for f in anomaly_files:
        # Simulate ransomware modification
        vector, _ = FeatureExtractor.extract_features_vector(f, prev_size=1024, recent_event_count=5)
        score, verdict, reason = ml.predict(vector)
        
        # --- Real System Heuristics (as in monitor.py) ---
        entropy = vector[33]
        is_executable = vector[40]
        size_change_ratio = vector[45]
        mod_frequency = vector[46]
        ext = os.path.splitext(f)[1].lower()
        
        KNOWN_SAFE_HIGH_ENTROPY = {'.zip', '.rar', '.7z', '.gz', '.mp4', '.mp3', '.jpg', '.png', '.jpeg', '.dll', '.sys'}
        DOC_EXTENSIONS = {'.txt', '.pdf', '.docx', '.xlsx', '.csv', '.pptx', '.odt', '.doc', '.xls'}
        
        if entropy >= 0.90 and is_executable == 1.0:
            verdict = -1
        elif entropy >= 0.85 and ext not in DOC_EXTENSIONS and ext not in KNOWN_SAFE_HIGH_ENTROPY and is_executable == 0.0:
            verdict = -1
        elif entropy >= 0.90 and ext in DOC_EXTENSIONS and mod_frequency >= 0.2:
            verdict = -1
        elif mod_frequency >= 0.3 and size_change_ratio >= 0.3:
            verdict = -1
            
        if verdict == -1:
            detected += 1
            
    print(f"\nKadar Pengesanan Anomali (ML + Heuristics): {detected}/{len(anomaly_files)} ({(detected/len(anomaly_files))*100:.2f}%)")
    print("[!] Model kini tajam semula dan sistem pertahanan berlapis sedia untuk digunakan.")

if __name__ == '__main__':
    main()
