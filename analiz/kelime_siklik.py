#!/usr/bin/env python3
"""
Kelime ve Kelime Grubu Sikliklari (yillara gore)
================================================
makaleler.jsonl'deki ozlerden, her kelimenin (--n 1) veya n kelimelik grubun
(--n 2, 3, 4: "onemli bir rol oynamaktadir" gibi kalip ifadeler) her yil KAC
OZETTE gectigini sayar (Kobak vd. 2025 gibi: ayni ozette kac kez gectigi
degil, gecip gecmedigi). Analizde makalenin yil_guvenilir alani kullanilir;
arsiv/yilsiz makaleler disarida kalir.

Kelime gruplari cumle/yan cumle sinirini (. ! ? ; : , parantez) asmaz:
"...sonuclandi. Bu calisma..." icinden "sonuclandi bu" grubu cikmaz.

Cikti (--cikti, varsayilan siklik_<dil>.tsv.gz, n>1 icin
siklik_<dil>_<n>gram.tsv.gz): yil, kelime, belge_sayisi
Ayrica <cikti>.belge.json: her yil kac ozet sayildi (oranin paydasi).

Bellek: dosya her yil icin ayri okunur ve o yil --min-belge'den az ozette
gecen ogeler atilir. Kelime gruplari cok daha fazla cesit urettigi icin her
yilin sayimi ayrica --parca kadar parcaya bolunur (her parca ogelerin bir
kismini sayar; sonuc ayni, bellek 1/parca).

Kullanim:
  python3 kelime_siklik.py --dil tr
  python3 kelime_siklik.py --dil tr --n 3
  python3 kelime_siklik.py --dil en --yillar 2018-2026
"""

import argparse
import gzip
import json
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
VARSAYILAN_GIRDI = KLASOR.parent / "toplama" / "makaleler.jsonl"

KELIME = re.compile(r"[^\W\d_]+", re.UNICODE)  # sadece harflerden olusan diziler
KESME_EKI = re.compile(r"[’'`]\w+", re.UNICODE)  # "Türkiye'nin" -> "Türkiye"
CUMLE_SINIRI = re.compile(r"[.!?;:,()\[\]\"“”«»\n]+")


def turkce_kucult(metin: str) -> str:
    # Python'un .lower() metodu 'İ'yi yanlis donusturuyor
    return metin.replace("İ", "i").replace("I", "ı").lower()


TR_BUYUK = set("ÇĞİÖŞÜ")


def tr_kelime_kucult(kelime: str) -> str:
    # Tamami buyuk harfli ve Turkceye ozgu harf icermeyen kelimeler genelde
    # Ingilizce kisaltma: "COVID" -> "covid" (Turkce kurala gore "covıd" olurdu)
    if kelime.isupper() and not (set(kelime) & TR_BUYUK):
        return kelime.lower()
    return turkce_kucult(kelime)


# ------------------------------------------------------------------
# Birlesik kelime onarimi
# ------------------------------------------------------------------
# Bircok ozet PDF'ten kopyalanirken satir sonu bosluklari kaybolmus:
# "rakımlaragöre", "yaşamımızınayrılmaz", "arızadankaynaklanan". Sozluk dosyasi
# (birlesik_kelime.py sozluk ile uretilir) varsa, bir kelime her parcasi en az
# SIK_ESIK ozette gecen 2 (gerekirse 3) kelimeye bolunebiliyorsa VE kendisi ya
# cok nadirse (< NADIR_ESIK ozet) ya da en seyrek parcasindan en az KAT_ESIK
# kat daha seyrekse bolunur ("biryandan" gibi tekrarlayan hatalar icin).
# Sik kelimeler ("neden", "bilgisayar") bu yuzden bolunmez. Turkcenin eklemeli
# yapisi yuzunden yanlis bolme riski dusuk: "kitaplarımızdan" bolunmez, cunku
# "ımızdan" bir kelime degil.
NADIR_ESIK = 3
SIK_ESIK = 30
KAT_ESIK = 20
ADAY_UST_SINIR = 1000  # bundan cok ozette gecen kelime birlesik sayilmaz (hiz icin)
EN_KISA_PARCA = 2
EN_KISA_ONARILAN = 5
_SOZLUKLER = {}


def sozluk_dosyasi(dil: str) -> Path:
    return KLASOR / f"sozluk_{dil}.tsv.gz"


def sozluk(dil: str):
    """{kelime: belge sayisi} (yalnizca >= NADIR_ESIK olanlar) veya dosya yoksa None."""
    if dil not in _SOZLUKLER:
        dosya = sozluk_dosyasi(dil)
        if dosya.exists():
            with gzip.open(dosya, "rt", encoding="utf-8") as f:
                next(f)
                _SOZLUKLER[dil] = {k: int(n) for k, n in (s.rstrip("\n").split("\t") for s in f)}
            print(f"[birlesik kelime onarimi acik: {dosya.name}, {len(_SOZLUKLER[dil])} kelime]",
                  file=sys.stderr)
        else:
            _SOZLUKLER[dil] = None
    return _SOZLUKLER[dil]


def bol(kelime: str, sz: dict, derinlik: int = 2):
    """Birlesik kelimeyi sik kelimelere boler (parcalarin en az sik olani en sik
    olacak sekilde); bolunemezse None."""
    en_iyi, en_iyi_puan = None, 0
    for i in range(EN_KISA_PARCA, len(kelime) - EN_KISA_PARCA + 1):
        bas, son = kelime[:i], kelime[i:]
        if sz.get(bas, 0) < SIK_ESIK:
            continue
        if sz.get(son, 0) >= SIK_ESIK:
            parcalar = [bas, son]
        elif derinlik > 1 and sz.get(son, 0) < NADIR_ESIK:
            geri = bol(son, sz, derinlik - 1)
            if not geri:
                continue
            parcalar = [bas] + geri
        else:
            continue
        puan = min(sz[p] for p in parcalar)
        if puan > en_iyi_puan:
            en_iyi, en_iyi_puan = parcalar, puan
    return en_iyi


