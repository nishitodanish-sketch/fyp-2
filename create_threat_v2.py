import os

# Cipta fail teks dengan data rawak (Entropi Tinggi)
path = r"apip testing\secret_data.txt"
with open(path, "wb") as f:
    f.write(os.urandom(1024 * 30)) # 30KB random data

print(f"Fail {path} dicipta. Mari kita lihat jika AI dapat menangkapnya!")
