#!/usr/bin/env python3
"""
Yayin Yili Kuralinin Elle Dogrulanmasi (2026-11-27; dis degerlendirme onerisi)
=============================================================================
Yil kurali (oai_ayristir.py, yontem.md §3) iki karar veriyor; ikisi de daha once
rastgele ornekle dogrulanmadi:
  A) ARSIV: ayni dergide ayni gun >= 3 farkli cilt yuklenmisse (ve o dergide toplu
     yuklenen en buyuk cilde kadar) makale "arsiv" sayilir, yili guvenilmez, analiz
     disi kalir (173.496 makale). Dogruysa makalenin GERCEK yayin yili, kayittaki
     tarih yilindan ONCE olmali.
  B) GUVENILIR YIL: analize giren makalelerde (2015-2025, Turkce ozet) kullanilan
     yil (yil_guvenilir). Dogruysa GERCEK yayin yili ile ayni olmali. Bu grup sonuc
     icin daha onemli: yanlis yil dogrudan analize girer.

Her gruptan 73 rastgele makale (hepsi dogruysa %95 Wilson alt siniri %95; onceki
dogrulamalarla ayni kural). Iki grup KARISIK sirada; Excel'de grup ve kayittaki yil
YOK (kor): kullanici yalnizca makale sayfasindaki gercek yayin yilini yazar.
Anahtar (grup, kayittaki yil) ayri dosyada: yil_dogrulama_anahtar.json.

  excel   : ornek secer -> yil_dogrulama.xlsx + yil_dogrulama_anahtar.json
  gir     : KOLAY GIRIS: bos satirlarin makale sayfasini sirayla tarayicida acar,
            terminalde yili sorar ve Excel'e yazar (her cevaptan sonra kaydeder).
            Excel acikken calistirmayin (once kapatin).
  hesapla : doldurulmus Excel'den grup basina dogruluk ve Wilson %95 araligi

Kullanim (toplama/ klasorunde):
  python3 yil_dogrulama.py excel
  python3 yil_dogrulama.py hesapla
"""

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR.parent / "analiz"))

TOHUM = 20261127
ORNEK = 73
EXCEL = KLASOR / "yil_dogrulama.xlsx"
ANAHTAR = KLASOR / "yil_dogrulama_anahtar.json"
YIL_BASLIK = "sayfadaki yayın yılı"


