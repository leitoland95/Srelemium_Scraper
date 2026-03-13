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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi import Body

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
    
def build_xpath(el):
    return driver.execute_script(
        """function absoluteXPath(element){
            var comp, comps = [];
            var parent = null;
            var xpath = '';
            var getPos = function(element){
                var position = 1, curNode;
                for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){
                    if (curNode.nodeName == element.nodeName){
                        ++position;
                    }
                }
                return position;
            };
            if (element instanceof Document){
                return '/';
            }
            for (; element && !(element instanceof Document); element = element.parentNode){
                comp = comps[comps.length] = {};
                comp.name = element.nodeName;
                comp.position = getPos(element);
            }
            for (var i = comps.length - 1; i >= 0; i--){
                comp = comps[i];
                xpath += '/' + comp.name.toLowerCase();
                if (comp.position != null){
                    xpath += '[' + comp.position + ']';
                }
            }
            return xpath;
        } return absoluteXPath(arguments[0]);""", el)      

# ------------------- ENDPOINTS -------------------



@app.post("/buscar_xpath")
def buscar_xpath_por_descripcion(descripcion: str = Body(..., embed=True)):
    try:
        # Recolectamos elementos relevantes: divs, links, inputs, botones
        elementos = driver.find_elements(By.XPATH, "//div | //a | //input | //textarea | //button | //*[@role='button']")
        resultados = []

        for el in elementos:
            if not el.is_displayed():
                continue

            xp = build_xpath(el)
            if not xp:
                continue

            # Construimos una descripción similar a la de tus otros endpoints
            desc = el.text.strip() or el.get_attribute("placeholder") or el.get_attribute("value") or \
                   el.get_attribute("name") or el.get_attribute("id") or el.get_attribute("href") or ""

            # Comparamos con la descripción recibida (case-insensitive, substring)
            if descripcion.lower() in desc.lower():
                resultados.append({
                    "xpath": xp,
                    "descripcion": desc,
                    "tipo": el.tag_name.lower()
                })

        if resultados:
            log(f"Encontrados {len(resultados)} elementos con descripción '{descripcion}'")
            return {"resultados": resultados}
        else:
            return {"resultados": [], "mensaje": f"No se encontraron elementos con descripción '{descripcion}'"}

    except Exception as e:
        return {"error": f"Error al buscar descripción '{descripcion}': {e}"}
@app.post("/navegar")
def navegar(url: str):
    driver.get(url)
    log(f"Navegado a {url}")
    return {"status": "ok", "url": url}



@app.get("/xpaths_divs")
def get_xpaths_divs_full():
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div"))
        )
    except Exception as e:
        return {"error": f"No se encontraron divs: {e}"}

    elementos = []
    for el in driver.find_elements(By.XPATH, "//div"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                # Para divs, la descripción puede ser su texto interno o atributos relevantes
                desc = el.text.strip() or el.get_attribute("id") or \
                       el.get_attribute("class") or ""
                elementos.append({
                    "xpath": xp,
                    "descripcion": desc,
                    "tipo": el.tag_name.lower()
                })

    return {"divs": elementos}


@app.get("/xpaths_links")
def get_xpaths_links_full():
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a"))
        )
    except Exception as e:
        return {"error": f"No se encontraron enlaces: {e}"}

    elementos = []
    for el in driver.find_elements(By.XPATH, "//a"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                # Para enlaces, la descripción puede ser el texto visible o atributos relevantes
                desc = el.text.strip() or el.get_attribute("href") or \
                       el.get_attribute("title") or el.get_attribute("id") or ""
                elementos.append({
                    "xpath": xp,
                    "descripcion": desc,
                    "tipo": el.tag_name.lower()
                })

    return {"links": elementos}
    
@app.get("/xpaths_inputs")
def get_xpaths_inputs_full():
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | //input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | //textarea")
            )
        )
    except Exception as e:
        return {"error": f"No se encontraron inputs: {e}"}

    elementos = []
    for el in driver.find_elements(By.XPATH, "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | //input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | //textarea"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                desc = el.get_attribute("placeholder") or el.get_attribute("name") or \
                       el.get_attribute("id") or el.get_attribute("value") or ""
                elementos.append({
                    "xpath": xp,
                    "descripcion": desc,
                    "tipo": el.tag_name.lower()
                })

    return {"inputs": elementos}
    


@app.get("/xpaths_buttons")
def get_xpaths_buttons_full():
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//button | //*[@role='button'] | //input[@type='button'] | //input[@type='submit']")
            )
        )
    except Exception as e:
        return {"error": f"No se encontraron botones: {e}"}

    elementos = []
    for el in driver.find_elements(By.XPATH, "//button | //*[@role='button'] | //input[@type='button'] | //input[@type='submit']"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                desc = el.text.strip() or el.get_attribute("value") or \
                       el.get_attribute("name") or el.get_attribute("id") or ""
                elementos.append({
                    "xpath": xp,
                    "descripcion": desc,
                    "tipo": el.tag_name.lower()
                })

    return {"botones": elementos}    
            

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

@app.post("/navegar_atras")
def navegar_atras():
    try:
        driver.back()
        log("Navegado un paso atrás")
        return {"status": "ok", "accion": "back"}
    except Exception as e:
        return {"error": f"No se pudo navegar atrás: {e}"}
        
@app.get("/escribir_input")
def escribir_unico_input():
    try:
        # Espera hasta que haya al menos un input o textarea visible
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | //input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | //textarea")
            )
        )
    except Exception as e:
        return {"error": f"No se encontró ningún input: {e}"}

    try:
        # Obtiene el primer input/textarea visible
        el = driver.find_element(By.XPATH, "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | //input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | //textarea")
        if el.is_displayed():
            el.clear()  # Limpia el campo antes de escribir
            el.send_keys("@RichDogGameBot")
            return {"resultado": "Texto '@RichDogGameBot' escrito en el único input"}
        else:
            return {"error": "El input encontrado no está visible"}
    except Exception as e:
        return {"error": f"No se pudo escribir en el input: {e}"}

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