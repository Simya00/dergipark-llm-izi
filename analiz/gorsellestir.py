#!/usr/bin/env python3
"""
Sonuclarin Gorsellestirilmesi (pandas + matplotlib)
===================================================
Iki grafik ciziyor; ikisi de yalnizca var olan cikti dosyalarini OKUR, hicbir
seyi yeniden hesaplamaz ve degistirmez.

1) egilim : Secilen kelimelerin yillara gore "gectigi ozet orani" (%).
            Kaynak: kelime_siklik.py ciktisi (siklik_<dil>.tsv.gz + .belge.json).
            Her kelime kendi kucuk panelinde (kelimelerin sikliklari cok farkli;
            tek eksende kucukler gorunmez olur). Panelde:
              - mavi cizgi  : gerceklesen oran p_y
              - gri kesikli : LLM olmasaydi beklenen (karsi-olgusal q, Kobak vd.)
              - dikey cizgi : ChatGPT'nin cikisi (Kasim 2022)
2) asiri  : Hedef yilda en cok "fazla" kullanilan kelimeler.
            Kaynak: asiri_kullanim.py ciktisi (asiri_<dil>_<hedef>.tsv).
            Her kelime icin iki nokta: gri = beklenen (q), mavi = gerceklesen (p);
            aradaki cizgi = fark (delta).
3) dagilim: Histogram. Hedef yilda >= 30 ozette gecen TUM kelimelerin "kac kat"
            (oran = p / q) dagilimi, log2 olcekte (x1 = degisim yok, x2 = iki kat).
            Kelimelerin cogu x1 civarinda toplanir; LLM isaretcileri saga, kuyruga
            dusmeli. --liste verilirse listedeki kelimeler turuncu cizgilerle
            isaretlenir (nerede durduklari gorulsun).

Kullanim:
  python3 gorsellestir.py egilim --dil tr --liste aday_liste_tr.txt
  python3 gorsellestir.py egilim --dil tr --kelimeler kapsamlı,kritik,derinlemesine
  python3 gorsellestir.py asiri --dil tr --hedef 2024 --ilk 30
  python3 gorsellestir.py dagilim --dil tr --hedef 2024 --liste aday_liste_tr.txt
Grafikler: analiz/grafikler/*.png (makale icin 300 dpi)

Kurulum (gerekirse, Fedora):
  sudo dnf install python3-pandas python3-matplotlib
"""

import argparse
import json
from pathlib import Path

try:
    import pandas as pd
    import matplotlib
    matplotlib.use("Agg")  # ekran acmadan dosyaya ciz
    import matplotlib.pyplot as plt
except ImportError as h:
    raise SystemExit(f"Eksik paket: {h.name}. Kurulum: sudo dnf install python3-pandas python3-matplotlib")

KLASOR = Path(__file__).resolve().parent
GRAFIK_KLASORU = KLASOR / "grafikler"

# Renkler (dataviz referans paleti, acik tema): tek seri = 1. kategorik renk
MAVI = "#2a78d6"       # gerceklesen
TURUNCU = "#eb6834"    # 2. kategorik renk: listedeki kelimeler (histogram)
GRI = "#8a8985"        # beklenen (karsi-olgusal) ve yardimci cizgiler
YAZI = "#0b0b0b"
YAZI_IKINCIL = "#52514e"
IZGARA = "#e6e5e0"
CHATGPT_YIL = 2022 + 11 / 12  # 30 Kasim 2022 ~ 2022.92

plt.rcParams.update({
    "font.family": "DejaVu Sans",  # Turkce harfleri eksiksiz gosterir
    "font.size": 9, "axes.edgecolor": IZGARA, "axes.labelcolor": YAZI_IKINCIL,
    "xtick.color": YAZI_IKINCIL, "ytick.color": YAZI_IKINCIL, "text.color": YAZI,
    "axes.spines.top": False, "axes.spines.right": False,
})


# ------------------------------------------------------------------
# Veri okuma
# ------------------------------------------------------------------

