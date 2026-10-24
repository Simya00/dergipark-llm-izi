#!/usr/bin/env python3
"""
LLM ile Islenmis Ozet Oranina Alt Sinir
=======================================
Secilen isaretci kelimelerden EN AZ BIRINI iceren ozetlerin orani (p) her yil
icin hesaplanir; asiri_kullanim.py'deki ayni dogrusal egilimle karsi-olgusal
oran (q) tahmin edilir. Hedef yilda ozetlerin L kadari LLM ile islendiyse ve
LLM'li bir ozet isaretcilerden en az birini en fazla 1 olasilikla iceriyorsa:

    p = L + (1 - L) q   ->   L >= (p - q) / (1 - q)

Isaretci icermeyen LLM'li ozetler sayilmadigi ve yazarlarin bu kelimeleri
silmis olabilecegi icin bu bir ALT sinirdir.

Isaretci dosyasi: her satirda bir kelime (# ile baslayan satirlar yorum).

Kullanim:
  python3 alt_sinir.py --dil tr --isaretciler isaretciler_tr.txt
"""

import argparse
import json
from pathlib import Path

from asiri_kullanim import karsi_olgusal
from kelime_siklik import VARSAYILAN_GIRDI, kelimeler, yil_araligi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--isaretciler", required=True)
    p.add_argument("--yillar", default="2015-2026")
    p.add_argument("--taban", type=int, default=2022)
    arg = p.parse_args()

    isaretciler = {s.strip() for s in Path(arg.isaretciler).read_text(encoding="utf-8").splitlines()
                   if s.strip() and not s.startswith("#")}
    yillar = yil_araligi(arg.yillar)
    alan = f"ozet_{arg.dil}"
    n = dict.fromkeys(yillar, 0)
    isaretli = dict.fromkeys(yillar, 0)
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in n or not m.get(alan):
                continue
            n[y] += 1
            isaretli[y] += bool(kelimeler(m[alan], arg.dil) & isaretciler)

    oran = {y: isaretli[y] / n[y] for y in yillar if n[y]}
    b = arg.taban
    print(f"{len(isaretciler)} isaretci, dil={arg.dil}, taban {b - 1}-{b}\n")
    print(f"{'yil':>6} {'ozet':>8} {'isaretli':>9} {'p':>8} {'q':>8} {'alt sinir':>10}")
    for y in yillar:
        if not n[y]:
            continue
        satir = f"{y:>6} {n[y]:>8} {isaretli[y]:>9} {oran[y]:>8.4f}"
        if y > b and b in oran and b - 1 in oran:
            q = karsi_olgusal(oran[b - 1], oran[b], y - b)
            satir += f" {q:>8.4f} {(oran[y] - q) / (1 - q):>9.1%}"
        print(satir)


if __name__ == "__main__":
    main()
