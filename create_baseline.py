import os
import sys
import hashlib
import time

sys.path.insert(0, os.path.abspath('fim_system'))
from database.db_manager import DatabaseManager

def get_sha256(file_path):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def create_baseline(folders_to_baseline):
    db = DatabaseManager()
    total_added = 0
    
    print("\n=== MEMBINA BASELINE INTEGRITI SISTEM ===\n")
    
    for folder in folders_to_baseline:
        if not os.path.exists(folder):
            print(f"[!] Folder tidak dijumpai, melangkau: {folder}")
            continue
            
        print(f"[*] Mengimbas: {folder} ...")
        count = 0
        for root, _, files in os.walk(folder):
            for name in files:
                file_path = os.path.join(root, name)
                file_hash = get_sha256(file_path)
                
                if file_hash:
                    db.add_to_baseline(file_path, file_hash)
                    count += 1
                    total_added += 1
                    
                    if count % 100 == 0:
                        print(f"    - Berjaya mendaftarkan {count} fail...")
        
        print(f"[+] Selesai untuk {folder}: {count} fail didaftarkan.\n")
    
    print(f"=== BASELINE SELESAI: {total_added} fail kini dipercayai 100% ===\n")

if __name__ == "__main__":
    # Folder yang kita mahu AI 'percaya' 100% sebagai program asal
    paths = [
        r"C:\Windows\System32\drivers\etc", # Contoh kecil untuk demo pantas
        # r"C:\Windows",                   # Amaran: Ini akan ambil masa lama!
        r"C:\Program Files\Google\Chrome",   # Contoh program biasa
        r"C:\Users\User\AppData\Local\Packages\AD2F1837.myHP_v10z8vjag6ke6" # Folder HP yang bising tadi
    ]
    
    # Minta input atau gunakan default
    print("Skrip ini akan mendaftarkan fail sebagai 'SAFE' dalam database.")
    print("AI tidak akan mengganggu fail yang ada dalam folder ini selepas ini.")
    
    create_baseline(paths)
