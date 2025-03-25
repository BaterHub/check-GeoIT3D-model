#!/usr/bin/env python
# coding: utf-8

# # chk3D
# 

# # 1. Importa librerie e funzioni

# In[890]:


## Importa librerie necessarie
import sys
import os
import pandas as pd
from IPython.display import display, Markdown, HTML
from datetime import datetime

#############################################################################################
## Importa funzioni
import importlib # modulo per il reload delle funzioni

# Reimporta i moduli originali
import file_utils
import csv_validator
import ts_validator
import json_validator

# Ricarica forzata di ciascun modulo
importlib.reload(file_utils)
importlib.reload(csv_validator)
importlib.reload(ts_validator)
importlib.reload(json_validator)

# Reimporta le funzioni dai moduli ricaricati
from file_utils import verifica_file_presenti
from csv_validator import verifica_csv, valida_csv, verifica_numero_campi_csv, valida_id_univoci_csv, valida_campi_booleani_csv, valida_codici_csv, valida_campi_numerici_csv
from ts_validator import analyze_gocad_files, print_gocad_summary, valida_gocad_e_confronta_csv
from json_validator import check_descriptor_structure
#############################################################################################

# In[891]:


# Percorso cartella
cartella = input("Inserisci il nome della cartella contenente i file: NB deve essere nella stessa cartella dell'eseguibile")
# ## 1.1 Specifiche file

# In[892]:


## Lista dei file necessari
file_necessari = ["dem.ts", "faults.ts", "horizons.ts", "units.ts", "descriptor.json",
                  "main_fault_attributes.csv", "main_fault_derived_attributes.csv", "main_fault_kinematics_attributes.csv",
                  "main_horizon_attributes.csv", "main_horizon_derived_attributes.csv", "main_unit_attributes.csv"]

## Validazione della struttura dei file CSV
# Definiamo le specifiche per ogni file CSV
specifiche_csv = {
    'main_fault_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'name_fault', 'name_model', 'name_system', 'type_fault',
                         'color_fault', 'color_tone', 'evaluation_method', 'observation_method',
                         'active_fault', 'seismogenic_fault', 'capable_fault'],
        'campi_lunghezza_custom': {
            'code_model': 4,
            'name_fault': 15,
            'name_model': 15,
            'name_system': 15
        }
    },
    'main_fault_derived_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'mean_dip_azimuth', 'mean_dip_azimuth_uom',
                         'mean_dip', 'mean_dip_uom', 'mean_strike', 'mean_strike_uom'],
        'campi_lunghezza_custom': {
            'code_model': 4
        }
    },
    'main_fault_kinematics_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'net_slip', 'net_slip_uom', 'hor_throw', 'hor_throw_uom',
                         'ver_throw', 'ver_throw_uom', 'str_slip', 'str_slip_uom', 'heave', 'heave_uom',
                         'dip_slip', 'dip_slip_uom', 'rake', 'rake_uom', 'pitch', 'pitch_uom'],
        'campi_lunghezza_custom': {
            'code_model': 4
        }
    },
    'main_horizon_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'name_surface', 'name_model', 'type_contact',
                         'color_surface', 'color_tone', 'age_min_surface', 'age_max_surface',
                         'evaluation_method', 'observation_method', 'id_ref_unit_up', 'id_ref_unit_down'],
        'campi_lunghezza_custom': {
            'code_model': 4,
            'name_surface': 15,
            'name_model': 15
        }
    },
    'main_horizon_derived_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'mean_dip_azimuth', 'mean_dip_azimuth_uom',
                         'mean_dip', 'mean_dip_uom', 'mean_strike', 'mean_strike_uom'],
        'campi_lunghezza_custom': {
            'code_model': 4
        }
    },
    'main_unit_attributes.csv': {
        'campi_attesi': ['id', 'code_model', 'name_unit', 'name_model', 'type_unit',
                         'type_lithology_main', 'type_lithology_sec', 'color_unit', 'color_tone',
                         'id_surface_top', 'id_surface_bottom', 'age_up', 'age_low',
                         'type_event_process', 'type_event_environment'],
        'campi_lunghezza_custom': {
            'code_model': 4,
            'name_unit': 15,
            'name_model': 15
        }
    }
    # Aggiungi qui le specifiche per altri file CSV
}



# # 2. Imposta logging

# In[893]:


import logging

# Ottieni il nome della cartella per il file di log
log_filename = os.path.basename(cartella) + ".log"
log_filepath = os.path.join(cartella, log_filename)

# Cancella il file di log esistente se presente
if os.path.exists(log_filepath):
    # Apri il file in modalità 'w' per sovrascrivere completamente il contenuto
    with open(log_filepath, 'w') as f:
        f.write("")  # Sovrascrive con stringa vuota

