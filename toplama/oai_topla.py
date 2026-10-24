#!/usr/bin/env python3
"""
DergiPark OAI-PMH Toplayici
===========================
DergiPark'in acik OAI-PMH arayuzunden (https://dergipark.org.tr/api/public/oai)
makale ustverisini (baslik, oz/abstract, tarih, dergi...) toplu olarak indirir.

Ham XML sayfalarini OLDUGU GIBI diske yazar (ham/<set>/sayfa_00001.xml.gz).
Ayristirma ayri bir adimdir (oai_ayristir.py) -> ayristirmada hata cikarsa
sunucudan tekrar indirmek gerekmez.

Ozellikler:
  - Kaldigi yerden devam: her sayfadan sonra resumptionToken durum dosyasina
    yazilir; script kesilirse ayni komutla tekrar calistirmak yeterli.
  - Sunucuyu yormamak icin istekler arasi bekleme (varsayilan 1 sn).
  - Gecici hatalarda (zaman asimi, 5xx, 503 Retry-After) artan beklemeyle
    tekrar deneme.
  - Sadece Python standart kutuphanesi (kurulum gerekmez).

Kullanim:
  # 0) Once arayuzun calistigini ve verinin neye benzedigini gor:
  python3 oai_topla.py deneme

  # 1) Dergi (set) listesini indir -> setler.tsv
  python3 oai_topla.py setler

  # 2) Belirli dergileri topla (set adlari setler.tsv'den):
  python3 oai_topla.py topla --set ogummf --set ogusbd

  # 3) Tum DergiPark'i topla (gunler surebilir; kesilirse ayni komut devam eder):
  python3 oai_topla.py topla

NOT: OAI'deki --from/--until KAYDIN DEGISTIRILME tarihine (datestamp) gore
suzer, makalenin YAYIN tarihine gore DEGIL. Bu yuzden yil suzmesi burada
degil, ayristirma/analiz asamasinda dc:date uzerinden yapilir.
"""

import argparse
import gzip
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

TABAN_URL = "https://dergipark.org.tr/api/public/oai/"
KLASOR = Path(__file__).resolve().parent
HAM_KLASOR = KLASOR / "ham"
SETLER_DOSYASI = KLASOR / "setler.tsv"

