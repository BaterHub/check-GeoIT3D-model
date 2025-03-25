# csv_validator.py
# Contiene funzioni per validare la struttura dei file CSV

import os
import chardet
import csv
import re
import pandas as pd


def verifica_csv(cartella, file_csv):
    """
    Verifica che i file CSV siano in formato UTF-8 e abbiano terminazioni di riga LF.
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        file_csv (list): Lista dei file CSV da verificare
        
    Returns:
        dict: Dizionario con i risultati della verifica per ogni file CSV
    """
    risultati = {}
    
    for file in file_csv:
        percorso_completo = os.path.join(cartella, file)
        
        if not os.path.exists(percorso_completo):
            risultati[file] = {
                'esiste': False,
                'encoding': None,
                'terminazioni': None
            }
            continue
            
        # Controllo dell'encoding
        with open(percorso_completo, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding']
            
            # Controllo delle terminazioni di riga
            contains_cr = b'\r\n' in raw_data
            
            if contains_cr:
                terminazioni = 'CRLF'  # Windows-style
            else:
                terminazioni = 'LF'    # Unix-style
                
        risultati[file] = {
            'esiste': True,
            'encoding': encoding,
            'terminazioni': terminazioni,
            'is_utf8': encoding and encoding.lower().replace('-', '') in ['utf8', 'utf', 'ascii'],
            'is_lf': terminazioni == 'LF'
        }
    
    return risultati

    

def valida_csv(cartella, specifiche_csv):
    """
    Verifica che i file CSV rispettino i vincoli specificati:
    - Presenza dei campi corretti nell'header
    - Uso della virgola come separatore
    - Lunghezza corretta per campi specifici (custom)
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        specifiche_csv (dict): Dizionario con le specifiche per ogni file CSV.
                             Formato: {
                                'nome_file.csv': {
                                    'campi_attesi': ['campo1', 'campo2', ...],
                                    'campi_lunghezza_custom': {
                                        'campo1': 10,  # Lunghezza massima 10 caratteri
                                        'campo2': 15,  # Lunghezza massima 15 caratteri
                                    }
                                },
                                ...
                             }
        
    Returns:
        dict: Dizionario con i risultati della validazione per ogni file
    """
    risultati = {}
    
    for nome_file, specifiche in specifiche_csv.items():
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': []
        }
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            continue
        
        # Controlliamo se il file usa virgole come separatore
        with open(percorso_file, 'r', encoding='utf-8', errors='replace') as f:
            prime_righe = ''.join([f.readline() for _ in range(3)])
            
            # Se non troviamo virgole ma troviamo altri separatori comuni
            if ',' not in prime_righe:
                if ';' in prime_righe:
                    risultato_file['errori'].append("Separatore errato: trovato ';' invece di ','")
                elif '\t' in prime_righe:
                    risultato_file['errori'].append("Separatore errato: trovato '\\t' (tab) invece di ','")
                else:
                    risultato_file['errori'].append("Separatore non riconosciuto o mancante")
        
        # Proviamo a leggere il file con pandas per controlli più dettagliati
        try:
            # Prova con la virgola come separatore
            df = pd.read_csv(percorso_file, sep=',', encoding='utf-8', on_bad_lines='warn')
            
            # Controlliamo i nomi delle colonne
            campi_attesi = specifiche.get('campi_attesi', [])
            if campi_attesi:
                campi_mancanti = [campo for campo in campi_attesi if campo not in df.columns]
                campi_extra = [campo for campo in df.columns if campo not in campi_attesi]
                
                if campi_mancanti:
                    risultato_file['errori'].append(f"Campi mancanti: {', '.join(campi_mancanti)}")
                if campi_extra:
                    risultato_file['errori'].append(f"Campi non attesi: {', '.join(campi_extra)}")
            
            # Controlliamo la lunghezza custom dei campi specificati
            campi_lunghezza_custom = specifiche.get('campi_lunghezza_custom', {})
            for campo, lunghezza_attesa in campi_lunghezza_custom.items():
                if campo in df.columns:
                    # Convertiamo i valori in stringhe e controlliamo la lunghezza
                    mask = df[campo].astype(str).str.len() > lunghezza_attesa
                    num_errori = mask.sum()
                    if num_errori > 0:
                        righe_errore = df.index[mask].tolist()
                        righe_da_mostrare = righe_errore[:5]  # Mostriamo solo le prime 5 righe con errori
                        
                        errore = f"Campo '{campo}' ha lunghezza > {lunghezza_attesa} caratteri in {num_errori} righe"
                        if righe_da_mostrare:
                            righe_str = ", ".join([str(r+2) for r in righe_da_mostrare])  # +2 per tenere conto dell'header e dell'indice base 0
                            if len(righe_errore) > 5:
                                righe_str += f" e altre {len(righe_errore) - 5} righe"
                            errore += f" (righe: {righe_str})"
                        
                        risultato_file['errori'].append(errore)
                else:
                    risultato_file['errori'].append(f"Campo '{campo}' non trovato per controllo lunghezza custom")
            
        except Exception as e:
            risultato_file['errori'].append(f"Errore nell'analisi del file: {str(e)}")
        
        # Se non ci sono errori, aggiungiamo un'informazione positiva
        if not risultato_file['errori']:
            risultato_file['valido'] = True
        else:
            risultato_file['valido'] = False
            
        risultati[nome_file] = risultato_file
    
    return risultati


