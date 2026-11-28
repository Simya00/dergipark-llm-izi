#!/usr/bin/env python3
"""
LLM Yeniden Yazim Deneyi: API ile otomatik cevap alma
=====================================================
deney_ornekleri.json'daki ozetleri, deney_yapistir.py ile AYNI komutla, API
uzerinden modele gonderir ve cevabi ayni alana (cevaplar[<alan>]) yazar.
Analiz tarafi degismez; elle yapistirma yerine gecer.

Kararlar (kullanici, 2026-11-07):
  - Her istekte TEK ozet (her ozet sifirdan bir sohbet; paket etkisi yok).
  - Komut deney_hazirla.py'deki KOMUT, degistirilmeden.
  - Sicaklik (temperature) vb. ayarlar GONDERILMEZ: servisin varsayilani
    kullanilir (siradan kullaniciya en yakin; Claude'un onerisi).
  - Her ozet 1 kez.
  - Model adi kodda YAZILI DEGIL: her calistirmada --model ile tam surum adi
    verilir ve ozete kaydedilir (makalede raporlanir).

KOSULLAR (2026-11-28; dis degerlendirme onerisi; komutlar deney_ornekleri.json "komutlar"):
  --kosul duzenle : (varsayilan) eski KOMUT ile Turkce ozet  -> cevaplar[<alan>]
  --kosul duzelt  : notr komut (yalnizca yazim/dil bilgisi)   -> cevaplar[<alan>_duzelt]
  --kosul ceviri  : ayni makalenin INGILIZCE ozeti -> Turkceye -> cevaplar[<alan>_ceviri]
  (once: python3 deney_hazirla.py --kosullar-ekle)

KALDIGI YERDEN DEVAM: her cevap gelir gelmez dosyaya kaydedilir; dolu alanlar atlanir.
Kredi/kota biterse ya da hata olursa program durur, o ana kadarkiler kayitlidir;
ayni komutu sonra yeniden calistirmak yeter. Durum: --durum

API ANAHTARI hicbir dosyaya yazilmaz, koda yazilmaz. Ortam degiskeninde yoksa
terminalde GORUNMEZ olarak sorulur (yapistirip Enter):
  OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY

Kayitlar:
  - cevaplar[<alan>]        : modelin metni (analizin kullandigi alan)
  - api[<alan>]             : istenen ve donen model adi, tarih, bitis nedeni, token sayilari
  - api_ham_<alan>.jsonl    : her istegin ham cevabi (sonradan inceleme icin)

Yarida kesilirse (Ctrl+C, hata) yeniden calistirin: dolu ornekler atlanir.

Kullanim:
  export OPENAI_API_KEY=...        # anahtari sohbete/dosyaya YAZMAYIN
  python3 api_yeniden_yaz.py openai --model <tam-surum-adi> --sinir 3   # once 3 ornekle deneme
  python3 api_yeniden_yaz.py openai --model <tam-surum-adi>
  python3 api_yeniden_yaz.py gemini --model <tam-surum-adi>
  python3 api_yeniden_yaz.py anthropic --model <tam-surum-adi>
  python3 api_yeniden_yaz.py openai --model x --kuru      # hicbir sey gondermeden ilk istegi goster
"""

import argparse
import datetime as dt
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KLASOR = Path(__file__).resolve().parent

# saglayici -> (cevap alani, anahtar degiskeni, istekler arasi bekleme sn)
SAGLAYICILAR = {
    "openai": ("chatgpt", "OPENAI_API_KEY", 1.0),
    "gemini": ("gemini", "GEMINI_API_KEY", 13.0),  # ucretsiz katman Flash: dakikada 5 istek (AI Studio, 2026-11-28)
    "anthropic": ("claude", "ANTHROPIC_API_KEY", 1.0),
}
TEKRAR_EN_FAZLA = 5          # 429 / 5xx hatalarinda en fazla deneme
ANTHROPIC_MAX_TOKENS = 4096  # Anthropic API'de zorunlu alan; ozetler ~1500 karakter, fazlasiyla yeter


# ------------------------------------------------------------------
# Saglayiciya gore istek ve cevap
# ------------------------------------------------------------------

def istek_hazirla(saglayici, model, metin, anahtar):
    """(url, basliklar, govde) dondurur. Anahtar URL'ye DEGIL basliga konur (hata mesajlarinda gorunmesin)."""
    if saglayici == "openai":
        return ("https://api.openai.com/v1/chat/completions",
                {"Authorization": f"Bearer {anahtar}"},
                {"model": model, "messages": [{"role": "user", "content": metin}]})
    if saglayici == "gemini":
        return (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"x-goog-api-key": anahtar},
                {"contents": [{"role": "user", "parts": [{"text": metin}]}]})
    if saglayici == "anthropic":
        return ("https://api.anthropic.com/v1/messages",
                {"x-api-key": anahtar, "anthropic-version": "2023-06-01"},
                {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS,
                 "messages": [{"role": "user", "content": metin}]})
    raise ValueError(saglayici)


