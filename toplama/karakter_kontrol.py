#!/usr/bin/env python3
"""
Bozuk Karakter Sayimi (metne DOKUNMAZ)
=====================================
makaleler.jsonl'deki ozlerde PDF/sistem kaynakli olasi bozuk karakterleri sayar
ve her turden rastgele ornekleri Excel'e yazar. Kullanici her ornekte "onerilen
duzeltme dogru mu?" sorusunu D / Y diye cevaplar; kural ancak bundan sonra
oai_ayristir.py'ye eklenir (2026-10-31 karari).

Turler (yalnizca KELIME SAYIMINI bozanlar; 2026-11-03 karari):
  tire_harf_arasi  harf¬harf -> harfharf   (PDF tirelemesi: bu¬lunmaktadir)
  tire_bosluklu    harf¬ harf -> harfharf  (tireleme + satir sonu boslugu)
  yumusak_tire     gorunmez tire (U+00AD) -> silinir
  birlestirici_isaret  harf + ayri birlestirici isaret (Tu\u0308rkçe) -> NFC (2026-11-05)
  html_kalinti     iki kez cozulmesine ragmen kalan HTML kacisi (&amp;lt; -> <): metin
                   en az 3 kez kacislanmis; degismeyene kadar cozulur ("amp", "lt" sahte kelime)

Yillara gore: her turun 10.000 ozde kac ozde gectigi (yil_guvenilir). Amac: bozukluk
yillara gore degisiyorsa kelime sikliginda SAHTE egilim yaratabilir (2026-11-01).

CIKARILAN turler (2026-11-03, kullanici: "sadece harfleri alacagiz, zaman kaybetmeyelim"):
\\' ve \\" kacis hatalari kelime sayimini DEGISTIRMIYOR (ters egik cizgi ve tirnak zaten
kelime siniri: "29\\'u" ve "29'u" ikisi de ['u']); duzeltme LaTeX harf kodlarini bozuyordu
(Schr\\"{o}dinger). Bunlara ve dokunulmayacak diger \\ / ¬ kullanimlarina dokunulmaz,
dogrulanmaz. Excel'de bu turlerin satirlari varsa silinir (diger isaretler korunur).

Kullanim:
  python3 karakter_kontrol.py              # sayim + karakter_kontrol.xlsx
  python3 karakter_kontrol.py --adet 20
  python3 karakter_kontrol.py --hesapla    # isaretli Excel'den tur basina dogruluk + %95 aralik
  (Excel zaten varsa yalnizca sayim yapilir; yeniden olusturmak icin --uzerine-yaz)

  Yalnizca Turkce ozlerden, yalnizca gorunmez tire, ilk Excel'deki makaleler haric (2026-11-03):
  python3 karakter_kontrol.py --dil tr --tur yumusak_tire --haric karakter_kontrol.xlsx \\
                              --cikti karakter_kontrol_tr.xlsx
  python3 karakter_kontrol.py --hesapla --cikti karakter_kontrol_tr.xlsx
"""

import argparse
import html
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from dil_dogrulama import openpyxl_gerekli, wilson

KLASOR = Path(__file__).resolve().parent
TOHUM = 20261031
BAGLAM = 50  # isaretin iki yanindan gosterilecek karakter sayisi

# (tur, desen, onerilen duzeltme ya da None = dokunma)
TURLER = [
    ("tire_harf_arasi", re.compile(r"(?<=[^\W\d_])¬(?=[^\W\d_])"), ""),
    ("tire_bosluklu", re.compile(r"(?<=[^\W\d_])¬\s+(?=[^\W\d_])"), ""),
    ("yumusak_tire", re.compile("\u00ad"), ""),
    ("html_kalinti", re.compile(r"&(?:amp;)*(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);"), "COZ"),
    # 2026-11-05: harf + AYRI birlestirici isaret (u + \u0308 = ü; Unicode NFD). Kelime kurali isareti
    # harf saymadigi icin kelimeyi boler: "Tu\u0308rkçeye" -> "tu" + "rkçeye". Onerilen: NFC (birlestir).
    ("birlestirici_isaret", re.compile(r"(?<=[^\W\d_])[\u0300-\u036f]+"), "NFC"),
]
YIL_ALT, YIL_UST = 2010, 2026  # yillik tabloda gosterilen yillar


