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

PAKET MODU (--paket 10): Ozetler 10'arli JSON paketleri halinde verilir; model
10 cevabi JSON olarak dondurur, tek seferde yapistirilir (model basina ~20
yapistirma). Karsilastirma adil olsun diye TUM modellerde ayni paket boyutu
kullanilmali.

Ipucu: Onceki cevaplarin modeli etkilememesi icin her pakette (tekli modda her
10-20 ornekte) yeni sohbet acin; ChatGPT'de "hafiza" ozelligini kapatin.

Kullanim:
  python3 deney_yapistir.py chatgpt --paket 10
  python3 deney_yapistir.py claude --paket 10
  python3 deney_yapistir.py gemini --paket 10
  python3 deney_yapistir.py chatgpt            # tek tek
  python3 deney_yapistir.py --durum
"""

import argparse
import json
import re
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
        if s.rstrip().endswith("###"):  # ### ayri satirda ya da metnin sonunda
            satirlar.append(s.rstrip()[:-3])
            return "\n".join(satirlar).strip()
        if not satirlar and s.strip().lower() in ("atla", "cik"):
            return s.strip().lower()
        satirlar.append(s)
    return "cik"  # girdi bitti (Ctrl+D)


PAKET_TALIMATI = (
    "Aşağıdaki JSON listesinde {n} ayrı akademik özet var. Her özeti BİRBİRİNDEN BAĞIMSIZ olarak "
    "şu talimata göre düzenle:\n\n{komut}\n"
    "Cevabını SADECE şu biçimde bir JSON listesi olarak ver, başka hiçbir şey yazma; her özet için "
    "aynı \"no\" değerini kullan ve hiçbir özeti atlama veya kısaltma:\n"
    '[{{"no": 1, "metin": "düzenlenmiş özet"}}, ...]\n\n')


def json_listesi_ayikla(metin):
    """Model cevabindaki JSON listesini bulur (```json ... ``` ve oncesi/sonrasi yazilar olabilir).
    ChatGPT ekrandan secilerek kopyalaninca koseli parantezler \\[ \\] olarak gelebiliyor."""
    metin = re.sub(r"\\([\[\]])", r"\1", metin)
    bas, son = metin.find("["), metin.rfind("]")
    if bas < 0 or son <= bas:
        raise ValueError("Cevapta JSON listesi ([ ... ]) bulunamadi")
    return json.loads(metin[bas:son + 1])


def paket_modu(veri, model, boyut):
    bekleyen = [o for o in veri["ornekler"] if not o["cevaplar"].get(model, "").strip()]
    print(f"{model}: {len(bekleyen)} ornek bekliyor, {boyut}'arli paketler. "
          f"Modelin JSON cevabini yapistirip yeni satira ### yazin.\n")
    for i in range(0, len(bekleyen), boyut):
        paket = bekleyen[i:i + boyut]
        girdi = [{"no": o["no"], "ozet": o["ozet_tr"]} for o in paket]
        komut = veri["komut"].split("Sadece düzenlenmiş özeti yaz")[0].strip()
        print("=" * 70)
        print(f"Paket: ornek {paket[0]['no']}-{paket[-1]['no']} ({len(paket)} ozet). YENI SOHBET acin.")
        print("-" * 25 + " MODELE VERILECEK METIN " + "-" * 21)
        print(PAKET_TALIMATI.format(n=len(paket), komut=komut) + json.dumps(girdi, ensure_ascii=False, indent=1))
        print("-" * 70)
        while True:
            print(f"{model} cevabini yapistirin (bitince yeni satira ###; 'atla' / 'cik'):")
            cevap = cevap_oku()
            if cevap in ("cik", "atla"):
                break
            try:
                liste = json_listesi_ayikla(cevap)
                gelen = {int(x["no"]): str(x["metin"]).strip() for x in liste}
            except (ValueError, KeyError, TypeError) as h:
                print(f"  HATA: cevap okunamadi ({h}). Tekrar yapistirin.\n")
                continue
            eksik = [o["no"] for o in paket if not gelen.get(o["no"])]
            if eksik:
                print(f"  UYARI: su orneklerin cevabi yok: {eksik} (sonra tekrar sorulur)")
            for o in paket:
                if gelen.get(o["no"]):
                    o["cevaplar"][model] = gelen[o["no"]]
            kaydet(veri)
            print(f"  kaydedildi: {len(paket) - len(eksik)}/{len(paket)}\n")
            break
        if cevap == "cik":
            break
    print("\nDurum:")
    durum(veri)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("model", nargs="?")
    p.add_argument("--durum", action="store_true", help="Sadece kac cevabin dolu oldugunu goster")
    p.add_argument("--paket", type=int, help="Ozetleri bu boyutta JSON paketleri halinde ver (orn. 10)")
    arg = p.parse_args()

    veri = json.loads(DOSYA.read_text(encoding="utf-8"))
    if arg.durum or not arg.model:
        durum(veri)
        return
    if arg.model not in veri["modeller"]:
        raise SystemExit(f"Model listede yok: {arg.model}. Secenekler: {', '.join(veri['modeller'])}")

    if arg.paket:
        paket_modu(veri, arg.model, arg.paket)
        return
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
