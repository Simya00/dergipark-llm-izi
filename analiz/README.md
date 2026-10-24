# Analiz

Kobak vd. (2025) aşırı kelime yönteminin DergiPark özetlerine uygulanması.
Girdi: `../toplama/makaleler.jsonl` (yalnızca `yil_guvenilir` dolu makaleler).

İki yol birlikte kullanılır:
- **Veriden keşif** (`kelime_siklik.py` + `asiri_kullanim.py`): beklenenden
  çok artan tek kelimeleri (`--n 1`) ve kelime gruplarını (`--n 2/3/4`,
  "önemli bir rol oynamaktadır" gibi kalıplar) kod kendisi bulur.
- **Hazır liste** (`liste_kontrol.py`): veriye bakmadan önce yazdığımız aday
  ifadeler (`aday_liste_tr.txt`, `aday_liste_en.txt`) doğrudan test edilir.
  Listeyi veriden önce yazmak "işine gelen kelimeyi seçmek" eleştirisine
  karşı korur; listeye sonradan ekleme yapılırsa tarihiyle not düşülmeli.

- **Ek düzeyi** (`ek_siklik.py`, Zemberek): her ekin ve ek zincirinin
  ("Prog2+A3sg+Cop" = -mAktAdIr) yıllara göre kullanımı. Modelden bağımsız:
  gerçek özetlerde neyin değiştiğini ölçer. (LLM'lerin ek profilini deneyle
  çıkarmak ayrı iş; birden çok model gerektirdiği için ertelendi.)

Kök (Zemberek) düzeyi sonraki adım.

## Adımlar

```bash
cd analiz

# 0) Birleşik kelime onarımı (PDF'ten kopyalamada kaybolan boşluklar:
#    "rakımlaragöre", "arızadankaynaklanan"). Sözlük bir kez oluşturulur;
#    dosya varsa TÜM analiz betikleri birleşik kelimeleri otomatik böler.
python3 birlesik_kelime.py sozluk --dil tr
python3 birlesik_kelime.py sozluk --dil en
python3 birlesik_kelime.py rapor --dil tr      # yıllara göre birleşik kelime oranı

# 1) Her kelimenin her yıl kaç özette geçtiği (her yıl için dosya bir kez okunur)
python3 kelime_siklik.py --dil tr
python3 kelime_siklik.py --dil en

#    Kelime grupları (cümle sınırını aşmaz):
python3 kelime_siklik.py --dil tr --n 2
python3 kelime_siklik.py --dil tr --n 3

# 2) Beklenenden fazla artan kelimeler / gruplar (veriden keşif)
python3 asiri_kullanim.py --dil tr --hedef 2024
python3 asiri_kullanim.py --dil tr --n 3 --hedef 2024
python3 asiri_kullanim.py --dil en --hedef 2024

# 2b) Hazır listeyi kontrol et
python3 liste_kontrol.py --dil tr --liste aday_liste_tr.txt --hedef 2024
python3 liste_kontrol.py --dil en --liste aday_liste_en.txt --hedef 2024

# 2c) Ek düzeyi (bir kez: bash zemberek_kur.sh; ilk çalıştırma ~1–2 saat,
#     kelime çözümlemeleri ek_onbellek.json.gz'ye kaydedilir)
zemberek_env/bin/python3 ek_siklik.py --hedef 2024
python3 asiri_kullanim.py --dil tr --siklik siklik_tr_ekzinciri.tsv.gz --hedef 2024 --en-az-belge 50

# 4) Sabit dergi paneliyle tekrar (geç katılan dergilerin etkisini ayıklar):
python3 dergi_paneli.py --dil tr                  # -> dergi_paneli_tr.txt
python3 kelime_siklik.py --dil tr --dergiler dergi_paneli_tr.txt --cikti siklik_tr_panel.tsv.gz
python3 asiri_kullanim.py --dil tr --siklik siklik_tr_panel.tsv.gz --hedef 2024
python3 liste_kontrol.py --dil tr --liste aday_liste_tr.txt --dergiler dergi_paneli_tr.txt

# 3) Aday listeden içerik kelimelerini (covid, deprem...) ayıklayıp üslup
#    kelimelerini/gruplarını isaretciler_tr.txt'ye yaz, sonra alt sınırı hesapla:
python3 alt_sinir.py --dil tr --isaretciler isaretciler_tr.txt
```

