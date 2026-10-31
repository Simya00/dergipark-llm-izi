#!/usr/bin/env python3
"""
Iki Dilli Alanlari Yerel LLM ile Bolme (pilot)
==============================================
Ayni alanda Turkce oz + Ingilizce abstract yazilmis kayitlari (oai_ayristir.py
"iki_dilli_bolundu") yerel bir modele (Ollama: gemma4, llama3.1) bolduruyor.

GUVENCE: Model metni yeniden yazar; bu yuzden modelin verdigi iki parca art
arda konup (bosluklar yok sayilarak) orijinalle HARF HARF karsilastirilir.
Tek harf farkinda sonuc REDDEDILIR. Kabul edilirse parcalar modelin
yazdigindan degil, ORIJINAL metinden kesilir (orijinal karakterler korunur).

Setler (2026-10-31 karari):
  ayar: daha once elle isaretlenen dil_dogrulama.xlsx'teki 50 iki dilli ornek
        (komut bunlarda denenip duzeltilebilir)
  test: daha once gorulmemis, rastgele 100 iki dilli alan (sabit tohum);
        komut bu sette DEGISTIRILMEZ. Kabul esigi: 100'de >= 98 dogru (D/Y).

Komutlar:
  ornekle   ayar ve test setlerini llm_bol_ayar.jsonl / llm_bol_test.jsonl'e yazar
  calistir  --set ayar|test --model gemma4:latest  -> llm_bol_<set>_<model>.jsonl
            (kesilirse ayni komut kaldigi yerden devam eder)
  farklar   --set ... --model ...  -> reddedilenlerde modelin metinde neyi degistirdigi
  excel     --set ... --model ...  -> llm_bol_<set>_<model>.xlsx (D/Y listesi)
  yanlislar --set ... --model ...  -> Y (ve bos) satirlarda kesimin iki yani
  hesapla   --set ... --model ...  -> kapsama, dogruluk, %95 Wilson araligi

Gerekli: Ollama calisiyor olmali (ollama serve), openpyxl (excel/hesapla icin).
"""

import argparse
import json
import random
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

from dil_dogrulama import openpyxl_gerekli, wilson

KLASOR = Path(__file__).resolve().parent
OLLAMA = "http://localhost:11434/api/generate"
TOHUM = 20261031
SICAKLIK = 0      # temperature 0: her seferinde ayni cevap
NUM_CTX = 8192    # modelin tek seferde gordugu en uzun metin (token)

KOMUT = """You are given one field from an academic journal record. It contains a
Turkish abstract and an English abstract written one after the other.

Split it into the Turkish part and the English part.

Rules:
1. Copy the text EXACTLY. Do not correct, translate, reformat, add or
   remove any character, including punctuation and spelling errors.
2. Headings such as "Özet", "Öz", "Abstract" stay in the part they
   belong to.
3. A keywords section goes with its language: "Anahtar Kelimeler: ..."
   with Turkish, "Keywords: ..." with English.

Return only JSON:
{"tr": "<Turkish part>", "en": "<English part>"}

Text:
"""

# v2 (2026-10-31): ayar setinde v1 9/52 alanda metni degistirdi: yazim/buyuk harf
# duzeltti ("ABSRACT" -> "ABSTRACT"), makale basliklarini ve "Başlık:" satirlarini sildi.
KOMUT_V2 = KOMUT.replace(
    """with Turkish, "Keywords: ..." with English.
""",
    """with Turkish, "Keywords: ..." with English.
4. Never fix anything: keep typos, capitalization and headings exactly
   as written (for example "ABSRACT" stays "ABSRACT").
5. Keep EVERY part of the text, even if it does not look like part of
   an abstract (article titles, "Başlık:" lines, headings). Put each
   such part with its language.
""")

