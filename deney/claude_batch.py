#!/usr/bin/env python3
"""
LLM Yeniden Yazim Deneyi: Claude, Message Batches API ile (yari fiyat)
=====================================================================
api_yeniden_yaz.py ile AYNI komutlar ve AYNI cevap alanlari; tek fark istekler
toplu (batch) gonderilir: fiyat %50 dusuk, sonuclar genellikle 1 saat icinde,
en gec 24 saatte hazir olur (Anthropic belgeleri).

  gonder : bos ornekleri toplu gonderir; batch kimligi claude_batch_kayit.json'a yazilir
  topla  : bitmis batch'lerin sonuclarini deney_ornekleri.json'a yazar
  durum  : batch'lerin ve kosullarin durumu

KALDIGI YERDEN DEVAM:
  - Her cevap deney_ornekleri.json'a yazilir; dolu alanlar bir daha gonderilmez.
  - Gonderilmis ama sonucu henuz toplanmamis ornekler tekrar gonderilmez.
  - Basarisiz / kesilmis / reddedilmis cevaplar kaydedilmez; sonraki `gonder` onlari yeniden gonderir.
  - Kredi biterse batch hata verir; o ana kadar toplananlar kayitlidir. Kredi yukleyince
    once `topla`, sonra ayni `gonder` komutu.

Kararlar (onceki deney kararlariyla ayni): her istekte tek ozet; sicaklik vb. gonderilmez
(servis varsayilani); model adi --model ile verilir ve her cevaba kaydedilir.

API ANAHTARI: koda ya da dosyaya YAZILMAZ. ANTHROPIC_API_KEY ortam degiskeninde yoksa
terminalde gorunmez olarak sorulur.

Gerekli paket: pip install anthropic

Kullanim (deney/ klasorunde):
  python3 claude_batch.py gonder --model <model> --kosul duzenle --sinir 3   # once 3 ornekle deneme
  python3 claude_batch.py topla
  python3 claude_batch.py gonder --model <model> --kosul duzenle            # kalanlar
  python3 claude_batch.py gonder --model <model> --kosul duzelt
  python3 claude_batch.py gonder --model <model> --kosul ceviri
  python3 claude_batch.py durum
"""

import argparse
import datetime as dt
import getpass
import json
import os
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
DENEY = KLASOR / "deney_ornekleri.json"
KAYIT = KLASOR / "claude_batch_kayit.json"
HAM = KLASOR / "api_ham_claude_batch.jsonl"
TABAN_ALAN = "claude"
MAX_TOKENS = 16000  # dusunme de bu sinira dahil; ozetler kisa, fazlasiyla yeter


def alan_adi(kosul):
    return TABAN_ALAN if kosul == "duzenle" else f"{TABAN_ALAN}_{kosul}"


def kaynak_alan(kosul):
    return "ozet_en" if kosul == "ceviri" else "ozet_tr"


def oku(dosya, varsayilan):
    return json.loads(dosya.read_text(encoding="utf-8")) if dosya.exists() else varsayilan


def yaz(dosya, veri):
    gecici = dosya.with_suffix(dosya.suffix + ".gecici")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    gecici.replace(dosya)  # yarim yazilmis dosya kalmasin


def istemci():
    import anthropic
    anahtar = os.environ.get("ANTHROPIC_API_KEY") or getpass.getpass(
        "ANTHROPIC_API_KEY (yapistirin, ekranda GORUNMEZ; hicbir yere kaydedilmez): ").strip()
    if not anahtar:
        raise SystemExit("Anahtar girilmedi.")
    return anthropic.Anthropic(api_key=anahtar)


def komut_bul(veri, kosul):
    if kosul != "duzenle" and kosul not in veri.get("komutlar", {}):
        raise SystemExit("Bu kosulun komutu dosyada yok. Once: python3 deney_hazirla.py --kosullar-ekle")
    return veri.get("komutlar", {}).get(kosul, veri["komut"])


