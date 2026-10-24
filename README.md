# DergiPark'ta LLM İzi

DergiPark'taki Türkçe özlerde ve İngilizce abstract'larda büyük dil modeli
(ChatGPT vb.) kullanımının izlerini **aşırı kelime (excess vocabulary)**
yöntemiyle inceler.

Yöntem: Kobak, González-Márquez, Horvát, Lause (2025), *Delving into
LLM-assisted writing in biomedical publications through excess vocabulary*,
Science Advances (arXiv:2406.07016). Eğitilmiş bir dedektör kullanmadan,
kelime sıklıklarının LLM'ler olmasaydı ne olacağı tahmin edilip gerçek
değerle karşılaştırılır; buradan LLM ile işlenmiş özetlerin oranına bir
**alt sınır** çıkarılır.

Bu çalışmanın katkıları:
- Eklemeli Türkçe için kelime yerine **kök (lemma)**, **n-gram** ve **ek**
  düzeyinde analiz (Zemberek).
- Aynı makalenin Türkçe özü ile İngilizce abstract'ındaki LLM izinin
  **iki dilli karşılaştırması**.
- 2025–2026'da işaretçi kelimelerde olası **düşüş** (yazarların izleri silmesi).

## Klasörler

| Klasör | İçerik |
|---|---|
| `toplama/` | DergiPark OAI-PMH toplayıcı ve ayrıştırıcı ([talimatlar](toplama/README.md)) |
| `analiz/` | Kelime sıklıkları, aşırı kullanım, alt sınır ([talimatlar](analiz/README.md)) |
| `notlar/` | [Günlük ilerleme](notlar/gunluk_ilerleme.md), veri planı, ESOGÜ dergi listesi, e-posta taslakları |

## Durum

- [x] Toplama betikleri
- [x] Gerçek DergiPark'ta `deneme` + `setler`
- [x] ESOGÜ pilotu (arşiv tarihi sorunu bulundu ve çözüldü)
- [ ] Tüm DergiPark (sürüyor)
- [x] Kelime düzeyi analiz kodu (sahte veriyle doğrulandı)
- [ ] Gerçek veride kelime düzeyi sonuçlar
- [ ] Kök (Zemberek) ve n-gram düzeyi
- [ ] İki dilli karşılaştırma, 2025–2026 düşüşü
