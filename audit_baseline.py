import sys
import os
sys.path.insert(0, os.path.abspath('fim_system'))
from core.feature_extractor import FeatureExtractor

def audit_clean_dir(directory):
    fe = FeatureExtractor()
    files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    
    print(f"Auditing {len(files)} files in {directory}...\n")
    high_entropy_count = 0
    for f in files[:20]: # Check first 20
        vector, _ = fe.extract_features_vector(f)
        entropy = vector[33]
        print(f"File: {os.path.basename(f)} | Entropy: {entropy:.4f}")
        if entropy > 0.8:
            high_entropy_count += 1
            
    print(f"\nAudit complete. Found {high_entropy_count} high-entropy files in first 20.")

if __name__ == "__main__":
    audit_clean_dir(r"sample_dataset\clean")
