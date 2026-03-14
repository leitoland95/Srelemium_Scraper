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
user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")


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
                (By.XPATH,
                 "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | "
                 "//input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | "
                 "//textarea | //input[@type='checkbox']")
            )
        )
    except Exception as e:
        return {"error": f"No se encontraron inputs ni checkboxes: {e}"}

    elementos = []
    for el in driver.find_elements(
        By.XPATH,
        "//input[@type='text'] | //input[@type='password'] | //input[@type='email'] | "
        "//input[@type='search'] | //input[@type='tel'] | //input[@type='url'] | "
        "//textarea | //input[@type='checkbox']"
    ):
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
        
@app.get("/checkboxes")
def get_xpaths_checkboxes():
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='checkbox']")
            )
        )
    except Exception as e:
        return {"error": f"No se encontró ningún checkbox: {e}"}

    try:
        el = driver.find_element(By.XPATH, "//input[@type='checkbox']")
        xp = build_xpath(el)
        return {"xpath": xp}
    except Exception as e:
        return {"error": f"No se pudo obtener el xpath del checkbox: {e}"}
    

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
    

@app.get("/navegar_atras")
def navegar_atras():
    try:
        driver.back()
        log("Navegado un paso atrás")
        return {"status": "ok", "accion": "back"}
    except Exception as e:
        return {"error": f"No se pudo navegar atrás: {e}"}
        
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

@app.post("/escribir_input")
def escribir(xpath: str, texto: str):
    elem = driver.find_element(By.XPATH, xpath)
    elem.clear()
    elem.send_keys(texto)
    log(f"Texto '{texto}' introducido en {xpath}")
    return {"status": "ok"}
    
@app.post("/clicar_checkbox")
def clicar_checkbox(xpath: str):
    try:
        element = driver.find_element(By.XPATH, xpath)
        # Intento normal
        element.click()
        return {"status": "ok", "method": "selenium", "xpath": xpath}
    except (ElementClickInterceptedException, ElementNotInteractableException):
        try:
            # Si falla, forzamos con JS
            driver.execute_script("arguments[0].click();", element)
            return {"status": "ok", "method": "javascript", "xpath": xpath}
        except Exception as e:
            return {"status": "error", "xpath": xpath, "detail": str(e)}
    except Exception as e:
        return {"status": "error", "xpath": xpath, "detail": str(e)}    
  
@app.post("/xpaths_labels")
def obtener_labels(url: str = Body(..., embed=True)):
    labels = driver.find_elements(By.TAG_NAME, "label")
    resultados = []

    for idx, label in enumerate(labels, start=1):
        try:
            # Obtener XPath absoluto vía JS
            xpath = driver.execute_script(
                "function absoluteXPath(element) {"
                "var comp, comps = [];"
                "var parent = null;"
                "var xpath = '';"
                "var getPos = function(element) {"
                "var position = 1, curNode;"
                "if (element.nodeType == Node.ATTRIBUTE_NODE) {"
                "return null;"
                "}"
                "for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){"
                "if (curNode.nodeName == element.nodeName){"
                "++position;"
                "}"
                "}"
                "return position;"
                "};"
                "if (element instanceof Document) {return '/';}"
                "for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {"
                "comp = comps[comps.length] = {};"
                "switch (element.nodeType) {"
                "case Node.TEXT_NODE:"
                "comp.name = 'text()';"
                "break;"
                "case Node.ATTRIBUTE_NODE:"
                "comp.name = '@' + element.nodeName;"
                "break;"
                "case Node.PROCESSING_INSTRUCTION_NODE:"
                "comp.name = 'processing-instruction()';"
                "break;"
                "case Node.COMMENT_NODE:"
                "comp.name = 'comment()';"
                "break;"
                "case Node.ELEMENT_NODE:"
                "comp.name = element.nodeName;"
                "break;"
                "}"
                "comp.position = getPos(element);"
                "}"
                "for (var i = comps.length - 1; i >= 0; i--) {"
                "comp = comps[i];"
                "xpath += '/' + comp.name.toLowerCase();"
                "if (comp.position !== null) {"
                "xpath += '[' + comp.position + ']';"
                "}"
                "}"
                "return xpath;"
                "} return absoluteXPath(arguments[0]);", label)

            # Descripción: texto visible o atributos
            descripcion = label.text.strip()
            if not descripcion:
                descripcion = label.get_attribute("for") or label.get_attribute("class") or f"label_{idx}"

            resultados.append({
                "xpath": xpath,
                "descripcion": descripcion
            })
        except Exception as e:
            resultados.append({
                "xpath": None,
                "descripcion": f"Error: {str(e)}"
            })

    return {"labels": resultados}
    
    
@app.get("/download_html")
def download_html():
    html = driver.page_source
    return {
        "status": "Código HTML obtenido",
        "length": len(html),
        "html": html
    }
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