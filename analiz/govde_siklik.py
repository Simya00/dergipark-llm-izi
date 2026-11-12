#!/usr/bin/env python3
"""
Turkce Kelime (Govde) ve Ek Sikliklari: Zemberek, Cumle Icinde Cozumleme
========================================================================
2026-11-12 kullanici kararlari (notlar/yontem.md):
  - Turkce ANA analiz kelime (govde) duzeyinde: "etkiler", "etkilerini",
    "etkisini" -> etki. Bicimler "kullanilan varyasyonlar" olarak saklanir.
  - Govde = kok + YAPIM ekleri (kapsam != kapsamli, deger -> degerlendir).
    EDILGEN (-Il/-In) ve FIILIMSILER (-ArAk, -An, -mA, -mAk, -DIk, ...) ve
    ek-fiil/yardimci fiil turleri ATILIR: vurgulamaktadir, vurgulayarak,
    vurgulanmaktadir -> vurgula. Ilk ATILAN ekte durulur (sonrasi kullanim).
  - Zemberek CUMLE ICINDE cozumler (analyze_and_disambiguate): "sonuclar"
    -> sonuc (isim), tek basina bakinca "sonuclamak" (fiil) cikiyordu.
  - Ayni geciste ekler de sayilir: (1) tek tek ekler (Prog2, Pass, Cop ...),
    (2) son ek zinciri (vurgulamaktadir -> Prog2+A3sg+Cop = -mAktAdIr).

Metin, ana analizdeki kurallarla kelimelere ayrilir (kelime_siklik.kelime_listesi:
kucuk harf, kesme sonrasi ek atilir, onayli birlesik kelimeler bolunur, tek
harfliler atilir); cumle sinirlari korunur. Zemberek'in tanimadigi kelimeler
(covid, chatgpt) oldugu gibi sayilir; yillara gore taninmayan orani raporlanir.

Ciktilar (kelime_siklik.py ile ayni bicim; asiri_kullanim.py --siklik ile calisir):
  siklik_tr_govde.tsv.gz       (+ .belge.json)
  siklik_tr_ek.tsv.gz          (+ .belge.json)
  siklik_tr_ekzinciri.tsv.gz   (+ .belge.json)
  govde_bicimleri_tr.json.gz   govde -> en sik bicimleri (Excel'de gosterilir)

MAKALE BASINA SONUC (2026-11-12, kullanici karari): her parca dosyasi her makale
icin [yil, dergi_kodu, govdeler, ekler, zincirler] saklar. Boylece dergi
panelleri ve alt gruplar Zemberek'i yeniden calistirmadan, dakikalar icinde
hesaplanir:
  python3 govde_siklik.py birlestir --dergiler dergi_paneli_tr_kisa.txt --ad-eki panel_kisa
  -> siklik_tr_govde_panel_kisa.tsv.gz, siklik_tr_ek_panel_kisa.tsv.gz, ...

HIZ: cumle icinde cozumleme yavas (~10 ms/kelime). Is parcalara (--parca-boyu
ozet) bolunur, --isci kadar islemde paralel calisir; her biten parca
govde_parcalar/ klasorune yazilir. Kesilirse ayni komutla KALDIGI YERDEN devam
eder. Ekran karti kullanilmaz (Zemberek saf Python, islemci ile calisir).

Kullanim (Zemberek ortami gerekir):
  zemberek_env/bin/python3 govde_siklik.py sayim --isci 10 --sinir 1000   # sure denemesi
  zemberek_env/bin/python3 govde_siklik.py sayim --isci 10                # tamami
  python3 govde_siklik.py birlestir --dergiler dergi_paneli_tr_kisa.txt --ad-eki panel_kisa
  zemberek_env/bin/python3 govde_siklik.py ornek                          # 73'luk dogrulama ornegi (JSON)
  python3 govde_siklik.py excel                                           # ornegi Excel'e (normal python)
  python3 govde_siklik.py hesapla                                         # isaretli Excel'den dogruluk
"""

import argparse
import gzip
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from kelime_siklik import (VARSAYILAN_GIRDI, analize_girer, dergi_filtresi, kelime_listesi,
                           yil_araligi)

