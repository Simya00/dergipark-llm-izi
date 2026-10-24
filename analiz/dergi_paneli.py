#!/usr/bin/env python3
"""
Sabit Dergi Paneli
==================
Taban yillarinda da hedef yillarda da duzenli yayin yapan dergileri secer.
Neden: Bazi dergiler DergiPark'a gec gecmis (orn. gazimmfd'nin ilk guvenilir
yili 2023). Bu dergiler 2021-2022 tabaninda yok, 2024'te var; dergi karisimi
degistigi icin (orn. yeni katilan muhendislik dergileri) bazi kelimeler LLM
olmadan da "artmis" gorunebilir. Panelle sinirlanan analiz bu etkiyi ayiklar.

Secim: --yillar araligindaki HER yilda en az --en-az tane guvenilir yilli,
ilgili dilde ozeti olan makalesi bulunan dergiler.

Cikti: dergi_paneli_<dil>.txt (her satirda bir dergi_kodu). Analiz
betiklerine --dergiler ile verilir:
  python3 kelime_siklik.py --dil tr --dergiler dergi_paneli_tr.txt --cikti siklik_tr_panel.tsv.gz

Kullanim:
  python3 dergi_paneli.py --dil tr
  python3 dergi_paneli.py --dil tr --yillar 2020-2025 --en-az 10
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from kelime_siklik import VARSAYILAN_GIRDI, yil_araligi

KLASOR = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--yillar", default="2021-2025", help="Dergi bu yillarin HER birinde yayin yapmis olmali")
    p.add_argument("--en-az", type=int, default=5, help="Her yilda en az bu kadar makale")
    p.add_argument("--cikti")
    arg = p.parse_args()

    yillar = yil_araligi(arg.yillar)
    alan = f"ozet_{arg.dil}"
    sayi = defaultdict(Counter)  # dergi -> yil -> makale
    tum = Counter()              # yil -> makale (tum dergiler)
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y is None or not m.get(alan):
                continue
            sayi[m["dergi_kodu"]][y] += 1
            tum[y] += 1

    panel = sorted(d for d, s in sayi.items() if all(s[y] >= arg.en_az for y in yillar))
    cikti = Path(arg.cikti or KLASOR / f"dergi_paneli_{arg.dil}.txt")
    cikti.write_text("".join(d + "\n" for d in panel), encoding="utf-8")

    print(f"{len(sayi)} dergiden {len(panel)} tanesi panelde "
          f"({arg.yillar} her yil >= {arg.en_az} makale, dil={arg.dil})\n")
    print(f"{'yil':>6} {'tum':>8} {'panel':>8} {'oran':>6}")
    for y in range(min(yillar) - 3, max(yillar) + 2):
        if tum[y]:
            p_say = sum(sayi[d][y] for d in panel)
            print(f"{y:>6} {tum[y]:>8} {p_say:>8} {p_say / tum[y]:>6.0%}")
    print(f"\nPanel: {cikti}")


if __name__ == "__main__":
    main()
