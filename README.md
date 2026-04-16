# NASA C-MAPSS 2008 RUL Projesi

Bu repo, NASA C-MAPSS veri seti ile Remaining Useful Life (RUL) tahmini çalışmasını içerir. Repoda yalnızca projeyi çalıştırmak için gereken veri dosyaları, preprocess kodları, eğitim notebook/scriptleri ve bağımlılık listesi tutulur. Sunumlar, raporlar, model çıktıları, grafikler ve lokal çalışma dosyaları `.gitignore` ile dışarıda bırakılır.

## İçerik

- `data/raw/`: FD001-FD004 ham C-MAPSS `.txt` dosyaları ve RUL dosyaları.
- `data/processed/`: Eğitim akışında kullanılan işlenmiş `.csv` dosyaları.
- `Preprocess/`: FD004 preprocess ve sekans uzunluğu analiz kodları.
- `scripts/fd002_sensor_selection_and_clustering.py`: FD002 operasyon rejimi kümeleme ve sensör seçimi hazırlığı.
- `notebooks/`: FD002 klasik model ve Attention-LSTM eğitim notebookları.
- `model_script/mamba2.ipynb`: FD004 için deneysel Mamba2 eğitim notebooku.
- `requirements.txt`: Python bağımlılıkları.

## Kurulum

Python paketlerini global ortama kurma; proje için sanal ortam kullan.

```bash
cd /Users/cihan/Desktop/CMAPSS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Çalıştırma Sırası

1. Ham verilerin yerinde olduğunu kontrol et:

```bash
ls data/raw
```

2. FD004 train/test sekans uzunluklarını incele:

```bash
python Preprocess/analyze_sequence_lengths.py
```

3. FD004 verisini işle:

```bash
python Preprocess/preprocess.py
```

Bu adım şu dosyaları üretir veya günceller:

- `data/processed/train_FD004_processed.csv`
- `data/processed/test_FD004_processed.csv`

4. FD002 için operasyon rejimi ve sensör seçimi hazırlığını çalıştır:

```bash
python scripts/fd002_sensor_selection_and_clustering.py
```

Bu adım eğitim notebooklarının kullandığı şu dosyaları üretir veya günceller:

- `data/processed/fd002_train_regimes.csv`
- `data/processed/fd002_test_regimes.csv`

Script ayrıca yerel analiz grafikleri ve tabloları üretir; bunlar `reports/` altında kalır ve repoya alınmaz.

5. FD002 klasik modellerini eğit:

```bash
jupyter nbconvert --to notebook --execute notebooks/fd002_svm_rf_training.ipynb --inplace
```

Bu notebook SVR ve Random Forest modellerini eğitir. Model dosyaları, tahminler ve metrikler `artifacts/` altında üretilir; bu klasör repoya alınmaz.

6. FD002 Attention-LSTM modelini eğit:

```bash
jupyter nbconvert --to notebook --execute notebooks/fd002_attention_lstm_training.ipynb --inplace
```

Bu notebook PyTorch tabanlı Attention-LSTM modelini eğitir. Model state dosyaları ve eğitim çıktıları `artifacts/` altında üretilir; bu klasör repoya alınmaz.

7. İsteğe bağlı olarak FD004 Mamba2 denemesini çalıştır:

```bash
jupyter notebook model_script/mamba2.ipynb
```

Bu notebook deneysel/opsiyonel akıştır. `mamba_ssm` paketi gerekiyorsa ayrıca kurulmalıdır. Notebook, FD004 preprocess çıktıları hazır olduktan sonra kullanılmalıdır.

## Git Politikası

Repoya alınanlar:

- Ham ve işlenmiş veri dosyaları (`data/raw/*.txt`, `data/processed/*.csv`)
- Preprocess kodları
- Eğitim script/notebookları
- `requirements.txt`
- `README.md`
- `.gitignore`

Repoya alınmayanlar:

- `reports/`
- `artifacts/`
- `models/`
- `kaynaklar/`
- `.venv/`
- Notebook cache dosyaları
- Python cache dosyaları
- `.DS_Store`
