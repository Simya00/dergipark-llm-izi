#!/usr/bin/env python3
"""
Kilavuz Kontrol Seti: Kobak vd. Etiketleriyle Sinama (on kayit: yontem.md §6.3)
==============================================================================
Kappa yalnizca iki isaretleyicinin tutarliligini olcer. Bu set, kilavuzun Kobak
vd.'nin "style / content" ayrimina ne kadar yakin oldugunu olcer.

  excel   : 30 style + 30 content Kobak kelimesi (tohum 20261128; dislama listesi
            disinda), her biri icin DergiPark INGILIZCE ozetlerinden 2 rastgele cumle.
            2 cumle bulunamazsa ayni turden siradaki kelimeye gecilir. Kor: etiket yok.
            -> kobak_kontrol.xlsx (bos form) + kobak_kontrol_anahtar.json
  hesapla : doldurulmus Excel(ler)den, her isaretleyici icin:
            (1) style -> Ü orani, (2) content -> YANLISLIKLA Ü orani (asil soru),
            (3) Ü/İ ikilisi uzerinden Kobak ile Cohen kappa; Wilson %95.
            Esikler (on kayit): content -> Ü en fazla %30; kappa >= 0,6.

Kullanim (analiz/ klasorunde):
  python3 kobak_kontrol.py excel
  python3 kobak_kontrol.py hesapla kobak_kontrol_kullanici.xlsx [kobak_kontrol_hoca.xlsx]
"""

import argparse
import csv
import json
import math
import random
from pathlib import Path

from isaretleme import CUMLE, isaretle, kisalt
from kelime_siklik import VARSAYILAN_GIRDI, analize_girer, kelime_listesi

KLASOR = Path(__file__).resolve().parent
KOBAK = KLASOR / "kaynaklar" / "kobak_excess_words.csv"
DISLAMA = KLASOR / "kaynaklar" / "kobak_kontrol_dislama.txt"
KILAVUZ_KAYNAK = KLASOR / "isaretleme_kayit" / "isaretleme_tr_govde_ikinci_bos.xlsx"
EXCEL = KLASOR / "kobak_kontrol.xlsx"
ANAHTAR = KLASOR / "kobak_kontrol_anahtar.json"
TOHUM, N_TUR, ORNEK = 20261128, 30, 2
ESIK_ICERIK_U, ESIK_KAPPA = 0.30, 0.6
ETIKET_BASLIK = "etiket (Ü/İ/B/D)"


