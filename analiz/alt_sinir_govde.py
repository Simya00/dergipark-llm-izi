#!/usr/bin/env python3
"""
Alt Sinir, Govde Duzeyi (on kayit: notlar/yontem.md §6.2, 2026-11-22)
====================================================================
"Ozetlerin EN AZ yuzde kacinda LLM izi var?" Kobak vd.'nin frekans farki:
isaretci govdelerden EN AZ BIRINI iceren ozet orani p, ayni karsi-olgusal q
(taban T-2, egilim T-3 -> T-2, iki yil ileri) ve

    alt sinir = Delta = p_T - q_T        (Kobak vd. gibi; 1 - q'ya bolunmez)

Isaretciler: elle isaretlemede Ü (uslup) denen govdeler (isaretleme Excel'i).

A) ANA SONUC, CAPRAZ (on kayit karari 1-A): secim yili S ile olcum yili M farkli.
     S = 2024 -> M = 2025  ve  S = 2025 -> M = 2024.
   Isaretci: Ü + S yilinda Kobak kuralina gore asiri + taban yilinda (2022)
   ozetlerin %10'undan azinda gecen (karar 2: X = %10; tek sabit esik, tarama yok).
C) KARSILASTIRMA, Kobak vd. ile birebir (karar 1-C): secim ve olcum AYNI yil T;
   Ü + T'de asiri govdeler, T yilindaki sikliklarina gore 11 esikle (0,0002 ... 0,5)
   gruplanir, her esik icin Delta; raporlanan en buyuk Delta ("iyimser").

Olcum, govde sayiminin makale basina sonuclarindan (govde_parcalar/, SURUM 2):
her makalenin govde kumesi. --dergiler ile panel (karar 3: kisa panel sagamlik).
Yumusatma Kobak vd. gibi (sayi + 1) / (ozet + 1).

PLASEBO (ek on kayit §6.2.1): A icin 2018-2022 komsu yil ciftleri (8 deger; taban
min(S, M) - 2), C icin T = 2018-2022 (5 deger), birebir ayni adimlar. Ana sonuc,
plasebo degerlerinin en buyugunu gecmeli.

Kullanim (analiz/ klasorunde; Zemberek gerekmez):
  python3 alt_sinir_govde.py
  python3 alt_sinir_govde.py --dergiler dergi_paneli_tr_kisa.txt
"""

import argparse
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from asiri_kullanim import oku
from govde_siklik import PARCA_KLASORU, SURUM
from kelime_siklik import dergi_filtresi

