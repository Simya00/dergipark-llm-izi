# Yöntem Notu

Makalenin yöntem bölümüne temel olacak, her adımın **ne yaptığını**,
**eşiklerini** ve **gerekçesini** anlatan not. Eşiklerin kimin seçimi olduğu
ve doğrulanıp doğrulanmadığı ayrıca belirtilir. Kod değiştikçe güncellenir.

Son güncelleme: 2026-10-25

---

## 1. Veri toplama

- **Kaynak:** DergiPark'ın açık OAI-PMH arayüzü
  (`https://dergipark.org.tr/api/public/oai/`), `oai_dc` biçimi. İzin
  gerektirmez. Kod: `toplama/oai_topla.py`.
- **Kapsam:** Tüm arşiv, filtresiz (arayüzün tarih süzgeci kayıt değişiklik
  tarihine göre çalıştığı ve tüm kayıtların tarihi yenilendiği için
  kullanılamıyor; yıl ayıklaması sonradan yapıldı).
- **Toplama tarihi:** 23–25 Ekim 2026. **Sonuç:** 8.468 sayfa, 844.745 makale,
  3.124 dergi.
- **Sunucu sorunları:** Hız sınırı (HTTP 429) için uyarlanır bekleme
  (temel 3 sn); geçici kesintiler için 12 deneme (~40 dk); bozuk XML için
  onarım (bir sayfada 4 kayıt okunamadı ve atlandı).

## 2. Ayrıştırma ve metin temizliği (`toplama/oai_ayristir.py`)

