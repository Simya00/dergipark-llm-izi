#!/usr/bin/env python3
"""
Dil Temizliginin Elle Dogrulanmasi
==================================
oai_ayristir.py'nin dil temizligi kararlarini (etiket duzeltme, iki dilli
bolme, bozuk metin, diger dil) kullanicinin elle kontrol etmesi icin.

  ornekle: Her kategoriden rastgele --adet oz secip dil_dogrulama.tsv'ye yazar.
  incele:  Bos kalan ornekleri terminalde TEK TEK, okunakli gosterir; cevabi
           (E / K / H, istege bagli aciklamayla) dosyaya kaydeder.
             E = dogru, K = kismen dogru (karar dogru, kucuk purus: orn. bolmede
             sinirdaki bir cumle yanlis tarafta), H = yanlis
  excel:   Ornekleri dil_dogrulama.xlsx'e yazar (sade soru, tiklanabilir link,
           satirlara bolunmus metin, E/K/H acilir listesi). Excel/LibreOffice'te
           doldurulur. (Gerekli: pip install openpyxl)
  hesapla: Kategori basina dogruluk oranini (sadece E ve E+K) ve %95 guven
           araligini (Wilson) hesaplar. dil_dogrulama.xlsx varsa onu, yoksa
           TSV'yi okur.

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
import shutil
import textwrap
from collections import defaultdict
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
DOSYA = KLASOR / "dil_dogrulama.tsv"
EXCEL = KLASOR / "dil_dogrulama.xlsx"
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


SORULAR = {
    "etiket_duzeltildi": "Metin gercekten 'karar' dilinde mi? (etiket {etiket} idi, kod {karar} yapti)",
    "iki_dilli_bolundu": "TR parca Turkce, EN parca Ingilizce mi? Bolme dogru yerden mi?",
    "bozuk_metin": "Metin gercekten bozuk/okunamaz mi (ya da TR/EN disi bir alfabede mi)?",
    "diger_dil": "Metin gercekten Turkce ve Ingilizce disinda bir dilde mi?",
    "dokunulmadi": "Metin gercekten SADECE Turkce mi? (Ingilizce oz ya da iki dil varsa: H)",
}


def satirlari_oku():
    with open(DOSYA, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def satirlari_yaz(satirlar):
    gecici = DOSYA.with_suffix(".tsv.gecici")
    with open(gecici, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUTUNLAR, delimiter="\t")
        w.writeheader()
        w.writerows(satirlar)
    gecici.replace(DOSYA)  # yarim yazilmis dosya kalmasin


def komut_incele(arg):
    satirlar = satirlari_oku()
    genislik = min(shutil.get_terminal_size().columns, 110) - 4
    bekleyen = [s for s in satirlar if not s["dogru_mu"].strip()]
    print(f"{len(bekleyen)}/{len(satirlar)} ornek bekliyor. Cevap: E / K / H (istersen bosluk + aciklama), "
          f"'atla' ya da 'cik'.\n")
    for s in bekleyen:
        print("=" * (genislik + 4))
        print(f"[{s['no']}/{len(satirlar)}]  KATEGORI: {s['kategori']}   etiket: {s['etiket']}   karar: {s['karar']}")
        print(f"  {s['url']}")
        print(f"  SORU: {SORULAR[s['kategori']].format(**s)}\n")
        bolumler = ([("TR PARCA", s["tr_parca"]), ("EN PARCA", s["en_parca"])]
                    if s["kategori"] == "iki_dilli_bolundu" else [("METIN", s["metin"])])
        for baslik, metin in bolumler:
            print(f"  --- {baslik} ---")
            print(textwrap.fill(metin or "(bos)", genislik, initial_indent="  ", subsequent_indent="  "))
            print()
        while True:
            cevap = input("  Cevap (E/K/H): ").strip()
            if cevap.lower() in ("cik", "atla"):
                break
            harf, _, aciklama = cevap.partition(" ")
            if harf.upper() in ("E", "K", "H"):
                s["dogru_mu"], s["not"] = harf.upper(), aciklama.strip()
                satirlari_yaz(satirlar)
                break
            print("  E, K, H, 'atla' ya da 'cik' yazin.")
        if cevap.lower() == "cik":
            break
    kalan = sum(1 for s in satirlar if not s["dogru_mu"].strip())
    print(f"\nKaydedildi. Kalan: {kalan}. Sonuc icin: python3 dil_dogrulama.py hesapla")


KATEGORI_ADI = {
    "etiket_duzeltildi": "Dil etiketi düzeltildi",
    "iki_dilli_bolundu": "İki dilli alan ikiye bölündü",
    "bozuk_metin": "Bozuk metin diye atıldı",
    "diger_dil": "Başka dil diye ayrıldı",
    "dokunulmadi": "Kod dokunmadı (Türkçe kabul edildi)",
}
SADE_SORU = {
    "etiket_duzeltildi": "DergiPark '{etiket}' demiş, kod '{karar}' dedi. Metin gerçekten {karar_ad} mi?",
    "iki_dilli_bolundu": "Kod bu alanda hem Türkçe hem İngilizce özet olduğunu söyleyip ikiye böldü. "
                         "'TR parça' Türkçe, 'EN parça' İngilizce mi? Bölme doğru yerden mi?",
    "bozuk_metin": "Kod bu metni okunamaz/bozuk diye attı. Metin gerçekten okunamaz ya da "
                   "Türkçe/İngilizce dışında bir alfabede mi?",
    "diger_dil": "Kod bu metnin Türkçe veya İngilizce olmadığını söyledi. Doğru mu?",
    "dokunulmadi": "Kod bu metni Türkçe kabul edip dokunmadı. Metin gerçekten SADECE Türkçe mi? "
                   "(İçinde İngilizce özet varsa ya da tamamen İngilizceyse: H)",
}
DIL_AD = {"tr": "Türkçe", "en": "İngilizce"}
EXCEL_SUTUNLAR = [("no", 6), ("kategori", 22), ("soru", 40), ("link", 18), ("metin / TR parça", 70),
                  ("EN parça", 60), ("cevap (E/K/H)", 10), ("açıklama", 30)]


def komut_excel(arg):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    if EXCEL.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{EXCEL.name} zaten var (doldurdugunuz cevaplar olabilir). "
                         f"Yeniden olusturmak icin --uzerine-yaz ekleyin.")
    wb = Workbook()
    ws = wb.active
    ws.title = "dogrulama"
    ws.append([ad for ad, _ in EXCEL_SUTUNLAR])
    for i, (_, genislik) in enumerate(EXCEL_SUTUNLAR, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = genislik
        ws.cell(1, i).font = Font(bold=True)
        ws.cell(1, i).fill = PatternFill("solid", fgColor="DDDDDD")
    for s in satirlari_oku():
        bolundu = s["kategori"] == "iki_dilli_bolundu"
        soru = SADE_SORU[s["kategori"]].format(etiket=s["etiket"], karar=s["karar"],
                                               karar_ad=DIL_AD.get(s["karar"], s["karar"]))
        ws.append([int(s["no"]), KATEGORI_ADI[s["kategori"]], soru, "makaleyi aç",
                   s["tr_parca"] if bolundu else s["metin"], s["en_parca"] if bolundu else "",
                   s["dogru_mu"], s["not"]])
        r = ws.max_row
        ws.cell(r, 4).hyperlink = s["url"]
        ws.cell(r, 4).font = Font(color="0563C1", underline="single")
    hizala = Alignment(wrap_text=True, vertical="top")
    for satir in ws.iter_rows(min_row=1):
        for hucre in satir:
            hucre.alignment = hizala
    dv = DataValidation(type="list", formula1='"E,K,H"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{ws.max_row}")
    ws.freeze_panes = "A2"  # basliklar kayarken gorunur kalsin
    wb.save(EXCEL)
    print(f"{ws.max_row - 1} satir -> {EXCEL}")


def excel_oku():
    """dil_dogrulama.xlsx'teki cevaplari TSV satirlariyla eslestirip dondurur (no -> (cevap, aciklama))."""
    from openpyxl import load_workbook
    ws = load_workbook(EXCEL).active
    basliklar = [c.value for c in ws[1]]
    i_no, i_cevap, i_not = basliklar.index("no"), basliklar.index("cevap (E/K/H)"), basliklar.index("açıklama")
    return {str(r[i_no]): (str(r[i_cevap] or ""), str(r[i_not] or ""))
            for r in ws.iter_rows(min_row=2, values_only=True) if r[i_no] is not None}


