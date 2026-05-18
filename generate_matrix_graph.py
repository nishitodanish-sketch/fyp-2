import matplotlib.pyplot as plt
import numpy as np

# Data based on estimation
events = [
    "Fail Log OS (.log)", 
    "Dokumen Biasa (.pdf, .docx)", 
    "Skrip Tersembunyi (.ps1)", 
    "Ransomware Asas (.crypt)", 
    "Serangan Lanjutan (Entropi Tinggi)", 
    "Virus Dikenali (EICAR)"
]

# x = Kerumitan Analisis (Complexity of Analysis: 0 = Mudah/Peraturan, 10 = Sukar/AI)
x = [2, 3, 7, 1, 9, 0.5]

# y = Tahap Risiko (Risk Level: 0 = Selamat, 10 = Kritikal)
y = [1, 2, 6, 9, 8.5, 9.8]

# Colors representing severity
colors = ['#2ca02c', '#2ca02c', '#ff7f0e', '#d62728', '#d62728', '#8c564b']

plt.figure(figsize=(11, 8), facecolor='#f4f4f9')
plt.scatter(x, y, s=600, c=colors, alpha=0.8, edgecolors='black', linewidth=1.5)

# Add annotations
for i, txt in enumerate(events):
    plt.annotate(txt, (x[i], y[i]), xytext=(12, -5), textcoords='offset points', 
                 fontsize=10, weight='bold', color='#333333',
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=1, alpha=0.8))

# Draw Quadrant lines
plt.axvline(x=5, color='#888888', linestyle='--', linewidth=2)
plt.axhline(y=5, color='#888888', linestyle='--', linewidth=2)

plt.xlim(0, 10)
plt.ylim(0, 10)

plt.xlabel(r"Kerumitan Analisis (Mudah $\longrightarrow$ Sukar)", fontsize=12, weight='bold')
plt.ylabel(r"Tahap Risiko (Rendah $\longrightarrow$ Tinggi)", fontsize=12, weight='bold')
plt.title("Matriks Keputusan Pemprosesan Fail Sistem FIM", fontsize=16, weight='bold', color='#111111', pad=20)

# Quadrant labels
plt.text(2.5, 9.5, "Q1: Makluman & Kuarantin Cepat\n(Pengesanan Heuristik/Peraturan)", fontsize=11, ha='center', color='#8c564b', weight='bold', bbox=dict(facecolor='#ffcccc', alpha=0.6, edgecolor='none'))
plt.text(7.5, 9.5, "Q2: Analisis AI Mendalam\n(Pengesanan Anomali ML)", fontsize=11, ha='center', color='#d62728', weight='bold', bbox=dict(facecolor='#ffdddd', alpha=0.6, edgecolor='none'))
plt.text(2.5, 0.5, "Q3: Aktiviti Normal / Abaikan\n(Fail OS & Dokumen Biasa)", fontsize=11, ha='center', color='#2ca02c', weight='bold', bbox=dict(facecolor='#ccffcc', alpha=0.6, edgecolor='none'))
plt.text(7.5, 0.5, "Q4: Pemantauan Ketat\n(Skrip Mencurigakan)", fontsize=11, ha='center', color='#ff7f0e', weight='bold', bbox=dict(facecolor='#ffffcc', alpha=0.6, edgecolor='none'))

plt.grid(True, linestyle=':', alpha=0.5)
plt.tight_layout()
plt.savefig("keputusan_matriks_fim.png", dpi=300)
print("Graph saved as keputusan_matriks_fim.png")
