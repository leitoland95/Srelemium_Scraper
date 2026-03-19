import requests
import json
import base64
import os

BASE_URL = "https://srelemium-scraper-1.onrender.com"  # Ajusta si tu backend corre en otro host/puerto


def string_a_lista(cadena: str) -> list:
    return [int(x) for x in cadena.split(",")]
    

def navegar():
    url = input("URL a navegar: ")
    r = requests.post(f"{BASE_URL}/navegar", params={"url": url})
    print(r.json())

def listar_divs():
    r = requests.get(f"{BASE_URL}/xpaths_divs")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def listar_links():
    r = requests.get(f"{BASE_URL}/xpaths_links")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def listar_inputs():
    r = requests.get(f"{BASE_URL}/xpaths_inputs")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    
def listar_checkboxes():
    r = requests.get(f"{BASE_URL}/checkboxes")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))    

def listar_botones():
    r = requests.get(f"{BASE_URL}/xpaths_buttons")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def screenshot():
    r = requests.get(f"{BASE_URL}/screenshots")
    data = r.json()
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(data["screenshot"]))
    print("Captura guardada en screenshot.png")

def refrescar():
    r = requests.post(f"{BASE_URL}/refrescar")
    print(r.json())

def clicar():
    xpath = input("XPath a clicar: ")
    r = requests.post(f"{BASE_URL}/clicar", params={"xpath": xpath})
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text)

def exportar_cookies():
    r = requests.get(f"{BASE_URL}/exportar_cookies")
    with open("telegram_cookies.json", "w", encoding="utf-8") as f:
        json.dump(r.json(), f, indent=2, ensure_ascii=False)
    print("Cookies exportadas a telegram_cookies.json")

def cargar_cookies():
    r = requests.post(f"{BASE_URL}/cargarcookies")
    print(r.json())

def limpiar_cookies():
    r = requests.post(f"{BASE_URL}/limpiar_cookies")
    print(r.json())

def mostrar_cookies():
    r = requests.get(f"{BASE_URL}/mostrar_cookies")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

def navegar_atras():
    r = requests.get(f"{BASE_URL}/navegar_atras")
    print(r.json())

# --- NUEVO ENDPOINT: buscar por descripciÃ³n ---

def escribir_input():
    xpath = input("XPath del input: ")
    texto = input("Texto a escribir: ")
    r = requests.post(f"{BASE_URL}/escribir_input", params={"xpath": xpath, "texto": texto})
    print(r.json())

def clicar_checkbox():
    xpath = input("XPath a clicar: ")
    r = requests.post(f"{BASE_URL}/clicar_checkbox", params={"xpath": xpath})
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text)

def listar_labels():
    r = requests.get(f"{BASE_URL}/xpaths_labels")
    print(r.json())
    
def download():
    try:
        # Llamada al endpoint
        response = requests.get(f"{BASE_URL}/download_html")
        data = response.json()

        # Mostrar informaciÃ³n bÃ¡sica
        print("Estado:", data.get("status"))
        print("Longitud del HTML:", data.get("length"))

        # Guardar el HTML en un archivo local
        html_content = data.get("html", "")
        with open("pagina_descargada.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        print("Archivo 'pagina_descargada.html' creado exitosamente.")

    except Exception as e:
        print("Error al descargar el HTML:", str(e))

def scrap_iframe():
	xpath = input("Ingresar Xpath del Iframe: ")
    r = requests.post(f"{BASE_URL}/scrap_iframe", params={"xpath":xpath})
    print(r.json())
    
def list_iframes():
    r = requests.get(f"{BASE_URL}/list_iframes")
    print(r.json())

def switch_iframe():
    xpath = input("XPath del Iframe: ")
    r = requests.post(f"{BASE_URL}/switch_iframe", params={"xpath": xpath})
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text)
    
def switch_default():
    r = requests.get(f"{BASE_URL}/switch_default")
    print(r.json())

def click_elemento():
    sec = input("secuencia:")
    secuencia = string_a_lista(sec)
    r = requests.post(
        f"{BASE_URL}/click_elemento",
        json={"secuencia": secuencia}   # ðŸ‘ˆ aquÃ­ va json, no params
    )
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text)
	
def click_actionchains():
    xpath = input("Xpath del elemento web:")
    r = requests.post(
        f"{BASE_URL}/click_actionchains",
        json={"xpath": xpath}   # ðŸ‘ˆ aquÃ­ va json, no params
    )
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text)


def click_js():
    xpath = input("Xpath del elemento web:")
    r = requests.post(
        f"{BASE_URL}/click_js",
        json={"xpath": xpath}   # ðŸ‘ˆ aquÃ­ va json, no params
    )
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text) 

def click_touch():
    xpath = input("Xpath del elemento web:")
    r = requests.post(
        f"{BASE_URL}/click_touch",
        json={"xpath": xpath}   # ðŸ‘ˆ aquÃ­ va json, no params
    )
    try:
        print(r.json())
    except Exception:
        print("Respuesta no es JSON:", r.text) 	