def wilson(dogru, n, z=1.96):
    """Oran icin %95 guven araligi (Wilson). Kucuk orneklerde ve %100'e yakin oranlarda guvenilir."""
    if n == 0:
        return 0.0, 0.0
    p = dogru / n
    merkez = (p + z * z / (2 * n)) / (1 + z * z / n)
    yari = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, merkez - yari), min(1.0, merkez + yari)


def komut_hesapla(arg):
    sayac = defaultdict(lambda: {"E": 0, "K": 0, "H": 0, "bos": 0})
    excel = excel_oku() if EXCEL.exists() else None
    print(f"Okunan: {EXCEL.name if excel is not None else DOSYA.name}\n")
    for s in satirlari_oku():
        if excel is not None:
            s["dogru_mu"], s["not"] = excel.get(s["no"], ("", ""))
        cevap = s["dogru_mu"].strip().upper()[:1]
        sayac[s["kategori"]][cevap if cevap in ("E", "K", "H") else "bos"] += 1
    print(f"{'kategori':>18} {'E':>4} {'K':>4} {'H':>4} {'bos':>4}   {'sadece E (%95 aralik)':>24}   "
          f"{'E+K (%95 aralik)':>22}")
    for kat in KATEGORILER:
        c = sayac[kat]
        n = c["E"] + c["K"] + c["H"]
        if not n:
            print(f"{kat:>18} {'-':>4} {'-':>4} {'-':>4} {c['bos']:>4}")
            continue
        sonuc = []
        for dogru in (c["E"], c["E"] + c["K"]):
            alt, ust = wilson(dogru, n)
            sonuc.append(f"{100 * dogru / n:5.1f}% ({100 * alt:4.1f}–{100 * ust:5.1f})")
        print(f"{kat:>18} {c['E']:>4} {c['K']:>4} {c['H']:>4} {c['bos']:>4}   {sonuc[0]:>24}   {sonuc[1]:>22}")
    print("\nNot: 'dokunulmadi' satirinda H = kodun KACIRDIGI bir sorun (yanlis etiket ya da iki dilli).")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["ornekle", "excel", "incele", "hesapla"])
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--adet", type=int, default=50, help="Kategori basina ornek sayisi")
    p.add_argument("--tohum", type=int, default=20261025)
    p.add_argument("--uzerine-yaz", action="store_true")
    arg = p.parse_args()
    {"ornekle": komut_ornekle, "excel": komut_excel, "incele": komut_incele,
     "hesapla": komut_hesapla}[arg.komut](arg)


if __name__ == "__main__":
    main()
