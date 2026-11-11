# Günlük İlerleme Günlüğü

Bu dosya, her çalışma günü sonunda o gün yapılanların kısa özetini tutmak
için. Amaç: makaleyi yazarken "o gün ne yapmıştım, neden öyle karar
vermiştim" diye geriye dönüp bakabilmek.

**Nasıl kullanılır:** Her gün çalışmanın sonunda, en alta yeni bir
`## YYYY-AA-GG` başlığı ile o günün özeti eklenir (ne yapıldı, hangi kararlar
alındı, bir sonraki adım ne). Eskiye dönüp düzenleme yapılmaz, sadece
eklenir; böylece kronolojik bir kayıt oluşur.

---

## 2026-10-23 — 2026-10-24 — Fikir, veri toplama altyapısı, tüm DergiPark toplaması

### Fikir ve kapsam
- Kaynak çalışma: Kobak, González-Márquez, Horvát, Lause (2025), Science
  Advances (arXiv:2406.07016). PubMed'de 15M+ özet; ChatGPT sonrası "delve,
  underscores, showcasing" gibi üslup kelimelerinin beklenenden fazla artışı;
  2024 özetlerinin **en az %13,5**'i LLM ile işlenmiş. Eğitilmiş dedektör
  yok; "fazla ölüm" analizine benzer karşı-olgusal yöntem. Alt sınır olmasının
  bir nedeni: bazı yazarlar bu kelimeleri fark edip siliyor.
- Plan: Aynı yöntemi DergiPark'taki Türkçe özlere uygulamak. Özgün katkılar:
  - Eklemeli Türkçe için kelime yerine kök, n-gram ve ek düzeyinde analiz.
  - Aynı makalenin TR özü ve EN abstract'ı arasında iki dilli karşılaştırma.
  - 2025–2026'da işaretçi kelimelerde olası düşüş (izleri silme).
- **Öncelik:** Ana analiz Türkçe özler. EN abstract'lar yöntemin bu veride
  çalıştığını doğrulamak için (bilinen İngilizce işaretçiler), iki dilli
  karşılaştırma ek bulgu.
- SIU 2027'ye bu değil, başka bir çalışma gönderilecek. Bu çalışma için yayın
  yeri (dergi/konferans) sonra belirlenecek.

### Hocanın görüşü
- "Aynısını uygulayabiliriz. Osmangazi'nin yayınlarına da bak, orada
  tanıdığımız var. Eski dergilere istek gönderebiliriz, makaleleri toplu
  paylaşsınlar diye."
- Karar: Veri önce DergiPark'tan; ESOGÜ ve eski dergilerden gelecek veri
  sonra eklenecek. Hakeme ilk gönderilen / reddedilen makaleler (etik kurul
  gerektirir) şimdilik yok.
- ESOGÜ dergi listesi ve iki e-posta taslağı: `notlar/veri_plani.md`.

### Repo
- Tez reposundan (TR-LLM-Analiz) ayrı repo açıldı: `Simya00/dergipark-llm-izi`
  (private). Claude GitHub uygulamasına bu repo için erişim verildi.

### Veri toplama betikleri (`toplama/`)
- `oai_topla.py`: DergiPark'ın açık OAI-PMH arayüzünden
  (`https://dergipark.org.tr/api/public/oai/`) toplu üstveri indirir. İzin
  gerekmez. Ham XML sayfaları `ham/` altına sıkıştırılmış kaydedilir;
  kesilirse kaldığı yerden devam eder (`durum.json`).
- `oai_ayristir.py`: Ham sayfaları `makaleler.jsonl`'e çevirir (başlık, TR öz,
  EN abstract, yıl, dergi, cilt/sayı) ve özet tablo basar.
- Neden Hugging Face'teki hazır veri seti (`musapeker/dergipark-tr-en-abstracts`)
  değil: hangi alanları/filtreleri kullandığı doğrulanamadı; kendi düzeltmelerimizi
  uygulayabilmek ve makalede tekrarlanabilirlik için kendi toplamamız. O veri
  setinin açıklamasındaki ~843 bin kayıt sadece toplamın tahmini için kullanıldı.

### Gerçek veride öğrenilenler ve düzeltmeler
- **Arayüz:** Sayfa başına 100 kayıt; toplam sayı verilmiyor. `ListSets` en
  fazla 100 dergi döndürüyor (devam yok) ama set adı = dergi kısa adı
  (`ogummf` gibi), doğrudan istenebiliyor. Tüm kayıtların datestamp'i
  yenilenmiş; tarih süzgeci işe yaramıyor. Gönderilme tarihi OAI'de yok.
  Desteklenen formatlar: `oai_dc`, `oai_mods`, `oai_etdms`, `oai_marc`.
- **Metin temizliği:** HTML kaçışları (`TBMM&#039;nin`) çözülüyor; dil
  etiketleri `tr-TR`/`en-US` → `tr`/`en`; dergi URL'den çıkarılıyor
  (`dergi_kodu`).
- **EN abstract:** Mülkiye'nin eski makalelerinde EN abstract yok (sayfada da
  yok, dergiye özgü). ESOGÜ Mühendislik'te 100 makalenin 97'sinde TR+EN var
  → iki dilli karşılaştırma mümkün. 2019 öncesi EN abstract'lar OAI'de büyük
  ölçüde eksik → EN/iki dilli taban en erken 2020–2022.
- **ESOGÜ pilotu** (`ogummf`, `ogusbd`, `esoguifd`, `esogutd`): 1.871 makale.
- **Arşiv tarihi sorunu:** Dergiler DergiPark'a geçerken eski sayıları toplu
  yüklemiş; `dc:date` yükleme tarihi. Sayfadan kontrol: `ogusbd` Cilt 10
  gerçekte 2009 (görünen 2014); `ogummf` Cilt 10 gerçekte 1997 (görünen 2017).
  Cilt'ten yıl tahmini `ogummf`'de tutmadı → arşiv makalelerine yıl
  uydurulmuyor: aynı gün ≥3 farklı cilt yüklenmişse toplu yükleme sayılıyor,
  bu makaleler `arsiv: true`, `yil_guvenilir: null`. **Analizde
  `yil_guvenilir` kullanılır.**
- **Yılla numaralanan ciltler** (`bmj`: "Vol. 2014"): arşiv kuralı bunları
  tamamen atıyordu; artık cilt yıl gibiyse yayın yılı olarak kullanılıyor
  (`yil_kaynagi: cilt_yil`). 1990–2027 dışı yıllar (1902, 2068) geçersiz.
- **Sunucu sorunları:**
  - HTTP 429 (çok hızlı): bekleme uyarlanır hale getirildi; toplama
    `--bekleme 3` ile çalıştırılıyor.
  - Sayfa 1317'de bozuk XML (kontrol karakteri vb.) → onarım eklendi; o
    sayfada okunamayan 4 kayıt atlandı.
  - HTTP 500 ile ~2 dk kesinti → toplama durdu; deneme sayısı 6 → 12
    (~40 dk bekler). Yeniden başlatınca devam etti (geçici kesintiymiş).
- **Bellek:** Ayrıştırıcı iki geçişli yapıldı (100 bin sahte kayıtta ~86 MB).
- **Disk tahmini:** `ham/` birkaç yüz MB, `makaleler.jsonl` 2–3 GB.

### Ara sonuç (142 bin makale, ~%17)
- 2016–2025 arası her yıl güvenilir yıllı 6–7 bin makale. Makalelerin ~%35'i
  arşiv olarak dışarıda; 2019 sonrası kayıp %10–20, 2023 sonrası ~0.
- Not: `ausbf` neredeyse tamamen arşiv sayılıyor (ilk güvenilir yıl 2019);
  kural burada fazla temkinli olabilir. Sabit dergi paneliyle kontrol edilecek.

### Analiz kodu (`analiz/`) — kelime biçimi düzeyi
- `kelime_siklik.py`: Her kelimenin her yıl kaç özette geçtiği.
- `asiri_kullanim.py`: Karşı-olgusal `q_T = p_2022 + (T−2022)·max(p_2022 − p_2021, 0)`,
  fark ve kat; aday kelime listesi.
- `alt_sinir.py`: İşaretçilerle `L ≥ (p − q)/(1 − q)`.
- Sahte veriyle doğrulandı (gerçek LLM oranı 2023: %5, 2024: %15, 2025: %20,
  2026: %22): 6 işaretçinin 5'i en üstte; alt sınır %4,6 / %13,7 / %17,0 /
  %20,2 (gerçeğin altında, beklendiği gibi).
- Türkçe küçültme: "COVID" gibi kısaltmalar "covıd" olmuyor.

### Kelime grupları ve hazır liste
- Türkçede iz büyük ihtimalle kalıp ifadelerde ("önemli bir rol
  oynamaktadır", "ışık tutmaktadır"): tek kelimeler sıradan, grup olarak
  LLM'e özgü. → `kelime_siklik.py --n 2/3/4` ile kelime grupları eklendi
  (cümle/yan cümle sınırını aşmaz; bellek için parçalı sayım).
- Hazır liste kontrolü eklendi (`liste_kontrol.py`): veriye bakmadan önce
  yazılan aday ifadeler doğrudan test ediliyor. Başlangıç listeleri:
  `analiz/aday_liste_tr.txt` (Türkçe tahminler), `analiz/aday_liste_en.txt`
  (Kobak vd. kelimeleri; makalenin ek listesiyle karşılaştırılacak).
  Veriden keşif + hazır liste birlikte kullanılacak.
- Sahte veri testi: gizlenen kalıplar 16–23 kat çıktı, içlerindeki yaygın
  kelimeler artmamış göründü (sadece kelimeye bakmak izi kaçırırdı).

### Literatür taraması (ilk) — ayrıntı: `notlar/literatur.md`
- Türkçe özetlerde aşırı kelime yöntemiyle LLM yaygınlığı ölçen çalışma
  bulunamadı ("Türkçe için ilk" şimdilik geçerli). Türkçede sadece dedektör
  çalışmaları var (Er & Çoğalmış 2024 vb.).
- **Kritik:** Lee (2026, arXiv:2609.07447) Korece için biçimbilime duyarlı
  aşırı kelime analizi + aynı makalelerin İngilizce özetleriyle karşılaştırma
  + 2018–2026 zaman çizgisi yapmış. Koo, Kim, Kim (2026) de Korece. → Bizim
  "eklemeli dil" ve "iki dilli" katkılarımız tek başına özgün değil.
- Üstüne katılabilecekler (aday): Korece ile karşılaştırma (aynı tür LLM
  tercihleri diller arası aktarılıyor mu?), kalıp ifade (n-gram) düzeyinde
  alt sınır, ek düzeyi (-mektedir/-iyor, edilgen), DergiPark arşiv tarihi
  sorununun yöntemsel çözümü, alanlara/üniversitelere göre kırılım, birden
  çok LLM ile (Türkçe yerel modeller dahil) doğrulama deneyi, 2025–2026
  düşüş/düzleşme. Lee (2026) tam metni okunduktan sonra kesinleşecek.

### Ek (suffix) düzeyi analiz — ertelendi
- Fikir: Tez çalışmasındaki (TR-LLM-Analiz) "LLM'in en çok kullandığı ekler"
  analizini buraya bağlamak. İki parça: (1) eski DergiPark özetlerini
  LLM'lere yeniden yazdırıp orijinalle ek yoğunluğunu karşılaştırmak (LLM ek
  profili), (2) DergiPark'ta eklerin yıllara göre beklenenden fazla artıp
  artmadığı (Kobak hesabı eklere).
