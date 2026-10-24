#!/usr/bin/env python3
"""
DergiPark OAI Ayristirici
=========================
oai_topla.py'nin indirdigi ham XML sayfalarini (ham/*/sayfa_*.xml.gz) okur,
makale basina bir satir olacak sekilde makaleler.jsonl dosyasina yazar ve
kisa bir ozet rapor basar (yillara gore makale sayisi, TR/EN oz orani).

Her satirdaki alanlar:
  oai_id, setler, url, doi, tarihler, yil, dil, tur, dergi, yayinci,
  anahtar_kelimeler, basliklar, ozler (tum dc:description'lar, dil etiketiyle),
  ozet_tr, ozet_en (ozler icinden secilen Turkce / Ingilizce oz)

  cilt, sayi (dc:source'taki "Vol. X No. Y"), arsiv, yil_guvenilir

ARSIV TESPITI: Bir dergi DergiPark'a gectiginde eski arsivini toplu yuklemis;
bu makalelerin dc:date'i YAYIN degil YUKLEME tarihi (orn. ogusbd Cilt 10:
gercekte 2009, dc:date "2014"; ogummf Cilt 10: gercekte 1997, dc:date "2017").
Yili cilt numarasindan tahmin etmek guvenilir degil (ogummf her yil duzenli
cilt cikarmamis), bu yuzden arsiv makalelerine yil UYDURULMAZ:
  1. Ayni dergide ayni tarihte >= TOPLU_ESIK farkli cilt varsa o tarih bir
     toplu yukleme tarihidir.
  2. Bu tarihlerdeki makaleler ve cildi, toplu yuklenen en buyuk cilde esit
     veya kucuk olan makaleler "arsiv" sayilir.
  3. yil_guvenilir = arsiv degilse dc:date yili, arsivse None (analiz disi).

Oz dili: once xml:lang etiketine bakilir; yoksa basit bir sezgisel dil
tespiti yapilir (Turkceye ozgu harfler + sik gecen ilgec/baglaclar).
dil_kaynagi alani hangisinin kullanildigini soyler ("etiket" / "tahmin").

Kullanim:
  python3 oai_ayristir.py                  # ham/ altindaki her seyi ayristir
  python3 oai_ayristir.py --ham ham/ogummf --cikti ogummf.jsonl
  python3 oai_ayristir.py --dosya deneme_ornek.xml --cikti deneme.jsonl
"""

import argparse
import gzip
import html
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from oai_topla import xml_coz

KLASOR = Path(__file__).resolve().parent
NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
CILT_SAYI = re.compile(r"Vol\.?\s*(\d+)(?:\s*No\.?\s*([\w-]+))?", re.IGNORECASE)
TOPLU_ESIK = 3  # ayni gun bu kadar farkli cilt -> toplu yukleme
DC = "{" + NS["dc"] + "}"

# ------------------------------------------------------------------
# Sezgisel dil tespiti
# ------------------------------------------------------------------
TR_HARFLER = set("ğışĞİŞ")  # ç/ö/ü baska dillerde de var, bunlar degil
TR_KELIMELER = {"ve", "bir", "bu", "ile", "için", "olarak", "olan", "da", "de",
                "çalışmada", "çalışmanın", "amacı", "sonuç", "sonuçlar", "göre",
                "ise", "daha", "veya", "ancak", "arasında", "üzerine", "yöntem"}
EN_KELIMELER = {"the", "and", "of", "in", "to", "is", "was", "were", "this",
                "that", "with", "for", "study", "results", "are", "by", "on",
                "an", "as", "which", "from"}
KELIME = re.compile(r"\w+", re.UNICODE)


def turkce_kucult(metin: str) -> str:
    # Python'un .lower() metodu 'İ'yi yanlis donusturuyor (bkz. birlesik_analiz.py)
    return metin.replace("İ", "i").replace("I", "ı").lower()


def dil_tahmin(metin: str) -> str:
    kelimeler = KELIME.findall(turkce_kucult(metin))
    if len(kelimeler) < 5:
        return "bilinmiyor"
    tr = sum(k in TR_KELIMELER for k in kelimeler)
    en = sum(k in EN_KELIMELER for k in kelimeler)
    tr_harf = sum(ch in TR_HARFLER for ch in metin)
    if tr_harf >= 3 or tr > en:
        return "tr"
    if en > tr:
        return "en"
    return "bilinmiyor"


def dil_normalle(etiket):
    if not etiket:
        return None
    etiket = etiket.lower().split("-")[0].split("_")[0]
    return {"tur": "tr", "tr": "tr", "eng": "en", "en": "en"}.get(etiket, etiket)


# ------------------------------------------------------------------
# Kayit ayristirma
# ------------------------------------------------------------------
HTML_ETIKET = re.compile(r"<[^>]+>")


