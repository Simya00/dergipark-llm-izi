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

Anahtarlar ortam degiskeninden okunur, hicbir dosyaya yazilmaz:
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
    "gemini": ("gemini", "GEMINI_API_KEY", 6.5),   # ucretsiz katman: dakikada ~10 istek
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
            govde_metni = h.read().decode("utf-8", "replace")[:500]
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
    p.add_argument("--model", required=True, help="tam model surum adi (saglayicinin listesinden)")
    p.add_argument("--sinir", type=int, help="yalnizca bu kadar bos ornegi doldur (deneme icin)")
    p.add_argument("--kuru", action="store_true", help="hicbir sey gonderme; ilk istegi ekrana bas")
    p.add_argument("--dosya", default=str(KLASOR / "deney_ornekleri.json"))
    arg = p.parse_args()

    alan, anahtar_adi, bekleme = SAGLAYICILAR[arg.saglayici]
    dosya = Path(arg.dosya)
    veri = json.loads(dosya.read_text(encoding="utf-8"))
    if alan not in veri["modeller"]:
        raise SystemExit(f"'{alan}' alani deney dosyasinda yok (modeller: {veri['modeller']})")
    bekleyen = [o for o in veri["ornekler"] if not o["cevaplar"].get(alan, "").strip()]
    if arg.sinir:
        bekleyen = bekleyen[:arg.sinir]
    print(f"{arg.saglayici} / {arg.model} -> cevaplar['{alan}']: {len(bekleyen)} ornek gonderilecek")

    if arg.kuru:
        if bekleyen:
            url, _, govde = istek_hazirla(arg.saglayici, arg.model, veri["komut"] + bekleyen[0]["ozet_tr"], "GIZLI")
            print(url)
            print(json.dumps(govde, ensure_ascii=False, indent=1))
        return

    anahtar = os.environ.get(anahtar_adi)
    if not anahtar:
        raise SystemExit(f"{anahtar_adi} ortam degiskeni tanimli degil (export {anahtar_adi}=...)")

    ham_dosya = KLASOR / f"api_ham_{alan}.jsonl"
    tamam = 0
    for i, o in enumerate(bekleyen, 1):
        metin = veri["komut"] + o["ozet_tr"]
        url, basliklar, govde = istek_hazirla(arg.saglayici, arg.model, metin, anahtar)
        try:
            ham = gonder(url, basliklar, govde)
        except RuntimeError as h:
            print(f"  ornek {o['no']}: HATA, duruldu: {h}")
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
            o.setdefault("api", {})[alan] = {"istenen_model": arg.model, "donen_model": donen_model,
                                             "zaman": zaman, "bitis": neden, "tokenlar": tokenlar}
            kaydet(dosya, veri)
            tamam += 1
            print(f"  [{i}/{len(bekleyen)}] ornek {o['no']}: {len(o['ozet_tr'])} -> {len(cevap)} karakter")
        time.sleep(bekleme)

    dolu = sum(1 for o in veri["ornekler"] if o["cevaplar"].get(alan, "").strip())
    print(f"\nBu calistirmada {tamam} cevap kaydedildi; '{alan}' toplam {dolu}/{len(veri['ornekler'])}.")
    surumler = sorted({o.get("api", {}).get(alan, {}).get("donen_model") for o in veri["ornekler"]} - {None})
    if surumler:
        print(f"Donen model surum(ler)i (README'ye yazin): {', '.join(surumler)}")


if __name__ == "__main__":
    sys.exit(main())
