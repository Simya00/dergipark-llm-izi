#!/usr/bin/env python3
"""
Asiri Kelimelerin Elle Isaretlenmesi: Icerik mi, Uslup mu? (Kobak vd. gibi)
===========================================================================
Kobak vd. her yilin asiri kelimelerini elle "icerik" (konu: covid, deprem) ya
da "uslup" (yazim tarzi: kapsamli, vurgulamaktadir) diye isaretledi. Ana
bulgulari: LLM oncesi yillarda asiri kelimeler hep icerik kelimeleriydi,
2024'te ilk kez uslup kelimeleri cogunlukta.

1) excel   : Isaretlenecek kelimeleri secer ve Excel'e yazar.
             SECIM: 2018-2025'ten herhangi birinde Kobak kuralina gore asiri VE
             farki (delta) 0.01'den buyuk olan kelimeler (Claude'un onerisi,
             kullanici onayi 2026-11-12). Her hedef yil T icin taban T-2.
             Her kelime icin, kelimenin ASIRI ciktigi yillardaki ozetlerden
             rastgele 2 ornek cumle (sabit tohum: ayni komut ayni ornekleri verir).
             KOR ISARETLEME: "isaretleme" sayfasinda yalnizca kelime ve ornek
             cumleler var; hangi yilda arttigi ayri sayfada ("bilgi"). Boylece
             "2024'te artmis, demek ki uslup" diye yanlilik olmaz. Sira rastgele.
2) hesapla : Isaretli Excel'den her yil icin Ü / İ / B sayilarini hesaplar ve
             uslup kelimelerini uslup_kelimeleri_<dil>.txt'ye yazar (alt sinir
             hesabi icin, alt_sinir.py --isaretciler).

Etiketler:  Ü = uslup (yazim tarzi; konu degisse de kullanilabilir)
            İ = icerik (bir konuya, olaya, yonteme ozgu)
            B = belirsiz (ikisi de olabilir / karar verilemedi)

Kullanim:
  python3 isaretleme.py excel --dil tr
  python3 isaretleme.py hesapla --dil tr
"""

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from asiri_kullanim import KLASOR, asiri_hesapla, oku
from kelime_siklik import (VARSAYILAN_GIRDI, analize_girer, kelime_listesi, siklik_dosya_adi,
                           turkce_kucult, yil_araligi)

TOHUM = 20261112
FARK_ESIGI = 0.01       # delta > 0.01 (Kobak vd. kuralinin "buyuk fark" kolu)
ORNEK_SAYISI = 2
CUMLE = re.compile(r"(?<=[.!?])\s+")  # basit cumle bolme
ETIKETLER = ("Ü", "İ", "B")


def excel_dosyasi(dil):
    return KLASOR / f"isaretleme_{dil}.xlsx"


# ------------------------------------------------------------------
# 1) Secim ve Excel
# ------------------------------------------------------------------

def secim(dil, yillar):
    """kelime -> {yil: (delta, oran, p, q, sayi)} ; yalnizca delta > esik olan bir yili olanlar."""
    belge, sayi = oku(KLASOR / siklik_dosya_adi(dil, 1))
    bilgi = defaultdict(dict)
    for T in yillar:
        if not all(belge.get(y) for y in (T - 3, T - 2, T - 1, T)):
            continue
        for r in asiri_hesapla(belge, sayi, T - 2, T):
            if r["asiri"]:
                bilgi[r["kelime"]][T] = (r["delta"], r["oran"], r["p"], r["q"], r["sayi"])
    return {k: v for k, v in bilgi.items() if any(d > FARK_ESIGI for d, *_ in v.values())}


def isaretle(cumle, kelime, dil):
    """Cumlede kelimeyi ⟦ ⟧ icine alir (kucuk harfe cevrilmis kopyada arar; uzunluk korunur)."""
    kucuk = turkce_kucult(cumle) if dil == "tr" else cumle.lower()
    if len(kucuk) == len(cumle):
        m = re.search(r"(?<!\w)" + re.escape(kelime) + r"(?!\w)", kucuk)
        if m:
            return cumle[:m.start()] + "⟦" + cumle[m.start():m.end()] + "⟧" + cumle[m.end():]
    return cumle  # bulunamadi (or. birlesik onarimiyla bolunmus kelime): isaretsiz


