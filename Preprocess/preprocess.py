import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler

def load_data(file_path):
    # C-MAPSS standart sütun isimleri
    index_names = ['unit_nr', 'time_cycles']
    setting_names = ['setting_1', 'setting_2', 'setting_3']
    sensor_names = ['s_{}'.format(i) for i in range(1, 22)] 
    col_names = index_names + setting_names + sensor_names
    
    print(f"Veri okunuyor: {file_path}")
    df = pd.read_csv(file_path, sep=r'\s+', header=None, names=col_names)
    return df, setting_names, sensor_names

def process_dataframe(df, setting_names, sensor_names, is_test=False, true_rul_df=None, scaler=None):
    # 1. Gereksiz Sensörleri Çıkar
    # Kullanıcı isteği üzerine bu sensörler atılıyor
    drop_sensors = ['s_1', 's_5', 's_6', 's_10', 's_16', 's_18', 's_19']
    df.drop(columns=drop_sensors, inplace=True, errors='ignore')
    
    # Kalan sensörler
    remaining_sensors = [s for s in sensor_names if s not in drop_sensors]
    
    # 2. RUL Hesapla
    max_cycle = df.groupby('unit_nr')['time_cycles'].max().reset_index()
    max_cycle.columns = ['unit_nr', 'max']
    
    if is_test:
        # TEST VERİSİ RUL HESABI
        # Test verisi kesilmiş veridir. Gerçek RUL dosyadan (true_rul_df) alınır.
        # Formul: RUL(t) = True_RUL_of_Unit + (Max_Cycle_of_Unit - Current_Cycle_t)
        # Ancak burada genellikle Test verisinin SON satırı için RUL tahmini yapılır.
        # Eğitim için test verisinin tüm geçmişini kullanacaksak, RUL kolonunu buna göre doldurmalıyız.
        
        # True RUL bilgisini max_cycle ile birleştir
        # true_rul_df index'i unit_nr ile eşleşmeli (0-indexed geliyorsa dikkat)
        
        # true_rul_df tek sütunlu varsayıyoruz
        true_rul_df['unit_nr'] = true_rul_df.index + 1
        true_rul_df.columns = ['true_rul', 'unit_nr']
        
        rul_info = max_cycle.merge(true_rul_df, on='unit_nr', how='left')
        
        # Ana tabloyu birleştir
        df = df.merge(rul_info, on='unit_nr', how='left')
        
        # RUL hesapla: 
        # Bir unit'in t anındaki RUL'u: (O unitin toplam ömrü) - t
        # Toplam Ömür = (Kesildiği andaki Max Cycle) + (Kalan Gerçek Ömür)
        df['RUL'] = (df['max'] + df['true_rul']) - df['time_cycles']
        
        # Temizlik
        df.drop(columns=['max', 'true_rul'], inplace=True)
        
    else:
        # EĞİTİM VERİSİ RUL HESABI
        # Eğitim verisi bozulana kadar gider.
        # RUL = Max Ömür - O Anki Döngü
        df = df.merge(max_cycle, on='unit_nr', how='left')
        df['RUL'] = df['max'] - df['time_cycles']
        df.drop(columns=['max'], inplace=True)
    
    # 3. RUL Clipping
    df['RUL'] = df['RUL'].clip(upper=125)
    
    # 4. Normalization
    features_to_normalize = setting_names + remaining_sensors
    
    if scaler is None:
        # Train aşaması: Fit + Transform
        scaler = MinMaxScaler()
        df[features_to_normalize] = scaler.fit_transform(df[features_to_normalize])
    else:
        # Test aşaması: Sadece Transform
        df[features_to_normalize] = scaler.transform(df[features_to_normalize])
        
    return df, scaler, len(features_to_normalize)

def main():
    # Yollar repo köküne göre kurulur; script her makinede aynı şekilde çalışır.
    base_dir = Path(__file__).resolve().parents[1]
    train_path = base_dir / "data" / "raw" / "train_FD004.txt"
    test_path = base_dir / "data" / "raw" / "test_FD004.txt"
    rul_path = base_dir / "data" / "raw" / "RUL_FD004.txt"
    output_dir = base_dir / "data" / "processed"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # --- TRAIN & VALIDATION IŞLEMLERI ---
    print("\n--- TRAIN ve VALIDATION Verisi İşleniyor ---")
    if os.path.exists(train_path):
        raw_train_df, setting_names, sensor_names = load_data(train_path)
        
        # Validation Unitleri
        validation_units = list(range(212, 250)) # 212'den 249'a kadar
        
        # Split Data
        print(f"Validation Unitleri: {validation_units[0]} ... {validation_units[-1]}")
        
        train_df = raw_train_df[~raw_train_df['unit_nr'].isin(validation_units)].copy()
        val_df = raw_train_df[raw_train_df['unit_nr'].isin(validation_units)].copy()
        
        print(f"Split Sonrası - Train Satır: {len(train_df)}, Val Satır: {len(val_df)}")
        
        # 1. TRAIN: Fit + Transform
        train_df_processed, scaler, num_features = process_dataframe(
            train_df, setting_names, sensor_names, is_test=False, scaler=None
        )
        print(f"Train Özet: {train_df_processed.shape}, Norm. Feat: {num_features}")
        
        # 2. VALIDATION: Sadece Transform (Train parametreleri ile)
        val_df_processed, _, _ = process_dataframe(
            val_df, setting_names, sensor_names, is_test=False, scaler=scaler
        )
        print(f"Validation Özet: {val_df_processed.shape}")
        
        # 3. MERGE & SAVE
        # Tekrar birleştir ve sırala
        final_train_df = pd.concat([train_df_processed, val_df_processed], axis=0)
        final_train_df.sort_values(by=['unit_nr', 'time_cycles'], inplace=True)
        
        print(f"Final Train Özet: {final_train_df.shape}")
        
        train_out = os.path.join(output_dir, 'train_FD004_processed.csv')
        final_train_df.to_csv(train_out, index=False)
        print(f"Kaydedildi: {train_out}")

    else:
        print("Train dosyası bulunamadı!")
        return

    # --- TEST IŞLEMLERI ---
    print("\n--- TEST Verisi İşleniyor ---")
    if os.path.exists(test_path) and os.path.exists(rul_path):
        test_df, _, _ = load_data(test_path)
        
        # RUL dosyasını oku
        true_rul_df = pd.read_csv(rul_path, sep=r'\s+', header=None)
        
        test_df_processed, _, _ = process_dataframe(
            test_df, setting_names, sensor_names, is_test=True, 
            true_rul_df=true_rul_df, scaler=scaler
        )
        
        print(f"Test Özet: {test_df_processed.shape}")
        
        test_out = os.path.join(output_dir, 'test_FD004_processed.csv')
        test_df_processed.to_csv(test_out, index=False)
        print(f"Kaydedildi: {test_out}")
        
        print("\nTest Verisi İlk 5 Satır:")
        print(test_df_processed.head())
    else:
        print("Test veya RUL dosyası eksik!")

if __name__ == "__main__":
    main()