def gonder(arg):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    veri, kayit = oku(DENEY, None), oku(KAYIT, [])
    komut, alan, kaynak = komut_bul(veri, arg.kosul), alan_adi(arg.kosul), kaynak_alan(arg.kosul)
    yolda = {(b["kosul"], n) for b in kayit if not b.get("toplandi") for n in b["numaralar"]}
    bekleyen = [o for o in veri["ornekler"]
                if (o.get(kaynak) or "").strip() and not o["cevaplar"].get(alan, "").strip()
                and (arg.kosul, o["no"]) not in yolda]
    if arg.sinir:
        bekleyen = bekleyen[:arg.sinir]
    print(f"Claude / {arg.model} / kosul {arg.kosul} -> cevaplar['{alan}']: {len(bekleyen)} ornek")
    if not bekleyen:
        print("Gonderilecek ornek yok (hepsi dolu ya da sonucu bekleniyor: `topla` / `durum`).")
        return
    istekler = [Request(custom_id=f"{arg.kosul}-{o['no']}",
                        params=MessageCreateParamsNonStreaming(
                            model=arg.model, max_tokens=MAX_TOKENS,
                            messages=[{"role": "user", "content": komut + o[kaynak]}]))
                for o in bekleyen]
    if arg.kuru:
        print(json.dumps(istekler[0], ensure_ascii=False, indent=1, default=str))
        return
    batch = istemci().messages.batches.create(requests=istekler)
    kayit.append({"batch_id": batch.id, "model": arg.model, "kosul": arg.kosul,
                  "numaralar": [o["no"] for o in bekleyen],
                  "gonderim": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "toplandi": False})
    yaz(KAYIT, kayit)
    print(f"Gonderildi: batch {batch.id} ({len(bekleyen)} istek). Genellikle 1 saat icinde biter, "
          f"en gec 24 saat. Sonra: python3 claude_batch.py topla")


def topla(arg):
    veri, kayit = oku(DENEY, None), oku(KAYIT, [])
    acik = [b for b in kayit if not b.get("toplandi")]
    if not acik:
        print("Toplanacak batch yok.")
        return
    c = istemci()
    no_ornek = {o["no"]: o for o in veri["ornekler"]}
    for b in acik:
        durum = c.messages.batches.retrieve(b["batch_id"])
        if durum.processing_status != "ended":
            print(f"{b['batch_id']} ({b['kosul']}): henuz bitmedi ({durum.processing_status}; "
                  f"isleniyor {durum.request_counts.processing}). Sonra yeniden `topla`.")
            continue
        alan, kaydedilen, sorunlu = alan_adi(b["kosul"]), 0, []
        with open(HAM, "a", encoding="utf-8") as ham:
            for r in c.messages.batches.results(b["batch_id"]):
                no = int(r.custom_id.rsplit("-", 1)[1])
                ham.write(json.dumps({"batch_id": b["batch_id"], "custom_id": r.custom_id,
                                      "sonuc": r.to_dict()}, ensure_ascii=False, default=str) + "\n")
                if r.result.type != "succeeded":
                    sorunlu.append(f"{no}:{r.result.type}")
                    continue
                m = r.result.message
                metin = "".join(blok.text for blok in m.content if blok.type == "text").strip()
                if m.stop_reason != "end_turn" or not metin:
                    sorunlu.append(f"{no}:{m.stop_reason}")  # kesilmis/reddedilmis: kaydedilmez
                    continue
                o = no_ornek[no]
                o["cevaplar"][alan] = metin
                o.setdefault("api", {})[alan] = {
                    "istenen_model": b["model"], "donen_model": m.model, "kosul": b["kosul"],
                    "batch_id": b["batch_id"], "zaman": b["gonderim"], "bitis": m.stop_reason,
                    "tokenlar": m.usage.to_dict()}
                kaydedilen += 1
        yaz(DENEY, veri)
        b["toplandi"] = True
        yaz(KAYIT, kayit)
        print(f"{b['batch_id']} ({b['kosul']}): {kaydedilen} cevap kaydedildi"
              + (f"; kaydedilmeyen (yeniden gonderilecek): {', '.join(sorunlu)}" if sorunlu else ""))
    durum_yaz(veri)


def durum_yaz(veri):
    for k in ("duzenle", "duzelt", "ceviri"):
        uygun = [o for o in veri["ornekler"] if (o.get(kaynak_alan(k)) or "").strip()]
        dolu = sum(1 for o in uygun if o["cevaplar"].get(alan_adi(k), "").strip())
        print(f"  claude {k:<8} cevaplar['{alan_adi(k)}']: {dolu}/{len(uygun)} dolu")


def durum(arg):
    for b in oku(KAYIT, []):
        print(f"{b['batch_id']}  {b['kosul']:<8} {len(b['numaralar']):>4} istek  {b['gonderim']}  "
              f"{'toplandi' if b.get('toplandi') else 'BEKLIYOR (topla)'}")
    durum_yaz(oku(DENEY, None))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    g = alt.add_parser("gonder")
    g.add_argument("--model", required=True, help="tam model adi (ornegin Anthropic model listesinden)")
    g.add_argument("--kosul", choices=["duzenle", "duzelt", "ceviri"], default="duzenle")
    g.add_argument("--sinir", type=int, help="yalnizca bu kadar ornek (deneme icin)")
    g.add_argument("--kuru", action="store_true", help="gondermeden ilk istegi goster")
    alt.add_parser("topla")
    alt.add_parser("durum")
    arg = p.parse_args()
    {"gonder": gonder, "topla": topla, "durum": durum}[arg.komut](arg)


if __name__ == "__main__":
    main()