KLASOR = Path(__file__).resolve().parent
PARCA_KLASORU = KLASOR / "govde_parcalar"
CUMLE = re.compile(r"(?<=[.!?;:])\s+|\n+")

# Govdeden ATILAN (ilk gorulende durulur) Zemberek ekleri: edilgen, fiilimsiler,
# ek-fiil (Zero), -ki (Rel), yeterlik ve birlesik fiil turleri.
ATILAN = {
    "Pass",
    "Inf1", "Inf2", "Inf3", "PresPart", "PastPart", "FutPart", "NarrPart", "AorPart",
    "ByDoingSo", "While", "AfterDoingSo", "When", "SinceDoingSo", "WithoutHavingDoneSo",
    "AsLongAs", "AsIf", "WithoutBeingAbleToHaveDoneSo", "NotState", "ActOf", "FeelLike",
    "Zero", "Rel", "Able", "Unable", "Hastily", "EverSince", "Repeat", "Almost", "Start",
    "Stay", "Adamantly",
}
# Yumusamis son unsuz (degisikliG-in) yalin bicime: degisikliğ -> degisiklik
YUMUSAMA = {"ğ": "k", "b": "p", "c": "ç"}

TOHUM = 20261112
SURUM = 2  # parca dosyasi bicimi (2: makale basina sonuc); eski parcalarla karistirilmasin
ORNEK_SAYISI = 73


# ------------------------------------------------------------------
# Tek bir cozumlemeden govde, ekler, zincir
# ------------------------------------------------------------------

def govde_ve_ekler(analiz, kelime):
    """(govde, ek kimlikleri listesi, son zincir) ; taninmayan kelimede (kelime, [], "")."""
    if analiz.is_unknown():
        return kelime, [], ""
    md = analiz.morpheme_data_list
    govde = analiz.item.root
    durdu = False
    son_yapim = ""
    for d in md[1:]:
        m = d.morpheme
        if m.pos is not None:          # Noun/Verb/Adj gibi tur isaretleri (bos ek)
            continue
        if m.derivational_ and not durdu:
            if m.id_ in ATILAN:
                durdu = True
            else:
                govde += d.surface
                son_yapim = d.surface
    if son_yapim and govde[-1] in YUMUSAMA:
        govde = govde[:-1] + YUMUSAMA[govde[-1]]
    ekler = [d.morpheme.id_ for d in md[1:] if d.morpheme.pos is None]
    # son zincir: son yapim ekinden sonraki cekim ekleri (yoksa son yapim eki)
    son = []
    for d in md[1:]:
        m = d.morpheme
        if m.pos is not None:
            continue
        son = [m.id_] if m.derivational_ else son + [m.id_]
    return govde, ekler, "+".join(son)


def cumle_coz(morfoloji, kelimeler):
    """Cumle icinde cozumleme; Zemberek kelimeleri farkli bolerse (nadir) kelime kelime ilk cozumleme."""
    sonuc = morfoloji.analyze_and_disambiguate(" ".join(kelimeler)).best_analysis()
    if len(sonuc) == len(kelimeler):
        return sonuc
    tek = []
    for k in kelimeler:
        r = morfoloji.analyze(k).analysis_results
        tek.append(r[0] if r else morfoloji.analyze_and_disambiguate(k).best_analysis()[0])
    return tek


def ozet_coz(morfoloji, metin):
    """Ozet -> (govde kumesi, ek kumesi, zincir kumesi, [(bicim, govde)], kelime sayisi, taninmayan)."""
    govdeler, ekler, zincirler, ciftler = set(), set(), set(), []
    n = taninmayan = 0
    for cumle in CUMLE.split(metin):
        kelimeler = kelime_listesi(cumle, "tr")
        if not kelimeler:
            continue
        sonuc = cumle_coz(morfoloji, kelimeler)
        for kelime, a in zip(kelimeler, sonuc):
            g, e, z = govde_ve_ekler(a, kelime)
            n += 1
            taninmayan += a.is_unknown()
            govdeler.add(g)
            ekler.update(e)
            if z:
                zincirler.add(z)
            ciftler.append((kelime, g))
    return govdeler, ekler, zincirler, ciftler, n, taninmayan


