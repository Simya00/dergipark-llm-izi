#!/usr/bin/env python3
"""
Bozuk Karakter Sayimi (metne DOKUNMAZ)
=====================================
makaleler.jsonl'deki ozlerde PDF/sistem kaynakli olasi bozuk karakterleri sayar
ve her turden rastgele ornekleri Excel'e yazar. Kullanici her ornekte "onerilen
duzeltme dogru mu?" sorusunu D / Y diye cevaplar; kural ancak bundan sonra
oai_ayristir.py'ye eklenir (2026-10-31 karari).

Turler:
  ters_tirnak      \\'  -> '      (kacis hatasi: Universitesi\\'nde)
  ters_cift_tirnak \\"  -> "
  diger_ters       baska bir \\ kullanimi (yalnizca sayilir, duzeltme onerilmez)
  tire_harf_arasi  harf¬harf -> harfharf   (PDF tirelemesi: bu¬lunmaktadir)
  tire_bosluklu    harf¬ harf -> harfharf  (tireleme + satir sonu boslugu)
  tire_diger       baska bir ¬ kullanimi (ornegin mantikta "degil": ¬p) -> dokunulmaz
  yumusak_tire     gorunmez tire (U+00AD) -> silinir
  html_kalinti     iki kez cozulmesine ragmen kalan HTML kacisi (&amp;lt; -> <): metin
                   en az 3 kez kacislanmis; degismeyene kadar cozulur ("amp", "lt" sahte kelime)

Yillara gore: her turun 10.000 ozde kac ozde gectigi (yil_guvenilir). Amac: bozukluk
yillara gore degisiyorsa kelime sikliginda SAHTE egilim yaratabilir (2026-11-01).

Kullanim:
  python3 karakter_kontrol.py              # sayim + karakter_kontrol.xlsx
  python3 karakter_kontrol.py --adet 20
  (Excel zaten varsa yalnizca sayim yapilir; yeniden olusturmak icin --uzerine-yaz)
"""

import argparse
import html
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from dil_dogrulama import openpyxl_gerekli

KLASOR = Path(__file__).resolve().parent
TOHUM = 20261031
BAGLAM = 50  # isaretin iki yanindan gosterilecek karakter sayisi

# (tur, desen, onerilen duzeltme ya da None = dokunma)
TURLER = [
    ("ters_tirnak", re.compile(r"\\'"), "'"),
    ("ters_cift_tirnak", re.compile(r'\\"'), '"'),
    ("diger_ters", re.compile(r"\\(?!['\"])"), None),
    ("tire_harf_arasi", re.compile(r"(?<=[^\W\d_])¬(?=[^\W\d_])"), ""),
    ("tire_bosluklu", re.compile(r"(?<=[^\W\d_])¬\s+(?=[^\W\d_])"), ""),
    ("tire_diger", re.compile(r"(?<![^\W\d_])¬|¬(?!\s*[^\W\d_])"), None),
    ("yumusak_tire", re.compile("\u00ad"), ""),
    ("html_kalinti", re.compile(r"&(?:amp;)*(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+);"), "COZ"),
]
YIL_ALT, YIL_UST = 2010, 2026  # yillik tabloda gosterilen yillar


def tamamen_coz(parca):
    """HTML kacisini degismeyene kadar cozer (en fazla 5 kez): "&amp;lt;" -> "&lt;" -> "<"."""
    for _ in range(5):
        yeni = html.unescape(parca)
        if yeni == parca:
            break
        parca = yeni
    return parca


