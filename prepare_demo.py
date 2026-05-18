import os
import shutil
import sqlite3

def prepare():
    print("=== PERSEDIAAN DEMO FIM (CLEAN START) ===")
    
    # 1. Tutup database lama
    db_path = os.path.join('fim_system', 'database', 'fim.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("[+] Database lama dipadam.")

    # 2. Kosongkan folder kuarantin
    quarantine_path = os.path.join('fim_system', 'quarantine')
    if os.path.exists(quarantine_path):
        shutil.rmtree(quarantine_path)
        print("[+] Folder kuarantin lama dibersihkan.")
    os.makedirs(quarantine_path)
    print("[+] Folder kuarantin baru dicipta.")

    # 3. Jalankan inisialisasi database baru
    # (Akan automatik dicipta apabila aplikasi dijalankan)
    
    print("\n[SUCCESS] Sistem anda kini bersih dan sedia untuk DEMO!")
    print("Sila jalankan aplikasi FIM sebagai ADMINISTRATOR sekarang.")

if __name__ == "__main__":
    prepare()
