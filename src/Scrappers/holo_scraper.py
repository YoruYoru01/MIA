import requests
from bs4 import BeautifulSoup
import csv
import time
import re  

# URL base con paginación
base_url = "https://hololist.net/page/{}/?s=&type=&category_name=&group=hololive-production&link=&content=&language=&gender=&zodiac=&model=&status=&sort=added-date"

# Función para obtener los enlaces de VTubers
def get_vtuber_links():
    vtuber_links = []
    page = 1

    while True:
        current_page_url = base_url.format(page)
        print(f"Leyendo la página {page}: {current_page_url}")

        response = requests.get(current_page_url)
        if response.status_code != 200:
            print(f"Error al acceder a la página {page}. Deteniendo.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        vtuber_elements = soup.find_all("a", class_="line-truncate", href=True)

        new_links = [vtuber['href'] for vtuber in vtuber_elements if vtuber['href'].startswith("https")]
        if not new_links:
            print(f"No se encontraron más enlaces en la página {page}. Fin de la paginación.")
            break

        vtuber_links.extend(new_links)
        print(f"Página {page}: {len(new_links)} enlaces encontrados.")
        page += 1
        time.sleep(1)

    print(f"Total de enlaces de VTubers encontrados: {len(vtuber_links)}")
    return vtuber_links

# Función para limpiar texto adicional (eliminar nombres de campo)
def clean_text(text):
    if text is None:
        return "No disponible"
    # Eliminar etiquetas como 'Description', 'Lore', etc., al inicio del texto
    text = re.sub(r"^(Description|Lore|Nickname\(s\)|Birthday|Height|Weight|Affiliation|Gender|Likes|Dislikes|Achievements):?", "", text)
    return text.replace("\n", " ").replace(",", "").strip()

# Función para extraer datos de una VTuber específica
def extract_vtuber_data(url):
    print(f"Extrayendo datos de: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error al acceder a {url}")
        return {"URL": url, "Error": "No se pudo acceder"}

    soup = BeautifulSoup(response.text, "html.parser")
    fields = [
        "description", "lore", "nickname", "birthday", "height",
        "weight", "affiliation", "gender", "likes", "dislikes", "achievements"
    ]

    vtuber_data = {"URL": url}
    for field in fields:
        element = soup.find(id=field)
        content = element.get_text(strip=True) if element else "No disponible"
        vtuber_data[field.capitalize()] = clean_text(content)
    return vtuber_data

# Función principal
def main():
    print("Iniciando scraping de VTubers de Hololive...")
    vtuber_links = get_vtuber_links()

    # Archivo CSV
    output_file = "hololive_vtubers_data.csv"
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=[
            "URL", "Description", "Lore", "Nickname", "Birthday",
            "Height", "Weight", "Affiliation", "Gender", "Likes", "Dislikes", "Achievements"
        ])
        writer.writeheader()

        # Extraer datos de cada VTuber
        for idx, vtuber_url in enumerate(vtuber_links, start=1):
            print(f"[{idx}/{len(vtuber_links)}] Procesando: {vtuber_url}")
            data = extract_vtuber_data(vtuber_url)
            writer.writerow(data)
            time.sleep(1)

    print(f"Datos guardados correctamente en '{output_file}'.")

if __name__ == "__main__":
    main()