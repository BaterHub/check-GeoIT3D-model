import json
from datetime import datetime
import os
from typing import Dict, Any

def check_descriptor_structure(cartella: str, required_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida il file descriptor.json con report avanzato senza mostrare la struttura completa.
    
    Args:
        cartella: Percorso della cartella contenente descriptor.json
        required_fields: Dizionario {campo: tipo_atteso}
    
    Returns:
        Dizionario con: {
            'valid': bool,
            'errors': lista_errori,
            'warnings': lista_warning,
            'summary': report_sintetico
        }
    """
    file_path = os.path.join(cartella, "descriptor.json")
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'summary': ""
    }

    # Lettura file
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            try:
                data = json.loads(raw_data.decode('utf-8'))
            except UnicodeDecodeError:
                data = json.loads(raw_data.decode('latin-1'))
    except Exception as e:
        return _handle_error(result, f"❌ Errore lettura file: {str(e)}")

    # Analisi campi
    fields_present = set(data.keys())
    fields_required = set(required_fields.keys())
    
    # Campi mancanti
    missing_fields = fields_required - fields_present
    for field in missing_fields:
        _handle_error(result, f"❌ Campo obbligatorio mancante: '{field}'")

    # Campi extra
    extra_fields = fields_present - fields_required
    for field in extra_fields:
        result['warnings'].append(f"⚠️ Campo non previsto: '{field}'")

    # Verifica tipi
    for field, expected_type in required_fields.items():
        if field not in data:
            continue
            
        value = data[field]
        
        if expected_type == datetime:
            if not isinstance(value, str):
                _handle_error(result, f"❌ '{field}': deve essere stringa (ISO date)")
            else:
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    _handle_error(result, f"❌ '{field}': formato data non valido")
        elif expected_type == type(None):
            if value is not None:
                _handle_error(result, f"❌ '{field}': deve essere null")
        elif not isinstance(value, expected_type):
            _handle_error(result, 
                f"❌ Tipo errato in '{field}': "
                f"atteso {expected_type.__name__}, "
                f"trovato {type(value).__name__}"
            )

    # Generazione report sintetico
    result['summary'] = _generate_summary_report(result)
    return result

def _handle_error(result: Dict[str, Any], message: str) -> Dict[str, Any]:
    result['valid'] = False
    result['errors'].append(message)
    return result

def _generate_summary_report(result: Dict[str, Any]) -> str:
    """Genera un report sintetico senza struttura completa"""
    report = [
        "="*50,
        " VALIDAZIONE DESCRIPTOR.JSON ".center(50, "="),
        "="*50,
        f"\nStato: {'✅ VALIDO' if result['valid'] else '❌ INVALIDO'}\n"
    ]
    
    if result['errors']:
        report.append("\nERRORI RISCONTRATI:")
        report.extend([f"- {e}" for e in result['errors']])
    
    if result['warnings']:
        report.append("\nAVVERTENZE:")
        report.extend([f"- {w}" for w in result['warnings']])
    
    report.append("\n" + "="*50)
    report.append(f"RIEPILOGO: {len(result['errors'])} errori, {len(result['warnings'])} avvertenze")
    report.append("="*50)
    
    return "\n".join(report)
