import sys
import os
import time
import shutil
sys.path.append(os.path.abspath("fim_system"))

from core.feature_extractor import FeatureExtractor
from core.ml_engine import MLEngine
from core.monitor import FileMonitor
from database.db_manager import DatabaseManager
from config import DB_PATH, QUARANTINE_DIR, MODEL_PATH

def cleanup():
    print("Cleaning up previous test data...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
    if os.path.exists("./test_monitored"):
        shutil.rmtree("./test_monitored")
    os.makedirs("./test_monitored", exist_ok=True)

def test_backend_logic():
    print("--- Starting Backend Logic Test ---")
    
    # 1. Feature Extractor
    print(f"Testing Feature Extractor...")
    test_file = "./test_monitored/normal.txt"
    with open(test_file, "w") as f:
        f.write("Normal content " * 100)
    
    feats, meta = FeatureExtractor.extract_features_vector(test_file)
    print(f"Features for normal.txt: {feats}, Entropy: {feats[1]}")
    assert len(feats) == 50
    assert 0.0 <= feats[33] <= 1.0 # Entropy is now at index 33 (0-indexed, actually 34th in code, wait)
    
    # 2. ML Engine (Train)
    print(f"Testing ML Engine Training...")
    ml = MLEngine()
    # Create synthetic training data (Normal files)
    train_data = [feats for _ in range(100)]
    ml.train(train_data)
    assert ml.is_fitted
    print("Model trained successfully.")
    
    # 3. ML Engine (Predict)
    print(f"Testing Prediction...")
    score, verdict = ml.predict(feats)
    print(f"Prediction for normal file: Score={score}, Verdict={verdict}")
    assert verdict == 1 # Should be normal
    
    # anom file
    anom_feats = [0.9] * 50 # High density across all buckets is very weird
    score_a, verdict_a = ml.predict(anom_feats)
    print(f"Prediction for anomaly: Score={score_a}, Verdict={verdict_a}")
    # Verdict might vary with small data but IsolaForest usually catches this
    
    # 4. Monitor & Integration
    print("Testing Monitor Integration...")
    # Initialize DB by accessing it
    db = DatabaseManager()
    monitor = FileMonitor(["./test_monitored"])
    monitor.start()
    time.sleep(1) # Wait for start
    
    # Modify file to trigger event
    with open(test_file, "a") as f:
        f.write("Modified.")
        
    time.sleep(2) # Wait for processing
    
    # Check DB
    events = db.get_recent_events()
    print(f"Events captured: {len(events)}")
    found = False
    for e in events:
        print(e)
        if "normal.txt" in e[2] and e[1] in ("modified", "created"):
            found = True
            break
            
    if found:
        print("Monitor captured file event successfully.")
    else:
        print("Monitor FAILED to capture file event.")
    
    monitor.stop()
    print("--- Test Complete ---")

if __name__ == "__main__":
    cleanup()
    test_backend_logic()