def wilson(d, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = d / n
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    o = (p + z * z / (2 * n)) / (1 + z * z / n)
    return o - m, o + m


def excel(arg):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from kelime_siklik import analize_girer
    if EXCEL.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{EXCEL} zaten var (isaretleriniz olabilir). Yeniden olusturmak icin --uzerine-yaz.")
    rng = random.Random(TOHUM)
    havuz = {"A": [], "B": []}
    gorulen = {"A": 0, "B": 0}
    with open(KLASOR / "makaleler.jsonl", encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            if m.get("yil_kaynagi") == "arsiv":
                grup = "A"
            elif m.get("yil_guvenilir") in range(2015, 2026) and analize_girer(m, "ozet_tr", None):
                grup = "B"
            else:
                continue
            kayit = {"grup": grup, "url": m.get("url"), "dergi": (m.get("dergi") or [""])[0],
                     "cilt": m.get("cilt"), "sayi": m.get("sayi"),
                     "baslik": next((b["metin"] for b in m.get("basliklar", [])), ""),
                     "kayit_yili": m.get("yil"), "yil_guvenilir": m.get("yil_guvenilir")}
            gorulen[grup] += 1  # rezervuar ornekleme
            if len(havuz[grup]) < ORNEK:
                havuz[grup].append(kayit)
            elif (j := rng.randrange(gorulen[grup])) < ORNEK:
                havuz[grup][j] = kayit
    secilen = havuz["A"] + havuz["B"]
    rng.shuffle(secilen)

    wb = Workbook()
    a = wb.active
    a.title = "aciklama"
    for s in [
        "Her satirdaki makalenin GERCEK yayin yilini bulun ve 'sayfadaki yayın yılı' sutununa yazin.",
        "1. 'makale sayfasi' baglantisini acin (DergiPark).",
        "2. Basligin ustundeki/altindaki kunye satirina bakin: 'Yıl 2009, Cilt: 10, Sayı: 2' gibi. Oradaki YIL'i yazin.",
        "   DIKKAT: 'Yayımlanma Tarihi' / 'Gönderilme Tarihi' DEGIL; toplu yuklenen eski sayilarda bu tarih yukleme tarihidir.",
        "3. Kunyede yil yoksa sayi sayfasina (cilt/sayi baglantisi) bakin. Hala bulunamiyorsa '?' yazin, nedenini 'not'a yazin.",
        "Sira rastgeledir; hangi makalenin hangi gruptan geldigi bilerek gosterilmiyor.",
        "Tahmini sure: makale basina ~1 dakika (146 makale). 10'arli parcalar halinde yapabilirsiniz.",
    ]:
        a.append([s])
    a.column_dimensions["A"].width = 120
    ws = wb.create_sheet("dogrulama")
    ws.append(["no", "makale sayfasi", "dergi", "cilt", "sayi", "baslik", YIL_BASLIK, "not"])
    for i, k in enumerate(secilen, 1):
        ws.append([i, k["url"], k["dergi"], k["cilt"], k["sayi"], (k["baslik"] or "")[:150], "", ""])
        if k["url"]:
            ws.cell(i + 1, 2).hyperlink = k["url"]
    for s, w in zip("ABCDEFGH", (6, 45, 30, 6, 6, 60, 14, 30)):
        ws.column_dimensions[s].width = w
    sari = PatternFill("solid", fgColor="FFF2CC")
    for row in ws.iter_rows(min_row=2):
        row[5].alignment = Alignment(wrap_text=True, vertical="top")
        row[6].fill = sari
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "C2"
    wb.active = 1
    wb.save(EXCEL)
    ANAHTAR.write_text(json.dumps([{"no": i, **k} for i, k in enumerate(secilen, 1)], ensure_ascii=False, indent=1),
                       encoding="utf-8")
    print(f"Havuz: arsiv {gorulen['A']}, analize giren {gorulen['B']} -> her birinden {ORNEK}")
    print(f"-> {EXCEL} ({len(secilen)} satir)\n-> {ANAHTAR} (anahtar: grup ve kayittaki yil; Excel'i doldururken acmayin)")


def gir(arg):
    import webbrowser
    from openpyxl import load_workbook
    wb = load_workbook(EXCEL)
    ws = wb["dogrulama"]
    j = [h.value for h in ws[1]].index(YIL_BASLIK)
    if arg.no:  # belirli satirlari yeniden gir (yanlis yazilan yil)
        bos = [row for row in ws.iter_rows(min_row=2) if row[0].value in set(arg.no)]
    else:
        bos = [row for row in ws.iter_rows(min_row=2) if row[0].value and row[j].value in (None, "")]
    print(f"{len(bos)} bos satir. Her makale tarayicida acilacak; kunyedeki 'Yıl / Year' degerini yazin.")
    print("Yil bulunamazsa ?  | atlamak icin bos Enter | cikmak icin q | 3 yerine x yazabilirsiniz (201x = 2013)\n")
    for row in bos:
        url = row[1].value
        print(f"#{row[0].value}  {url}" + (f"   (su anki deger: {row[j].value})" if row[j].value else ""))
        if url:
            webbrowser.open(url)
        while True:  # yazim hatasi korumasi: 4 haneli yil (1900-2099), ? , bos ya da q
            cevap = input("  Yil: ").strip().replace("x", "3").replace("X", "3")  # 3 tusu yerine x
            if cevap.lower() in ("q", "?", "") or re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", cevap):
                break
            print(f"  '{cevap}' gecerli bir yil degil (4 hane olmali, orn. 2019). Tekrar yazin.")
        if cevap.lower() == "q":
            break
        if not cevap:
            continue
        print(f"  -> kaydedildi: {cevap}")
        row[j].value = cevap
        if cevap == "?":
            row[j + 1].value = input("  Neden bulunamadi (kisaca, bos gecilebilir): ").strip() or None
        wb.save(EXCEL)
    wb.save(EXCEL)
    kalan = sum(1 for row in ws.iter_rows(min_row=2) if row[0].value and row[j].value in (None, ""))
    print(f"Kaydedildi. Kalan bos satir: {kalan}")


def hesapla(arg):
    from openpyxl import load_workbook
    anahtar = {k["no"]: k for k in json.loads(ANAHTAR.read_text(encoding="utf-8"))}
    ws = load_workbook(EXCEL)["dogrulama"]
    satirlar = list(ws.iter_rows(values_only=True))
    j = satirlar[0].index(YIL_BASLIK)
    sonuc = {"A": [0, 0, 0, 0], "B": [0, 0, 0, 0]}  # dogru, yanlis, ?, bos
    yanlislar = []
    for r in satirlar[1:]:
        if r[0] not in anahtar:
            continue
        k = anahtar[r[0]]
        deger = str(r[j]).strip() if r[j] is not None else ""
        s = sonuc[k["grup"]]
        if not deger:
            s[3] += 1
            continue
        bulunan = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", deger)  # "Yıl 2012 Cilt: 4" de olur
        if not bulunan:
            s[2] += 1
            continue
        gercek = int(bulunan.group())
        if k["grup"] == "A" and k["kayit_yili"] is None:
            s[2] += 1  # kayitta yil yok: olcut uygulanamaz (makale zaten yilsiz, analiz disi)
            continue
        if k["grup"] == "A":
            dogru = k["kayit_yili"] is not None and gercek < k["kayit_yili"]
        else:
            dogru = gercek == k["yil_guvenilir"]
        s[0 if dogru else 1] += 1
        if not dogru:
            yanlislar.append((r[0], k["grup"], gercek, k["kayit_yili"], k["yil_guvenilir"], k["url"]))
    adlar = {"A": "A) arsiv kurali (gercek yil < kayittaki yil)", "B": "B) analizdeki yil (gercek = kullanilan)"}
    for g in ("A", "B"):
        d, y, s, b = sonuc[g]
        n = d + y
        alt, ust = wilson(d, n)
        print(f"{adlar[g]}: {d}/{n} dogru" + (f" = %{100 * d / n:.1f} (%95 Wilson {100 * alt:.1f}-{100 * ust:.1f})" if n else "")
              + f"; degerlendirilemeyen ('?' ya da kayitta yil yok) {s}, bos {b}")
    if yanlislar:
        print("\nYanlislar (no, grup, gercek, kayittaki yil, kullanilan yil, url):")
        for y in yanlislar:
            print("  ", *y)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    e = alt.add_parser("excel")
    e.add_argument("--uzerine-yaz", action="store_true")
    alt.add_parser("hesapla")
    g = alt.add_parser("gir")
    g.add_argument("--no", type=int, nargs="+", help="yalnizca bu satirlari yeniden gir (orn. --no 42)")
    arg = p.parse_args()
    {"excel": excel, "gir": gir, "hesapla": hesapla}[arg.komut](arg)


if __name__ == "__main__":
    main()
