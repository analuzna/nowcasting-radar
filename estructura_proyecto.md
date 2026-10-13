# Estructura del proyecto

**radar-nowcasting/**

├── data/
│   ├── raw/            # volúmenes de radar originales, intocados (solo lectura)
│   ├── interim/         # post-QC, reproyectados, aún no en grilla final
│   ├── processed/        # grilla uniforme espacial+temporal, lista para empaquetar
│   └── packaged/         # secuencias empaquetadas train/val (secuencias) + metadata
├── configs/              # yaml: definición  grilla,  secuencias,  modelo,  entrenamiento
├── src/
│   ├── ingestion/         # lectura con pyart, catálogo de eventos disponibles
│   ├── datasets/          # Dataset/DataLoader
│   ├── models/            # ConvLSTM (arquitecturas)
│   ├── training/          # loop, loss, scheduler 
│   └── evaluation/        # CSI, POD, FAR, visualización -> MLflow
├── experiments/           # una subcarpeta por corrida: config congelada + checkpoints + logs + métricas -> Optuna
├── notebooks/             # exploración
├── scripts/               # entry points CLI (run_preprocessing.py, run_training.py...)
└── tests/