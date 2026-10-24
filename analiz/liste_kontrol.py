#!/usr/bin/env python3
"""
Hazir Liste Kontrolu
====================
Onceden (veriye bakmadan) hazirlanmis bir kelime / kelime grubu listesindeki
her oge icin yillara gore gectigi ozet oranini (p), hedef yildaki
karsi-olgusal orani (q), farki ve kati hesaplar. asiri_kullanim.py veriden
KESIF yapar; bu betik bizim tahmin ettigimiz ifadeleri TEST eder.

Liste dosyasi: her satirda bir kelime veya kelime grubu; # ile baslayan
satirlar yorum. Ornek: aday_liste_tr.txt, aday_liste_en.txt

Kullanim:
  python3 liste_kontrol.py --dil tr --liste aday_liste_tr.txt --hedef 2024
  python3 liste_kontrol.py --dil en --liste aday_liste_en.txt --hedef 2024
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from asiri_kullanim import karsi_olgusal
from kelime_siklik import VARSAYILAN_GIRDI, gruplar, yil_araligi

KLASOR = Path(__file__).resolve().parent


def liste_oku(dosya):
    return [" ".join(s.split()) for s in Path(dosya).read_text(encoding="utf-8").splitlines()
            if s.strip() and not s.lstrip().startswith("#")]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--liste", required=True)
    p.add_argument("--yillar", default="2015-2026")
    p.add_argument("--taban", type=int, default=2022)
    p.add_argument("--hedef", type=int, default=2024)
    arg = p.parse_args()

    liste = list(dict.fromkeys(liste_oku(arg.liste)))  # tekrarlari at, sirayi koru
    aranan = set(liste)
    uzunluklar = {len(o.split()) for o in liste}
    yillar = yil_araligi(arg.yillar)
    alan = f"ozet_{arg.dil}"
    n = Counter()
    sayi = {y: Counter() for y in yillar}
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in sayi or not m.get(alan):
                continue
            n[y] += 1
            ogeler = set().union(*(gruplar(m[alan], arg.dil, u) for u in uzunluklar))
            sayi[y].update(ogeler & aranan)

    b, T = arg.taban, arg.hedef
    for y in (b - 1, b, T):
        if not n[y]:
            raise SystemExit(f"{y} yilinda hic ozet yok.")
    satirlar = []
    for oge in liste:
        oran = {y: sayi[y][oge] / n[y] for y in yillar if n[y]}
        q = karsi_olgusal(oran[b - 1], oran[b], T - b)
        satirlar.append({"oge": oge, "q": q, "delta": oran[T] - q,
                         "oran": oran[T] / max(q, 1 / n[b]), **{f"p{y}": v for y, v in oran.items()}})
    satirlar.sort(key=lambda r: -r["delta"])

    cikti = KLASOR / f"liste_{Path(arg.liste).stem}_{T}.tsv"
    with open(cikti, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]), delimiter="\t")
        w.writeheader()
        for r in satirlar:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    gosterilen = [y for y in yillar if n[y] and y >= b - 3]
    print(f"{arg.dil.upper()} | {len(liste)} oge | taban {b - 1}-{b} -> hedef {T} | ozet sayisi: "
          + ", ".join(f"{y}:{n[y]}" for y in yillar if n[y]))
    print("\nOzetlerin yuzde kacinda geciyor (%), q ve fark hedef yil icin:")
    print(f"{'oge':>36} " + " ".join(f"{y:>6}" for y in gosterilen) + f" {'q':>6} {'fark':>7} {'kat':>5}")
    for r in satirlar:
        print(f"{r['oge']:>36} " + " ".join(f"{100 * r[f'p{y}']:>6.2f}" for y in gosterilen)
              + f" {100 * r['q']:>6.2f} {100 * r['delta']:>+7.2f} {r['oran']:>5.1f}")
    print(f"\nTablo: {cikti}")


if __name__ == "__main__":
    main()
