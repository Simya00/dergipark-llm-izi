#!/usr/bin/env python3
"""
Oz Dili Kontrolu
================
makaleler.jsonl'deki ozlerde iki sorunu SAYAR ve ornek gosterir (hicbir seyi
degistirmez):

  1. Yanlis etiket: "tr" etiketli alanda tamamen Ingilizce metin (veya tersi).
  2. Iki dilli alan: ayni alanda hem Turkce oz hem Ingilizce abstract.

Yontem (oai_ayristir.metin_dili): Metin cumlelere bolunur, her cumlenin dili
islev kelimeleri (ve, bir, bu / the, and, of ...) ve Turkceye ozgu harflerle
(ğ, ı, ş, İ) belirlenir.
  - cumlelerin (kelime agirlikli) >= %80'i diger dildeyse -> yanlis etiket
  - her iki dilde de >= 2 cumle ve azinlik dil >= %20 ise -> iki dilli
  - aksi halde etiketle uyumlu (veya belirsiz)

oai_ayristir.py bu sorunlari artik ayristirirken temizliyor (dil_kaynagi:
etiket_duzeltildi / iki_dilli_bolundu / bozuk_metin). Yeni ayristirilmis
dosyada bu betik (1) kac ozun temizlendigini ve (2) temizlikten sonra KALAN
sorunlari gosterir; eski dosyada temizlik oncesi durumu gosterir.

Ciktilar:
  - ekrana: yillara gore sayilar, sorunlarin en cok gorueldugu dergiler, ornekler
  - dil_sorunlari.tsv: sorunlu her oz icin oai_id, url, yil, dergi, etiket, tespit, metnin basi

Kullanim:
  python3 dil_kontrol.py
  python3 dil_kontrol.py --ornek 10
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from oai_ayristir import metin_dili

KLASOR = Path(__file__).resolve().parent


def son_etiket(oz):
    """Kontrol edilecek etiket: ozun (temizlik sonrasi) dili; bozuk/etiketsiz olanlar atlanir."""
    return oz["dil"] if oz["dil_kaynagi"] != "tahmin" and oz["dil"] in ("tr", "en") else None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--ornek", type=int, default=5, help="Her sorun turu icin gosterilecek ornek sayisi")
    arg = p.parse_args()

    sayac = defaultdict(Counter)        # yil -> (etiket, tespit) -> adet
    dergi_sorun = defaultdict(Counter)  # (etiket, tespit) -> dergi -> adet
    ornekler = defaultdict(list)
    toplam = Counter()
    temizlik = Counter()  # dil_kaynagi -> adet
    with open(arg.girdi, encoding="utf-8") as g, \
            open(KLASOR / "dil_sorunlari.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["oai_id", "url", "yil", "dergi", "etiket", "tespit", "tr_payi", "en_payi", "metin_basi"])
        for satir in g:
            m = json.loads(satir)
            yil = m.get("yil_guvenilir")
            for oz in m["ozler"]:
                temizlik[oz["dil_kaynagi"]] += 1
                etiket = son_etiket(oz)
                if etiket is None:
                    continue
                tespit, _, trp, enp = metin_dili(oz["metin"])
                anahtar = (etiket, tespit)
                sayac[yil][anahtar] += 1
                toplam[anahtar] += 1
                if tespit in ("tr", "en") and tespit == etiket or tespit == "belirsiz":
                    continue
                dergi_sorun[anahtar][m["dergi_kodu"]] += 1
                if len(ornekler[anahtar]) < arg.ornek:
                    ornekler[anahtar].append((m.get("url"), yil, oz["metin"]))
                w.writerow([m["oai_id"], m.get("url"), yil, m["dergi_kodu"], etiket, tespit,
                            f"{trp:.2f}", f"{enp:.2f}", oz["metin"][:150]])

    sorunlar = [("tr", "en"), ("tr", "iki_dilli"), ("en", "tr"), ("en", "iki_dilli")]
    adlar = {("tr", "en"): "TR etiket, metin EN", ("tr", "iki_dilli"): "TR etiket, iki dilli",
             ("en", "tr"): "EN etiket, metin TR", ("en", "iki_dilli"): "EN etiket, iki dilli"}
    print("Ayristirmada yapilan temizlik (dil_kaynagi):")
    for k, v in temizlik.most_common():
        print(f"   {k:>18}: {v}")
    print("\nTemizlik SONRASI kontrol:")
    for etiket in ("tr", "en"):
        n = sum(v for (e, _), v in toplam.items() if e == etiket)
        print(f"'{etiket}' etiketli oz: {n}")
        for t in ("tr", "en", "iki_dilli", "belirsiz"):
            print(f"   metin {t:>9}: {toplam[(etiket, t)]:>8} ({100 * toplam[(etiket, t)] / max(n, 1):.2f}%)")
    print()

    print(f"{'yil':>6} " + " ".join(f"{adlar[s]:>22}" for s in sorunlar))
    for y in sorted(sayac, key=lambda y: (y is None, y)):
        if y is not None and y < 2015:
            continue
        print(f"{str(y):>6} " + " ".join(f"{sayac[y][s]:>22}" for s in sorunlar))

    for s in sorunlar:
        if not toplam[s]:
            continue
        print(f"\n=== {adlar[s]}: {toplam[s]} oz ===")
        print("En cok gorulen dergiler: " + ", ".join(f"{d} ({a})" for d, a in dergi_sorun[s].most_common(8)))
        for url, yil, metin in ornekler[s]:
            print(f"  - {yil} {url}\n    {metin[:300]}{'...' if len(metin) > 300 else ''}")
    print(f"\nTum sorunlu ozler: {KLASOR / 'dil_sorunlari.tsv'}")


if __name__ == "__main__":
    main()