def kisalt(cumle, en_fazla=350):
    if len(cumle) <= en_fazla:
        return cumle
    i = max(cumle.find("⟦"), 0)
    bas = max(0, i - en_fazla // 2)
    return ("…" if bas else "") + cumle[bas:bas + en_fazla] + "…"


def ornekler(dil, secilen):
    """Her kelime icin, ASIRI ciktigi yillarin ozetlerinden rastgele ORNEK_SAYISI cumle.
    Rezervuar ornekleme: dosya bir kez okunur, her kelime icin esit olasilikla secilir."""
    rng = random.Random(TOHUM)
    gorulen = Counter()
    secilmis = defaultdict(list)
    alan = f"ozet_{dil}"
    yil_kelime = defaultdict(set)  # yil -> o yil asiri olan secili kelimeler
    for k, v in secilen.items():
        for y in v:
            yil_kelime[y].add(k)
    with open(VARSAYILAN_GIRDI, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in yil_kelime or not analize_girer(m, alan, None):
                continue
            aranan = yil_kelime[y]
            for cumle in CUMLE.split(m[alan]):
                for k in set(kelime_listesi(cumle, dil)) & aranan:
                    gorulen[k] += 1
                    kayit = (y, m.get("dergi_kodu"), cumle)
                    if len(secilmis[k]) < ORNEK_SAYISI:
                        secilmis[k].append(kayit)
                    else:
                        j = rng.randrange(gorulen[k])
                        if j < ORNEK_SAYISI:
                            secilmis[k][j] = kayit
    return secilmis


def excel(arg):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation

    yol = excel_dosyasi(arg.dil)
    if yol.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{yol} zaten var (isaretleriniz olabilir). Yeniden olusturmak icin --uzerine-yaz.")
    yillar = yil_araligi(arg.yillar)
    secilen = secim(arg.dil, yillar)
    print(f"{len(secilen)} kelime secildi (2018-2025'ten birinde asiri ve delta > {FARK_ESIGI}).")
    orn = ornekler(arg.dil, secilen)
    kelimeler = sorted(secilen)
    random.Random(TOHUM).shuffle(kelimeler)  # rastgele sira: yila/buyukluge gore siralama yanliligi olmasin

    wb = Workbook()
    ws = wb.active
    ws.title = "isaretleme"
    ws.append(["no", "kelime", "ornek cumle 1", "ornek cumle 2", "etiket (Ü/İ/B)", "not"])
    for i, k in enumerate(kelimeler, 1):
        c = [kisalt(isaretle(cumle, k, arg.dil)) for _, _, cumle in orn.get(k, [])]
        ws.append([i, k, *(c + ["", ""])[:2], "", ""])
    dv = DataValidation(type="list", formula1='"' + ",".join(ETIKETLER) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"E2:E{ws.max_row}")
    for sutun, gen in zip("ABCDEF", (6, 22, 70, 70, 14, 30)):
        ws.column_dimensions[sutun].width = gen
    for satir in ws.iter_rows(min_row=2):
        for h in satir[2:4]:
            h.alignment = Alignment(wrap_text=True, vertical="top")
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "C2"

    b = wb.create_sheet("bilgi")  # yillar burada: isaretlerken bakmamaniz onerilir
    b.append(["no", "kelime", "asiri yillar", "delta>0.01 yillar", "en buyuk delta (puan)", "en buyuk oran",
              *[f"delta {y}" for y in yillar], "ornek yil/dergi"])
    for i, k in enumerate(kelimeler, 1):
        v = secilen[k]
        b.append([i, k, ",".join(map(str, sorted(v))),
                  ",".join(str(y) for y in sorted(v) if v[y][0] > FARK_ESIGI),
                  round(100 * max(d for d, *_ in v.values()), 2), round(max(o for _, o, *_ in v.values()), 2),
                  *[round(100 * v[y][0], 2) if y in v else None for y in yillar],
                  "; ".join(f"{y}/{d}" for y, d, _ in orn.get(k, []))])
    a = wb.create_sheet("aciklama")
    for s in [
        "Her kelimeye bir etiket verin (E sutunu, acilir liste):",
        "Ü = USLUP: yazim tarzi kelimesi; konudan bagimsiz, her alanda kullanilabilir "
        "(kapsamli, vurgulamaktadir, kritik, ayrica, temel).",
        "İ = ICERIK: bir konuya, olaya, yonteme ozgu (deprem, covid, yapay, gazze, veri, kultürel).",
        "B = BELIRSIZ: ikisi de olabilir ya da karar veremediniz.",
        "Kelimenin hangi yilda arttigina bakmadan karar verin ('bilgi' sayfasi sonra).",
        "Ornek cumleler kelimenin ASIRI ciktigi yillardan rastgele secildi; kelime ⟦ ⟧ icinde.",
    ]:
        a.append([s])
    a.column_dimensions["A"].width = 120
    wb.save(yol)
    print(f"-> {yol}  ({len(kelimeler)} satir; ornegi olmayan: {sum(1 for k in kelimeler if not orn.get(k))})")


# ------------------------------------------------------------------
# 2) Hesapla
# ------------------------------------------------------------------

def hesapla(arg):
    from openpyxl import load_workbook
    wb = load_workbook(excel_dosyasi(arg.dil))
    etiket = {}
    for r in wb["isaretleme"].iter_rows(min_row=2, values_only=True):
        if r[1]:
            e = str(r[4] or "").strip().upper()[:1].replace("I", "İ").replace("U", "Ü")
            etiket[r[1]] = e if e in ETIKETLER else "bos"
    bilgi = {r[1]: r for r in wb["bilgi"].iter_rows(min_row=2, values_only=True) if r[1]}
    baslik = [h.value for h in wb["bilgi"][1]]
    yil_sutun = {int(h.split()[1]): i for i, h in enumerate(baslik) if h and h.startswith("delta ")}

    print(f"Toplam: {Counter(etiket.values())}\n")
    print("Her yil, farki (delta) 0.01'den buyuk asiri kelimelerin etiketleri:")
    print(f"{'yil':>5} {'toplam':>7} {'Ü uslup':>8} {'İ icerik':>9} {'B':>4} {'bos':>4} {'uslup %':>8}")
    for y, i in sorted(yil_sutun.items()):
        c = Counter(etiket[k] for k, r in bilgi.items() if r[i] is not None and r[i] > 100 * FARK_ESIGI)
        n = sum(c.values())
        isaretli = c["Ü"] + c["İ"]
        print(f"{y:>5} {n:>7} {c['Ü']:>8} {c['İ']:>9} {c['B']:>4} {c['bos']:>4} "
              f"{(100 * c['Ü'] / isaretli if isaretli else 0):>7.0f}%")
    uslup = sorted(k for k, e in etiket.items() if e == "Ü")
    cikti = KLASOR / f"uslup_kelimeleri_{arg.dil}.txt"
    cikti.write_text("# isaretleme.py hesapla ciktisi: kullanici Ü (uslup) dedi\n" + "\n".join(uslup) + "\n",
                     encoding="utf-8")
    print(f"\n{len(uslup)} uslup kelimesi -> {cikti}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    e = alt.add_parser("excel")
    e.add_argument("--dil", choices=["tr", "en"], required=True)
    e.add_argument("--yillar", default="2018-2025")
    e.add_argument("--uzerine-yaz", action="store_true")
    h = alt.add_parser("hesapla")
    h.add_argument("--dil", choices=["tr", "en"], required=True)
    arg = p.parse_args()
    excel(arg) if arg.komut == "excel" else hesapla(arg)


if __name__ == "__main__":
    main()
