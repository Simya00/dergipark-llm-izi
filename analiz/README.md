# Analiz

Kobak vd. (2025) aşırı kelime yönteminin DergiPark özetlerine uygulanması.
Girdi: `../toplama/makaleler.jsonl` (yalnızca `yil_guvenilir` dolu makaleler).

İlk adım Kobak vd. gibi **kelime biçimi** düzeyinde; kök (Zemberek) ve
n-gram düzeyi sonraki adım.

## Adımlar

```bash
cd analiz

# 1) Her kelimenin her yıl kaç özette geçtiği (her yıl için dosya bir kez okunur)
python3 kelime_siklik.py --dil tr
python3 kelime_siklik.py --dil en

# 2) Beklenenden fazla artan kelimeler (aday liste)
python3 asiri_kullanim.py --dil tr --hedef 2024
python3 asiri_kullanim.py --dil en --hedef 2024

# 3) Aday listeden içerik kelimelerini (covid, deprem...) ayıklayıp üslup
#    kelimelerini isaretciler_tr.txt'ye yaz, sonra alt sınırı hesapla:
python3 alt_sinir.py --dil tr --isaretciler isaretciler_tr.txt
```

## Yöntem

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