- HTML kaçışları çözülür (`&#039;` → `'`), HTML etiketleri atılır. **Yalnızca
  gerçek etiketler** (`<p>`, `<br>`, `<span …>` gibi; `<`'den hemen sonra
  bilinen etiket adı) silinir. **Hata düzeltmesi (2026-10-27):** ilk kural
  `<` ile `>` arasındaki her şeyi siliyordu; istatistik yazan özetlerde
  "p<0,05 … p>0,05" arasındaki metin kayboluyordu (doğrulamada kullanıcı
  #30'da fark etti, makale sayfasıyla karşılaştırarak doğruladı).
  **Etkilenen öz: 7.376** (eski kural ≥20 karakter fazladan silerdi);
  düzeltildi.
- Dergi, makale URL'sindeki kısa addan belirlenir (`dergi_kodu`).
- Cilt/sayı `dc:source` alanından ("Vol. X No. Y") okunur.

## 3. Yayın yılı

### 3.1 Arşiv (toplu yükleme) sorunu
- **Sorun:** Dergiler DergiPark'a geçerken eski sayılarını toplu yüklemiş;
  bu makalelerin `dc:date` alanı yayın değil yükleme tarihi. Sayfalardan
  elle doğrulandı: `ogusbd` Cilt 10 gerçekte 2009 (görünen 2014), `ogummf`
  Cilt 10 gerçekte 1997 (görünen 2017).
- **Kural:** Aynı dergide aynı gün **≥3 farklı cilt** yüklenmişse o gün toplu
  yüklemedir; bu makaleler ve cildi, toplu yüklenen en büyük cilde eşit ya
  da küçük olan makaleler **arşiv** sayılır ve yılsız bırakılır (analiz dışı).
- **Neden yıl tahmin edilmiyor:** Cilt numarasından yıl hesaplamak `ogummf`'de
  tutmadı (dergi her yıl düzenli cilt çıkarmamış); yanlış yıl, yılsız
  bırakmaktan daha zararlı.
- **Eşik:** "≥3 farklı cilt" Claude'un seçimi; ESOGÜ pilotunda ve ilk ara
  çıktıda beklenen dergileri yakaladı. Elle doğrulama: yok (yapılabilir).

### 3.2 Yılla numaralanan ciltler
- Bazı dergiler cildi yıl olarak numaralıyor (`bmj`: "Vol. 2014"). Cilt
  1900–2100 arasındaysa yayın yılı olarak kullanılır ve arşiv hesabına
  katılmaz.

### 3.3 Geçersiz yıllar
- 1990–2027 dışındaki yıllar (1902, 2068 gibi veri giriş hataları) yılsız.

**Sonuç (tam veri):** Güvenilir yıllı makale 2021: 57.347, 2022: 58.172,
2023: 58.416, 2024: 60.547, 2025: 65.057, 2026 (kısmi): 22.149.

## 4. Öz dili temizliği

**Temizlik sonrası tam veri (2026-10-27, `oai_ayristir.py` raporu):**
öz başına `dil_kaynagi`: etiket 1.243.627; etiket düzeltildi 32.264; iki
dilli bölündü 27.502 parça (~13.750 alan); bozuk/Latin dışı 7.870; diğer
dil 3.230. Öz dilleri: Türkçe 667.475, İngilizce 635.918. Özü olmayan makale
46.540 (toplam 844.745).

### 4.1 Ölçüm (temizlik öncesi, `toplama/dil_kontrol.py`)
| | Sayı | Oran |
|---|---|---|
| TR etiketli, metin İngilizce | 21.345 | %3,17 |
| TR etiketli, iki dilli | 9.334 | %1,38 |
| EN etiketli, metin Türkçe | 12.264 | %1,96 |
| EN etiketli, iki dilli | 4.508 | %0,72 |

TR→EN yanlış etiket yıllara göre sabit (~%3/yıl, 2017'den beri) → yıllık
karşılaştırmayı çarpıtmaz. İki dilli alanlar zamanla azalıyor (2016: 1.017,
2025: 58). Örneklerde ayrıca bozuk kodlamalı metin ve Almanca özetler var.

### 4.2 Cümle düzeyinde dil tespiti
- Metin `.`, `?`, `!` sonrasında cümlelere bölünür.
- Her cümle için **Türkçe puanı** = listedeki Türkçe işlev kelimesi sayısı
  (ve, bir, bu, ile, için, olarak... 22 kelime) + 2 × (ğ, ı, ş, İ harfi
  sayısı); **İngilizce puanı** = listedeki İngilizce işlev kelimesi sayısı
  (the, and, of, in, is... 21 kelime). Yüksek olan dil seçilir; eşitlikte ya
  da 4 kelimeden kısa cümlede karar verilmez. Almanca/Fransızca işlev
  kelimeleri baskınsa "diğer".
- Gerekçe: İşlev kelimeleri konudan bağımsızdır; ğ/ı/ş/İ İngilizcede yoktur.
  Türkçe metindeki İngilizce terimler ("machine learning") kararı
  değiştirmez.
- Bilinen zayıflık: Türkçe yer/kişi adı çok geçen İngilizce cümle Türkçe
  sanılabilir; kısaltmalar ("vb.", "Dr.") cümleyi böler.

### 4.3 Kararlar
- **Bozuk metin:** Harflerin **>%20**'si Türk alfabesi + İngiliz alfabesi +
  Batı Avrupa harfleri dışındaysa atılır (PDF'ten bozuk kodlamayla
  kopyalanmış metin, ör. "^ŝŶĂŶ 'ƺůŚĂŶ͛ŦŶ").
- **Yanlış etiket:** Cümlelerin (kelime ağırlıklı) **≥%80**'i etiketin
  tersi dildeyse etiket düzeltilir.
- **İki dilli:** Her iki dilde **≥2 cümle** ve azınlık dil **≥%20** ise alan
  bölünür: Türkçe cümleler Türkçe öze, İngilizce cümleler İngilizce
  abstract'a; dili belirsiz cümle önceki cümlenin diline katılır. "≥2 cümle"
  şartı, tek bir yabancı alıntı cümlesi yüzünden bölmemek için.
- **Diğer dil:** Metnin yarısından fazlası Almanca/Fransızca ise ayrılır.
- **Belirsiz:** Hiçbiri değilse DergiPark etiketine **dokunulmaz**
  (şüphede orijinal veri korunur).
- Baştaki "Özet", "Öz", "Abstract" başlıkları atılır ("Özetle",
  "Özellikle" gibi kelimeler korunur).
- Her değişiklik `dil_kaynagi` alanında kayıtlıdır (`etiket_duzeltildi`,
  `iki_dilli_bolundu`, `bozuk_metin`, `diger_dil`).
- **Eşikler** (%80, %20, ≥2 cümle, %20 bozuk) Claude'un seçimi.
  **Doğrulama: yapılacak** — `toplama/dil_dogrulama.py`: 5 kategoriden
  (etiket düzeltildi, iki dilli bölündü, bozuk, diğer dil, dokunulmadı)
  rastgele 50'şer öz (sabit tohum 20261025, kategoriler karışık sırada)
  kullanıcı tarafından E (doğru) / K (kısmen: karar doğru, küçük pürüz,
  ör. bölmede sınırdaki bir cümle yanlış tarafta) / H (yanlış) işaretlenir;
  "sadece E" ve "E+K" doğrulukları ayrı raporlanır; kategori başına doğruluk ve %95
  Wilson güven aralığı raporlanır. "Dokunulmadı" kategorisi kodun
  kaçırdığı sorunları ölçer. (50 örnekte 48 doğru → %96, aralık %86,5–98,9.)

  **1. doğrulama sonucu (düzeltmelerden ÖNCE; kullanıcı, 2026-10-27;
  250 örnek, `toplama/dil_dogrulama.xlsx`):**
  | Kategori | Doğru | Oran | %95 aralık |
  |---|---|---|---|
  | Etiket düzeltildi | 45/50 | %90 | %78,6–95,7 |
  | İki dilli bölündü | 16/50 | **%32** | %20,8–45,8 |
  | Bozuk / okunamaz | 50/50 | %100 | %92,9–100 |
  | Diğer dil | 49/50 | %98 | %89,5–99,6 |
  | Dokunulmadı | 50/50 | %100 | %92,9–100 |
  - İki dilli bölmedeki hataların neredeyse tamamı sınırda (TR ve EN öz
    arasındaki geçiş yanlış yerde; "Abstract"/"Keywords" yanlış tarafta).
    → Düzeltmeler (başlık kelimeleri, tek geçiş noktası, kısaltmalar,
    büyük harf bölmesi) bu kategori için gerekli.
  - "Bozuk" kategorisindekilerin çoğu aslında bozuk değil, Arapça/Yunanca/
    Kiril alfabesinde metin; analiz dışı kalmaları doğru, kategori adı
    "Türkçe/İngilizce dışı alfabe veya bozuk" olarak düzeltilmeli.
  - "Dokunulmadı"da hiç kaçırılmış dil sorunu bulunmadı.

## 5. Birleşik kelime onarımı (`analiz/kelime_siklik.py`, `analiz/birlesik_kelime.py`)

- **Sorun:** PDF'ten kopyalamada satır sonu boşlukları kaybolmuş
  ("rakımlaragöre", "arızadankaynaklanan"); kullanıcı örneklerde fark etti.
- **Kural:** Verinin kendisinden sözlük çıkarılır (her kelime biçimi kaç
  özette geçiyor). Bir kelime, her parçası **≥30 özette** geçen 2 (gerekirse
  3) kelimeye bölünebiliyorsa VE kendisi **<3 özette** geçiyorsa ya da en
  seyrek parçasından **≥20 kat** seyrekse bölünür.
- Gerekçe: Türkçenin eklemeli yapısında ekler tek başına kelime olmadığı
  için ("kitaplarımızdan" → "ımızdan" sözlükte yok) yanlış bölme riski düşük;
  sık kelimeler ("neden", "bilgisayar") hiç bölünmez.
- Eşikler Claude'un seçimi; kullanıcının bulduğu 10 gerçek örneğin hepsi
  doğru bölündü. **Doğrulama: rapor çıktısındaki en sık onarımlar kullanıcı
  tarafından gözden geçirilecek.**

## 6. Aşırı kelime yöntemi (Kobak vd. 2025)

- `p_y`: öğenin (kelime, kelime grubu, ek zinciri) y yılında geçtiği özet oranı.
- Karşı-olgusal: `q_T = p_2022 + (T − 2022) · max(p_2022 − p_2021, 0)`.
- Fark `δ = p_T − q_T`, kat `r = p_T / q_T`.
- Alt sınır: işaretçilerden en az birini içeren özet oranı için
  `L ≥ (p − q) / (1 − q)`.
- Kelime grupları cümle/yan cümle sınırını aşmaz.

## 7. Dergi paneli

- Geç katılan dergiler (ör. `gazimmfd` 2023) tabanda yok, hedef yılda var →
  dergi karışımı değişimi sahte artış üretebilir. Panel: 2021–2025'in her
  yılında ≥5 makalesi olan dergiler. Tüm sonuçlar hem tüm veride hem panelde
  raporlanacak.

## 8. İşaretçi listeleri

- `analiz/aday_liste_tr.txt`: veriye bakmadan önce yazıldı (2026-10-24, git
  geçmişinde tarihli).
- `analiz/aday_liste_tr_llm.txt`: 3 özetin ChatGPT ile yeniden yazımından
  (2026-10-24); keşif amaçlı.
- `analiz/aday_liste_en.txt`: Kobak vd. kelimeleri (hafızadan; makalenin ek
  listesiyle karşılaştırılacak).
- Planlanan: geleneksel kalıplar kontrol listesi (kullanıcı katkısıyla).

## 9. LLM yeniden yazım deneyi (`deney/`)

- 2018–2021'den 200 özet (her dergiden ≤1, 400–1500 karakter, birleşik
  kelimesiz, Türkçe olduğu doğrulanmış, sabit tohum 20261024).
- ChatGPT, Claude, Gemini'ye aynı komutla, 10'arlı paketler halinde, her
  pakette yeni sohbet; hafıza kapalı.
- Amaç: modellerin eklediği kelime, kalıp, ek ve imla tercihlerini çıkarmak;
  ortak olanlar asıl işaretçiler.
