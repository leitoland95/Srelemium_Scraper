from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uvicorn
import threading
import time
import requests
import os

app = FastAPI()

# --- Logs globales ---
execution_logs = []

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    execution_logs.append(entry)

# Inicializar Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

log("Inicializando driver de Chrome en modo headless")
driver = webdriver.Chrome(options=chrome_options)

def build_xpath(el):
    try:
        xpath = driver.execute_script(
            "function absoluteXPath(element){"
            "var comp, comps = [];"
            "var xpath = '';"
            "var getPos = function(element){"
            "var position = 1, curNode;"
            "if (element.nodeType == Node.ATTRIBUTE_NODE){return null;}"
            "for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){"
            "if (curNode.nodeName == element.nodeName){++position;}}"
            "return position;};"
            "if (element instanceof Document){return '/';}"
            "for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode){"
            "comp = comps[comps.length] = {};"
            "switch (element.nodeType){"
            "case Node.TEXT_NODE: comp.name = 'text()'; break;"
            "case Node.ATTRIBUTE_NODE: comp.name = '@' + element.nodeName; break;"
            "case Node.ELEMENT_NODE: comp.name = element.nodeName; break;}"
            "comp.position = getPos(element);}"
            "for (var i = comps.length - 1; i >= 0; i--){"
            "comp = comps[i];"
            "xpath += '/' + comp.name.toLowerCase();"
            "if (comp.position !== null){xpath += '[' + comp.position + ']';}}"
            "return xpath;} return absoluteXPath(arguments[0]);", el)
        return xpath
    except Exception as e:
        log(f"Error generando XPath: {e}")
        return None

@app.post("/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        log("Error: no se proporcionó URL")
        return {"error": "No URL provided"}

    log(f"Navegando a {url}")
    driver.get(url)

    # Esperar elementos dinámicos
    try:
        log("Esperando elementos dinámicos...")
        WebDriverWait(driver, 80).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"))
        )
        log("Elementos detectados en el DOM")
    except:
        log("Timeout: no se encontraron elementos")
        return {"botones": {}, "cajas_texto": {}}

    botones = {}
    cajas_texto = {}

    # Botones
    log("Buscando botones...")
    for el in driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']"):
        key = el.get_attribute("id") or el.get_attribute("name") or f"sin_atributo_{len(botones)+1}"
        botones[key] = build_xpath(el)
        log(f"Botón encontrado: clave={key}, xpath={botones[key]}")

    # Cajas de texto
    log("Buscando cajas de texto...")
    for el in driver.find_elements(By.XPATH, "//input | //textarea | //*[@contenteditable='true']"):
        key = el.get_attribute("id") or el.get_attribute("name") or f"sin_atributo_{len(cajas_texto)+1}"
        cajas_texto[key] = build_xpath(el)
        log(f"Input encontrado: clave={key}, xpath={cajas_texto[key]}")

    log("Scraping finalizado")
    return {
        "botones": botones,
        "cajas_texto": cajas_texto
    }

@app.get("/logs")
async def get_logs():
    return {"logs": execution_logs}

# --- Keep Alive ---
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        log("No se encontró RENDER_EXTERNAL_URL, keep_alive desactivado")
        return
    while True:
        try:
            requests.get(url)
            log(f"Ping a {url} para mantener vivo el servicio")
        except Exception as e:
            log(f"Error en keep_alive: {e}")
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)