# Ek zincirlerinin okunur adlari (Zemberek kimlikleri -> Turkce ek kalibi)
ZINCIR_ADI = {
    "Prog2+A3sg+Cop": "-mAktAdIr (incelemektedir)",
    "Pass+Prog2+A3sg+Cop": "edilgen -mAktAdIr (incelenmektedir)",
    "Pass+Narr+A3sg+Cop": "edilgen -mIştIr (incelenmiştir)",
    "Narr+A3sg+Cop": "-mIştIr (incelemiştir)",
    "Pass+Narr+A3sg": "edilgen -mIş (incelenmiş)",
    "Past+A3sg": "-DI (inceledi)",
    "Pass+Past+A3sg": "edilgen -DI (incelendi)",
    "Prog1+A3sg": "-Iyor (inceliyor)",
    "Aor+A3sg": "geniş zaman (inceler)",
}


def oranlar_tablosu(dil, n=1, siklik=None):
    """Satir = kelime, sutun = yil, deger = o yil kelimenin gectigi ozet orani (0-1)."""
    ad = siklik or (f"siklik_{dil}.tsv.gz" if n == 1 else f"siklik_{dil}_{n}gram.tsv.gz")
    yol = Path(ad) if Path(ad).is_absolute() else KLASOR / ad
    if not yol.exists():
        raise SystemExit(f"{yol} yok. Once: python3 kelime_siklik.py --dil {dil}")
    sayilar = pd.read_csv(yol, sep="\t", dtype={"kelime": str}, keep_default_na=False)
    belge = pd.Series({int(y): n for y, n in json.loads(Path(str(yol) + ".belge.json").read_text()).items()})
    tablo = sayilar.pivot_table(index="kelime", columns="yil", values="belge_sayisi", fill_value=0)
    return tablo.div(belge[tablo.columns], axis=1)  # sayi / o yilin ozet sayisi


def liste_oku(dosya):
    """Aday listesinden TEK KELIMELERI alir (# yorum ve bos satirlar, kelime gruplari atlanir)."""
    kelimeler = []
    for satir in Path(dosya).read_text(encoding="utf-8").splitlines():
        s = satir.split("#")[0].strip()
        if s and " " not in s:
            kelimeler.append(s)
    return kelimeler


def karsi_olgusal(seri, taban, yillar):
    """Kobak vd.: q_T = p_b + (T-b) * max(p_b - p_{b-1}, 0). Taban yilindan itibaren."""
    egim = max(seri.get(taban, 0) - seri.get(taban - 1, 0), 0)
    return pd.Series({y: seri.get(taban, 0) + (y - taban) * egim for y in yillar if y >= taban})


# ------------------------------------------------------------------
# 1) Egilim grafigi (kucuk paneller)
# ------------------------------------------------------------------