KLASOR = Path(__file__).resolve().parent
VARSAYILAN_EXCEL = KLASOR / "isaretleme_kayit" / "isaretleme_tr_govde_2026-11-26.xlsx"
TABAN_YILI, X_ESIGI = 2022, 0.10           # on kayit karari 2
KOBAK_ESIKLERI = [0.0002, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
CAPRAZ = [(2024, 2025), (2025, 2024)]      # (secim yili, olcum yili)
# PLASEBO (ek on kayit, yontem.md §6.2.1, 2026-11-28): LLM oncesi yillarda AYNI adimlar.
# Kural: ana sonuc, plasebo degerlerinin EN BUYUGUNU gecmezse "LLM izi" diye yorumlanmaz.
PLASEBO_YILLARI = range(2018, 2023)        # 2018-2022
A_PLASEBO = [c for a in range(2018, 2022) for c in ((a, a + 1), (a + 1, a))]  # komsu yillar, iki yon
ETIKET_BASLIK = "etiket (Ü/İ/B)"


def etiketleri_oku(yol):
    """govde -> (etiket, Kobak'a gore asiri oldugu yillar)."""
    from openpyxl import load_workbook
    wb = load_workbook(yol, read_only=True)
    satirlar = list(wb["isaretleme"].iter_rows(values_only=True))
    j = satirlar[0].index(ETIKET_BASLIK)
    etiket = {r[1]: str(r[j] or "").strip().upper()[:1].replace("I", "İ").replace("U", "Ü")
              for r in satirlar[1:] if r[1]}
    bilgi = list(wb["bilgi"].iter_rows(values_only=True))
    k = bilgi[0].index("asiri yillar")
    yillar = {r[1]: {int(y) for y in str(r[k]).split(",") if y.strip()} for r in bilgi[1:] if r[1]}
    return etiket, yillar


def karsi_olgusal_T(p, T):
    return p[T - 2] + 2 * max(p[T - 2] - p[T - 3], 0)


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--isaretleme", default=str(VARSAYILAN_EXCEL))
    a.add_argument("--siklik", default="siklik_tr_govde.tsv.gz", help="taban ve hedef yil sikliklari (tum veri)")
    a.add_argument("--dergiler", help="olcum yalnizca bu dergilerde (orn. dergi_paneli_tr_kisa.txt)")
    arg = a.parse_args()

    etiket, asiri_yil = etiketleri_oku(arg.isaretleme)
    uslup = {g for g, e in etiket.items() if e == "Ü"}
    belge, sayi = oku(KLASOR / arg.siklik)
    siklik = lambda g, y: sayi.get(g, {}).get(y, 0) / belge[y]  # ham oran (secim kurallari icin)

    kumeler = {}  # ad -> isaretci govde kumesi
    for S, M in CAPRAZ + A_PLASEBO:
        taban = min(S, M) - 2  # ana sonucta 2022 (= TABAN_YILI); plaseboda ayni kural
        kumeler[f"A {S}->{M}"] = {g for g in uslup if S in asiri_yil.get(g, ()) and siklik(g, taban) < X_ESIGI}
    assert all(min(S, M) - 2 == TABAN_YILI for S, M in CAPRAZ)
    for T in [*PLASEBO_YILLARI, 2024, 2025]:
        for c in KOBAK_ESIKLERI:
            kumeler[f"C {T} <{c}"] = {g for g in uslup if T in asiri_yil.get(g, ()) and siklik(g, T) < c}

    dergiler = dergi_filtresi(arg.dergiler)
    ozet, isaretli = Counter(), defaultdict(Counter)
    parcalar = sorted(PARCA_KLASORU.glob("*.json.gz"))
    if not parcalar:
        raise SystemExit(f"{PARCA_KLASORU} bos: govde sayimi (govde_siklik.py sayim) gerekli.")
    for p in parcalar:
        with gzip.open(p, "rt", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("surum") != SURUM:
            raise SystemExit(f"{p} eski bicimde.")
        for yil, dergi, govdeler, _, _ in d["makaleler"]:
            if dergiler is not None and dergi not in dergiler:
                continue
            ozet[yil] += 1
            gs = set(govdeler)
            for ad, kume in kumeler.items():
                if kume and not kume.isdisjoint(gs):
                    isaretli[ad][yil] += 1

    def oran(ad):
        return {y: (isaretli[ad][y] + 1) / (ozet[y] + 1) for y in ozet}

    print(f"Etiketler: {arg.isaretleme}\nOlcum: {'tum veri' if dergiler is None else arg.dergiler} "
          f"| ozet: " + ", ".join(f"{y}:{ozet[y]}" for y in sorted(ozet) if 2018 <= y <= 2025))
    print(f"Ü govde: {len(uslup)} | formul: Delta = p_T - q_T (Kobak vd.), q: taban T-2, egilim T-3 -> T-2\n")

    print("A) ANA SONUC — capraz secim (secim yili != olcum yili), tabanda (2022) < %10:")
    for S, M in CAPRAZ:
        ad = f"A {S}->{M}"
        p = oran(ad)
        q = karsi_olgusal_T(p, M)
        print(f"  {S}'te secilen {len(kumeler[ad])} govdeyle {M}: p = {p[M]:.4f}, q = {q:.4f}, "
              f"ALT SINIR = {p[M] - q:+.4f} ({100 * (p[M] - q):.1f}%)")
        print("    yillara gore p: " + ", ".join(f"{y}:{p[y]:.3f}" for y in sorted(p) if 2015 <= y <= 2025))
        print("    govdeler: " + ", ".join(sorted(kumeler[ad])))

    print("\nC) Kobak vd. ile birebir (ayni yil secim ve olcum; 11 esik, en buyuk Delta = iyimser):")
    for T in (2024, 2025):
        print(f"  {T}:  {'esik':>7} {'govde':>6} {'p':>7} {'q':>7} {'Delta':>7}")
        en_iyi = None
        for c in KOBAK_ESIKLERI:
            ad = f"C {T} <{c}"
            p = oran(ad)
            q = karsi_olgusal_T(p, T)
            dlt = p[T] - q
            en_iyi = max(en_iyi or (dlt, c), (dlt, c))
            print(f"       {c:>7} {len(kumeler[ad]):>6} {p[T]:>7.4f} {q:>7.4f} {dlt:>+7.4f}")
        print(f"     en buyuk Delta: {en_iyi[0]:+.4f} ({100 * en_iyi[0]:.1f}%), esik {en_iyi[1]}")

    def delta_A(S, M):
        p = oran(f"A {S}->{M}")
        return p[M] - karsi_olgusal_T(p, M)

    def delta_C(T):
        sonuc = []
        for c in KOBAK_ESIKLERI:
            p = oran(f"C {T} <{c}")
            sonuc.append((p[T] - karsi_olgusal_T(p, T), c))
        return max(sonuc)

    print("\nPLASEBO (ek on kayit §6.2.1; LLM oncesi yillarda ayni adimlar):")
    print("  A) capraz secim, komsu yillar:")
    pa = []
    for S, M in A_PLASEBO:
        d = delta_A(S, M)
        pa.append(d)
        print(f"     {S}->{M}: {len(kumeler[f'A {S}->{M}']):>4} govde  Delta = {100 * d:+.1f}%")
    print(f"     plasebo en buyuk: {100 * max(pa):+.1f}%")
    for S, M in CAPRAZ:
        d = delta_A(S, M)
        print(f"     ANA {S}->{M}: {100 * d:+.1f}%  -> {'GECIYOR' if d > max(pa) else 'GECMIYOR'}")
    print("  C) Kobak ile birebir (ayni yil, 11 esik, en buyuk Delta):")
    pc = []
    for T in PLASEBO_YILLARI:
        d, c = delta_C(T)
        pc.append(d)
        print(f"     {T}: Delta = {100 * d:+.1f}% (esik {c})")
    print(f"     plasebo en buyuk: {100 * max(pc):+.1f}%")
    for T in (2024, 2025):
        d, c = delta_C(T)
        print(f"     ANA {T}: {100 * d:+.1f}%  -> {'GECIYOR' if d > max(pc) else 'GECMIYOR'}")


if __name__ == "__main__":
    main()