def gerekli_orneklem(hedef=0.95, z=1.96):
    """Ornegin HEPSI dogru cikarsa %95 Wilson araliginin alt siniri >= hedef olacak en kucuk n.
    (hepsi dogruyken alt sinir = n / (n + z^2)) -> hedef 0.95 icin n = 73.
    Kullanici karari (2026-11-01): her tur icin "%95 dogruluk" gosterilebilecek kadar ornek.
    Bir tek hata bile alt siniri %95'in altina indirir (72/73 -> %92,6)."""
    n = 1
    while n / (n + z * z) < hedef:
        n += 1
    return n


ADET = gerekli_orneklem()  # 73; adayi bundan az olan turde HEPSI incelenir


def tamamen_coz(parca):
    """HTML kacisini degismeyene kadar cozer (en fazla 5 kez): "&amp;lt;" -> "&lt;" -> "<"."""
    for _ in range(5):
        yeni = html.unescape(parca)
        if yeni == parca:
            break
        parca = yeni
    return parca


HARFLER = re.compile(r"[^\W\d_]+")


def parcalar(metin, m):
    """Isaretin solundaki ve sagindaki kelime parcasi: 'öğretme | öğrenme -> öğretmeöğrenme'.
    Iki parca da kendi basina bir kelimeyse isaret buyuk olasilikla gercek bir kisa cizginin
    yerine gecmis (birlesik terim); biri kelime degilse satir sonu bolmesidir ("koy | maktadır")."""
    sol = re.search(r"[^\W\d_]+$", metin[:m.start()])
    sag = re.match(r"\s*([^\W\d_]+)", metin[m.end():])
    if not sol or not sag:
        return ""
    return f"{sol.group()} | {sag.group(1)}  →  {sol.group()}{sag.group(1)}"


def ornek_metni(metin, m, duzeltme):
    """Isaretin cevresi: once (isaret ⟦ ⟧ icinde), sonra onerilen duzeltmeyle."""
    bas, son = max(0, m.start() - BAGLAM), min(len(metin), m.end() + BAGLAM)
    once = metin[bas:m.start()] + "⟦" + m.group().replace("\u00ad", "[görünmez tire]") + "⟧" + metin[m.end():son]
    if duzeltme == "COZ":
        duzeltme = tamamen_coz(m.group())
    elif duzeltme == "NFC":  # harfi isaretiyle birlikte tek karaktere cevir; birlesmeyen isaret kalir
        bas, son = max(0, m.start() - BAGLAM), min(len(metin), m.end() + BAGLAM)
        once = metin[bas:m.start() - 1] + "⟦" + metin[m.start() - 1:m.end()] + "⟧" + metin[m.end():son]
        return once, unicodedata.normalize("NFC", metin[bas:son])
    sonra = "" if duzeltme is None else metin[bas:m.start()] + duzeltme + metin[m.end():son]
    return once, sonra


def haric_adresler(yol):
    """Onceki Excel'deki (tur, makale adresi) ciftleri; yeni ornek bunlari tekrar almaz.
    Excel'deki adres /tr/ ya da /en/ olabilir; jsonl'deki adres bicimine (/en/) cevrilir."""
    openpyxl_gerekli()
    from openpyxl import load_workbook
    cift = set()
    for r in load_workbook(yol).active.iter_rows(min_row=2, values_only=True):
        if r[3]:
            cift.add((r[1], str(r[3]).replace("/tr/", "/en/")))
    return cift


