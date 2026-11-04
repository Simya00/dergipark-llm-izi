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

### 4.4 İki dilli alanların yerel LLM ile bölünmesi (pilot, `toplama/llm_bol.py`)
Kural tabanlı bölme %32 doğru çıktığı için (§4.3) denenen alternatif
(kullanıcı kararı, 2026-10-31).
- **Model:** yerel, Ollama üzerinden (`gemma4:latest`, `llama3.1:latest`;
  kullanıcının bilgisayarı: RTX 5060 Laptop 8 GB, 32 GB RAM). temperature 0,
  seed 20261031, num_ctx 8192; cevap JSON şemasına zorlanır. Komutun tam
  metni koddadır (`KOMUT`), test setinde değiştirilmez.
- **Metin değiştirilmez:** Model iki parçayı yazar; parçalar art arda konup
  (boşluklar yok sayılarak, Unicode NFC) orijinalle harf harf karşılaştırılır.
  Tek harf farkında sonuç reddedilir. Kabul edilirse parçalar **orijinal
  metinden** kesilir (modelin yazdığı metin veriye girmez). Model yalnızca
  böler; kendi kararına ("emin değilim") yer yok, doğru/yanlış kararını
  kullanıcı verir (kullanıcı kararı, 2026-10-31). Tek otomatik red, metnin
  değiştirilmesidir (o zaman orijinalden kesilemez).
- **Ayar seti:** 1. doğrulamadaki 50 iki dilli örnek (komut burada denenip
  düzeltilebilir). **Test seti:** bu makaleler hariç rastgele 100 iki dilli
  alan (tohum 20261031); komut ve model test öncesi sabitlenir.
- **Doğrulama:** kullanıcı, yalnızca D (doğru) / Y (yanlış); "kısmen" yok.
- **Kabul eşiği (kullanıcı, veriden önce):** test setinde **≥98/100 doğru**
  (98/100 → %95 Wilson %93,0–99,4). Altında kalırsa iki dilli alanlar analiz
  dışı. Reddedilen örneklerin yanlış mı sayılacağı / kapsamın ayrı mı
  raporlanacağı: karar bekliyor (kod ikisini de hesaplıyor).
