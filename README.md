## Performance Comparison (NASA CMAPSS)

**Dataset:** [NASA CMAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)  
**Current SoTA Work:** [Sensors 2024, 24(3), 824](https://www.mdpi.com/1424-8220/24/3/824)


| Method | FD001 (RMSE) | FD001 (Score) | FD002 (RMSE) | FD002 (Score) | FD003 (RMSE) | FD003 (Score) | FD004 (RMSE) | FD004 (Score) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| BiLSTM (2018) | 13.65 | 295 | 23.18 | 4130 | 13.74 | 317 | 24.86 | 5430 |
| DCNN (2018) | 12.61 | 237 | 22.36 | 1041 | 12.64 | 284 | 23.31 | 12,466 |
| GCT (2021) | 11.27 | - | 22.81 | - | 11.42 | - | 24.86 | - |
| BiLSTM Attention (2021) | 13.78 | 255 | 15.94 | 1280 | 14.36 | 438 | 16.96 | 1650 |
| DATCN (2021) | 11.78 | 229 | 16.95 | 1842 | 11.56 | 257 | 18.23 | 2317 |
| AGCNN (2021) | 12.42 | 225 | 19.43 | 1492 | 13.39 | 227 | 21.50 | 3392 |
| DAST (2022) | 11.43 | 203 | 15.25 | 924 | 11.32 | **154** | 18.23 | 1490 |
| DLformer (2023) | - | - | 15.93 | 1283 | - | - | **15.86** | 1601 |
| CNN-LSTM-SAM (2023) | 12.6 | 261 | 18.9 | 1156 | 12.5 | 253 | 20.5 | 2425 |
| BiLSTM-DAE-Trans (2023)| 10.98 | 186 | 16.12 | 2937 | 11.14 | 252 | 18.15 | 3840 |
| Hierarchical Transformer (SoTA) | **10.61** | **169** | **13.47** | **784** | **10.71** | 202 | 15.87 | **1449** |
| Proposed Method(Mamba2) | - | - | - | - | - | - | 18.5837 | 2898 |

**Note:** Mamba2 outperformed all studies that do not use the attention mechanism and possesses significantly fewer parameters compared to those utilizing attention.