# Configura il logging
logging.basicConfig(
    filename=log_filepath,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='w',  # Importante: 'w' sovrascrive il file invece di appendere
    force=True
)

# Reindirizza stdout e stderr al file di log
class LoggerWriter:
    def __init__(self, level):
        self.level = level
    
    def write(self, message):
        if message.strip():  # Evita righe vuote
            self.level(message)
    
    def flush(self):  # Necessario per compatibilità con sys.stdout
        pass

sys.stdout = LoggerWriter(logging.info)  # Reindirizza print() in logging.info
sys.stderr = LoggerWriter(logging.error)  # Reindirizza errori in logging.error

# Log iniziale per indicare l'avvio di una nuova sessione
logging.info("---- NUOVA SESSIONE AVVIATA ----")

# # 3. Verifica la presenza di tutti i file nella cartella (e segnala quelli aggiuntivi)

# In[894]:


# Esegue la verifica della presenza dei file
file_presenti, file_mancanti, file_simili, file_aggiuntivi = verifica_file_presenti(cartella, file_necessari)

# Visualizza i risultati
print(f"Cartella analizzata: {os.path.abspath(cartella)}")
print("\nFile presenti:")
for file in file_presenti:
    print(f"✅ {file}")

print("\nFile mancanti:")
for file in file_mancanti:
    print(f"❌ {file}")

# Visualizza i file aggiuntivi
if file_aggiuntivi:
    print("\nAltri file nella cartella:")
    for file in file_aggiuntivi:
        print(f"ℹ️ {file}")

risultati = pd.DataFrame({
    'Nome File': file_necessari,
    'Presente': [file in file_presenti for file in file_necessari],
    'File Simili': [', '.join(file_simili.get(file, [])) if file in file_mancanti else 'N/A' for file in file_necessari]
})

# Visualizza il DataFrame
display(Markdown("### Riepilogo dei file mandatori"))
display(risultati)
print(risultati)

# ## Percentuale di completezza
# completezza = len(file_presenti) / len(file_necessari) * 100 if file_necessari else 100
# print(f"\nPercentuale di completezza: {completezza:.2f}%")

# # 4. Verifica formattazione file CSV

# ##  4.1 codifica e terminazione linee

# In[895]:


# Filtriamo i file CSV dalla lista dei file necessari
file_csv = [file for file in file_necessari if file.lower().endswith('.csv')]

# Visualizziamo i risultati della verifica dei file CSV
display(Markdown("### Riepilogo formattazione file CSV"))

# Eseguiamo la verifica dei file CSV
risultati_csv = verifica_csv(cartella, file_csv)

# Creiamo un DataFrame per visualizzare i risultati della verifica dei file CSV
dati_csv = []
for file, info in risultati_csv.items():
    if info['esiste']:
        stato_encoding = "✅ UTF-8" if info['is_utf8'] else f"❌ {info['encoding']}"
        stato_terminazioni = "✅ LF" if info['is_lf'] else f"❌ {info['terminazioni']}"
        dati_csv.append({
            'Nome File': file,
            'Esiste': "✅",
            'Encoding': stato_encoding,
            'Terminazioni': stato_terminazioni
        })
    else:
        dati_csv.append({
            'Nome File': file,
            'Esiste': "❌",
            'Encoding': "N/A",
            'Terminazioni': "N/A"
        })

df_csv = pd.DataFrame(dati_csv)
display(df_csv)

# Riepilogo
print("\nRiepilogo verifica file CSV (codifica):")
for file, info in risultati_csv.items():
    if info['esiste']:
        if info['is_utf8'] and info['is_lf']:
            print(f"✅ {file} - UTF-8 con terminazioni LF")
        else:
            problemi = []
            if not info['is_utf8']:
                problemi.append(f"non è UTF-8 (rilevato: {info['encoding']})")
            if not info['is_lf']:
                problemi.append(f"non ha terminazioni LF (rilevato: {info['terminazioni']})")
            print(f"❌ {file} - {', '.join(problemi)}")
    else:
        print(f"❌ {file} - File non trovato")

# ## 4.2 numero campi per ogni record

# In[896]:


# Esegui la validazione del numero di campi
risultati, riepilogo = verifica_numero_campi_csv(cartella, specifiche_csv, verbose=True)

# Visualizziamo i risultati della validazione
display(Markdown("### Validazione del numero dei campi dei file CSV"))

# Visualizza i risultati
pd.DataFrame.from_dict(risultati, orient='index')

# ## 4.3 headers, separatori, lunghezza campi testo

# In[897]:


# Eseguiamo la validazione della struttura dei file CSV
risultati_validazione = valida_csv(cartella, specifiche_csv)

