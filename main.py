import tomllib  # Libreria per leggere il file config.toml
import os
import fitz  # PyMuPDF
import json  # Per scrivere su file JSON
import re  # Per le regex

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

# Funzione per leggere l'elenco dei campi da elenco_campi.json
def read_fields_to_copy(fields_json_path):
    try:
        with open(fields_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("fields_to_copy", [])
    except Exception as e:
        print(f"Errore durante la lettura del file JSON: {e}")
        return []

# Funzione per estrarre i Default Value dei campi dal PDF sorgente
def get_default_values_from_pdf(pdf_path):
    extracted_fields = {}
    # Apri il PDF con PyMuPDF
    pdf_document = fitz.open(pdf_path)

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        field_widgets = page.widgets()  # Ottiene i widget (campi editabili)

        for widget in field_widgets:
            field_name = widget.field_name
            field_value = widget.field_value

            # Gestione dei caratteri Unicode non validi
            field_name_safe = field_name.encode('utf-8', 'replace').decode('utf-8')
            if field_value is not None:
                field_value_safe = str(field_value).encode('utf-8', 'replace').decode('utf-8')
            else:
                field_value_safe = "N/A"  # Se il valore è vuoto o nullo

            # Aggiungi il nome del campo e il valore al dizionario
            extracted_fields[field_name_safe] = field_value_safe

    pdf_document.close()

    return extracted_fields  # Assicurati di restituire il dizionario

# Funzione per scrivere i dati estratti su un file JSON
def write_to_json(data, json_file_path):
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Dati scritti con successo su {json_file_path}")
    except Exception as e:
        print(f"Errore durante la scrittura del file JSON: {e}")

# Funzione per filtrare i dati di pre.json con regex e scrivere post.json
def filter_fields_with_regex(pre_json_path, post_json_path, fields_to_copy):
    try:
        with open(pre_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        filtered_data = {}

        # Per ogni campo in fields_to_copy, creiamo una regex per cercarlo in pre.json
        for field in fields_to_copy:
            # Creiamo dinamicamente la regex per il campo corrente
            regex = re.compile(f'"\\[?{re.escape(field)}\\]?":\\s*"([^"]+)"')

            # Converti il contenuto di pre.json in una stringa
            pre_json_str = json.dumps(data)

            # Cerca il campo nel file JSON con la regex
            match = regex.search(pre_json_str)

            if match:
                # Se troviamo una corrispondenza, aggiungiamo il campo e il valore a filtered_data
                filtered_data[field] = match.group(1)

        # Scrivi i campi filtrati in post.json
        write_to_json(filtered_data, post_json_path)

    except Exception as e:
        print(f"Errore durante la lettura o scrittura dei file JSON: {e}")

# Funzione per leggere i dati da post.json
def read_json(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Errore durante la lettura del file JSON: {e}")
        return {}

# Funzione per scrivere i valori nei campi editabili del PDF destinazione e output
def fill_multiple_pdf_fields(input_pdf, output_pdf, data_dict, fields_to_copy):
    pdf_document = fitz.open(input_pdf)

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        field_widgets = page.widgets()

        # Verifica se ci sono widget (campi editabili) sulla pagina
        if field_widgets:
            # Cerca i campi corrispondenti nella lista fields_to_copy
            for widget in field_widgets:
                widget_name = widget.field_name

                # Gestisce sia i campi con che senza parentesi quadre
                for field_name in fields_to_copy:
                    if widget_name in [field_name, f'[{field_name}]', f'{field_name}]', f'[{field_name}']:
                        # Se il campo esiste nel JSON, scrivi il valore nel campo
                        if field_name in data_dict:
                            field_value = data_dict[field_name]
                            if field_value is None:
                                field_value = ""  # Assegna una stringa vuota se il valore è None
                            else:
                                field_value = str(field_value)  # Converte il valore in stringa

                            # Assegna il valore al widget
                            widget.field_value = field_value
                            widget.update()  # Aggiorna il widget con il nuovo valore
                            print(f"Campo '{widget_name}' aggiornato con il valore '{field_value}'")

    # Salva il nuovo PDF compilato ovvero il PDF_output
    pdf_document.save(output_pdf)
    pdf_document.close()



# Lettura del file di configurazione
config = read_config()

# Percorsi dei PDF presi dal file config.toml
pdf1 = config["pdf_paths"]["pdf_sorgente"]
pdf2 = config["pdf_paths"]["pdf_destinazione"]
output_pdf = config["pdf_paths"]["pdf_output"]
json_output_path = config["json_paths"]["json_pre"]
post_json_output_path = config["json_paths"]["json_post"]
fields_to_copy_path = config["json_paths"]["json_elenco_campi"]

pdf1 = find_pdf_in_directory(pdf1)  # Trova il primo PDF nella directory sorgente
pdf2 = find_pdf_in_directory(pdf2)  # Trova il primo PDF nella directory destinazione

# Lettura dei campi da elenco_campi.json
fields_to_copy = read_fields_to_copy(fields_to_copy_path)

# Estrazione dei valori di default dal primo PDF
fields_pdf1 = get_default_values_from_pdf(pdf1)

# Scrittura dei dati estratti su file JSON
write_to_json(fields_pdf1, json_output_path)

# Filtrare i dati di pre.json e scriverli in post.json
filter_fields_with_regex(json_output_path, post_json_output_path, fields_to_copy)

# Stampa i valori estratti per conferma
print("Valori di default estratti dal PDF sorgente:")
for field, value in fields_pdf1.items():
    print(f"{field}: {value}")

# Attesa per raccogliere tutti i dati
#input("Premi Invio per continuare e scrivere i dati nel PDF di destinazione...")

# Lettura dei dati da post.json
fields_from_post_json = read_json(post_json_output_path)

# Compilazione del secondo PDF con i dati letti da post.json per tutti i campi in fields_to_copy
fill_multiple_pdf_fields(pdf2, output_pdf, fields_from_post_json, fields_to_copy)

print(f"Il PDF compilato è stato salvato in: {post_json_output_path}")