def verifica_numero_campi_csv(cartella, specifiche_csv, verbose=True):
    """
    Verifica che ogni riga dei file CSV contenga esattamente il numero di campi
    corrispondenti a quelli specificati nei campi_attesi.
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        specifiche_csv (dict): Dizionario con le specifiche per ogni file CSV.
                             Formato: {
                                'nome_file.csv': {
                                    'campi_attesi': ['campo1', 'campo2', ...],
                                    ...
                                },
                                ...
                             }
        verbose (bool): Se True, stampa un report formattato durante l'esecuzione
        
    Returns:
        tuple: (dict con i risultati della validazione, str con il riepilogo)
    """
    risultati = {}
    
    # Contatori per il riepilogo finale
    totale_file = len(specifiche_csv)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0
    
    output_lines = []
    
    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE NUMERO CAMPI CSV - {totale_file} file da controllare")
        output_lines.append("="*60)
    
    for nome_file, specifiche in specifiche_csv.items():
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'valido': False
        }
        
        if verbose:
            output_lines.append(f"\n📄 File: {nome_file}")
            output_lines.append("  " + "-"*50)
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1
            
            if verbose:
                output_lines.append("  ❌ File non trovato")
            
            continue
        
        # Otteniamo il numero di campi attesi dalle specifiche
        campi_attesi = specifiche.get('campi_attesi', [])
        num_campi_attesi = len(campi_attesi)
        
        if not campi_attesi:
            risultato_file['errori'].append("Nessun campo atteso specificato")
            risultati[nome_file] = risultato_file
            file_con_errori += 1
            
            if verbose:
                output_lines.append("  ❌ Nessun campo atteso specificato")
            
            continue
        
        try:
            # Apriamo il file CSV direttamente per controllare il numero di campi
            righe_errate = []
            with open(percorso_file, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                for i, riga in enumerate(reader):
                    if i == 0:  # Saltiamo l'header
                        continue
                    
                    num_campi = len(riga)
                    if num_campi != num_campi_attesi:
                        righe_errate.append({
                            'riga': i + 1,  # +1 perché i è 0-based
                            'num_campi': num_campi
                        })
                        
                        # Limitiamo a 10 righe errate per non appesantire troppo il report
                        if len(righe_errate) >= 10:
                            break
            
            if righe_errate:
                num_righe_errate = len(righe_errate)
                errore_msg = f"Trovate {num_righe_errate} righe con numero di campi diverso da {num_campi_attesi}"
                
                # Aggiungiamo dettagli sulle prime 5 righe errate
                righe_da_mostrare = righe_errate[:5]
                righe_str = ", ".join([f"riga {r['riga']}: {r['num_campi']} campi" for r in righe_da_mostrare])
                
                if len(righe_errate) > 5:
                    righe_str += f" e altre {len(righe_errate) - 5} righe"
                
                errore_msg += f" (es. {righe_str})"
                risultato_file['errori'].append(errore_msg)
                
                if verbose:
                    output_lines.append(f"  ❌ {errore_msg}")
            else:
                if verbose:
                    output_lines.append(f"  ✅ Tutte le righe contengono i {num_campi_attesi} campi richiesti")
            
        except Exception as e:
            errore_msg = f"Errore nell'analisi del file: {str(e)}"
            risultato_file['errori'].append(errore_msg)
            
            if verbose:
                output_lines.append(f"  ❌ {errore_msg}")
        
        # Se non ci sono errori, impostiamo valido a True
        if not risultato_file['errori']:
            risultato_file['valido'] = True
            file_validi += 1
            
            if verbose:
                output_lines.append(f"  ✅ Tutte le righe contengono i {num_campi_attesi} campi richiesti")
        else:
            file_con_errori += 1
            
        risultati[nome_file] = risultato_file
    
    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE NUMERO CAMPI")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    riepilogo_lines.append("="*60)
    
    riepilogo = "\n".join(riepilogo_lines)
    
    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))
    
    return risultati, riepilogo



