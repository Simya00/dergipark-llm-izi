#!/usr/bin/env python3
"""
Asiri Kelime Kullanimi (Kobak vd. 2025 yontemi)
===============================================
kelime_siklik.py ciktisindan her kelime icin, LLM'ler olmasaydi hedef yilda
beklenecek sikligi (karsi-olgusal q) tahmin eder ve gerceklesen siklikla (p)
karsilastirir.

  p_y  = kelimenin y yilinda gectigi ozet orani
  q_T  = p_b + (T - b) * max(p_b - p_{b-1}, 0)      (b = --taban, varsayilan 2022)
         -> taban yilina kadarki dogrusal egilim; azalan egilim sifir alinir
            (azalan kelimelerde q'yu dusuk tahmin edip asiri kullanimi
            sisirmemek icin, Kobak vd. ile ayni)
  delta = p_T - q_T   (fark: kac yuzde puan fazla)
  oran  = p_T / q_T   (kat: kac kat fazla)

Kobak vd. ile BIREBIR ayni olan kisimlar (2026-11-11, kullanici karari; kaynak:
berenslab/llm-excess-vocab, preprocess_and_count_utils.py compute_excess):
  - Siklik yumusatilir: p = (sayi + 1) / (ozet sayisi + 1)  (hic gecmeyen kelimede
    oran sonsuza gitmesin diye)
  - Hesaba giren kelime: hedef yilda VE bir onceki yilda p >= 1e-4; yalnizca
    harflerden olusan kelimeler (Kobak: yalnizca alfabe harfleri)
  - ASIRI KELIME: delta > 0.01  VEYA
        log10(oran) > log10(2) - (log10(p) + 4) * log10(2) / 4
    (oran esigi sikliga gore: p=1e-4 -> x2, 1e-3 -> x1.68, 1e-2 -> x1.41)
--en-az-belge: Kobak'ta YOK; istege bagli ek filtre (saglamlik kontrolu icin,
varsayilan 0 = kapali).

Cikti: asiri_<dil>_<hedef>.tsv (tum kelimeler, delta'ya gore sirali) ve ekrana
delta'ya ve orana gore en ustteki kelimeler. Bu liste ADAY listedir: icerik
kelimeleri (orn. "covid", "deprem") elle ayiklanip ust uslup kelimeleri
isaretci olarak secilecek (bkz. alt_sinir.py).

Kullanim:
  python3 asiri_kullanim.py --dil tr --hedef 2024
  python3 asiri_kullanim.py --dil tr --n 3 --hedef 2024     # 3 kelimelik gruplar
  python3 asiri_kullanim.py --dil en --hedef 2025 --en-az-belge 50
"""

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

from kelime_siklik import siklik_dosya_adi

KLASOR = Path(__file__).resolve().parent


def karsi_olgusal(p_onceki, p_taban, adim):
    return p_taban + adim * max(p_taban - p_onceki, 0.0)


KOBAK_EN_AZ_SIKLIK = 1e-4  # hedef yil ve bir onceki yilda


def kobak_asiri_mi(p, delta, oran):
    """Kobak vd. aşırı kelime kuralı: fark 1 puandan büyük YA DA sıklığa bağlı kat eşiği aşılmış."""
    return delta > 0.01 or math.log10(oran) > math.log10(2) - (math.log10(p) + 4) * (math.log10(2) / 4)


def oku(siklik_dosyasi):
    belge = {int(y): n for y, n in json.loads(Path(str(siklik_dosyasi) + ".belge.json").read_text()).items()}
    sayi = defaultdict(dict)  # kelime -> {yil: belge_sayisi}
    with gzip.open(siklik_dosyasi, "rt", encoding="utf-8") as f:
        for satir in csv.DictReader(f, delimiter="\t"):
            sayi[satir["kelime"]][int(satir["yil"])] = int(satir["belge_sayisi"])
    return belge, sayi


