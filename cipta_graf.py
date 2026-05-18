import matplotlib
matplotlib.use('Agg') # Menghalang isu GUI hang
import matplotlib.pyplot as plt

# Data Pilihan
events = [
    "EICAR (Virus Dikenali)", 
    "Fail .crypt (Ransomware)", 
    "Entropi Tinggi Mendadak (AI)", 
    "Modifikasi Fail Serentak", 
    "Proses OS / Fail Log", 
    "Edit Dokumen Biasa", 
    "Skrip Asing (.ps1, .bat)"
]

# Koordinat
x = [1, 2, 8.5, 7.5, 1, 2.5, 7]
y = [9, 8.5, 9, 7.5, 1, 2, 6]
colors = ['#ff3333', '#ff3333', '#800000', '#800000', '#33cc33', '#33cc33', '#ff9900']

# Cipta Rajah
plt.figure(figsize=(11, 8), facecolor='white')
plt.scatter(x, y, s=500, c=colors, alpha=0.9, edgecolors='black', linewidth=1.5)

# Teks Label
for i, txt in enumerate(events):
    plt.annotate(txt, (x[i], y[i]), xytext=(15, -5), textcoords='offset points', 
                 fontsize=11, weight='bold', 
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f9f9f9", ec="gray", lw=1))

# Garisan Pembahagi Kuadran
plt.axvline(x=5, color='#aaaaaa', linestyle='--', linewidth=2)
plt.axhline(y=5, color='#aaaaaa', linestyle='--', linewidth=2)

plt.xlim(0, 10)
plt.ylim(0, 10)

plt.xlabel(r"Kerumitan Analisis (Kiri: Mudah / Peraturan $\longrightarrow$ Kanan: Kompleks / AI)", fontsize=13, weight='bold')
plt.ylabel(r"Tahap Risiko (Bawah: Selamat $\longrightarrow$ Atas: Berbahaya)", fontsize=13, weight='bold')
plt.title("Matriks Keputusan Pemprosesan Fail Sistem FIM", fontsize=16, weight='bold', pad=20)

# Label Kuadran
plt.text(2.5, 9.5, "Q1: Kuarantin Heuristik\n(Tindakan Pantas)", fontsize=13, ha='center', color='red', weight='bold')
plt.text(7.5, 9.5, "Q2: Analisis Anomali AI\n(Pemprosesan Mendalam)", fontsize=13, ha='center', color='#800000', weight='bold')
plt.text(2.5, 0.5, "Q3: Aktiviti Normal\n(Abaikan & Rekod)", fontsize=13, ha='center', color='green', weight='bold')
plt.text(7.5, 0.5, "Q4: Pemantauan AI\n(Mencurigakan)", fontsize=13, ha='center', color='#cc7a00', weight='bold')

plt.grid(True, linestyle=':', alpha=0.5)
plt.tight_layout()

# Simpan Imej
output_path = r"c:\Users\User\Documents\SYSTEM_FYP2026\FYP2\graf_matriks_fim.png"
plt.savefig(output_path, dpi=300)
print(f"Imej berjaya disimpan di {output_path}")