- Zemberek hızı ~600 kelime biçimi/sn → tüm özetler için önbellekle ~1–2 saat.
- **Karar:** Şimdilik ertelendi. Ek profili tek bir modelden çıkarılırsa
  güvenilir sayılmaz; birden çok LLM'den (ör. Llama, Gemma, Qwen + ChatGPT,
  Claude, Gemini) alınıp birleştirilmeli (ortak ve modele özgü ekler ayrı).
- Ama DergiPark tarafı (eklerin yıllara göre değişimi) modelden bağımsız →
  şimdi yapılıyor: `analiz/ek_siklik.py` (ek ve ek zinciri sıklığı + 100
  kelimede yoğunluk; Kobak hesabı `asiri_kullanim.py` ile). Sahte veride
  "-mAktAdIr" artışı ~11 kat, edilgen "-Il+mAktAdIr" ayrı zincir olarak
  bulundu. LLM ek profili deneyi (çok modelli) hâlâ ertelendi.

### Toplama tamamlandı — son tablo
- **8.468 sayfa, 844.745 makale, 3.124 dergi.**
- Güvenilir yıllı makale: 2021: 57.347, 2022: 58.172, 2023: 58.416,
  2024: 60.547, 2025: 65.057, 2026 (kısmi): 22.149. TR öz yılda 48–56 bin,
  EN abstract 46–63 bin, TR+EN 36–53 bin.
- Yıl kaynağı: tarih 624.728, arşiv 173.496, aralık dışı 40.665, cilt-yıl 5.856.
- Bazı dergiler tamamen arşiv sayıldı (`aott`, `politeknik`, `opus`: muhtemelen
  yakın zamanda toplu yeniden yüklenmiş) ya da geç başlıyor (`gazimmfd` 2023,
  `pajes` 2022, `kefdergi` 2021).
- → **Dergi karışımı sorunu:** geç katılan dergiler tabanda yok, hedef yılda
  var; LLM olmadan sahte "artış" üretebilir. Çözüm: `analiz/dergi_paneli.py`
  (2021–2025 her yıl ≥5 makale) + tüm analiz betiklerine `--dergiler`. Sahte
  veride sahte artış (133 kat) panelde sıfıra indi. Ana sonuçlar hem tüm
  veride hem panelde raporlanacak.

### Birleşik kelime sorunu
- Örnek özetlerde (incelemeyi kullanıcı yaptı) çok sayıda boşluğu kaybolmuş
  kelime: "küçükmeyve", "rakımlaragöre", "yaşamımızınayrılmaz",
  "arızadankaynaklanan", "biryandan" (muhtemelen PDF'ten kopyalama).
  Zemberek'i ve kelime sayımını bozar; oran yıllara göre farklıysa sahte
  artış üretebilir.
- Çözüm: `analiz/birlesik_kelime.py` (veriden sözlük + yıllık oran raporu);
  `kelime_listesi()` sözlük varsa birleşik kelimeleri otomatik bölüyor
  (parçalar ≥30 özet; kelime <3 özet veya parçadan ≥20 kat seyrek).
  10 gerçek örneğin hepsi doğru bölündü, sağlam kelimeler bölünmedi.

### Aday liste üzerine (kullanıcı)
- Liste eksik görünüyor. 2025–2026 makalelerini okuyup eklemek "veriye
  bakmış" olur → öneri: 2019 özetlerini birkaç LLM'e yeniden yazdırıp
  eklenen ifadeleri toplamak. Mevcut liste git'te tarihli ("ön kayıtlı");
  sonradan eklenenler ayrı dosyada (`aday_liste_tr_ek.txt`) raporlanacak.
- Kullanıcı gözlemi: "bir parçası haline gelmiştir", "göre
  değerlendirilmiştir", "nedeniyle" gibi klasik kalıplar LLM öncesi de çok
  yaygın. → Yöntem "beklenenden fazla artış"a baktığı için bunlar elenir;
  ayrıca **kontrol listesi** olarak kullanılacak (artmamalı; azalıyorsa LLM
  geleneksel kalıpların yerini alıyor olabilir). `aday_liste_tr_kontrol.txt`
  kullanıcının katkısıyla hazırlanacak.

### İlk LLM yeniden yazım denemesi (kullanıcı)
- 3 DergiPark özeti ChatGPT'ye "akademik dile uygun
  yeniden düzenle" komutuyla verildi. Eklenen ifadeler →
  `analiz/aday_liste_tr_llm.txt` (orijinal aday liste değişmedi).
- Gözlemler:
  - Eklenenlerin çoğu geleneksel Türk akademik kalıbı ("elde edilen
    bulgular", "çalışma kapsamında", "ortaya koymuştur"). İngilizcede
    "delve" gibi yeni kelimeler gelirken Türkçede LLM'in mevcut kalıpları
    abartıyor olabileceği hipotezi → iz daha zayıf, alt sınır daha düşük
    çıkabilir; kontrol listesi daha da önemli.
  - Ek düzeyi aday: "-ebilmektedir" (Able+Prog2+A3sg+Cop: "sunabilmektedir",
    "etkileyebilmektedir").
  - İmla adayı: şapkalı yazım ("hâline"; orijinalde "haline"). Kelime
    seçiminden bağımsız bir işaret olabilir.
- Sınırlılık: tek model, tek komut, 3 özet. Gemini/Claude/yerel modellerle
  ve nötr komutla tekrarlanacak.

### LLM yeniden yazım deneyi (200 özet × 3 model) — kurulum
- Kullanıcı kararı: 3 özet yetmez; 2018–2021'den rastgele 200 özet,
  ChatGPT + Claude + Gemini'ye aynı komutla verilecek, cevaplar elle
  yapıştırılacak.
- `deney/deney_hazirla.py`: seçim (her dergiden ≤1, 400–1500 karakter,
  birleşik kelimeli özetler hariç, sabit tohum 20261024) →
  `deney/deney_ornekleri.json` (model cevapları boş).
- `deney/deney_yapistir.py <model>`: sırayla komut + özeti gösterir, cevap
  terminale yapıştırılıp `###` ile kaydedilir (elle JSON düzenleme hatası
  olmasın diye). Kurallar: aynı komut, sık sık yeni sohbet, hafıza kapalı,
  model sürümleri not edilecek.
- Bu deney hem ortak LLM işaretçilerini (kelime/kalıp/imla) hem ertelenen
  çok modelli ek profilini verecek.
- Kullanıcı önerisi: Claude Pro'ya tüm dosyayı tek seferde vermek. Karar:
  üç modele de **aynı** 10'arlı JSON paketleriyle sorulacak (`--paket 10`;
  model başına ~20 yapıştırma). Gerekçe: koşullar modeller arasında aynı
  olmalı; tek seferde toplu işte kısaltma/benzeşme olur ve çıktı sınırına
  takılır. Claude cevapları claude.ai'dan; kod asistanı hipotezi bildiği
  için üretmiyor.

### Durum (2026-10-24 sonu)
- Toplama ve ayrıştırma bitti; analiz çalıştırılmaya hazır (önce sözlük).

## 2026-10-25 — Deney başladı; yanlış dil etiketleri

- Kullanıcı ChatGPT ile ilk paketi denedi. Sorunlar ve düzeltmeler:
  - ChatGPT cevabı ekrandan seçilip kopyalanınca köşeli parantezler `\[ \]`
    geliyor; `###` metnin sonunda aynı satırda kalabiliyor → yapıştırma
    yardımcısı ikisini de kabul ediyor.
  - **9. örnek İngilizceydi** ama DergiPark'ta Türkçe öz olarak etiketliydi
    (Irak telekomünikasyon makalesi); ChatGPT akademikleştirmek yerine
    çevirdi. → Bazı dergiler İngilizce abstract'ı Türkçe alanına (ya da
    tersini) girmiş.
- Düzeltmeler:
  - `toplama/oai_ayristir.py`: etiket ile metnin dili açıkça çelişiyorsa
    (`dil_kesin`: ≥5 işlev kelimesi, 3 kat baskın, Türkçe harf kontrolü)
    metnin diline göre düzeltiliyor (`dil_kaynagi: etiket_duzeltildi`).
    Karışık/kısa metinlerde etikete dokunulmuyor. → `makaleler.jsonl`
    yeniden üretilmeli.
  - `deney/deney_hazirla.py`: Türkçe olmayan özetler seçilmiyor;
    `--degistir` var olan dosyadaki uygun olmayan örnekleri yenileriyle
    değiştiriyor (diğer cevaplar korunuyor).
- Kullanıcı: önce kaç özetin yanlış etiketli olduğunu ölçmek, ayrıca aynı
  alanda iki özet (TR + EN) olan kayıtları tespit etmek gerekiyor; adım
  adım. → `toplama/dil_kontrol.py`: cümle düzeyinde dil tespiti, hiçbir şeyi
  değiştirmeden sayar (yanlış etiket / iki dilli / belirsiz), yıllara ve
  dergilere göre dağılım, örnekler, `dil_sorunlari.tsv`. Sonuca göre
  çıkarma/bölme kararı verilecek.
- **Dil kontrolü sonucu (temizlik öncesi):** TR etiketli 674.199 özün
  %3,17'si (21.345) İngilizce, %1,38'i (9.334) iki dilli; EN etiketli
  626.547 özün %1,96'sı (12.264) Türkçe, %0,72'si (4.508) iki dilli.
  TR→EN yanlış etiket yıllara göre sabit (2017'den beri ~1.300–1.600/yıl,
  ~%3) → sonuçları çarpıtmaz, gürültü. İki dilli alanlar azalıyor
  (2016: 1.017 → 2025: 58). Örneklerde ek sorunlar: PDF'ten bozuk
  kodlamayla kopyalanmış metin ("^ŝŶĂŶ 'ƺůŚĂŶ͛ŦŶ", Türkçe sanılmıştı),
  Almanca özetler, başta "Özet"/"Abstract" başlıkları.