def wilson(d, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p = d / n
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    o = (p + z * z / (2 * n)) / (1 + z * z / n)
    return o - m, o + m


def excel(arg):
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    if EXCEL.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{EXCEL} zaten var. Yeniden olusturmak icin --uzerine-yaz.")
    dislama = {s.strip() for s in DISLAMA.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")}
    kobak = {r["word"]: r["type"] for r in csv.DictReader(open(KOBAK, encoding="utf-8"))}
    rng = random.Random(TOHUM)
    sira = {}
    for tur in ("style", "content"):
        aday = sorted(w for w, t in kobak.items() if t == tur and w not in dislama)
        rng.shuffle(aday)
        sira[tur] = aday
    adaylar = set(sira["style"]) | set(sira["content"])

    # Her aday kelime icin Ingilizce ozetlerden rezervuar ornekleme (ayni cumle iki kez yok)
    secilmis, gorulen = {w: [] for w in adaylar}, dict.fromkeys(adaylar, 0)
    with open(VARSAYILAN_GIRDI, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            if not m.get("yil_guvenilir") or not analize_girer(m, "ozet_en", None):
                continue
            for cumle in CUMLE.split(m["ozet_en"]):
                for w in set(kelime_listesi(cumle, "en")) & adaylar:
                    if any(cumle == c for c in secilmis[w]):
                        continue
                    gorulen[w] += 1
                    if len(secilmis[w]) < ORNEK:
                        secilmis[w].append(cumle)
                    elif (j := rng.randrange(gorulen[w])) < ORNEK:
                        secilmis[w][j] = cumle

    secilen, atlanan = [], {"style": [], "content": []}
    for tur in ("style", "content"):
        n = 0
        for w in sira[tur]:
            if n == N_TUR:
                break
            if len(secilmis[w]) < ORNEK:
                atlanan[tur].append(w)  # on kayit: 2 cumle yoksa siradakine gec
                continue
            secilen.append({"kelime": w, "kobak": tur, "cumleler": secilmis[w]})
            n += 1
    rng.shuffle(secilen)

    wb = Workbook()
    k = wb.active
    k.title = "1_kilavuz"
    for r in load_workbook(KILAVUZ_KAYNAK, read_only=True)["1_kilavuz"].iter_rows(values_only=True):
        k.append([r[0]])
    for s in ["", "BU SET HAKKINDA (kontrol seti)",
              "Bu sayfadaki kilavuzun AYNISINI uygulayin. Bu sette kelimeler INGILIZCE ve tek bicimdir (govde degil); "
              "ornek cumleler DergiPark'taki Ingilizce ozetlerdendir. 60 kelime, ~20 dakika."]:
        k.append([s])
    for row in k.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    k.column_dimensions["A"].width = 140
    ws = wb.create_sheet("2_isaretleme")
    ws.append(["no", "kelime", "örnek cümle 1", "örnek cümle 2", ETIKET_BASLIK, "not"])
    for i, s in enumerate(secilen, 1):
        c = [kisalt(isaretle(x, s["kelime"], "en")) for x in s["cumleler"]]
        ws.append([i, s["kelime"], *c, "", ""])
    dv = DataValidation(type="list", formula1='"Ü,İ,B,D"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"E2:E{ws.max_row}")
    for col, w in zip("ABCDEF", (6, 18, 65, 65, 12, 30)):
        ws.column_dimensions[col].width = w
    sari = PatternFill("solid", fgColor="FFF2CC")
    for row in ws.iter_rows(min_row=2):
        for h in row[2:4]:
            h.alignment = Alignment(wrap_text=True, vertical="top")
        row[4].fill = sari
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "C2"
    wb.save(EXCEL)
    ANAHTAR.write_text(json.dumps({"tohum": TOHUM, "atlanan_2_cumle_yok": atlanan,
                                   "kelimeler": [{"no": i, "kelime": s["kelime"], "kobak": s["kobak"]}
                                                 for i, s in enumerate(secilen, 1)]},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {EXCEL} ({len(secilen)} kelime; atlanan (2 cumle yok): style {len(atlanan['style'])}, "
          f"content {len(atlanan['content'])})\n-> {ANAHTAR} (anahtar; isaretlerken ACMAYIN)")


def hesapla(arg):
    from openpyxl import load_workbook
    anahtar = {k["no"]: k for k in json.loads(ANAHTAR.read_text(encoding="utf-8"))["kelimeler"]}
    for dosya in arg.exceller:
        ws = load_workbook(dosya, read_only=True)["2_isaretleme"]
        satir = list(ws.iter_rows(values_only=True))
        j = satir[0].index(ETIKET_BASLIK)
        et = {}
        for r in satir[1:]:
            if r[0] in anahtar:
                e = str(r[j] or "").strip().upper()[:1].replace("I", "İ").replace("U", "Ü")
                et[r[0]] = e if e in ("Ü", "İ", "B", "D") else "bos"
        sty = [et[n] for n, k in anahtar.items() if k["kobak"] == "style"]
        con = [et[n] for n, k in anahtar.items() if k["kobak"] == "content"]
        su, cu = sty.count("Ü"), con.count("Ü")
        print(f"\n{Path(dosya).name}:  bos {list(et.values()).count('bos')}, B {list(et.values()).count('B')}, "
              f"D {list(et.values()).count('D')}")
        a, b = wilson(su, len(sty))
        print(f"  (1) Kobak style -> Ü:            {su}/{len(sty)} = %{100 * su / len(sty):.0f} (Wilson {100 * a:.0f}-{100 * b:.0f})")
        a, b = wilson(cu, len(con))
        oran = cu / len(con)
        print(f"  (2) Kobak content -> YANLIS Ü:   {cu}/{len(con)} = %{100 * oran:.0f} (Wilson {100 * a:.0f}-{100 * b:.0f})"
              f"  esik %{100 * ESIK_ICERIK_U:.0f} -> {'KILAVUZ FAZLA GENIS' if oran > ESIK_ICERIK_U else 'tamam'}")
        # Cohen kappa, yalnizca Ü/İ verilen kelimeler (B, D, bos haric)
        ciftler = [(k["kobak"], et[n]) for n, k in anahtar.items() if et[n] in ("Ü", "İ")]
        n = len(ciftler)
        if n:
            po = sum((t == "style") == (e == "Ü") for t, e in ciftler) / n
            ps = sum(t == "style" for t, _ in ciftler) / n
            pu = sum(e == "Ü" for _, e in ciftler) / n
            pe = ps * pu + (1 - ps) * (1 - pu)
            kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
            print(f"  (3) Kobak ile uyum (Ü/İ, n={n}): ham %{100 * po:.0f}, kappa {kappa:.2f}"
                  f"  esik {ESIK_KAPPA} -> {'YETERLI' if kappa >= ESIK_KAPPA else 'YETERSIZ'}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    e = alt.add_parser("excel")
    e.add_argument("--uzerine-yaz", action="store_true")
    h = alt.add_parser("hesapla")
    h.add_argument("exceller", nargs="+")
    arg = p.parse_args()
    excel(arg) if arg.komut == "excel" else hesapla(arg)


if __name__ == "__main__":
    main()
