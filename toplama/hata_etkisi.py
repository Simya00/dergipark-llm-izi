#!/usr/bin/env python3
"""
Iki Bilinen Hatanin Etkisini Sayma (2026-11-22; dis degerlendirmede bulundu)
==========================================================================
Yalnizca SAYAR; hicbir dosyayi degistirmez. Sonuca gore kullanici karar verir:
duzeltme (veri dondurmasi acilir) ya da sinirlilik olarak raporlama.

1) baslik : oai_ayristir.py BASLIK kurali, tamami buyuk harfli "ÖZ..." kelimesiyle
            baslayan ozetlerde kelimenin basini siliyor ("ÖZEL egitim" -> "EL egitim").
            Ham sayfalardan (toplama/ham) her description alani temiz() sonrasinda
            kontrol edilir. Sinif:
              hata_suphesi : ilk kelime tamami buyuk harf ve ÖZ/ÖZET/ABSTRACT degil
                             (ÖZEL, ÖZGÜN, ÖZETLE...) -> kural kelimeyi bozdu
              bitisik      : karisik harfli bitisik baslik (ÖzetÇalışmanın) -> dogru silme
              normal       : "ÖZET:", "Abstract " gibi -> dogru silme
2) harf   : kelime_siklik.py tr_kelime_kucult: tamami buyuk harfli, ÇĞİÖŞÜ icermeyen
            kelimeler Ingilizce gibi kucultuluyor ("AMACI" -> "amaci"; dogrusu "amacı").
            Yalnizca icinde "I" olanlar etkilenir (I -> i yerine ı olmaliydi).
            makaleler.jsonl'deki Turkce ozetlerde (analize girenler) yillara gore sayilir.

Kullanim (toplama/ klasorunde):
  python3 hata_etkisi.py baslik
  python3 hata_etkisi.py harf
"""

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

from oai_ayristir import BASLIK, DC, NS, temiz, xml_coz

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR.parent / "analiz"))

ILK_KELIME = re.compile(r"\w+", re.UNICODE)
BASLIK_KELIMELERI = {"ÖZET", "ÖZ", "ABSTRACT"}


def baslik(arg):
    dosyalar = sorted(Path(arg.ham).rglob("sayfa_*.xml.gz"))
    if not dosyalar:
        raise SystemExit(f"{arg.ham} altinda sayfa_*.xml.gz bulunamadi.")
    sinif, ilk = Counter(), Counter()
    ornekler = []
    for i, dosya in enumerate(dosyalar, 1):
        with gzip.open(dosya, "rb") as f:
            kok, _, _ = xml_coz(f.read())
        for e in kok.iter(DC + "description"):
            t = temiz(e.text)
            if not t or not BASLIK.match(t):
                continue
            kelime = ILK_KELIME.match(t.lstrip()).group(0)
            if kelime.isupper() and kelime not in BASLIK_KELIMELERI:
                sinif["hata_suphesi"] += 1
                ilk[kelime] += 1
                if len(ornekler) < arg.ornek:
                    ornekler.append((t[:80], BASLIK.sub("", t)[:80]))
            elif not kelime.isupper() and kelime not in {"Özet", "Öz", "Abstract"}:
                sinif["bitisik"] += 1
            else:
                sinif["normal"] += 1
        if i % 500 == 0:
            print(f"  {i}/{len(dosyalar)} sayfa...", end="\r", file=sys.stderr)
    print(f"Basligi silinen oz alani: {sum(sinif.values())}")
    for k in ("normal", "bitisik", "hata_suphesi"):
        print(f"  {k:<13} {sinif[k]:>8}")
    print("\nHata suphesi: en sik ilk kelimeler")
    for k, n in ilk.most_common(25):
        print(f"  {k:<20} {n:>6}")
    print(f"\nOrnekler (once -> sonra), ilk {len(ornekler)}:")
    for once, sonra in ornekler:
        print(f"  {once!r}\n    -> {sonra!r}")


def harf(arg):
    from kelime_siklik import KELIME, TR_BUYUK, VARSAYILAN_GIRDI, analize_girer, turkce_kucult
    ozet, etkilenen, gecis = Counter(), Counter(), Counter()
    kelimeler = Counter()
    kucuk = Counter()  # metinde zaten kucuk harfle yazilmis kelimeler (hangi kucultmenin dogru oldugunu soyler)
    yil_kelime = []
    with open(VARSAYILAN_GIRDI, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if not y or not analize_girer(m, "ozet_tr", None):
                continue
            ozet[y] += 1
            tum = KELIME.findall(m["ozet_tr"])
            kucuk.update(k for k in tum if k.islower())
            bulunan = [k for k in tum
                       if len(k) > 1 and k.isupper() and "I" in k and not (set(k) & TR_BUYUK)]
            if bulunan:
                yil_kelime.append((y, bulunan))
                kelimeler.update(bulunan)
    # Turkce mi? Kucuk harfli metinde Turkce kucultmesi (amacı) Ingilizce kucultmesinden (amaci)
    # daha sik geciyorsa kelime Turkce sayilir: COVID -> covid (Ingilizce, dogru), AMACI -> amacı (Turkce, hatali)
    turkce = {k for k in kelimeler if kucuk[turkce_kucult(k)] > kucuk[k.lower()]}
    for y, bulunan in yil_kelime:
        tr = [k for k in bulunan if k in turkce]
        if tr:
            etkilenen[y] += 1
            gecis[y] += len(tr)
    print("YALNIZCA TURKCE KELIMELER (hatali kucultulen; Ingilizce kisaltmalar haric):")
    print(f"{'yil':>5} {'ozet':>7} {'etkilenen':>10} {'%':>6} {'kelime gecisi':>14}")
    for y in sorted(ozet):
        if 2015 <= y <= 2026:
            print(f"{y:>5} {ozet[y]:>7} {etkilenen[y]:>10} {100 * etkilenen[y] / ozet[y]:>5.1f}% {gecis[y]:>14}")
    print(f"\nTurkce sayilan {len(turkce)} farkli kelime, en sik {arg.ornek}"
          " (kucuk harfli metindeki TR / EN kucultme sayisiyla):")
    for k, n in Counter({k: kelimeler[k] for k in turkce}).most_common(arg.ornek):
        print(f"  {k:<20} {n:>7}   {turkce_kucult(k)}: {kucuk[turkce_kucult(k)]}  {k.lower()}: {kucuk[k.lower()]}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    b = alt.add_parser("baslik")
    b.add_argument("--ham", default=str(KLASOR / "ham"))
    b.add_argument("--ornek", type=int, default=20)
    h = alt.add_parser("harf")
    h.add_argument("--ornek", type=int, default=40)
    arg = p.parse_args()
    baslik(arg) if arg.komut == "baslik" else harf(arg)


if __name__ == "__main__":
    main()
