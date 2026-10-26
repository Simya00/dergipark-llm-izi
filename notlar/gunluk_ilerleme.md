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