def egilim(arg):
    tablo = oranlar_tablosu(arg.dil, arg.n, arg.siklik)
    yillar = [y for y in tablo.columns if arg.ilk_yil <= y <= arg.son_yil]
    tablo = tablo[yillar]
    istenen = liste_oku(arg.liste) if arg.liste else [k.strip() for k in arg.kelimeler.split(",")]
    bulunan = [k for k in istenen if k in tablo.index]
    eksik = [k for k in istenen if k not in tablo.index]
    if eksik:
        print(f"Veride hic (ya da yilda <5 ozette) gecmeyen {len(eksik)} kelime atlandi: {', '.join(eksik)}")
    if not bulunan:
        raise SystemExit("Cizilecek kelime yok.")

    # Paneller hedef yildaki farka (delta) gore siralanir: en cok artan ustte-solda
    def fark(k):
        q = karsi_olgusal(tablo.loc[k], arg.taban, yillar)
        return tablo.loc[k].get(arg.hedef, 0) - q.get(arg.hedef, 0)
    if arg.siralama == "fark":
        bulunan.sort(key=fark, reverse=True)
    bulunan = bulunan[:arg.en_fazla]

    sutun = min(4, len(bulunan))  # az panel varsa bos yer kalmasin
    satir = -(-len(bulunan) // sutun)  # yukari yuvarlama
    fig, eksenler = plt.subplots(satir, sutun, figsize=(sutun * 2.6, satir * 2.0), squeeze=False, sharex=True)
    for ax, kelime in zip(eksenler.flat, bulunan):
        seri = tablo.loc[kelime] * 100  # yuzde
        q = karsi_olgusal(seri, arg.taban, yillar)
        ax.axvline(CHATGPT_YIL, color=GRI, linewidth=1, linestyle=":")
        ax.plot(q.index, q.values, color=GRI, linewidth=1.5, linestyle="--")
        ax.plot(seri.index, seri.values, color=MAVI, linewidth=2, marker="o", markersize=3)
        ax.set_title(ZINCIR_ADI.get(kelime, kelime), fontsize=10, loc="left", color=YAZI)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", color=IZGARA, linewidth=0.6)
        ax.tick_params(length=0)
        ax.yaxis.set_major_formatter(lambda v, _: f"%{v:g}")
        ax.set_xticks([y for y in yillar if (y - yillar[0]) % 3 == 0])  # tam yillar (2015.0 / 2017.5 degil)
        ax.xaxis.set_major_formatter(lambda v, _: f"{int(v)}")
    for ax in list(eksenler.flat)[len(bulunan):]:
        ax.set_visible(False)

    tur = "Ek kalıplarının" if arg.siklik and "_ek" in str(arg.siklik) else "Kelimelerin"
    fig.suptitle(f"{tur} geçtiği özet oranı ({arg.dil.upper()}, {yillar[0]}–{yillar[-1]})",
                 x=0.01, ha="left", fontsize=11)
    fig.text(0.01, 0.005, "Mavi: gerçekleşen   Gri kesikli: LLM olmasaydı beklenen (Kobak vd., taban "
             f"{arg.taban - 1}–{arg.taban})   Noktalı dikey: ChatGPT (Kasım 2022)",
             fontsize=8, color=YAZI_IKINCIL)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    kaydet(fig, arg.cikti or f"egilim_{arg.dil}.png")


# ------------------------------------------------------------------
# 2) Asiri kullanim grafigi (beklenen - gerceklesen noktalari)
# ------------------------------------------------------------------

def asiri(arg):
    yol = KLASOR / (f"asiri_{arg.dil}_{arg.hedef}.tsv" if arg.n == 1 else f"asiri_{arg.dil}_{arg.n}gram_{arg.hedef}.tsv")
    if not yol.exists():
        raise SystemExit(f"{yol} yok. Once: python3 asiri_kullanim.py --dil {arg.dil} --hedef {arg.hedef}")
    df = pd.read_csv(yol, sep="\t", dtype={"kelime": str}, keep_default_na=False)
    if "asiri" in df.columns:  # Kobak vd. kuralina gore asiri kelimeler (2026-11-11)
        df = df[df["asiri"] == 1]
    df = df.sort_values("delta", ascending=False).head(arg.ilk).iloc[::-1]  # en buyuk en ustte
    p, q = df["p"] * 100, df["q"] * 100

    fig, ax = plt.subplots(figsize=(7, 0.28 * len(df) + 1.2))
    y = range(len(df))
    ax.hlines(y, q, p, color=IZGARA, linewidth=2)
    ax.scatter(q, y, color=GRI, s=30, zorder=3, label="LLM olmasaydı beklenen (q)")
    ax.scatter(p, y, color=MAVI, s=30, zorder=3, label=f"{arg.hedef}'te gerçekleşen (p)")
    ax.set_yticks(list(y), df["kelime"])
    ax.xaxis.set_major_formatter(lambda v, _: f"%{v:g}")
    ax.set_xlabel("Kelimenin geçtiği özet oranı")
    ax.grid(axis="x", color=IZGARA, linewidth=0.6)
    ax.tick_params(length=0)
    ax.set_title(f"{arg.hedef}'te beklenenden en çok fazla kullanılan {len(df)} kelime ({arg.dil.upper()})",
                 loc="left", fontsize=11)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    kaydet(fig, arg.cikti or f"asiri_{arg.dil}_{arg.hedef}.png")


# ------------------------------------------------------------------
# 3) Dagilim (histogram): tum kelimelerin "kac kat" degeri
# ------------------------------------------------------------------

def dagilim(arg):
    import numpy as np
    yol = KLASOR / (f"asiri_{arg.dil}_{arg.hedef}.tsv" if arg.n == 1 else f"asiri_{arg.dil}_{arg.n}gram_{arg.hedef}.tsv")
    if not yol.exists():
        raise SystemExit(f"{yol} yok. Once: python3 asiri_kullanim.py --dil {arg.dil} --hedef {arg.hedef}")
    df = pd.read_csv(yol, sep="\t", dtype={"kelime": str}, keep_default_na=False)
    log_oran = np.log2(df["oran"].clip(lower=1 / 64, upper=64))  # cok uc degerler kenarda toplanir

    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.hist(log_oran, bins=arg.kutu, color=MAVI, edgecolor="white", linewidth=0.5,
            label=f"tüm kelimeler (n = {len(df):,})".replace(",", "."))
    ax.axvline(0, color=GRI, linewidth=1, linestyle=":")  # x1: degisim yok
    if arg.liste:
        liste = set(liste_oku(arg.liste))
        secili = df[df["kelime"].isin(liste)]
        # alt kenarda kisa cizgiler ("hali" isareti): cubuklari ortmeden yerlerini gosterir
        ax.vlines(np.log2(secili["oran"].clip(lower=1 / 64, upper=64)), 0, 0.12,
                  transform=ax.get_xaxis_transform(), color=TURUNCU, linewidth=1.5,
                  label=f"aday listedeki kelimeler (n = {len(secili)})")
        ust = len(df[df["oran"] > secili["oran"].median()]) if len(secili) else 0
        print(f"Listeden {len(secili)}/{len(liste)} kelime veride (hedef yilda >= 30 ozet). "
              f"Liste medyani: x{secili['oran'].median():.2f}; tum kelimelerin "
              f"%{100 * ust / len(df):.1f}'i bundan buyuk.")
    ax.set_yscale("log")  # cogu kelime ortada; kuyruktaki az sayida kelime de gorunsun
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:g}")
    alt, ust = int(np.floor(log_oran.min())), int(np.ceil(log_oran.max()))  # yalnizca verinin araligi
    ax.set_xlim(alt - 0.2, ust + 0.2)
    ax.set_xticks(range(alt, ust + 1), [f"×{2 ** k}" if k >= 0 else f"×1/{2 ** -k}" for k in range(alt, ust + 1)])
    ax.set_xlabel(f"{arg.hedef}'te gerçekleşen / beklenen (kaç kat)")
    ax.set_ylabel("kelime sayısı (log ölçek)")
    ax.grid(axis="y", color=IZGARA, linewidth=0.6)
    ax.tick_params(length=0)
    ax.set_title(f"Kelimelerin {arg.hedef}'teki değişim dağılımı ({arg.dil.upper()})", loc="left", fontsize=11)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    fig.tight_layout()
    kaydet(fig, arg.cikti or f"dagilim_{arg.dil}_{arg.hedef}.png")


