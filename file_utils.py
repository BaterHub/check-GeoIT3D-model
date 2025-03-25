# file_utils.py
# Contiene funzioni per verificare la presenza di file in una cartella

import os
import difflib

def verifica_file_presenti(cartella, file_necessari, soglia_similarita=0.95):
    """
    Verifica la presenza di file necessari in una cartella, segnala file simili e file aggiuntivi.
    
    Args:
        cartella (str): Percorso della cartella da controllare
        file_necessari (list): Lista dei nomi dei file da verificare
        soglia_similarita (float): Soglia per considerare due nomi di file simili (tra 0 e 1)
        
    Returns:
        tuple: (file_presenti, file_mancanti, file_simili, file_aggiuntivi)
    """
    # Verifica che la cartella esista
    if not os.path.exists(cartella):
        return [], file_necessari, {}, []
    
    # Ottiene la lista dei file nella cartella
    file_nella_cartella = os.listdir(cartella)
    
    # Verifica quali file sono presenti
    file_presenti = [file for file in file_necessari if file in file_nella_cartella]
    file_mancanti = [file for file in file_necessari if file not in file_nella_cartella]
    
    # Identifica file aggiuntivi (file presenti nella cartella ma non nella lista dei necessari)
    file_aggiuntivi = [file for file in file_nella_cartella if file not in file_necessari]
    
    # Cerca file con nomi simili per ogni file mancante
    file_simili = {}
    for file_mancante in file_mancanti:
        # Usa difflib per trovare sequenze simili
        matches = difflib.get_close_matches(
            file_mancante, 
            file_nella_cartella, 
            n=3,  # massimo 3 suggerimenti per file mancante
            cutoff=soglia_similarita
        )
        
        if matches:
            file_simili[file_mancante] = matches
    
    return file_presenti, file_mancanti, file_simili, file_aggiuntivi