def valida_id_univoci_csv(cartella, specifiche_id_csv, verbose=True):
    """
    Verifica che gli ID nelle colonne specificate dei file CSV rispettino il formato,
    che gli ID nella colonna principale siano univoci e che gli ID delle colonne principali
    dei file dello stesso gruppo siano gli stessi.
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        specifiche_id_csv (dict): Dizionario con le specifiche per ogni file CSV.
        verbose (bool): Se True, stampa un report formattato durante l'esecuzione
        
    Returns:
        tuple: (dict con i risultati della validazione, str con il riepilogo)
    """
    risultati = {}
    
    # Contatori per il riepilogo finale
    totale_file = len(specifiche_id_csv)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0
    
    # Definizione dei gruppi di file che devono avere ID consistenti
    gruppi_file = {
        'fault': [
            'main_fault_attributes.csv',
            'main_fault_derived_attributes.csv',
            'main_fault_kinematics_attributes.csv'
        ],
        'horizon': [
            'main_horizon_attributes.csv',
            'main_horizon_derived_attributes.csv'
        ],
        'unit': [
            'main_unit_attributes.csv'
            # Eventuali file aggiuntivi possono essere aggiunti qui
        ]
    }
    
    # Dizionario per memorizzare gli ID delle colonne principali per gruppo
    id_per_gruppo = {gruppo: {} for gruppo in gruppi_file}
    
    output_lines = []
    
    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE ID CSV - {len(specifiche_id_csv)} file da controllare")
        output_lines.append("="*60)
    
    for nome_file, specifiche in specifiche_id_csv.items():
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'warning': [],
            'valido': False,
            'gruppo': None
        }
        
        # Determina a quale gruppo appartiene il file
        for gruppo, file_list in gruppi_file.items():
            if nome_file in file_list:
                risultato_file['gruppo'] = gruppo
                break
        
        colonne_da_controllare = specifiche.get('colonne', {})
        colonna_principale = specifiche.get('colonna_principale', None)
        
        if verbose:
            output_lines.append(f"\n📄 File: {nome_file} {'(' + risultato_file['gruppo'] + ')' if risultato_file['gruppo'] else ''}")
            output_lines.append("  " + "-"*50)
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1
            
            if verbose:
                output_lines.append("  ❌ File non trovato")
            
            continue
        
        try:
            # Leggiamo il file CSV
            df = pd.read_csv(percorso_file, sep=',', encoding='utf-8', on_bad_lines='warn')
            
            # Verifica che ci siano colonne
            if df.shape[1] == 0:
                risultato_file['errori'].append("Il file non contiene colonne")
                risultati[nome_file] = risultato_file
                file_con_errori += 1
                
                if verbose:
                    output_lines.append("  ❌ Il file non contiene colonne")
                continue
            
            # Controllo per ogni colonna specificata
            for colonna, prefisso_atteso in colonne_da_controllare.items():
                if colonna not in df.columns:
                    risultato_file['errori'].append(f"Colonna '{colonna}' non trovata")
                    continue
                
                valori_colonna = df[colonna].astype(str)
                
                # Controllo specifico per i campi 'id_surface_top' e 'id_surface_bottom' in 'main_unit_attributes.csv'
                if nome_file == 'main_unit_attributes.csv' and colonna in ['id_surface_top', 'id_surface_bottom']:
                    for index, valore in valori_colonna.items():
                        if valore in ['dem', 'nd', 'ND']:
                            # Aggiungi un warning se il valore è 'dem' o 'nd'
                            risultato_file['warning'].append({
                                "riga": index + 2,
                                "valore": valore,
                                "messaggio": f"Valore '{valore}' ammesso come warning per la colonna '{colonna}'"
                            })
                            if verbose:
                                output_lines.append(f"  ⚠️ Valore '{valore}' ammesso come warning per la colonna '{colonna}' (riga {index + 2})")
                        else:
                            # Altrimenti, applica il controllo normale
                            pattern = re.compile(f"^{prefisso_atteso}_\\d{{4}}_\\d{{3}}$")
                            if not pattern.match(valore):
                                risultato_file['errori'].append({
                                    "riga": index + 2,
                                    "valore": valore,
                                    "errore": f"Formato {colonna} non valido, atteso: {prefisso_atteso}_XXXX_XXX"
                                })
                                if verbose:
                                    output_lines.append(f"  ❌ Formato {colonna} non valido, atteso: {prefisso_atteso}_XXXX_XXX (riga {index + 2})")
                
                # Controllo specifico per i campi 'id_ref_unit_up' e 'id_ref_unit_down' in 'main_horizon_attributes.csv'
                elif nome_file == 'main_horizon_attributes.csv' and colonna in ['id_ref_unit_up', 'id_ref_unit_down']:
                    for index, valore in valori_colonna.items():
                        if valore.lower() == 'nd':
                            # Aggiungi un warning se il valore è 'nd'
                            risultato_file['warning'].append({
                                "riga": index + 2,
                                "valore": valore,
                                "messaggio": f"Valore '{valore}' ammesso come warning per la colonna '{colonna}'"
                            })
                            if verbose:
                                output_lines.append(f"  ⚠️ Valore '{valore}' ammesso come warning per la colonna '{colonna}' (riga {index + 2})")
                        elif valore == 'dem':
                            # Considera 'dem' come errore
                            risultato_file['errori'].append({
                                "riga": index + 2,
                                "valore": valore,
                                "errore": f"Valore '{valore}' non ammesso per la colonna '{colonna}'"
                            })
                            if verbose:
                                output_lines.append(f"  ❌ Valore '{valore}' non ammesso per la colonna '{colonna}' (riga {index + 2})")
                        else:
                            # Altrimenti, applica il controllo normale
                            pattern = re.compile(f"^{prefisso_atteso}_\\d{{4}}_\\d{{3}}$")
                            if not pattern.match(valore):
                                risultato_file['errori'].append({
                                    "riga": index + 2,
                                    "valore": valore,
                                    "errore": f"Formato {colonna} non valido, atteso: {prefisso_atteso}_XXXX_XXX"
                                })
                                if verbose:
                                    output_lines.append(f"  ❌ Formato {colonna} non valido, atteso: {prefisso_atteso}_XXXX_XXX (riga {index + 2})")
                
                else:
                    # Controllo normale per tutte le altre colonne
                    pattern = re.compile(f"^{prefisso_atteso}_\\d{{4}}_\\d{{3}}$")
                    errori_formato = []
                    for index, valore in valori_colonna.items():
                        if not pattern.match(valore):
                            errori_formato.append({
                                "riga": index + 2,  # +2 per header e base 0
                                "valore": valore,
                                "errore": f"Formato {colonna} non valido, atteso: {prefisso_atteso}_XXXX_XXX"
                            })
                    
                    if errori_formato:
                        num_errori = len(errori_formato)
                        errori_da_mostrare = errori_formato[:5]
                        errore_msg = f"Colonna '{colonna}': {num_errori} ID con formato non valido"
                        
                        if errori_da_mostrare:
                            righe_str = ", ".join([f"riga {e['riga']}: '{e['valore']}'" for e in errori_da_mostrare])
                            if num_errori > 5:
                                righe_str += f" e altri {num_errori - 5}"
                            errore_msg += f" (es. {righe_str})"
                        
                        risultato_file['errori'].append(errore_msg)
                        if verbose:
                            output_lines.append(f"  ℹ️❌ {errore_msg}")
                
                # Controllo unicità e memorizzazione ID per la colonna principale
                if colonna == colonna_principale:
                    # Controllo unicità
                    duplicati = valori_colonna[valori_colonna.duplicated()].unique()
                    if len(duplicati) > 0:
                        duplicati_str = ", ".join([f"'{d}'" for d in duplicati[:5]])
                        if len(duplicati) > 5:
                            duplicati_str += f" e altri {len(duplicati) - 5}"
                        msg_duplicati = f"Colonna '{colonna}': {len(duplicati)} ID duplicati ({duplicati_str})"
                        risultato_file['errori'].append(msg_duplicati)
                        if verbose:
                            output_lines.append(f"  ❌ {msg_duplicati}")
                    
                    # Memorizza gli ID della colonna principale per il gruppo
                    if risultato_file['gruppo']:
                        id_per_gruppo[risultato_file['gruppo']][nome_file] = set(valori_colonna.unique())
            
            if verbose and not risultato_file['errori']:
                output_lines.append("  ✅ Tutti gli ID sono validi e univoci (dove richiesto)")
            
        except Exception as e:
            errore_msg = f"Errore nell'analisi del file: {str(e)}"
            risultato_file['errori'].append(errore_msg)
            if verbose:
                output_lines.append(f"  ❌ {errore_msg}")
        
        # Aggiorna lo stato del file
        if not risultato_file['errori']:
            risultato_file['valido'] = True
            file_validi += 1
        else:
            file_con_errori += 1
        
        risultati[nome_file] = risultato_file
    
    # Controllo consistenza ID all'interno di ciascun gruppo
    for gruppo, file_ids in id_per_gruppo.items():
        if len(file_ids) < 2:
            continue  # Non possiamo fare confronti con meno di 2 file
            
        # Prendiamo il primo file del gruppo come riferimento
        file_riferimento, id_riferimento = next(iter(file_ids.items()))
        
        for nome_file, id_set in file_ids.items():
            if nome_file == file_riferimento:
                continue
                
            # Trova differenze simmetriche tra i set
            differenze = id_riferimento.symmetric_difference(id_set)
            
            if differenze:
                # Prepara il messaggio di errore
                msg_diff = f"ID nella colonna principale non corrispondono con {file_riferimento} nel gruppo {gruppo}: "
                differenze_list = list(differenze)
                differenze_str = ", ".join([f"'{d}'" for d in differenze_list[:5]])
                if len(differenze_list) > 5:
                    differenze_str += f" e altri {len(differenze_list) - 5}"
                
                msg_diff += f"{len(differenze)} differenze ({differenze_str})"
                
                # Aggiungi l'errore al risultato del file
                risultati[nome_file]['errori'].append(msg_diff)
                risultati[nome_file]['valido'] = False
                
                # Aggiorna i contatori (potrebbe cambiare lo stato da valido a non valido)
                if risultati[nome_file]['valido'] == False and len(risultati[nome_file]['errori']) == 1:
                    file_validi -= 1
                    file_con_errori += 1
                
                if verbose:
                    output_lines.append(f"\n📄 File: {nome_file}")
                    output_lines.append("  " + "-"*50)
                    output_lines.append(f"  ❌ {msg_diff}")
    
    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    
    # Aggiungi informazioni sul controllo consistenza ID per gruppo
    riepilogo_lines.append("-"*60)
    riepilogo_lines.append("CONTROLLO CONSISTENZA ID PER GRUPPO:")
    
    for gruppo in gruppi_file:
        file_gruppo = [f for f in gruppi_file[gruppo] if f in specifiche_id_csv]
        if len(file_gruppo) < 2:
            continue
            
        if gruppo in id_per_gruppo and len(id_per_gruppo[gruppo]) >= 2:
            # Verifica se tutti gli ID corrispondono
            id_corrispondenti = True
            id_riferimento = None
            
            for nome_file, id_set in id_per_gruppo[gruppo].items():
                if id_riferimento is None:
                    id_riferimento = id_set
                elif id_riferimento != id_set:
                    id_corrispondenti = False
                    break
            
            if id_corrispondenti:
                riepilogo_lines.append(f"✅ Gruppo {gruppo}: tutti gli ID corrispondono")
            else:
                riepilogo_lines.append(f"❌ Gruppo {gruppo}: ID non corrispondenti tra i file")
    
    riepilogo_lines.append("="*60)
    
    riepilogo = "\n".join(riepilogo_lines)
    
    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))
    
    return risultati, riepilogo