NS = {
    "oai": "http://www.openarchives.org/OAI/2.0/",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
KULLANICI_AJANI = "TR-LLM-Analiz arastirma toplayicisi (akademik, OAI-PMH; 429 gelince yavaslar)"
ZAMAN_ASIMI = 120
MAKS_DENEME = 12  # 2+4+...+300 sn: sunucu ~40 dk dusse de bekler

# Uyarlanir ek bekleme: sunucu 429 ("cok hizli") dedikce artar, basarili
# isteklerle yavasca azalir. Boylece hiz sunucunun sinirina kendiliginden oturur.
EK_BEKLEME = 0.0
EK_BEKLEME_MAKS = 60.0


# ------------------------------------------------------------------
# HTTP: tekrar denemeli istek
# ------------------------------------------------------------------
def oai_istek(parametreler: dict, bekleme: float) -> bytes:
    global EK_BEKLEME
    url = TABAN_URL + "?" + urllib.parse.urlencode(parametreler)
    for deneme in range(1, MAKS_DENEME + 1):
        try:
            istek = urllib.request.Request(url, headers={"User-Agent": KULLANICI_AJANI})
            with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
                veri = yanit.read()
            time.sleep(bekleme + EK_BEKLEME)
            EK_BEKLEME *= 0.98  # ~35 basarili istekte yariya iner
            return veri
        except urllib.error.HTTPError as h:
            if h.code == 429:
                EK_BEKLEME = min(max(EK_BEKLEME * 2, 1.0), EK_BEKLEME_MAKS)
                print(f"  HTTP 429: hiz dusuruluyor, istekler arasi artik ~{bekleme + EK_BEKLEME:.1f} sn",
                      file=sys.stderr)
            if h.code in (429, 503) and h.headers.get("Retry-After", "").isdigit():
                sure = int(h.headers["Retry-After"])
            elif h.code >= 500 or h.code == 429:
                sure = min(2 ** deneme, 300)
            else:
                raise  # 4xx: tekrar denemenin anlami yok
            print(f"  HTTP {h.code}, {sure} sn sonra tekrar ({deneme}/{MAKS_DENEME})", file=sys.stderr)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as h:
            sure = min(2 ** deneme, 300)
            print(f"  Baglanti hatasi ({h}), {sure} sn sonra tekrar ({deneme}/{MAKS_DENEME})", file=sys.stderr)
        time.sleep(sure)
    raise RuntimeError(f"{MAKS_DENEME} denemede de basarisiz: {url}")


# ------------------------------------------------------------------
# Bozuk XML onarimi
# ------------------------------------------------------------------
# DergiPark bazen XML'de gecersiz icerik donduruyor (ozlere karismis kontrol
# karakterleri, kacissiz "&", HTML varliklari). Sayfa once oldugu gibi, olmazsa
# temizlenerek, o da olmazsa kayit kayit ayiklanarak okunur.
KONTROL_KARAKTERI = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")
GECERSIZ_KARAKTER_REF = re.compile(
    rb"&#(?:0*(?:[0-8]|1[124-9]|2\d|3[01])|x0*(?:[0-8bcef]|1[0-9a-f]));", re.IGNORECASE)
VARLIK = re.compile(rb"&(?!#\d+;|#x[0-9a-fA-F]+;)(\w+;)?")
XML_VARLIKLARI = {b"amp;", b"lt;", b"gt;", b"quot;", b"apos;"}
KAYIT = re.compile(rb"<record>.*?</record>", re.DOTALL)
TOKEN = re.compile(rb"<resumptionToken[^>]*>([^<]*)</resumptionToken>")


def _varlik_duzelt(m):
    ad = m.group(1)
    if ad is None:
        return b"&amp;"  # kacissiz "&"
    if ad in XML_VARLIKLARI:
        return m.group(0)
    cozulmus = html.unescape("&" + ad.decode())  # orn. &nbsp; -> karakter
    return html.escape(cozulmus, quote=False).encode()


def xml_temizle(ham: bytes) -> bytes:
    ham = ham.decode("utf-8", errors="replace").encode("utf-8")
    ham = KONTROL_KARAKTERI.sub(b" ", ham)
    ham = GECERSIZ_KARAKTER_REF.sub(b" ", ham)
    return VARLIK.sub(_varlik_duzelt, ham)


def xml_coz(ham: bytes):
    """(kok, saklanacak_bayt, atlanan_kayit_sayisi) dondurur."""
    try:
        return ET.fromstring(ham), ham, 0
    except ET.ParseError:
        pass
    temiz = xml_temizle(ham)
    try:
        return ET.fromstring(temiz), temiz, 0
    except ET.ParseError:
        pass
    # Son care: kayitlari tek tek dene, okunamayanlari at
    kayitlar = list(KAYIT.finditer(temiz))
    if not kayitlar:
        raise ET.ParseError("sayfa onarilamadi (kayit bulunamadi)")
    sarmal = b'<x xmlns="http://www.openarchives.org/OAI/2.0/">%s</x>'
    iyiler = []
    for k in kayitlar:
        try:
            ET.fromstring(sarmal % k.group(0))
            iyiler.append(k.group(0))
        except ET.ParseError:
            pass
    bas, son = temiz[:kayitlar[0].start()], temiz[kayitlar[-1].end():]
    onarilmis = bas + b"".join(iyiler) + son
    return ET.fromstring(onarilmis), onarilmis, len(kayitlar) - len(iyiler)


def oai_hatasi(kok: ET.Element):
    """OAI <error> ogesi varsa (kod, mesaj) dondurur."""
    hata = kok.find("oai:error", NS)
    if hata is None:
        return None
    return hata.get("code"), (hata.text or "").strip()


def resumption_token(kok: ET.Element):
    """Sonraki sayfanin token'i ve (varsa) toplam kayit sayisi."""
    rt = kok.find(".//oai:resumptionToken", NS)
    if rt is None:
        return None, None
    token = (rt.text or "").strip() or None  # bos token = son sayfa
    return token, rt.get("completeListSize")


# ------------------------------------------------------------------
# Komut: deneme
# ------------------------------------------------------------------
def komut_deneme(arg):
    print("[1/2] Identify")
    kok = ET.fromstring(oai_istek({"verb": "Identify"}, arg.bekleme))
    for alan in ("repositoryName", "earliestDatestamp", "granularity", "deletedRecord"):
        e = kok.find(f".//oai:{alan}", NS)
        print(f"  {alan}: {e.text if e is not None else '-'}")

    print("[2/2] ListRecords (ilk sayfa)")
    parametre = {"verb": "ListRecords", "metadataPrefix": arg.format}
    if arg.set:
        parametre["set"] = arg.set[0]
    ham = oai_istek(parametre, arg.bekleme)
    kok = ET.fromstring(ham)
    if (h := oai_hatasi(kok)):
        sys.exit(f"  OAI hatasi: {h}")
    kayitlar = kok.findall(".//oai:record", NS)
    token, toplam = resumption_token(kok)
    print(f"  Bu sayfada {len(kayitlar)} kayit, toplam (sunucuya gore): {toplam}")

    ornek = KLASOR / "deneme_ornek.xml"
    ornek.write_bytes(ham)
    print(f"  Ham sayfa kaydedildi: {ornek}")

    # Ilk 3 kaydin ozeti: hangi alanlar var, oz dilleri etiketli mi?
    for kayit in kayitlar[:3]:
        print("  ---")
        print("  id:", kayit.findtext("oai:header/oai:identifier", "", NS))
        print("  set:", [s.text for s in kayit.findall("oai:header/oai:setSpec", NS)])
        md = kayit.find("oai:metadata", NS)
        if md is None:
            print("  (metadata yok - silinmis kayit olabilir)")
            continue
        for e in md.iter():
            if e.tag.startswith("{" + NS["dc"] + "}"):
                ad = e.tag.split("}")[1]
                dil = e.get("{http://www.w3.org/XML/1998/namespace}lang")
                metin = " ".join((e.text or "").split())
                print(f"  dc:{ad}" + (f" [{dil}]" if dil else "") + f": {metin[:90]}")


# ------------------------------------------------------------------
# Komut: setler
# ------------------------------------------------------------------
def komut_setler(arg):
    satirlar, token = [], None
    while True:
        parametre = {"verb": "ListSets"} if token is None else {"verb": "ListSets", "resumptionToken": token}
        kok = ET.fromstring(oai_istek(parametre, arg.bekleme))
        if (h := oai_hatasi(kok)):
            sys.exit(f"OAI hatasi: {h}")
        for s in kok.findall(".//oai:set", NS):
            satirlar.append((s.findtext("oai:setSpec", "", NS), " ".join(s.findtext("oai:setName", "", NS).split())))
        token, _ = resumption_token(kok)
        print(f"  {len(satirlar)} set...", end="\r")
        if not token:
            break
    with SETLER_DOSYASI.open("w", encoding="utf-8") as f:
        f.write("setSpec\tsetName\n")
        for spec, ad in satirlar:
            f.write(f"{spec}\t{ad}\n")
    print(f"\n{len(satirlar)} set yazildi: {SETLER_DOSYASI}")


# ------------------------------------------------------------------
# Komut: topla
# ------------------------------------------------------------------
def tek_set_topla(set_adi, arg):
    """Bir set'i (veya set_adi=None ise tum arsivi) sayfa sayfa indirir."""
    hedef = HAM_KLASOR / (set_adi or "_hepsi")
    hedef.mkdir(parents=True, exist_ok=True)
    durum_dosyasi = hedef / "durum.json"
    durum = json.loads(durum_dosyasi.read_text()) if durum_dosyasi.exists() else {}

    if durum.get("bitti"):
        print(f"[{set_adi or 'hepsi'}] zaten tamamlanmis, atlaniyor.")
        return
    sayfa = durum.get("sayfa", 0)
    token = durum.get("token")
    kayit_sayisi = durum.get("kayit", 0)

    while True:
        if token:
            parametre = {"verb": "ListRecords", "resumptionToken": token}
        else:
            if sayfa > 0:
                # Token yok ama sayfa var: onceki calisma tutarsiz kalmis.
                sys.exit(f"{durum_dosyasi} tutarsiz; klasoru silip bastan baslatin.")
            parametre = {"verb": "ListRecords", "metadataPrefix": arg.format}
            if set_adi:
                parametre["set"] = set_adi

        try:
            ham = oai_istek(parametre, arg.bekleme)
        except urllib.error.HTTPError as h:
            if token and h.code in (400, 422):
                sys.exit(f"Token reddedildi (suresi dolmus olabilir): {h}. "
                         f"{hedef} klasorunu silip bu set'i bastan toplayin.")
            raise
        kok, ham, atlanan = xml_coz(ham)
        if atlanan:
            print(f"  UYARI: sayfa {sayfa + 1}'de okunamayan {atlanan} kayit atlandi", file=sys.stderr)
        hata = oai_hatasi(kok)
        if hata and hata[0] == "noRecordsMatch":
            print(f"[{set_adi or 'hepsi'}] kayit yok.")
            token = None
        elif hata and hata[0] == "badResumptionToken":
            sys.exit(f"Token gecersiz/suresi dolmus: {hata}. {hedef} klasorunu silip bastan toplayin.")
        elif hata:
            sys.exit(f"OAI hatasi: {hata}")
        else:
            sayfa += 1
            with gzip.open(hedef / f"sayfa_{sayfa:05d}.xml.gz", "wb") as f:
                f.write(ham)
            kayit_sayisi += len(kok.findall(".//oai:record", NS))
            token, toplam = resumption_token(kok)
            print(f"[{set_adi or 'hepsi'}] sayfa {sayfa}, {kayit_sayisi}/{toplam or '?'} kayit")

        durum = {"sayfa": sayfa, "token": token, "kayit": kayit_sayisi, "bitti": token is None}
        durum_dosyasi.write_text(json.dumps(durum))
        if token is None:
            return


def komut_topla(arg):
    setler = list(arg.set or [])
    if arg.set_dosyasi:
        setler += [s.strip() for s in Path(arg.set_dosyasi).read_text(encoding="utf-8").splitlines()
                   if s.strip() and not s.startswith("#")]
    for set_adi in (setler or [None]):
        tek_set_topla(set_adi, arg)
    print("Tamamlandi.")


def main():
    global TABAN_URL
    # nohup ile dosyaya yonlendirildiginde ilerleme satirlari hemen yazilsin
    sys.stdout.reconfigure(line_buffering=True)
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["deneme", "setler", "topla"])
    p.add_argument("--set", action="append", help="OAI set adi (dergi); birden cok kez verilebilir")
    p.add_argument("--set-dosyasi", help="Her satirda bir set adi olan dosya")
    p.add_argument("--format", default="oai_dc", help="metadataPrefix (varsayilan oai_dc)")
    p.add_argument("--bekleme", type=float, default=1.0, help="Istekler arasi bekleme, sn (varsayilan 1)")
    p.add_argument("--url", default=TABAN_URL, help="OAI adresi (test icin degistirilebilir)")
    arg = p.parse_args()
    TABAN_URL = arg.url
    {"deneme": komut_deneme, "setler": komut_setler, "topla": komut_topla}[arg.komut](arg)


if __name__ == "__main__":
    main()