- **Temizlik (`oai_ayristir.py`):** bozuk metin atılır (harflerin >%20'si
  alfabe dışı); cümlelerin ≥%80'i diğer dildeyse etiket düzeltilir; iki
  dilli alan bölünür (TR cümleler TR öze, EN cümleler EN abstract'a); başka
  dildeki metin ("diğer") ayrılır; "Özet"/"Abstract" başlığı atılır
  ("Özetle", "Özellikle" korunur). `dil_kontrol.py` artık temizlik
  sayılarını ve temizlik SONRASI kalan sorunları gösteriyor. Sahte testte
  temizlik sonrası kalan sorun sıfır. → `makaleler.jsonl` yeniden üretilmeli.

### Çalışma şekli değişti
- Kullanıcı: "Kodun doğru olduğunu nasıl bileceğim? Anlatmam lazım, yoksa
  bu benim değil senin çalışman olur." → Üç karar:
  1. Kod birlikte okunacak; her seferinde kod sohbette gösterilip satır
     satır açıklanacak (ilk olarak dil temizliği kodu okundu).
  2. Yeni kural/eşik eklemeden önce anlatılacak, kararı kullanıcı verecek.
  3. Her adım `notlar/yontem.md`'ye (eşik + gerekçe + doğrulama durumu).
- Kurallar repo köküne `CLAUDE.md` olarak yazıldı (sonraki oturumlar da uysun).
- Eşiklerin çoğunun Claude'un seçimi olduğu ve elle doğrulanmadığı yöntem
  notunda açıkça belirtildi; dil temizliği için elle kontrol planlanıyor.

### Dil temizliğinin elle doğrulanması — kurulum
- Kullanıcı onayıyla: kategori başına 50 örnek. `toplama/dil_dogrulama.py
  ornekle` → `dil_dogrulama.tsv` (E/H sütunu), `hesapla` → doğruluk + %95
  Wilson aralığı. "Dokunulmadı" kategorisi kaçırılan sorunlar için.

- TSV dosyası uzun metinler yüzünden okunamıyordu → `dil_dogrulama.py
  incele`: örnekleri terminalde tek tek, satırlara bölünmüş gösterir, cevabı
  kaydeder. Ölçek kullanıcıya önerildi: E / K (kısmen) / H; hesaplama hem
  "sadece E" hem "E+K" doğruluğunu veriyor.

- Kullanıcı terminal incelemesini de anlamadı; amaç (özetin dili hakkında
  kodun kararını doğrulamak) sade dille yeniden anlatıldı. İsteği üzerine
  Excel: `dil_dogrulama.py excel` → `dil_dogrulama.xlsx` (sade soru,
  tıklanabilir link, satırlara bölünmüş metin, E/K/H açılır listesi);
  `hesapla` Excel'i doğrudan okuyor.

### Sınır hatalarını azaltma — kararlar (kod yarın)
- Doğrulama örneklerinde iki dilli bölmede sınır hataları görüldü: TR ve
  EN öz arasında nokta/boşluk yok ("…osteopontin AbstractOligodendrogliomas
  are…"), "Keywords:" satırı yanlış tarafa gidiyor, "LaryngealSquamous",
  "RampantCariesLaringealskuamoz" gibi yapışmalar.
- Kullanıcının gözlemleri ve önerileri:
  - Dergiler önce bir dili sonra diğerini yazıyor → **tek geçiş noktası**
    aranabilir (başlık kelimeleri "Abstract/Özet/Keywords/Anahtar Kelimeler"
    ipucu; yoksa en iyi tek kesim noktası).
  - **Anahtar kelime bölümleri özetten atılsın** (konu listesi, üslupla
    ilgisi yok; DergiPark zaten `dc:subject`'te veriyor). Önerilen bitiş:
    nokta / sonraki başlık kelimesi / en fazla 20 kelime. (Tüm özetlerden mi
    yoksa sadece iki dillilerden mi: Claude tüm özetleri önerdi; kesin karar
    bekliyor.)
  - Birleşik kelime onarımı neden çalışmadı sorusu: onarım analiz
    aşamasında ve sadece TR+TR yapışmalar için; dil temizliği ondan önce
    çalışıyor; sözlük de henüz oluşturulmadı. "Laringealskuamoz" = iki
    Türkçe tıp terimi ("Laringeal skuamoz").
  - Büyük harf kuralı (küçük→BÜYÜK harf geçişinde böl) için kullanıcı:
    "istisna listesi yerine **sözlük** daha mantıklı." → **Karar:** ortasında
    büyük harf olan kelime YALNIZCA (a) kendisi verimizde nadirse (<5 öz)
    ve (b) iki parçası da TR/EN sözlükte varsa (≥3 öz) bölünür
    ("LaryngealSquamous" bölünür; "DergiPark", "pH", "McDonald" korunur).
    Elle istisna listesi yedek olarak kalır.
  - **Kısaltma sözlüğü** de yapılacak (Dr., Prof., Doç., vb., vd., örn., s.,
    et al., e.g., i.e. …): bu kısaltmalardan sonraki nokta cümle sonu
    sayılmaz; noktadan sonra büyük harf geliyorsa araya boşluk eklenir.
- Eşikler (5 / 3, 20 kelime) Claude'un önerisi; kullanıcı yaklaşımı onayladı,
  eşiklere yarın son kez bakılacak.

### Kullanıcının kararları (aynı gün, sonradan)
- **Anahtar kelime bölümü SİLİNMEYECEK**; yalnızca dil tespitinde
  görmezden gelinecek (dil kararını etkilemesin). Bölmede başlığına göre
  ilgili tarafa gidecek ("Anahtar Kelimeler" → TR, "Keywords" → EN).
  (Claude'un yorumu; kullanıcı teyidi bekleniyor.)
- **Tek geçiş noktası:** kullanıcı ne olduğunu sordu, sade anlatıldı
  (bütün olası kesim noktalarını deneyip "solu bir dil, sağı diğer dil"e en
  iyi uyanı seçmek; başlık kelimeleri öncelikli kesim noktası). Ekleme
  kararı kullanıcıda.
- **Excel doğrulaması iki kez:** düzeltmelerden ÖNCE ve SONRA, aynı
  örneklerde.
- **Kelime ayırma da doğrulanacak:** birleşik kelime onarımı ve büyük harf
  bölmesi için ayrı Excel sayfası (orijinal / bölünmüş / özetten kesit /
  link, E-K-H).

### Git: yanlışlıkla eklenen dosyalar (2026-10-27)
- Kullanıcının yerel commit'ine deneme/sonuç dosyaları girmişti (küçük;
  GitHub'a gitmedi). İşaretlenmiş `dil_dogrulama.xlsx` ise `.gitignore`
  yüzünden girmemişti. → Commit `git reset --mixed HEAD~1` ile geri alındı;
  `.gitignore` düzeltildi: deneme ve `sonuc_*.txt` çıktıları dışarıda,
  elle girilen araştırma verisi (`dil_dogrulama.xlsx`,
  `deney/deney_ornekleri.json`) bilerek repoda tutulacak.

### Dil temizliği 1. doğrulama sonucu (kullanıcı işaretledi)
- Etiket düzeltme %90 (45/50), iki dilli bölme **%32** (16/50), bozuk
  %100, diğer dil %98, dokunulmadı %100. Ayrıntı: `notlar/yontem.md` §4.3.
- İki dilli bölme hataları sınırda → planlanan düzeltmeler doğrulandı.
- Kullanıcı notları: bozuk sayılanların çoğu Arapça/Yunanca; bazı özetler
  "Amaç: … Yöntem: …" biçiminde (yapılandırılmış özet, özetin kendisi);
  birkaçında "özet eksik/yarım gibi" notu → link üzerinden kontrol edilecek;
  #39 Fransızca metin "diğer dil" kategorisinde H işaretlenmiş (E olmalı
  mı, kullanıcıya soruldu).

### HTML etiket hatası (kullanıcının doğrulamasından)
- "Özet yarım kalmış" notları: #30 metni "(sırasıyla p" diye kesik; makale
  sayfasında "(p <0.001, …)" devam ediyor. Sebep: HTML temizliği
  `r"<[^>]+>"` istatistikteki "<" ile ">" arasını siliyordu. → Yalnızca
  bilinen HTML etiketleri silinecek şekilde düzeltildi; eski kuralın kaç
  özette kayba yol açtığı ayrıştırma raporunda sayılıyor. Kullanıcı
  `oai_ayristir.py`'yi yeniden çalıştırmalı.
- Kullanıcı kontrolleri: #39 → E (Fransızca, "diğer dil" doğru; Excel'de
  düzeltildi), #40/#41/#94 sorun yok (#41'deki bozuk semboller makalenin
  matematik ifadeleri, sitede de öyle). Linkler LibreOffice'te açılmadı
  (Ctrl+tık gerekiyor); sonraki Excel'de adres metin olarak da yazılacak.

### Durum özeti (kullanıcıyla)
- Dil temizliğinde tek ciddi sorun: iki dilli alanların **bölünmesi** (%32
  doğru). **Tespit** iyi (yanlış bölünenlerin hemen hepsi gerçekten iki
  dilli). "Bende Türkçe, sitede İngilizce" farkı linkteki `/en/` yüzünden
  (veri hatası değil). İki dilli alanlar TR özlerin ~%1,4'ü ve azalıyor.
- Karar yolu: önce bölme düzeltmeleri → aynı 50 örnekte yeniden ölçüm;
  doğruluk ~%85–90'ı geçmezse iki dilli alanlar analizden çıkarılır. Her
  durumda "iki dilliler hariç" sağlamlık analizi yapılacak.

### HTML düzeltmesiyle yeniden ayrıştırma (kullanıcı çalıştırdı)
- Eski HTML kuralıyla metin kaybı olan öz: **7.376** (düzeltildi).
- Temizlik: etiket düzeltildi 32.264, iki dilli bölündü 27.502 parça,
  bozuk 7.870, diğer dil 3.230. Türkçe öz 667.475, İngilizce 635.918.

### Bir sonraki adım (yarın)
1. Kullanıcı: `git pull` + `toplama/oai_ayristir.py` (HTML düzeltmesiyle);
   raporun sonundaki "Eski HTML kuraliyla metin kaybi" sayısı yöntem notuna.
2. Bölme düzeltmeleri (önce anlat, sonra kodu sohbette göster): başlık
   kelimelerinde bölme ("Abstract", "Keywords", "Özet", "Anahtar
   Kelimeler"), anahtar kelimeler dil kararında görmezden gelinsin, tek
   geçiş noktası, kısaltma sözlüğü, sözlüğe dayalı büyük harf bölmesi,
   noktadan sonra boşluk. Sözlükler: `analiz/birlesik_kelime.py sozluk
   --dil tr` ve `--dil en` (kullanıcının bilgisayarında).
3. Aynı 50 iki dilli örnekte yeniden doğrulama (yeni Excel: Türkçe metne
   `/tr/` linki, adres ayrıca düz metin); kelime ayırma doğrulaması için
   ayrı sayfa.
4. Sonra: deney (ChatGPT/Claude/Gemini), ilk liste kontrolleri, dergi paneli.
5. Bekleyenler: geleneksel kalıplar kontrol listesi, Lee (2026) PDF'i,
   ESOGÜ e-postası.

## 2026-10-31 — İki dilli bölme için yerel LLM pilotu

### Literatür taraması (dil temizliği yöntemi)
- Aynı problemi (TR + EN öz aynı alanda yapışık) çözen çalışma bulunamadı.
  Yakın olanlar: Icelandic Parallel Abstracts Corpus (2021; başlık eş
  anlamlılarıyla özet sınırı), "dil bölütleme" (language segmentation;
  geçiş cezalı Viterbi), SciPar / TURNA / OpenAlex çalışması (fastText,
  langid ile dil kontrolü), Rose vd. (2025; özet temizliği, 9.000 elle
  etiketli özet). arxiv.org bu oturumda erişime kapalıydı; tam metinler
  okunmadı. `literatur.md`'ye eklenmesi kullanıcı onayı bekliyor.

### Karar: iki dilli alanları yerel LLM bölsün (kullanıcı)
- Kullanıcı önerisi: metni doğrudan modele verip ikiye böldürmek, 100
  örnekte denemek, doğruluk yüksekse tümüne uygulamak.
- Claude'un eklediği güvence: modelin parçaları orijinalle harf harf
  karşılaştırılır, kabul edilirse orijinalden kesilir (veriye LLM metni
  girmez). Kullanıcı itiraz etmedi.
- Kararlar: ayar seti (eski 50 örnek) / test seti (yeni 100) ayrı; eşik
  **98/100**; işaretleme yalnızca D/Y (kısmen yok); kontrolleri kullanıcı
  yapacak. Bilgisayar: RTX 5060 Laptop 8 GB (16 değil), 32 GB RAM; Ollama'da
  gemma4:latest, llama3.1:latest (llama3.2 kullanıcı tercih etmiyor).
- Kod: `oai_ayristir.py` iki dilli alanların orijinalini `orijinal_metin`
  olarak saklıyor (bölme kuralı değişmedi); yeni `toplama/llm_bol.py`
  (ornekle / calistir / excel / hesapla). Sahte veri ve sahte modelle test
  edildi; gerçek modelle henüz çalıştırılmadı.

### Bir sonraki adım
1. Kullanıcı: `git pull`, `oai_ayristir.py` yeniden, `llm_bol.py ornekle`.
2. Ayar setinde iki model (`calistir --set ayar`), hız ve red oranları;
   gerekirse komut düzeltilir; model seçilir.
3. Test seti → Excel → kullanıcı D/Y → `hesapla`; eşik 98/100.

### Düzeltme (aynı gün): modelin "emin" alanı kaldırıldı
- Kullanıcı: "Modele yetki vermeyelim, sadece ayırsın; doğruluğu ben
  belirleyeceğim." → Komuttan 4. kural ve JSON'dan `emin` alanı çıkarıldı.
  Tek dil döndürse bile sonuç Excel'e gider, kullanıcı işaretler. Harf harf
  kontrol (teknik güvence) kaldı.

### Ayar seti, ilk çalıştırma (kullanıcı, 52 alan)
- gemma4:latest: 43 kabul / 9 metni değiştirdi (%83 harf kontrolünden
  geçti), ~6 sn/alan. llama3.1:latest: 20 kabul / 32 değiştirdi, ~15 sn/alan
  (bir örnekte 375 sn). → gemma4 açık ara önde; llama3.1 elendi (öneri).
- Tahmini tüm veri süresi (gemma4): ~27.500 × 6 sn ≈ 46 saat (Claude'un
  hesabı; birkaç gece).
- `llm_bol.py farklar` eklendi: reddedilenlerde modelin neyi değiştirdiğini
  kelime düzeyinde gösterir (komutu düzeltmeden önce sebebi görmek için).

### v1 reddlerinin sebepleri ve komut v2 (kullanıcı: "bir deneme daha")
- gemma4 v1'in 9 reddi: 3 düzeltme (#52 "ABSRACT"→"ABSTRACT", #19 büyük
  harf, #29 kelimeyi bozan "düzeltme"), 4 silme (#5, #11, #17: alan içindeki
  makale başlıkları / "Turkish Başlık:"; #26 "Abstract" kelimesi), 2 bozuk
  karakter temizliği (#28 `\'` → `'`, #42 PDF tirelemesi `¬`).
- v2 komutuna iki kural eklendi (düzeltme yapma; hiçbir şeyi silme). v1
  kodda ve dosyalarda korunuyor.
- Önerilen ama bu denemeye girmeyen: `oai_ayristir.py`'de `\'` ve `¬`
  temizliği (kelime sıklığını da etkiliyor) — karar bekliyor.

### v2 sonucu ve sonraki yol (kullanıcı onayı: "senin dediğin gibi")
- gemma4 v2: 46/52 kabul (v1: 43). Düzelenler #11, #17, #19, #52; kalanlar
  #5, #26 (silme), #28, #42 (bozuk karakter), #29 ve yeni #23 (kopyalama
  hatası).
- Kullanıcı ücretsiz API'yi (daha güçlü model) sordu. Claude'un önerisi
  kabul edildi: önce yerel Gemma ile v3 (yalnızca sınırı sordurmak), sonra
  D/Y işaretleme; Gemma yetersizse ayar setinde Groq/Gemini karşılaştırması
  (ücretsiz sınırlar pilot için yeterli; tüm veri için haftalar sürer,
  tekrarlanabilirlik zayıf).
- Bozuk karakterler: modele değil kurala bırakıldı. Önce
  `karakter_kontrol.py` ile sayım + örnek (metne dokunmaz); kullanıcı
  "hepsini nasıl kontrol edeceğim" diye sordu → hepsi değil, tür başına 10
  rastgele örnek.

### v3 sonucu (ayar seti, gemma4)
- **51/52 kabul**, ~1,4 sn/alan (v2: 46/52, ~6 sn). Tek red #52: orijinalde
  yazım hatası "ABSRACTObjective", model "ABSTRACTObjective" yazdı →
  bulunamadı (doğru davranış: kod uydurma bir yerden kesmedi).
- Tüm iki dilli alanlar için tahmini süre: ~27.500 × 1,4 sn ≈ 11 saat (bir gece).
- Kabul ≠ doğru: sıradaki adım ayar setinin D/Y işaretlenmesi.

### v3 ayar seti elle doğrulama (kullanıcı, D/Y)
- Kabul edilen 51'den işaretlenen 50: **39 D / 11 Y → %78** (%95: 64,8–87,2).
  Tümünde (red = yanlış) 39/52 = %75. Eşik (98) çok uzakta.
- Kullanıcı notları: işaretlenmeyen 1 alanda aslında tek dil vardı (kural
  iki dilli sanmış: tespit hatası, bölme değil). 2 makale ikişer kez geçiyor
  (aynı makalede TR ve EN etiketli iki iki dilli alan → ayar 52, 50 değil).
- `llm_bol.py yanlislar` eklendi: Y ve boş satırlarda kesimin iki yanını
  gösterir (sebepleri görmek için; metne dokunmaz).
- Açık öneriler (karar bekliyor): test setinde aynı makalenin aynı metinli
  alanları bir kez sayılsın; "tek dil" çıkan alan nasıl işaretlensin.

### v3 hatalarının sebepleri ve v4 (kullanıcı: "deneyelim")
- Kullanıcı #15, #16, #18'i açtı: EN özün sonunda "Turkish Başlık: …
  Anahtar Kelimeler: …" (TR–EN–TR). 12 hata: başlık yanlış tarafta 5, çift
  dil geçişi 4, aslında tek dil 3.
- Ayrıca görüldü: `p&amp;lt; 0.01` — çok katmanlı HTML kaçışı iki kez
  çözmekle gitmiyor ("amp", "lt" sahte kelime). Öneri: değişmeyene kadar
  çöz (en fazla 5) — karar bekliyor, bozuk karakter kuralıyla birlikte.
- Kod: v4 (parça listesi), `tek_dil` kontrolü, testte tekrar ayıklama,
  `excel --onceki v3` (bölmesi v3 ile aynı satırların cevabını aktarır,
  yalnızca değişenler işaretlenir). Sahte veriyle test edildi.

## 2026-11-01 — v4 sonucu ve karar noktası

### v4 (ayar seti, gemma4)
- 27 kabul, **22 bulunamadı**, 3 tek_dil; ~8,5 sn/alan. İşaretlenenlerde
  20/27 D (%74); tümünde 20/52 (%38). → v3'ten (51 kabul, 39/50 D) belirgin
  kötü. Parça listesi istemek modeli zorladı: her parçanın başlangıcı
  aynen bulunmalı, biri bile değişirse alanın tamamı reddediliyor.
- Claude'un önerisi: LLM bölmesini burada bırakıp önceden kararlaştırılan
  yedek plana geçmek (iki dilli alanlar analiz dışı); gerekçe yöntem notunda.
  Karar kullanıcıda.

### Karar: iki dilli alanlar analiz dışı (kullanıcı: "çıkaralım, gerekirse sonradan ekleriz")
- `oai_ayristir.py`: `ilk_oz` iki dilli parçaları seçmiyor; parçalar
  `ozler`de kalıyor. Raporda yeni satır: iki dilli alan yüzünden özeti
  analiz dışı kalan makale (TR / EN). Sahte kayıtlarla test edildi.
- `llm_bol.py` ve sonuç dosyaları kayıt için repoda kalıyor (makalede
  raporlanacak doğruluklar buradan).
- Kullanıcı: `oai_ayristir.py`'yi yeniden çalıştırmalı; rapordaki yeni
  sayılar yöntem notuna girecek.
- Sırada: bozuk karakter temizliği (`karakter_kontrol.xlsx` işaretlenince)
  + çok katmanlı HTML kaçışı; sonra deney / aday listeler / dergi paneli.

### Oturum özeti (2026-10-31 / 11-01)
**İki dilli alanların bölünmesi — sonuç tablosu (ayar seti, 52 alan):**

| Yöntem | Kontrolden geçen | Elle doğru (D) | Süre/alan |
|---|---|---|---|
| Kural (1. doğrulama, 50 örnek) | — | 16/50 (%32) | — |
| gemma4 v1 (metni kopyala) | 43/52 | işaretlenmedi | ~6 sn |
| llama3.1 v1 | 20/52 | işaretlenmedi | ~15 sn |
| gemma4 v2 (+ düzeltme yapma, silme) | 46/52 | işaretlenmedi | ~6 sn |
| gemma4 v3 (yalnızca sınırın ilk 8 kelimesi) | 51/52 | **39/50 (%78)** | ~1,4 sn |
| gemma4 v4 (tüm parçaların listesi) | 27/52 | 20/27 (%74) | ~8,5 sn |

- v3 hataları: ikinci özün başlığı yanlış tarafta 5, TR–EN–TR (ör. bmj:
  "Turkish Başlık: … Anahtar Kelimeler: …") 4, aslında tek dil 3.
- Eşik %98 (veriden önce, kullanıcı). Test setine geçilmedi → **iki dilli
  alanlar analiz dışı** (ön kayıtlı yedek plan).

**Yeni / değişen dosyalar:**
- `toplama/llm_bol.py` — ornekle / calistir / farklar / excel (`--onceki`)
  / yanlislar / hesapla; komut sürümleri v1–v4 kodda korunuyor.
- `toplama/karakter_kontrol.py` — bozuk karakter sayımı + 70 örneklik
  Excel (metne dokunmaz).
- `toplama/oai_ayristir.py` — `orijinal_metin` saklanıyor; iki dilli
  parçalar `ozet_tr`/`ozet_en` olarak seçilmiyor; raporda sayılıyor.

**Bozuk karakter sayımı (1.314.493 öz):** görünmez tire 4.359 öz (%0,33),
diğer `\` 3.702 (%0,28; muhtemelen LaTeX, dokunulmayacak), `harf¬harf`
1.819 (%0,14), `\'` 1.770 (%0,13), `¬` diğer 138, `\"` 83, `harf¬ harf` 35.
Analizin kelime ayırıcısı bunları kelimeyi bölen işaret sayıyor
("bu¬lunmaktadır" → "bu" + "lunmaktadır"). Ayrıca çok katmanlı HTML
kaçışı (`p&amp;lt; 0.01`) görüldü.

**Kullanıcıda bekleyenler:**
1. `oai_ayristir.py`'yi yeniden çalıştırmak; rapordaki "iki dilli alan
   yüzünden özeti analiz dışı kalan makale" sayısı yöntem notuna.
2. `karakter_kontrol.xlsx` (70 satır) D/Y.

**Sıradaki adımlar:**
1. Bozuk karakter + çok katmanlı HTML kaçışı kuralı (`temiz()`), Excel
   sonucuna göre; kod önce sohbette gösterilecek.
2. LLM yeniden yazım deneyi (ChatGPT/Claude/Gemini), aday listelerin ilk
   kontrolleri, dergi paneli.
3. Bekleyenler (eskiden): geleneksel kalıplar kontrol listesi, Lee (2026)
   tam metni, ESOGÜ e-postası, sözlüğe dayalı büyük harf bölmesi ve
   kısaltma sözlüğü (iki dilli bölme kalktığı için öncelik düştü; birleşik
   kelime onarımı için hâlâ gerekli olabilir).

### Bozuk karakter temizliğinin gerekçesi (kullanıcı sordu) ve ölçümün genişletilmesi
- Gerekçe: analizin kelime kuralı (`[^\W\d_]+`) görünmez tireyi ve `¬`'yı
  kelime sınırı sayıyor ("bu¬lunmaktadır" → "bu" + "lunmaktadır");
  `&amp;lt;` "amp", "lt" sahte kelimeleri üretiyor. Asıl risk: bozukluk
  yıllara göre değişirse kelime sıklığında sahte eğilim.
- Düzeltme (Claude): `\'` kelime sayımını DEĞİŞTİRMİYOR (normal kesme
  işareti de kelimeyi böler); yalnızca ek çözümlemesi / deney için, öncelik
  düşük. Öncelik: görünmez tire, harf¬harf; sonra HTML kalıntısı.
- `karakter_kontrol.py`'ye eklendi: yıllara göre tablo (10.000 özde kaç
  özde) ve `html_kalinti` türü (değişmeyene kadar çözülür). Excel varsa
  yalnızca sayım yapılır; yeni tür Excel'in sonuna eklenir (ilk 70 örnek
  aynı kalır, aynı tohum).