def onar(kelimeler: list, dil: str) -> list:
    sz = sozluk(dil)
    if not sz:
        return kelimeler
    sonuc = []
    for k in kelimeler:
        parcalar = birlesik_mi(k, sz)
        sonuc.extend(parcalar or [k])
    return sonuc


def birlesik_mi(kelime: str, sz: dict):
    """Kelime birlesikse parcalari, degilse None."""
    adet = sz.get(kelime, 0)
    if len(kelime) < EN_KISA_ONARILAN or adet >= ADAY_UST_SINIR:
        return None
    parcalar = bol(kelime, sz)
    if parcalar and (adet < NADIR_ESIK or adet * KAT_ESIK <= min(sz[p] for p in parcalar)):
        return parcalar
    return None


def kelime_listesi(metin: str, dil: str, onarim: bool = True) -> list:
    """Metindeki kelimeler, sirasiyla (sozluk varsa birlesik kelimeler bolunmus)."""
    if dil == "tr":
        bulunan = (tr_kelime_kucult(k) for k in KELIME.findall(KESME_EKI.sub("", metin)))
    else:
        bulunan = KELIME.findall(metin.lower())
    kelimeler = [k for k in bulunan if len(k) >= 2]
    return onar(kelimeler, dil) if onarim else kelimeler


def kelimeler(metin: str, dil: str) -> set:
    return set(kelime_listesi(metin, dil))


def gruplar(metin: str, dil: str, n: int) -> set:
    """Metindeki n kelimelik gruplar ("onemli bir rol"); cumle sinirini asmaz."""
    if n == 1:
        return kelimeler(metin, dil)
    sonuc = set()
    for parca in CUMLE_SINIRI.split(metin):
        k = kelime_listesi(parca, dil)
        sonuc.update(" ".join(k[i:i + n]) for i in range(len(k) - n + 1))
    return sonuc


def parca_no(oge: str, parca_sayisi: int) -> int:
    return zlib.crc32(oge.encode()) % parca_sayisi  # calismadan calismaya sabit


def siklik_dosya_adi(dil: str, n: int) -> str:
    return f"siklik_{dil}.tsv.gz" if n == 1 else f"siklik_{dil}_{n}gram.tsv.gz"


def dergi_filtresi(dosya):
    """--dergiler dosyasindaki dergi kodlari (her satirda bir); dosya yoksa None (filtre yok)."""
    if not dosya:
        return None
    return {s.strip() for s in Path(dosya).read_text(encoding="utf-8").splitlines() if s.strip()}


def secili(m, dergiler):
    return dergiler is None or m.get("dergi_kodu") in dergiler


def yil_araligi(metin: str):
    bas, son = metin.split("-")
    return list(range(int(bas), int(son) + 1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", default=str(VARSAYILAN_GIRDI))
    p.add_argument("--dil", choices=["tr", "en"], required=True)
    p.add_argument("--yillar", default="2015-2026", help="orn. 2015-2026")
    p.add_argument("--n", type=int, default=1, help="1: tek kelime, 2-4: kelime gruplari")
    p.add_argument("--min-belge", type=int, default=5, help="Bir yilda bundan az ozette gecen oge atilir")
    p.add_argument("--parca", type=int, help="Her yilin sayimini kac parcaya bol (varsayilan n=1: 1, n>1: 8)")
    p.add_argument("--dergiler", help="Sadece bu dergiler (orn. dergi_paneli_tr.txt)")
    p.add_argument("--cikti")
    arg = p.parse_args()

    dergiler = dergi_filtresi(arg.dergiler)
    cikti = Path(arg.cikti or KLASOR / siklik_dosya_adi(arg.dil, arg.n))
    parca_sayisi = arg.parca or (1 if arg.n == 1 else 8)
    alan = f"ozet_{arg.dil}"
    belge_sayisi = {}

    with gzip.open(cikti, "wt", encoding="utf-8") as f:
        f.write("yil\tkelime\tbelge_sayisi\n")
        for yil in yil_araligi(arg.yillar):
            # O yilin ozetlerini bir kez oku, her ozetin ogelerini tut
            ozet_ogeleri = []
            with open(arg.girdi, encoding="utf-8") as g:
                for satir in g:
                    m = json.loads(satir)
                    if m.get("yil_guvenilir") == yil and m.get(alan) and secili(m, dergiler):
                        ozet_ogeleri.append(gruplar(m[alan], arg.dil, arg.n))
            belge_sayisi[yil] = len(ozet_ogeleri)
            farkli = tutulan = 0
            for k in range(parca_sayisi):
                sayac = Counter()
                for ogeler in ozet_ogeleri:
                    sayac.update(o for o in ogeler if parca_sayisi == 1 or parca_no(o, parca_sayisi) == k)
                farkli += len(sayac)
                for oge, adet in sayac.items():
                    if adet >= arg.min_belge:
                        f.write(f"{yil}\t{oge}\t{adet}\n")
                        tutulan += 1
            del ozet_ogeleri
            print(f"{yil}: {belge_sayisi[yil]} ozet, {farkli} farkli oge, {tutulan} tutuldu")

    Path(str(cikti) + ".belge.json").write_text(json.dumps(belge_sayisi, indent=1))
    print(f"Cikti: {cikti}")


if __name__ == "__main__":
    main()
