#!/usr/bin/env python3
"""
Ingilizce Karsilastirma: Kobak vd. (2025) PubMed verisinden kelime oranlari
===========================================================================
Kaynak veri: Kobak, Gonzalez-Marquez, Horvat, Lause (2025), Science Advances
11(27): eadt3813, https://doi.org/10.1126/sciadv.adt3813 ; veri dosyasi
https://github.com/berenslab/llm-excess-vocab  results/yearly-counts.csv.gz
(her kelime ve yil icin o kelimeyi iceren PubMed ozeti sayisi; son satir toplam).
Dosya repoya EKLENMEZ; indirip yolunu verin.

Hesap Kobak vd. ile ayni: p = (sayi+1)/(toplam+1); q2024 = p2022 + 2*max(p2022-p2021, 0).
Not: Ingilizce sayim BICIM duzeyinde (highlight / highlights ayri), Turkce
karsilastirma govde duzeyinde; dogrudan esit degil.

Kullanim:
  python3 kobak_karsilastir.py <yearly-counts.csv.gz> highlights crucial ...
"""

import csv
import gzip
import sys

yol = sys.argv[1]
VARSAYILAN = ["highlights","highlight","highlighted","highlighting","underscores","underscore","crucial","critical",
           "foster","fostering","challenges","comprehensive","potential","strategies","strategy","role","play","enhance",
           "enhancing","understanding","delves","delve","pivotal","insights"]
with gzip.open(yol, "rt", encoding="utf-8") as f:
    r = csv.reader(f); bas = next(r); yillar = [int(y) for y in bas[1:]]
    satirlar = {s[0]: [int(x) for x in s[1:]] for s in r}
top = satirlar[""]
i = {y: k for k, y in enumerate(yillar)}
print(f"toplam ozet: 2021 {top[i[2021]]}, 2022 {top[i[2022]]}, 2024 {top[i[2024]]}")
print(f"{'kelime':15} {'p2021%':>7} {'p2022%':>7} {'q2024%':>7} {'p2024%':>7} {'kat':>6} {'fark(puan)':>10}")
for w in (sys.argv[2:] or VARSAYILAN):
    if w not in satirlar: print(w, "yok"); continue
    c = satirlar[w]
    p = {y: (c[i[y]] + 1) / (top[i[y]] + 1) for y in (2021, 2022, 2024)}
    q = p[2022] + 2 * max(p[2022] - p[2021], 0)
    print(f"{w:15} {100*p[2021]:7.2f} {100*p[2022]:7.2f} {100*q:7.2f} {100*p[2024]:7.2f} {p[2024]/q:6.2f} {100*(p[2024]-q):10.2f}")
