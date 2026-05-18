# 🛡️ FIM System Demonstration Guide (FYP)

Panduan ini menyediakan langkah demi langkah untuk menunjukkan kehebatan sistem **Anomaly-Based File Integrity Monitoring** anda menggunakan simulasi serangan standard industri (ART).

---

## 🏗️ Persediaan Awal (Prerequisites)
1.  Buka **FIM Application** (Jalankan sebagai **Administrator**).
2.  Pergi ke **Settings** dan pastikan folder berikut telah ditambah:
    *   `C:\` (Untuk ujian Akira)
    *   `C:\Users\User\Documents\test1` (Untuk ujian SDelete & T1560.001)
3.  Klik **Start Protection** pada Dashboard.

---

## 🧪 Senario 1: Serangan Ransomware Akira (MITRE T1486)
Mensimulasikan serangan ransomware sebenar yang menjatuhkan fail `.akira` secara pukal.

1.  Buka **PowerShell (Administrator)**.
2.  Import modul ART dari folder demo anda:
    ```powershell
    cd "C:\Users\User\Documents\demo\AtomicRedTeam\Invoke-AtomicRedTeam"
    Import-Module .\Invoke-AtomicRedTeam.psm1 -Force
    ```
3.  Jalankan serangan Akira:
    ```powershell
    Invoke-AtomicTest T1486 -TestNumbers 10 -PathToAtomicsFolder "C:\Users\User\Documents\demo\AtomicRedTeam\atomics"
    ```
4.  **Apa yang diperhatikan:** Dashboard akan berkelip merah (**CRITICAL**) kerana sistem mengesan perubahan pantas pada integriti fail sistem.

---

## 🧪 Senario 2: Data Destruction / Sabotaj (MITRE T1485)
Mensimulasikan teknik pemadaman fail secara kekal menggunakan alat `SDelete`.

1.  Buka PowerShell dan pergi ke folder alat serangan:
    ```powershell
    cd "C:\Users\User\Documents\demo\AtomicRedTeam\ExternalPayloads\Sdelete"
    ```
2.  Cipta 10 fail ujian (Manga) jika folder kosong:
    ```powershell
    1..10 | ForEach-Object { "Data simulasi $_" | Out-File "C:\Users\User\Documents\test1\fail_$_.txt" }
    ```
3.  Jalankan pemadaman paksa menggunakan SDelete:
    ```powershell
    .\sdelete.exe -p 1 -q "C:\Users\User\Documents\test1\*.txt"
    ```
4.  **Apa yang diperhatikan:** Sistem mengesan lebih daripada 5 fail dipadam dalam masa 5 saat, secara automatik menukar status kepada **CRITICAL** (Warna Merah) dengan label **"Mass Activity"**. Amaran ini kekal muncul sepanjang proses pemadaman berlaku.

---

## 🧪 Senario 3: Pencurian Data (Exfiltration/Archiving) (MITRE T1560.001)
Mensimulasikan teknik penggodam memampatkan dan menyulitkan (encrypt) data penting menggunakan 7-zip sebelum memindahkannya keluar.

1.  Pastikan anda sedang memantau folder `C:\Users\User\Documents\test1`.
2.  Buka **PowerShell** dan jalankan arahan ART berikut:
    ```powershell
    powershell -Command "Import-Module C:\Users\User\Documents\demo\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1; Invoke-AtomicTest T1560.001 -TestNumbers 4 -PathToAtomicsFolder C:\Users\User\Documents\demo\AtomicRedTeam\atomics"
    ```
3.  **Apa yang diperhatikan:** FIM anda akan serta-merta mengesan penciptaan arkib baru, memeriksa fail tersebut, dan jika ia dilindungi kata laluan (password-protected), GUI akan mencetuskan amaran **CRITICAL** dengan label **"Encrypted Archive (T1560.001)"**.

---

## 🧪 Senario 4: Pengesanan Tandatangan Malware / Obfuscation (MITRE T1027.013)
Menguji keupayaan Hibrid (AI + Signature) sistem FIM dalam mengesan fail hasad yang cuba disembunyikan menggunakan pengekodan (encoding). Ujian ini menggunakan kod EICAR (Standard Antivirus Antarabangsa).

> [!IMPORTANT]
> **Penting:** Pastikan anda mematikan/tutup (Off) "Real-time Protection" pada **Windows Defender** anda seketika untuk simulasi ini. Jika tidak, Defender akan memadam fail EICAR sekelip mata sebelum FIM sempat mengimbasnya!

1.  Pastikan Windows Defender dimatikan (sementara).
2.  Jalankan arahan ART ini di **PowerShell**:
    ```powershell
    powershell -Command "Import-Module C:\Users\User\Documents\demo\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1; Invoke-AtomicTest T1027.013 -TestNumbers 1 -PathToAtomicsFolder C:\Users\User\Documents\demo\AtomicRedTeam\atomics"
    ```
3.  **Apa yang diperhatikan:** Sebaik sahaja ART mengekstrak fail `T1027.013_decodedEicar.txt` ke dalam cakera keras, enjin statik FIM akan terus membaca kod di dalamnya dan melabelnya sebagai **CRITICAL** dengan label **"EICAR Signature"**. (Jangan lupa *On* semula Windows Defender selepas ini).

---

## 🔄 Senario 5: Pemulihan Fail (Restore) & Audit
Tunjukkan keupayaan sistem memulihkan fail yang terjejas.

1.  Pergi ke tab **Quarantine**.
2.  Pilih fail yang telah "dipadam" atau "dikunci" tadi.
3.  Klik **Restore Selected** (Membuktikan keupayaan *Self-Healing*).
4.  Klik **Export CSV** di tab Events untuk menunjukkan bukti audit bagi laporan forensik.

---

> [!TIP]
> Semasa demo, tekankan bahawa sistem ini menggunakan **AI (Isolation Forest)** untuk mengesan anomali tingkah laku, bukan sekadar database virus biasa!