def valida_campi_booleani_csv(cartella, lista_file, colonne_da_controllare=["active_fault","seismogenic_fault","capable_fault"], verbose=True):
    """
    Verifica che le colonne dei file CSV indicate contengano solo 
    i valori "TRUE", "FALSE" o "nd".
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        lista_file (list): Lista dei nomi dei file CSV da controllare
        verbose (bool): Se True, stampa un report formattato durante l'esecuzione
        
    Returns:
        tuple: (dict con i risultati della validazione, str con il riepilogo)
    """
    risultati = {}
    
    # Contatori per il riepilogo finale
    totale_file = len(lista_file)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0
    
    output_lines = []
    
    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE CAMPI BOOLEANI CSV - {totale_file} file da controllare")
        output_lines.append("="*60)
    
    for nome_file in lista_file:
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'valido': False
        }
        
        if verbose:
            output_lines.append(f"\n📄 File: {nome_file}")
            output_lines.append("  " + "-"*50)
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1
            
            if verbose:
                output_lines.append("  ❌ File non trovato")
            
            continue
        
        try:
            # Leggiamo il file CSV
            df = pd.read_csv(percorso_file, sep=',', encoding='utf-8', on_bad_lines='warn')
           
            if verbose:
                colonne_str = ", ".join([f"'{col}'" for col in colonne_da_controllare])
                output_lines.append(f"  📊 Righe: {len(df)}, Colonne da controllare: {colonne_str}")
            
            # Valori consentiti
            valori_consentiti = ["TRUE", "true", "FALSE", "false", "ND", "nd"]
            
            # Controllo dei valori per ogni colonna
            for colonna in colonne_da_controllare:
                # Convertiamo i valori in stringhe maiuscole per il confronto
                valori_colonna = df[colonna].astype(str).str.upper()
                
                # Troviamo i valori non validi
                mask_non_validi = ~valori_colonna.isin(valori_consentiti)
                num_non_validi = mask_non_validi.sum()
                
                if num_non_validi > 0:
                    # Prendiamo fino a 5 esempi di valori non validi
                    esempi = df.loc[mask_non_validi, colonna].astype(str).unique()[:5]
                    esempi_str = ", ".join([f"'{e}'" for e in esempi])
                    
                    # Prepariamo il messaggio di errore
                    errore_msg = f"Colonna '{colonna}': {num_non_validi} valori non validi"
                    if len(esempi) > 0:
                        errore_msg += f" ({esempi_str})"
                        if len(df.loc[mask_non_validi, colonna].unique()) > 5:
                            errore_msg += " e altri"
                    
                    risultato_file['errori'].append(errore_msg)
                    
                    if verbose:
                        output_lines.append(f"  ❌ {errore_msg}")
                else:
                    if verbose:
                        output_lines.append(f"  ✅ Colonna '{colonna}': tutti i valori sono validi")
            
        except Exception as e:
            errore_msg = f"Errore nell'analisi del file: {str(e)}"
            risultato_file['errori'].append(errore_msg)
            
            if verbose:
                output_lines.append(f"  ❌ {errore_msg}")
        
        # Se non ci sono errori, impostiamo valido a True
        if not risultato_file['errori']:
            risultato_file['valido'] = True
            file_validi += 1
            
            if verbose:
                output_lines.append("  ✅ Tutte le colonne contengono solo valori validi (TRUE, FALSE, nd)")
        else:
            file_con_errori += 1
            
        risultati[nome_file] = risultato_file
    
    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE CAMPI BOOLEANI")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    riepilogo_lines.append("="*60)
    
    riepilogo = "\n".join(riepilogo_lines)
    
    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))
    
    return risultati, riepilogo