def ornek_metni(metin, m, duzeltme):
    """Isaretin cevresi: once (isaret ⟦ ⟧ icinde), sonra onerilen duzeltmeyle."""
    bas, son = max(0, m.start() - BAGLAM), min(len(metin), m.end() + BAGLAM)
    once = metin[bas:m.start()] + "⟦" + m.group().replace("\u00ad", "[görünmez tire]") + "⟧" + metin[m.end():son]
    if duzeltme == "COZ":
        duzeltme = tamamen_coz(m.group())
    sonra = "" if duzeltme is None else metin[bas:m.start()] + duzeltme + metin[m.end():son]
    return once, sonra


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--adet", type=int, default=10, help="Tur basina Excel'e yazilacak ornek")
    p.add_argument("--cikti", default=str(KLASOR / "karakter_kontrol.xlsx"))
    p.add_argument("--uzerine-yaz", action="store_true")
    arg = p.parse_args()
    excel_yaz = arg.uzerine_yaz or not Path(arg.cikti).exists()

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
                metin = oz["metin"]
                toplam_oz += 1
                yil_oz[yil] += 1
                for tur, desen, duzeltme in TURLER:
                    bulunan = list(desen.finditer(metin))
                    if bulunan:
                        oz_sayisi[tur] += 1
                        yil_tur[yil][tur] += 1
                        isaret_sayisi[tur] += len(bulunan)
                        # her ozden bir isaret aday olur (ayni ozden ornek yigilmasin)
                        adaylar[tur].append((m.get("url"), oz["dil"], metin, bulunan[0], duzeltme))

    print(f"Toplam oz: {toplam_oz}\n")
    print(f"{'tur':>18} {'oz sayisi':>10} {'oz %':>7} {'isaret':>8}  onerilen")
    for tur, _, duzeltme in TURLER:
        oneri = ("dokunma (yalnizca sayim)" if duzeltme is None else
                 "-> degismeyene kadar coz" if duzeltme == "COZ" else f"-> {duzeltme!r}")
        print(f"{tur:>18} {oz_sayisi[tur]:>10} {100 * oz_sayisi[tur] / max(toplam_oz, 1):>6.2f}% "
              f"{isaret_sayisi[tur]:>8}  {oneri}")

    # Yillara gore: 10.000 ozde kac oz (turler sutun, yillar satir)
    kisa = {t: t.replace("ters_", "t_").replace("tire_", "¬_")[:10] for t, _, _ in TURLER}
    print(f"\nYillara gore (10.000 ozde kac ozde var; yil_guvenilir; None = yili guvenilmez):")
    print(f"{'yil':>6} {'oz':>8} " + " ".join(f"{kisa[t]:>10}" for t, _, _ in TURLER))
    yillar = [y for y in sorted(y for y in yil_oz if y is not None) if YIL_ALT <= y <= YIL_UST] + [None]
    for y in yillar:
        if not yil_oz[y]:
            continue
        print(f"{str(y):>6} {yil_oz[y]:>8} " +
              " ".join(f"{10000 * yil_tur[y][t] / yil_oz[y]:>10.1f}" for t, _, _ in TURLER))

    if not excel_yaz:
        print(f"\n{arg.cikti} zaten var: Excel'e dokunulmadi (yeniden olusturmak icin --uzerine-yaz).")
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
                ("önerilen düzeltmeden sonra", 60), ("cevap (D/Y)", 10), ("açıklama", 30)]
    ws.append([a for a, _ in sutunlar])
    for i, (_, gen) in enumerate(sutunlar, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = gen
        ws.cell(1, i).font = Font(bold=True)
    no = 0
    for tur, _, duzeltme in TURLER:
        for url, dil, metin, m, duz in rng.sample(adaylar[tur], min(arg.adet, len(adaylar[tur]))):
            no += 1
            once, sonra = ornek_metni(metin, m, duz)
            soru = ("Bu işaret gerçek bir işaret mi (ör. mantıkta 'değil')? D = evet, dokunulmamalı; "
                    "Y = hayır, veri hatası" if duz is None else
                    "Önerilen düzeltme doğru mu? (işaret bir veri hatası ve düzeltilmiş hali doğru) D / Y")
            url_dil = url.replace("/en/", f"/{dil}/") if url and dil in ("tr", "en") else url
            ws.append([no, tur, soru, url_dil, once, sonra, "", ""])
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
