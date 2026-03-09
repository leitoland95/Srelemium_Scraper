import os
import threading
import time
import requests
import base64
import json
from pathlib import Path
from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import uvicorn

app = FastAPI()
execution_logs = []

# Inicializar WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

def log(msg: str):
    execution_logs.append(msg)
    print(msg)

# ------------------- ENDPOINTS -------------------

@app.post("/navegar")
def navegar(url: str):
    driver.get(url)
    log(f"Navegado a {url}")
    return {"status": "ok", "url": url}

@app.get("/xpaths")
def obtener_xpaths():
    elementos = driver.find_elements(By.XPATH, "//input|//button|//a|//div")
    resultado = []
    for e in elementos:
        try:
            desc = e.get_attribute("name") or e.get_attribute("id") or e.text or e.get_attribute("href")
            resultado.append({"xpath": get_xpath(e), "descripcion": desc})
        except Exception:
            continue
    return resultado

def get_xpath(element):
    # Construir un xpath absoluto
    path = ""
    while element is not None and element.tag_name.lower() != "html":
        parent = element.find_element(By.XPATH, "..")
        siblings = parent.find_elements(By.XPATH, element.tag_name)
        index = siblings.index(element) + 1
        path = f"/{element.tag_name}[{index}]" + path
        element = parent
    return "/html" + path

@app.get("/screenshots")
def screenshot():
    png = driver.get_screenshot_as_base64()
    log("Captura de pantalla tomada")
    return {"screenshot": png}

@app.post("/refrescar")
def refrescar():
    driver.refresh()
    log("Página refrescada")
    return {"status": "ok"}

@app.post("/clicar")
def clicar(xpath: str):
    elem = driver.find_element(By.XPATH, xpath)
    elem.click()
    log(f"Clic en {xpath}")
    return {"status": "ok"}

@app.post("/input")
def escribir(xpath: str, texto: str):
    elem = driver.find_element(By.XPATH, xpath)
    elem.clear()
    elem.send_keys(texto)
    log(f"Texto '{texto}' introducido en {xpath}")
    return {"status": "ok"}

@app.get("/exportar_cookies")
def exportar_cookies():
    cookies = driver.get_cookies()
    local_storage = driver.execute_script("return JSON.stringify(window.localStorage);")
    session_storage = driver.execute_script("return JSON.stringify(window.sessionStorage);")
    data = {
        "cookies": cookies,
        "localStorage": json.loads(local_storage),
        "sessionStorage": json.loads(session_storage)
    }
    log("Cookies y storage exportados")
    return data

from fastapi import FastAPI
from pathlib import Path
import json
from selenium import webdriver

app = FastAPI()

# Supongamos que ya tienes tu driver inicializado
driver = webdriver.Chrome()

@app.post("/cargarcookies")
def cargar_cookies():
    path = Path("telegram_cookies.json")
    if not path.exists():
        return {"error": "telegram_cookies.json no encontrado"}

    # Leer archivo JSON
    with open(path, "r") as f:
        data = json.load(f)

    # Ir al dominio correcto antes de cargar cookies
    driver.get("https://web.telegram.org")

    # Cargar cookies
    driver.delete_all_cookies()
    for c in data.get("cookies", []):
        try:
            driver.add_cookie(c)
        except Exception as e:
            print(f"Error al cargar cookie {c}: {e}")

    # Refrescar para aplicar cookies
    driver.refresh()

    # Cargar localStorage y sessionStorage
    driver.execute_script(f"""
        let localData = {json.dumps(data.get("localStorage", {}))};
        for (let key in localData) {{ localStorage.setItem(key, localData[key]); }}
        let sessionData = {json.dumps(data.get("sessionStorage", {}))};
        for (let key in sessionData) {{ sessionStorage.setItem(key, sessionData[key]); }}
    """)

    # Refrescar otra vez para aplicar storages
    driver.refresh()

    return {"status": "Sesión restaurada correctamente"}

@app.post("/limpiar_cookies")
def limpiar_cookies():
    driver.delete_all_cookies()
    log("Cookies eliminadas")
    return {"status": "ok"}

@app.get("/mostrar_cookies")
def mostrar_cookies():
    cookies = driver.get_cookies()
    log(f"Cookies actuales: {cookies}")
    return {"cookies": cookies}

# ------------------- KEEP ALIVE -------------------

def keep_alive():
    url = os.getenv("RENDEREXTERNALURL")
    if not url:
        log("No se encontró RENDEREXTERNALURL, keep_alive desactivado")
        return
    while True:
        try:
            requests.get(url, timeout=10)
            log(f"Ping a {url} para mantener vivo el servicio")
        except Exception as e:
            log(f"Error en keep_alive: {e}")
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))