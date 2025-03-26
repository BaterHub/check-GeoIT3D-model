# check-GeoIT3D-model

# GeoIT3D Model Validator 🔍

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Release](https://img.shields.io/badge/version-1.0.0-blue)

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BaterHub/check-GeoIT3D-model/blob/main/chk_3D.ipynb)

## Introduzione

> Strumento di validazione per modelli geologici 3D compatibili con **GeoIT3D Web Viewer*

Il notebook `chk3D` è progettato per verificare la presenza e la validità dei file necessari per il caricamento dei modelli geologici 3D in formato GOCAD e CSV secondo le specifiche del visualizzatore web GeoIT3D di ISPRA - Servizio Geologico d'Italia.

### Obiettivi Principali

- Verificare la struttura dei file
- Controllare la formattazione dei dati
- Garantire la coerenza dei dati geologici 3D secondo il formato dati del web-viewer GeoIT3D


### Librerie Importate

- `sys`: Accesso a parametri e funzioni del sistema
- `os`: Gestione di file e directory
- `pandas`: Manipolazione e analisi dei dati
- `IPython.display`: Visualizzazione di output formattati
- `datetime`: Gestione di date e orari

### Moduli Importati

- `file_utils.py`: funzioni per la verifica della presenza dei file
- `csv_validator.py`: funzioni per la validazione della struttura e del contenuto dei file CSV
- `ts_validator.py`: funzioni per la validazione e l'analisi dei file GOCAD (geometrie)
- `json_validator.py`: funzioni per la validazione del file descriptor.json

## Funzionalità Principali

### Verifica File

## 📁 File Richiesti

| File                          | Descrizione                     | Stato       |
|-------------------------------|---------------------------------|-------------|
| `dem.ts`                      | Modello digitale di elevazione  | **Obbligatorio** ✅ |
| `faults.ts`                   | Superfici di faglia             | **Obbligatorio** ✅ |
| `horizons.ts`                 | Superfici geologiche            | **Obbligatorio** ✅ |
| `units.ts`                    | Unità geologiche                | **Obbligatorio** ✅ |
| `descriptor.json`             | Metadati del modello            | **Obbligatorio** ✅ |
| `main_*_attributes.csv`       | Attributi principali (7 file)   | **Obbligatorio** ✅ |

## ✅ Cosa Verifica

## 🎯 Funzionalità

✔ **Verifica completa** di tutti i componenti del modello  
✔ **Controllo incrociato** tra file correlati  
✔ **Validazione formale** secondo specifiche tecniche  
✔ **Generazione report** dettagliato  

### 🔍 Controlli Generali (tutti i file)
- ✔ Presenza e nomi corretti dei file  
- ✔ Encoding UTF-8  
- ✔ Terminazioni linea (LF)  

### 📊 File CSV
- 🧩 Struttura colonne conforme  
- 🔢 Tipi di dati corretti (numerici/booleani)  
- 🏷️ Codici validi (tabelle dominio)  
- 🔗 Consistenza ID tra file correlati  

### 🗺️ File GOCAD (.ts)
- 📜 Sintassi corretta  
- 🔑 Keywords valide  
- 🕸️ Connettività mesh  
- 🔄 Corrispondenza ID con CSV  

### 📝 descriptor.json
- ✅ Campi obbligatori presenti  
- ⏱️ Formato datetime valido  
- 📦 Struttura metadati corretta  

## 🚀 Utilizzo su colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BaterHub/check-GeoIT3D-model/blob/main/chk_3D.ipynb)

1. **Apertura notebook**:
    Clicca sul badge "Open in Colab" per aprire il notebook
2. **Configurazione iniziale**:
    Carica il workspace eseguendo la prima cella 
3. **Preparazione files**:
    Carica il pacchetto dati del modello 3D (file .csv, .ts e .json) all'interno della cartella "cartella_files"
4. **Esecuzione notebook**:
    Posizionati nella seconda cella e lancia lo script con "ctrl + F10" oppure dal menù "Runtime > Run cell and below"
5. **Lettura log file**:
    Al termine del RUN verrà generato un log_file all'interno della cartella_files che conterrà il report sui check eseguiti.

## 🚀 Utilizzo in locale

1. **Clona il repository**:
   ```bash
   git clone https://github.com/BaterHub/check-GeoIT3D-model.git
   cd check-GeoIT3D-model
2. **Preparazione files**:
    Carica il pacchetto dati del modello 3D (file .csv, .ts e .json) all'interno della cartella "cartella_files"
3. **Esecuzione notebook**:
    Eseguire il RUN del notebook

## Specifiche Tecniche

- I file da validare devono essere prodotti secondo le specifiche CARG per i modelli 3D
- Tutti i file devono essere posizionati in un'unica cartella nominata "cartella_files"

## Note

- Il notebook è essenziale per garantire l'accuratezza e la conformità dei dati secondo il modello dati richiesto per il caricamento dei modelli geologici 3D sul web-viewer GeoIT3D di ISPRA
- Il pacchetto dati sarà conforme agli standard richiesti per il caricamento sul web-viewer GeoIT-3D solo se passerà tutte le verifiche (ammessi anche i WARNINGS)