def temiz(metin):
    # DergiPark metinleri HTML kacisli geliyor ("TBMM&#039;nin"), bazen
    # cift kacisli ("&amp;#039;") ve <p>/<br> etiketli. Iki kez coz, etiketleri at.
    metin = html.unescape(html.unescape(metin or ""))
    metin = HTML_ETIKET.sub(" ", metin)
    return " ".join(metin.split())


def kayit_ayristir(kayit: ET.Element):
    baslik = kayit.find("oai:header", NS)
    if baslik is None or baslik.get("status") == "deleted":
        return None
    md = kayit.find("oai:metadata", NS)
    if md is None:
        return None

    alanlar = {}
    for e in md.iter():
        if e.tag.startswith(DC) and temiz(e.text):
            alanlar.setdefault(e.tag[len(DC):], []).append((temiz(e.text), dil_normalle(e.get(XML_LANG))))

    def degerler(ad):
        return [m for m, _ in alanlar.get(ad, [])]

    ozler = []
    for metin, etiket in alanlar.get("description", []):
        if etiket:
            ozler.append({"dil": etiket, "dil_kaynagi": "etiket", "metin": metin})
        else:
            ozler.append({"dil": dil_tahmin(metin), "dil_kaynagi": "tahmin", "metin": metin})

    def ilk_oz(dil):
        adaylar = [o["metin"] for o in ozler if o["dil"] == dil]
        return max(adaylar, key=len) if adaylar else None  # birden coksa en uzunu

    tanimlayicilar = degerler("identifier")
    # Dergi kisa adi (orn. "mulkiye") makale URL'sinden; set'ler sayisal ve
    # bazi kayitlarda hic yok, bu yuzden dergiyi buradan tanimliyoruz.
    dergi_kodu = next((m.group(1) for t in tanimlayicilar + degerler("relation")
                       if (m := re.search(r"dergipark\.org\.tr/\w+/pub/([^/]+)", t))), None)
    url = next((t for t in tanimlayicilar if t.startswith("http") and "doi.org" not in t), None)
    doi = next((t for t in tanimlayicilar if "10." in t and ("doi" in t.lower() or t.startswith("10."))), None)
    kaynak = degerler("source")
    cs = next((m for k in kaynak if (m := CILT_SAYI.search(k))), None)
    tarihler = degerler("date")
    yillar = [int(m.group()) for t in tarihler if (m := re.search(r"(19|20)\d{2}", t))]

    return {
        "oai_id": baslik.findtext("oai:identifier", "", NS),
        "datestamp": baslik.findtext("oai:datestamp", "", NS),
        "setler": [s.text for s in baslik.findall("oai:setSpec", NS)],
        "url": url,
        "doi": doi,
        "tarihler": tarihler,
        "yil": min(yillar) if yillar else None,
        "dil": [dil_normalle(d) for d in degerler("language")],
        "tur": degerler("type"),
        "dergi_kodu": dergi_kodu,
        "dergi": kaynak,
        "cilt": int(cs.group(1)) if cs else None,
        "sayi": cs.group(2) if cs else None,
        "yayinci": degerler("publisher"),
        "anahtar_kelimeler": degerler("subject"),
        "basliklar": [{"dil": d, "metin": m} for m, d in alanlar.get("title", [])],
        "ozler": ozler,
        "ozet_tr": ilk_oz("tr"),
        "ozet_en": ilk_oz("en"),
    }


def arsiv_bilgisi(tarih_ciltleri):
    """Bir derginin {ilk tarih -> cilt kumesi} haritasindan toplu yukleme
    tarihlerini ve toplu yuklenen en buyuk cildi bulur."""
    toplu = {t for t, c in tarih_ciltleri.items() if len(c) >= TOPLU_ESIK}
    # Arsiv birkac gune yayilmis olabilir: toplu yuklenen en buyuk cilde
    # kadar olan her sey arsiv sayilir.
    arsiv_son_cilt = max((c for t in toplu for c in tarih_ciltleri[t]), default=None)
    return toplu, arsiv_son_cilt


