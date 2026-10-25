#!/usr/bin/env python3
"""
Dil Temizliginin Elle Dogrulanmasi
==================================
oai_ayristir.py'nin dil temizligi kararlarini (etiket duzeltme, iki dilli
bolme, bozuk metin, diger dil) kullanicinin elle kontrol etmesi icin.

  ornekle: Her kategoriden rastgele --adet oz secip dil_dogrulama.tsv'ye yazar.
           "dogru_mu" sutununu E (dogru) / H (yanlis) diye doldurun; istersen
           "not" sutununa aciklama yazin. (LibreOffice/Excel'de acilir.)
  hesapla: Doldurulmus dosyadan kategori basina dogruluk oranini ve %95 guven
           araligini (Wilson) hesaplar.

Kategoriler:
  etiket_duzeltildi  metnin dili etiketin tersiydi, etiket degisti
  iki_dilli_bolundu  ayni alanda TR + EN vardi, ikiye bolundu (tr_parca / en_parca)
  bozuk_metin        bozuk kodlama diye atildi
  diger_dil          baska dil (Almanca vb.) diye ayrildi
  dokunulmadi        TR etiketli, kod bir sey yapmadi (kacirilan sorun var mi?)

Kullanim:
  python3 dil_dogrulama.py ornekle
  python3 dil_dogrulama.py hesapla
"""

import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
DOSYA = KLASOR / "dil_dogrulama.tsv"
KATEGORILER = ["etiket_duzeltildi", "iki_dilli_bolundu", "bozuk_metin", "diger_dil", "dokunulmadi"]
SUTUNLAR = ["no", "kategori", "url", "etiket", "karar", "metin", "tr_parca", "en_parca", "dogru_mu", "not"]


def adaylari_topla(girdi):
    """Kategori -> aday listesi. Bolunen ozlerin iki parcasi tek aday olarak birlestirilir."""
    adaylar = defaultdict(list)
    with open(girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            bolunen = {}
            for oz in m["ozler"]:
                k = oz["dil_kaynagi"]
                if k == "iki_dilli_bolundu":
                    bolunen.setdefault(oz.get("etiket"), {})[oz["dil"]] = oz["metin"]
                elif k in ("etiket_duzeltildi", "bozuk_metin", "diger_dil"):
                    adaylar[k].append({"url": m.get("url"), "etiket": oz.get("etiket"),
                                       "karar": oz["dil"], "metin": oz["metin"]})
                elif k == "etiket" and oz["dil"] == "tr":
                    adaylar["dokunulmadi"].append({"url": m.get("url"), "etiket": "tr",
                                                   "karar": "tr (dokunulmadi)", "metin": oz["metin"]})
            for etiket, parcalar in bolunen.items():
                adaylar["iki_dilli_bolundu"].append({
                    "url": m.get("url"), "etiket": etiket, "karar": "bolundu",
                    "tr_parca": parcalar.get("tr", ""), "en_parca": parcalar.get("en", "")})
    return adaylar


def komut_ornekle(arg):
    if DOSYA.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{DOSYA.name} zaten var (doldurdugunuz isaretler olabilir). "
                         f"Yeniden olusturmak icin --uzerine-yaz ekleyin.")
    adaylar = adaylari_topla(arg.girdi)
    rng = random.Random(arg.tohum)
    satirlar = []
    for kat in KATEGORILER:
        liste = adaylar.get(kat, [])
        secilen = rng.sample(liste, min(arg.adet, len(liste)))
        print(f"  {kat:>18}: {len(liste):>7} aday, {len(secilen)} secildi")
        for a in secilen:
            satirlar.append({"kategori": kat, **a})
    rng.shuffle(satirlar)  # kategoriler karisik sirada: bir kategoriye alisip dikkat dagilmasin
    with open(DOSYA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUTUNLAR, delimiter="\t")
        w.writeheader()
        for i, s in enumerate(satirlar, 1):
            w.writerow({"no": i, "dogru_mu": "", "not": "", **{k: s.get(k, "") for k in SUTUNLAR if k in s}})
    print(f"\n{len(satirlar)} satir -> {DOSYA}\n'dogru_mu' sutununu E / H diye doldurun.")


def wilson(dogru, n, z=1.96):
    """Oran icin %95 guven araligi (Wilson). Kucuk orneklerde ve %100'e yakin oranlarda guvenilir."""
    if n == 0:
        return 0.0, 0.0
    p = dogru / n
    merkez = (p + z * z / (2 * n)) / (1 + z * z / n)
    yari = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, merkez - yari), min(1.0, merkez + yari)


def komut_hesapla(arg):
    sayac = defaultdict(lambda: {"E": 0, "H": 0, "bos": 0})
    with open(DOSYA, encoding="utf-8") as f:
        for s in csv.DictReader(f, delimiter="\t"):
            cevap = s["dogru_mu"].strip().upper()[:1]
            sayac[s["kategori"]][cevap if cevap in ("E", "H") else "bos"] += 1
    print(f"{'kategori':>18} {'E':>4} {'H':>4} {'bos':>4} {'dogruluk':>9} {'%95 aralik':>14}")
    for kat in KATEGORILER:
        c = sayac[kat]
        n = c["E"] + c["H"]
        if not n:
            print(f"{kat:>18} {'-':>4} {'-':>4} {c['bos']:>4}")
            continue
        alt, ust = wilson(c["E"], n)
        print(f"{kat:>18} {c['E']:>4} {c['H']:>4} {c['bos']:>4} {100 * c['E'] / n:>8.1f}% "
              f"{100 * alt:>6.1f}–{100 * ust:.1f}%")
    print("\nNot: 'dokunulmadi' satirinda H = kodun KACIRDIGI bir sorun (yanlis etiket ya da iki dilli).")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["ornekle", "hesapla"])
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--adet", type=int, default=50, help="Kategori basina ornek sayisi")
    p.add_argument("--tohum", type=int, default=20261025)
    p.add_argument("--uzerine-yaz", action="store_true")
    arg = p.parse_args()
    {"ornekle": komut_ornekle, "hesapla": komut_hesapla}[arg.komut](arg)


if __name__ == "__main__":
    main()
