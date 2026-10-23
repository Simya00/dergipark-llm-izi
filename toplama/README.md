# DergiPark Veri Toplama

DergiPark'ın açık OAI-PMH arayüzünden (`https://dergipark.org.tr/api/public/oai`)
makale üstverisini (başlık, Türkçe öz, İngilizce abstract, tarih, dergi) toplar.
Sadece Python 3 standart kütüphanesi gerekir, kurulum yok.

Plan ve bağlam: `../notlar/veri_plani.md`

## Adımlar

```bash
cd toplama

# 1) Arayüz çalışıyor mu, veri neye benziyor? (~5 sn)
python3 oai_topla.py deneme
#    İlk sayfanın (100 kayıt) TR/EN öz sayımı:
python3 oai_ayristir.py --dosya deneme_ornek.xml --cikti deneme.jsonl
#    Belirli bir derginin ilk sayfası için:  python3 oai_topla.py deneme --set <setSpec>

# 2) Dergi (set) listesini indir -> setler.tsv
python3 oai_topla.py setler
#    ESOGÜ dergilerini bul:  grep -i osmangazi setler.tsv

# 3) Pilot: ESOGÜ dergilerini topla (set adları setler.tsv'den)
python3 oai_topla.py topla --set <set1> --set <set2>
#    veya set adlarını esogu_setler.txt'ye satır satır yazıp:
python3 oai_topla.py topla --set-dosyasi esogu_setler.txt

# 4) Ayrıştır -> makaleler.jsonl + yıllara göre özet tablo
python3 oai_ayristir.py

# 5) Pilot iyi görünürse: tüm DergiPark (günler sürebilir)
python3 oai_topla.py topla
```

- **Kesilirse** aynı komutu tekrar çalıştır; kaldığı yerden devam eder
  (`ham/<set>/durum.json`).
- **Token süresi dolmuş** hatası alınırsa ilgili `ham/<set>/` klasörünü silip
  o set'i baştan topla.
- İstekler arası 1 sn beklenir (`--bekleme`); sunucuyu yormamak için düşürme.
- `ham/` ve `makaleler.jsonl` büyük olacağı için git'e eklenmez.

## İlk denemede öğrenilenler (2026-10-24)

- Arayüz çalışıyor; sayfa başına 100 kayıt, toplam sayı (`completeListSize`) verilmiyor.
- `earliestDatestamp` 2026-10-24: tüm kayıtların datestamp'i yenilenmiş,
  yani `--from/--until` işe yaramaz.
- Set'ler sayısal (`54`) ve bazı kayıtlarda set yok → dergi, URL'deki kısa
  addan (`pub/mulkiye`) `dergi_kodu` alanına çıkarılıyor.
- Dil etiketleri `tr-TR` / `en-US` biçiminde → `tr` / `en`'e indirgeniyor.
- Metinler HTML kaçışlı (`&#039;`) → ayrıştırmada çözülüyor.
- `dc:date` yayın tarihi gibi görünüyor; gönderilme tarihi OAI'de yok.
- İlk 3 (eski, 2012–2014) kayıtta İngilizce abstract yok, 2'sinde öz hiç yok.
  Yeni makalelerde EN abstract oranı kontrol edilecek.

## ESOGÜ pilotunda öğrenilenler

- 4 dergi (`ogummf`, `ogusbd`, `esoguifd`, `esogutd`): 1.871 makale.
  Yeni makalelerin neredeyse hepsinde TR öz + EN abstract var (iki dilli
  karşılaştırma mümkün).
- **Arşiv sorunu:** Dergiler DergiPark'a geçerken eski sayıları toplu
  yüklemiş; bunların `dc:date`'i yükleme tarihi. Örnek: `ogusbd` Cilt 10
  gerçekte 2009, `dc:date` 2014; `ogummf` Cilt 10 gerçekte 1997, `dc:date` 2017.
  Cilt numarasından yıl tahmini güvenilir değil (`ogummf` düzenli cilt
  çıkarmamış). Bu yüzden ayrıştırıcı arşiv makalelerini `arsiv: true`
  işaretler ve `yil_guvenilir: null` yapar; **analizde `yil_guvenilir`
  kullanılır.**

## Bilinen belirsizlikler

- `--from/--until` kaydın **değiştirilme** tarihine göre süzer, yayın yılına
  göre değil; bu yüzden yıl süzmesi ayrıştırmada `dc:date` üzerinden yapılıyor.
- `yil` = `dc:date` içindeki en erken yıl. Bunun yayın mı gönderilme tarihi mi
  olduğu pilot veride kontrol edilecek. Gönderilme tarihi büyük ihtimalle
  OAI'de yok; gerekirse makale sayfalarından ayrıca çekilecek.
- Özlerde `xml:lang` etiketi yoksa dil sezgisel olarak tahmin ediliyor
  (`dil_kaynagi: "tahmin"`).
- `oai_dc` yetersiz kalırsa `--format oai_mods` denenebilir (daha zengin olabilir).
