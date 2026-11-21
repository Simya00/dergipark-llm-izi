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

GOVDE DUZEYI (2026-11-21; Turkce ana analiz govde duzeyinde, kullanici karari
2026-11-12): --siklik siklik_tr_govde.tsv.gz ile secim govdelerden yapilir
(vurgula, kritik, kapsamli...). Excel'de her govdenin en sik bicimleri
(govde_bicimleri_tr.json.gz; vurgulamaktadir, vurgulanmistir...) gosterilir ve
ornek cumleler bu bicimlerden HERHANGI birini iceren cumlelerden secilir.
Dosya adlari: isaretleme_tr_govde.xlsx, uslup_kelimeleri_tr_govde.txt.

Kullanim:
  python3 isaretleme.py excel --dil tr --siklik siklik_tr_govde.tsv.gz
  python3 isaretleme.py hesapla --dil tr --siklik siklik_tr_govde.tsv.gz
  python3 isaretleme.py excel --dil tr            (bicim duzeyi, eski)
"""

import argparse
import gzip
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from asiri_kullanim import KLASOR, asiri_hesapla, harf_filtresi_gerekli, oku
from kelime_siklik import (VARSAYILAN_GIRDI, analize_girer, kelime_listesi, siklik_dosya_adi,
                           turkce_kucult, yil_araligi)

TOHUM = 20261112
FARK_ESIGI = 0.01       # delta > 0.01 (Kobak vd. kuralinin "buyuk fark" kolu)
ORNEK_SAYISI = 2
CUMLE = re.compile(r"(?<=[.!?])\s+")  # basit cumle bolme
ETIKETLER = ("Ü", "İ", "B")
BICIM_GOSTER = 5        # Excel'de govdenin yaninda gosterilen en sik bicim sayisi
ETIKET_BASLIK = "etiket (Ü/İ/B)"


def siklik_yolu(arg):
    if not arg.siklik:
        return KLASOR / siklik_dosya_adi(arg.dil, 1)
    yol = Path(arg.siklik)
    return yol if yol.is_absolute() or yol.exists() else KLASOR / yol


def ad(arg):
    """siklik_tr_govde.tsv.gz -> tr_govde; --siklik yoksa dil (eski dosya adlari korunur)."""
    return siklik_yolu(arg).name.replace("siklik_", "").replace(".tsv.gz", "") if arg.siklik else arg.dil


def excel_dosyasi(arg):
    return KLASOR / f"isaretleme_{ad(arg)}.xlsx"


def bicimler_oku(arg):
    """govde -> [(bicim, sayi), ...] en sikdan baslayarak; govde duzeyi degilse bos.
    govde_bicimleri dosyasi yalnizca govdeden FARKLI bicimleri tutar; govdenin kendisi
    (kritik, kapsamli) ayrica eklenir (bkz. ornekler)."""
    if "_govde" not in ad(arg):
        return {}
    with gzip.open(KLASOR / f"govde_bicimleri_{arg.dil}.json.gz", "rt", encoding="utf-8") as f:
        d = json.load(f)
    return {g: sorted(c.items(), key=lambda x: -x[1]) for g, c in d.items()}


# ------------------------------------------------------------------
# 1) Secim ve Excel
# ------------------------------------------------------------------

def secim(siklik_dosyasi, yillar):
    """kelime -> {yil: (delta, oran, p, q, sayi)} ; yalnizca delta > esik olan bir yili olanlar."""
    belge, sayi = oku(siklik_dosyasi)
    harf = harf_filtresi_gerekli(siklik_dosyasi)
    bilgi = defaultdict(dict)
    for T in yillar:
        if not all(belge.get(y) for y in (T - 3, T - 2, T - 1, T)):
            continue
        for r in asiri_hesapla(belge, sayi, T - 2, T, harf_filtresi=harf):
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


def ornekler(dil, secilen, bicimler=None):
    """Her kelime icin, ASIRI ciktigi yillarin ozetlerinden rastgele ORNEK_SAYISI cumle.
    Rezervuar ornekleme: dosya bir kez okunur, her kelime icin esit olasilikla secilir.
    Govde duzeyinde (bicimler verilirse) cumlede govdenin kendisi YA DA en sik bicimlerinden
    biri gecmeli; kayitta eslesen bicim de tutulur (Excel'de o bicim isaretlenir)."""
    rng = random.Random(TOHUM)
    gorulen = Counter()
    secilmis = defaultdict(list)
    alan = f"ozet_{dil}"
    yil_kelime = defaultdict(set)  # yil -> o yil asiri olan secili kelimeler
    for k, v in secilen.items():
        for y in v:
            yil_kelime[y].add(k)
    bicim_oge = defaultdict(set)  # metindeki bicim -> secili oge(ler); bicim duzeyinde kelimenin kendisi
    for k in secilen:
        bicim_oge[k].add(k)
        for b, _ in (bicimler or {}).get(k, [])[:10]:
            bicim_oge[b].add(k)
    with open(VARSAYILAN_GIRDI, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in yil_kelime or not analize_girer(m, alan, None):
                continue
            aranan = yil_kelime[y]
            for cumle in CUMLE.split(m[alan]):
                eslesen = {}  # oge -> cumlede bulunan ilk bicimi
                for b in kelime_listesi(cumle, dil):
                    for k in bicim_oge.get(b, ()):
                        if k in aranan:
                            eslesen.setdefault(k, b)
                for k, b in eslesen.items():
                    if any(cumle == s[2] for s in secilmis[k]):
                        continue  # ayni cumle (kalip cumle, tekrar eden ozet) iki kez gosterilmesin
                    gorulen[k] += 1
                    kayit = (y, m.get("dergi_kodu"), cumle, b)
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

    yol = excel_dosyasi(arg)
    if yol.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{yol} zaten var (isaretleriniz olabilir). Yeniden olusturmak icin --uzerine-yaz.")
    yillar = yil_araligi(arg.yillar)
    print(f"Sayim dosyasi: {siklik_yolu(arg).name}")
    secilen = secim(siklik_yolu(arg), yillar)
    print(f"{len(secilen)} oge secildi (2018-2025'ten birinde asiri ve delta > {FARK_ESIGI}).")
    bicimler = bicimler_oku(arg)
    orn = ornekler(arg.dil, secilen, bicimler)
    kelimeler = sorted(secilen)
    random.Random(TOHUM).shuffle(kelimeler)  # rastgele sira: yila/buyukluge gore siralama yanliligi olmasin

    wb = Workbook()
    ws = wb.active
    ws.title = "isaretleme"
    ws.append(["no", "kelime (gövde)" if bicimler else "kelime", "en sık biçimler",
               "ornek cumle 1", "ornek cumle 2", ETIKET_BASLIK, "not"])
    for i, k in enumerate(kelimeler, 1):
        c = [kisalt(isaretle(cumle, b, arg.dil)) for _, _, cumle, b in orn.get(k, [])]
        formlar = ", ".join(b for b, _ in bicimler.get(k, [])[:BICIM_GOSTER])
        ws.append([i, k, formlar, *(c + ["", ""])[:2], "", ""])
    dv = DataValidation(type="list", formula1='"' + ",".join(ETIKETLER) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"F2:F{ws.max_row}")
    for sutun, gen in zip("ABCDEFG", (6, 18, 30, 65, 65, 14, 30)):
        ws.column_dimensions[sutun].width = gen
    for satir in ws.iter_rows(min_row=2):
        for h in satir[2:5]:
            h.alignment = Alignment(wrap_text=True, vertical="top")
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "D2"

    b = wb.create_sheet("bilgi")  # yillar burada: isaretlerken bakmamaniz onerilir
    b.append(["no", "kelime", "asiri yillar", "delta>0.01 yillar", "en buyuk delta (puan)", "en buyuk oran",
              *[f"delta {y}" for y in yillar], "ornek yil/dergi"])
    for i, k in enumerate(kelimeler, 1):
        v = secilen[k]
        b.append([i, k, ",".join(map(str, sorted(v))),
                  ",".join(str(y) for y in sorted(v) if v[y][0] > FARK_ESIGI),
                  round(100 * max(d for d, *_ in v.values()), 2), round(max(o for _, o, *_ in v.values()), 2),
                  *[round(100 * v[y][0], 2) if y in v else None for y in yillar],
                  "; ".join(f"{y}/{d}" for y, d, *_ in orn.get(k, []))])
    a = wb.create_sheet("aciklama")
    for s in [
        "Her kelimeye bir etiket verin (F sutunu, acilir liste):",
        "Ü = USLUP: yazim tarzi kelimesi; konudan bagimsiz, her alanda kullanilabilir "
        "(kapsamli, vurgulamaktadir, kritik, ayrica, temel).",
        "İ = ICERIK: bir konuya, olaya, yonteme ozgu (deprem, covid, yapay, gazze, veri, kultürel).",
        "B = BELIRSIZ: ikisi de olabilir ya da karar veremediniz.",
        "Kelimenin hangi yilda arttigina bakmadan karar verin ('bilgi' sayfasi sonra).",
        "Ornek cumleler kelimenin ASIRI ciktigi yillardan rastgele secildi; kelime ⟦ ⟧ icinde.",
        "Govde duzeyinde: 'en sik bicimler' govdenin metinde en cok gectigi halleridir; ornek "
        "cumlede bunlardan biri isaretlidir. Karar govde icin verilir (tum bicimleri birlikte).",
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
    wb = load_workbook(excel_dosyasi(arg))
    etiket = {}
    sutun = [h.value for h in wb["isaretleme"][1]].index(ETIKET_BASLIK)  # bicim/govde Excel'inde farkli
    for r in wb["isaretleme"].iter_rows(min_row=2, values_only=True):
        if r[1]:
            e = str(r[sutun] or "").strip().upper()[:1].replace("I", "İ").replace("U", "Ü")
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
    cikti = KLASOR / f"uslup_kelimeleri_{ad(arg)}.txt"
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
    e.add_argument("--siklik", help="orn. siklik_tr_govde.tsv.gz (govde duzeyi); yoksa bicim duzeyi")
    h = alt.add_parser("hesapla")
    h.add_argument("--dil", choices=["tr", "en"], required=True)
    h.add_argument("--siklik", help="excel'de kullanilanla ayni")
    arg = p.parse_args()
    excel(arg) if arg.komut == "excel" else hesapla(arg)


if __name__ == "__main__":
    main()