def scrape_iframe_click():
    xpath = input("Xpath del inicio:")
    r = requests.post(
        f"{BASE_URL}/scrape_iframe_click",
        json={"xpath": xpath}   # ðŸ‘ˆ aquÃ­ va json, no params
    )
    try:
        print(r.json())
    except Exception as e:
        print("Respuesta no es JSON:", e) 

def models():
    r = requests.get(f"{BASE_URL}/models")
    print(r.json())	
    
def cliente_subir_foto():

    image_path = input("Ingresa la ruta de la foto a subir: ").strip()

    if not os.path.exists(image_path):
        print("Error: la ruta de la foto no existe.")
        return None

    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/png")}
            resp = requests.post("https://srelemium-scraper-1.onrender.com/upload", files=files)

        if resp.status_code == 200:
            data = resp.json()
            print("Foto subida correctamente.")
            print("URL publica:", data["url"])
            return data["url"]
        else:
            print("Error al subir la foto:", resp.status_code, resp.text)
            return None
    except Exception as e:
        print("Error de conexion:", e)
        return None    
    
def cliente_limpiar_uploads():
    """
    Cliente que llama al endpoint /clean_uploads
    y muestra la respuesta del servidor.
    """
    try:
        resp = requests.get("https://srelemium-scraper-1.onrender.com/clean_uploads")
        if resp.status_code == 200:
            print("Servidor:", resp.text)
            return resp.text
        else:
            print("Error:", resp.status_code, resp.text)
            return None
    except Exception as e:
        print("Error de conexion:", e)
        return None    
    
def escribir_fijo():
  try:
    texto = input("Texto a escribir: ")
    r = requests.post(f"{BASE_URL}/escribir_fijo", params={"texto": texto})
    print(r.json())
  except Exception as e:
    return {"error":e}
    
    
def escribir_y_click():
    texto = input("Introduce el texto a escribir en el input: ")
    try:
        # El endpoint espera el parametro 'texto' en la query
        response = requests.post(f"{BASE_URL}/escribir_y_click", params={"texto": texto})
        
        if response.status_code == 200:
            print("Respuesta del servidor:", response.json())
        else:
            print("Error en la peticion:", response.status_code, response.text)
    except Exception as e:
        print("Excepcion al consumir el endpoint:", str(e))    
        
def sol_xcap():
    r = requests.get(f"{BASE_URL}/sol_xcap")
    print(r.json())
            
  
def menu():
    opciones = {
        "1": ("Navegar a URL", navegar),
        "2": ("Listar DIVs", listar_divs),
        "3": ("Listar Links", listar_links),
        "4": ("Listar Inputs", listar_inputs),
        "5": ("Listar Botones", listar_botones),
        "6": ("Tomar Screenshot", screenshot),
        "7": ("Refrescar PÃ¡gina", refrescar),
        "8": ("Clicar elemento por XPath", clicar),
        "9": ("Exportar Cookies", exportar_cookies),
        "10": ("Cargar Cookies", cargar_cookies),
        "11": ("Limpiar Cookies", limpiar_cookies),
        "12": ("Mostrar Cookies", mostrar_cookies),
        "13": ("Navegar un paso atrÃ¡s", navegar_atras),
        "14": ("Escribir texto en input", escribir_input),
        "15": ("Listar_Checkboxes", listar_checkboxes),
        "16": ("Clicar_Checkbox", clicar_checkbox),
        "17": ("Listar_labels", listar_labels),
        "18": ("Descargar_PÃ¡gina", download),
        "19": ("Scraping iFrame", scrap_iframe),
        "20": ("Listar_Iframes", list_iframes),
        "21": ("Cambiar_Iframe", switch_iframe),
        "22": ("Salir_de_Iframe", switch_default),
        "23": ("Clicar_captcha", click_elemento),
        "24": ("Clicar_actionchains", click_actionchains),
        "25": ("Clicar_click_js", click_js),
        "26": ("Clicar_click_touch", click_touch),
        "27": ("Scraping_puter_iframe", scrape_iframe_click),
        "28": ("Mostrar modelos IA", models),
        "29": ("Subir foto a servidor", cliente_subir_foto),
        "30": ("Limpiar carpeta upload", cliente_limpiar_uploads),
        "31": ("Escribir fijo", escribir_fijo),
        "32": ("Escribir y Clicar", escribir_y_click),
        "33": ("Solucionar xCaptcha", sol_xcap),
        "0": ("Salir", None),
    }

    while True:
        print("\n--- MENÃš CLIENTE ---")
        for k, v in opciones.items():
            print(f"{k}. {v[0]}")
        choice = input("Selecciona opciÃ³n: ").strip()
        if choice == "0":
            break
        action = opciones.get(choice)
        if action:
            try:
                action[1]()
            except Exception as e:
                print(f"Error ejecutando acciÃ³n: {e}")
        else:
            print("OpciÃ³n invÃ¡lida")

if __name__ == "__main__":
    menu()