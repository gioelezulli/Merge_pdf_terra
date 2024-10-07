import tomllib  # Libreria per leggere il file config.toml
import os
from fillpdf import fillpdfs
import json  # Per scrivere su file JSON

# Funzione per leggere i percorsi dal file config.toml
def read_config():
    # Definisce il percorso del file di configurazione
    config_path = os.path.join(os.path.dirname(__file__), 'Config', 'config.toml')

    # Legge il file config.toml usando tomllib
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    return config

# Funzione per trovare il primo file PDF in una directory
def find_pdf_in_directory(directory):
    for file in os.listdir(directory):
        if file.endswith(".pdf"):
            return os.path.join(directory, file)
    raise FileNotFoundError(f"Nessun file PDF trovato nella directory: {directory}")

# Funzione per estrarre i default value dei campi editabili dal PDF
def get_default_values_from_pdf(pdf_path):
    # Estrai i campi editabili e i loro valori dal PDF
    field_values = fillpdfs.get_form_fields(pdf_path)
    # Stampa i campi e i valori predefiniti
    print("Valori di default estratti dal PDF:")

    return field_values

# Funzione per leggere l'elenco dei campi da elenco_campi.json
def read_fields_to_copy(fields_json_path):
    try:
        with open(fields_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("fields_to_copy", [])
    except Exception as e:
        print(f"Errore durante la lettura del file JSON: {e}")
        return []


# Funzione per filtrare i default value che ci interessano e memorizzarli in un dizionario
def filter_default_values(fields_to_copy, field_values):
    filtered_values = {}
    for field_name in fields_to_copy:
        if field_name in field_values:
            filtered_values[field_name] = field_values[field_name]

    return filtered_values

# Funzione per scrivere i valori filtrati nei campi del PDF di destinazione e salvare il PDF compilato
def fill_pdf_and_save(pdf2, pdf_output, filtered_values):
    # Compila i campi del PDF con i valori filtrati
    fillpdfs.write_fillable_pdf(pdf2, pdf_output, filtered_values)
    print(f"PDF compilato e salvato in: {pdf_output}")

# Lettura del file di configurazione
config = read_config()

# Percorso del PDF
pdf1 = config["pdf_paths"]["pdf_sorgente"]
fields_to_copy_path = config["json_paths"]["json_elenco_campi"]
pdf2 = config["pdf_paths"]["pdf_destinazione"]
output_pdf = config["pdf_paths"]["pdf_output"]

# Cerca il PDF necessario nella cartella indicata dal percorso
pdf1 = find_pdf_in_directory(pdf1)  # Trova il primo PDF nella directory sorgente
pdf2 = find_pdf_in_directory(pdf2)  # Trova il primo PDF nella directory destinazione

# Estrazione dei valori di default dal PDF sorgente
default_values = get_default_values_from_pdf(pdf1)

# Lettura dei campi da elenco_campi.json
fields_to_copy = read_fields_to_copy(fields_to_copy_path)

# Filtraggio dei valori che ci interessano
filtered_values = filter_default_values(fields_to_copy, default_values)

# Scrittura dei valori nel PDF di destinazione e salvataggio del nuovo PDF
fill_pdf_and_save(pdf2, output_pdf, filtered_values)

# Stampa dei valori filtrati
print("Valori filtrati:")
for field_name, field_value in filtered_values.items():
    print(f"Campo: {field_name}, Valore: {field_value}")
