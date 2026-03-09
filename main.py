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

# ------------------- INICIALIZAR WEBDRIVER -------------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")
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
def obtener_xpaths(limite: int = 3):
    elementos = driver.find_elements(By.XPATH, "//input|//button|//a|//div")
    resultado = []
    contador = {"input": 0, "button": 0, "div": 0, "a": 0}

    for e in elementos:
        try:
            tag = e.tag_name.lower()
            if tag in contador and contador[tag] < limite:
                desc = e.get_attribute("name") or e.get_attribute("id") or e.text or e.get_attribute("href")
                resultado.append({"xpath": get_xpath(e), "descripcion": desc, "tipo": tag})
                contador[tag] += 1

                # Si ya alcanzamos el límite en todos los tipos, detenemos el bucle
                if all(c >= limite for c in contador.values()):
                    break
        except Exception:
            continue

    return resultado
    
@app.get("/xpaths_inputs_buttons")
def obtener_xpaths_inputs_buttons(limite: int = 10):
    # Selecciona inputs y botones en todas sus variantes
    elementos = driver.find_elements(
        By.XPATH,
        "//input | //button | //input[@type='button'] | //input[@type='submit'] | //*[@role='button']"
    )
    resultado = []
    count = 0

    for e in elementos:
        if count >= limite:
            break
        try:
            desc = (
                e.get_attribute("name")
                or e.get_attribute("id")
                or e.get_attribute("placeholder")
                or e.get_attribute("value")
                or e.text
            )
            resultado.append({
                "xpath": get_xpath(e),
                "descripcion": desc,
                "tipo": e.tag_name.lower()
            })
            count += 1
        except Exception:
            continue

    return resultado    
    
@app.get("/xpaths_inputs")
def obtener_xpaths_inputs(limite: int = 3):
    elementos = driver.find_elements(By.TAG_NAME, "input")
    resultado = []
    for e in elementos[:limite]:
        try:
            desc = e.get_attribute("name") or e.get_attribute("id") or e.text or e.get_attribute("placeholder")
            resultado.append({"xpath": get_xpath(e), "descripcion": desc, "tipo": "input"})
        except Exception:
            continue
    return resultado


@app.get("/xpaths_buttons")
def obtener_xpaths_buttons(limite: int = 3):
    elementos = driver.find_elements(By.TAG_NAME, "button")
    resultado = []
    for e in elementos[:limite]:
        try:
            desc = e.get_attribute("name") or e.get_attribute("id") or e.text
            resultado.append({"xpath": get_xpath(e), "descripcion": desc, "tipo": "button"})
        except Exception:
            continue
    return resultado


@app.get("/xpaths_divs")
def obtener_xpaths_divs(limite: int = 3):
    elementos = driver.find_elements(By.TAG_NAME, "div")
    resultado = []
    for e in elementos[:limite]:
        try:
            desc = e.get_attribute("id") or e.get_attribute("class") or (e.text or "").strip()
            resultado.append({"xpath": get_xpath(e), "descripcion": desc, "tipo": "div"})
        except Exception:
            continue
    return resultado


@app.get("/xpaths_links")
def obtener_xpaths_links(limite: int = 3):
    elementos = driver.find_elements(By.TAG_NAME, "a")
    resultado = []
    for e in elementos[:limite]:
        try:
            desc = e.text or e.get_attribute("href")
            resultado.append({"xpath": get_xpath(e), "descripcion": desc, "tipo": "a"})
        except Exception:
            continue
    return resultado    

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

@app.post("/cargarcookies")
def cargar_cookies():
    path = Path("telegram_cookies.json")
    if not path.exists():
        return {"error": "telegram_cookies.json no encontrado"}

    with open(path, "r") as f:
        data = json.load(f)

    driver.get("https://web.telegram.org")
    driver.delete_all_cookies()
    for c in data.get("cookies", []):
        try:
            driver.add_cookie(c)
        except Exception as e:
            log(f"Error al cargar cookie {c.get('name')}: {e}")

    driver.execute_script(f"""
        let localData = {json.dumps(data.get("localStorage", {}))};
        for (let key in localData) {{ localStorage.setItem(key, localData[key]); }}
        let sessionData = {json.dumps(data.get("sessionStorage", {}))};
        for (let key in sessionData) {{ sessionStorage.setItem(key, sessionData[key]); }}
    """)

    driver.refresh()
    log("Cookies y storage cargados desde telegramcookies.json")
    return {"status": "Sesión restaurada correctamente"}

@app.post("/limpiar_cookies")
def limpiar_cookies():
    driver.delete_all_cookies()
    log("Cookies eliminadas")
    return {"status": "ok"}

@app.get("/mostrar_cookies")
def mostrar_cookies():
    cookies = driver.get_cookies()
    local_storage = driver.execute_script("return JSON.stringify(window.localStorage);")
    session_storage = driver.execute_script("return JSON.stringify(window.sessionStorage);")
    data = {
        "cookies": cookies,
        "localStorage": json.loads(local_storage),
        "sessionStorage": json.loads(session_storage)
    }
    log(f"Cookies actuales: {cookies}")
    return data

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