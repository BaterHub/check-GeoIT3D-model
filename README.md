# check-GeoIT3D-model

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/BaterHub/check-GeoIT3D-model/blob/main/chk_3D.ipynb)

## Introduzione

Il notebook `chk3D` è progettato per verificare la presenza e la validità dei file necessari per il caricamento dei modelli geologici 3D in formato GOCAD e CSV secondo le specifiche del visualizzatore web GeoIT3D.

### Obiettivi Principali

- Verificare la struttura dei file
- Controllare la formattazione dei dati
- Garantire la coerenza dei dati geologici 3D secondo il formato dati del web-viewer GeoIT3D

## Struttura del Notebook

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

1. **Presenza dei File**
   - Controllo dei file necessari nella cartella specificata
   - Identificazione di file mancanti, simili o aggiuntivi

2. **Validazione File CSV**
   - Controllo della codifica (UTF-8)
   - Verifica delle terminazioni di riga
   - Convalida del numero di campi
   - Controllo degli ID univoci
   - Validazione campi booleani e numerici

3. **Analisi File GOCAD**
   - Verifica delle geometrie
   - Convalida della sintassi e delle keywords

4. **Validazione Descriptor JSON**
   - Controllo della struttura del file descriptor.json
   - Verifica dei campi richiesti

## Utilizzo

1. Clicca sul badge "Open in Colab" per aprire il notebook
2. Caricare il pacchetto dati (file) del modello 3D all'interno della cartella "cartella_files"
3. Eseguire il notebook per ottenere il report di validazione

## Specifiche Tecniche

- I file devono essere prodotti secondo le specifiche CARG per i modelli 3D
- Tutti i file devono essere posizionati in un'unica cartella nominata "cartella_files"

## Note

- Il notebook è essenziale per garantire l'accuratezza e la conformità dei dati secondo il modello dati richiesto per il caricamento dei modelli geologici 3D sul web-viewer GeoIT3D di ISPRA