def cevap_ayikla(saglayici, ham):
    """(metin, donen_model, bitis_nedeni, tamam_mi, tokenlar) dondurur."""
    if saglayici == "openai":
        c = ham["choices"][0]
        neden = c.get("finish_reason")
        return (c["message"].get("content") or "", ham.get("model"), neden, neden == "stop", ham.get("usage"))
    if saglayici == "gemini":
        c = ham["candidates"][0]
        neden = c.get("finishReason")
        # dusunme (thought) parcalari cevaba dahil edilmez
        metin = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []) if not p.get("thought"))
        return (metin, ham.get("modelVersion"), neden, neden == "STOP", ham.get("usageMetadata"))
    if saglayici == "anthropic":
        neden = ham.get("stop_reason")
        metin = "".join(b.get("text", "") for b in ham.get("content", []) if b.get("type") == "text")
        return (metin, ham.get("model"), neden, neden == "end_turn", ham.get("usage"))
    raise ValueError(saglayici)


def gonder(url, basliklar, govde):
    """POST; 429 ve 5xx'te bekleyip tekrar dener. Basarisizsa RuntimeError."""
    veri = json.dumps(govde, ensure_ascii=False).encode("utf-8")
    for deneme in range(1, TEKRAR_EN_FAZLA + 1):
        req = urllib.request.Request(url, data=veri, method="POST",
                                     headers={"Content-Type": "application/json", **basliklar})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as h:
            tam_govde = h.read().decode("utf-8", "replace")
            govde_metni = tam_govde[:500]
            if h.code == 429 and "PerDay" in tam_govde:
                # GUNLUK kota doldu: beklemek ise yaramaz, hemen dur (ertesi gun ayni komut)
                raise RuntimeError(f"GUNLUK KOTA DOLDU (HTTP 429). Ertesi gun ayni komutla devam edin. {govde_metni[:200]}")
            if h.code == 429 or h.code >= 500:
                bekle = 2 ** deneme * 5
                print(f"  HTTP {h.code} (sinir/sunucu), {bekle} sn bekleniyor ({deneme}/{TEKRAR_EN_FAZLA})")
                time.sleep(bekle)
                continue
            raise RuntimeError(f"HTTP {h.code}: {govde_metni}")
        except (urllib.error.URLError, TimeoutError) as h:
            bekle = 2 ** deneme * 5
            print(f"  Baglanti hatasi ({h}), {bekle} sn bekleniyor ({deneme}/{TEKRAR_EN_FAZLA})")
            time.sleep(bekle)
    raise RuntimeError("Tekrar sayisi doldu")


# ------------------------------------------------------------------

