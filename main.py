import os
import threading
import time
import requests
import base64
import json
from pathlib import Path
from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import uvicorn

app = FastAPI()

execution_logs = []
current_url = None  # Guardará la última URL navegada

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    execution_logs.append(entry)

# --- Configuración de Selenium (User-Agent móvil proporcionado por el usuario) ---
mobile_user_agent = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36"
)

chrome_options = Options()
# Si quieres ver el navegador en un entorno con GUI, quita --headless
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"user-agent={mobile_user_agent}")
# Opcional: emulación de dispositivo (ajusta si lo deseas)
# mobile_emulation = {"deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 3.0}}
# chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

driver = webdriver.Chrome(options=chrome_options)

# Ruta donde se guardarán las cookies en el servidor (y nombre por defecto)
COOKIES_FILE = Path("cookies.json")

def save_cookies_to_file(path: Path = COOKIES_FILE):
    cookies = driver.get_cookies()
    with open(path, "w") as f:
        json.dump(cookies, f)
    log(f"Cookies exportadas a {path}")

def load_cookies_from_file(path: Path = COOKIES_FILE):
    if path.exists():
        with open(path, "r") as f:
            cookies = json.load(f)
        driver.delete_all_cookies()
        for cookie in cookies:
            # Selenium requiere al menos 'name' y 'value'
            if "name" in cookie and "value" in cookie:
                # Eliminar campos que a veces causan problemas al reinsertar
                cookie_to_add = {k: cookie[k] for k in cookie if k in ("name", "value", "domain", "path", "expiry", "secure", "httpOnly")}
                try:
                    driver.add_cookie(cookie_to_add)
                except Exception:
                    # Intentar añadir sin domain/path si falla
                    minimal = {"name": cookie["name"], "value": cookie["value"]}
                    try:
                        driver.add_cookie(minimal)
                    except Exception as e:
                        log(f"No se pudo añadir cookie {cookie.get('name')}: {e}")
        log(f"Cookies cargadas desde {path}")
        return True
    else:
        log(f"No se encontró archivo de cookies en {path}")
        return False

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
    except Exception:
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

# -------------------- Endpoints --------------------

@app.post("/navigate")
async def navigate(request: Request):
    global current_url
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}
    try:
        driver.get(url)
        current_url = url
        log(f"Navegación a {url} completada")
        return {"status": "success", "url": url}
    except Exception as e:
        log(f"Error al navegar a {url}: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/scrape")
async def scrape():
    if not current_url:
        return {"error": "No URL set. Use /navigate first."}

    log(f"Scraping en {current_url}")
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"))
        )
    except Exception:
        return {"botones": {}, "cajas_texto": {}, "html": driver.page_source}

    botones = {}
    cajas_texto = {}

    for el in driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']"):
        if el.is_displayed():
            key = el.get_attribute("id") or el.get_attribute("name") or f"boton_{len(botones)+1}"
            botones[key] = element_info(el)

    for el in driver.find_elements(By.XPATH, "//input | //textarea | //*[@contenteditable='true']"):
        if el.is_displayed():
            key = el.get_attribute("id") or el.get_attribute("name") or f"input_{len(cajas_texto)+1}"
            cajas_texto[key] = element_info(el)

    return {
        "botones": botones,
        "cajas_texto": cajas_texto,
        "html": driver.page_source
    }

@app.post("/xpaths")
async def get_xpaths():
    if not current_url:
        return {"error": "No URL set. Use /navigate first."}

    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"))
        )
    except Exception:
        return {"xpaths": []}

    elementos = []
    for el in driver.find_elements(By.XPATH, "//button | //input | //textarea | //*[@contenteditable='true']"):
        if el.is_displayed():
            xp = build_xpath(el)
            if xp:
                texto = el.text.strip() if el.text else None
                if not texto:
                    texto = el.get_attribute("placeholder") or el.get_attribute("value") or ""
                elementos.append({"xpath": xp, "texto": texto})

    return {"elementos": elementos}

@app.post("/click")
async def click_element(request: Request):
    data = await request.json()
    xpath = data.get("xpath")
    if not xpath:
        return {"error": "No XPath provided"}

    try:
        el = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
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
        el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
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

# --- ENDPOINTS PARA COOKIES ---
@app.get("/cookies/export")
async def export_cookies():
    try:
        cookies = driver.get_cookies()
        return {"status": "success", "cookies": cookies}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/cookies/load")
