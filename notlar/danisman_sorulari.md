# Danışman hocaya sorulacaklar

Kullanıcının danışmanına götüreceği açık sorular. Cevaplar tarihle buraya ve
günlüğe yazılır.

## 1. 2019'daki aşırı kelimeler için ek test gerekli mi? (2026-11-17)

**Durum:** Gövde düzeyinde δ>0,01 aşırı kelime sayısı 2018–2025:
82, 60, 12, 35, 6, 22, 120, 237 (tüm veri); kısa panel 65, 90, 22, 43, 18,
17, 124, 231. LLM öncesi 2019 da yüksek (kısa panelde 90). 2019 kelimeleri
(taban 2016–2017) klinik tıp özeti kelimeleri: bulgu, tespit, amaçla, anlamlı,
hasta, yaş, cinsiyet, gereç, retrospektif, demografik, tedavi, başvur, dahil,
tara… Aynı resim sabit dergili uzun panelde de var. 2024 kelimeleri ise üslup
kelimeleri (vurgula, kritik, kapsamlı, potansiyel, teşvik).
Taban etkisi: "hasta" 2016 %7,1 → 2017 %5,6 → 2019 %7,8.

**Mevcut plan (test olmadan):** kelime listesini göstermek + elle Ü/İ/B
işaretlemesi (beklenti: 2019 = İ ağırlıklı, 2024 = Ü ağırlıklı). Makalede
yalnızca betimleyici cümle: "2019'un aşırı kelimeleri ağırlıkla klinik
araştırma kelimeleridir". Neden-sonuç iddiası yok.

**İsteğe bağlı testler:**
- **Test 1 (ucuz, birkaç dakika):** yıllara göre "gereç ve yöntem",
  "retrospektif" içeren ve "Amaç:" ile başlayan özetlerin payı. Beklenti:
  2017'de düşüş, 2019'da yükseliş. Aynı betik "etik kurul" eğilimi için de
  kullanılır. (İfadeleri Claude seçti.)
- **Test 2 (daha pahalı, en güçlü):** klinik özetleri ("gereç ve yöntem"
  içerenler) çıkarıp 2019 hesabını tekrarlamak; aşırı kelime sayısı LLM
  öncesi düzeye inerse açıklama kanıtlanır. Zemberek yeniden çalışmaz
  (parçalarda makale başına gövde listesi var).

**Sorular:** Test 1 / Test 2 yapılsın mı, yoksa elle işaretleme yeterli mi?

## 2. Bağlam olarak mevzuat (literatur.md)

7100 sayılı Kanun (RG 6.3.2018) ve YÖK 07.03.2019 yağmacı dergi kararı
(ÜAK yazısı 23.09.2020). Claude değerlendirmesi: 2019'daki klinik
kelime artışıyla uyumlu (yağmacı dergilerden en çok tıp etkilendi) ama
zamanlama zayıf (2020 hedef yılı düşük). **Soru:** makalede bağlam olarak
anılsın mı, hiç anılmasın mı?

## 3. Tekrarlanabilirlik farkı (yontem.md §6.1)

Sayım iki kez yapıldı: ek sayıları birebir aynı; gövdede 42 gövde / 219
kayıt (binde birden az) farklı (periyod/periyot gibi iki yazımlı kelimeler,
Zemberek eşit puanlı seçim). Ana tablo (δ>0,01) birebir aynı.
Claude önerisi: birleştirme listesi kurulmasın, sınırlılık olarak yazılsın.
**Soru:** yeterli mi?

## 4. Başlık (makale.md)

"Kelimeleri Ayarlama Enstitüsü: DergiPark Özetlerinde Büyük Dil Modeli
İzleri". **Soru:** alt başlıktaki "İzleri" iddialı mı? Alternatif:
"… Kelime Tercihlerinin Değişimi (2015–2025)".

## 5. Hedef dergi ve dil (2026-11-17)

Makale Türkçe mi İngilizce mi yazılmalı, hangi dergiye gönderilmeli?

## 6. Yapay zekâ asistanı kullanımının beyanı (2026-11-17)

Kodlama asistanı (Claude Code) kullanımı yöntem bölümünde ya da beyanlar
kısmında nasıl belirtilmeli? (Kod asistanla yazıldı; eşik/yöntem kararları
ve elle doğrulamalar kullanıcıya ait, notlarda ayrı ayrı kayıtlı.)

Görüşme özeti belgesi (Claude Docs): https://claude.ai/artifact/T4UPHJdEtY4PVFEh2CFexg