### Bozuk karakterler — yıllara göre sonuç (kullanıcı çalıştırdı)
- HTML kalıntısı da yaygın: 4.035 öz (%0,31). Görünmez tire ve HTML
  kalıntısı eski yıllarda yoğun, 2020 sonrası neredeyse sıfır (tablo:
  `yontem.md` §4.5). → Sahte eğilim riski gerçek; temizlik gerekli.
- Excel 80 satırla yeniden oluşturuldu (70 + 10 HTML kalıntısı); kullanıcı
  işaretleyecek, sonra kural yazılacak.

### Bozuk karakter doğrulaması: örnek sayısı (kullanıcı)
- Kullanıcı: "Tür başına 10 örnek az; her grup için %95 doğruluk olacak
  şekilde ayrılsın." → n = 73 (hepsi doğruysa %95 alt sınır %95,0).
  `karakter_kontrol.py`: varsayılan 73, `--hesapla` (tür başına D/Y,
  doğruluk, Wilson aralığı). Dil sütunu ve Türkçe karakterli ekran çıktısı
  önerileri kullanıcı tarafından istenmedi.
- Kullanıcıya Excel'in nasıl okunacağı `teachers\'` örneğiyle anlatıldı;
  İngilizce örneklerin neden olduğu soruldu (EN özler de analizde).