async def load_cookies():
    try:
        local_path = Path("cookies.json")
        cookies = None
        source = None

        # 1. Intentar leer archivo local en el servidor (Render)
        if local_path.exists():
            with open(local_path, "r") as f:
                cookies = json.load(f)
            source = "local"
            log("Cookies cargadas desde archivo local en servidor")
        else:
            # 2. Si no existe, intentar leer COOKIES_FILE (por si se guardó con otro nombre)
            if COOKIES_FILE.exists():
                with open(COOKIES_FILE, "r") as f:
                    cookies = json.load(f)
                source = "local"
                log(f"Cookies cargadas desde {COOKIES_FILE}")
            else:
                # 3. Si no existe local, descargar desde tu repo remoto (raw GitHub)
                repo_url = "https://raw.githubusercontent.com/tu_usuario/tu_repo/main/telegram_cookies.json"
                resp = requests.get(repo_url, timeout=15)
                if resp.status_code == 200:
                    cookies = resp.json()
                    source = "remote"
                    log("Cookies descargadas desde repo remoto")
                else:
                    log(f"No se pudo descargar cookies desde repo remoto: {resp.status_code}")
                    return {"status": "error", "message": f"No se pudo descargar cookies: {resp.status_code}"}

        # Aplicar cookies en Selenium
        driver.delete_all_cookies()
        applied = 0
        for cookie in cookies:
            if "name" in cookie and "value" in cookie:
                cookie_to_add = {k: cookie[k] for k in cookie if k in ("name", "value", "domain", "path", "expiry", "secure", "httpOnly")}
                try:
                    driver.add_cookie(cookie_to_add)
                    applied += 1
                except Exception:
                    try:
                        driver.add_cookie({"name": cookie["name"], "value": cookie["value"]})
                        applied += 1
                    except Exception as e:
                        log(f"No se pudo añadir cookie {cookie.get('name')}: {e}")

        # Refrescar la página para que las cookies tomen efecto
        if current_url:
            try:
                driver.refresh()
            except Exception as e:
                log(f"Error al refrescar después de cargar cookies: {e}")

        return {"status": "success", "source": source, "applied_cookies": applied}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/cookies/clear")
async def clear_cookies():
    try:
        driver.delete_all_cookies()
        # Intentar eliminar archivos locales si existen
        removed = []
        try:
            if COOKIES_FILE.exists():
                COOKIES_FILE.unlink()
                removed.append(str(COOKIES_FILE))
        except Exception as e:
            log(f"No se pudo eliminar {COOKIES_FILE}: {e}")

        # Intentar eliminar archivo con nombre alternativo
        alt = Path("/storage/emulated/0/Documents/telegram_cookies.json")
        try:
            if alt.exists():
                alt.unlink()
                removed.append(str(alt))
        except Exception as e:
            log(f"No se pudo eliminar {alt}: {e}")

        log("Cookies borradas y archivos eliminados si existían")
        return {"status": "success", "removed_files": removed}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/logs")
async def get_logs():
    return {"logs": execution_logs}

@app.post("/refresh")
async def refresh_page():
    try:
        driver.refresh()
        log("Página refrescada con driver.refresh()")
        return {"status": "success", "message": "Página refrescada"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scroll")
async def scroll_page(request: Request):
    try:
        data = await request.json()
        direction = data.get("direction", "down")  # "up" o "down"
        pixels = int(data.get("pixels", 500))      # cantidad de píxeles
        xpath = data.get("xpath")                  # opcional: scroll hasta un elemento

        if xpath:
            el = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'nearest'});", el)
            log(f"Scroll hacia elemento {xpath}")
            return {"status": "success", "message": f"Scrolled to element {xpath}"}
        else:
            if direction == "up":
                driver.execute_script(f"window.scrollBy(0, -{pixels});")
                log(f"Scroll hacia arriba {pixels}px")
                return {"status": "success", "message": f"Scrolled up {pixels}px"}
            else:
                driver.execute_script(f"window.scrollBy(0, {pixels});")
                log(f"Scroll hacia abajo {pixels}px")
                return {"status": "success", "message": f"Scrolled down {pixels}px"}
    except Exception as e:
        log(f"Error en scroll: {e}")
        return {"status": "error", "message": str(e)}

# --- Keep Alive (opcional para Render u otros hosts) ---
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        log("No se encontró RENDER_EXTERNAL_URL, keep_alive desactivado")
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