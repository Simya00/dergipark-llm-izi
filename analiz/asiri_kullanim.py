#!/usr/bin/env python3
"""
Asiri Kelime Kullanimi (Kobak vd. 2025 yontemi)
===============================================
kelime_siklik.py ciktisindan her kelime icin, LLM'ler olmasaydi hedef yilda
beklenecek sikligi (karsi-olgusal q) tahmin eder ve gerceklesen siklikla (p)
karsilastirir.

  p_y  = kelimenin y yilinda gectigi ozet orani
  q_T  = p_b + (T - b) * max(p_b - p_{b-1}, 0)      (b = --taban, varsayilan 2022)
         -> taban yilina kadarki dogrusal egilim; azalan egilim sifir alinir
            (azalan kelimelerde q'yu dusuk tahmin edip asiri kullanimi
            sisirmemek icin, Kobak vd. ile ayni)
  delta = p_T - q_T   (fark: kac yuzde puan fazla)
  oran  = p_T / q_T   (kat: kac kat fazla)

Cikti: asiri_<dil>_<hedef>.tsv (tum kelimeler, delta'ya gore sirali) ve ekrana
delta'ya ve orana gore en ustteki kelimeler. Bu liste ADAY listedir: icerik
kelimeleri (orn. "covid", "deprem") elle ayiklanip ust uslup kelimeleri
isaretci olarak secilecek (bkz. alt_sinir.py).

Kullanim:
  python3 asiri_kullanim.py --dil tr --hedef 2024
  python3 asiri_kullanim.py --dil en --hedef 2025 --en-az-belge 50
"""

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

KLASOR = Path(__file__).resolve().parent


def karsi_olgusal(p_onceki, p_taban, adim):
    return p_taban + adim * max(p_taban - p_onceki, 0.0)


def oku(siklik_dosyasi):
    belge = {int(y): n for y, n in json.loads(Path(str(siklik_dosyasi) + ".belge.json").read_text()).items()}
    sayi = defaultdict(dict)  # kelime -> {yil: belge_sayisi}
    with gzip.open(siklik_dosyasi, "rt", encoding="utf-8") as f:
        for satir in csv.DictReader(f, delimiter="\t"):
            sayi[satir["kelime"]][int(satir["yil"])] = int(satir["belge_sayisi"])
    return belge, sayi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--siklik", help="kelime_siklik.py ciktisi (varsayilan siklik_<dil>.tsv.gz)")
    p.add_argument("--taban", type=int, default=2022, help="Egilimin son yili (b); b-1 ve b kullanilir")
    p.add_argument("--hedef", type=int, default=2024)
    p.add_argument("--en-az-belge", type=int, default=30, help="Hedef yilda en az bu kadar ozette gecmeli")
    p.add_argument("--goster", type=int, default=40)
    arg = p.parse_args()

    belge, sayi = oku(arg.siklik or KLASOR / f"siklik_{arg.dil}.tsv.gz")
    b, T = arg.taban, arg.hedef
    for y in (b - 1, b, T):
        if not belge.get(y):
            raise SystemExit(f"{y} yilinda hic ozet yok; --yillar araligini kontrol edin.")
    yillar = sorted(belge)

    satirlar = []
    for kelime, s in sayi.items():
        if s.get(T, 0) < arg.en_az_belge:
            continue
        oranlar = {y: s.get(y, 0) / belge[y] for y in yillar if belge[y]}
        q = karsi_olgusal(oranlar.get(b - 1, 0.0), oranlar.get(b, 0.0), T - b)
        pT = oranlar[T]
        # Taban yillarinda hic gorulmeyen (--min-belge altinda kalan) kelimelerde
        # q=0 olur; oran sonsuza gitmesin diye q'yu 1 ozetlik orana sabitle.
        q_alt = max(q, 1 / belge[b])
        satirlar.append({
            "kelime": kelime, "p": pT, "q": q, "delta": pT - q, "oran": pT / q_alt,
            **{f"p{y}": oranlar.get(y, 0.0) for y in yillar},
        })

    satirlar.sort(key=lambda r: -r["delta"])
    cikti = KLASOR / f"asiri_{arg.dil}_{T}.tsv"
    with open(cikti, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]) if satirlar else ["kelime"], delimiter="\t")
        w.writeheader()
        for r in satirlar:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    def tablo(baslik, liste):
        print(f"\n{baslik}")
        print(f"{'kelime':>22} {'p' + str(b - 1):>8} {'p' + str(b):>8} {'q':>8} {'p' + str(T):>8} {'delta':>8} {'oran':>6}")
        for r in liste[:arg.goster]:
            print(f"{r['kelime']:>22} {r[f'p{b - 1}']:>8.4f} {r[f'p{b}']:>8.4f} {r['q']:>8.4f} "
                  f"{r['p']:>8.4f} {r['delta']:>+8.4f} {r['oran']:>6.2f}")

    print(f"{arg.dil.upper()} | taban {b - 1}-{b} -> hedef {T} | ozet sayisi: "
          + ", ".join(f"{y}:{belge[y]}" for y in yillar))
    print(f"{len(satirlar)} kelime (hedef yilda >= {arg.en_az_belge} ozet)")
    tablo("Farka (delta) gore en cok artanlar:", satirlar)
    tablo("Kata (oran) gore en cok artanlar:",
          sorted(satirlar, key=lambda r: (-r["oran"], -r["delta"])))
    print(f"\nTum liste: {cikti}")


if __name__ == "__main__":
    main()