def arsiv_mi(m, toplu, arsiv_son_cilt):
    return bool(
        (m["tarihler"] and m["tarihler"][0] in toplu)
        or (arsiv_son_cilt is not None and m["cilt"] is not None and m["cilt"] <= arsiv_son_cilt))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ham", default=str(KLASOR / "ham"), help="Ham sayfalarin klasoru")
    p.add_argument("--dosya", action="append", help="Tek tek XML/XML.gz dosyalari (orn. deneme_ornek.xml)")
    p.add_argument("--cikti", default=str(KLASOR / "makaleler.jsonl"))
    arg = p.parse_args()

    dosyalar = [Path(d) for d in arg.dosya] if arg.dosya else sorted(Path(arg.ham).rglob("sayfa_*.xml.gz"))
    if not dosyalar:
        raise SystemExit(f"{arg.ham} altinda sayfa_*.xml.gz bulunamadi.")

    # Tum DergiPark (~800 bin makale) bellege sigmayabilir; bu yuzden iki gecis:
    #   1. gecis: kayitlari gecici dosyaya yaz, sadece kucuk ozetleri bellekte tut
    #      (gorulen id'ler, set'ler, dergi basina tarih -> cilt haritasi)
    #   2. gecis: gecici dosyayi okuyup arsiv/yil_guvenilir alanlarini ekle
    gecici = Path(arg.cikti + ".gecici")
    setler = {}  # oai_id -> set kumesi (ayni makale birden cok set'te olabilir)
    tarih_ciltleri = defaultdict(lambda: defaultdict(set))  # dergi -> tarih -> ciltler
    silinen = 0
    with open(gecici, "w", encoding="utf-8") as g:
        for i, dosya in enumerate(dosyalar, 1):
            acici = gzip.open if dosya.suffix == ".gz" else open
            with acici(dosya, "rb") as f:
                kok, _, _ = xml_coz(f.read())
            for kayit in kok.findall(".//oai:record", NS):
                m = kayit_ayristir(kayit)
                if m is None:
                    silinen += 1
                    continue
                if m["oai_id"] in setler:  # tekrar: sadece set'leri birlestir
                    setler[m["oai_id"]].update(m["setler"])
                    continue
                setler[m["oai_id"]] = set(m["setler"])
                if m["tarihler"] and m["cilt"] is not None:
                    tarih_ciltleri[m["dergi_kodu"]][m["tarihler"][0]].add(m["cilt"])
                g.write(json.dumps(m, ensure_ascii=False) + "\n")
            if i % 500 == 0:
                print(f"  {i}/{len(dosyalar)} sayfa...", end="\r")

    print(" " * 40, end="\r")  # ilerleme satirini temizle
    arsiv = {kod: arsiv_bilgisi(tc) for kod, tc in tarih_ciltleri.items()}

    # 2. gecis + rapor sayaclari
    dergi_say, dergi_arsiv, dergi_ilk_yil = Counter(), Counter(), {}
    yil_say, ham_say, tr_say, en_say, cift_say = Counter(), Counter(), Counter(), Counter(), Counter()
    kaynak, oz_dil = Counter(), Counter()
    ozsuz = kodsuz = 0
    with open(gecici, encoding="utf-8") as g, open(arg.cikti, "w", encoding="utf-8") as f:
        for satir in g:
            m = json.loads(satir)
            m["setler"] = sorted(setler[m["oai_id"]])
            kod = m["dergi_kodu"]
            m["arsiv"] = arsiv_mi(m, *arsiv.get(kod, (set(), None)))
            m["yil_guvenilir"] = None if m["arsiv"] else m["yil"]
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

            y = m["yil_guvenilir"]
            dergi_say[kod] += 1
            dergi_arsiv[kod] += m["arsiv"]
            if y and (kod not in dergi_ilk_yil or y < dergi_ilk_yil[kod]):
                dergi_ilk_yil[kod] = y
            yil_say[y] += 1
            ham_say[m["yil"]] += 1
            tr_say[y] += bool(m["ozet_tr"])
            en_say[y] += bool(m["ozet_en"])
            cift_say[y] += bool(m["ozet_tr"] and m["ozet_en"])
            kaynak.update(o["dil_kaynagi"] for o in m["ozler"])
            oz_dil.update(o["dil"] for o in m["ozler"])
            ozsuz += not m["ozler"]
            kodsuz += not kod
    gecici.unlink()

    # Kisa rapor
    print(f"{len(dosyalar)} sayfa, {len(setler)} makale, {silinen} silinmis/bos kayit atlandi")
    print(f"Cikti: {arg.cikti}\n")
    print("Arsiv tespiti (dergi basina):")
    print(f"{'dergi':>14} {'makale':>7} {'arsiv':>6} {'arsiv son cilt':>15} {'ilk guvenilir yil':>18}")
    for kod, n in dergi_say.most_common(30):
        son_cilt = arsiv.get(kod, (set(), None))[1]
        print(f"{str(kod):>14} {n:>7} {dergi_arsiv[kod]:>6} {str(son_cilt):>15} {str(dergi_ilk_yil.get(kod)):>18}")
    if len(dergi_say) > 30:
        print(f"  ... ve {len(dergi_say) - 30} dergi daha")
    print()

    print("Yillara gore ('makale' = guvenilir yil, None = arsiv/yilsiz; 'ham' = dc:date yili):")
    print(f"{'yil':>6} {'makale':>8} {'ham':>6} {'TR oz':>8} {'EN oz':>8} {'TR+EN':>8}")
    for y in sorted(set(yil_say) | set(ham_say), key=lambda y: (y is None, y)):
        print(f"{str(y):>6} {yil_say[y]:>8} {ham_say[y]:>6} {tr_say[y]:>8} {en_say[y]:>8} {cift_say[y]:>8}")
    print(f"\nOz dili kaynagi: {dict(kaynak)}")
    print(f"Oz dilleri: {dict(oz_dil)}")
    print(f"Ozu hic olmayan makale: {ozsuz}")
    print(f"Dergi kodu bulunamayan: {kodsuz}")


if __name__ == "__main__":
    main()