# v3 (2026-10-31): v2'de kalan redlerin cogu kopyalama hatasi ("saptanan" -> "saptananan").
# Model artik metni kopyalamiyor; yalnizca IKINCI dilin basladigi ilk kelimeleri yaziyor,
# kesmeyi kod yapiyor (bkz. sinirdan_kes).
KOMUT_V3 = """You are given one field from an academic journal record. It contains a
Turkish abstract and an English abstract written one after the other
(either one may come first).

Find the point where the first abstract ends and the second abstract
begins.

Rules:
1. "ikinci_baslangic": copy the FIRST 8 WORDS of the second abstract
   EXACTLY as they appear in the text: same spelling, capitalization and
   punctuation, even if they contain typos or words glued together.
   If the second abstract starts with a heading such as "Abstract",
   "ABSTRACT:", "Özet" or "Öz", the heading is part of the second abstract.
2. Article titles and keywords sections belong to the abstract in the
   same language ("Anahtar Kelimeler" with Turkish, "Keywords" with English).
3. "ilk_dil": the language of the FIRST abstract, "tr" or "en".

Return only JSON:
{"ikinci_baslangic": "<first 8 words of the second abstract>", "ilk_dil": "tr"}

Text:
"""

# v4 (2026-10-31): v3 ayar dogrulamasi 39/50. Hatalar: ikinci ozun basligi yanlis tarafta (5),
# dil iki kez degisiyor: "... Turkish Başlık: ... Anahtar Kelimeler: ..." (4), aslinda tek dil (3).
# Model artik metnin TUM dil parcalarini sirayla listeler (yine yalnizca baslangic kelimeleri).
KOMUT_V4 = """You are given one field from an academic journal record. It contains a
Turkish abstract and an English abstract, and sometimes other parts such as
article titles, keywords ("Anahtar Kelimeler", "Keywords") or a line like
"Turkish Başlık: ...". The languages may alternate more than once.

List the parts of the text IN ORDER. A new part starts every time the
language changes between Turkish and English.

Rules:
1. "baslangic": copy the FIRST 8 WORDS of the part EXACTLY as they appear
   in the text: same spelling, capitalization and punctuation, even if they
   contain typos or words glued together. If the part is shorter than 8
   words, copy all of it.
2. "dil": the language of the part, "tr" or "en".
3. An article title belongs to the abstract that follows it. If an English
   title comes right before "Abstract", the English part STARTS AT THE FIRST
   WORD OF THAT TITLE. Headings ("Abstract", "ABSTRACT:", "Özet", "Öz",
   "Turkish Başlık:") belong to the part they introduce.
4. Keywords go with their language: "Anahtar Kelimeler" with Turkish,
   "Keywords" with English.
5. Do not start a new part for a single foreign word, name or term inside
   a sentence.

Return only JSON:
{"parcalar": [{"baslangic": "<first 8 words>", "dil": "tr"}, {"baslangic": "<first 8 words>", "dil": "en"}]}

Text:
"""
KOMUTLAR = {"v1": KOMUT, "v2": KOMUT_V2, "v3": KOMUT_V3, "v4": KOMUT_V4}  # eski surumler silinmez (tekrarlanabilirlik)

SEMA = {"type": "object",
        "properties": {"tr": {"type": "string"}, "en": {"type": "string"}},
        "required": ["tr", "en"]}
SEMA_V3 = {"type": "object",
           "properties": {"ikinci_baslangic": {"type": "string"}, "ilk_dil": {"enum": ["tr", "en"]}},
           "required": ["ikinci_baslangic", "ilk_dil"]}
SEMA_V4 = {"type": "object",
           "properties": {"parcalar": {"type": "array", "items": {
               "type": "object",
               "properties": {"baslangic": {"type": "string"}, "dil": {"enum": ["tr", "en"]}},
               "required": ["baslangic", "dil"]}}},
           "required": ["parcalar"]}
SEMALAR = {"v1": SEMA, "v2": SEMA, "v3": SEMA_V3, "v4": SEMA_V4}


