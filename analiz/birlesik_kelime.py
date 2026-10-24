#!/usr/bin/env python3
"""
Birlesik Kelime Sozlugu ve Raporu
=================================
Bircok ozette satir sonu bosluklari kaybolmus ("rakımlaragöre",
"arızadankaynaklanan"). Bu betik:

  sozluk: Tum ozetlerden her kelime biciminin kac ozette gectigini sayar ve
          sozluk_<dil>.tsv.gz'ye yazar. Bu dosya varsa kelime_siklik.py'deki
          kelime_listesi() birlesik kelimeleri otomatik boler (tum analiz
          betikleri etkilenir).
  rapor:  Her yil ozetlerin yuzde kacinda birlesik kelime oldugunu ve en sik
          onarimlari gosterir. Oran yillar arasinda cok farkliysa onarim
          yapilmadan yapilan analiz sahte "artis/azalis" uretebilir.

Kullanim:
  python3 birlesik_kelime.py sozluk --dil tr
  python3 birlesik_kelime.py rapor --dil tr
"""

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

from kelime_siklik import (NADIR_ESIK, VARSAYILAN_GIRDI, birlesik_mi, kelime_listesi, parca_no,
                           sozluk, sozluk_dosyasi, yil_araligi)


def ozetler(girdi, alan):
    with open(girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            if m.get(alan):
                yield m


def komut_sozluk(arg, alan):
    # Turkcede milyonlarca farkli kelime bicimi var; bellek icin dosya
    # --parca kez okunur, her seferinde kelimelerin bir kismi sayilir.
    cikti = sozluk_dosyasi(arg.dil)
    gecici = Path(str(cikti) + ".gecici")
    toplam = 0
    with gzip.open(gecici, "wt", encoding="utf-8") as f:
        f.write("kelime\tbelge_sayisi\n")
        for k in range(arg.parca):
            sayac, n = Counter(), 0
            for m in ozetler(arg.girdi, alan):
                n += 1
                sayac.update(w for w in set(kelime_listesi(m[alan], arg.dil, onarim=False))
                             if parca_no(w, arg.parca) == k)
            for w, adet in sayac.items():
                if adet >= NADIR_ESIK:
                    f.write(f"{w}\t{adet}\n")
                    toplam += 1
            print(f"  parca {k + 1}/{arg.parca}: {n} ozet, {len(sayac)} farkli kelime")
    gecici.replace(cikti)
    print(f"{toplam} kelime (>= {NADIR_ESIK} ozet) -> {cikti}")


def komut_rapor(arg, alan):
    if not sozluk(arg.dil):
        raise SystemExit(f"Once sozluk olusturun: python3 birlesik_kelime.py sozluk --dil {arg.dil}")
    yillar = set(yil_araligi(arg.yillar))
    n, birlesikli, kelime, onarilan = Counter(), Counter(), Counter(), Counter()
    ornekler = Counter()
    for m in ozetler(arg.girdi, alan):
        y = m.get("yil_guvenilir")
        if y not in yillar:
            continue
        ham = kelime_listesi(m[alan], arg.dil, onarim=False)
        sz = sozluk(arg.dil)
        bu_ozet = 0
        for w in ham:
            if p := birlesik_mi(w, sz):
                bu_ozet += 1
                ornekler[(w, " + ".join(p))] += 1
        n[y] += 1
        kelime[y] += len(ham)
        onarilan[y] += bu_ozet
        birlesikli[y] += bu_ozet > 0

    print(f"Birlesik kelime orani ({arg.dil}):\n")
    print(f"{'yil':>6} {'ozet':>8} {'birlesikli ozet %':>18} {'100 kelimede':>13}")
    for y in sorted(n):
        print(f"{y:>6} {n[y]:>8} {100 * birlesikli[y] / n[y]:>17.1f}% {100 * onarilan[y] / kelime[y]:>13.2f}")
    print(f"\nEn sik onarimlar:")
    for (w, p), adet in ornekler.most_common(arg.ornek):
        print(f"  {adet:>6}  {w}  ->  {p}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["sozluk", "rapor"])
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--parca", type=int, default=4, help="sozluk: dosya kac kez okunsun (bellek / parca)")
    p.add_argument("--yillar", default="2015-2026")
    p.add_argument("--ornek", type=int, default=40, help="rapor: gosterilecek ornek onarim sayisi")
    arg = p.parse_args()
    alan = f"ozet_{arg.dil}"
    {"sozluk": komut_sozluk, "rapor": komut_rapor}[arg.komut](arg, alan)


if __name__ == "__main__":
    main()