def eski_turleri_sil(yol):
    """Excel'de artik TURLER'de olmayan turlerin satirlarini siler; kalan satirlarin cevaplari korunur."""
    openpyxl_gerekli()
    from openpyxl import load_workbook
    wb = load_workbook(yol)
    ws = wb.active
    gecerli = {t for t, _, _ in TURLER}
    silinecek = [r for r in range(2, ws.max_row + 1) if ws.cell(r, 2).value not in gecerli]
    for r in reversed(silinecek):  # alttan silinir ki satir numaralari kaymasin
        ws.delete_rows(r)
    if silinecek:
        wb.save(yol)
    return len(silinecek)


def hesapla(yol):
    """Excel'deki D/Y cevaplarindan tur basina dogruluk ve %95 Wilson araligi."""
    openpyxl_gerekli()
    from openpyxl import load_workbook
    sayac = defaultdict(Counter)
    for r in load_workbook(yol).active.iter_rows(min_row=2, values_only=True):
        cevap = str(r[6] or "").strip().upper()[:1]
        sayac[r[1]][cevap if cevap in ("D", "Y") else "bos"] += 1
    print(f"{'tur':>18} {'D':>4} {'Y':>4} {'bos':>4}   dogruluk (%95 aralik)")
    for tur, _, _ in TURLER:
        c = sayac.get(tur)
        if not c:
            continue
        n = c["D"] + c["Y"]
        sonuc = ""
        if n:
            alt, ust = wilson(c["D"], n)
            sonuc = f"%{100 * c['D'] / n:5.1f} ({100 * alt:.1f}–{100 * ust:.1f})"
        print(f"{tur:>18} {c['D']:>4} {c['Y']:>4} {c['bos']:>4}   {sonuc}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--adet", type=int, default=ADET, help=f"Tur basina ornek (varsayilan {ADET})")
    p.add_argument("--hesapla", action="store_true", help="isaretli Excel'den dogruluk hesapla")
    p.add_argument("--cikti", default=str(KLASOR / "karakter_kontrol.xlsx"))
    p.add_argument("--uzerine-yaz", action="store_true")
    p.add_argument("--dil", choices=["tr", "en"], help="yalnizca bu dildeki ozler (sayim da)")
    p.add_argument("--tur", action="append", choices=[t for t, _, _ in TURLER],
                   help="yalnizca bu tur(ler); birden cok kez verilebilir")
    p.add_argument("--haric", help="bu Excel'deki makaleler (ayni turde) ornege alinmaz")
    arg = p.parse_args()
    if arg.hesapla:
        return hesapla(arg.cikti)
    excel_yaz = arg.uzerine_yaz or not Path(arg.cikti).exists()
    secili = [t for t in TURLER if not arg.tur or t[0] in arg.tur]
    haric = haric_adresler(arg.haric) if arg.haric else set()

    oz_sayisi = Counter()      # tur -> kac ozde var
    isaret_sayisi = Counter()  # tur -> toplam kac kez
    adaylar = defaultdict(list)
    toplam_oz = 0
    yil_oz = Counter()                 # yil -> oz sayisi
    yil_tur = defaultdict(Counter)     # yil -> tur -> oz sayisi
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            yil = m.get("yil_guvenilir")
            for oz in m["ozler"]:
                if arg.dil and oz["dil"] != arg.dil:
                    continue
                metin = oz["metin"]
                toplam_oz += 1
                yil_oz[yil] += 1
                for tur, desen, duzeltme in secili:
                    bulunan = list(desen.finditer(metin))
                    if bulunan:
                        oz_sayisi[tur] += 1
                        yil_tur[yil][tur] += 1
                        isaret_sayisi[tur] += len(bulunan)
                        # her ozden bir isaret aday olur (ayni ozden ornek yigilmasin)
                        if (tur, m.get("url")) not in haric:
                            adaylar[tur].append((m.get("url"), oz["dil"], metin, bulunan[0], duzeltme))

    print(f"Toplam oz: {toplam_oz}" + (f" (yalnizca dil={arg.dil})" if arg.dil else "") + "\n")
    print(f"{'tur':>18} {'oz sayisi':>10} {'oz %':>7} {'isaret':>8}  onerilen")
    for tur, _, duzeltme in secili:
        oneri = ("dokunma (yalnizca sayim)" if duzeltme is None else
                 "-> degismeyene kadar coz" if duzeltme == "COZ" else
                 "-> NFC (harf + isaret tek karakter)" if duzeltme == "NFC" else f"-> {duzeltme!r}")
        print(f"{tur:>18} {oz_sayisi[tur]:>10} {100 * oz_sayisi[tur] / max(toplam_oz, 1):>6.2f}% "
              f"{isaret_sayisi[tur]:>8}  {oneri}")

    # Yillara gore: 10.000 ozde kac oz (turler sutun, yillar satir)
    kisa = {t: t.replace("ters_", "t_").replace("tire_", "¬_")[:10] for t, _, _ in secili}
    print(f"\nYillara gore (10.000 ozde kac ozde var; yil_guvenilir; None = yili guvenilmez):")
    print(f"{'yil':>6} {'oz':>8} " + " ".join(f"{kisa[t]:>10}" for t, _, _ in secili))
    yillar = [y for y in sorted(y for y in yil_oz if y is not None) if YIL_ALT <= y <= YIL_UST] + [None]
    for y in yillar:
        if not yil_oz[y]:
            continue
        print(f"{str(y):>6} {yil_oz[y]:>8} " +
              " ".join(f"{10000 * yil_tur[y][t] / yil_oz[y]:>10.1f}" for t, _, _ in secili))

    if not excel_yaz:
        silinen = eski_turleri_sil(arg.cikti)
        print(f"\n{arg.cikti} zaten var: yeniden olusturulmadi (isaretler korundu)"
              + (f"; cikarilan turlerin {silinen} satiri silindi." if silinen else ".")
              + " Yeniden olusturmak icin --uzerine-yaz.")
        return
    openpyxl_gerekli()
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation
    rng = random.Random(TOHUM)
    wb = Workbook()
    ws = wb.active
    ws.title = "kontrol"
    sutunlar = [("no", 5), ("tür", 16), ("soru", 34), ("adres", 30), ("önce (işaret ⟦ ⟧ içinde)", 60),
                ("önerilen düzeltmeden sonra", 60), ("cevap (D/Y)", 10), ("açıklama", 30),
                ("birleşen parçalar (sol | sağ → sonuç)", 40)]
    ws.append([a for a, _ in sutunlar])
    for i, (_, gen) in enumerate(sutunlar, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = gen
        ws.cell(1, i).font = Font(bold=True)
    no = 0
    for tur, _, duzeltme in secili:
        for url, dil, metin, m, duz in rng.sample(adaylar[tur], min(arg.adet, len(adaylar[tur]))):
            no += 1
            once, sonra = ornek_metni(metin, m, duz)
            soru = ("Bu işaret gerçek bir işaret mi (ör. mantıkta 'değil')? D = evet, dokunulmamalı; "
                    "Y = hayır, veri hatası" if duz is None else
                    "Önerilen düzeltme doğru mu? (işaret bir veri hatası ve düzeltilmiş hali doğru) D / Y")
            url_dil = url.replace("/en/", f"/{dil}/") if url and dil in ("tr", "en") else url
            ws.append([no, tur, soru, url_dil, once, sonra, "", "",
                       parcalar(metin, m) if tur != "html_kalinti" else ""])
            ws.cell(ws.max_row, 4).hyperlink = url_dil
    for satir in ws.iter_rows():
        for h in satir:
            h.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"D,Y"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{ws.max_row}")
    ws.freeze_panes = "A2"
    wb.save(arg.cikti)
    print(f"\n{no} ornek -> {arg.cikti} (tohum {TOHUM})")


if __name__ == "__main__":
    main()
