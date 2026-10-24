#!/usr/bin/env python3
"""
Kelime Sikliklari (yillara gore)
================================
makaleler.jsonl'deki ozlerden, her kelimenin her yil KAC OZETTE gectigini
sayar (Kobak vd. 2025 gibi: ayni ozette kac kez gectigi degil, gecip
gecmedigi). Analizde makalenin yil_guvenilir alani kullanilir; arsiv/yilsiz
makaleler disarida kalir.

Cikti (--cikti, varsayilan siklik_<dil>.tsv.gz): yil, kelime, belge_sayisi
Ayrica <cikti>.belge.json: her yil kac ozet sayildi (oranin paydasi).

Bellek: tum yillari tek seferde saymak Turkcede milyonlarca farkli kelime
bicimi yuzunden cok bellek ister; bu yuzden dosya her yil icin ayri okunur
ve o yil --min-belge'den az ozette gecen kelimeler atilir.

Kullanim:
  python3 kelime_siklik.py --dil tr
  python3 kelime_siklik.py --dil en --yillar 2018-2026
"""

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
VARSAYILAN_GIRDI = KLASOR.parent / "toplama" / "makaleler.jsonl"

KELIME = re.compile(r"[^\W\d_]+", re.UNICODE)  # sadece harflerden olusan diziler
KESME_EKI = re.compile(r"[’'`]\w+", re.UNICODE)  # "Türkiye'nin" -> "Türkiye"


def turkce_kucult(metin: str) -> str:
    # Python'un .lower() metodu 'İ'yi yanlis donusturuyor
    return metin.replace("İ", "i").replace("I", "ı").lower()


TR_BUYUK = set("ÇĞİÖŞÜ")


def tr_kelime_kucult(kelime: str) -> str:
    # Tamami buyuk harfli ve Turkceye ozgu harf icermeyen kelimeler genelde
    # Ingilizce kisaltma: "COVID" -> "covid" (Turkce kurala gore "covıd" olurdu)
    if kelime.isupper() and not (set(kelime) & TR_BUYUK):
        return kelime.lower()
    return turkce_kucult(kelime)


def kelimeler(metin: str, dil: str) -> set:
    if dil == "tr":
        bulunan = (tr_kelime_kucult(k) for k in KELIME.findall(KESME_EKI.sub("", metin)))
    else:
        bulunan = KELIME.findall(metin.lower())
    return {k for k in bulunan if len(k) >= 2}


def yil_araligi(metin: str):
    bas, son = metin.split("-")
    return list(range(int(bas), int(son) + 1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--yillar", default="2015-2026", help="orn. 2015-2026")
    p.add_argument("--min-belge", type=int, default=5, help="Bir yilda bundan az ozette gecen kelime atilir")
    p.add_argument("--cikti")
    arg = p.parse_args()

    cikti = Path(arg.cikti or KLASOR / f"siklik_{arg.dil}.tsv.gz")
    alan = f"ozet_{arg.dil}"
    belge_sayisi = {}

    with gzip.open(cikti, "wt", encoding="utf-8") as f:
        f.write("yil\tkelime\tbelge_sayisi\n")
        for yil in yil_araligi(arg.yillar):
            sayac, n = Counter(), 0
            with open(arg.girdi, encoding="utf-8") as g:
                for satir in g:
                    m = json.loads(satir)
                    if m.get("yil_guvenilir") != yil or not m.get(alan):
                        continue
                    n += 1
                    sayac.update(kelimeler(m[alan], arg.dil))
            belge_sayisi[yil] = n
            tutulan = 0
            for kelime, adet in sayac.items():
                if adet >= arg.min_belge:
                    f.write(f"{yil}\t{kelime}\t{adet}\n")
                    tutulan += 1
            print(f"{yil}: {n} ozet, {len(sayac)} farkli kelime, {tutulan} tutuldu")

    Path(str(cikti) + ".belge.json").write_text(json.dumps(belge_sayisi, indent=1))
    print(f"Cikti: {cikti}")


if __name__ == "__main__":
    main()