- **Komut sürümleri** (eski sürümler kodda korunur, `KOMUTLAR`; çıktı
  dosyası sürüm adını taşır):
  - v1: ilk komut. Ayar setinde gemma4 43/52, llama3.1 20/52 harf
    kontrolünden geçti.
  - v2: v1'in 9 reddinden sonra (3 yazım/büyük harf düzeltmesi, 4 başlık /
    "Başlık:" satırı silme, 2 bozuk karakter temizliği) iki kural eklendi:
    hiçbir şeyi düzeltme; özet gibi görünmeyen kısımlar (başlık vb.) dahil
    hiçbir şeyi silme, kendi dilinin tarafına koy.
  - v2 sonucu (ayar, gemma4): 46/52 harf kontrolünden geçti; kalan redlerin
    ikisi kopyalama hatası ("saptanan"→"saptananan"), ikisi bozuk karakter
    (`\'`, `¬`), ikisi silme.
  - v3 sonucu (ayar, gemma4): 51/52 kabul, ~1,4 sn/alan (red: orijinaldeki
    yazım hatasını model düzeltti, başlangıç bulunamadı).
  - v3: model metni KOPYALAMAZ; yalnızca ikinci özün ilk 8 kelimesini
    (8: Claude'un seçimi) ve ilk özün dilini yazar. Kod bu kelimeleri
    orijinalde (boşluklar yok sayılarak) arar; tam olarak bir kez bulunursa
    orijinal o noktadan kesilir. Bulunamazsa ya da birden fazla yerde
    bulunursa reddedilir (teknik red; doğruluk kararı yine kullanıcıda).
    Bilinen sınır: tek kesim noktası, TR–EN–TR gibi metinleri bölemez.
  - v3 elle doğrulama (ayar, kullanıcı): 39/50 D (%78). Hatalar: ikinci
    özün başlığı yanlış tarafta (5), dil iki kez değişiyor — ör. bmj
    dergisinde EN özün sonunda "Turkish Başlık: … Anahtar Kelimeler: …" (4),
    metin aslında tek dilli, eski kural iki dilli sanmış (3).
  - v4: model metnin TÜM dil parçalarını sırayla listeler (her parçanın ilk
    8 kelimesi + dili). Kod her başlangıcı bir öncekinden sonra arar (tam bir
    kez bulunmalı), orijinali bu noktalardan keser; TR parçalar TR öze, EN
    parçalar EN öze (sırayla) gider. İlk parça metnin başından başlar.
    Başlık, kendisinden sonra gelen öze aittir. Taraflardan biri boş kalırsa
    alan **bölünmez** (`tek_dil`; mekanik kontrol), kullanıcı "tek dilli mi"
    diye D/Y işaretler.
  - Test setinde aynı makalenin aynı metinli alanları (TR ve EN etiketli
    alanda tekrar) bir kez sayılır; ayar seti değiştirilmedi.
- **Bilinen sınır:** Harf kontrolü modelin metni değiştirdiğini yakalar ama
  sınırın doğru yerde olduğunu garanti etmez; bunu yalnızca elle kontrol ölçer.

- **KARAR (kullanıcı, 2026-11-01): iki dilli alanlar analiz dışı.**
  Ayar setinde en iyi sonuç v3 (39/50 doğru, %78); v4 geriledi (27/52
  kontrolden geçti, 20/27 doğru). Ön kayıtlı eşik (%98) uzakta olduğundan
  test setine geçilmedi ve önceden belirlenen yedek plan uygulandı.
  Uygulama: `oai_ayristir.py` iki dilli alandan bölünen parçaları `ozet_tr` /
  `ozet_en` olarak seçmez (analiz kodları yalnızca bu alanları okur).
  Parçalar ve `orijinal_metin` `ozler` içinde kalır (kullanıcı: "gerekirse
  sonradan ekleriz"). Ayrıştırma raporu, bu yüzden bir dilde özeti kalmayan
  makale sayısını verir. Gerekçe: iki dilli alanlar TR etiketli özlerin
  ~%1,4'ü ve çoğunlukla eski yıllarda (2016: 1.017 → 2025: 58), yani LLM
  dönemi yıllarını neredeyse etkilemez; etki taban yıllarında küçük.
  Makalede raporlanacak: kural %32, yerel LLM %78 (ayar seti), eşik %98.

### 4.5 Bozuk karakterler (ölçüm aşaması, `toplama/karakter_kontrol.py`)
- LLM bölme denemesinde görüldü: `Üniversitesi\'nde` (kaçış hatası),
  `bu¬lunmaktadır` (PDF tirelemesi). Kelime sıklığını da bozar.
- Düzeltme modele değil kurala bırakıldı (tekrarlanabilir, sayılabilir,
  tüm özetlere uygulanabilir). Kural yazılmadan önce ölçüm: tür başına
  sayım + 10 rastgele örnek (tohum 20261031) Excel'de kullanıcı tarafından
  D/Y işaretlenir. `¬` yalnızca iki harf arasındaysa (arada boşluk olabilir)
  tireleme sayılır; diğer `¬` (mantıkta "değil") ve diğer `\` kullanımlarına
  dokunulmaz, yalnızca sayılır.
- **Ölçüm (2026-11-01, 1.314.493 öz):** görünmez tire 4.359 öz (%0,33),
  çok katmanlı HTML kaçışı 4.035 (%0,31), diğer `\` 3.702 (%0,28; LaTeX,
  dokunulmaz), harf¬harf 1.819 (%0,14), `\'` 1.770 (%0,13).
  **Yıllara göre (10.000 özde):** görünmez tire 2010–2016 ~43–74, 2017–2019
  ~18–24, 2020'den sonra ≤1; HTML kalıntısı 2010–2013 ~60–168, 2015'ten sonra
  ~0; harf¬harf 2–12 (dalgalı); `\'` ~0,5–2. Yılı güvenilmez (arşiv) özlerde
  hepsi yüksek (analiz dışı zaten). → Bozukluk zamanla AZALIYOR: temizlenmezse
  eski yıllarda bazı kelimeler eksik sayılır, sonraki yıllarda "artış" gibi
  görünür. Görünmez tirenin düşüşü 2017–2020'ye, yani taban (baseline)
  yıllarına denk geliyor. Temizliğin gerekçesi bu.
- **Doğrulama örneklemi (kullanıcı kararı, 2026-11-01):** her tür için
  "%95 doğruluk" gösterilebilecek kadar örnek: hepsi doğru çıkarsa %95
  Wilson aralığının alt sınırı ≥%95 olacak en küçük n = **73** (alt sınır
  = n/(n+1,96²)). Adayı 73'ten az olan türde (harf¬ harf: 35) hepsi
  incelenir. Toplam ~546 satır. Bir tek hata alt sınırı %92,6'ya indirir;
  o durumda oran ve aralık olduğu gibi raporlanır.
- **KARAR (kullanıcı, 2026-11-03): `\'` ve `\"` kaçış hataları
  DÜZELTİLMEZ.** Analiz yalnızca harf dizilerini kelime sayar; ters eğik
  çizgi ve tırnak zaten kelime sınırı olduğundan bozuk ve düzeltilmiş hal
  aynı kelimeleri verir ("29\'u" ve "29'u" → `u`). Yıllara göre de sabit
  (~0,5–2 / 10.000). Düzeltme ise LaTeX harf kodlarını bozuyordu
  (`Schr\"{o}dinger` = Schrödinger, `Szeg\"{o}`; DergiPark bunları ham
  gösteriyor). Doğrulamada görülen örnekler: `bag\'in`, `29\'u` (gerçek
  hata, sitede de aynı; kaynak DergiPark kaydı), `\"{o}` (LaTeX). Diğer `\`
  (LaTeX) ve harf arasında olmayan `¬` de dokunulmaz → doğrulanmaz.
  **Temizlenecek türler:** görünmez tire, harf¬harf, harf¬ harf, HTML
  kalıntısı (73 + 73 + 35 + 73 = 254 örnek).
- **Doğrulama sonucu (kullanıcı, 2026-11-03), hiç Y yok:** görünmez tire
  73/73 (%95 alt sınır %95,0); harf¬ harf 35/35 (türün tamamı);
  HTML kalıntısı 71/71 (%94,9; 2 boş); harf¬harf 65/65 (%94,4; 8 boş).
- **Kural (`oai_ayristir.py` `temiz()`, tüm dc alanlarına):** (1) HTML
  kaçışı değişmeyene kadar çözülür (en fazla 5 kat; eskiden sabit 2);
  (2) görünmez tire (U+00AD) silinir; (3) iki harf arasındaki `¬` (arada
  boşluk olabilir) silinir; harf arasında olmayan `¬` (mantık) korunur.
  `\'`, `\"`, LaTeX dokunulmaz. Her düzeltmenin kaç metinde yapıldığı
  ayrıştırma raporunda. Kontrol: yeniden ayrıştırmadan sonra
  `karakter_kontrol.py` bu türler için ~0 göstermeli.
- **Türkçe görünmez tire seti (kullanıcı, 2026-11-03; ilk setteki
  makaleler hariç, 73 örnek):** iki ayrı kelimenin birleşmesi 0/73; görünmez
  tire + boşluk ("neden[gt] le") 8/73. → Kural genişletildi: iki harf
  arasındaki görünmez tire arkasındaki boşlukla birlikte silinir (`¬`
  kuralıyla aynı); 8 örneğin hepsi test edildi, doğru birleşiyor.
  Zemberek ile karar (kullanıcı önerisi) görünmez tire için gereksiz
  bulundu (birleşik terim hatası görülmedi; yavaş; yalnızca Türkçe).

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
- **Plan (kullanıcı onayı, 2026-11-03):** bozuk karakter temizliğinden
  sonra `birlesik_kelime.py rapor` ile boşluk kaybının oranı ve yıllara göre
  dağılımı ölçülecek; onarımlardan örneklem kullanıcı tarafından
  doğrulanacak. Yanlış bölme görülürse **Zemberek kontrolü** eklenecek:
  Zemberek bütün kelimeyi tanıyorsa bölünmez; tanımıyor ama iki parçayı
  tanıyorsa bölünür (kullanıcının fikri).
- **İlk ölçüm (2026-11-04, temizlenmiş veri, sözlük 447.503 kelime):**
  rapor TR özlerin %79–94'ünde "birleşik" kelime ve 100 kelimede 1,8–8,1
  onarım gösterdi. En sık 40 onarımın ~26'sı **yanlış**: `verilerde →
  veriler + de`, `bağlamındaki → bağlamında + ki`, `göreve → göre + ve`,
  `ölçeğine → ölçeği + ne`, `alanya → alan + ya`, `işgören`, `anadili`…
  Sebep: "≥20 kat seyrek" ölçütü + `de/da/ki/ne/ve/ya` hem ek hem bağımsız
  kelime; önceki gerekçe ("ekler tek başına kelime olmadığı için risk
  düşük") bu ekler için YANLIŞ. Doğru olanlar: `birşekilde`, `ileilgili`,
  `olmaküzere`, `buaraştırmanın`, `eldeedilmiştir`, `bunedenle`…
  → Otomatik onarım KAPATILDI (sözlük dosyası devre dışı); Zemberek
  kontrolü tasarlanacak. Gerçek boşluk kaybının 2017–2019'da yoğunlaştığı
  görülüyor (100 kelimede 7–8 vs. sonraki yıllarda ~2), ama sayılar yanlış
  bölmelerle şişkin; temiz ölçüm Zemberek'ten sonra.
- **Yeni yöntem (kullanıcı onayı, 2026-11-04):** sıklık kuralı yalnızca
  ADAY üretir. Her aday için: (1) TDK madde başıysa bölme; (2) Zemberek
  tamamını tanıyorsa bölme; (3) parçalar TDK'de iki kelimelik maddeyse böl;
  (4) Zemberek (ya da TDK) her parçayı tanıyorsa böl; (5) aksi halde bölme.
  Zemberek ölçütü tez reposundaki `zemberek_gecerli_mi` ile aynı (en az bir
  çözümleme). TDK: Güncel Türkçe Sözlük madde başları (MIT,
  ogun/guncel-turkce-sozluk), tez reposundan kopyalandı
  (`analiz/kaynaklar/`). Yalnızca Türkçe; İngilizce onarım kapalı.
- **Kullanıcı kontrolü (zorunlu, son karar kullanıcıda):** `bol` ve `bolme`
  gruplarından 73'er kelime, geçtikleri özet sayısıyla ağırlıklı rastgele
  (tohum 20261104; sık onarım daha olası → metne etkiyi temsil eder).
  Analiz betikleri YALNIZCA kullanıcı onayından sonra `onayla` ile yazılan
  `birlesik_onayli_tr.tsv`'deki bölmeleri uygular; liste yoksa hiçbir kelime
  bölünmez (canlı sıklık kuralı analizden kaldırıldı).
- **v1 doğrulaması (kullanıcı, kısmi):** bölünen grupta 42/72 doğru (%58).
  Hatalar: yanlış yerden 3'e bölme (19), Zemberek'in bilmediği tek kelime
  (11). → **v2 kuralları (kullanıcı onayı 2026-11-05):** yalnızca iki
  parça; bölme noktasını Zemberek/TDK seçer (iki parça da TDK'de, beyaz
  listede ya da ≥30 özet + Zemberek); iki harfli parça yalnızca kısa kelime
  listesinden (bu, şu, su, de, da, ve, ne, ya, en, iş, ön, az, el, ay, on,
  öz — Claude'un seçimi); yalnızca ek olan parça (ini, den, lar…) geçersiz;
  beyaz liste ve zorla-böl listesi (`analiz/kaynaklar/`, veriden sonra,
  tarih ve kaynakla). Excel sorusu T/B olarak değiştirildi.
- **v2 ön testi (Claude, gerçek Zemberek; sözlük bu ortamda yok, bütün
  parçalar "sık" sayıldı = en gevşek durum):** kullanıcının D verdiği 42
  bölmeden 40'ı aynı (kayıp: 3 parçalı `akreditasyon…`, `değişikliğinen`
  eşitlik bozulması); Y verilen 30'un ~28'i düzeldi (19 doğru yerden
  bölme, 9 bölünmeme). Kalan riskler sıklık eşitliğinden (`model +
  inegöre`, `bar + sakla`); gerçek sözlükle ortadan kalkması bekleniyor —
  kullanıcının makinesinde `karsilastir` ile doğrulanacak.
- **v2 doğrulaması, 1. tur (kullanıcı, 2026-11-05):** bölünen 70/73
  (%95,9; GA 88,6–98,6) — hatalar özel ad/yazım hatası (cihanzâde, bankya,
  habitatda); bölünmeyen 70/72 (%97,2; GA 90,4–99,2).
- **2. tur (kullanıcı kararı):** daha dar güven aralığı için yalnızca
  bölünen grupta 73 yeni kelime (`ek_tur`; önceki Excel'lerdeki kelimeler
  hariç, tohum 20261106, aynı ağırlıklı seçim). **Kurallar donduruldu:** aynı
  `birlesik_karar_tr.tsv` kullanılır; 1. turda bulunan 3 kelime beyaz
  listeye 2. tur bitmeden eklenmez. Sonuç iki tur birleştirilerek
  (`hesapla --excel-listesi`) raporlanır. Beklenti (Claude): hata ~%4
  sürerse 146'da ~%95,9 (GA ~91–98); alt sınırın %95'i geçmesi için ≤2 hata
  gerekir.
- **SONUÇ (kullanıcı, iki tur birleşik, 2026-11-05):** bölünen grup
  **142/146 doğru = %97,3 (%95 Wilson 93,2–98,9)**; 2. tur tek başına 72/73.
  Bölünmeyen grup 70/72 = %97,2 (90,4–99,2). Makalede raporlanacak sayı bu
  (beyaz listeye sonradan eklenen kelimelerden ÖNCEKİ ölçüm).

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
