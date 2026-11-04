#!/usr/bin/env python3
"""
Birlesik Kelime Sozlugu ve Raporu
=================================
Bircok ozette satir sonu bosluklari kaybolmus ("rakımlaragöre",
"arızadankaynaklanan"). Bu betik:

  sozluk: Tum ozetlerden her kelime biciminin kac ozette gectigini sayar ve
          sozluk_<dil>.tsv.gz'ye yazar. Bu dosya varsa kelime_siklik.py'deki
          kelime_listesi() birlesik kelimeleri otomatik boler (tum analiz
          betikleri etkilenir).
  rapor:  Her yil ozetlerin yuzde kacinda birlesik kelime oldugunu ve en sik
          onarimlari gosterir. Oran yillar arasinda cok farkliysa onarim
          yapilmadan yapilan analiz sahte "artis/azalis" uretebilir.

  zemberek: (2026-11-04) Siklik kuralinin bolmek istedigi her kelime (ADAY) icin karar:
            1. kelime TDK madde basi            -> BOLME  (küçükbaş, sözde, alanya)
            2. Zemberek kelimenin tamamini taniyor -> BOLME  (verilerde, göreve)
            3. parcalar TDK'de iki kelimelik madde -> BOL  (okulöncesi -> okul öncesi)
            4. Zemberek her parcayi taniyor       -> BOL    (buaraştırmanın -> bu + araştırmanın)
            5. hicbiri                           -> BOLME
          Kararlar birlesik_karar_<dil>.tsv'ye; kullanici kontrolu icin
          birlesik_kontrol_<dil>.xlsx (73 bolunen + 73 bolunmeyen ornek).
  (v2, 2026-11-05) Kurallar: YALNIZCA iki parca; bolme noktasini Zemberek/TDK secer (iki parca
          da gercek kelime: TDK, beyaz liste ya da >=30 ozet + Zemberek); iki harfli parca yalnizca
          KISA_KELIMELER'den; yalnizca ek olan parca (ini, den...) gecersiz; beyaz liste (asla
          bolunmez) ve zorla-bol listesi: analiz/kaynaklar/birlesik_*.txt (tarih + kaynakla).
  excel:    Ornek JSON'dan kontrol Excel'i (normal python). Eski Excel _vN olarak saklanir,
            ayni kelime + ayni bolme icin cevap aktarilir. Soru: T (tek kelime) / B (bolme dogru).
  karsilastir: Isaretli Excel'deki kelimeleri SIMDIKI kurallardan gecirir (eski/yeni yan yana).
  ek_tur:   Ayni kararlardan yeni 73 'bol' ornegi (incelenenler haric) -> birlesik_kontrol_<dil>_tur2.xlsx.
            hesapla --excel-listesi A.xlsx B.xlsx ile turlar birlestirilir.
  hesapla:  Excel'deki T/B cevaplarindan iki grubun dogrulugu.
  onayla:   KULLANICI kontrolunden sonra: BOL kararlarini birlesik_onayli_<dil>.tsv'ye
            yazar. Analiz betikleri YALNIZCA bu dosyadaki bolmeleri uygular.

Kullanim:
  python3 birlesik_kelime.py sozluk --dil tr
  python3 birlesik_kelime.py rapor --dil tr
  zemberek_env/bin/python3 birlesik_kelime.py zemberek --dil tr   # Zemberek ortami gerekir
  python3 birlesik_kelime.py excel --dil tr                       # Excel (normal python, openpyxl)
  python3 birlesik_kelime.py hesapla --dil tr
  python3 birlesik_kelime.py onayla --dil tr
"""

import argparse
import gzip
import json
import random
import re
from collections import Counter
from pathlib import Path

from kelime_siklik import (NADIR_ESIK, SIK_ESIK, VARSAYILAN_GIRDI, birlesik_mi, kelime_listesi, parca_no,
                           sozluk, sozluk_dosyasi, yil_araligi)


