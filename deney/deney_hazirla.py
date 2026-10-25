#!/usr/bin/env python3
"""
LLM Yeniden Yazim Deneyi: Ornek Secimi
======================================
ChatGPT oncesi (varsayilan 2018-2021) DergiPark Turkce ozetlerinden rastgele
--adet tanesini secer ve deney_ornekleri.json'a yazar. Her ornekte modellerin
cevaplari icin bos alanlar vardir; deney_yapistir.py ile doldurulur.

Secim kurallari:
  - yil_guvenilir --yillar araliginda, ozet_tr --min/--max karakter arasinda
  - her dergiden en fazla 1 ozet (alan cesitliligi)
  - birlesik kelimesi (bosluk kaybi: "rakımlaragöre") >= 2 olan ozetler
    haric: modeller bosluklari duzeltir, bu da sahte bir "LLM degisikligi"
    gibi gorunur. (analiz/sozluk_tr.tsv.gz varsa kontrol edilir; yoksa uyari.)
  - metni gercekten Turkce olmayan ozetler haric (bazi dergiler Ingilizce
    abstract'i Turkce alanina girmis; model bunu "akademiklestirmek" yerine
    cevirir)
  - sabit tohum (--tohum): ayni komut ayni ornekleri secer

--degistir: Var olan deney_ornekleri.json'daki uygun OLMAYAN ornekleri (orn.
Turkce olmayan) kullanilmamis dergilerden yeni orneklerle degistirir; diger
orneklerin yapistirilmis cevaplari korunur, degisen orneklerin cevaplari
silinir (yeniden sorulmali).

Kullanim:
  python3 deney_hazirla.py
  python3 deney_hazirla.py --adet 200 --modeller chatgpt,claude,gemini
  python3 deney_hazirla.py --degistir
"""

import argparse
import json
import random
import sys
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR.parent / "analiz"))
sys.path.insert(0, str(KLASOR.parent / "toplama"))
from kelime_siklik import birlesik_mi, kelime_listesi, sozluk  # noqa: E402
from oai_ayristir import dil_kesin, dil_tahmin  # noqa: E402

VARSAYILAN_GIRDI = KLASOR.parent / "toplama" / "makaleler.jsonl"
CIKTI = KLASOR / "deney_ornekleri.json"

KOMUT = ("Aşağıdaki akademik özeti, anlamını ve bulgularını değiştirmeden, akademik yazım "
         "diline uygun olacak şekilde yeniden düzenle. Sadece düzenlenmiş özeti yaz; başlık, "
         "açıklama veya not ekleme.\n\n")


def turkce_mi(oz):
    return dil_tahmin(oz) == "tr" and dil_kesin(oz) != "en"


def uygun_mu(oz, sz, arg):
    if not (arg.min <= len(oz) <= arg.max) or not turkce_mi(oz):
        return False
    return not (sz and sum(1 for w in kelime_listesi(oz, "tr", onarim=False) if birlesik_mi(w, sz)) >= 2)


def ornek(no, m, modeller):
    return {"no": no, "oai_id": m["oai_id"], "url": m.get("url"), "dergi_kodu": m["dergi_kodu"],
            "yil": m["yil_guvenilir"], "ozet_tr": m["ozet_tr"], "cevaplar": {model: "" for model in modeller}}


def degistir(arg, adaylar, sz):
    veri = json.loads(CIKTI.read_text(encoding="utf-8"))
    kullanilan = {o["dergi_kodu"] for o in veri["ornekler"]}
    rng = random.Random(arg.tohum + 1)
    yedek = sorted(set(adaylar) - kullanilan)
    rng.shuffle(yedek)
    degisen = 0
    for i, o in enumerate(veri["ornekler"]):
        if uygun_mu(o["ozet_tr"], sz, arg):
            continue
        if not yedek:
            raise SystemExit("Yedek dergi kalmadi.")
        d = yedek.pop()
        yeni = ornek(o["no"], rng.choice(sorted(adaylar[d], key=lambda x: x["oai_id"])), veri["modeller"])
        dolu = [m for m, c in o["cevaplar"].items() if c.strip()]
        print(f"  ornek {o['no']} ({o['dergi_kodu']}) degisti -> {d}"
              + (f"; silinen cevaplar: {', '.join(dolu)} (yeniden sorulmali)" if dolu else ""))
        veri["ornekler"][i] = yeni
        degisen += 1
    CIKTI.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{degisen} ornek degistirildi -> {CIKTI}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--adet", type=int, default=200)
    p.add_argument("--yillar", default="2018-2021")
    p.add_argument("--min", type=int, default=400, help="En kisa ozet (karakter)")
    p.add_argument("--max", type=int, default=1500, help="En uzun ozet (karakter)")
    p.add_argument("--modeller", default="chatgpt,claude,gemini")
    p.add_argument("--tohum", type=int, default=20261024)
    p.add_argument("--uzerine-yaz", action="store_true", help="Var olan deney dosyasinin uzerine yaz")
    p.add_argument("--degistir", action="store_true", help="Var olan dosyadaki uygun olmayan ornekleri degistir")
    arg = p.parse_args()

    if CIKTI.exists() and not (arg.uzerine_yaz or arg.degistir):
        raise SystemExit(f"{CIKTI.name} zaten var (icinde yapistirilmis cevaplar olabilir). "
                         f"Gercekten yeniden olusturmak icin --uzerine-yaz ekleyin.")
    bas, son = map(int, arg.yillar.split("-"))
    sz = sozluk("tr")
    if not sz:
        print("UYARI: analiz/sozluk_tr.tsv.gz yok; birlesik kelime kontrolu yapilamiyor. "
              "Once: cd ../analiz && python3 birlesik_kelime.py sozluk --dil tr", file=sys.stderr)

    adaylar = {}  # dergi -> ozetler
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            oz = m.get("ozet_tr")
            if not oz or not (bas <= (m.get("yil_guvenilir") or 0) <= son) or not uygun_mu(oz, sz, arg):
                continue
            adaylar.setdefault(m["dergi_kodu"], []).append(m)

    if arg.degistir:
        degistir(arg, adaylar, sz)
        return

    rng = random.Random(arg.tohum)
    dergiler = sorted(adaylar)
    rng.shuffle(dergiler)
    if len(dergiler) < arg.adet:
        raise SystemExit(f"Yalnizca {len(dergiler)} dergiden uygun ozet var; --adet'i dusurun.")
    modeller = [m.strip() for m in arg.modeller.split(",") if m.strip()]
    ornekler = []
    for i, d in enumerate(dergiler[:arg.adet], 1):
        ornekler.append(ornek(i, rng.choice(sorted(adaylar[d], key=lambda x: x["oai_id"])), modeller))

    veri = {"aciklama": "LLM yeniden yazim deneyi. Her ornek icin komut + ozet modele verilir, "
                        "cevap deney_yapistir.py ile ilgili alana yazilir.",
            "komut": KOMUT, "modeller": modeller, "tohum": arg.tohum, "yillar": arg.yillar,
            "ornekler": ornekler}
    CIKTI.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(adaylar)} dergiden uygun ozet bulundu; {len(ornekler)} ornek secildi -> {CIKTI}")
    yil_say = {}
    for o in ornekler:
        yil_say[o["yil"]] = yil_say.get(o["yil"], 0) + 1
    print("Yillara gore:", dict(sorted(yil_say.items())))


if __name__ == "__main__":
    main()
