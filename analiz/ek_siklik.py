#!/usr/bin/env python3
"""
Ek (suffix) Sikliklari (yillara gore)
=====================================
Turkce ozetlerdeki her kelimeyi Zemberek ile kok + eklere ayirir
(orn. "oynamaktadir" -> oyna + makta(Prog2) + A3sg + dir(Cop)) ve her yil icin:

  1. Her ekin ve her ek zincirinin ("Prog2+A3sg+Cop" = -mAktAdIr) KAC OZETTE
     gectigi -> kelime_siklik.py ile ayni bicimde yazilir; asiri_kullanim.py
     dogrudan calisir:
       siklik_tr_ek.tsv.gz, siklik_tr_ekzinciri.tsv.gz (+ .belge.json)
  2. Her ekin 100 kelimede kac kez gectigi (yogunluk) -> ek_yogunluk_tr.tsv
     "Hemen her ozette gecen" yaygin ekler (Prog2, Pass gibi) icin ozet orani
     doyar; yogunluk degisimi daha iyi gosterir. Ekrana, hedef yil icin
     yogunluga Kobak vd. karsi-olgusalinin uygulandigi tablo basilir.

Ayni yontem tez calismasindaki (TR-LLM-Analiz, ek_idf_analizi.py) gibidir:
Zemberek'in ILK cozumlemesi kullanilir, kokten sonraki bicimbirimler sayilir.
Kesme isaretinden sonraki ekler (ozel isimler: "Turkiye'nin") sayilmaz.

Her farkli kelime bicimi bir kez cozumlenir; sonuclar onbellek dosyasina
yazilir (ek_onbellek.json.gz), yeniden calistirmada tekrar kullanilir.

Calistirma (Zemberek sanal ortami gerekir: bash zemberek_kur.sh):
  zemberek_env/bin/python3 ek_siklik.py
  zemberek_env/bin/python3 ek_siklik.py --hedef 2025
Sonra ornegin:
  python3 asiri_kullanim.py --dil tr --siklik siklik_tr_ekzinciri.tsv.gz --hedef 2024 --en-az-belge 50
"""

import argparse
import gzip
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from asiri_kullanim import karsi_olgusal
from kelime_siklik import VARSAYILAN_GIRDI, dergi_filtresi, kelime_listesi, secili, yil_araligi

KLASOR = Path(__file__).resolve().parent
ONBELLEK = KLASOR / "ek_onbellek.json.gz"

EK_ACIKLAMA = {
    "A3pl": "cogul (-lAr)", "A1sg": "1.tekil sahis", "A2sg": "2.tekil sahis",
    "A1pl": "1.cogul sahis", "A2pl": "2.cogul sahis", "A3sg": "3.tekil sahis",
    "P1sg": "1.tekil iyelik (-Im)", "P2sg": "2.tekil iyelik (-In)",
    "P3sg": "3.tekil iyelik (-(s)I)", "P1pl": "1.cogul iyelik (-ImIz)",
    "P2pl": "2.cogul iyelik (-InIz)", "P3pl": "3.cogul iyelik (-lArI)",
    "Gen": "ilgi hali (-In)", "Acc": "belirtme hali (-I)", "Dat": "yonelme hali (-A)",
    "Loc": "bulunma hali (-DA)", "Abl": "ayrilma hali (-DAn)", "Ins": "vasita hali (-lA)",
    "Equ": "esitlik hali (-cA)", "Cop": "bildirme / ek-fiil (-DIr)",
    "Pass": "edilgen (-Il/-In)", "Caus": "ettirgen (-DIr/-t)", "Recip": "isteslik (-Is)",
    "Reflex": "donusluluk (-In)", "Neg": "olumsuzluk (-mA)", "Able": "yeterlik (-Abil)",
    "Unable": "olumsuz yeterlik (-AmA)", "Aor": "genis zaman (-Ir/-Ar)",
    "Prog1": "simdiki zaman (-Iyor)", "Prog2": "simdiki zaman (-mAktA)",
    "Past": "gorulen gecmis (-DI)", "Narr": "duyulan gecmis / rivayet (-mIs)",
    "Fut": "gelecek zaman (-AcAk)", "Cond": "sart (-sA)", "Imp": "emir",
    "Opt": "istek (-A)", "Neces": "gereklilik (-mAlI)", "Desr": "dilek (-sA)",
    "Inf1": "mastar (-mAk)", "Inf2": "isim-fiil (-mA)", "Inf3": "isim-fiil (-Is)",
    "PresPart": "sifat-fiil (-An)", "PastPart": "sifat-fiil (-DIk)",
    "FutPart": "sifat-fiil (-AcAk)", "NarrPart": "sifat-fiil (-mIs)",
    "AorPart": "sifat-fiil (-Ir/-Ar)", "ByDoingSo": "zarf-fiil (-ArAk)",
    "While": "zarf-fiil (-ken)", "AfterDoingSo": "zarf-fiil (-Ip)",
    "When": "zarf-fiil (-IncA)", "SinceDoingSo": "zarf-fiil (-AlI)",
    "WithoutHavingDoneSo": "zarf-fiil (-mAdAn)", "AsLongAs": "zarf-fiil (-DIkcA)",
    "AsIf": "zarf-fiil (-cAsInA)", "Ness": "isimlik (-lIk)", "With": "sahiplik (-lI)",
    "Without": "yokluk (-sIz)", "Rel": "ilgi eki (-ki)", "Related": "iliskililik (-sAl)",
    "Agt": "yapan (-cI)", "Dim": "kucultme (-cIk)", "JustLike": "benzerlik (-msI)",
    "Ly": "zarf yapan (-cA)", "Become": "olma (-lAs)", "Acquire": "edinme (-lAn)",
    "FitFor": "uygunluk (-lIk)", "Ordinal": "sira sayi (-IncI)",
    "Distrib": "ulestirme (-Ar)", "Ql": "-ce/-ca (sifat)", "Pnon": "iyeliksiz",
    "Nom": "yalin hal", "Pres": "simdiki/genis", "Past2": "-DI",
    "Hastily": "tezlik (-Iver)", "EverSince": "suregelme (-Agel)",
    "Repeat": "surerlik (-Adur)", "Almost": "yaklasma (-Ayaz)",
    "Start": "baslama (-Akoy)", "Stay": "kalma (-Akal)",
    "Inst": "-In (zarf)", "Dup": "ikileme", "NotState": "-mAzlIk",
    "ActOf": "-mAcA", "FeelLike": "-AsI", "Opt2": "istek",
}