### Yarın (kaldığımız yer)
1. Kullanıcı: `git pull`; `karakter_kontrol.py --uzerine-yaz` (73'er örnek,
   ~546 satır) → işaretleme → `--hesapla` çıktısı.
2. Kullanıcı: `oai_ayristir.py` yeniden (iki dilli alanlar analiz dışı) →
   rapordaki "iki dilli alan yüzünden özeti analiz dışı kalan makale" sayısı.
3. Claude: doğrulama sonucuna göre `temiz()`'e karakter kuralı (görünmez
   tire, harf¬harf, HTML kalıntısı, `\'`); kod önce sohbette.
4. Sonra: LLM deneyi, aday listeler, dergi paneli.

## 2026-11-03 — Bozuk karakter doğrulaması: sadeleştirme

- Kullanıcı 73'er örnekli Excel'i (546 satır) oluşturdu, işaretlemeye
  başladı. Gözlemler: `bag\'in` sitede de aynı (hata DergiPark kaydında);
  Excel her özetten yalnızca ilk işareti gösteriyor (gerçek kural hepsini
  düzeltir — açıklandı); `Schr\"{o}dinger`, `Szeg\"{o}` LaTeX harf kodu,
  düzeltme bozuyor → Y.
- Claude: `\'` / `\"` kelime sayımını değiştirmiyor (tablo ile gösterildi).
- **Karar (kullanıcı):** "Sadece harfleri alacağız, bu düzeltmeyle zaman
  kaybetmeyelim, tamamen silin, plana sadık kalalım." → `karakter_kontrol.py`
  türleri 4'e indi (görünmez tire, harf¬harf, harf¬ harf, HTML kalıntısı);
  mevcut Excel'den çıkarılan türlerin satırları siliniyor, diğer işaretler
  korunuyor (sahte Excel ile test edildi). İşaretlenecek: 254 satır.

### Bozuk karakter doğrulaması sonucu ve kural
- `--hesapla`: 244 işaretli satırın hepsi D (görünmez tire 73/73, harf¬ harf
  35/35, HTML 71/71 + 2 boş, harf¬harf 65/65 + 8 boş). Boşların sebebi
  kullanıcıya soruldu.
- Kural `temiz()`'e yazıldı (HTML değişmeyene kadar, görünmez tire,
  harf¬harf); örneklerle test edildi (`¬p`, `\'`, LaTeX, `p&lt;0,05`
  korunuyor). Kullanıcı `oai_ayristir.py`'yi yeniden çalıştıracak; sonra
  `karakter_kontrol.py` ile kalan sayılar kontrol edilecek.
- **Kullanıcı bir sorun buldu (aynı gün):** `öğretme[görünmez tire]öğrenme
  süreci` → kural `öğretmeöğrenme` yapıyor. Burada görünmez tire gerçek bir
  kısa çizginin yerine geçmiş (birleşik terim "öğretme-öğrenme"); silmek iki
  kelimeyi birleştiriyor. Düzeltmeden önce kelime kuralı zaten doğru
  sayıyordu (`öğretme`, `öğrenme`). Kullanıcı satırı "d" işaretlemişti →
  Y olmalı. Görünmez tire satırları bu gözle yeniden gözden geçirilecek;
  sayıya göre karar (kabul / sözlüğe dayalı kural). Kullanıcı karar
  verilene kadar `oai_ayristir.py`'yi çalıştırmayacak.
- **Gözden geçirme sonrası `--hesapla` (kullanıcı):** harf¬harf 73/73
  (%95,0–100), harf¬ harf 35/35 (tamamı), görünmez tire **72/73** (%98,6;
  %95: 92,6–99,8; tek Y: `öğretme[görünmez tire]öğrenme` birleşik terim),
  HTML kalıntısı 71/71 (2 boş). Claude'un önerisi: görünmez tire kuralı
  olduğu gibi kalsın, sınır makalede raporlansın (karar kullanıcıda).
