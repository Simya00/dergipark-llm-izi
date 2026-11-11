#!/usr/bin/env python3
"""
Yillara Gore Ozet Uzunlugu
==========================
Iki soruya cevap verir (2026-11-11):
  1. Ozetler yillar icinde uzadi mi? Uzama, her kelimenin bir ozette "gecme"
     olasiligini artirir; asiri kelime analizinde sik kelimeleri (icin, calisma)
     yapay olarak yukari iter.
  2. Kobak vd. uzunluk filtresi (250 < karakter < 4000) her yil kac ozeti
     disarida birakiyor? (filtre kelime_siklik.py, alt_sinir.py vb.'de uygulanir)

Uzunluk olculeri FILTREDEN SONRAKI ozetler uzerinden: karakter ve kelime sayisi
(kelime = analizdeki kelime kurali, birlesik onarimi dahil).

Kullanim:
  python3 ozet_uzunluk.py --dil tr
  python3 ozet_uzunluk.py --dil en --yillar 2015-2026
"""

import argparse
import json
import statistics
from collections import defaultdict

from kelime_siklik import (OZET_EN_KISA, OZET_EN_UZUN, VARSAYILAN_GIRDI, kelime_listesi,
                           uzunluk_uygun, yil_araligi)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--yillar", default="2015-2026")
    arg = p.parse_args()

    yillar = set(yil_araligi(arg.yillar))
    alan = f"ozet_{arg.dil}"
    kisa, uzun = defaultdict(int), defaultdict(int)
    karakter, kelime = defaultdict(list), defaultdict(list)
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            metin = m.get(alan)
            if y not in yillar or not metin:
                continue
            if not uzunluk_uygun(metin):
                if len(metin) <= OZET_EN_KISA:
                    kisa[y] += 1
                else:
                    uzun[y] += 1
                continue
            karakter[y].append(len(metin))
            kelime[y].append(len(kelime_listesi(metin, arg.dil)))

    print(f"{arg.dil.upper()} ozetleri | filtre: {OZET_EN_KISA} < karakter < {OZET_EN_UZUN} (Kobak vd.)\n")
    print(f"{'yil':>5} {'tum':>7} {'kisa':>6} {'uzun':>5} {'atilan%':>8} {'kalan':>7} "
          f"{'ort.kar':>8} {'med.kar':>8} {'ort.kel':>8} {'med.kel':>8}")
    for y in sorted(yillar):
        kalan = len(karakter[y])
        tum = kalan + kisa[y] + uzun[y]
        if not tum:
            continue
        print(f"{y:>5} {tum:>7} {kisa[y]:>6} {uzun[y]:>5} {100 * (kisa[y] + uzun[y]) / tum:>7.1f}% {kalan:>7} "
              f"{statistics.fmean(karakter[y]) if kalan else 0:>8.0f} {statistics.median(karakter[y]) if kalan else 0:>8.0f} "
              f"{statistics.fmean(kelime[y]) if kalan else 0:>8.1f} {statistics.median(kelime[y]) if kalan else 0:>8.0f}")


if __name__ == "__main__":
    main()
