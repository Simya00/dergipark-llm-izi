#!/usr/bin/env python3
"""
Yillara Gore Asiri Kelime Sayisi (Kobak vd. Sekil 2'nin karsiligi)
===================================================================
Asiri kelime hesabini (asiri_kullanim.py, Kobak vd. kurali) TEK bir hedef yil
yerine her yil icin tekrarlar. Kobak vd. gibi her hedef yil T icin taban T-2
alinir (egilim T-3 -> T-2, iki yil ileri uzatilir).

Amac: "2024'te 5.846 asiri kelime" tek basina bir sey soylemez; kucuk veride
rastlantisal dalgalanma da asiri kelime uretir. Asil soru: LLM oncesi yillarda
(2018-2022) her yil kac asiri kelime cikiyordu, 2023 sonrasi bundan farkli mi?
Kobak vd.'nin ana bulgusu da bu karsilastirma.

Cikti:
  - Ekrana: yil basina asiri kelime sayisi; >= --saglamlik ozette gecenler
    (2026-11-11 karari: her sonuc iki bicimde); delta > 0.01 olanlar.
  - asiri_kelimeler_<dil>.tsv: herhangi bir yilda asiri cikan TUM kelimeler,
    hangi yillarda cikti, en buyuk delta ve oran, en yuksek ozet sayisi.
    Bu dosya elle icerik / uslup isaretlemesinin girdisi olacak.

Kullanim:
  python3 yillara_gore_asiri.py --dil tr
  python3 yillara_gore_asiri.py --dil tr --yillar 2018-2025 --saglamlik 30
"""

import argparse
import csv
from pathlib import Path
from collections import defaultdict

from asiri_kullanim import KLASOR, asiri_hesapla, harf_filtresi_gerekli, oku
from kelime_siklik import siklik_dosya_adi, yil_araligi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--yillar", default="2018-2025",
                   help="hedef yillar (ilk yil icin T-3 verisi gerekir; 2026 eksik yil, varsayilan disinda)")
    p.add_argument("--saglamlik", type=int, default=30)
    p.add_argument("--siklik", help="baska sayim dosyasi, orn. siklik_tr_govde.tsv.gz / siklik_tr_ekzinciri.tsv.gz")
    arg = p.parse_args()

    siklik_dosyasi = Path(arg.siklik) if arg.siklik else KLASOR / siklik_dosya_adi(arg.dil, arg.n)
    if not siklik_dosyasi.is_absolute() and not siklik_dosyasi.exists():
        siklik_dosyasi = KLASOR / siklik_dosyasi
    belge, sayi = oku(siklik_dosyasi)
    harf = harf_filtresi_gerekli(siklik_dosyasi)
    print(f"Sayim dosyasi: {siklik_dosyasi.name}")
    hedefler = [T for T in yil_araligi(arg.yillar) if all(belge.get(y) for y in (T - 3, T - 2, T - 1, T))]

    tum = defaultdict(lambda: {"yillar": [], "delta": 0.0, "oran": 0.0, "sayi": 0})
    print(f"{arg.dil.upper()} | her hedef yil T icin taban T-2 (Kobak vd.)\n")
    print(f"{'yil':>5} {'ozet':>7} {'hesaba giren':>13} {'asiri':>7} {'>=' + str(arg.saglamlik) + ' ozet':>10} "
          f"{'delta>0.01':>11}")
    for T in hedefler:
        satirlar = asiri_hesapla(belge, sayi, T - 2, T, harf_filtresi=harf)
        asiri = [r for r in satirlar if r["asiri"]]
        for r in asiri:
            k = tum[r["kelime"]]
            k["yillar"].append(T)
            k["delta"], k["oran"] = max(k["delta"], r["delta"]), max(k["oran"], r["oran"])
            k["sayi"] = max(k["sayi"], r["sayi"])
        print(f"{T:>5} {belge[T]:>7} {len(satirlar):>13} {len(asiri):>7} "
              f"{sum(r['sayi'] >= arg.saglamlik for r in asiri):>10} {sum(r['delta'] > 0.01 for r in asiri):>11}")

    ad = siklik_dosyasi.name.replace("siklik_", "").replace(".tsv.gz", "")  # tr, tr_govde, tr_ekzinciri
    cikti = KLASOR / f"asiri_kelimeler_{ad}.tsv"
    with open(cikti, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["kelime", "yillar", "en_buyuk_delta", "en_buyuk_oran", "en_yuksek_ozet_sayisi"])
        for kelime, k in sorted(tum.items(), key=lambda x: -x[1]["delta"]):
            w.writerow([kelime, ",".join(map(str, k["yillar"])), f"{k['delta']:.6f}", f"{k['oran']:.3f}", k["sayi"]])
    print(f"\nHerhangi bir yilda asiri cikan {len(tum)} farkli kelime -> {cikti}")


if __name__ == "__main__":
    main()
