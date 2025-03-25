import re
import os
import numpy as np
import pandas as pd


def parse_gocad_file(filepath):
    """
    Funzione per analizzare i file GOCAD .ts, estraendo header, vertici e connettività.
    
    Args:
        filepath (str): Percorso completo del file GOCAD .ts da analizzare
        
    Returns:
        list: Lista di dizionari, uno per ogni oggetto nel file, con struttura:
            {
                'name': Nome dell'oggetto,
                'header': Informazioni di intestazione,
                'vertices': Array numpy di coordinate dei vertici (x, y, z),
                'triangles/tetrahedra': Array numpy di indici di connettività,
                'properties': Dizionario di proprietà aggiuntive (se presenti)
            }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Il file {filepath} non è stato trovato")
    
    objects = []
    current_object = None
    vertices = []
    triangles = []
    tetrahedra = []
    header_lines = []
    properties = {}
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Controllo inizio oggetto
        if line.startswith('GOCAD '):
            # Se ho già un oggetto, lo salvo prima di iniziare il nuovo
            if current_object is not None:
                objects.append({
                    'name': current_object,
                    'header': header_lines,
                    'vertices': np.array(vertices) if vertices else np.array([]),
                    'triangles': np.array(triangles) if triangles else np.array([]),
                    'tetrahedra': np.array(tetrahedra) if tetrahedra else np.array([]),
                    'properties': properties
                })
            
            # Inizializzo nuovo oggetto
            current_object = None
            vertices = []
            triangles = []
            tetrahedra = []
            header_lines = [line]
            properties = {}
        
        # Estrazione nome dell'oggetto
        elif line.startswith('name:'):
            current_object = line.split('name:')[1].strip()
            header_lines.append(line)
        
        # Parsing vertici
        elif line.startswith(('VRTX', 'PVRTX')):  # Modifica qui
            parts = line.split()
            if len(parts) >= 5:  # VRTX id x y z [optional properties]
                try:
                    vrtx_id = int(parts[1])  # Assicurati che sia un intero
                    x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                    vertices.append((vrtx_id, x, y, z))
                    
                    # Proprietà opzionali dei vertici
                    if len(parts) > 5:
                        prop_values = [float(p) for p in parts[5:]]
                        if 'vertex_properties' not in properties:
                            properties['vertex_properties'] = {}
                        properties['vertex_properties'][vrtx_id] = prop_values
                except ValueError as e:
                    header_lines.append(f"WARNING: Errore nel parsing del vertice: {line} - {e}")
        
        # Parsing triangoli (TRGL)
        elif line.startswith('TRGL'):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    v1, v2, v3 = int(parts[1]), int(parts[2]), int(parts[3])
                    triangles.append((v1, v2, v3))
                except ValueError:
                    header_lines.append(f"WARNING: Errore nel parsing del triangolo: {line}")
        
        # Parsing tetraedri (TETRA) - se presenti
        elif line.startswith('TETRA'):
            parts = line.split()
            if len(parts) >= 5:
                try:
                    v1, v2, v3, v4 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    tetrahedra.append((v1, v2, v3, v4))
                except ValueError:
                    header_lines.append(f"WARNING: Errore nel parsing del tetraedro: {line}")
        
        # Salvataggio righe di header
        elif line.startswith(('HEADER', 'GEOLOGICAL', 'STRATIGRAPHIC', 'PROPERTY', 'SOLID', '*')):
            header_lines.append(line)
            
            # Estrazione di proprietà specifiche
            if line.startswith('PROPERTY'):
                prop_match = re.match(r'PROPERTY\s+(\S+)', line)
                if prop_match:
                    prop_name = prop_match.group(1)
                    if 'property_names' not in properties:
                        properties['property_names'] = []
                    properties['property_names'].append(prop_name)
        
        elif line.startswith('END'):
            header_lines.append(line)
        
        i += 1
    
    # Aggiungo l'ultimo oggetto
    if current_object is not None:
        objects.append({
            'name': current_object,
            'header': header_lines,
            'vertices': np.array(vertices) if vertices else np.array([]),
            'triangles': np.array(triangles) if triangles else np.array([]),
            'tetrahedra': np.array(tetrahedra) if tetrahedra else np.array([]),
            'properties': properties
        })
    
    return objects



def validate_gocad_geometry(objects):
    """
    Funzione per verificare la validità delle geometrie GOCAD
    
    Args:
        objects (list): Lista di oggetti GOCAD come restituiti da parse_gocad_file
        
    Returns:
        dict: Dizionario con i risultati della validazione per ogni oggetto
    """
    validation_results = {}
    
    for obj in objects:
        obj_name = obj['name']
        validation_results[obj_name] = {
            'valid': True,
            'issues': []
        }
        
        # Controllo 1: Verifica che ci siano vertici
        if len(obj['vertices']) == 0:
            validation_results[obj_name]['valid'] = False
            validation_results[obj_name]['issues'].append("Nessun vertice definito")
        
        # Controllo 2: Verifica triangoli o tetraedri
        if len(obj['triangles']) == 0 and len(obj['tetrahedra']) == 0:
            validation_results[obj_name]['valid'] = False
            validation_results[obj_name]['issues'].append("Nessun triangolo o tetraedro definito")
        
        # Estrai gli ID dei vertici esistenti
        vertex_ids = {v[0] for v in obj['vertices']}  # Usa gli ID originali dal file
        
        # Controllo 3: Verifica riferimenti a vertici validi nei triangoli
        if len(obj['triangles']) > 0:
            for i, (v1, v2, v3) in enumerate(obj['triangles']):
                if v1 not in vertex_ids or v2 not in vertex_ids or v3 not in vertex_ids:
                    validation_results[obj_name]['valid'] = False
                    validation_results[obj_name]['issues'].append(
                        f"Triangolo {i} riferisce a vertici non esistenti: ({v1}, {v2}, {v3}) - Vertici disponibili: {len(vertex_ids)}"
                    )
        
        # Controllo 4: Verifica riferimenti a vertici validi nei tetraedri
        if len(obj['tetrahedra']) > 0:
            for i, (v1, v2, v3, v4) in enumerate(obj['tetrahedra']):
                if v1 not in vertex_ids or v2 not in vertex_ids or v3 not in vertex_ids or v4 not in vertex_ids:
                    validation_results[obj_name]['valid'] = False
                    validation_results[obj_name]['issues'].append(
                        f"Tetraedro {i} riferisce a vertici non esistenti: ({v1}, {v2}, {v3}, {v4})"
                    )
        
        # Controllo 5: Verifica che i triangoli abbiano vertici distinti
        for i, (v1, v2, v3) in enumerate(obj['triangles']):
            if v1 == v2 or v1 == v3 or v2 == v3:
                validation_results[obj_name]['valid'] = False
                validation_results[obj_name]['issues'].append(
                    f"Triangolo {i} ha vertici duplicati: ({v1}, {v2}, {v3})"
                )
        
        # Controllo 6: Verifica che i tetraedri abbiano vertici distinti
        for i, (v1, v2, v3, v4) in enumerate(obj['tetrahedra']):
            if v1 == v2 or v1 == v3 or v1 == v4 or v2 == v3 or v2 == v4 or v3 == v4:
                validation_results[obj_name]['valid'] = False
                validation_results[obj_name]['issues'].append(
                    f"Tetraedro {i} ha vertici duplicati: ({v1}, {v2}, {v3}, {v4})"
                )
        
        # Controllo 7: Verifica che ci siano almeno 4 valori di quota diversi
        heights = obj['vertices'][:, 2]  # Estrai le quote (z) dai vertici
        unique_heights = set(heights)  # Ottieni i valori di quota unici
        
        if len(unique_heights) < 4:
            validation_results[obj_name]['valid'] = False
            validation_results[obj_name]['issues'].append("WARNING la geometria potrebbe non essere valida - ha meno di 4 valori di quota differenti")
    
    return validation_results



def validate_gocad_keywords(filepath, valid_header_kw, valid_coord_kw, valid_conn_kw, special_keywords=None):
    """
    Verifica che le keywords nelle varie sezioni del file GOCAD siano valide
    con rilevamento preciso delle keywords non riconosciute.
    """
    # Valori di default per special_keywords
    if special_keywords is None:
        special_keywords = {
            '*visible:': {'valid_values': ['true', 'false', '1', '0']},
            '*solid*color:': {'valid_values': 'rgb'},
            '*atoms*color:': {'valid_values': 'rgb'}
        }

    # Caratteri e linee da ignorare
    IGNORE_CHARS = ['{', '}', '#', '//']
    IGNORE_LINES = ['END', 'PROPERTIES', 'ESIZES']

    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'invalid_keywords': [],
        'line_numbers': {}
    }

    current_section = None
    line_number = 0

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line_number += 1
                stripped_line = line.strip()

                # Ignora linee vuote, commenti o caratteri speciali
                if (not stripped_line or 
                    any(stripped_line.startswith(c) for c in IGNORE_CHARS) or
                    stripped_line in IGNORE_LINES):
                    continue

                # Controlla se è una special keyword
                is_special = False
                for skw in special_keywords.keys():
                    if stripped_line.startswith(skw):
                        is_special = True
                        break

                if is_special:
                    continue

                # Determina la sezione corrente
                if stripped_line.startswith('GOCAD'):
                    current_section = 'header'
                elif any(stripped_line.startswith(kw) for kw in valid_coord_kw):
                    current_section = 'coordinates'
                elif any(stripped_line.startswith(kw) for kw in valid_conn_kw):
                    current_section = 'connectivity'
                elif stripped_line.startswith('END'):
                    current_section = None

                # Estrai la prima parola (keyword)
                first_word = stripped_line.split()[0] if stripped_line else ''

                # Validazione in base alla sezione corrente
                if current_section == 'header':
                    if (not any(stripped_line.startswith(kw) for kw in valid_header_kw) and first_word):
                        validation_result['valid'] = False
                        err_msg = f"Keyword non valida nell'header: '{first_word}' (linea {line_number})"
                        if err_msg not in validation_result['errors']:
                            validation_result['errors'].append(err_msg)
                            validation_result['invalid_keywords'].append(first_word)
                            validation_result['line_numbers'][f'error_{line_number}'] = line_number

                elif current_section == 'coordinates':
                    if (not any(stripped_line.startswith(kw) for kw in valid_coord_kw) and first_word):
                        validation_result['valid'] = False
                        err_msg = f"Keyword non valida in coordinate: '{first_word}' (linea {line_number})"
                        if err_msg not in validation_result['errors']:
                            validation_result['errors'].append(err_msg)
                            validation_result['invalid_keywords'].append(first_word)
                            validation_result['line_numbers'][f'error_{line_number}'] = line_number

                elif current_section == 'connectivity':
                    if (not any(stripped_line.startswith(kw) for kw in valid_conn_kw) and first_word):
                        validation_result['valid'] = False
                        err_msg = f"Keyword non valida in connettività: '{first_word}' (linea {line_number})"
                        if err_msg not in validation_result['errors']:
                            validation_result['errors'].append(err_msg)
                            validation_result['invalid_keywords'].append(first_word)
                            validation_result['line_numbers'][f'error_{line_number}'] = line_number

                # Rileva keywords sconosciute in qualsiasi sezione
                if (first_word and 
                    not any(stripped_line.startswith(kw) for kw in valid_header_kw + valid_coord_kw + valid_conn_kw + list(special_keywords.keys())) and
                    not stripped_line.startswith(('*', 'PROPERTY', 'SOLID')) and
                    first_word not in validation_result['invalid_keywords']):
                    
                    validation_result['valid'] = False
                    err_msg = f"Keyword sconosciuta: '{first_word}' (linea {line_number})"
                    validation_result['errors'].append(err_msg)
                    validation_result['invalid_keywords'].append(first_word)
                    validation_result['line_numbers'][f'error_{line_number}'] = line_number

    except Exception as e:
        validation_result['valid'] = False
        validation_result['errors'].append(f"Errore durante la lettura del file: {str(e)}")

    return validation_result



def analyze_gocad_files(cartella, filenames, valid_header_kw=None, valid_coord_kw=None, valid_conn_kw=None, special_keywords=None):
    """
    Analizza un elenco di file GOCAD in una specifica cartella
    
    Args:
        cartella (str): Percorso della cartella contenente i file
        filenames (list): Lista dei nomi dei file GOCAD da analizzare
        valid_header_kw (list, optional): Keywords valide per l'header
        valid_coord_kw (list, optional): Keywords valide per le coordinate
        valid_conn_kw (list, optional): Keywords valide per la connettività
        special_keywords (dict, optional): Special keywords e regole di validazione
        
    Returns:
        dict: Risultati dell'analisi
    """
    # Valori di default per le keywords
    if valid_header_kw is None:
        valid_header_kw = ['GOCAD', 'TSurf', 'HEADER', 'name:', 'NAME', 'AXIS_NAME', 
                         'AXIS_UNIT', 'ZPOSITIVE', 'GOCAD_ORIGINAL_COORDINATE_SYSTEM', 
                         'END_ORIGINAL_COORDINATE_SYSTEM']
    if valid_coord_kw is None:
        valid_coord_kw = ['TFACE', 'TSOLID', 'VRTX', 'PVRTX']
    if valid_conn_kw is None:
        valid_conn_kw = ['TRGL', 'TETRA']
    
    results = {}
    
    for filename in filenames:
        filepath = os.path.join(cartella, filename)
        
        try:
            print(f"\n_____________________")
            print(f"ANALISI FILE GOCAD")
            print(f"---------------------")
            print(f"Analisi del file: {filepath}")
            
            # Parsing del file
            objects = parse_gocad_file(filepath)
            
            # Validazione delle geometrie
            validation = validate_gocad_geometry(objects)
            
            # Validazione delle keywords
            kw_validation = validate_gocad_keywords(
                filepath=filepath,
                valid_header_kw=valid_header_kw,
                valid_coord_kw=valid_coord_kw,
                valid_conn_kw=valid_conn_kw,
                special_keywords=special_keywords
            )
            
            # Statistiche
            stats = {
                'total_objects': len(objects),
                'valid_objects': sum(1 for obj_name, result in validation.items() if result['valid']),
                'invalid_objects': sum(1 for obj_name, result in validation.items() if not result['valid']),
                'kw_validation': kw_validation,
                'objects': []
            }
            
            for obj in objects:
                obj_name = obj['name']
                obj_stats = {
                    'name': obj_name,
                    'vertices_count': len(obj['vertices']),
                    'triangles_count': len(obj['triangles']),
                    'tetrahedra_count': len(obj['tetrahedra']),
                    'validation': validation.get(obj_name, {'valid': False, 'issues': ["Oggetto non validato"]})
                }
                stats['objects'].append(obj_stats)
            
            results[filename] = {
                'stats': stats,
                'objects': objects
            }
            
        except Exception as e:
            results[filename] = {
                'error': str(e),
                'stats': {
                    'total_objects': 0,
                    'valid_objects': 0,
                    'invalid_objects': 0,
                    'objects': []
                },
                'objects': []
            }
            print(f"Errore durante l'analisi del file {filename}: {str(e)}")
    
    return results



def print_gocad_summary(analysis_results, cartella):
    """
    Stampa un report completo dei risultati dell'analisi con riferimenti alle linee
    
    Args:
        analysis_results (dict): Risultati dell'analisi come restituiti da analyze_gocad_files
        cartella (str): Percorso della cartella contenente i file
    """
    print("\n" + "="*80)
    print("SOMMARIO ANALISI FILE GOCAD".center(80))
    print("="*80)
    
    # Intestazione tabella principale
    print("\n{:<20} {:<10} {:<10} {:<12} {:<15} {:<15}".format(
        'File', 'Oggetti', 'Validi', 'Non validi', 'Keywords OK', 'Keywords non valide'))
    print("-"*80)
    
    total_objects = 0
    total_valid = 0
    total_invalid = 0
    total_kw_errors = 0
    
    for filename, result in analysis_results.items():
        if 'error' in result:
            print("{:<20} {:<10}".format(filename, f"ERRORE: {result['error']}"))
            continue
        
        stats = result['stats']
        total_objects += stats['total_objects']
        total_valid += stats['valid_objects']
        total_invalid += stats['invalid_objects']
        
        kw_status = "SI" if stats['kw_validation']['valid'] else "NO"
        invalid_kw_count = len(stats['kw_validation'].get('invalid_keywords', []))
        total_kw_errors += invalid_kw_count
        
        invalid_kw_display = str(invalid_kw_count) + " errori"
        if invalid_kw_count > 0:
            invalid_kw_display += f" ({', '.join(stats['kw_validation']['invalid_keywords'][:3])}"
            if invalid_kw_count > 3:
                invalid_kw_display += ", ..."
        
        print("{:<20} {:<10} {:<10} {:<12} {:<15} {:<15}".format(
            filename,
            stats['total_objects'],
            stats['valid_objects'],
            stats['invalid_objects'],
            kw_status,
            invalid_kw_display if invalid_kw_count > 0 else '-'
        ))
    
    # Footer tabella principale
    print("-"*80)
    print("{:<20} {:<10} {:<10} {:<12} {:<15} {:<15}".format(
        'TOTALE',
        total_objects,
        total_valid,
        total_invalid,
        '',
        f"{total_kw_errors} errori" if total_kw_errors > 0 else '-'
    ))
    
    # Dettaglio errori
    print("\n" + "="*80)
    print("DETTAGLIO ERRORI".center(80))
    print("="*80)
    
    issues_found = False
    
    for filename, result in analysis_results.items():
        if 'error' in result:
            continue
            
        file_issues = False
        
        # Problemi di validazione delle keywords
        if not result['stats']['kw_validation']['valid']:
            issues_found = True
            file_issues = True
            print(f"\n[KEYWORDS] File: {filename}")
            
            # Stampa errori con numeri di linea
            for error in result['stats']['kw_validation']['errors']:
                print(f"  - ERRORE: {error}")
            
            # Stampa warnings
            for warning in result['stats']['kw_validation']['warnings']:
                print(f"  - ATTENZIONE: {warning}")
            
            # Stampa keywords non valide
            if 'invalid_keywords' in result['stats']['kw_validation']:
                invalid_kws = result['stats']['kw_validation']['invalid_keywords']
                if invalid_kws:
                    print(f"  - KEYWORDS NON VALIDE TROVATE: {', '.join(invalid_kws)}")
        
        # Problemi di validazione delle geometrie
        if any(not obj_stats['validation']['valid'] for obj_stats in result['stats']['objects']):
            issues_found = True
            file_issues = True
            line_map = create_line_map(os.path.join(cartella, filename))
            
            print(f"\n[GEOMETRIA] File: {filename}")
            for obj_stats in result['stats']['objects']:
                validation = obj_stats['validation']
                if not validation['valid']:
                    obj_name = obj_stats['name']
                    print(f"  - Oggetto: {obj_name}")
                    
                    for issue in validation['issues']:
                        line_number = None
                        if "Triangolo" in issue:
                            coords = extract_coords_from_issue(issue)
                            obj_start_line = find_object_line(line_map, obj_name)
                            line_number = find_element_line(line_map, "TRGL", coords, obj_start_line)
                        elif "Tetraedro" in issue:
                            coords = extract_coords_from_issue(issue)
                            obj_start_line = find_object_line(line_map, obj_name)
                            line_number = find_element_line(line_map, "TETRA", coords, obj_start_line)
                        
                        if line_number:
                            print(f"    • {issue} (linea {line_number})")
                        else:
                            print(f"    • {issue}")
        
        if not file_issues:
            print(f"\nFile: {filename} - Nessun problema rilevato")
    
    if not issues_found:
        print("\nNessun problema rilevato in nessun file.")
    
    print("\n" + "="*80)
    print("FINE REPORT".center(80))
    print("="*80)



def create_line_map(filepath):
    """
    Crea una mappa tra contenuto delle linee e numeri di linea
    
    Args:
        filepath (str): Percorso completo del file
        
    Returns:
        dict: Mappa {numero_linea: contenuto_linea}
    """
    line_map = {}
    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):  # Inizia conteggio da 1
            line_map[i] = line.strip()
    return line_map

def find_object_line(line_map, obj_name):
    """
    Trova il numero di linea dell'inizio dell'oggetto
    
    Args:
        line_map (dict): Mappa {numero_linea: contenuto_linea}
        obj_name (str): Nome dell'oggetto da trovare
        
    Returns:
        int: Numero di linea o None se non trovato
    """
    for line_num, content in line_map.items():
        if content.startswith(f"name:") and obj_name in content:
            return line_num
    return None

def extract_index_from_issue(issue):
    """
    Estrae l'indice dell'elemento problematico dal messaggio di errore
    
    Args:
        issue (str): Messaggio di errore
        
    Returns:
        int: Indice dell'elemento o None
    """
    import re
    match = re.search(r'(Triangolo|Tetraedro) (\d+)', issue)
    if match:
        return int(match.group(2))
    return None

def extract_coords_from_issue(issue):
    """
    Estrae le coordinate dell'elemento problematico dal messaggio di errore
    
    Args:
        issue (str): Messaggio di errore
        
    Returns:
        tuple: Tuple di coordinate
    """
    import re
    match = re.search(r'\(([^)]+)\)', issue)
    if match:
        coords_str = match.group(1)
        return tuple(int(x.strip()) for x in coords_str.split(','))
    return None

def find_element_line(line_map, element_type, coords, start_line=1):
    """
    Trova il numero di linea di un elemento specifico
    
    Args:
        line_map (dict): Mappa {numero_linea: contenuto_linea}
        element_type (str): Tipo di elemento (TRGL, TETRA, ecc.)
        coords (tuple): Coordinate dell'elemento
        start_line (int): Linea da cui iniziare la ricerca
        
    Returns:
        int: Numero di linea o None se non trovato
    """
    coord_strs = [str(c) for c in coords]
    
    for line_num in range(start_line, max(line_map.keys()) + 1):
        if line_num in line_map:
            content = line_map[line_num]
            if content.startswith(element_type):
                parts = content.split()
                if len(parts) >= len(coords) + 1:  # +1 per il prefisso (TRGL/TETRA)
                    element_coords = parts[1:len(coords)+1]
                    if all(ec == cc for ec, cc in zip(element_coords, coord_strs)):
                        return line_num
    return None


def valida_gocad_e_confronta_csv(cartella, specifiche_gocad, risultati_csv, verbose=True):
    risultati = {}
    
    # Contatori per il riepilogo finale
    totale_file = len(specifiche_gocad)
    file_validi = 0
    file_con_errori = 0
    file_non_trovati = 0
    
    output_lines = []
    
    if verbose:
        output_lines.append("\n" + "="*60)
        output_lines.append(f"VALIDAZIONE FILE GOCAD - {len(specifiche_gocad)} file da controllare")
        output_lines.append("="*60)
    
    # Estrai gli ID dai file CSV principali per il confronto
    id_csv_principali = {}
    for nome_gocad, specifiche in specifiche_gocad.items():
        csv_corrispondente = specifiche['csv_corrispondente']
        if csv_corrispondente in risultati_csv and risultati_csv[csv_corrispondente]['esiste']:
            try:
                percorso_csv = os.path.join(cartella, csv_corrispondente)
                df_csv = pd.read_csv(percorso_csv)
                
                # Leggi gli ID dalla prima colonna del CSV
                id_csv_principali[nome_gocad] = set(df_csv.iloc[:, 0].astype(str).unique())
                
            except Exception as e:
                id_csv_principali[nome_gocad] = None
                if verbose:
                    output_lines.append(f"  ⚠️ Impossibile leggere ID da {csv_corrispondente}: {str(e)}")
        else:
            id_csv_principali[nome_gocad] = None
    
    for nome_file, specifiche in specifiche_gocad.items():
        percorso_file = os.path.join(cartella, nome_file)
        risultato_file = {
            'esiste': os.path.exists(percorso_file),
            'errori': [],
            'warning': [],
            'valido': False,
            'id_trovati': set(),
            'csv_corrispondente': specifiche['csv_corrispondente']
        }
        
        prefisso_atteso = specifiche['prefisso_atteso']
        pattern = re.compile(f"^{prefisso_atteso}_\\d{{4}}_\\d{{3}}$")  # Regex per il formato atteso
        
        if verbose:
            output_lines.append(f"\n📄 File GOCAD: {nome_file}")
            output_lines.append(f"  CSV corrispondente: {specifiche['csv_corrispondente']}")
            output_lines.append("  " + "-"*50)
        
        if not risultato_file['esiste']:
            risultato_file['errori'].append("File non trovato")
            risultati[nome_file] = risultato_file
            file_non_trovati += 1
            
            if verbose:
                output_lines.append("  ❌ File non trovato")
            
            continue
        
        try:
            with open(percorso_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            id_trovati = set()
            
            for line in lines:
                # Cerca la stringa "name:" e estrai l'ID
                if "name:" in line:
                    nome_oggetto = line.split("name:")[1].strip()  # Estrai l'ID dopo "name:"
                    
                    # Verifica il formato dell'ID
                    if not pattern.match(nome_oggetto):
                        risultato_file['errori'].append({
                            "valore": nome_oggetto,
                            "errore": f"Formato ID non valido, atteso: {prefisso_atteso}_XXXX_XXX"
                        })
                        if verbose:
                            output_lines.append(f"  ❌ Formato ID non valido: '{nome_oggetto}', atteso: {prefisso_atteso}_XXXX_XXX")
                    else:
                        id_trovati.add(nome_oggetto)
            
            risultato_file['id_trovati'] = id_trovati
            
            # Controlla unicità degli ID trovati
            if len(id_trovati) != len(set(id_trovati)):
                risultato_file['errori'].append("ID non univoci trovati nel file GOCAD")
                if verbose:
                    output_lines.append("  ❌ ID non univoci trovati nel file GOCAD")
            
            # Controlla corrispondenza con il file CSV principale
            if nome_file in id_csv_principali and id_csv_principali[nome_file] is not None:
                id_csv = id_csv_principali[nome_file]
                
                # Differenze tra GOCAD e CSV
                solo_in_gocad = id_trovati - id_csv
                solo_in_csv = id_csv - id_trovati
                
                if solo_in_gocad:
                    msg = f"{len(solo_in_gocad)} ID presenti in GOCAD ma non nel CSV: {', '.join(sorted(solo_in_gocad)[:3])}"
                    if len(solo_in_gocad) > 3:
                        msg += f" e altri {len(solo_in_gocad) - 3}"
                    risultato_file['errori'].append(msg)
                    if verbose:
                        output_lines.append(f"  ❌ {msg}")
                
                if solo_in_csv:
                    msg = f"{len(solo_in_csv)} ID presenti nel CSV ma non in GOCAD: {', '.join(sorted(solo_in_csv)[:3])}"
                    if len(solo_in_csv) > 3:
                        msg += f" e altri {len(solo_in_csv) - 3}"
                    risultato_file['warning'].append(msg)
                    if verbose:
                        output_lines.append(f"  ⚠️ {msg}")
            
            if verbose and not risultato_file['errori']:
                output_lines.append(f"  ✅ Tutti gli ID sono validi (trovati {len(id_trovati)} ID)")
            
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
    
    # Creazione del riepilogo
    riepilogo_lines = []
    riepilogo_lines.append("="*60)
    riepilogo_lines.append("RIEPILOGO VALIDAZIONE GOCAD")
    riepilogo_lines.append("="*60)
    riepilogo_lines.append(f"✅ File validi: {file_validi}/{totale_file}")
    riepilogo_lines.append(f"❌ File con errori: {file_con_errori}/{totale_file}")
    riepilogo_lines.append(f"🔍 File non trovati: {file_non_trovati}/{totale_file}")
    
    # Aggiungi informazioni sul confronto con CSV
    riepilogo_lines.append("-"*60)
    riepilogo_lines.append("CONFRONTO CON FILE CSV PRINCIPALI:")
    
    for nome_file in specifiche_gocad:
        if nome_file in risultati and risultati[nome_file]['esiste']:
            csv_corrispondente = specifiche_gocad[nome_file]['csv_corrispondente']
            if csv_corrispondente in risultati_csv and risultati_csv[csv_corrispondente]['esiste']:
                id_gocad = risultati[nome_file]['id_trovati']
                id_csv = id_csv_principali.get(nome_file, set())
                
                if id_csv is not None:
                    corrispondenti = id_gocad == id_csv
                    riepilogo_lines.append(
                        f"{'✅' if corrispondenti else '❌'} {nome_file} vs {csv_corrispondente}: "
                        f"{'ID corrispondenti' if corrispondenti else 'ID non corrispondenti'}"
                    )
                else:
                    riepilogo_lines.append(f"⚠️ {nome_file}: impossibile verificare corrispondenza con {csv_corrispondente}")
            else:
                riepilogo_lines.append(f"⚠️ {nome_file}: file CSV {csv_corrispondente} non trovato o non valido")
    
    riepilogo_lines.append("="*60)
    
    riepilogo = "\n".join(riepilogo_lines)
    
    # Aggiungo il riepilogo all'output
    if verbose:
        output_lines.append("\n" + riepilogo)
        # Stampo l'output
        print("\n".join(output_lines))
    
    return risultati, riepilogo

