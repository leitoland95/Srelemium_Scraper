from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import uvicorn
import threading
import time
import requests
import os

app = FastAPI()

# Inicializar Selenium al arrancar
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
            "case Node.PROCESSING_INSTRUCTION_NODE: comp.name = 'processing-instruction()'; break;"
            "case Node.COMMENT_NODE: comp.name = 'comment()'; break;"
            "case Node.ELEMENT_NODE: comp.name = element.nodeName; break;}"
            "comp.position = getPos(element);}"
            "for (var i = comps.length - 1; i >= 0; i--){"
            "comp = comps[i];"
            "xpath += '/' + comp.name.toLowerCase();"
            "if (comp.position !== null){xpath += '[' + comp.position + ']';}}"
            "return xpath;} return absoluteXPath(arguments[0]);", el)
    except:
        return None

@app.post("/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}

    driver.get(url)

    botones = {}
    cajas_texto = {}

    # Botones: <button>, <input type="button">, <input type="submit">
    for el in driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']"):
        key = el.get_attribute("id") or el.get_attribute("name") or f"sin_atributo_{len(botones)+1}"
        botones[key] = build_xpath(el)

    # Cajas de texto: todos los <input> y <textarea>
    for el in driver.find_elements(By.XPATH, "//input | //textarea"):
        key = el.get_attribute("id") or el.get_attribute("name") or f"sin_atributo_{len(cajas_texto)+1}"
        cajas_texto[key] = build_xpath(el)

    return {
        "botones": botones,
        "cajas_texto": cajas_texto
    }

# --- Keep Alive ---
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")  # Render expone esta variable con tu dominio
    if not url:
        print("No se encontró RENDER_EXTERNAL_URL, keep_alive desactivado")
        return
    while True:
        try:
            requests.get(url)
            print(f"Ping a {url} para mantener vivo el servicio")
        except Exception as e:
            print(f"Error en keep_alive: {e}")
        time.sleep(60)  # cada 60 segundos

# Lanzar el hilo de keep_alive
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)