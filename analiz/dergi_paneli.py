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
ilgili dilde ANALIZE GIREN (250-4000 karakter) ozeti olan makalesi bulunan dergiler.

Esik (2026-11-12, kullanici karari): yilda en az 12 makale (TR Dizin'in saglik
bilimleri icin istedigi en az 12 arastirma makalesi; DOAJ'in alt siniri 5).
Iki panel: kisa (2021-2025: ana sonucun kontrolu) ve uzun (2015-2025: yillik
tablonun tamami; 2018 satiri 2015 verisini kullanir).
Ekrana ayrica: yillara gore aktif / yeni katilan dergi sayisi, dergi basina
yillik makale dagilimi (ceyrekler) ve panelin ozetlerin yuzde kacini kapsadigi.

Cikti: dergi_paneli_<dil>.txt (her satirda bir dergi_kodu). Analiz
betiklerine --dergiler ile verilir:
  python3 kelime_siklik.py --dil tr --dergiler dergi_paneli_tr.txt --cikti siklik_tr_panel.tsv.gz

Kullanim:
  python3 dergi_paneli.py --dil tr --yillar 2021-2025 --cikti dergi_paneli_tr_kisa.txt
  python3 dergi_paneli.py --dil tr --yillar 2015-2025 --cikti dergi_paneli_tr_uzun.txt
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import statistics

from kelime_siklik import VARSAYILAN_GIRDI, analize_girer, yil_araligi

KLASOR = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--yillar", default="2021-2025", help="Dergi bu yillarin HER birinde yayin yapmis olmali")
    p.add_argument("--en-az", type=int, default=12, help="Her yilda en az bu kadar makale (varsayilan 12)")
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
            if y is None or not analize_girer(m, alan, None):
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
    # Dergi dunyasinin yillara gore degisimi (panelden bagimsiz)
    ilk_yil = {d: min(y for y, n in s.items() if n) for d, s in sayi.items()}
    print(f"\nYillara gore dergiler (tum veri; 'yeni' = dergide analize giren ilk makale o yil):")
    print(f"{'yil':>6} {'aktif':>6} {'yeni':>5} {'makale/dergi: Q1':>17} {'ortanca':>8} {'Q3':>5} "
          f"{'>=5':>6} {'>=12':>6}")
    for y in range(2015, max(yillar) + 2):
        aktif = [s[y] for s in sayi.values() if s[y]]
        if not aktif:
            continue
        q1, q2, q3 = statistics.quantiles(aktif, n=4) if len(aktif) > 1 else (aktif[0],) * 3
        print(f"{y:>6} {len(aktif):>6} {sum(1 for v in ilk_yil.values() if v == y):>5} {q1:>17.0f} {q2:>8.0f} "
              f"{q3:>5.0f} {sum(n >= 5 for n in aktif):>6} {sum(n >= 12 for n in aktif):>6}")
    print(f"\nPanel: {cikti}")


if __name__ == "__main__":
    main()