def valida_codici_csv(cartella, specifiche_codici, file_domini_codici="code_domain.csv", verbose=True):
    """
    Verifica che i codici presenti nei file CSV siano validi rispetto 
    ai codici definiti nel file di dominio specificato.
    Gestisce sia colonne numeriche (es. color_surface) che non numeriche (es. type_contact).

    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        specifiche_codici (dict): Dizionario con le specifiche per ogni file CSV.
                               Formato: {
                                  'nome_file.csv': {
                                      'colonne_codici': {
                                          'nome_colonna': 'nome_dominio',
                                          ...
                                      }
                                  },
                                  ...
                               }
        file_domini_codici (str): Nome del file CSV che contiene i domini di codici validi.
                             Il file deve avere una colonna per ogni dominio, con i codici validi.
        verbose (bool): Se True, stampa un report formattato durante l'esecuzione

    Returns:
        tuple: (dict con i risultati della validazione, str con il riepilogo)
    """
    import os
    import pandas as pd

    risultati = {}

    # Contatori per il riepilogo finale
    totale_file = len(specifiche_codici)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0

    output_lines = []

    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE CODICI CSV - {totale_file} file da controllare")
        output_lines.append(f"File domini: {file_domini_codici}")
        output_lines.append("="*60)

    # Carica il file dei domini di codici
    percorso_domini_codici = os.path.join(cartella, file_domini_codici)
    if not os.path.exists(percorso_domini_codici):
        if verbose:
            output_lines.append(f"❌ File {file_domini_codici} non trovato nella cartella specificata")
        return {}, f"File {file_domini_codici} non trovato"

    try:
        # Leggiamo il file dei domini di codici
        df_domini_codici = pd.read_csv(percorso_domini_codici, sep=',', encoding='utf-8', on_bad_lines='warn')

        # Creiamo un dizionario dei domini con i codici validi
        domini_codici = {}
        for colonna in df_domini_codici.columns:
            # Gestione colonne numeriche e non numeriche
            if colonna.strip().lower() in ['color_surface', 'color_fault', 'color_unit']:
                # Se la colonna è numerica, converti i valori in numeri interi
                codici_validi = set(df_domini_codici[colonna].dropna().astype(int))
            else:
                # Se la colonna non è numerica, gestisci i valori come stringhe
                codici_validi = set(df_domini_codici[colonna].dropna().astype(str).str.strip().str.lower())
            
            domini_codici[colonna.strip().lower()] = codici_validi

        if verbose:
            output_lines.append(f"✅ Caricati {len(domini_codici)} domini di codici da {file_domini_codici}")
            for domain, codes in domini_codici.items():
                output_lines.append(f"  - {domain}: {len(codes)} codici validi")

    except Exception as e:
        if verbose:
            output_lines.append(f"❌ Errore nel caricamento di {file_domini_codici}: {str(e)}")
        return {}, f"Errore nel caricamento di {file_domini_codici}: {str(e)}"

    # Processiamo ogni file specificato
    for nome_file, specifiche in specifiche_codici.items():
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'valido': False
        }

        if verbose:
            output_lines.append(f"\n📄 File: {nome_file}")
            output_lines.append("  " + "-"*50)

        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1

            if verbose:
                output_lines.append("  ❌ File non trovato")

            continue

        colonne_codici = specifiche.get('colonne_codici', {})

        if not colonne_codici:
            risultato_file['errori'].append("Nessuna colonna di codici specificata")
            risultati[nome_file] = risultato_file
            file_con_errori += 1

            if verbose:
                output_lines.append("  ❌ Nessuna colonna di codici specificata")

            continue

        try:
            # Leggiamo il file CSV
            df = pd.read_csv(percorso_file, sep=',', encoding='utf-8', on_bad_lines='warn')

            # Controlliamo ogni colonna specificata
            for colonna, dominio in colonne_codici.items():
                # Rimuovi spazi e caratteri invisibili dai nomi delle colonne e converti in minuscolo
                colonna_pulita = colonna.strip().lower()
                dominio_pulito = dominio.strip().lower()

                if colonna_pulita not in df.columns:
                    risultato_file['errori'].append(f"Colonna '{colonna}' non trovata")
                    if verbose:
                        output_lines.append(f"  ❌ Colonna '{colonna}' non trovata")
                    continue

                if dominio_pulito not in domini_codici:
                    risultato_file['errori'].append(f"Dominio '{dominio}' non trovato in {file_domini_codici}")
                    if verbose:
                        output_lines.append(f"  ❌ Dominio '{dominio}' non trovato in {file_domini_codici}")
                    continue

                # Otteniamo i codici validi per questo dominio
                codici_validi = domini_codici[dominio_pulito]

                # Gestione colonne numeriche e non numeriche
                if dominio_pulito in ['color_surface', 'color_fault', 'color_unit']:
                    # Se la colonna è numerica, converti i valori in numeri interi
                    try:
                        valori_colonna = df[colonna_pulita].dropna().astype(int)
                    except ValueError as e:
                        risultato_file['errori'].append(f"Errore nella conversione dei valori in numeri per la colonna '{colonna}': {str(e)}")
                        if verbose:
                            output_lines.append(f"  ❌ Errore nella conversione dei valori in numeri per la colonna '{colonna}': {str(e)}")
                        continue
                else:
                    # Se la colonna non è numerica, gestisci i valori come stringhe
                    valori_colonna = df[colonna_pulita].dropna().astype(str).str.strip().str.lower()

                # Troviamo i valori non validi
                mask_non_validi = ~valori_colonna.isin(codici_validi)
                num_non_validi = mask_non_validi.sum()

                if num_non_validi > 0:
                    # Prendiamo fino a 5 esempi di valori non validi
                    esempi = df.loc[mask_non_validi, colonna_pulita].astype(str).unique()[:5]
                    esempi_str = ", ".join([f"'{e}'" for e in esempi])

                    # Prepariamo il messaggio di errore
                    errore_msg = f"Colonna '{colonna}' (dominio '{dominio}'): {num_non_validi} valori non validi"

                    # Aggiungiamo esempi di righe non valide
                    if len(esempi) > 0:
                        righe_non_valide = df.index[mask_non_validi].tolist()[:5]
                        righe_str = ", ".join([str(r+2) for r in righe_non_valide])  # +2 per tenere conto dell'header e dell'indice base 0

                        errore_msg += f" (es. righe: {righe_str}, valori: {esempi_str})"
                        if len(df.loc[mask_non_validi, colonna_pulita].unique()) > 5:
                            errore_msg += " e altri"

                    risultato_file['errori'].append(errore_msg)

                    if verbose:
                        output_lines.append(f"  ❌ {errore_msg}")
                else:
                    if verbose:
                        output_lines.append(f"  ✅ Colonna '{colonna}' (dominio '{dominio}'): tutti i valori sono validi")

        except Exception as e:
            errore_msg = f"Errore nell'analisi del file: {str(e)}"
            risultato_file['errori'].append(errore_msg)

            if verbose:
                output_lines.append(f"  ❌ {errore_msg}")

        # Se non ci sono errori, impostiamo valido a True
        if not risultato_file['errori']:
            risultato_file['valido'] = True
            file_validi += 1

            if verbose:
                output_lines.append("  ✅ Tutte le colonne contengono solo codici validi")
        else:
            file_con_errori += 1

        risultati[nome_file] = risultato_file

    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE CODICI")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    riepilogo_lines.append("="*60)

    riepilogo = "\n".join(riepilogo_lines)

    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))

    return risultati, riepilogo