- Yan bulgular (plan dışı, yalnızca not): kodlama bozukluğu
  (`2008â"2009`, uzun tire yerine), OCR bozuk metin ("Kitap Oç :ana
  bölümden nle'ydana ııe! mi}tir"); eski bozuk metin kuralına takılmıyor
  (Latin harfli). Sıklık ileride ölçülebilir.
- Kullanıcı: "Ya daha çok varsa?" → (Claude) 1/73 için %95 üst sınır %7,4;
  en kötü durumda ~320 öz (%0,02). Kullanıcı ek kontrol istedi: **yalnızca
  Türkçe özlerden** görünmez tire seti. `karakter_kontrol.py`'ye `--dil`,
  `--tur`, `--haric` (ilk Excel'deki makaleler tekrar alınmaz) ve
  "birleşen parçalar" sütunu (`öğretme | öğrenme → öğretmeöğrenme`)
  eklendi; çıktı ayrı dosya `karakter_kontrol_tr.xlsx` (73 örnek).

### Türkçe görünmez tire seti (kullanıcı işaretledi, `karakter_kontrol_tr.xlsx`)
- 73 Türkçe örnek: 68 D, 3 Y, 2 boş. Claude'un satır satır incelemesi:
  - **İki ayrı kelimenin birleşmesi (öğretme-öğrenme türü): 0/73.**
  - **Görünmez tire + boşluk: 8/73 (~%11)** — `BELİRTİ[gt] LEN`, `tem[gt]
    poya`, `çağ[gt] daş`, `neden[gt] le`, `ara[gt] sında`, `uy[gt] gun`,
    `öldü[gt] rülmesi`, `kolaylaş[gt] tırmak`. Mevcut kural boşluğu
    bırakıyor, kelime bölük kalıyor (kullanıcı kısmen Y, kısmen D + not
    işaretledi). Öneri: `¬` kuralı gibi görünmez tire + arkasındaki boşluk
    birlikte silinsin (harf arasındaysa).
  - Diğer notlar önceden var olan boşluk kaybı (`analizininyapılması`,
    `konularınıhaber`, `önlemekamacıyla`, `katkılaryaptı`, `yarısından
    itibarenönemli`) ve OCR bozukluğu — görünmez tireden bağımsız.
- Kullanıcı önerisi: **Zemberek** ile karar (görünmez tirede birleşik hal
  bir kelimeyse birleştir, iki kelimeyse ayır) ve boşluk kaybını ayırmak
  için de kullanmak. Tartışıldı (aşağıdaki karar bekliyor).
- **Karar (kullanıcı: "dediklerini yapalım"):** görünmez tire + boşluk
  kuralı eklendi (`YUMUSAK_TIRE_HARF`), kullanıcının 8 örneği + çoklu
  görünmez tire + `¬` örnekleriyle test edildi. Zemberek görünmez tire için
  kullanılmayacak; boşluk kaybı onarımında doğrulamadan sonra
  değerlendirilecek (`yontem.md` §5).
- Sırada (kullanıcı): `git pull` → `oai_ayristir.py` → `karakter_kontrol.py`
  (kalan ~0 olmalı) → `analiz/birlesik_kelime.py sozluk/rapor --dil tr`.

## 2026-11-04 — Yeniden ayrıştırma ve birleşik kelime raporu

- `oai_ayristir.py` (kullanıcı): bozuk karakter temizliği — harf¬harf 3.662,
  görünmez tire 10.754, HTML >2 kat 11.810 metin (tüm dc alanları).
  `karakter_kontrol.py` dört tür için **0** → temizlik tam.
- İki dilli alan yüzünden özeti analiz dışı kalan makale: **TR 11.134,
  EN 11.634**.
- `birlesik_kelime.py sozluk/rapor --dil tr`: onarım kuralı aşırı bölüyor
  (en sık 40 onarımın ~26'sı yanlış, ör. `verilerde → veriler + de`).
  Sözlük oluşturulunca TÜM analiz betikleri bu onarımı otomatik uyguluyor
  → kullanıcıya sözlük dosyasını devre dışı bırakması söylendi (önceki
  analizlerde sözlük yoktu, etkilenmedi). Kullanıcının Zemberek fikri
  artık gerekli: tasarım onaya sunulacak.
- Kullanıcı tez reposu `Simya00/TR-LLM-Analiz`'i oturuma ekletti (salt
  okuma). Orada: `tdk_sozluk_maddeleri.txt` (TDK Güncel Türkçe Sözlük 12.
  baskı madde başları, 97.823 madde; MIT lisanslı, github.com/ogun/
  guncel-turkce-sozluk), `tr_50k.txt` (hermitdave FrequencyWords sıklık
  listesi), Zemberek geçerlilik fonksiyonu ve önbelleği. TDK'de madde başı
  olarak: `küçükbaş`, `sözde`, `alanya`, `veri`, `göre`, iki kelimelik
  `okul öncesi` (çekimli biçimler yok: `verilerde` yok).
- Kullanıcı kararı: nadir kelimeler ek Zemberek kontrolünden geçsin,
  Zemberek onay verirse bölünsün; TR-LLM-Analiz'deki sözlük ek kontrol
  olsun; **son kontrolü kullanıcı yapacak.** Tasarım onaya sunuldu.
- Kod (kullanıcı: "dediklerini deneyelim"): `kelime_siklik.py` artık
  yalnızca onaylı listeyle bölüyor; `birlesik_kelime.py` → `zemberek`,
  `hesapla`, `onayla`. TDK dosyası `analiz/kaynaklar/`'a kopyalandı (tez
  reposu değişmedi: `git status` boş). Sahte Zemberek ile test: verilerde,
  göreve, ölçeğine, bağlamındaki (Zemberek), alanya, küçükbaş, sözde (TDK)
  bölünmedi; buaraştırmanın, ileilgili, birşekilde (Zemberek), okulöncesi
  (TDK iki kelime) bölündü.
- Kullanıcı: Zemberek tez ortamında, oraya bir şey kurmak istemiyor →
  `zemberek` komutu Excel yazmıyor; örnekleri `birlesik_ornek_tr.json`'a
  yazıyor, Excel'i normal python ile `excel` komutu oluşturuyor. Önerilen:
  bu projenin kendi `analiz/zemberek_kur.sh` ile ayrı ortam (tezden bağımsız).

## 2026-11-05 — Zemberek kontrolü ilk çalıştırma (kullanıcı)
- Projeye ayrı Zemberek ortamı kuruldu (`analiz/zemberek_env`, tezden
  bağımsız). `birlesik_kelime.py zemberek --dil tr` (2015–2026 TR özler):
  **940.056 farklı aday** (sıklık kuralının bölmek istediği kelime).
  | gerekçe | farklı kelime | geçiş (özet) |
  |---|---|---|
  | Zemberek parçaları tanıyor → BÖL | 545.480 | 933.096 |
  | Zemberek tamamını tanıyor → bölme | 206.225 | 817.916 |
  | onay yok → bölme | 177.013 | 227.580 |
  | TDK madde başı → bölme | 9.795 | 67.479 |
  | TDK iki kelimelik madde → BÖL | 1.543 | 11.310 |
- Not (Claude): bölünecek grup çok büyük ve çoğu tek geçişli kelime;
  gerçek yapışmalar çoğunlukla tekildir (her kombinasyon farklı), ama
  Zemberek'in tanımadığı terim/yabancı kelimelerin de bu gruba düşme riski
  var. Doğruluk yalnızca kullanıcının Excel kontrolüyle bilinecek.

### Birleşik kelime Excel'i — ilk işaretleme (kullanıcı, kısmi)
- **bol grubu: 72 işaretli, 42 D / 30 Y (%58)** → mevcut kural kabul
  edilemez. Claude'un sınıflandırması (30 Y):
  - **A. Yapışma gerçek ama bölme noktası yanlış (19):** kural parçaları en
    sık kelimelerden seçip 3'e bölüyor: `modelinegöre → modeli+ne+göre`
    (doğrusu modeline+göre), `şirketineait`, `literatürdenfarklı`,
    `makaledetanrı`, `içindeortalaması`, `amacıgütmeden`,
    `mektebindenmezun`, `balıkçılığınüzerinde`, `bitkiailesine`,
    `inciçiftine`…
  - **B. Aslında tek kelime, Zemberek bilmiyor (11):** terim/yabancı/eski
    yazım/OCR: `hautbois → ha+ut+bois`, `eritemin`, `mikrokarsinom`,
    `positum`, `cerge`, `lanns`, `nushiye`, `payini` (payını), `barsakla`,
    `habishanelere`, `amfitiyatronuntarih` (amfitiyatro TDK'de yok,
    "amfiteatr" var).
- **bolme grubu:** 6 Y, ama açıklamalar (gelmişler, müzelik, değiştirmese…)
  kelimenin tek kelime olduğunu söylüyor → soru kafa karıştırıcı; büyük
  olasılıkla D kastedildi. Ayrıca "onay yok" grubunda gerçek yapışmalar
  kaçmış (`vergidenetimlerinin`, `şiirinindili`, `deklinisyen`) ve
  Zemberek'in tanıdığı sık bir yapışma var: `yeralan` (586 özet).
- Yan bulgu: `gö̈revleri` — birleştirici iki nokta (U+0308) kelimeyi bölüyor.
- v2 kuralları yazıldı (kullanıcı onayı). Bu ortama projenin Zemberek'i
  kuruldu (`analiz/zemberek_env`, gitignore'da). `karsilastir` komutu
  eklendi; kullanıcının 146 satırı gerçek Zemberek ve "her parça sık"
  varsayımıyla tekrar oynatıldı (sonuç `yontem.md` §5). Beyaz listeye Claude
  2 kök ekledi (takson, orbita; testte görülen `tak + sonunda`, `orbit +
  adaki` riskleri) — kullanıcı onayı bekliyor.
- **v2 `karsilastir` (kullanıcı, gerçek sözlük + Zemberek), işaretli 72
  "bol" satırı:** D verilen 42'nin 41'i aynı (kayıp: 3 parçalı
  `akreditasyon…`); yanlış yerden bölünmüş 19'un 17'si artık doğru yerden
  (`modeline + göre`, `şirketine + ait`…), 2'si bölünmüyor
  (`mevsimsellikten…`, `mektebinden…`: güvenli kaçırma); tek kelime 11'in
  10'u bölünmüyor, 1 hata `habishanelere → habis + hanelere` (hapishanenin
  eski yazımı) → beyaz listeye `habishane` eklendi. Claude'un sayımı:
  ~68/72 doğru karar, yanlış bölme 1/72. "bolme" grubunda da gerçek
  yapışmalar yakalanıyor (`vergi + denetimlerinin`, `şiirinin + dili`,
  `yapılarındaki + iznik`, `yer + alan`).

### Birleşik kelime v2 doğrulaması (kullanıcı, `birlesik_kontrol_tr.xlsx`, T/B)
- **bol (bölünen) grubu: 70/73 doğru = %95,9 (%95 Wilson 88,6–98,6).**
  Yanlış bölmeler: `cihanzâde → cihan + zâde` (soyadı), `bankya → bank + ya`
  (yer adı), `habitatda → habitat + da` (yazım hatalı tek kelime).
  (v1: %58.)
- **bolme grubu: 70/72 doğru = %97,2 (90,4–99,2)**, 1 boş. Kaçırılan 2
  yapışma (`muradıntebliği`, `çıkarsamalardabulunulmuştur`): parçalar <30
  özet; bölünmeden kalıyor (zararsız).
- **Yeni bulgu:** `Tü⟦rkçeye⟧` (13 özette "rkçeye" ayrı kelime): "ü" büyük
  olasılıkla ayrıştırılmış biçimde (u + birleştirici iki nokta, Unicode NFD);
  kelime kuralı birleştirici işareti harf saymadığı için kelimeyi bölüyor.
  Öneri: `temiz()`'de Unicode NFC normalleştirmesi (önce ölçüm).
- Kullanıcı: "bir tarama daha yapsak?" → evet, yalnızca bölünen grup, 73
  yeni kelime, kurallar dondurulmuş. `ek_tur` ve çoklu `hesapla` eklendi,
  sahte veriyle test edildi (önceki kelimeler hariç tutuldu, iki dosya
  doğru birleştirildi).
- **2. tur sonucu:** 72/73; iki tur birleşik bölünen 142/146 = %97,3
  (93,2–98,9). Kullanıcıya onay (`onayla`) ve beyaz liste eklemeleri
  soruldu.
- Kullanıcı: "tamam başlayalım". Beyaz listeye 1. turun 3 hatası eklendi
  (cihanzâde, bankya, habitat; "doğrulama SONRASI" notuyla). 2. turdaki
  hatalı kelime kullanıcıdan bekleniyor.
- `karakter_kontrol.py`'ye ölçüm türü `birlestirici_isaret` eklendi: harf +
  ayrı birleştirici işaret (U+0300–036F). Önerilen düzeltme NFC; test:
  `Türkçeye → Türkçeye` düzeliyor, `gö̈revleri` (zaten
  noktalı harfe fazladan işaret) NFC ile DÜZELMİYOR → ayrı alt tür, ölçüme
  göre karar.
- `onayla` çalıştırıldı: **546.522 onaylı bölme** — birleşik kelime onarımı
  analizde AÇIK. (Sayılar `yontem.md` §5.)
- Birleştirici işaret ölçümü (kullanıcı): 7.725 öz (%0,59), 151.538 işaret;
  yıllara göre artıyor (2010: 22,9 → 2018–2026: 64–86 / 10.000). Ayrıntı
  `yontem.md` §4.6. NFC önerildi; 73 örnek kullanıcıda.
- Kullanıcı: NFC gerekli mi? → (Claude) ana sonuçlara etkisi küçük
  (yıllar arası fark ~binde 1), maliyeti tek satır, standart uygulama.
  Kullanıcı: "ne kadar gerekliyse o kadar kontrol edelim, tam olsun." →
  NFC `temiz()`'e eklendi; `nfc_sonrasi_isaret` ölçümü eklendi (test:
  `Tu+¨rkçeye → Türkçeye`, `çalışma` düzeliyor; `gö+¨+¨revleri` NFC sonrası
  kalan işaret olarak yakalanıyor).
- NFC sonrası kalan işaret örnekleri (kullanıcı inceledi): çoğu meşru
  (X̄ ortalama, transliterasyon alt çizgileri `dj̲ihād`, `Os̠māniyye`) →
  dokunulmayacak. Gerçek bozukluk: fazladan noktalı i (`Ni̇ghti̇ngale`,
  muhtemel kaynak: İ'nin yanlış küçültülmesi → `i̇`). Türkçede de kelime
  bölebilir (`İSTANBUL → i̇stanbul`) → yalnızca TR'de sayılacak.
- Kullanıcı: "çoğu İngilizce, İngilizceyi hiç dahil etmeyebiliriz." →
  (Claude, danışman görüşü) EN özler pozitif kontrol (bilinen işaretçiler,
  ör. "delve") ve iki dilli karşılaştırma için tutulsun; ek temizlik
  yapılmasın, kalan sorunlar sınırlılık listesine. Kullanıcı: "haklısın".
  **Karar: EN kalıyor, ikincil rolde, ek temizlik yok.**

**Yarın (2026-11-06) yapılacaklar:**
1. `karakter_kontrol.py`'ye dar sayım türü: `i` + U+0307 (yalnızca `--dil tr`);
   önce kod sohbette gösterilecek. Az → sınırlılık; çok → tek dar kural
   (kullanıcı karar verir).
2. `nfc_sonrasi_isaret` sayım çıktısı kullanıcıdan alınacak.
3. Bekleyen onaylar: 2. turdaki hatalı bölünen kelime (beyaz liste);
   `takson`, `orbita` beyaz liste eklemeleri.
4. `yontem.md`'ye "Bilinen sınırlılıklar" listesi (OCR bozukluğu, mojibake,
   kalan birleştirici işaretler, EN birleşik onarımı kapalı, iki dilli
   alanlar dışarıda, 3 parçalı yapışmalar bölünmüyor).
