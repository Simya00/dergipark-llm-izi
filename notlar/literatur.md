# Literatür

İlk tarama: 2026-10-24 (web araması; tam metinler henüz okunmadı).

## Doğrudan ilgili (aşırı kelime yöntemi)

| Çalışma | Ne yapmış | Bizimle ilişkisi |
|---|---|---|
| Kobak, González-Márquez, Horvát, Lause (2025), *Science Advances* 11(27): eadt3813; arXiv:2406.07016 | 15M+ PubMed özeti (2010–2024); 2024 özetlerinin en az %13,5'i LLM'li, bazı alt gruplarda %40 | Yöntemin kaynağı. Kod: [berenslab/llm-excess-vocab](https://github.com/berenslab/llm-excess-vocab) — parametreleri birebir karşılaştırmak için okunmalı |
| **Lee (2026), arXiv:2609.07447** — *An LLM-Associated Register Shift in Korean Journal Abstracts: A Morphology-Aware Excess-Vocabulary Study, 2018–2026* (hakemsiz ön baskı) | 398.296 KCI (Kore) özeti + 47.165 Vietnamca özet; **biçimbilime duyarlı** aşırı kelime; 2023'te değişim yok, 2024 sonunda başlıyor, 2025'te büyüyor, 2026 ortasında düzleşiyor; alt sınır ~%3,5 / %10,5 / %16,1 (2024–2026); konu kontrolleri etkiyi küçültüyor ama yok etmiyor; çeviri yolu açıklamıyor; **aynı makalelerin İngilizce özetlerinde etki ~1 yıl önce** | **En yakın çalışma.** Eklemeli dil + biçimbilim + iki dilli karşılaştırma + 2026'ya kadar zaman çizgisi → bizim "özgün" dediğimiz üç katkının üçü de Korece için yapılmış. Tam metin mutlaka okunmalı |
| Koo, Kim, Kim (2026), *Language and Information* | ~880 bin KCI beşeri/sosyal bilim özeti; 2024'ü 2021–2022'den tahmin; İngilizce özetlerde keskin artış, Korece özetlerde ılımlı | Korece için ikinci çalışma (veri 2024'te bitiyor) |
| arXiv:2602.03864 (2026) — inşaat ve çevre mühendisliği yazımı, 25 yıl | "enhance, offer, demonstrate" gibi kelimeler 2023'ten sonra eğilimden sapıyor; 2025'te %15,6–38,4 | Alan bazlı uygulama örneği |
| Tübingen grubu, PubMed Central tam metinleri (ikincil kaynaktan; doğrulanmadı) | Aralık 2025 tam metinlerinin %89'unda aşırı LLM kelimesi; İngilizce konuşmayan ülkelerde önce düşük, 2025'te yetişiyor | Doğrulanırsa "Türkiye gibi ülkeler" tartışması için önemli |

## Türkçe — dedektör yaklaşımı (bizden farklı)

- Er & Çoğalmış (2024), "Determining Whether a Turkish Text is Produced by
  Artificial Intelligence or Human", IEEE ICMI 2024 — DergiPark özetleri
  (ChatGPT öncesi insan metni) ile sınıflandırma.
- İZÜ tezi: "Yapay Zekâ ile Üretilmiş Türkçe Bir Metni Tespit Etmek" —
  DergiPark'tan 4 alanda 250'şer makale + ChatGPT-4 özetleri.
- MDPI *Applied Sciences* 15(10):5541 — Türkçe için LSTM dedektörü (%97 doğruluk).

Bunlar tek tek metni sınıflandırıyor (dedektör); hiçbiri DergiPark genelinde
yıllara göre yaygınlık ölçmüyor. Bizim yöntem dedektör gerektirmiyor ve
dağılım düzeyinde.

## Sonuç (ilk tarama)

- Türkçe özetlerde aşırı kelime yöntemiyle LLM yaygınlığını ölçen bir çalışma
  **bulunamadı** → "Türkçe için ilk" iddiası şimdilik geçerli.
- Ama "eklemeli dilde ilk" ve "iki dilli karşılaştırma ilk" iddiaları
  **geçersiz** (Lee 2026, Koo vd. 2026). Bunların üstüne katkı gerekiyor
  (bkz. `gunluk_ilerleme.md`, 2026-10-24).

## Okunacaklar

- [ ] Lee (2026) tam metin — birimler (biçimbirim mi, kök mü, ek mi, n-gram mı?),
      işaretçi seçimi, sağlamlık testleri, sınırlılıklar.
- [ ] Koo, Kim, Kim (2026).
- [x] Kobak vd. kodu okundu (2026-11-11, `berenslab/llm-excess-vocab`,
  `scripts/preprocess_and_count_utils.py` ve `01-process-baseline.ipynb`):
  - Özet uzunluğu filtresi: 250–4000 karakter arası özetler.
  - Kelime: sklearn `CountVectorizer(binary=True)`, yalnızca İngiliz alfabesi
    harfleri (`allowedWords`).
  - Sıklık yumuşatılmış: `(sayı + 1) / (toplam + 1)`; kelime hedef yılda VE
    bir önceki yılda sıklık ≥ 10⁻⁴ ise hesaba girer.
  - Karşı-olgusal: `p(T−2) + max((p(T−2) − p(T−3)) · 2, 0)` (bizimkiyle aynı).
  - **Aşırı kelime kuralı:** `δ > 0,01` VEYA
    `log10(r) > log10(2) − (log10(p) + 4) · log10(2)/4` (p = hedef yıl
    sıklığı). Yani eşik sıklığa göre değişir: p = 10⁻⁴ → r > 2;
    p = 10⁻³ → r > 1,68; p = 10⁻² → r > 1,41; p = 1 → r > 1.
  - 2013–2024 her yıl için uygulanmış → 900 farklı aşırı kelime, elle
    işaretlenmiş (`results/excess_words.csv`): içerik 462, üslup 407
    (üslup: 268 fiil, 53 sıfat, 43 isim, 23 zarf), karışık 27, diğer 4.
  - Lemmatize edilmiş sürüm de var (`excess-per-year-lemmatized`).
- [ ] Tübingen tam metin çalışması (asıl kaynak).
- [ ] Liang vd. (2024) dağılımsal tahmin; Gray (2024); Geng & Trotta (2024).

## Dil temizliği yöntemi için (tarama: 2026-10-31; arxiv.org erişimi kapalıydı, tam metinler okunmadı)

Aynı problemi (TR + EN öz aynı alanda yapışık) çözen çalışma bulunamadı.
Yöntemin parçaları için dayanak olabilecekler:

| Çalışma | Ne yapmış | Bizimle ilişkisi |
|---|---|---|
| Símonarson & Snæbjarnarson (2021), *Icelandic Parallel Abstracts Corpus*, arXiv:2108.05289 | Tezlerden İzlandaca–İngilizce özet çiftleri; özet sınırını bölüm başlıklarının eş anlamlıları ve uzunluk sınırlarıyla bulmuşlar; 7.845 çift | Başlık kelimesine göre bölme. İkincil kaynağa göre 100 çiftte elle %71 doğru (doğrulanmadı) |
| Dil bölütleme (language segmentation): SIGUL 2022 Korsikaca makalesi; CoSwID (HAL 03722821); US patent 9400787 | Belgeyi tek dilli parçalara ayırma; cümle puanları + dil değiştirme cezası, Viterbi | "Tek geçiş noktası" fikrinin literatürdeki adı |
| SciPar (LREC 2022); TURNA (ACL Findings 2024); "Sorting the Babble in Babel" (OpenAlex, arXiv:2502.03627) | Dil etiketine güvenmeyip fastText / langid ile yeniden kontrol; TURNA Türkçe akademik metni satır satır langid ile | Hakem "neden standart araç değil" diye sorabilir; fastText çapraz kontrolü bir seçenek |
| Rose, Herrmann, Erhardt (2025), *Cleaning English Abstracts of Scientific Publications*, arXiv:2512.24459 | Özetlerden başlık/telif vb. fazlalıkları silen spaCy modeli; 9.000 elle etiketli Scopus özeti; %98 doğru temizlik, %0 fazla silme; model Hugging Face'te | Elle doğrulama tasarımına benzer; yalnızca İngilizce |

Sonuç (2026-11-01): iki dilli alanlar analiz dışı bırakıldı (`yontem.md`
§4.4); bu kaynaklar yöntem bölümünde "denenen yaklaşımlar" için.

## Bağlam verisi: Türkiye'nin yayın sayısı (eklendi 2026-11-12)

- **TÜBİTAK, "Türkiye Kaynaklı Bilimsel Yayın Sayısı"** (PDF:
  https://tubitak.gov.tr/sites/default/files/2026-05/60_TR_bilimsel_yayin.pdf;
  kaynak: WoS-InCites, Mayıs 2026 itibarıyla güncel; belge türü: makale,
  derleme). Tam künye (hazırlayan birim, başlık) PDF'ten kontrol edilecek;
  sayılar kullanıcının paylaştığı grafikten.
- 2021: 49.677 · 2022: 49.091 · 2023: 49.303 · 2024: 52.611 (+%7) ·
  **2025: 65.693 (+%25)**.
- **Kullanım kararı (kullanıcı):** duruma göre, yalnızca bağlam olarak.
  "Yapay zekâ yayın üretimini hızlandırdı" denmeyecek; sansasyon yok. Olası
  başka nedenler (teşvik/doçentlik kuralları, WoS kapsamının genişlemesi,
  pandemi sonrası birikim) birlikte anılmalı. WoS ≠ DergiPark dergi kümesi.
- Kendi verimizde: DergiPark TR özet 2022: 46.568 → 2025: 54.181 (+%16).

## Mevzuat bağlamı (eklendi 2026-11-12)

- **7100 sayılı Kanun**, "Yükseköğretim Kanunu ile Bazı Kanun ve Kanun
  Hükmünde Kararnamelerde Değişiklik Yapılması Hakkında Kanun", kabul
  22.02.2018, **Resmî Gazete 6 Mart 2018, Sayı 30352** (yayımı tarihinde
  yürürlükte, md. 35). Kullanıcının yüklediği PDF'ten okundu.
  - md. 3 (2547 s.K. 11/b-6): doçentlik unvanı Üniversitelerarası Kurulca,
    jürilerin adayın yayın ve çalışmalarını değerlendirmesiyle verilir.
  - md. 5 (2547 s.K. 24): başvuru yılda iki kez; şart "yeterli sayı ve
    nitelikte özgün bilimsel yayın"; esaslar YÖK yönetmeliğiyle (ç bendi).
  - md. 1, 11 vd.: "yardımcı doçent" → "doktor öğretim üyesi".
  - TR Dizin / ulusal dergi şartı bu kanunda YOK → Doçentlik Yönetmeliği
    (2018) ve ÜAK doçentlik başvuru şartlarına bakılacak.
  - Kullanım: yalnızca bağlam ("2018'de doçentlik yayın değerlendirmesine
    bağlandı; aynı dönemde DergiPark'ta dergi sayısı hızla arttı, en çok
    yeni dergi 2018'de: 288"). Neden-sonuç iddiası yok.
- Not: kullanıcının paylaştığı kaynaksız bir metin (muhtemelen başka bir
  yapay zekâdan) 2019 için dört neden öne sürüyordu (doçentlik/teşvik,
  DergiPark altyapı/PDF, TR Dizin şartları, genişletilmiş özet). Yalnızca
  doçentlik değişikliği belgelendi; PDF/tam metin iddiası bizim analizle
  ilgisiz (yalnızca özet), özet uzunluğunda 2019 sıçraması yok. Test
  edilebilir fikirler: özel/ek sayı oranı (2019), "etik kurul" (2020+).
