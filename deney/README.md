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

## API ile (2026-11-07 kararı; elle yapıştırmanın yerine geçer)

`api_yeniden_yaz.py` aynı komutu API üzerinden gönderir, cevabı aynı alana
yazar. Her istekte **tek özet** (her özet sıfırdan bir sohbet), sıcaklık vb.
ayar **gönderilmez** (servisin varsayılanı), her özet **1 kez**.

```bash
cd deney
export OPENAI_API_KEY=...      # anahtarı sohbete ya da dosyaya YAZMAYIN
python3 api_yeniden_yaz.py openai --model <tam-sürüm-adı> --kuru      # göndermeden ilk isteği göster
python3 api_yeniden_yaz.py openai --model <tam-sürüm-adı> --sinir 3   # 3 örnekle deneme
python3 api_yeniden_yaz.py openai --model <tam-sürüm-adı>             # kalanların hepsi
# aynısı: gemini (GEMINI_API_KEY), anthropic (ANTHROPIC_API_KEY)
python3 deney_yapistir.py --durum
```

- Kesilmiş (uzunluk sınırı) ya da boş cevaplar kaydedilmez; tekrar
  çalıştırınca yeniden sorulur. Yarıda kalırsa yeniden çalıştırın.
- Her cevabın yanında `api` alanı: istenen/dönen model adı, zaman, bitiş
  nedeni, token sayıları. Ham cevaplar `api_ham_<alan>.jsonl`.
- API'deki Claude boş bir sohbetle başlar, hipotezi bilmez; aşağıdaki
  "claude.ai'dan alınmalı" kuralının amacı (kod asistanını dışarıda tutmak)
  korunur.
- Sınırlılık: API, web arayüzüyle aynı değil (arayüzün gizli talimatları ve
  varsayılanları farklı olabilir). Gemini ücretsiz sınırları (AI Studio, 2026-11-28, kullanıcının hesabı): Gemini 3.8 / 3.6 / 3 / 2.5 Flash dakikada 5, günde 20 istek; 3.5 ve 3.1 Flash Lite dakikada 15, günde 500; Pro modeller 0. Kod Gemini için istekler arasında 13 sn bekler (`--bekle` ile değişir) ve günlük kota dolunca hemen durur. Gemini ücretsiz katmanı yalnızca Flash
  modelleri kapsar; gönderilen veriyi Google kullanabilir (özetler zaten açık
  erişimli).

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

## Ek koşullar ve Claude Batch (2026-11-28)

Dış değerlendirme önerisi: tek komut ("akademik yazım diline uygun ... düzenle") akademik
kalıpları kendisi çağırabilir. İki koşul eklendi (komutlar `deney_ornekleri.json` →
`komutlar`; bir kez yazılır, değişmez):

| Koşul | Girdi | Komut | Cevap alanı |
|---|---|---|---|
| duzenle | Türkçe özet | eski KOMUT | `cevaplar[<model>]` |
| duzelt | Türkçe özet | yalnızca yazım/noktalama/dil bilgisi düzelt, başka değişiklik yok | `cevaplar[<model>_duzelt]` |
| ceviri | aynı makalenin İngilizce özeti | Türkçeye çevir | `cevaplar[<model>_ceviri]` |

```bash
cd deney
python3 deney_hazirla.py --kosullar-ekle          # komutlar + ozet_en; CEVAPLARA DOKUNMAZ
python3 api_yeniden_yaz.py gemini --durum
python3 api_yeniden_yaz.py gemini --model <tam-ad> --kosul duzelt --sinir 3
pip install anthropic
python3 claude_batch.py gonder --model <tam-ad> --kosul duzenle --sinir 3   # Batch: yarı fiyat
python3 claude_batch.py topla                                               # sonuçları yaz
python3 claude_batch.py durum
```

- Anahtarlar koda/dosyaya yazılmaz; ortam değişkeninde yoksa terminalde görünmez sorulur.
- Kaldığı yerden devam: her cevap gelince kaydedilir; kredi/kota biterse program durur,
  aynı komut sonra kaldığı yerden sürer. Batch'te gönderilmiş ama toplanmamış örnekler
  tekrar gönderilmez; başarısız/kesilmiş/reddedilmiş cevaplar kaydedilmez, yeniden gider.