class EkCozumleyici:
    """Kelime -> ek listesi (Zemberek ilk cozumlemesi), disk onbellekli."""

    def __init__(self, onbellek_dosyasi=ONBELLEK):
        from zemberek import TurkishMorphology  # sadece zemberek_env'de var
        self.morfoloji = TurkishMorphology.create_with_defaults()
        self.dosya = Path(onbellek_dosyasi)
        self.onbellek = {}
        if self.dosya.exists():
            with gzip.open(self.dosya, "rt", encoding="utf-8") as f:
                self.onbellek = json.load(f)
        self.yeni = 0

    def ekler(self, kelime):
        """Ek kimlikleri listesi; Zemberek taniyamazsa None."""
        if kelime in self.onbellek:
            return self.onbellek[kelime]
        sonuc = self.morfoloji.analyze(kelime).analysis_results
        ekler = [md.morpheme.id_ for md in sonuc[0].morpheme_data_list[1:]] if sonuc else None
        self.onbellek[kelime] = ekler
        self.yeni += 1
        if self.yeni % 50000 == 0:
            self.kaydet()
        return ekler

    def kaydet(self):
        with gzip.open(self.dosya, "wt", encoding="utf-8") as f:
            json.dump(self.onbellek, f, ensure_ascii=False)


def ozet_ekleri(metin, cozumleyici):
    """(ek sayaci, ek kumesi, zincir kumesi, kelime sayisi, taninmayan sayisi)"""
    sayac, zincirler = Counter(), set()
    kelimeler = kelime_listesi(metin, "tr")
    taninmayan = 0
    for k in kelimeler:
        ekler = cozumleyici.ekler(k)
        if ekler is None:
            taninmayan += 1
            continue
        sayac.update(ekler)
        if ekler:
            zincirler.add("+".join(ekler))
    return sayac, set(sayac), zincirler, len(kelimeler), taninmayan


