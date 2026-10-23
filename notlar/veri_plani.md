# DergiPark LLM İzi Çalışması — Veri Toplama Planı

Kaynak çalışma: Kobak, González-Márquez, Horvát, Lause — "Delving into
LLM-assisted writing in biomedical publications through excess vocabulary"
(Science Advances 2025; ön baskı arXiv:2406.07016). PubMed'deki 15M+ özette,
ChatGPT sonrası "delve, underscores, showcasing" gibi üslup kelimelerinin
beklenenden fazla arttığı gösterilmiş; 2024 özetlerinin **en az %13,5**'inin
LLM ile işlendiği sonucuna varılmış. Alt sınır olmasının nedenlerinden biri:
bazı yazarlar bu kelimeleri fark edip siliyor.

Hocanın cevabı (özet): Aynı yöntemi uygulayabiliriz. Osmangazi'nin
yayınlarına da bakalım (orada tanıdık var). Eski dergilerden makaleleri
toplu paylaşmalarını isteyebiliriz.

---

## 1. Veri kaynakları ve rolleri

| Kaynak | Rol | Nasıl |
|---|---|---|
| Tüm DergiPark | Ana veri seti (aşırı kelime keşfi + alt sınır) | OAI-PMH ile toplu üstveri (açık erişim, izin gerekmez) |
| ESOGÜ dergileri | Pilot + gönderilme tarihi + (mümkünse) ilk sürüm/son sürüm | DergiPark'tan + tanıdık üzerinden editörlük |
| DergiPark dışı / eski dergiler | Taban dönemini (2015–2022) uzatmak | E-posta ile toplu paylaşım talebi |

Neden ESOGÜ tek başına ana veri olamaz: yılda birkaç yüz makale, kelime
düzeyinde "beklenenden fazla artış" keşfi için yetersiz. Ama pilot ve
dergi içi ayrıntılı veri (tarihler, sürümler) için çok değerli.

## 2. ESOGÜ dergileri (ilk tarama — kesin liste DergiPark kurum sayfasından çıkarılacak)

