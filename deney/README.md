# LLM Yeniden Yazım Deneyi

ChatGPT öncesi (2018–2021) 200 DergiPark Türkçe özeti, aynı komutla
ChatGPT, Claude ve Gemini'ye yeniden yazdırılır. Orijinal ile yeniden yazım
karşılaştırılarak LLM'lerin **eklediği** kelime, kalıp, ek ve imla tercihleri
çıkarılır:

- Birden çok modelde ortak olanlar → DergiPark'ta aranacak asıl işaretçiler
  (tek modelden çıkan liste güvenilir sayılmaz).
- Modele özgü olanlar → ayrıca raporlanır.
- Aynı veri, ertelenen "LLM ek profili" analizinin de girdisi.

## Adımlar

```bash
cd deney

# 1) Örnekleri seç (önce analiz/sozluk_tr.tsv.gz oluşturulmuş olmalı:
#    birleşik kelimeli özetler dışarıda kalsın diye)
python3 deney_hazirla.py            # -> deney_ornekleri.json (200 örnek)

# 2) Her model için cevapları yapıştır (istediğiniz zaman bırakıp devam edebilirsiniz)
python3 deney_yapistir.py chatgpt
python3 deney_yapistir.py claude
python3 deney_yapistir.py gemini

# Ne kadar doldu?
python3 deney_yapistir.py --durum
```

`deney_yapistir.py` her örnek için modele verilecek metni (komut + özet)
ekrana basar; modelin cevabını terminale yapıştırıp **yeni bir satıra `###`**
yazınca JSON'a kaydeder. `atla` o örneği geçer, `cik` kaydedip çıkar.

## Kurallar (karşılaştırmanın adil olması için)

- **Komut her modelde aynı** (JSON'daki `komut` alanı; değiştirmeyin).
- Her 10–20 örnekte bir **yeni sohbet** açın; ChatGPT'de **hafıza** kapalı
  olsun. Önceki cevaplar sonrakileri etkilemesin.
- Hangi model sürümünü kullandığınızı not edin (ör. ChatGPT'nin ücretsiz /
  ücretli sürümü, Claude ve Gemini'nin sürüm adı) → aşağıya yazın.
- `deney_ornekleri.json` doldukça git'e eklenir (özetler zaten açık erişimli).

## Seçim

- 2018–2021, 400–1500 karakter, her dergiden en fazla 1 özet.
- Birleşik kelimesi ≥2 olan özetler hariç (modeller boşlukları düzeltir,
  sahte "LLM değişikliği" gibi görünür).
- Sabit tohum `20261024`: aynı komut aynı 200 özeti seçer.

## Kullanılan model sürümleri

- ChatGPT: (doldurulacak)
- Claude: (doldurulacak)
- Gemini: (doldurulacak)