def yaz_siklik(dosya, sayilar, belge):
    with gzip.open(dosya, "wt", encoding="utf-8") as f:
        f.write("yil\tkelime\tbelge_sayisi\n")
        for yil in sorted(sayilar):
            for oge, adet in sayilar[yil].items():
                f.write(f"{yil}\t{oge}\t{adet}\n")
    Path(str(dosya) + ".belge.json").write_text(json.dumps(belge, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--yillar", default="2015-2026")
    p.add_argument("--taban", type=int, default=2022)
    p.add_argument("--hedef", type=int, default=2024)
    p.add_argument("--min-belge", type=int, default=5, help="Zincir bir yilda bundan az ozette geciyorsa atilir")
    p.add_argument("--onek", default="", help="Cikti dosyalarinin basina eklenecek on ek (test icin)")
    p.add_argument("--dergiler", help="Sadece bu dergiler (orn. dergi_paneli_tr.txt)")
    arg = p.parse_args()

    dergiler = dergi_filtresi(arg.dergiler)
    yillar = set(yil_araligi(arg.yillar))
    cozumleyici = EkCozumleyici()
    print(f"Onbellekte {len(cozumleyici.onbellek)} kelime bicimi var.")

    belge = Counter()
    ek_ozet = defaultdict(Counter)       # yil -> ek -> kac ozette
    zincir_ozet = defaultdict(Counter)   # yil -> zincir -> kac ozette
    ek_adet = defaultdict(Counter)       # yil -> ek -> toplam adet
    kelime_say, taninmayan_say = Counter(), Counter()
    basla = time.time()
    with open(arg.girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            y = m.get("yil_guvenilir")
            if y not in yillar or not m.get("ozet_tr") or not secili(m, dergiler):
                continue
            sayac, ekler, zincirler, n_kelime, n_tanin = ozet_ekleri(m["ozet_tr"], cozumleyici)
            belge[y] += 1
            ek_ozet[y].update(ekler)
            zincir_ozet[y].update(zincirler)
            ek_adet[y].update(sayac)
            kelime_say[y] += n_kelime
            taninmayan_say[y] += n_tanin
            toplam = sum(belge.values())
            if toplam % 5000 == 0:
                print(f"  {toplam} ozet, {len(cozumleyici.onbellek)} farkli kelime, "
                      f"{time.time() - basla:.0f} sn", end="\r")
    cozumleyici.kaydet()
    print(" " * 70, end="\r")

    for y in zincir_ozet:  # nadir zincirleri at (dosya boyutu)
        zincir_ozet[y] = Counter({z: a for z, a in zincir_ozet[y].items() if a >= arg.min_belge})
    belge_json = {y: belge[y] for y in sorted(belge)}
    yaz_siklik(KLASOR / f"{arg.onek}siklik_tr_ek.tsv.gz", ek_ozet, belge_json)
    yaz_siklik(KLASOR / f"{arg.onek}siklik_tr_ekzinciri.tsv.gz", zincir_ozet, belge_json)

    # Yogunluk (100 kelimede) + karsi-olgusal
    tum_ekler = sorted({e for y in ek_adet for e in ek_adet[y]})
    yogunluk = {y: {e: 100 * ek_adet[y][e] / kelime_say[y] for e in tum_ekler} for y in ek_adet if kelime_say[y]}
    with open(KLASOR / f"{arg.onek}ek_yogunluk_tr.tsv", "w", encoding="utf-8") as f:
        f.write("ek\taciklama\t" + "\t".join(str(y) for y in sorted(yogunluk)) + "\n")
        for e in tum_ekler:
            f.write(f"{e}\t{EK_ACIKLAMA.get(e, '')}\t"
                    + "\t".join(f"{yogunluk[y][e]:.4f}" for y in sorted(yogunluk)) + "\n")

    print("Yil  ozet  kelime  taninmayan%")
    for y in sorted(belge):
        print(f"{y} {belge[y]:>6} {kelime_say[y]:>9} {100 * taninmayan_say[y] / max(kelime_say[y], 1):>6.2f}")

    b, T = arg.taban, arg.hedef
    if all(y in yogunluk for y in (b - 1, b, T)):
        satirlar = []
        for e in tum_ekler:
            q = karsi_olgusal(yogunluk[b - 1][e], yogunluk[b][e], T - b)
            if yogunluk[T][e] >= 0.05:  # 100 kelimede en az 0,05 (cok nadir ekleri gosterme)
                satirlar.append((e, yogunluk[b - 1][e], yogunluk[b][e], q, yogunluk[T][e]))
        satirlar.sort(key=lambda r: -(r[4] / max(r[3], 1e-9)))
        print(f"\nEk yogunlugu (100 kelimede), taban {b - 1}-{b} -> hedef {T}, kata gore:")
        print(f"{'ek':>14} {'aciklama':>28} {b - 1:>7} {b:>7} {'q':>7} {T:>7} {'fark':>7} {'kat':>5}")
        for e, p1, p2, q, pT in satirlar:
            print(f"{e:>14} {EK_ACIKLAMA.get(e, '')[:28]:>28} {p1:>7.3f} {p2:>7.3f} {q:>7.3f} {pT:>7.3f} "
                  f"{pT - q:>+7.3f} {pT / max(q, 1e-9):>5.2f}")
    print(f"\nCiktilar: {arg.onek}siklik_tr_ek.tsv.gz, {arg.onek}siklik_tr_ekzinciri.tsv.gz, "
          f"{arg.onek}ek_yogunluk_tr.tsv; onbellek: {ONBELLEK.name}")


if __name__ == "__main__":
    main()