5. **Veri dondurma:** `oai_ayristir.py` (NFC uygulanır) → `birlesik_kelime.py
   sozluk/zemberek/onayla --dil tr` → yeni sayılar kaydedilir.
6. Dondurmadan sonra ana analize geçiş (aday listeler, LLM yeniden yazım
   deneyi, dergi paneli).
- (Akşam, ek) Kullanıcı onayları: `takson`, `orbita` beyaz listede onaylandı;
  "Bilinen sınırlılıklar" `yontem.md` §10'a yazıldı. `hekimliğininde`
  ("diş hekimliğinin de birçok alanında") yeniden incelendi, bölme doğru
  sayıldı → birleşik kelime bölünen grup **143/146 = %97,9 (94,1–99,3)**.
- Noktalı i: tezdeki `turkce_kucuk_harf` çözümü Türkçe tarafta zaten
  kullanılıyor; İngilizce tarafta `.lower()` hatası bulundu ("İstanbul" →
  `i` + `stanbul`) ve düzeltildi (onaylı). Kaynaktan bozuk gelen `i̇` için
  `fazla_noktali_i` sayım türü eklendi (test: `Ni̇ghti̇ngale` → 2 eşleşme,
  `İstanbul`/`çalışma` → 0). Sayım yarın kullanıcıda.

## 2026-11-07

- `fazla_noktali_i` sayımı: kullanıcı `--hesapla` ile çalıştırdı (eski
  Excel'in doğruluk tablosu çıktı, sayım değil; Claude'un komut hatası).
  Doğru komut verildi (`--hesapla` olmadan, yeni `--cikti`); sonuç bekleniyor.
  Kullanıcının yerel depo yolu: `~/Desktop/dergipark-llm-izi/dergipark-llm-izi`.
