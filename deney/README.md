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

# 2) Her model için cevapları yapıştır — 10'arlı paketler, ÜÇ MODELDE DE AYNI
#    (model başına ~20 yapıştırma; istediğiniz zaman bırakıp devam edebilirsiniz)
python3 deney_yapistir.py chatgpt --paket 10
python3 deney_yapistir.py claude --paket 10
python3 deney_yapistir.py gemini --paket 10

# Ne kadar doldu?
python3 deney_yapistir.py --durum

# Uygun olmayan örnekleri (ör. Türkçe etiketli İngilizce özet) yenileriyle
# değiştir; diğer cevaplar korunur:
python3 deney_hazirla.py --degistir
```

`deney_yapistir.py --paket 10` her seferinde 10 özeti talimatla birlikte JSON
olarak ekrana basar; bunu modele verip modelin döndürdüğü JSON listesini
terminale yapıştırın ve **yeni bir satıra `###`** yazın. Model JSON'un önüne
açıklama ya da ```json işareti eklese de okunur; eksik gelen özetler sonra
yeniden sorulur. `atla` paketi geçer, `cik` kaydedip çıkar. (`--paket`
olmadan tek tek sorar.)

## Kurallar (karşılaştırmanın adil olması için)

- **Komut ve paket boyutu her modelde aynı** (JSON'daki `komut` alanı;
  değiştirmeyin). Bütün dosyayı tek seferde bir modele vermeyin: toplu
  işte modeller kısaltmaya/benzeştirmeye eğilimli, koşullar modeller arasında
  farklı olursa fark modele mi yönteme mi ait bilinemez.
- Claude cevapları claude.ai'dan alınmalı; bu çalışmanın kod asistanı
  (Claude Code) hipotezi bildiği için üretmemeli.
- Her pakette **yeni sohbet** açın; ChatGPT'de **hafıza** kapalı
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