# Visualizziamo i risultati della validazione
display(Markdown("### Validazione della struttura dei file CSV"))

# Creiamo un DataFrame per visualizzare i risultati della validazione
dati_validazione = []
for file, info in risultati_validazione.items():
    if info['esiste']:
        stato = "✅ Valido" if info.get('valido', False) else "❌ Non valido"
        errori = "<br>".join(info.get('errori', [])) if info.get('errori') else "Nessun errore"
        dati_validazione.append({
            'Nome File': file,
            'Stato': stato,
            'Errori': errori
        })
    else:
        dati_validazione.append({
            'Nome File': file,
            'Stato': "❌ File non trovato",
            'Errori': "File non trovato"
        })

df_validazione = pd.DataFrame(dati_validazione)
# Usiamo HTML per formattare correttamente gli errori con interruzioni di riga
display(HTML(df_validazione.to_html(escape=False)))

# Riepilogo finale
print("\nRiepilogo validazione struttura file CSV (headers, separatori, lunghezza campi):")
for file, info in risultati_validazione.items():
    print(f"\n{file}:")
    if not info['esiste']:
        print("  ❌ File non trovato")
    elif info.get('valido', False):
        print("  ✅ Struttura valida")
    else:
        print("  ❌ Problemi riscontrati:")
        for errore in info.get('errori', []):
            print(f"    - {errore}")

# ## 4.4 controllo campi parametri aggiuntivi

# In[898]:


# Lista dei file CSV da controllare
file_da_controllare_numerici = [
    'main_fault_derived_attributes.csv',
    'main_horizon_derived_attributes.csv',
    'main_fault_kinematics_attributes.csv'
]

# Visualizziamo i risultati della validazione
display(Markdown("### Validazione campi numerici dei file CSV"))

# Validazione con output dettagliato
risultati, riepilogo = valida_campi_numerici_csv(cartella, file_da_controllare_numerici)

# Visualizzazione del riepilogo
display(Markdown(f"```\n{riepilogo}\n```"))

# ## 4.5 controllo campi booleani

# In[899]:


# Lista dei file CSV da controllare
file_da_controllare_boolean = [
    'main_fault_attributes.csv'
    # aggiungi altri file da controllare
]

# Visualizziamo i risultati della validazione
display(Markdown("### Validazione campi booleani dei file CSV"))

# Validazione con output dettagliato
risultati, riepilogo = valida_campi_booleani_csv(cartella, file_da_controllare_boolean)

# Visualizzazione del riepilogo
from IPython.display import Markdown
display(Markdown(f"```\n{riepilogo}\n```"))


# ## 4.6 correttezza ID's

# In[900]:



"""
NB Questa versione garantisce che:

I file main_fault_*.csv abbiano gli stessi ID nella colonna principale
I file main_horizon_*.csv abbiano gli stessi ID nella colonna principale
I file main_unit_*.csv (attualmente solo uno) possano essere estesi in futuro mantenendo la consistenza
"""

specifiche_id = {
    'main_fault_attributes.csv': {
        'colonne': {
            'id': 'FLT'
        },
        'colonna_principale': 'id'
    },
    'main_fault_derived_attributes.csv': {
        'colonne': {
            'id': 'FLT'
        },
        'colonna_principale': 'id'
    },'main_fault_kinematics_attributes.csv': {
        'colonne': {
            'id': 'FLT'
        },
        'colonna_principale': 'id'
    },'main_horizon_attributes.csv': {
        'colonne': {
            'id': 'SRF',
            'id_ref_unit_up': 'UNT',
            'id_ref_unit_down': 'UNT'
        },
        'colonna_principale': 'id'
    },'main_horizon_derived_attributes.csv': {
        'colonne': {
            'id': 'SRF'
        },
        'colonna_principale': 'id'
    },'main_unit_attributes.csv': {
        'colonne': {
            'id': 'UNT',
            'id_surface_top': 'SRF',
            'id_surface_bottom': 'SRF'
        },
        'colonna_principale': 'id'
    },
}


# Visualizziamo i risultati della validazione
display(Markdown("### Validazione ID nei file CSV"))

# Validazione con output dettagliato
risultati_id, riepilogo_id = valida_id_univoci_csv(cartella, specifiche_id)

# Visualizzazione del riepilogo
display(Markdown(f"```\n{riepilogo_id}\n```"))

# ## 4.7 esistenza codici tabelle domini

# In[901]:


# Percorso al file code_domain.csv nella cartella superiore
file_domini_codici = os.path.normpath(os.path.join(os.pardir, "code_domain.csv"))

print(f"Inizio validazione codici in {cartella} con file domini {file_domini_codici}")