def ozetler(girdi, alan):
    with open(girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            if m.get(alan):
                yield m


def komut_sozluk(arg, alan):
    # Turkcede milyonlarca farkli kelime bicimi var; bellek icin dosya
    # --parca kez okunur, her seferinde kelimelerin bir kismi sayilir.
    cikti = sozluk_dosyasi(arg.dil)
    gecici = Path(str(cikti) + ".gecici")
    toplam = 0
    with gzip.open(gecici, "wt", encoding="utf-8") as f:
        f.write("kelime\tbelge_sayisi\n")
        for k in range(arg.parca):
            sayac, n = Counter(), 0
            for m in ozetler(arg.girdi, alan):
                n += 1
                sayac.update(w for w in set(kelime_listesi(m[alan], arg.dil, onarim=False))
                             if parca_no(w, arg.parca) == k)
            for w, adet in sayac.items():
                if adet >= NADIR_ESIK:
                    f.write(f"{w}\t{adet}\n")
                    toplam += 1
            print(f"  parca {k + 1}/{arg.parca}: {n} ozet, {len(sayac)} farkli kelime")
    gecici.replace(cikti)
    print(f"{toplam} kelime (>= {NADIR_ESIK} ozet) -> {cikti}")


def komut_rapor(arg, alan):
    sozluk_hazirla(arg.dil)
    if not sozluk(arg.dil):
        raise SystemExit(f"Once sozluk olusturun: python3 birlesik_kelime.py sozluk --dil {arg.dil}")
    yillar = set(yil_araligi(arg.yillar))
    n, birlesikli, kelime, onarilan = Counter(), Counter(), Counter(), Counter()
    ornekler = Counter()
    for m in ozetler(arg.girdi, alan):
        y = m.get("yil_guvenilir")
        if y not in yillar:
            continue
        ham = kelime_listesi(m[alan], arg.dil, onarim=False)
        sz = sozluk(arg.dil)
        bu_ozet = 0
        for w in ham:
            if p := birlesik_mi(w, sz):
                bu_ozet += 1
                ornekler[(w, " + ".join(p))] += 1
        n[y] += 1
        kelime[y] += len(ham)
        onarilan[y] += bu_ozet
        birlesikli[y] += bu_ozet > 0

    print(f"Birlesik kelime orani ({arg.dil}):\n")
    print(f"{'yil':>6} {'ozet':>8} {'birlesikli ozet %':>18} {'100 kelimede':>13}")
    for y in sorted(n):
        print(f"{y:>6} {n[y]:>8} {100 * birlesikli[y] / n[y]:>17.1f}% {100 * onarilan[y] / kelime[y]:>13.2f}")
    print(f"\nEn sik onarimlar:")
    for (w, p), adet in ornekler.most_common(arg.ornek):
        print(f"  {adet:>6}  {w}  ->  {p}")


# ------------------------------------------------------------------
# Zemberek + TDK kontrolu (2026-11-04, kullanici karari)
# ------------------------------------------------------------------
KLASOR = Path(__file__).resolve().parent
TDK_DOSYASI = KLASOR / "kaynaklar" / "tdk_sozluk_maddeleri.txt"
ONBELLEK = KLASOR / "zemberek_birlesik_onbellek.json"
TOHUM = 20261104
ORNEK = 73  # hepsi dogruysa %95 Wilson alt siniri %95 (karakter_kontrol.py ile ayni ilke)
BAGLAM = 60


def karar_dosyasi(dil):
    return KLASOR / f"birlesik_karar_{dil}.tsv"


def kontrol_dosyasi(dil):
    return KLASOR / f"birlesik_kontrol_{dil}.xlsx"


def sozluk_hazirla(dil):
    """Sozluk 'sozluk_tr.tsv.gz.kapali' diye kapatildiysa onu da kabul et (artik analiz
    sozlugu kullanmiyor; yalnizca aday uretmek icin gerekli)."""
    from kelime_siklik import sozluk_dosyasi
    asil = sozluk_dosyasi(dil)
    kapali = Path(str(asil) + ".kapali")
    if not asil.exists() and kapali.exists():
        kapali.rename(asil)
        print(f"[{kapali.name} -> {asil.name} (analiz artik yalnizca onayli listeyi kullaniyor)]")


def tdk_yukle():
    if not TDK_DOSYASI.exists():
        raise SystemExit(f"{TDK_DOSYASI} yok (bkz. kaynaklar/README.md)")
    from kelime_siklik import turkce_kucult
    return {turkce_kucult(s.strip()) for s in TDK_DOSYASI.read_text(encoding="utf-8").splitlines() if s.strip()}


class Zemberek:
    """kelime -> Zemberek en az bir cozumleme buluyor mu (tez reposundaki zemberek_gecerli_mi ile
    ayni olcut: len(analysis_results) > 0). Diske onbelleklenir."""

    def __init__(self):
        try:
            from zemberek import TurkishMorphology
        except ImportError:
            raise SystemExit("Zemberek yok: bash zemberek_kur.sh, sonra zemberek_env/bin/python3 ile calistirin.")
        self.morf = TurkishMorphology.create_with_defaults()
        self.onbellek = json.loads(ONBELLEK.read_text(encoding="utf-8")) if ONBELLEK.exists() else {}
        self.yeni = 0

    def taniyor(self, kelime):
        if kelime not in self.onbellek:
            self.onbellek[kelime] = len(self.morf.analyze(kelime).analysis_results) > 0
            self.yeni += 1
            if self.yeni % 20000 == 0:
                self.kaydet()
        return self.onbellek[kelime]

    def kaydet(self):
        ONBELLEK.write_text(json.dumps(self.onbellek, ensure_ascii=False), encoding="utf-8")


# --- v2 kurallari (2026-11-05, kullanicinin ilk isaretlemesinden: bol grubu 42/72) ---
# Iki harfli parca YALNIZCA bu kisa kelimelerden biri olabilir (yapisma hatalarinda gercekten
# gorulenler: busoruya, dePapalık, SUarasında, değişikliğinen). "er", "it", "ut", "la", "ge"
# gercek kelime olsa da ek/hece parcasi olarak cok sik -> bilerek yok (Claude'un secimi).
KISA_KELIMELER = {"bu", "şu", "su", "de", "da", "ve", "ne", "ya", "en", "iş", "ön", "az", "el", "ay", "on", "öz"}
# Yalnizca ek olan parcalar (pay+ini, literatür+den): kendi basina kelime sayilmaz.
EK_PARCALARI = {"ini", "ını", "unu", "ünü", "ine", "ına", "una", "üne", "nin", "nın", "nun", "nün",
                "den", "dan", "ten", "tan", "ler", "lar", "dir", "dır", "dur", "dür", "tir", "tır",
                "tur", "tür", "nde", "nda", "yla", "yle", "dan", "lik", "lık", "luk", "lük", "siz",
                "sız", "suz", "süz", "ndeki", "ndaki", "deki", "daki"}
BEYAZ_LISTE_DOSYASI = KLASOR / "kaynaklar" / "birlesik_beyaz_liste.txt"
ZORLA_BOL_DOSYASI = KLASOR / "kaynaklar" / "birlesik_zorla_bol.txt"


def liste_oku(yol):
    if not yol.exists():
        return []
    return [s.rstrip("\n").split("\t") for s in yol.read_text(encoding="utf-8").splitlines()
            if s.strip() and not s.startswith("#")]


def beyaz_liste():
    return tuple(sutun[0] for sutun in liste_oku(BEYAZ_LISTE_DOSYASI))


def zorla_bol():
    return {sutun[0]: sutun[1].split() for sutun in liste_oku(ZORLA_BOL_DOSYASI)}


def parca_gecerli(p, sz, tdk, zemberek, beyaz):
    """Parca, o baglamda AYRI YAZILMIS gercek bir kelime olabilir mi?"""
    if len(p) <= 2:
        return p in KISA_KELIMELER
    if p in EK_PARCALARI:
        return False
    if p.startswith(beyaz) or p in tdk:
        return True
    return sz.get(p, 0) >= SIK_ESIK and zemberek.taniyor(p)


def karar_ver(kelime, sz, tdk, zemberek, beyaz, zorla):
    """(karar, gerekce, parcalar). Yalnizca IKI parcaya bolunur; bolme noktasini Zemberek/TDK secer."""
    if kelime in zorla:
        return "bol", "zorla böl listesi", zorla[kelime]
    if beyaz and kelime.startswith(beyaz):
        return "bolme", "beyaz liste", []
    if kelime in tdk:
        return "bolme", "TDK madde başı", []
    if zemberek.taniyor(kelime):
        return "bolme", "Zemberek tamamını tanıyor", []
    ikiler = [(kelime[:i], kelime[i:]) for i in range(2, len(kelime) - 1)]
    for bas, son in ikiler:
        if f"{bas} {son}" in tdk:
            return "bol", "TDK iki kelimelik madde", [bas, son]
    gecerli = [(b, s) for b, s in ikiler
               if parca_gecerli(b, sz, tdk, zemberek, beyaz) and parca_gecerli(s, sz, tdk, zemberek, beyaz)]
    if gecerli:
        # birden fazla gecerli bolme varsa: parcalarin seyrek olani en sik olan (eski olcut)
        en_iyi = max(gecerli, key=lambda bs: min(sz.get(bs[0], 0), sz.get(bs[1], 0)))
        return "bol", "iki parça da gerçek kelime", list(en_iyi)
    return "bolme", "onay yok", []


def agirlikli_ornek(liste, agirlik, n, rng):
    """Agirlikli, tekrarsiz ornek (Efraimidis-Spirakis): sik gecen adayin secilme sansi
    daha yuksek -> ornek, onarimin METNE etkisini temsil eder (tek tek kelimeyi degil)."""
    anahtarli = [(rng.random() ** (1.0 / agirlik(x)), x) for x in liste]
    return [x for _, x in sorted(anahtarli, reverse=True)[:n]]


def komut_zemberek(arg, alan):
    sozluk_hazirla(arg.dil)
    sz = sozluk(arg.dil)
    if not sz:
        raise SystemExit(f"Once sozluk: python3 birlesik_kelime.py sozluk --dil {arg.dil}")
    if arg.dil != "tr":
        raise SystemExit("Zemberek yalnizca Turkce; Ingilizce onarim simdilik kapali (2026-11-04).")
    tdk, zemberek = tdk_yukle(), Zemberek()
    beyaz, zorla = beyaz_liste(), zorla_bol()
    yillar = set(yil_araligi(arg.yillar))

    # 1) Adaylar: siklik kuralinin bolmek istedigi kelimeler, kac ozette gectikleri
    aday_parca, aday_ozet = {}, Counter()
    for i, m in enumerate(ozetler(arg.girdi, alan), 1):
        if m.get("yil_guvenilir") not in yillar:
            continue
        for w in set(kelime_listesi(m[alan], arg.dil, onarim=False)):
            if w not in aday_parca:
                p = birlesik_mi(w, sz) or zorla.get(w)  # eski siklik kurali yalnizca ADAY uretir
                if not p:
                    continue
                aday_parca[w] = p
            aday_ozet[w] += 1
        if i % 100000 == 0:
            print(f"  {i} ozet tarandi, {len(aday_parca)} aday")
    print(f"{len(aday_parca)} farkli aday kelime")

    # 2) Karar
    kararlar = {}
    for j, w in enumerate(aday_parca, 1):
        k, g, parcalar = karar_ver(w, sz, tdk, zemberek, beyaz, zorla)
        kararlar[w] = (k, g)
        if k == "bol":
            aday_parca[w] = parcalar  # bolme noktasini artik yeni kural seciyor
        if j % 50000 == 0:
            print(f"  {j}/{len(aday_parca)} karar")
    zemberek.kaydet()
    with open(karar_dosyasi(arg.dil), "w", encoding="utf-8") as f:
        f.write("kelime\tparcalar\tkarar\tgerekce\tozet_sayisi\n")
        for w, (k, g) in sorted(kararlar.items(), key=lambda x: -aday_ozet[x[0]]):
            f.write(f"{w}\t{' '.join(aday_parca[w])}\t{k}\t{g}\t{aday_ozet[w]}\n")

    print(f"\n{'gerekce':>28} {'farkli kelime':>14} {'ozet (gecis)':>13}")
    for g, adet in Counter(g for _, g in kararlar.values()).most_common():
        ozet = sum(aday_ozet[w] for w, (_, gg) in kararlar.items() if gg == g)
        print(f"{g:>28} {adet:>14} {ozet:>13}")
    print(f"-> {karar_dosyasi(arg.dil)}")

    # 3) Kullanici kontrolu icin ornek: her gruptan ORNEK kelime (sik gecene agirlikli)
    rng = random.Random(TOHUM)
    gruplar = {k: [w for w, (kk, _) in kararlar.items() if kk == k] for k in ("bol", "bolme")}
    secilen = {k: agirlikli_ornek(sorted(v), lambda w: aday_ozet[w], ORNEK, rng) for k, v in gruplar.items()}
    baglam = ornek_baglamlar(arg, alan, {w for v in secilen.values() for w in v})
    # Ornekler once JSON'a yazilir: Excel'i Zemberek ortami degil, normal python3 olusturur
    # (Zemberek ortamina openpyxl kurmak gerekmesin; kullanici karari 2026-11-04).
    ornek = {"secilen": secilen, "kararlar": {w: kararlar[w] for v in secilen.values() for w in v},
             "parcalar": {w: aday_parca[w] for v in secilen.values() for w in v},
             "ozet": {w: aday_ozet[w] for v in secilen.values() for w in v}, "baglam": baglam}
    ornek_dosyasi(arg.dil).write_text(json.dumps(ornek, ensure_ascii=False), encoding="utf-8")
    print(f"ornekler -> {ornek_dosyasi(arg.dil)}\nSimdi Excel icin (normal python ile):\n"
          f"  python3 birlesik_kelime.py excel --dil {arg.dil}")


def ornek_dosyasi(dil):
    return KLASOR / f"birlesik_ornek_{dil}.json"


def komut_excel(arg, alan):
    o = json.loads(ornek_dosyasi(arg.dil).read_text(encoding="utf-8"))
    excel_yaz(arg.dil, o["secilen"], o["kararlar"], o["parcalar"], o["ozet"], o["baglam"])


def ornek_baglamlar(arg, alan, kelimeler):
    """Secilen kelimelerin her biri icin ilk gectigi ozetten bir kesit ve makale adresi."""
    from kelime_siklik import turkce_kucult
    bulunan, kalan = {}, set(kelimeler)
    for m in ozetler(arg.girdi, alan):
        if not kalan:
            break
        metin = m[alan]
        kucuk = turkce_kucult(metin)
        for w in [w for w in kalan if w in kucuk]:
            if (x := re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", kucuk)):
                bas, son = max(0, x.start() - BAGLAM), min(len(metin), x.end() + BAGLAM)
                bulunan[w] = (metin[bas:x.start()] + "⟦" + metin[x.start():x.end()] + "⟧" + metin[x.end():son],
                              (m.get("url") or "").replace("/en/", "/tr/"))
                kalan.discard(w)
    return bulunan


SORU = ("Doğru yazım hangisi?  T = olduğu gibi TEK kelime   B = önerilen BÖLME doğru. "
        "İkisi de değilse (ör. başka yerden bölünmeli) açıklamaya doğru yazımı yazın.")
CEVAP_SUTUNU = "doğru yazım (T/B)"


def excel_yaz(dil, secilen, kararlar, parcalar, ozet, baglam, yol=None):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation
    yol = yol or kontrol_dosyasi(dil)
    eski = eski_cevaplar(yol) if yol.exists() else {}
    if yol.exists():  # isaretli eski dosya silinmez, surum adiyla saklanir
        n = 1
        while (yedek := yol.with_name(f"{yol.stem}_v{n}{yol.suffix}")).exists():
            n += 1
        yol.rename(yedek)
        print(f"eski Excel -> {yedek.name} (cevaplar korunuyor)")
    wb = Workbook()
    ws = wb.active
    ws.title = "kontrol"
    sutunlar = [("no", 5), ("grup", 8), ("soru", 34), ("kelime", 22), ("önerilen bölme", 26), ("gerekçe", 22),
                ("kaç özette", 9), ("örnek kesit (kelime ⟦ ⟧ içinde)", 60), ("adres", 30),
                (CEVAP_SUTUNU, 10), ("açıklama", 30)]
    ws.append([a for a, _ in sutunlar])
    for i, (_, gen) in enumerate(sutunlar, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = gen
        ws.cell(1, i).font = Font(bold=True)
    no = aktarilan = 0
    for grup in [g for g in ("bol", "bolme") if g in secilen]:
        for w in secilen[grup]:
            no += 1
            kesit, adres = baglam.get(w, ("", ""))
            oneri = " + ".join(parcalar[w])
            cevap, aciklama = eski.get((w, oneri if grup == "bol" else ""), ("", ""))
            aktarilan += bool(cevap)
            ws.append([no, grup, SORU, w, oneri if grup == "bol" else f"(bölünmüyor; aday: {oneri})",
                       kararlar[w][1], ozet[w], kesit, adres, cevap, aciklama])
            if adres:
                ws.cell(ws.max_row, 9).hyperlink = adres
    for satir in ws.iter_rows():
        for h in satir:
            h.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"T,B"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"J2:J{ws.max_row}")
    ws.freeze_panes = "A2"
    wb.save(yol)
    print(f"{no} ornek -> {yol}; onceki Excel'den {aktarilan} cevap aktarildi")


def eski_cevaplar(yol):
    """Onceki Excel'deki cevaplar, yeni (T/B) bicime cevrilmis: (kelime, bol-onerisi) -> (cevap, aciklama).
    Eski D/Y: bol grubunda D -> B; bolme grubunda D -> T. Y'ler belirsiz (bol-Y: tek kelime de
    olabilir, baska yerden bolunmesi gereken yapisma da) -> aktarilmaz."""
    from openpyxl import load_workbook
    ws = load_workbook(yol).active
    baslik = [c.value for c in ws[1]]
    i_cevap = baslik.index(CEVAP_SUTUNU) if CEVAP_SUTUNU in baslik else baslik.index("cevap (D/Y)")
    sonuc = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        grup, kelime, oneri, c = r[1], r[3], str(r[4] or ""), str(r[i_cevap] or "").strip().upper()[:1]
        aciklama = str(r[i_cevap + 1] or "")
        if CEVAP_SUTUNU not in baslik:  # eski D/Y bicimi
            c = {("bol", "D"): "B", ("bolme", "D"): "T"}.get((grup, c), "")
        if c in ("T", "B"):
            sonuc[(kelime, oneri if grup == "bol" else "")] = (c, aciklama)
            if c == "T":  # tek kelime oldugu bilgisi, yeni karar 'bolme' olsa da gecerli
                sonuc[(kelime, "")] = (c, aciklama)
    return sonuc


def wilson(dogru, n, z=1.96):
    """%95 Wilson araligi (toplama/dil_dogrulama.py ile ayni formul)."""
    p = dogru / n
    merkez = (p + z * z / (2 * n)) / (1 + z * z / n)
    yari = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / (1 + z * z / n)
    return max(0.0, merkez - yari), min(1.0, merkez + yari)


def incelenmis_kelimeler(dil):
    """Bu dil icin daha once kontrol Excel'lerine girmis butun kelimeler (her tur, her surum)."""
    from openpyxl import load_workbook
    kelimeler = set()
    for yol in KLASOR.glob(f"birlesik_kontrol_{dil}*.xlsx"):
        kelimeler.update(r[3] for r in load_workbook(yol).active.iter_rows(min_row=2, values_only=True) if r[3])
    return kelimeler


def komut_ek_tur(arg, alan):
    """Ayni (dondurulmus) kararlardan YENI bir 'bol' ornegi: daha once incelenen kelimeler haric,
    farkli tohum. Kurallar degismez: birlesik_karar_<dil>.tsv oldugu gibi kullanilir (2026-11-05)."""
    yol = KLASOR / f"birlesik_kontrol_{arg.dil}_tur{arg.tur}.xlsx"
    if yol.exists():
        raise SystemExit(f"{yol.name} zaten var (cevaplariniz olabilir).")
    gorulen = incelenmis_kelimeler(arg.dil)
    kararlar, parcalar, ozet = {}, {}, {}
    with open(karar_dosyasi(arg.dil), encoding="utf-8") as f:
        next(f)
        for satir in f:
            w, p, k, g, n = satir.rstrip("\n").split("\t")
            if k == "bol" and w not in gorulen:
                kararlar[w], parcalar[w], ozet[w] = (k, g), p.split(), int(n)
    rng = random.Random(TOHUM + arg.tur)  # her tur kendi sabit tohumuyla
    secilen = {"bol": agirlikli_ornek(sorted(kararlar), lambda w: ozet[w], ORNEK, rng)}
    print(f"{len(gorulen)} kelime daha once incelendi (haric); {len(kararlar)} bol adayi; "
          f"{len(secilen['bol'])} secildi (tohum {TOHUM + arg.tur})")
    baglam = ornek_baglamlar(arg, alan, set(secilen["bol"]))
    excel_yaz(arg.dil, secilen, kararlar, parcalar, ozet, baglam, yol=yol)


def komut_hesapla(arg, alan):
    """Bir ya da birden cok T/B Excel'ini birlestirerek hesaplar (ayni kelime bir kez sayilir)."""
    from openpyxl import load_workbook
    sayac = {"bol": Counter(), "bolme": Counter()}
    dogru_cevap = {"bol": "B", "bolme": "T"}
    gorulen = set()
    for yol in (arg.excel_listesi or [kontrol_dosyasi(arg.dil)]):
        ws = load_workbook(yol).active
        if CEVAP_SUTUNU not in [c.value for c in ws[1]]:
            raise SystemExit(f"{yol}: eski D/Y bicimi (v1 kurallari) — v2 sonucuyla birlestirilemez.")
        for r in ws.iter_rows(min_row=2, values_only=True):
            if r[3] in gorulen:
                continue
            gorulen.add(r[3])
            c = str(r[9] or "").strip().upper()[:1]
            sayac[r[1]]["bos" if c not in ("T", "B") else ("D" if c == dogru_cevap[r[1]] else "Y")] += 1
    for grup, c in sayac.items():
        n = c["D"] + c["Y"]
        oran = ""
        if n:
            alt, ust = wilson(c["D"], n)
            oran = f"%{100 * c['D'] / n:.1f} (%95: {100 * alt:.1f}–{100 * ust:.1f})"
        print(f"{grup:>6}: kod dogru {c['D']}, kod yanlis {c['Y']}, bos {c['bos']}  {oran}")


def komut_karsilastir(arg, alan):
    """Kullanicinin isaretledigi Excel'deki kelimeleri SIMDIKI kurallardan gecirir: eski oneri,
    kullanicinin cevabi ve yeni karar yan yana. Yeniden calistirmadan once kurali sinamak icin."""
    from openpyxl import load_workbook
    sozluk_hazirla(arg.dil)
    sz = sozluk(arg.dil) or {}
    tdk, zemberek, beyaz, zorla = tdk_yukle(), Zemberek(), beyaz_liste(), zorla_bol()
    ws = load_workbook(arg.excel or kontrol_dosyasi(arg.dil)).active
    baslik = [c.value for c in ws[1]]
    yeni_bicim = CEVAP_SUTUNU in baslik
    i_cevap = baslik.index(CEVAP_SUTUNU if yeni_bicim else "cevap (D/Y)")
    sayac = Counter()
    print(f"{'no':>3} {'grup':>5}  {'kelime':<28} {'eski öneri':<30} {'siz':<4} {'YENİ karar':<34} uyum")
    for r in ws.iter_rows(min_row=2, values_only=True):
        no, grup, kelime, eski_oneri = r[0], r[1], r[3], str(r[4] or "")
        c = str(r[i_cevap] or "").strip().upper()[:1]
        if not yeni_bicim:
            c = {("bol", "D"): "B", ("bolme", "D"): "T", ("bol", "Y"): "Y"}.get((grup, c), "?")
        k, g, parcalar = karar_ver(kelime, sz, tdk, zemberek, beyaz, zorla)
        yeni = " + ".join(parcalar) if k == "bol" else f"bölme ({g})"
        if c == "B":
            uyum = "✓" if k == "bol" and " + ".join(parcalar) == eski_oneri else "✗"
        elif c == "T":
            uyum = "✓" if k == "bolme" else "✗"
        else:
            uyum = "?"  # isaretlenmemis ya da eski Y (tek kelime mi, baska yerden mi?) -> aciklamaya bakin
        sayac[(c, uyum)] += 1
        aciklama = str(r[i_cevap + 1] or "")[:40]
        print(f"{no:>3} {grup:>5}  {kelime[:28]:<28} {eski_oneri[:30]:<30} {c:<4} {yeni[:34]:<34} {uyum}  {aciklama}")
    zemberek.kaydet()
    print("\nOzet (siz: B = bolunmeli, T = tek kelime, Y = eski 'yanlis' (aciklamaya bakin), ? = bos):")
    for (c, u), n in sorted(sayac.items()):
        print(f"  siz {c}  yeni kural {u}: {n}")
    print("Not: 'siz B' ama yeni bolme eski oneriden farkliysa ✗ gorunur; satira bakin "
          "(ör. eski oneri yanlis yerden bolmusse yeni bolme dogru olabilir).")


def komut_onayla(arg, alan):
    """KULLANICI kontrolunden sonra calistirilir: 'bol' kararlari analizde kullanilacak listeye."""
    kaynak = karar_dosyasi(arg.dil)
    if not kaynak.exists():
        raise SystemExit("Once: zemberek komutu")
    from kelime_siklik import onayli_dosyasi
    n = 0
    with open(kaynak, encoding="utf-8") as g, open(onayli_dosyasi(arg.dil), "w", encoding="utf-8") as f:
        next(g)
        f.write("kelime\tparcalar\n")
        for s in g:
            w, p, k, *_ = s.rstrip("\n").split("\t")
            if k == "bol":
                f.write(f"{w}\t{p}\n")
                n += 1
    print(f"{n} onayli bolme -> {onayli_dosyasi(arg.dil)} (analiz betikleri artik bunlari boler)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["sozluk", "rapor", "zemberek", "excel", "ek_tur", "karsilastir", "hesapla",
                                     "onayla"])
    p.add_argument("--tur", type=int, default=2, help="ek_tur: tur numarasi (dosya adi ve tohum)")
    p.add_argument("--excel-listesi", nargs="+", help="hesapla: birlestirilecek T/B Excel'leri")
    p.add_argument("--excel", help="karsilastir: isaretli Excel (varsayilan birlesik_kontrol_<dil>.xlsx)")
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--parca", type=int, default=4, help="sozluk: dosya kac kez okunsun (bellek / parca)")
    p.add_argument("--yillar", default="2015-2026")
    p.add_argument("--ornek", type=int, default=40, help="rapor: gosterilecek ornek onarim sayisi")
    arg = p.parse_args()
    alan = f"ozet_{arg.dil}"
    {"sozluk": komut_sozluk, "rapor": komut_rapor, "zemberek": komut_zemberek, "excel": komut_excel, "ek_tur": komut_ek_tur, "karsilastir": komut_karsilastir, "hesapla": komut_hesapla,
     "onayla": komut_onayla}[arg.komut](arg, alan)


if __name__ == "__main__":
    main()