- **Makale planı** (Claude'un tahmini, haftada 3 × 2 saat): 9 aşama, ~23–27
  oturum → ilk taslak Aralık sonu/Ocak başı, gönderim Ocak 2027 ikinci yarısı.
  Riskler: LLM deneyi süresi, beklenmedik bulgular, danışman dönüşü, kapsam
  genişlemesi (ESOGÜ verisi ikinci makaleye önerildi). Kullanıcıdan bekleyen:
  haftalık süre, hedef dergi.
- **Karar (kullanıcı): LLM yeniden yazım deneyi API ile.** OpenAI (5 $ kredi
  yeterli; Claude'un kaba hesabı model başına ~200–300 bin token), Gemini
  ücretsiz katman, Claude için kullanıcının tez için alacağı API anahtarı.
  Varsayılanlar (Claude'un önerisi, uygulandı): istek başına 1 özet, sıcaklık
  varsayılan, komut değişmez, 1 tekrar.
- `deney/api_yeniden_yaz.py` yazıldı: anahtar ortam değişkeninden, model adı
  `--model` ile (kodda yok), `--kuru` / `--sinir`, 429/5xx'te bekleyip tekrar,
  kesilmiş cevap kaydedilmez, ham cevaplar `api_ham_<alan>.jsonl`. Sahte
  cevaplarla test edildi (dolu örnek atlandı, kesilmiş cevap kaydedilmedi,
  Gemini düşünce parçası ayıklandı).

## 2026-11-10

- Noktalı i sayımı (kullanıcı, TR): `fazla_noktali_i` 50 öz / 162 kez;
  `nfc_sonrasi_isaret` 779 öz / 1.704 (2022 sonrası artmıyor). Ayrıntı
  `yontem.md` §10.1.
- Karar (kullanıcı): "i + U+0307 → i" kuralı TR ve EN için `temiz()`'e
  eklendi (NFC'den önce; test: `Ni̇ghti̇ngale → Nightingale`, `İSTANBUL`,
  `Türkçe`, `çalışma` değişmiyor, `i + nokta + ´ → í` tek karakter).
  Kullanıcı: "çok etkisi yok ama yine de 50 tanesine bakalım" → tüm vakalar
  Excel'de kontrol edilecek.
- Sıradaki: kontrol → veriyi dondurma → `deney_hazirla.py` → API deneyi.
- **Fazla noktalı i doğrulaması (kullanıcı, `karakter_kontrol_fazla_i.xlsx`,
  TR + EN, tüm vakalar: 64 öz):** 62 D, 0 Y, 2 boş → **62/62 = %100
  (%95 Wilson 94,2–100)**. Kullanıcı sorusu: Excel'de yalnızca ⟦ ⟧ içindeki
  vaka düzeltilmiş görünüyor → Claude: Excel her özetten tek vaka gösterir;
  `temiz()` `replace` ile hepsini düzeltir (test: `verimli̇`, `di̇hi̇droklorürün`
  → kalan fazla nokta 0).
- Fazla noktalı i: kullanıcı "boş yok, hepsi D" → 64/64 (Excel'deki 2 boş
  büyük olasılıkla kaydedilmeden hesaplandı).
- **VERİ DONDURULDU** (kullanıcının bilgisayarında): `oai_ayristir.py` →
  `sozluk` → (önce atlanan, sonra çalıştırılan) `zemberek` → `onayla`.
  **546.421 onaylı bölme.** Bütün sayılar `yontem.md` §5.1. Zemberek proje
  ortamıyla (`analiz/zemberek_env`) çalıştı; tez ortamına dokunulmadı.
- **1. aşama bitti.** Sıradaki: `deney_hazirla.py` → API anahtarları ve model
  adları → API deneyi.
- Kullanıcı: "Bana hiçbir şeyi açıklamıyorsun." → Büyük resim (6 aşama)
  ve aşırı kelime yöntemi örnekle anlatıldı. Bundan sonra her adımda: ne,
  neden, ne göreceğiz.
- Bütçe: Claude API'de 5 $ kredi var; ChatGPT için bu ay bütçe yok.
  Kullanıcı: ChatGPT en gereklisi (Claude: katılıyorum, kaynakla
  desteklenmeli). **Karar (kullanıcı): LLM deneyi gelecek aya ertelendi**;
  OpenAI API anahtarı o zaman alınacak, üç model aynı koşulda (API).
  Ücretsiz ChatGPT web yalnızca yedek (sessizce küçük modele geçebiliyor →
  sürüm raporlanamaz).
- Sıradaki: ana analiz (kelime sayımı → aşırı kullanım), LLM gerektirmiyor.

## 2026-11-11

- Kullanıcı sorusu: kelime sayımı ekran kartı kullanıyor mu? → Hayır
  (yalnızca CPU/RAM/disk).
- Kullanıcı isteği: sonuçları görselleştiren pandas kodu →
  `analiz/gorsellestir.py` (yalnızca okur, hesap değiştirmez):
  `egilim` (kelime başına küçük panel: gerçekleşen oran, Kobak vd.
  karşı-olgusalı, ChatGPT çizgisi; varsayılan 2015–2025, 2026 eksik yıl
  olduğu için dışarıda; paneller hedef yıldaki farka göre sıralı) ve `asiri`
  (hedef yılda en çok artan N kelime: beklenen q ile gerçekleşen p noktaları).
  Sahte veriyle test edildi (grafik çıktısı kontrol edildi). Gerçek veri
  kullanıcının `kelime_siklik.py` çalıştırmasını bekliyor.
- Kullanıcı: "histogram grafiği de olsun" → `gorsellestir.py dagilim`:
  hedef yılda ≥30 özette geçen tüm kelimelerin oran (p/q) dağılımı, log2
  x ekseni (×1 = değişim yok), log y ekseni (kuyruk görünsün); `--liste`
  ile aday listedeki kelimeler alt kenarda turuncu çizgilerle; ekrana liste
  medyanı ve tüm kelimelerin yüzde kaçının ondan büyük olduğu yazılır.
  Kutu sayısı 60 (Claude'un seçimi). Sahte veriyle test edildi.
- **İLK GERÇEK SONUÇ** (kullanıcı, `asiri_kullanim.py --dil tr --hedef 2024`,
  taban 2021–2022, ≥30 özet):
  - Farka göre: sunum fiilleri belirgin: göstermektedir ×1,64,
    amaçlamaktadır ×1,81, (ortaya) koymaktadır ×2,68, sunmaktadır ×2,25,
    vurgulamaktadır ×6,94 (%0,37 → %3,42), incelemektedir ×2,76; ayrıca
    kritik ×2,63, kapsamlı ×1,95, rol ×1,68, önemini ×2,09, teşvik ×2,40,
    katkıda ×1,88, etkilerini ×2,11.
  - Kata göre: vurgulamakta ×24,6, vurguluyor ×39,8, içgörüler ×19,3,
    şekillendirmedeki, perspektiflerini, kesişiminde, boşluklarını,
    oynayabileceğini, artırabileceğini… (İngilizce LLM kalıplarının
    çevirisi gibi). Konu kelimeleri: chatgpt, gpt, gemini, yapay, deprem*,
    hamas, gazze, filistinli, afetin. `r²` belirteç yan etkisi olabilir.
  - **Dikkat (Claude):** çok sık işlev kelimeleri de artmış (için ×1,05,
    çalışma, önemli, gibi, ortaya, ayrıca: +2–6 puan) → özetler
    uzamış olabilir; uzunluk artışı her kelimenin "geçme" olasılığını
    yükseltir. Yıllara göre özet uzunluğu kontrolü önerildi.
- Kullanıcı: "Kobak vd. ne yaptı, biz ne yapıyoruz?" → Kobak vd. kodu
  okundu, parametreler `literatur.md`'ye yazıldı; benzerlik/farklar ve
  özgün katkılar (Türkçe biçimbilim/ek analizi, ön kayıtlı liste, yeniden
  yazım deneyi, doğrulanmış temizlik, dergi paneli, iki dilli karşılaştırma)
  anlatıldı; Lee (2026) uyarısı tekrarlandı.
- **Karar (kullanıcı): uzunluk filtresi ve aşırı kelime kuralı Kobak vd.
  ile birebir aynı** ("İngilizce özetlerde tam uyum"). Kod: `kelime_siklik`
  (`analize_girer`, 250–4000 karakter; n=1'de tüm kelimeler tutulur),
  `asiri_kullanim` (yumuşatma, p ≥ 1e-4, Kobak kuralı, `asiri` sütunu),
  `ozet_uzunluk.py` (yeni), `gorsellestir asiri` yalnızca aşırı kelimeler.
  Sahte veriyle test edildi (atılan kısa/uzun sayıları doğru; sabit
  kelime aşırı sayılmadı, artan sayıldı; eşik değerleri ×2/×1,68/×1,41).
- Kullanıcı yeniden çalıştıracak: `ozet_uzunluk.py` → `kelime_siklik.py`
  → `asiri_kullanim.py` (önceki sonuç filtresizdi, geçersiz).
- Karar (kullanıcı): her sonuç hem Kobak kuralıyla hem ≥30 özet sağlamlık
  filtresiyle raporlanacak → `asiri_kullanim.py --saglamlik 30` (varsayılan).
- **Özet uzunluğu (kullanıcı, TR, filtre sonrası):** ortalama kelime
  2015: 130 → 2019: 154 → 2022: 166 → 2023: 170 → 2024: 173 → 2025: 178
  (2026 kısmi: 186). Yılda ~3,5–4,5 kelime, düzenli; 2023'te kırılma yok.
  Filtre yılda %0,9–3,8 özeti atıyor (çoğu kısa).
- **Kobak kuralıyla 2024 (TR):** 63.643 kelime hesaba girdi; **5.846 aşırı**
  (δ > 0,01: 103); **≥30 özet: 1.254**. Kata göre listenin çoğu ≤30 özetli
  nadir kelime (çalgılarının, icracılara, hukuksuz…: büyük olasılıkla tek
  dergi/sayı etkisi) → küçük veride Kobak kuralı çok fazla rastlantısal
  aşırı kelime üretiyor; asıl karşılaştırma yıllar arası.
- `yillara_gore_asiri.py` yazıldı (Kobak Şekil 2 karşılığı: her T için taban
  T−2; yıl başına aşırı / ≥30 / δ>0,01 sayısı; tüm aşırı kelimeler
  `asiri_kelimeler_<dil>.tsv` → elle içerik/üslup işaretleme girdisi).
  `asiri_kullanim.asiri_hesapla` fonksiyona ayrıldı. Sahte veriyle test.
- **ANA SONUÇ (ilk hali; kullanıcı, `yillara_gore_asiri.py --dil tr`, her T
  için taban T−2, Kobak kuralı):**

  | yıl | özet | aşırı | ≥30 özet | δ>0,01 |
  |---|---|---|---|---|
  | 2018 | 30.649 | 9.055 | 866 | 56 |
  | 2019 | 34.614 | 7.630 | 862 | 43 |
  | 2020 | 41.572 | 6.228 | 751 | 11 |
  | 2021 | 45.700 | 5.535 | 802 | 25 |
  | 2022 | 45.968 | 5.431 | 487 | 5 |
  | 2023 | 45.763 | 5.615 | 554 | 7 |
  | 2024 | 48.461 | 5.846 | 1.254 | 103 |
  | 2025 | 53.668 | 7.109 | 2.789 | 215 |

  Yorum (Claude): ham "aşırı" sayısı gürültü (küçük veri; özet sayısı
  azaldıkça artıyor) → anlamsız. ≥30 ve δ>0,01 sütunları net: 2022–2023
  en düşük (487/554; 5/7), 2024'te sıçrama (1.254; 103), 2025'te daha büyük
  (2.789; 215). 2023'te etki yok → yayın gecikmesi; Lee (2026) Korece ile
  aynı zamanlama. 2018–2019 δ>0,01 (56/43) beklenenden yüksek → dergi
  karışımı değişimi olabilir; dergi paneliyle kontrol edilecek. 42.876
  farklı aşırı kelime (gürültü dahil) → işaretleme için daraltma gerekli.
- Kullanıcıya sade anlatım (okul örneği): 2022–2023'te çok artan (δ>0,01)
  kelime 5–7, 2024'te 103, 2025'te 215; 2023'te yayın gecikmesi.
  Kullanıcı: "heyecanlandım, bir şey bulduk galiba." → Claude: hakemin üç
  sorusu kaldı (önceki yıllar ✔ bugün cevaplandı; dergi karışımı; içerik mi
  üslup mu).

**Yarın (2026-11-12) yapılacaklar:**
1. **Elle işaretleme Excel'i:** herhangi bir yılda δ > 0,01 olan kelimeler
   (~400), her biri için arttığı yıllar, p/q değerleri ve örnek cümle;
   kullanıcı Ü / İ / B işaretler. (Claude önce kodu gösterip açıklar.)
2. **Dergi paneli kontrolü:** `dergi_paneli.py` (2021–2025 her yıl ≥5
   makale) → `kelime_siklik.py --dergiler` → `yillara_gore_asiri.py`
   aynı tablo; özellikle 2018–2019'daki yüksek δ>0,01 (56/43) dergi
   karışımından mı?
3. **Ön kayıtlı liste sonucu:** `liste_kontrol.py` / `gorsellestir.py
   egilim --liste aday_liste_tr.txt` + `dagilim` histogramı; 54 adayın
   kaçı aşırı çıktı.
4. **İlk grafikler:** eğilim panelleri (vurgulamaktadır, kritik, kapsamlı,
   içgörüler…), yıllara göre aşırı kelime sayısı grafiği (yeni; Kobak
   Şekil 2 gibi — önce anlatılacak).
5. Sonra: alt sınır (`alt_sinir.py`, üslup kelimeleriyle), İngilizce
   özetlerde aynı zincir (pozitif kontrol), ek analizi (Zemberek).
6. Bekleyen: LLM deneyi gelecek ay (OpenAI API), Lee (2026) tam metni,
   Türkçe için önceki çalışma taraması.

## 2026-11-12

- Kullanıcı: "başlayalım" (elle işaretleme). `analiz/isaretleme.py`:
  - `excel`: 2018–2025'ten birinde Kobak kuralıyla aşırı VE δ > 0,01 olan
    kelimeler (Claude'un önerisi; dünkü tabloya göre birleşimi ~400 bekleniyor).
    Her kelimeye, aşırı çıktığı yılların özetlerinden rastgele 2 örnek cümle
    (rezervuar örnekleme, tohum 20261112). **Kör işaretleme** (Claude'un
    önerisi): "isaretleme" sayfasında yalnızca kelime + örnekler, rastgele
    sırada; yıllar/δ ayrı "bilgi" sayfasında. Etiket Ü / İ / B (açılır liste).
  - `hesapla`: her yıl δ > 0,01 kelimelerin Ü/İ/B sayısı ve üslup yüzdesi
    (Ü / (Ü + İ), B hariç); Ü kelimeleri `uslup_kelimeleri_<dil>.txt`
    (alt sınır için).
  - Sahte veriyle test edildi.
  - Fark edilen eski zayıflık: tamamı büyük harf ve Türkçeye özgü harf
    (ÇĞİÖŞÜ) içermeyen kelime İngilizce kısaltma sayılıp `.lower()` ile
    küçültülüyor → "VURGULAMAKTADIR" → `vurgulamaktadir` (ı yerine i).
    Özetlerde büyük harfli Türkçe kelime nadir; sınırlılık adayı, ölçülebilir.
- Kullanıcı: "etkilerini ve etkiler iki ayrı kelime sayılmış." → Claude:
  biçim düzeyinde sayım bilerek (Kobak vd. de böyle; biçim ayrıca bilgi
  taşıyor), ama bir kökün artışı biçimlere dağılıp eşik altında kalabilir.
  Öneri: kök düzeyinde (Zemberek) ek analiz, Kobak'ın lemmatize sürümü gibi.
  **Kullanıcı kararsız: "şimdilik bu şekilde bakalım."** → AÇIK SORU; elle
  işaretlemeden sonra yeniden değerlendirilecek. İşaretlemede her biçim ayrı
  etiketlenir; `hesapla` sonrası aynı kökün farklı etiket alan biçimleri
  tutarlılık için listelenebilir.
- Kullanıcı örneği: "ilişki" ve "ilişkili" ayrı sayılmış. → Claude: bu yapım
  eki (isim → sıfat, ayrı sözlük maddesi); "etkiler/etkilerini" ise çekim
  eki. Kök analizi yapılırsa iki düzey seçeneği: sözlük maddesi (lemma:
  etki ← etkiler, etkilerini; ilişki ≠ ilişkili) ya da kök (hepsi "ilişki").
  İşaretlemede ayrı ayrı etiketlenir. (Açık soruya örnek olarak eklendi.)
- **Karar (kullanıcı): Türkçe ana analiz kelime (sözcük) düzeyinde,
  Zemberek ile; biçimler (etkiler, etkilerini…) "kullanılan varyasyonlar"
  olarak tutulur.** Gerekçe (kullanıcı): İngilizce sondan eklemeli değil
  (will be, did ayrı kelime); Türkçede ekler kelimeye bitişik, biçim düzeyi
  sayım İngilizceyle eşdeğer değil.
- Zemberek denemesi (Claude, bu ortamda):
  - İLK ÇÖZÜMLEME (tezdeki yöntem) bağlamsız ve sık kelimelerde yanlış:
    `sonuçlar → sonuçlamak` (fiil, geniş zaman), `etkiler → etkilemek`,
    `değerlendirme → olumsuz emir`.
  - `item.lemma` KÖK veriyor: `kapsamlı → kapsam`, `önemli → önem`,
    `etkili → etki`, `gerçekleştirilmiştir → gerçek` → üslup bilgisi kaybolur.
  - Bağlamlı çözümleme (`analyze_and_disambiguate`) çoğunu düzeltiyor
    (`sonuçlar → sonuç+A3pl`, `etkilerini → etki`) ama hepsini değil
    (`değerlendirme süreçlerinin` hâlâ olumsuz emir); hız ~11 ms/kelime →
    TR derlemi (~110M kelime) tek çekirdekte ~14 gün.
  - Açık kararlar: düzey (kök mü, gövde = kök + yapım ekleri mi), yöntem
    (ilk çözümleme mi, bağlamlı mı; paralel çalıştırma), doğrulama örneklemi.
- Kararlar (kullanıcı): (a) gövde: yapım ekleri korunur, edilgen ve
  fiilimsiler atılır; (b) cümle içinde çözümleme; (c) bilgisayarı 20 iş
  parçacığı. Ekler de aynı geçişte sayılsın ("-mektedir çok kullanılıyor").
  Kullanıcı: ekran kartı hızlandırır mı? → Hayır (Zemberek saf Python, CPU).
- `analiz/govde_siklik.py` yazıldı (sayim / birlestir / ornek / excel /
  hesapla). Sahte 96 özetle test: gövdeler doğru (sonuçlar → sonuç,
  değerlendirme → değerlendir, değişikliğinin → değişiklik, edilen → et),
  zincirler doğru (Prog2+A3sg+Cop). Hız ~107 kelime/sn/işçi → gerçek veri
  (~112M kelime) 10 işçiyle ~1–1,5 gün (tahmin; kullanıcıda ölçülecek).
- **Gövde doğrulaması (kullanıcı): 73/73 = %100 (Wilson 95,0–100).**
  Kullanıcı dilbilgisi terimlerinde zorlandı ("bu denli dilbilgisi bilgim
  yok") → soru "sözlükte bu hali mi arardım?" diye sadeleştirildi; çözümleme
  sütununa bakmak gerekmiyor. Sıradaki: süre denemesi (1.000 özet).