def asiri_hesapla(belge, sayi, b, T, en_az_belge=0):
    """Her kelime icin p, q, delta, oran ve Kobak vd. asiri kelime karari (satir listesi)."""
    yillar = sorted(belge)
    satirlar = []
    for kelime, s in sayi.items():
        if not kelime.replace(" ", "").isalpha() or s.get(T, 0) < en_az_belge:
            continue  # yalnizca harflerden olusan ogeler (Kobak: allowedWords)
        # Kobak vd.: yumusatilmis siklik (sayi + 1) / (toplam + 1)
        oranlar = {y: (s.get(y, 0) + 1) / (belge[y] + 1) for y in yillar if belge[y]}
        if oranlar[T] < KOBAK_EN_AZ_SIKLIK or oranlar[T - 1] < KOBAK_EN_AZ_SIKLIK:
            continue
        q = karsi_olgusal(oranlar[b - 1], oranlar[b], T - b)
        pT = oranlar[T]
        delta, oran = pT - q, pT / q
        satirlar.append({
            "kelime": kelime, "p": pT, "q": q, "delta": delta, "oran": oran,
            "asiri": int(kobak_asiri_mi(pT, delta, oran)), "sayi": s.get(T, 0),
            **{f"p{y}": oranlar.get(y, 0.0) for y in yillar},
        })

    return satirlar


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--n", type=int, default=1, help="1: tek kelime, 2-4: kelime gruplari")
    p.add_argument("--siklik", help="kelime_siklik.py ciktisi (varsayilan --dil ve --n'den)")
    p.add_argument("--taban", type=int, default=2022, help="Egilimin son yili (b); b-1 ve b kullanilir")
    p.add_argument("--hedef", type=int, default=2024)
    p.add_argument("--en-az-belge", type=int, default=0,
                   help="Istege bagli ek filtre: hedef yilda en az bu kadar ozet (Kobak'ta yok; 0 = kapali)")
    p.add_argument("--saglamlik", type=int, default=30,
                   help="Saglamlik kontrolu (2026-11-11 kullanici karari: her zaman raporlanir): "
                        "asiri kelimelerden hedef yilda en az bu kadar ozette gecenler ayrica sayilir")
    p.add_argument("--goster", type=int, default=40)
    arg = p.parse_args()

    belge, sayi = oku(arg.siklik or KLASOR / siklik_dosya_adi(arg.dil, arg.n))
    b, T = arg.taban, arg.hedef
    for y in (b - 1, b, T):
        if not belge.get(y):
            raise SystemExit(f"{y} yilinda hic ozet yok; --yillar araligini kontrol edin.")
    yillar = sorted(belge)

    satirlar = asiri_hesapla(belge, sayi, b, T, arg.en_az_belge)

    satirlar.sort(key=lambda r: -r["delta"])
    cikti = KLASOR / (f"asiri_{arg.dil}_{T}.tsv" if arg.n == 1 else f"asiri_{arg.dil}_{arg.n}gram_{T}.tsv")
    with open(cikti, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0]) if satirlar else ["kelime"], delimiter="\t")
        w.writeheader()
        for r in satirlar:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})

    def tablo(baslik, liste):
        print(f"\n{baslik}")
        print(f"{'kelime':>32} {'p' + str(b - 1):>8} {'p' + str(b):>8} {'q':>8} {'p' + str(T):>8} {'delta':>8} {'oran':>6} {'ozet':>6}")
        for r in liste[:arg.goster]:
            print(f"{r['kelime']:>32} {r[f'p{b - 1}']:>8.4f} {r[f'p{b}']:>8.4f} {r['q']:>8.4f} "
                  f"{r['p']:>8.4f} {r['delta']:>+8.4f} {r['oran']:>6.2f} {r['sayi']:>6}"
                  + (" *" if r["sayi"] < arg.saglamlik else ""))

    print(f"{arg.dil.upper()} | taban {b - 1}-{b} -> hedef {T} | ozet sayisi: "
          + ", ".join(f"{y}:{belge[y]}" for y in yillar))
    asirilar = [r for r in satirlar if r["asiri"]]
    print(f"{len(satirlar)} kelime hesaba girdi (p >= 1e-4, {T - 1} ve {T})"
          + (f"; ek filtre: hedef yilda >= {arg.en_az_belge} ozet" if arg.en_az_belge else ""))
    saglam = [r for r in asirilar if r["sayi"] >= arg.saglamlik]
    print(f"Kobak vd. kuralina gore ASIRI KELIME: {len(asirilar)} "
          f"(delta > 0.01: {sum(r['delta'] > 0.01 for r in asirilar)})")
    print(f"  saglamlik: bunlardan hedef yilda >= {arg.saglamlik} ozette gecen: {len(saglam)} "
          f"(tablolarda 'ozet' < {arg.saglamlik} olanlar * ile isaretli)")
    tablo("Farka (delta) gore en cok artan ASIRI kelimeler:", asirilar)
    tablo("Kata (oran) gore en cok artan ASIRI kelimeler:",
          sorted(asirilar, key=lambda r: (-r["oran"], -r["delta"])))
    print(f"\nTum liste: {cikti}")


if __name__ == "__main__":
    main()