# ---------------------------------------------------------------- ornekleme
def iki_dilli_alanlar(girdi):
    """makaleler.jsonl'deki her iki dilli alan: {url, etiket, orijinal, kural_tr, kural_en}."""
    alanlar = []
    with open(girdi, encoding="utf-8") as g:
        for satir in g:
            m = json.loads(satir)
            bolunen = {}
            for oz in m["ozler"]:
                if oz["dil_kaynagi"] == "iki_dilli_bolundu":
                    if "orijinal_metin" not in oz:
                        raise SystemExit("makaleler.jsonl'de 'orijinal_metin' yok: oai_ayristir.py'yi "
                                         "yeniden calistirin (2026-10-31 degisikligi).")
                    a = bolunen.setdefault((oz.get("etiket"), oz["orijinal_metin"]), {})
                    a[oz["dil"]] = oz["metin"]
            for (etiket, orijinal), p in bolunen.items():
                alanlar.append({"url": m.get("url"), "etiket": etiket, "orijinal": orijinal,
                                "kural_tr": p.get("tr", ""), "kural_en": p.get("en", "")})
    return alanlar


def ayar_urlleri():
    """dil_dogrulama.xlsx'teki iki dilli orneklerin makale adresleri (link hucresinin hedefi)."""
    openpyxl_gerekli()
    from openpyxl import load_workbook
    ws = load_workbook(KLASOR / "dil_dogrulama.xlsx")["dogrulama"]
    return {r[3].hyperlink.target for r in ws.iter_rows(min_row=2)
            if r[1].value == "İki dilli alan ikiye bölündü" and r[3].hyperlink}