def valida_campi_numerici_csv(cartella, lista_file, verbose=True):
    """
    Verifica che i campi specificati nei file CSV contengano valori validi (interi, float, stringhe specifiche).
    Segnala anche le righe in cui si trovano gli errori, con numerazione corretta (partendo da 1).
    
    Args:
        cartella (str): Percorso della cartella contenente i file CSV
        lista_file (list): Lista dei nomi dei file CSV da controllare
        verbose (bool): Se True, stampa un report formattato durante l'esecuzione
        
    Returns:
        tuple: (dict con i risultati della validazione, str con il riepilogo)
    """
    risultati = {}
    
    # Contatori per il riepilogo finale
    totale_file = len(lista_file)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0
    
    output_lines = []
    
    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE CAMPI NUMERICI CSV - {totale_file} file da controllare")
        output_lines.append("="*60)
    
    for nome_file in lista_file:
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'valido': False
        }
        
        if verbose:
            output_lines.append(f"\n📄 File: {nome_file}")
            output_lines.append("  " + "-"*50)
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1
            
            if verbose:
                output_lines.append("  ❌ File non trovato")
            
            continue
        
        try:
            # Leggiamo il file CSV
            df = pd.read_csv(percorso_file, sep=',', encoding='utf-8', on_bad_lines='warn')
           
            if verbose:
                output_lines.append(f"  📊 Righe: {len(df)}")
            
            # Definiamo i controlli specifici per ogni file
            if nome_file == 'main_fault_derived_attributes.csv' or nome_file == 'main_horizon_derived_attributes.csv':
                # Controlli per i campi numerici
                campi_numerici = ["mean_dip_azimuth", "mean_dip", "mean_strike"]
                for campo in campi_numerici:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & ~df[campo].apply(lambda x: isinstance(x, int) or (isinstance(x, float) and x.is_integer()))
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere interi o vuoti) ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi (interi o vuoti)")
                
                # Controlli per i campi UOM
                campi_uom = ["mean_dip_azimuth_uom", "mean_dip_uom", "mean_strike_uom"]
                for campo in campi_uom:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & (df[campo].str.upper() != "DEG")
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere 'deg') ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi ('deg')")
            
            elif nome_file == 'main_fault_kinematics_attributes.csv':
                # Controlli per i campi numerici (float o vuoti)
                campi_float = ["net_slip", "hor_throw", "ver_throw", "str_slip", "heave", "dip_slip"]
                for campo in campi_float:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & ~df[campo].apply(lambda x: isinstance(x, float))
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere float o vuoti) ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi (float o vuoti)")
                
                # Controlli per i campi interi (interi o vuoti)
                campi_interi = ["rake", "pitch"]
                for campo in campi_interi:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & ~df[campo].apply(lambda x: isinstance(x, int) or (isinstance(x, float) and x.is_integer()))
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere interi o vuoti) ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi (interi o vuoti)")
                
                # Controlli per i campi UOM
                campi_uom = ["net_slip_uom", "hor_throw_uom", "ver_throw_uom", "str_slip_uom", "heave_uom", "dip_slip_uom"]
                for campo in campi_uom:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & (df[campo].str.upper() != "MM")
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere 'mm') ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi ('mm')")
                
                # Controlli per i campi UOM (deg)
                campi_uom_deg = ["rake_uom", "pitch_uom"]
                for campo in campi_uom_deg:
                    if campo in df.columns:
                        mask_non_validi = ~df[campo].isna() & (df[campo].str.upper() != "DEG")
                        num_non_validi = mask_non_validi.sum()
                        if num_non_validi > 0:
                            righe_con_errori = df.loc[mask_non_validi].index.tolist()
                            righe_con_errori = [r + 2 for r in righe_con_errori]  # Aggiungiamo 1 per la numerazione corretta
                            esempi = df.loc[mask_non_validi, campo].unique()[:5]
                            esempi_str = ", ".join([f"'{e}'" for e in esempi])
                            errore_msg = f"Campo '{campo}': {num_non_validi} valori non validi (devono essere 'deg') ({esempi_str})"
                            errore_msg += f" - Righe con errori: {righe_con_errori[:10]}"  # Mostra fino a 10 righe con errori
                            risultato_file['errori'].append(errore_msg)
                            if verbose:
                                output_lines.append(f"  ❌ {errore_msg}")
                        else:
                            if verbose:
                                output_lines.append(f"  ✅ Campo '{campo}': tutti i valori sono validi ('deg')")
        
        except Exception as e:
            errore_msg = f"Errore nell'analisi del file: {str(e)}"
            risultato_file['errori'].append(errore_msg)
            
            if verbose:
                output_lines.append(f"  ❌ {errore_msg}")
        
        # Se non ci sono errori, impostiamo valido a True
        if not risultato_file['errori']:
            risultato_file['valido'] = True
            file_validi += 1
            
            if verbose:
                output_lines.append("  ✅ Tutti i campi contengono valori validi")
        else:
            file_con_errori += 1
            
        risultati[nome_file] = risultato_file
    
    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE CAMPI NUMERICI")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    riepilogo_lines.append("="*60)
    
    riepilogo = "\n".join(riepilogo_lines)
    
    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))
    
    return risultati, riepilogo