| Dergi | Yer | Not |
|---|---|---|
| Mühendislik ve Mimarlık Fakültesi Dergisi | [dergipark/ogummf](https://dergipark.org.tr/tr/pub/ogummf) | TR Dizin, yılda 3 sayı |
| Sosyal Bilimler Dergisi | [dergipark/ogusbd](https://dergipark.org.tr/tr/pub/ogusbd) | Şu an makale gönderimine kapalı görünüyor |
| İlahiyat Fakültesi Dergisi | [dergipark/esoguifd](https://dergipark.org.tr/tr/pub/esoguifd) | TR Dizin, DOAJ; yılda 2 sayı |
| Tarih Dergisi (ESOGÜTD) | DergiPark (`esogutd`) | Yılda 2 sayı |
| Osmangazi Tıp Dergisi | e-ISSN 2587-1579 | DergiPark adresi doğrulanacak |
| İİBF Dergisi | ISSN 1306-6730 | DergiPark adresi doğrulanacak |
| Hukuk Fakültesi Dergisi (Periodicum Iuris) | DergiPark | |
| Osmangazi Journal of Educational Research | [ojer.ogu.edu.tr](https://ojer.ogu.edu.tr) | **DergiPark dışında** → doğrudan talep gerekir |
| Nicel Bilimler Dergisi | ? | Üniversitenin hakemli dergi listesinde geçiyor, adresi doğrulanacak |

Üniversitenin listeleri: [Hakemli Dergiler](https://www.ogu.edu.tr/Icerik/Index/262/hakemli-dergiler),
[ESOGÜ Yayınları — Dergiler](https://yayin.ogu.edu.tr/Sayfa/Index/10/dergiler).

## 3. Toplanacak alanlar (makale başına)

- Dergi, cilt/sayı, makale kimliği / DOI
- **Gönderilme tarihi**, kabul tarihi, yayın tarihi (zaman ekseni gönderilme
  tarihine göre kurulacak; Türk dergilerinde hakem süreci uzun)
- Makale dili, Türkçe öz, İngilizce abstract (ayrı alanlar)
- Anahtar kelimeler, alan/kategori
- (Yalnızca ESOGÜ, izinle) hakeme ilk gönderilen sürümün özeti

Yıl aralığı: 2015–2026 (taban dönemi en az 2015–2022).

## 4. Açık kararlar

- [ ] Veri nerede toplanacak: bulut oturumunda (`dergipark.org.tr` erişimi
      açılmalı) mı, yerel makinede mi?
- [ ] Önce ESOGÜ pilotu, sonra tüm DergiPark — onay
- [ ] İlk sürüm / reddedilen makale istenecek mi? İstenecekse gizli belge →
      etik kurul izni + anonimleştirme. Hocayla netleştirilecek.
- [ ] Hangi "eski dergiler"e yazılacak (DergiPark dışı, arşivi dijital olmayan)

---

## 5. E-posta taslakları

### 5a. ESOGÜ'deki tanıdık / dergi editörlüğü

> Konu: Akademik yazımda yapay zekâ kullanımı üzerine araştırma — veri desteği talebi
>
> Sayın [Ad Soyad],
>
> [Üniversite/bölüm] bünyesinde, [danışman] danışmanlığında Türkçe akademik
> yazımda büyük dil modeli (ChatGPT vb.) kullanımının izlerini inceleyen bir
> çalışma yürütüyoruz. Yöntemimiz, Science Advances'ta (2025) yayımlanan ve
> PubMed özetlerinde ChatGPT sonrası bazı kelimelerin beklenenden fazla
> arttığını gösteren çalışmanın Türkçeye uyarlanmasıdır. Tekil makaleler
> veya yazarlar hakkında hüküm vermiyoruz; yalnızca yıllara göre toplam
> kelime sıklıklarını inceliyoruz.
>
> Üniversitenizin dergilerindeki yayımlanmış makalelerin özetlerini zaten
> açık erişimden alabiliyoruz. Bunun ötesinde, mümkünse şu bilgiler
> çalışmamıza çok katkı sağlar:
>
> 1. Makalelerin gönderilme ve kabul tarihleri (toplu liste olarak),
> 2. Derginizin yapay zekâ kullanımına ilişkin politikasının başlangıç tarihi,
> 3. [İzin ve etik kurul onayı alınması koşuluyla] makalelerin hakeme ilk
>    gönderilen sürümlerinin özetleri — anonimleştirilmiş olarak.
>
> Veriler yalnızca bu araştırma için kullanılacak, dergi ve yazar adları
> yayında anonim tutulabilir. Uygun görürseniz kısa bir görüşme yapmaktan
> memnuniyet duyarız.
>
> Saygılarımla,
> [Ad Soyad, unvan, kurum, iletişim]

### 5b. Eski / DergiPark dışı dergiler

> Konu: Araştırma amaçlı toplu makale özeti paylaşımı talebi
>
> Sayın Editör,
>
> [Üniversite/bölüm] bünyesinde Türkçe akademik yazımın yıllar içindeki
> değişimini ve son dönemde yapay zekâ araçlarının bu değişime etkisini
> inceleyen bir çalışma yürütüyoruz. Bu analiz için yapay zekâ öncesi
> dönemi (2015–2022) temsil eden geniş bir özet derlemine ihtiyaç duyuyoruz.
>
> Derginizde [yıl aralığı] arasında yayımlanan makalelerin özetlerini
> (Türkçe ve İngilizce), yayın/gönderilme tarihleriyle birlikte toplu olarak
> (ör. Excel/CSV veya PDF arşivi) paylaşmanız mümkün müdür? Yalnızca toplam
> kelime sıklıkları incelenecek; tekil makale veya yazar hakkında
> değerlendirme yapılmayacak ve derginin adı istenirse yayında anonim
> tutulacaktır.
>
> Çalışma sonuçlarını sizinle paylaşmaktan memnuniyet duyarız.
>
> Saygılarımla,
> [Ad Soyad, unvan, kurum, iletişim]