specifiche_codici = {
    'main_fault_attributes.csv': {
        'colonne_codici': {
            'type_fault': 'type_fault',
            'color_fault': 'color_fault',
            'evaluation_method': 'evaluation_method',
            'observation_method': 'observation_method'
        }
    },
    'main_horizon_attributes.csv': {
        'colonne_codici': {
            'type_contact': 'type_contact',
            'color_surface': 'color_surface',
            'evaluation_method': 'evaluation_method',
            'observation_method': 'observation_method',
            'age_min_surface': 'age_min_surface',
            'age_max_surface': 'age_max_surface'
        }
    },
    'main_unit_attributes.csv': {
        'colonne_codici': {
            'type_unit': 'type_unit',
            'color_unit': 'color_unit',
            'type_event_process': 'type_event_process',
            'type_event_environment': 'type_event_environment',
            'age_up': 'age_up',
            'age_low': 'age_low',
            'type_lithology_main': 'type_lithology_main',
            'type_lithology_sec': 'type_lithology_sec'
        }
    }
}

# Con un file personalizzato
risultati, riepilogo = valida_codici_csv(cartella, specifiche_codici, 
                                         file_domini_codici=file_domini_codici, verbose=True)


# Visualizzazione del riepilogo
from IPython.display import Markdown
display(Markdown(f"```\n{riepilogo}\n```"))

# # 5. Verifica formattazione file GOCAD

# ## 5.1 struttura (header, coordinate, connettività, keywords, controllo poligonale)

# In[902]:


# Elenco dei file da analizzare
file_list = ["dem.ts", "faults.ts", "horizons.ts", "units.ts"]

# Definisci le keyword valide per ogni sezione
valid_header_keywords = ['GOCAD', 'TSurf', 'HEADER', 'name:', 'NAME', 'AXIS_NAME', 'AXIS_UNIT', 'ZPOSITIVE', 'GOCAD_ORIGINAL_COORDINATE_SYSTEM', 'END_ORIGINAL_COORDINATE_SYSTEM',
                         'PROPERTIES', 'PROP_LEGAL_RANGES', 'NO_DATA_VALUES', 'PROPERTY_CLASSES', 'PROPERTY_KINDS', 'PROPERTY_SUBCLASSES', 'ESIZES', 'UNITS']
valid_coordinate_keywords = ['TFACE', 'TSOLID', 'VRTX', 'PVRTX']
valid_connectivity_keywords = ['TRGL', 'TETRA']

# Lista di special keywords con relative regole di validazione
special_keywords = {
    '*visible:': {
        'valid_values': ['true', 'false', '1', '0', 'on', 'off'],
        'type': 'boolean',
        'description': 'Visibilità dell\'oggetto'
    },
    '*solid*color:': {
        'valid_values': 'rgb',  # Special case per colori RGB
        'type': 'color',
        'description': 'Colore RGB dell\'oggetto'
    }
}

# Analizza i file con validazione delle keywords
analysis = analyze_gocad_files(
    cartella=cartella,
    filenames=file_list,
    valid_header_kw=valid_header_keywords,
    valid_coord_kw=valid_coordinate_keywords,
    valid_conn_kw=valid_connectivity_keywords,
    special_keywords=special_keywords  # puoi omettere questo per usare i default
)

# Stampa solo il report sintetico
summary_ts = print_gocad_summary(analysis, cartella)

# ## 5.2 correttezza ID's e corrispondenza con csv

# In[903]:


# Specifiche per i file GOCAD
specifiche_gocad = {
    'faults.ts': {
        'prefisso_atteso': 'FLT',
        'csv_corrispondente': 'main_fault_attributes.csv'
    },
    'horizons.ts': {
        'prefisso_atteso': 'SRF',
        'csv_corrispondente': 'main_horizon_attributes.csv'
    },
    'units.ts': {
        'prefisso_atteso': 'UNT',
        'csv_corrispondente': 'main_unit_attributes.csv'
    }
}


# Poi valida i file GOCAD
risultati_gocad, riepilogo_gocad = valida_gocad_e_confronta_csv(cartella, specifiche_gocad, risultati_csv)

# # 6. Verifica DESCRIPTOR

# In[904]:


# struttura json
REQUIRED_FIELDS = {
    "code": str,
    "name": str,
    "description": dict,
    "author": str,
    "source": str,
    "doi": str,
    "license": str,
    "creation datetime": datetime,
    "publication datetime": datetime,
    "meta_url": type(None)
}

# Check
if __name__ == "__main__":
    report = check_descriptor_structure(cartella, REQUIRED_FIELDS)
    
    # Output a schermo
    print(report['summary'])


# Visualizzazione del riepilogo
display(report)
