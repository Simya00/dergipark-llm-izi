#!/usr/bin/env python3
"""
LLM Yeniden Yazim Deneyi: Cevap Yapistirma Yardimcisi
=====================================================
deney_ornekleri.json'da secilen modelin bos cevaplarini sirayla gosterir:
  1. Ekrana modele verilecek metni (komut + ozet) basar.
  2. Siz bunu kopyalayip modele (ChatGPT / Claude / Gemini) verirsiniz.
  3. Modelin cevabini terminale yapistirip YENI BIR SATIRA ### yazar, Enter'a basarsiniz.
  4. Cevap JSON'a hemen kaydedilir (her ornekten sonra; yarida birakmak guvenli).

Ozel girdiler (tek basina bir satirda):
  ###    cevabi bitir ve kaydet
  atla   bu ornegi simdilik atla
  cik    kaydedip cik

Ipucu: Onceki cevaplarin modeli etkilememesi icin her 10-20 ornekte bir yeni
sohbet acin (ChatGPT'de "hafiza" ozelligini de kapatmak iyi olur).

Kullanim:
  python3 deney_yapistir.py chatgpt
  python3 deney_yapistir.py claude
  python3 deney_yapistir.py --durum
"""

import argparse
import json
import sys
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
DOSYA = KLASOR / "deney_ornekleri.json"


def kaydet(veri):
    gecici = DOSYA.with_suffix(".json.gecici")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    gecici.replace(DOSYA)  # yarim yazilmis dosya kalmasin


def durum(veri):
    for model in veri["modeller"]:
        dolu = sum(1 for o in veri["ornekler"] if o["cevaplar"].get(model, "").strip())
        print(f"  {model:>10}: {dolu}/{len(veri['ornekler'])}")


def cevap_oku():
    satirlar = []
    for satir in sys.stdin:
        s = satir.rstrip("\n")
        if s.strip() == "###":
            return "\n".join(satirlar).strip()
        if not satirlar and s.strip().lower() in ("atla", "cik"):
            return s.strip().lower()
        satirlar.append(s)
    return "cik"  # girdi bitti (Ctrl+D)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("model", nargs="?")
    p.add_argument("--durum", action="store_true", help="Sadece kac cevabin dolu oldugunu goster")
    arg = p.parse_args()

    veri = json.loads(DOSYA.read_text(encoding="utf-8"))
    if arg.durum or not arg.model:
        durum(veri)
        return
    if arg.model not in veri["modeller"]:
        raise SystemExit(f"Model listede yok: {arg.model}. Secenekler: {', '.join(veri['modeller'])}")

    bekleyen = [o for o in veri["ornekler"] if not o["cevaplar"].get(arg.model, "").strip()]
    print(f"{arg.model}: {len(bekleyen)} ornek bekliyor. Cevabi yapistirdiktan sonra yeni satira ### yazin.\n")
    for o in bekleyen:
        print("=" * 70)
        print(f"Ornek {o['no']}/{len(veri['ornekler'])}  ({o['dergi_kodu']}, {o['yil']})")
        print("-" * 25 + " MODELE VERILECEK METIN " + "-" * 21)
        print(veri["komut"] + o["ozet_tr"])
        print("-" * 70)
        print(f"{arg.model} cevabini yapistirin (bitince yeni satira ###):")
        cevap = cevap_oku()
        if cevap == "cik":
            break
        if cevap == "atla" or not cevap:
            print("  (atlandi)\n")
            continue
        o["cevaplar"][arg.model] = cevap
        kaydet(veri)
        print(f"  kaydedildi ({len(cevap)} karakter)\n")
    print("\nDurum:")
    durum(veri)


if __name__ == "__main__":
    main()
