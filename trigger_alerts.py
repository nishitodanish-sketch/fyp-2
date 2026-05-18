import os
import time

FOLDER = r"c:\Users\User\Documents\SYSTEM_FYP2026\FYP2\apip testing"

def trigger_medium():
    print("Mencipta fail tahap MEDIUM (Suspicious Script)...")
    path = os.path.join(FOLDER, "simulasi_penggodam.bat")
    with open(path, "w") as f:
        f.write("echo 'Mencuri data...'")
    print(" Selesai MEDIUM")
    print("Selesai MEDIUM")

def trigger_critical():
    print("Mencipta fail tahap CRITICAL (Unknown Ext + High Entropy)...")
    path = os.path.join(FOLDER, "semua_rosak.locked")
    with open(path, "wb") as f:
        # Menulis 50KB data rawak (Entropi Hampir 8.0)
        f.write(os.urandom(1024 * 50))
    print("Selesai CRITICAL")

def trigger_critical_rapid():
    print("Mencipta fail tahap CRITICAL (Rapid Encrypted Document Rewrite)...")
    path = os.path.join(FOLDER, "simpanan_rahsia.pdf")
    
    # Untuk mencapai tahap CRITICAL, fail dokumen (.pdf) perlu:
    # 1. Berentropi tinggi
    # 2. Dimodifikasi banyak kali (melepasi sistem debounce 1.0 saat)
    for i in range(5):
        with open(path, "ab") as f:
            f.write(os.urandom(1024 * 10)) # Tambah 10KB rawak
        time.sleep(1.2) # Tunggu sikit supaya FIM tak buang (debounce) event ni
    print(" Selesai CRITICAL (Rapid)")

def trigger_low():
    print("Mencipta fail tahap LOW (Rapid Massive Modification pada fail biasa)...")
    path = os.path.join(FOLDER, "aktiviti_pelik.txt")
    
    # 1. Bina asas fail
    with open(path, "w") as f:
        f.write("Teks biasa " * 100)
    time.sleep(1.2)
    
    # 2. Modifikasi dengan sangat pantas (> 6 kali)
    for i in range(6):
        with open(path, "a") as f:
            f.write("Perubahan besar besaran! " * 500)
        time.sleep(1.2)
    print(" Selesai LOW")

if __name__ == "__main__":
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
        
    trigger_medium()
    time.sleep(2)
    trigger_critical()
    time.sleep(2)
    trigger_critical_rapid()
    time.sleep(2)
    trigger_low()
    
    print("\n🎉 Siap! Semua tahap telah dilakonkan. Sila semak tab 'Live Events' di GUI FIM anda.")