# ------------------------------------------------------------------
# Paralel sayim
# ------------------------------------------------------------------

_MORFOLOJI = None


def _isci_baslat():
    global _MORFOLOJI
    import logging
    logging.disable(logging.INFO)
    from zemberek import TurkishMorphology
    _MORFOLOJI = TurkishMorphology.create_with_defaults()


def _parca_isle(is_):
    """Bir parca ozeti isler, sonucu govde_parcalar/<no>.json.gz'ye yazar."""
    no, ozetler = is_
    makaleler = []
    kelime, taninmayan = Counter(), Counter()
    bicim = defaultdict(Counter)
    for yil, dergi, metin in ozetler:
        g, e, z, ciftler, n, t = ozet_coz(_MORFOLOJI, metin)
        kelime[yil] += n
        taninmayan[yil] += t
        makaleler.append([yil, dergi, sorted(g), sorted(e), sorted(z)])
        for b, gv in ciftler:
            if b != gv:
                bicim[gv][b] += 1
    gecici = PARCA_KLASORU / f"{no:06d}.json.gz.gecici"
    with gzip.open(gecici, "wt", encoding="utf-8") as f:
        json.dump({"surum": SURUM, "kelime": kelime, "taninmayan": taninmayan, "bicim": bicim,
                   "makaleler": makaleler}, f, ensure_ascii=False)
    gecici.rename(PARCA_KLASORU / f"{no:06d}.json.gz")  # yarim parca kalmasin
    return no, len(ozetler)


def parcalar(arg):
    """Girdiyi sabit sirada okuyup (parca no, [(yil, metin)]) uretir."""
    yillar = set(yil_araligi(arg.yillar))
    dergiler = dergi_filtresi(arg.dergiler)
    paket, no, toplam = [], 0, 0
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in yillar or not analize_girer(m, "ozet_tr", dergiler):
                continue
            paket.append((y, m.get("dergi_kodu"), m["ozet_tr"]))
            toplam += 1
            if len(paket) == arg.parca_boyu or (arg.sinir and toplam >= arg.sinir):
                yield no, paket
                paket, no = [], no + 1
                if arg.sinir and toplam >= arg.sinir:
                    return
    if paket:
        yield no, paket


def sayim(arg):
    import multiprocessing as mp
    PARCA_KLASORU.mkdir(exist_ok=True)
    ayar = {"surum": SURUM, "yillar": arg.yillar, "parca_boyu": arg.parca_boyu, "dergiler": arg.dergiler,
            "sinir": arg.sinir}
    ayar_dosyasi = PARCA_KLASORU / "ayar.json"
    if ayar_dosyasi.exists() and json.loads(ayar_dosyasi.read_text()) != ayar:
        raise SystemExit(f"{PARCA_KLASORU} baska ayarlarla baslatilmis ({ayar_dosyasi.read_text()}). "
                         "Ayni ayarlarla devam edin ya da klasoru silip yeniden baslayin.")
    ayar_dosyasi.write_text(json.dumps(ayar))
    bitmis = {int(p.name[:6]) for p in PARCA_KLASORU.glob("*.json.gz")}
    isler = ((no, p) for no, p in parcalar(arg) if no not in bitmis)
    print(f"Onceden biten parca: {len(bitmis)}. {arg.isci} isci basliyor...", flush=True)
    basla, islenen = time.time(), 0
    with mp.Pool(arg.isci, initializer=_isci_baslat) as havuz:
        for no, n in havuz.imap_unordered(_parca_isle, isler):
            islenen += n
            gecen = time.time() - basla
            print(f"  parca {no} bitti | bu calistirmada {islenen} ozet, {gecen / 60:.1f} dk, "
                  f"{islenen / gecen * 3600:.0f} ozet/saat", flush=True)
    arg.dergiler_birlestir, arg.ad_eki = None, None
    birlestir(arg)


