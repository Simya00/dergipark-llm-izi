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

### Bir sonraki adım (yarın)
1. `analiz/`: `birlesik_kelime.py sozluk --dil tr` (+ `en`), sonra
   `rapor --dil tr` → yıllara göre birleşik kelime oranı ve yanlış bölme
   kontrolü (kullanıcı listeye bakacak).
2. `deney/`: `deney_hazirla.py` → 200 özet; `deney_yapistir.py <model>
   --paket 10` ile ChatGPT, Claude, Gemini (hafıza kapalı, her pakette yeni
   sohbet, model sürümleri not edilecek). Bitince `deney_ornekleri.json` push.
3. İlk sonuçlar: `dergi_paneli.py`, `liste_kontrol.py` (TR, TR-panel, EN,
   TR-LLM listesi); "hâline/haline" eğilimine özellikle bakılacak.
4. Kullanıcıdan: geleneksel kalıplar kontrol listesi
   (`aday_liste_tr_kontrol.txt`); Lee (2026) ve Koo vd. (2026) PDF'leri
   (`notlar/kaynaklar/`).
5. Bekleyen: ESOGÜ/eski dergilere e-posta (kullanıcı henüz göndermedi;
   öncelik ESOGÜ: gönderilme/kabul tarihleri).
6. Ben: deney cevapları gelince orijinal–yeniden yazım karşılaştırma analizi
   (ortak/modele özgü kelime, kalıp, ek, imla).
