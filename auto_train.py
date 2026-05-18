import sys
import os
import time

sys.path.append(os.path.abspath("fim_system"))
from core.monitor import FileMonitor # type: ignore
from database.db_manager import DatabaseManager # type: ignore
from core.ml_engine import MLEngine # type: ignore
import json

def do_training():
    print("Membaca tetapan folder...")
    # Get monitored folders from config/db
    db = DatabaseManager()
    
    paths = [
        r"C:\Users\User\Documents\SYSTEM_FYP2026\FYP2\sample_dataset\000\000"
    ]
        
    print(f"Folder dipantau untuk training: {paths}")
    
    monitor = FileMonitor(paths)
    
    print("\nLangkah 1: Mengumpul data dari fail sedia ada (Training Mode)...")
    scanned, failed = monitor.scan_existing_files(training_mode=True)
    print(f"Selesai kumpul data! Berjaya: {scanned}, Gagal: {failed}")
    
    time.sleep(3) # Wait for db writing to finish
    
    print("\nLangkah 2: Melatih Model AI (Isolation Forest)...")
    monitor.train_model()
    
    print("\nModel AI berjaya dilatih dan disimpan! Anda boleh mula uji FIM sekarang.")

if __name__ == "__main__":
    do_training()
