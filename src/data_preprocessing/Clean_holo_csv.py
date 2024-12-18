import csv

# Función para limpiar los valores incompletos
def clean_value(value):
    if value is None or value.strip() in ["No disponible", ".", "....", "", "N/A"]:
        return "Unknown"
    return value.strip()

# Función para limpiar el archivo CSV
def clean_csv(input_file, output_file):
    with open(input_file, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames  # Obtener los nombres de las columnas

        with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Limpiar cada celda del CSV
                for key in row:
                    row[key] = clean_value(row[key])
                writer.writerow(row)

    print(f"Archivo limpio y formateado guardado en '{output_file}'.")

# Archivos de entrada y salida
input_csv = "data/raw/cobertura_tematica/hololive_vtubers_data.csv"
output_csv = "data/processed/Datasets/hololive_vtubers_cleaned.csv"

# Ejecutar la función
clean_csv(input_csv, output_csv)