def birlestir(arg):
    """Parca dosyalarindaki makale basina sonuclardan sayim dosyalarini yazar; --dergiler ile alt grup."""
    dergiler = dergi_filtresi(getattr(arg, "dergiler_birlestir", None))
    ad_eki = f"_{arg.ad_eki}" if getattr(arg, "ad_eki", None) else ""
    say = {k: defaultdict(Counter) for k in ("govde", "ek", "zincir")}
    belge, kelime, taninmayan = Counter(), Counter(), Counter()
    bicim = defaultdict(Counter)
    for p in sorted(PARCA_KLASORU.glob("*.json.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("surum") != SURUM:
            raise SystemExit(f"{p} eski bicimde (makale basina sonuc yok). govde_parcalar klasorunu silip "
                             "sayimi yeniden calistirin.")
        for yil, dergi, g, e, z in d["makaleler"]:
            if dergiler is not None and dergi not in dergiler:
                continue
            belge[yil] += 1
            say["govde"][yil].update(g)
            say["ek"][yil].update(e)
            say["zincir"][yil].update(z)
        if dergiler is None:  # taninmayan/bicim istatistikleri yalnizca tum veri icin
            kelime.update({int(y): v for y, v in d["kelime"].items()})
            taninmayan.update({int(y): v for y, v in d["taninmayan"].items()})
            for g, c in d["bicim"].items():
                bicim[g].update(c)
    for k, ad in (("govde", "govde"), ("ek", "ek"), ("zincir", "ekzinciri")):
        yol = KLASOR / f"siklik_tr_{ad}{ad_eki}.tsv.gz"
        with gzip.open(yol, "wt", encoding="utf-8") as f:
            f.write("yil\tkelime\tbelge_sayisi\n")
            for y in sorted(say[k]):
                for oge, adet in say[k][y].items():
                    f.write(f"{y}\t{oge}\t{adet}\n")
        Path(str(yol) + ".belge.json").write_text(json.dumps({str(y): belge[y] for y in sorted(belge)}, indent=1))
        print(f"-> {yol}")
    if dergiler is not None:
        print(f"\nAlt grup ({len(dergiler)} dergi): " + ", ".join(f"{y}:{belge[y]}" for y in sorted(belge)))
        return
    with gzip.open(KLASOR / "govde_bicimleri_tr.json.gz", "wt", encoding="utf-8") as f:
        json.dump({g: dict(c.most_common(10)) for g, c in bicim.items()}, f, ensure_ascii=False)
    print(f"\n{'yil':>5} {'ozet':>7} {'kelime':>10} {'taninmayan':>11} {'%':>6} {'farkli govde':>13}")
    for y in sorted(belge):
        print(f"{y:>5} {belge[y]:>7} {kelime[y]:>10} {taninmayan[y]:>11} "
              f"{100 * taninmayan[y] / max(kelime[y], 1):>5.1f}% {len(say['govde'][y]):>13}")


# ------------------------------------------------------------------
# Dogrulama ornegi: rastgele 73 kelime (metindeki gecis agirlikli)
# ------------------------------------------------------------------

def ornek(arg):
    _isci_baslat()
    rng = random.Random(TOHUM)
    yillar = set(yil_araligi("2018-2025"))
    adaylar = []
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            if m.get("yil_guvenilir") in yillar and analize_girer(m, "ozet_tr", None):
                adaylar.append(m["ozet_tr"])
    secilen = []
    for metin in rng.sample(adaylar, ORNEK_SAYISI):  # her ozetten 1 kelime: ozetler cesitli olsun
        cumleler = [c for c in CUMLE.split(metin) if kelime_listesi(c, "tr")]
        cumle = rng.choice(cumleler)
        kelimeler = kelime_listesi(cumle, "tr")
        sonuc = cumle_coz(_MORFOLOJI, kelimeler)
        i = rng.randrange(len(kelimeler))
        g, e, z = govde_ve_ekler(sonuc[i], kelimeler[i])
        secilen.append({"kelime": kelimeler[i], "govde": g, "ekler": "+".join(e), "zincir": z,
                        "cozumleme": sonuc[i].format_string(), "cumle": cumle})
    yol = KLASOR / "govde_dogrulama_tr.json"
    yol.write_text(json.dumps(secilen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(secilen)} ornek -> {yol}\nSimdi (normal python): python3 govde_siklik.py excel")


def excel(arg):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation
    secilen = json.loads((KLASOR / "govde_dogrulama_tr.json").read_text(encoding="utf-8"))
    yol = KLASOR / "govde_dogrulama_tr.xlsx"
    if yol.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{yol} zaten var. Yeniden olusturmak icin --uzerine-yaz.")
    wb = Workbook()
    ws = wb.active
    ws.title = "kontrol"
    ws.append(["no", "kelime (metinde)", "bulunan KELIME (govde)", "cumle", "Zemberek cozumlemesi",
               "dogru mu? (D/Y)", "not"])
    for i, s in enumerate(secilen, 1):
        cumle = re.sub(r"(?<!\w)(" + re.escape(s["kelime"]) + r")(?!\w)", r"⟦\1⟧", s["cumle"].lower(), count=1)
        ws.append([i, s["kelime"], s["govde"], cumle, s["cozumleme"], "", ""])
    dv = DataValidation(type="list", formula1='"D,Y"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"F2:F{ws.max_row}")
    for sutun, gen in zip("ABCDEFG", (5, 20, 20, 70, 45, 12, 25)):
        ws.column_dimensions[sutun].width = gen
    for satir in ws.iter_rows(min_row=2):
        satir[3].alignment = Alignment(wrap_text=True, vertical="top")
    for h in ws[1]:
        h.font = Font(bold=True)
    ws.freeze_panes = "B2"
    a = wb.create_sheet("aciklama")
    for s in ["Soru: 'bulunan KELIME (govde)' sutunu, cumledeki ⟦kelime⟧ icin dogru mu?",
              "Kural: cekim ekleri, edilgen (-il/-in) ve fiilimsiler (-arak, -en, -me, -mek, -dik...) atilir; "
              "yapim ekleri kalir.",
              "Ornek: 'vurgulanmaktadir' -> vurgula (D); 'kapsamli' -> kapsamli (D); "
              "'sonuclar' -> sonucla (Y: fiil sanilmis, dogrusu sonuc).",
              "Zemberek'in tanimadigi kelime oldugu gibi kalir (covid -> covid): bu D sayilir.",
              "Emin degilseniz bos birakip not yazin."]:
        a.append([s])
    a.column_dimensions["A"].width = 120
    wb.save(yol)
    print(f"-> {yol}")


def hesapla(arg):
    from openpyxl import load_workbook
    sayac = Counter()
    for r in load_workbook(KLASOR / "govde_dogrulama_tr.xlsx").active.iter_rows(min_row=2, values_only=True):
        c = str(r[5] or "").strip().upper()[:1]
        sayac[c if c in ("D", "Y") else "bos"] += 1
    n = sayac["D"] + sayac["Y"]
    from math import sqrt
    if n:
        p, z = sayac["D"] / n, 1.96
        m = (p + z * z / (2 * n)) / (1 + z * z / n)
        h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        print(f"D {sayac['D']}  Y {sayac['Y']}  bos {sayac['bos']}  ->  %{100 * p:.1f} "
              f"(%95 Wilson {100 * (m - h):.1f}–{100 * (m + h):.1f})")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    s = alt.add_parser("sayim")
    s.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    s.add_argument("--yillar", default="2015-2026")
    s.add_argument("--isci", type=int, default=10)
    s.add_argument("--parca-boyu", type=int, default=500, help="bir parcadaki ozet sayisi")
    s.add_argument("--sinir", type=int, help="yalnizca ilk N ozet (sure denemesi)")
    s.add_argument("--dergiler")
    o = alt.add_parser("ornek")
    o.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    e = alt.add_parser("excel")
    e.add_argument("--uzerine-yaz", action="store_true")
    alt.add_parser("hesapla")
    b = alt.add_parser("birlestir")
    b.add_argument("--dergiler", dest="dergiler_birlestir", help="yalnizca bu dergiler (dergi_paneli_*.txt)")
    b.add_argument("--ad-eki", help="cikti adina eklenir: siklik_tr_govde_<ek>.tsv.gz")
    arg = p.parse_args()
    {"sayim": sayim, "ornek": ornek, "excel": excel, "hesapla": hesapla, "birlestir": birlestir}[arg.komut](arg)


if __name__ == "__main__":
    sys.exit(main())
