"""Sistem inferensi fuzzy Tsukamoto untuk skor kesehatan ayam (3 masukan, 6 aturan)."""
import random

def turun(x, a, b):
    """Keanggotaan linear turun: 1 pada x<=a, 0 pada x>=b."""
    return 1.0 if x <= a else 0.0 if x >= b else (b - x) / (b - a)

def naik(x, a, b):
    """Keanggotaan linear naik: 0 pada x<=a, 1 pada x>=b."""
    return 1.0 - turun(x, a, b)

# --- Fuzzifikasi ---
def fuzzifikasi(pakan, bersih, dsuhu):
    return {
        "pakan":  {"Kurang": turun(pakan, 40, 80), "Cukup": naik(pakan, 40, 80)},
        "bersih": {"Kotor":  turun(bersih, 30, 70), "Bersih": naik(bersih, 30, 70)},
        "suhu":   {"Kecil":  turun(dsuhu, 1, 5),    "Besar": naik(dsuhu, 1, 5)},
    }

# --- Basis aturan: (variabel, himpunan, keluaran) ---
ATURAN = [
    ("pakan", "Cukup", "Baik"),  ("pakan", "Kurang", "Buruk"),
    ("bersih", "Bersih", "Baik"), ("bersih", "Kotor", "Buruk"),
    ("suhu", "Kecil", "Baik"),   ("suhu", "Besar", "Buruk"),
]

# --- Invers himpunan keluaran monoton (Tsukamoto) ---
def z_invers(label, alpha):
    # Baik : mu = (z-40)/60 -> z = 40 + 60*alpha
    # Buruk: mu = (60-z)/60 -> z = 60 - 60*alpha
    return 40 + 60 * alpha if label == "Baik" else 60 - 60 * alpha

def inferensi(pakan, bersih, dsuhu, rinci=False):
    mu = fuzzifikasi(pakan, bersih, dsuhu)
    sum_a = sum_az = 0.0
    for i, (var, himp, out) in enumerate(ATURAN, 1):
        a = mu[var][himp]          # satu anteseden, maka alpha = derajat keanggotaan
        z = z_invers(out, a)
        if rinci:
            print(f"R{i}: {var}={himp:6s} -> {out:5s} | alpha={a:.2f} z={z:6.2f} alpha*z={a*z:7.3f}")
        sum_a += a
        sum_az += a * z
    return sum_az / sum_a          # defuzzifikasi rata-rata terbobot

if __name__ == "__main__":
    print("=== 1. Contoh perhitungan (pakan 70, bersih 50, dsuhu 2) ===")
    print(f"Skor = {inferensi(70, 50, 2, rinci=True):.2f}\n")

    print("=== 2. Kasus uji ===")
    kasus = [("Ideal", 100, 100, 0), ("Pakan kurang", 30, 100, 0),
             ("Kandang kotor", 100, 10, 0), ("Suhu menyimpang", 100, 100, 6),
             ("Dua masalah", 30, 10, 0), ("Semua buruk", 20, 10, 8)]
    for nama, p, b, s in kasus:
        print(f"{nama:16s} pakan={p:3d} bersih={b:3d} dsuhu={s} -> skor={inferensi(p, b, s):.1f}")

    print("\n=== 3. Uji monotonitas: sapuan satu variabel ===")
    def sapuan(nama, f, rentang):
        v = [f(x) for x in rentang]
        ok = all(v[i] >= v[i + 1] - 1e-9 for i in range(len(v) - 1))
        print(f"{nama}: {[round(x, 1) for x in v]} -> tidak naik: {ok}")
    sapuan("pakan 100->0   ", lambda x: inferensi(x, 100, 0), range(100, -1, -10))
    sapuan("bersih 100->0  ", lambda x: inferensi(100, x, 0), range(100, -1, -10))
    sapuan("dsuhu 0->8     ", lambda x: inferensi(100, 100, x), range(0, 9))

    print("\n=== 4. Uji monotonitas: 20.000 titik acak (seed 1) ===")
    random.seed(1)
    pelanggaran = 0
    for _ in range(20000):
        p, b, s = random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 10)
        dasar = inferensi(p, b, s)
        if (inferensi(min(100, p + 5), b, s) < dasar - 1e-9 or
                inferensi(p, min(100, b + 5), s) < dasar - 1e-9 or
                inferensi(p, b, max(0, s - 0.5)) < dasar - 1e-9):
            pelanggaran += 1
    print(f"Pelanggaran: {pelanggaran} dari 20000")

    print("\n=== 5. Kesetaraan dengan rata-rata derajat kondisi menguntungkan x 100 ===")
    random.seed(2)
    selisih = 0.0
    for _ in range(5000):
        p, b, s = random.uniform(0, 100), random.uniform(0, 100), random.uniform(0, 10)
        mu = fuzzifikasi(p, b, s)
        rata2 = 100 * (mu["pakan"]["Cukup"] + mu["bersih"]["Bersih"] + mu["suhu"]["Kecil"]) / 3
        selisih = max(selisih, abs(inferensi(p, b, s) - rata2))
    print(f"Selisih maksimum: {selisih:.6f}")