def kaydet(fig, ad):
    GRAFIK_KLASORU.mkdir(exist_ok=True)
    yol = GRAFIK_KLASORU / ad
    fig.savefig(yol, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"Grafik -> {yol}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    for ad in ("egilim", "asiri", "dagilim"):
        a = alt.add_parser(ad)
        a.add_argument("--dil", choices=["tr", "en"], required=True)
        a.add_argument("--n", type=int, default=1, help="1: tek kelime, 2-4: kelime gruplari")
        a.add_argument("--hedef", type=int, default=2024)
        a.add_argument("--cikti", help="dosya adi (grafikler/ klasorune)")
    e = alt.choices["egilim"]
    grup = e.add_mutually_exclusive_group(required=True)
    grup.add_argument("--liste", help="aday listesi dosyasi (orn. aday_liste_tr.txt)")
    grup.add_argument("--kelimeler", help="virgulle ayrilmis kelimeler")
    e.add_argument("--taban", type=int, default=2022)
    e.add_argument("--siklik", help="baska sayim dosyasi, orn. siklik_tr_govde.tsv.gz / siklik_tr_ekzinciri.tsv.gz")
    e.add_argument("--siralama", choices=["fark", "verilen"], default="fark",
                   help="paneller hedef yildaki farka gore mi, verilen sirada mi")
    e.add_argument("--ilk-yil", type=int, default=2015)
    e.add_argument("--son-yil", type=int, default=2025, help="2026 eksik yil oldugu icin varsayilan 2025")
    e.add_argument("--en-fazla", type=int, default=16, help="en cok kac panel")
    alt.choices["asiri"].add_argument("--ilk", type=int, default=30, help="en cok artan kac kelime")
    d = alt.choices["dagilim"]
    d.add_argument("--liste", help="isaretlenecek aday listesi (orn. aday_liste_tr.txt)")
    d.add_argument("--kutu", type=int, default=60, help="histogram kutu (cubuk) sayisi")
    arg = p.parse_args()
    {"egilim": egilim, "asiri": asiri, "dagilim": dagilim}[arg.komut](arg)


if __name__ == "__main__":
    main()
