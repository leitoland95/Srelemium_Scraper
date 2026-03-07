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
import base64

app = FastAPI()

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

driver = webdriver.Chrome(options=chrome_options)

def build_xpath(el):
    try:
        return driver.execute_script(
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
    except:
        return None

def element_info(el):
    return {
        "xpath": build_xpath(el),
        "id": el.get_attribute("id"),
        "name": el.get_attribute("name"),
        "class": el.get_attribute("class"),
        "placeholder": el.get_attribute("placeholder"),
        "text": el.text.strip() if el.text else None
    }

@app.post("/navigate")
async def navigate(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}
    try:
        driver.get(url)
        log(f"Navegación a {url} completada")
        return {"status": "success", "url": url}
    except Exception as e:
        log(f"Error al navegar a {url}: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        log("Error: no se proporcionó URL")
        return {"error": "No URL provided"}

    log(f"Navegando a {url}")
    driver.get(url)

    try:
        log("Esperando elementos dinámicos...")
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"))
        )
        log("Elementos detectados en el DOM")
    except:
        log("Timeout: no se encontraron elementos")
        return {"botones": {}, "cajas_texto": {}, "html": driver.page_source}

    botones = {}
    cajas_texto = {}

    # Botones visibles
    log("Buscando botones...")
    for el in driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']"):
        if not el.is_displayed():
            continue
        key = el.get_attribute("id") or el.get_attribute("name") or f"boton_{len(botones)+1}"
        botones[key] = element_info(el)

    # Inputs visibles
    log("Buscando cajas de texto...")
    for el in driver.find_elements(By.XPATH, "//input | //textarea | //*[@contenteditable='true']"):
        if not el.is_displayed():
            continue
        key = el.get_attribute("id") or el.get_attribute("name") or f"input_{len(cajas_texto)+1}"
        cajas_texto[key] = element_info(el)

    html_code = driver.page_source
    log("Scraping finalizado")
    
    return {
        "botones": botones,
        "cajas_texto": cajas_texto,
        "html": html_code
    }

@app.post("/xpaths")
async def get_xpaths(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}

    driver.get(url)
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"))
        )
    except:
        return {"xpaths": []}

    xpaths = []
    for el in driver.find_elements(By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                xpaths.append(xp)

    return {"xpaths": xpaths}

@app.post("/click")
async def click_element(request: Request):
    data = await request.json()
    xpath = data.get("xpath")
    if not xpath:
        return {"error": "No XPath provided"}

    try:
        el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        el.click()
        log(f"Clic ejecutado en {xpath}")
        return {"status": "success", "xpath": xpath}
    except Exception as e:
        log(f"Error al hacer clic en {xpath}: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/type")
async def type_text(request: Request):
    data = await request.json()
    xpath = data.get("xpath")
    text = data.get("text")
    if not xpath or text is None:
        return {"error": "XPath y texto son requeridos"}

    try:
        el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        el.clear()
        el.send_keys(text)
        log(f"Texto '{text}' escrito en {xpath}")
        return {"status": "success", "xpath": xpath, "text": text}
    except Exception as e:
        log(f"Error al escribir en {xpath}: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/screenshot")
async def screenshot():
    try:
        png_bytes = driver.get_screenshot_as_png()
        encoded = base64.b64encode(png_bytes).decode("utf-8")
        log("Captura de pantalla realizada")
        return {"status": "success", "screenshot_base64": encoded}
    except Exception as e:
        log(f"Error al capturar pantalla: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/logs")
async def get_logs():
    return {"logs": execution_logs}

# --- Keep Alive ---
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        print("No se encontró RENDER_EXTERNAL_URL, keep_alive desactivado")
        return
    while True:
        try:
            requests.get(url)
            print(f"Ping a {url} para mantener vivo el servicio")
        except Exception as e:
            print(f"Error en keep_alive: {e}")
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)