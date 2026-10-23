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
#    -> çıktıyı ve oluşan deneme_ornek.xml dosyasını paylaş

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

## Bilinen belirsizlikler (pilotta netleşecek)

- `--from/--until` kaydın **değiştirilme** tarihine göre süzer, yayın yılına
  göre değil; bu yüzden yıl süzmesi ayrıştırmada `dc:date` üzerinden yapılıyor.
- `yil` = `dc:date` içindeki en erken yıl. Bunun yayın mı gönderilme tarihi mi
  olduğu pilot veride kontrol edilecek. Gönderilme tarihi büyük ihtimalle
  OAI'de yok; gerekirse makale sayfalarından ayrıca çekilecek.
- Özlerde `xml:lang` etiketi yoksa dil sezgisel olarak tahmin ediliyor
  (`dil_kaynagi: "tahmin"`).
- `oai_dc` yetersiz kalırsa `--format oai_mods` denenebilir (daha zengin olabilir).