def kaydet(dosya, veri):
    gecici = dosya.with_suffix(".json.gecici")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    gecici.replace(dosya)  # yarim yazilmis dosya kalmasin


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("saglayici", choices=sorted(SAGLAYICILAR))
    p.add_argument("--model", help="tam model surum adi (saglayicinin listesinden); --durum disinda zorunlu")
    p.add_argument("--kosul", choices=["duzenle", "duzelt", "ceviri"], default="duzenle")
    p.add_argument("--durum", action="store_true", help="hicbir sey gonderme; her kosulda kac cevap dolu, yaz")
    p.add_argument("--sinir", type=int, help="yalnizca bu kadar bos ornegi doldur (deneme icin)")
    p.add_argument("--kuru", action="store_true", help="hicbir sey gonderme; ilk istegi ekrana bas")
    p.add_argument("--bekle", type=float, help="istekler arasi bekleme (sn); varsayilan saglayiciya gore")
    p.add_argument("--dosya", default=str(KLASOR / "deney_ornekleri.json"))
    arg = p.parse_args()

    taban_alan, anahtar_adi, bekleme = SAGLAYICILAR[arg.saglayici]
    if arg.bekle is not None:
        bekleme = arg.bekle
    dosya = Path(arg.dosya)
    veri = json.loads(dosya.read_text(encoding="utf-8"))
    if taban_alan not in veri["modeller"]:
        raise SystemExit(f"'{taban_alan}' alani deney dosyasinda yok (modeller: {veri['modeller']})")

    def alan_adi(kosul):
        return taban_alan if kosul == "duzenle" else f"{taban_alan}_{kosul}"

    def kaynak_alan(kosul):
        return "ozet_en" if kosul == "ceviri" else "ozet_tr"

    if arg.durum:
        for k in ("duzenle", "duzelt", "ceviri"):
            uygun = [o for o in veri["ornekler"] if (o.get(kaynak_alan(k)) or "").strip()]
            dolu = sum(1 for o in uygun if o["cevaplar"].get(alan_adi(k), "").strip())
            print(f"  {arg.saglayici:<9} {k:<8} cevaplar['{alan_adi(k)}']: {dolu}/{len(uygun)} dolu")
        return
    if not arg.model:
        raise SystemExit("--model gerekli (tam surum adi).")
    if arg.kosul != "duzenle" and arg.kosul not in veri.get("komutlar", {}):
        raise SystemExit("Bu kosulun komutu dosyada yok. Once: python3 deney_hazirla.py --kosullar-ekle")
    komut = veri.get("komutlar", {}).get(arg.kosul, veri["komut"])
    alan, kaynak = alan_adi(arg.kosul), kaynak_alan(arg.kosul)
    bekleyen = [o for o in veri["ornekler"]
                if (o.get(kaynak) or "").strip() and not o["cevaplar"].get(alan, "").strip()]
    if arg.sinir:
        bekleyen = bekleyen[:arg.sinir]
    print(f"{arg.saglayici} / {arg.model} / kosul {arg.kosul} -> cevaplar['{alan}']: "
          f"{len(bekleyen)} ornek gonderilecek")

    if arg.kuru:
        if bekleyen:
            url, _, govde = istek_hazirla(arg.saglayici, arg.model, komut + bekleyen[0][kaynak], "GIZLI")
            print(url)
            print(json.dumps(govde, ensure_ascii=False, indent=1))
        return
    if not bekleyen:
        print("Gonderilecek ornek kalmadi.")
        return

    anahtar = os.environ.get(anahtar_adi) or getpass.getpass(
        f"{anahtar_adi} (yapistirin, ekranda GORUNMEZ; hicbir yere kaydedilmez): ").strip()
    if not anahtar:
        raise SystemExit("Anahtar girilmedi.")

    ham_dosya = KLASOR / f"api_ham_{alan}.jsonl"
    tamam = 0
    for i, o in enumerate(bekleyen, 1):
        metin = komut + o[kaynak]
        url, basliklar, govde = istek_hazirla(arg.saglayici, arg.model, metin, anahtar)
        try:
            ham = gonder(url, basliklar, govde)
        except RuntimeError as h:
            print(f"  ornek {o['no']}: HATA, duruldu: {h}")
            print("  (Kredi/kota bitmis ya da anahtar hatali olabilir. Simdiye kadarki cevaplar KAYITLI;\n"
                  "   sorun giderilince AYNI komutu yeniden calistirin, kaldigi yerden devam eder.)")
            break
        except KeyboardInterrupt:
            print("\n  Durduruldu (Ctrl+C). Simdiye kadarki cevaplar kayitli; ayni komutla devam edin.")
            break
        zaman = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        with open(ham_dosya, "a", encoding="utf-8") as f:
            f.write(json.dumps({"no": o["no"], "zaman": zaman, "istenen_model": arg.model, "ham": ham},
                               ensure_ascii=False) + "\n")
        cevap, donen_model, neden, bitti, tokenlar = cevap_ayikla(arg.saglayici, ham)
        if not bitti or not cevap.strip():
            # kesilmis ya da bos cevap analize girmesin; ham kayitta duruyor, sonra tekrar sorulur
            print(f"  ornek {o['no']}: KAYDEDILMEDI (bitis nedeni: {neden}, {len(cevap)} karakter)")
        else:
            o["cevaplar"][alan] = cevap.strip()
            o.setdefault("api", {})[alan] = {"istenen_model": arg.model, "donen_model": donen_model, "kosul": arg.kosul,
                                             "zaman": zaman, "bitis": neden, "tokenlar": tokenlar}
            kaydet(dosya, veri)
            tamam += 1
            print(f"  [{i}/{len(bekleyen)}] ornek {o['no']}: {len(o[kaynak])} -> {len(cevap)} karakter")
        time.sleep(bekleme)

    uygun = [o for o in veri["ornekler"] if (o.get(kaynak) or "").strip()]
    dolu = sum(1 for o in uygun if o["cevaplar"].get(alan, "").strip())
    print(f"\nBu calistirmada {tamam} cevap kaydedildi; '{alan}' toplam {dolu}/{len(uygun)}.")
    surumler = sorted({o.get("api", {}).get(alan, {}).get("donen_model") for o in veri["ornekler"]} - {None})
    if surumler:
        print(f"Donen model surum(ler)i (README'ye yazin): {', '.join(surumler)}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDurduruldu (Ctrl+C). Simdiye kadarki cevaplar kayitli; ayni komutla devam edin.")
