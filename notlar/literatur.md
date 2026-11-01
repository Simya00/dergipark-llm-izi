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
- [ ] Kobak vd. ek materyal: kelime listesi ve eşikler; `berenslab/llm-excess-vocab` kodu.
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