## Yöntem

- **Birleşik kelimeler:** Birçok özette satır sonu boşlukları kaybolmuş. Bir
  kelime, her parçası ≥30 özette geçen 2 (gerekirse 3) kelimeye bölünebiliyor
  ve kendisi ya <3 özette geçiyor ya da en seyrek parçasından ≥20 kat
  seyrekse bölünür. Oran yıllar arasında farklıysa onarımsız analiz sahte
  artış/azalış üretebileceği için onarım varsayılan olarak açık. Sahte
  testte 10 gerçek örneğin (DergiPark'tan) hepsi doğru bölündü; "neden",
  "bilgisayar", "kitaplarımızdan", "değerlendirilmektedir" bölünmedi.

- **Dergi paneli:** Bazı dergiler DergiPark'a geç geçmiş (`gazimmfd` ilk
  güvenilir yıl 2023, `pajes` 2022). Bunlar 2021–2022 tabanında yok, 2024'te
  var → dergi karışımı değiştiği için kelimeler LLM olmadan da "artmış"
  görünebilir. `dergi_paneli.py` 2021–2025'in her yılında ≥5 makalesi olan
  dergileri seçer; tüm analizler `--dergiler` ile panelde tekrarlanır. Sahte
  veride geç katılan bir derginin "beton" kelimesi tüm veride 133 kat artmış
  görünürken panelde artış sıfır çıktı.

- `p_y`: kelimenin y yılında geçtiği özet oranı.
- Karşı-olgusal: `q_T = p_2022 + (T − 2022) · max(p_2022 − p_2021, 0)`
  (2021–2022 doğrusal eğilimi; azalan eğilim sıfır alınır).
- Fark `δ = p_T − q_T`, kat `r = p_T / q_T`.
- Alt sınır: işaretçilerden en az birini içeren özet oranı için
  `L ≥ (p − q) / (1 − q)`.

## Doğrulama (sahte veri)

Bilinen LLM oranları (2023: %5, 2024: %15, 2025: %20, 2026: %22) ve her LLM
özetinde her işaretçinin %30 olasılıkla geçtiği sahte veride:
- 6 işaretçinin 5'i hem farka hem kata göre ilk sıralarda bulundu; doğal
  kullanımı zaten artan 6.'sı daha aşağıda kaldı.
- Alt sınır: %4,6 / %13,7 / %17,0 / %20,2 → beklendiği gibi gerçek oranın
  altında.

Kelime grupları için (LLM izi "önemli bir rol oynamaktadır", "ışık
tutmaktadır", "kapsamlı bir şekilde" kalıplarında gizlendi):
- 3'lü gruplarda bu kalıplar 2024'te beklenenin 16–23 katı çıktı; içlerindeki
  yaygın kelimeler ("rol", "önemli bir") ise hiç artmamış göründü (kat 1,0) →
  sadece kelimeye bakmak bu izi kaçırırdı.
- Grup işaretçileriyle alt sınır: %4,8 / %13,4 / %17,0 / %18,5 (gerçeğin altında).

Ek düzeyi için (LLM tarzı cümlelerde "-mAktAdIr" ve edilgen "-Il+mAktAdIr"):
- Ek yoğunluğunda Prog2 (-mAktA) ve Cop (-DIr) 2024'te beklenenin ~11 katı.
- Zincir düzeyinde "Prog2+A3sg+Cop" 9 kat, edilgen "Pass+Verb+Prog2+A3sg+Cop"
  ayrı zincir olarak yakalandı.