def yaz(yol, satirlar):
    with open(yol, "w", encoding="utf-8") as f:
        for s in satirlar:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def oku(yol):
    if not yol.exists():
        return []
    with open(yol, encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def komut_ornekle(arg):
    ayar_yol, test_yol = KLASOR / "llm_bol_ayar.jsonl", KLASOR / "llm_bol_test.jsonl"
    if test_yol.exists() and not arg.uzerine_yaz:
        raise SystemExit("llm_bol_test.jsonl zaten var. Yeniden olusturmak icin --uzerine-yaz.")
    alanlar = iki_dilli_alanlar(arg.girdi)
    ayar_url = ayar_urlleri()
    if not ayar_yol.exists():  # ayar seti bir kez olusturulur; isaretli Excel'ler onun numaralarina bagli
        ayar = [a for a in alanlar if a["url"] in ayar_url]
        yaz(ayar_yol, [{"no": i, **a} for i, a in enumerate(ayar, 1)])
        print(f"ayar: {len(ayar)} alan ({len(ayar_url)} makale adresi)")
    # Test: ayar makaleleri haric; ayni makalede ayni metin (TR ve EN etiketli alanda tekrar) bir kez
    # (2026-10-31 karari: ayar setinde 2 makale ikiser kez gecti).
    kalan, gorulen = [], set()
    for a in alanlar:
        anahtar = (a["url"], sade(a["orijinal"]))
        if a["url"] in ayar_url or anahtar in gorulen:
            continue
        gorulen.add(anahtar)
        kalan.append(a)
    test = random.Random(TOHUM).sample(kalan, arg.adet)
    yaz(test_yol, [{"no": i, **a} for i, a in enumerate(test, 1)])
    print(f"iki dilli alan: {len(alanlar)}; tekrar ve ayar haric: {len(kalan)}; "
          f"test: {len(test)} (tohum {TOHUM})")


# ---------------------------------------------------------------- model + kontrol
def ollama_sor(model, metin, surum):
    istek = {"model": model, "prompt": KOMUTLAR[surum] + metin, "stream": False, "format": SEMALAR[surum],
             "options": {"temperature": SICAKLIK, "seed": TOHUM, "num_ctx": NUM_CTX}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(istek).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["response"]


def sade(metin):
    """Karsilastirma bicimi: Unicode NFC (ayni harfin iki kodlamasi esitlensin) + tum bosluklar silinir."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", metin))


def orijinalden_kes(orijinal, ilk_parca):
    """ilk_parcanin bosluk-disi karakter sayisi kadar ilerleyip orijinali o noktadan ikiye boler."""
    hedef, sayac = len(sade(ilk_parca)), 0
    for i, ch in enumerate(unicodedata.normalize("NFC", orijinal)):
        if sayac == hedef:
            metin = unicodedata.normalize("NFC", orijinal)
            return metin[:i].strip(), metin[i:].strip()
        if not ch.isspace():
            sayac += 1
    return orijinal.strip(), ""


def kontrol(orijinal, cevap):
    """(durum, tr, en). durum: kabul | reddedildi_degisti | reddedildi_json
    Model yalnizca boler; dogru/yanlis kararini kullanici verir (2026-10-31).
    Tek otomatik red: model metni degistirdiyse (orijinalden kesilemez)."""
    try:
        c = json.loads(cevap)
        tr, en = c["tr"], c["en"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return "reddedildi_json", "", ""
    o = sade(orijinal)
    if sade(tr) + sade(en) == o:      # once Turkce yazilmis
        bas, son = orijinalden_kes(orijinal, tr)
        tr, en = bas, son
    elif sade(en) + sade(tr) == o:    # once Ingilizce yazilmis
        bas, son = orijinalden_kes(orijinal, en)
        en, tr = bas, son
    else:
        return "reddedildi_degisti", tr, en
    return "kabul", tr, en


def sinirdan_kes(orijinal, cevap):
    """v3: (durum, tr, en). Modelin yazdigi baslangic kelimeleri orijinalde (bosluklar yok
    sayilarak) aranir; TAM OLARAK BIR KEZ bulunursa orijinal o noktadan kesilir.
    durum: kabul | reddedildi_bulunamadi | reddedildi_birden_fazla | reddedildi_json"""
    try:
        c = json.loads(cevap)
        baslangic, ilk_dil = c["ikinci_baslangic"], c["ilk_dil"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return "reddedildi_json", "", ""
    metin = unicodedata.normalize("NFC", orijinal)
    konum = [i for i, ch in enumerate(metin) if not ch.isspace()]  # sade metindeki harf -> orijinaldeki yeri
    o, hedef = sade(metin), sade(baslangic)
    yer = o.find(hedef) if hedef else -1
    if yer < 0:
        return "reddedildi_bulunamadi", "", ""
    if o.find(hedef, yer + 1) >= 0:
        return "reddedildi_birden_fazla", "", ""
    kesim = konum[yer]
    ilk, ikinci = metin[:kesim].strip(), metin[kesim:].strip()
    return ("kabul", ilk, ikinci) if ilk_dil == "tr" else ("kabul", ikinci, ilk)


def parcalardan_kes(orijinal, cevap):
    """v4: (durum, tr, en). Her parcanin baslangici orijinalde, bir onceki parcadan SONRA
    (bosluklar yok sayilarak) aranir; orada tam olarak bir kez bulunmali. Orijinal bu
    noktalardan kesilir; Turkce parcalar TR oze, Ingilizce parcalar EN oze (sirayla) gider.
    Ilk parca her zaman metnin basindan baslar (oncesinde kalan metin kaybolmasin).
    durum: kabul | tek_dil (taraflardan biri bos: bolme yapilmaz) |
           reddedildi_bulunamadi | reddedildi_birden_fazla | reddedildi_json"""
    try:
        parcalar = [(p["baslangic"], p["dil"]) for p in json.loads(cevap)["parcalar"]]
    except (json.JSONDecodeError, KeyError, TypeError):
        return "reddedildi_json", "", ""
    parcalar = [(b, d) for b, d in parcalar if sade(b)]
    if not parcalar:
        return "reddedildi_json", "", ""
    metin = unicodedata.normalize("NFC", orijinal)
    konum = [i for i, ch in enumerate(metin) if not ch.isspace()]
    o = sade(metin)
    yerler, onceki = [], -1
    for baslangic, _ in parcalar:
        hedef = sade(baslangic)
        yer = o.find(hedef, onceki + 1)
        if yer < 0:
            return "reddedildi_bulunamadi", "", ""
        if o.find(hedef, yer + 1) >= 0:
            return "reddedildi_birden_fazla", "", ""
        yerler.append(yer)
        onceki = yer
    yerler[0] = 0
    sinirlar = [konum[y] for y in yerler] + [len(metin)]
    diller = {"tr": [], "en": []}
    for (_, dil), bas, son in zip(parcalar, sinirlar, sinirlar[1:]):
        if metin[bas:son].strip():
            diller[dil].append(metin[bas:son].strip())
    tr, en = " ".join(diller["tr"]), " ".join(diller["en"])
    if not tr or not en:
        return "tek_dil", tr, en
    return "kabul", tr, en


KESICI = {"v3": sinirdan_kes, "v4": parcalardan_kes}


def cikti_yolu(arg, uzanti):
    ek = "" if arg.surum == "v1" else f"_{arg.surum}"  # v1 dosyalari eski adlariyla kalir
    return KLASOR / f"llm_bol_{arg.set}_{arg.model.replace(':', '_')}{ek}.{uzanti}"


def komut_calistir(arg):
    girdiler = oku(KLASOR / f"llm_bol_{arg.set}.jsonl")
    if not girdiler:
        raise SystemExit(f"llm_bol_{arg.set}.jsonl yok: once 'ornekle'.")
    yol = cikti_yolu(arg, "jsonl")
    bitti = {s["no"] for s in oku(yol)}
    with open(yol, "a", encoding="utf-8") as f:
        for g in girdiler:
            if g["no"] in bitti:
                continue
            bas = time.time()
            cevap = ollama_sor(arg.model, g["orijinal"], arg.surum)
            durum, tr, en = KESICI.get(arg.surum, kontrol)(g["orijinal"], cevap)
            s = {**g, "model": arg.model, "komut_surum": arg.surum, "durum": durum, "llm_tr": tr, "llm_en": en,
                 "ham_cevap": cevap, "sure_sn": round(time.time() - bas, 1)}
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {g['no']:>3}/{len(girdiler)}  {durum:<22} {s['sure_sn']:>6} sn")


def farklari_bul(orijinal, tr, en, en_fazla=3):
    """Modelin metni nerede degistirdigini kelime duzeyinde gosterir (iki siradan daha az farkli olani)."""
    import difflib
    o = unicodedata.normalize("NFC", orijinal).split()
    en_iyi = None
    for birlesik in (tr + " " + en, en + " " + tr):
        m = unicodedata.normalize("NFC", birlesik).split()
        sm = difflib.SequenceMatcher(None, o, m, autojunk=False)
        farklar = [op for op in sm.get_opcodes() if op[0] != "equal"]
        if en_iyi is None or len(farklar) < len(en_iyi[0]):
            en_iyi = (farklar, m)
    farklar, m = en_iyi
    satirlar = []
    for tur, i1, i2, j1, j2 in farklar[:en_fazla]:
        satirlar.append(f"    {tur:<8} orijinal: {' '.join(o[i1:i2])[:120]!r}\n"
                        f"    {'':<8} model:    {' '.join(m[j1:j2])[:120]!r}")
    if len(farklar) > en_fazla:
        satirlar.append(f"    ... (+{len(farklar) - en_fazla} fark daha)")
    return len(farklar), "\n".join(satirlar)


def komut_farklar(arg):
    """Reddedilen (metni degistirilen) orneklerde modelin neyi degistirdigini yazar."""
    for s in oku(cikti_yolu(arg, "jsonl")):
        if s["durum"] in ("reddedildi_bulunamadi", "reddedildi_birden_fazla", "reddedildi_json"):
            print(f"#{s['no']}  {s['durum']}  {s['url']}\n    model: {s['ham_cevap'][:200]}\n")
            continue
        if s["durum"] != "reddedildi_degisti":
            continue
        n, metin = farklari_bul(s["orijinal"], s["llm_tr"], s["llm_en"])
        print(f"#{s['no']}  ({n} fark)  {s['url']}\n{metin}\n")


# ---------------------------------------------------------------- excel + hesap
SORU = ("Bölme doğru mu? TR sütununda YALNIZCA Türkçe öz, EN sütununda YALNIZCA İngilizce öz "
        "olmalı; hiçbir cümle yanlış tarafta ya da eksik olmamalı. D = doğru, Y = yanlış")


SORU_TEK_DIL = ("Kod bu alanı BÖLMEDİ (model tek dil gördü; metin bir sütunda). Metin gerçekten "
                "tek dilli mi (bölünmemesi doğru mu)? D = doğru, Y = yanlış")
ISARETLENECEK = ("kabul", "tek_dil")


def onceki_cevaplar(arg):
    """Onceki surumun sonuc + Excel'i: no -> ((tr, en), cevap, aciklama)."""
    from openpyxl import load_workbook
    from types import SimpleNamespace
    eski = SimpleNamespace(set=arg.set, model=arg.model, surum=arg.onceki)
    sonuc = {s["no"]: s for s in oku(cikti_yolu(eski, "jsonl"))}
    ws = load_workbook(cikti_yolu(eski, "xlsx")).active
    cikti = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        s = sonuc.get(r[0])
        if s and r[6]:
            cikti[r[0]] = ((s["llm_tr"], s["llm_en"]), str(r[6]).strip().upper()[:1], str(r[7] or ""))
    return cikti


def komut_excel(arg):
    openpyxl_gerekli()
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation
    yol = cikti_yolu(arg, "xlsx")
    if yol.exists() and not arg.uzerine_yaz:
        raise SystemExit(f"{yol.name} zaten var (cevaplariniz olabilir). --uzerine-yaz ile yeniden olusur.")
    wb = Workbook()
    ws = wb.active
    ws.title = "dogrulama"
    sutunlar = [("no", 5), ("soru", 30), ("adres", 30), ("model sonucu", 16),
                ("TR parça", 70), ("EN parça", 70), ("cevap (D/Y)", 10), ("açıklama", 30)]
    ws.append([a for a, _ in sutunlar])
    for i, (_, gen) in enumerate(sutunlar, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = gen
        ws.cell(1, i).font = Font(bold=True)
    onceki = onceki_cevaplar(arg) if arg.onceki else {}
    aktarilan = 0
    for s in oku(cikti_yolu(arg, "jsonl")):
        soru = {"kabul": SORU, "tek_dil": SORU_TEK_DIL}.get(s["durum"], "Model reddetti: işaretlemeye gerek yok")
        url_tr = s["url"].replace("/en/", "/tr/") if s["url"] else ""  # Turkce sayfa (bkz. 2026-10-27 notu)
        cevap, aciklama = "", ""
        o = onceki.get(s["no"])
        if o and o[0] == (s["llm_tr"], s["llm_en"]) and s["durum"] in ISARETLENECEK:
            cevap, aciklama = o[1], f"({arg.onceki}'ten aynen aktarıldı) {o[2]}".strip()
            aktarilan += 1
        ws.append([s["no"], soru, url_tr, s["durum"], s["llm_tr"], s["llm_en"], cevap, aciklama])
        ws.cell(ws.max_row, 3).hyperlink = url_tr
    for satir in ws.iter_rows():
        for h in satir:
            h.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"D,Y"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"G2:G{ws.max_row}")
    ws.freeze_panes = "A2"
    wb.save(yol)
    print(f"{ws.max_row - 1} satir -> {yol}")
    if arg.onceki:
        print(f"{aktarilan} satirin bolmesi {arg.onceki} ile AYNI: cevabi aktarildi; "
              f"bos kalan isaretlenecek satirlara bakin.")


def komut_yanlislar(arg):
    """Excel'de Y isaretlenen (ve bos birakilan) satirlarda kesim noktasinin iki yanini gosterir."""
    openpyxl_gerekli()
    from openpyxl import load_workbook
    sonuc = {s["no"]: s for s in oku(cikti_yolu(arg, "jsonl"))}
    ws = load_workbook(cikti_yolu(arg, "xlsx")).active
    for r in ws.iter_rows(min_row=2, values_only=True):
        no, cevap, aciklama = r[0], str(r[6] or "").strip().upper()[:1], r[7] or ""
        s = sonuc.get(no)
        if s is None or s["durum"] not in ISARETLENECEK or cevap == "D":
            continue
        print(f"#{no}  {s['durum']}  cevap: {cevap or 'BOS'}  not: {aciklama}\n    {s['url']}\n"
              f"    TR ({len(s['llm_tr'])} kr) sonu: ...{s['llm_tr'][-120:]!r}\n"
              f"    EN ({len(s['llm_en'])} kr) basi: {s['llm_en'][:120]!r}...\n")


def komut_hesapla(arg):
    openpyxl_gerekli()
    from openpyxl import load_workbook
    sonuc = {s["no"]: s for s in oku(cikti_yolu(arg, "jsonl"))}
    ws = load_workbook(cikti_yolu(arg, "xlsx")).active
    cevap = {r[0]: str(r[6] or "").strip().upper()[:1] for r in ws.iter_rows(min_row=2, values_only=True)}
    n = len(sonuc)
    kabul = [no for no, s in sonuc.items() if s["durum"] in ISARETLENECEK]
    d = sum(cevap.get(no) == "D" for no in kabul)
    y = sum(cevap.get(no) == "Y" for no in kabul)
    bos = len(kabul) - d - y
    print(f"model: {arg.model}  komut: {arg.surum}  set: {arg.set}  toplam: {n}")
    from collections import Counter
    for durum, sayi in Counter(s["durum"] for s in sonuc.values()).most_common():
        print(f"  {durum:<24} {sayi:>4}")
    sure = [s["sure_sn"] for s in sonuc.values()]
    print(f"  ortalama sure: {sum(sure) / len(sure):.1f} sn/alan")
    if bos:
        print(f"  UYARI: {bos} isaretlenecek satir bos")
    for ad, dogru, payda in (("isaretlenenlerde dogruluk", d, d + y),
                             ("tumunde (reddedilen = yanlis)", d, n)):
        if payda:
            alt, ust = wilson(dogru, payda)
            print(f"  {ad:<30} {dogru}/{payda} = %{100 * dogru / payda:.1f}  (%95: {100 * alt:.1f}–{100 * ust:.1f})")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("komut", choices=["ornekle", "calistir", "farklar", "excel", "yanlislar", "hesapla"])
    p.add_argument("--set", choices=["ayar", "test"], default="ayar")
    p.add_argument("--model", default="gemma4:latest")
    p.add_argument("--surum", choices=sorted(KOMUTLAR), default="v2", help="komut surumu")
    p.add_argument("--girdi", default=str(KLASOR / "makaleler.jsonl"))
    p.add_argument("--adet", type=int, default=100)
    p.add_argument("--uzerine-yaz", action="store_true")
    p.add_argument("--onceki", choices=sorted(KOMUTLAR), help="excel: bolmesi bu surumle ayni olan satirlarin "
                   "cevabini aktar")
    arg = p.parse_args()
    {"ornekle": komut_ornekle, "calistir": komut_calistir,
     "farklar": komut_farklar, "excel": komut_excel, "yanlislar": komut_yanlislar, "hesapla": komut_hesapla}[arg.komut](arg)


if __name__ == "__main__":
    main()
