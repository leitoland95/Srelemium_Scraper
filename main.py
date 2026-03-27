import os
import threading
import time
import requests
import base64
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import uvicorn
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi import Body, Form, UploadFile, File, Request
from pydantic import BaseModel, HttpUrl
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import ActionChains
from google import genai
from fastapi.responses import JSONResponse, PlainTextResponse
from openai import OpenAI
from typing import Optional

email = "treyreinger86@gmail.com"
passw = "TreyCaptcha68@#"

app = FastAPI()
execution_logs = []

XPATH_INPUT = "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/div[1]/input[1]"

XPATH_BOTON = "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/p[1]/button[2]"

# Diccionario de elementos disponibles

Iframe_login = {
    1: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]",
    2: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]",
    3: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[3]",
    4: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[4]",
    5: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[5]",
    6: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[6]",
    7: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[7]",
    8: "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[8]"
}

Iframe_dos_cap = {
    1: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]",
    2: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]",
    3: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[3]",
    4: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[4]",
    5: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[5]",
    6: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[6]",
    7: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[7]",
    8: "/html/body/div[1]/div[1]/div[1]/div[1]/div[2]/div[8]"
}

class SecuenciaModel(BaseModel):
    secuencia: list[int]

class SecuenciaRequest(BaseModel):
    secuencia: list[int]
    
class ClickRequest(BaseModel):
    xpath: str    
    
class PromptRequest(BaseModel):
    prompt: str    
    
class ChatRequest(BaseModel):
    messages: list[str]
    image_url: HttpUrl | None = None    
    

# ------------------- INICIALIZAR WEBDRIVER -------------------
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


driver = webdriver.Chrome(options=chrome_options)


# Login Fast
@app.get("/login_fast")
def login_captcha():
  try:
    driver.get("https://2captcha.com")
    
    quick_xpath = "/html[1]/body[1]/div[1]/div[2]/main[1]/div[1]/div[1]/section[1]/div[1]/a[1]"
    elem_1 = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.XPATH,elem_1)))
    driver.execute_script("documents[0].click()",elem_1)
    
    login_xpath = "/html[1]/body[1]/div[1]/main[1]/div[2]/div[1]/div[2]/form[1]/p[1]/a[1]"
    elem_2 = driver.find_element(By.XPATH, login_xpath)
    driver.execute_script("documents[0].click()",elem_2)
    
    email_xpath = "/html[1]/body[1]/div[1]/main[1]/div[2]/div[1]/div[2]/form[1]/p[1]/a[1]"
    elem_3 = driver.find_element(By.XPATH, continue_xpath)
    elem_3.send_keys(email)
    
    passw_xpath = "/html[1]/body[1]/div[1]/main[1]/div[2]/div[1]/div[1]/form[1]/div[4]/div[1]/input[1]"
    elem_4 = driver.find_element(By.XPATH, passw_xpath)
    elem_4.send_keys(passw)
    
    continue_xpath = "/html[1]/body[1]/div[1]/main[1]/div[2]/div[1]/div[1]/form[1]/button[1]"
    elem_5 = driver.find_element(By.XPATH, continue_xpath)
    driver.execute_script("documents[0].click()",elem_5)
    
    return {"status": "Login Realizado con Exito"}
  except Exception as e:
    return {"status": f"error: {str(e)}"}
      
#### Escribir_JS Ingresar solo Texto

@app.post("/escribir_js_general")
def escribir_js(texto: str):
    try: 
        input_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, XPATH_INPUT))
        )
        driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, input_element, texto)
    except Exception as e:
        return {"error al escribir en input: ": e}



##### CAMBIAR DE FRAME BY NAME ##

@app.post("/change_frame")
def change_frame(name: str):
    try:
        driver.switch_to.frame(name)
        log("cambiando de FRAME")
        return {"status": "Cambio Realizado"}
    except Exception as e:
        log("Ocurrió un error al intentar cambiar de FRAME ")
        return {"error":str(e)}



#####. SCRAP IFRAME_X_ID #########

def get_absolute_xpath(driver, element):
    return driver.execute_script("""
    function absoluteXPath(element) {
        if (element.tagName.toLowerCase() == 'html')
            return '/html';
        if (element===document.body)
            return '/html/body';
        var ix= 0;
        var siblings= element.parentNode.childNodes;
        for (var i= 0; i<siblings.length; i++) {
            var sibling= siblings[i];
            if (sibling===element)
                return absoluteXPath(element.parentNode)+'/'+element.tagName.toLowerCase()+'['+(ix+1)+']';
            if (sibling.nodeType===1 && sibling.tagName===element.tagName) {
                ix++;
            }
        }
    }
    return absoluteXPath(arguments[0]);
    """, element)
    
    
@app.get("/scrapear_iframe")
def scrape_iframe():
    driver.switch_to.frame("_2cFrame2")

    # Capturar todos los elementos dentro del iframe
    elements = driver.find_elements(By.XPATH, "//*")

    # Construir la lista con tag, texto y xpath absoluto
    data = []
    for el in elements:
        try:
            xpath = get_absolute_xpath(driver, el)
            data.append({
                "tag": el.tag_name,
                "text": el.text.strip(),
                "xpath": xpath
            })
        except Exception:
            continue

    # Volver al documento principal
    driver.switch_to.default_content()

    return {"iframe_elements": data}    

##############################    

def get_xpath(driver, element):
    return driver.execute_script(
        "function absoluteXPath(element) {"
        "var comp, comps = [];"
        "var xpath = '';"
        "var getPos = function(element) {"
        "var position = 1, curNode;"
        "for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {"
        "if (curNode.nodeName == element.nodeName) {++position;}}"
        "return position;};"
        "for (; element && !(element instanceof Document); element = element.parentNode) {"
        "comp = comps[comps.length] = {};"
        "comp.name = element.nodeName;"
        "comp.position = getPos(element);}"
        "for (var i = comps.length - 1; i >= 0; i--) {"
        "comp = comps[i];"
        "xpath += '/' + comp.name.toLowerCase();"
        "if (comp.position != null) {xpath += '[' + comp.position + ']';}}"
        "return xpath;}"
        "return absoluteXPath(arguments[0]);", element)



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

@app.get("/")
def root():
	return {"status": 200}
	
@app.get("/logs")
def devolver_logs():
    return execution_logs

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
    try:
        elem = driver.find_element(By.XPATH, xpath)
        elem.click()
        log(f"Clic en {xpath}")
        return {"status": "ok"}
    except Exception as e:
        return {"error": f"No se pudo clicar: {e}"}    

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

    driver.get("https://2captcha.com")
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
    
@app.post("/scrap_iframe")    
def obtener_fragmentos_captcha(xpath: str):
    # Cambiar al iframe del captcha
    iframe = driver.find_element(By.XPATH, xpath)
    driver.switch_to.frame(iframe)

    # Capturar todos los nodos dentro del iframe
    fragmentos = driver.find_elements(By.XPATH, "//*")

    # Diccionario para almacenar resultados
    resultado = {}

    # Función auxiliar para obtener XPath absoluto
    def get_xpath(el):
        return driver.execute_script("""
            function absoluteXPath(element) {
                var comp = [];
                while (element !== document.body) {
                    var index = 1;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) break;
                        if (sibling.nodeName === element.nodeName) index++;
                    }
                    comp.unshift(element.nodeName + '[' + index + ']');
                    element = element.parentNode;
                }
                return '/' + comp.join('/');
            }
            return absoluteXPath(arguments[0]);
        """, el)

    # Recorrer elementos y guardar en el diccionario
    for idx, el in enumerate(fragmentos, start=1):
        try:
            resultado[f"elemento_{idx}"] = {
                "tag": el.tag_name,
                "xpath": get_xpath(el),
                "descripcion": el.text.strip()
            }
        except Exception:
            continue

    # Volver al contexto principal
    driver.switch_to.default_content()

    return resultado
    
@app.post("/click_elemento")
def click_secuencia(req: SecuenciaRequest):
    log("Cambiando de iFrame")
    try:
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html[1]/body[1]/div[2]/div[2]/div[1]/iframe[1]"))
        )
        driver.switch_to.frame(iframe)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"No se encontró el iframe: {str(e)}")

    resultados = []
    log("Iniciando Bucle de Secuencia")

    for clave in req.secuencia:
        try:
            xpath_elemento = str(Iframe_login[clave])
            elem_aclicar = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath_elemento))
            )
        except Exception as e:
            log("El Xpath servido no se pudo encontrar en el iFrame actual")
            raise HTTPException(status_code=404, detail=f"No se encontró el elemento {idx}: {str(e)}")

        try:
            driver.execute_script("arguments[0].click();", elem_aclicar)
            resultados.append({"elemento": clave, "accion": "click_js"})
        except WebDriverException as e:
            raise HTTPException(status_code=500, detail=f"No se pudo clicar {clave}: {str(e)}")

        # Espera de 2 segundos entre cada clic, excepto después del último
        
    time.sleep(1)
    try:
        log("Iniciando resolución del Captcha")
        button_confirm = "/DIV[1]/DIV[1]/DIV[1]/DIV[1]/FOOTER[1]/BUTTON[1]"
        elem_confirm= WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_confirm))
            )
        driver.execute_script("arguments[0].click();", elem_confirm)
    except Exception as e:
    	return {"error al clicar confirm: ": e}
    
    driver.switch_to.default_content()
    return {"status": "ok", "resultados": resultados}
            
            
@app.get("/list_iframes")
def list_iframes():
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    result = []
    for idx, iframe in enumerate(iframes):
        try:
            src = iframe.get_attribute("src")
            name = iframe.get_attribute("name")
            # XPath absoluto usando JavaScript
            xpath = driver.execute_script("""
                function absoluteXPath(element) {
                    var comp, comps = [];
                    var parent = null;
                    var xpath = '';
                    var getPos = function(element) {
                        var position = 1, curNode;
                        if (element.nodeType == Node.ATTRIBUTE_NODE) {
                            return null;
                        }
                        for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {
                            if (curNode.nodeName == element.nodeName) {
                                ++position;
                            }
                        }
                        return position;
                    }
                    if (element instanceof Document) {
                        return '/';
                    }
                    for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                        comp = comps[comps.length] = {};
                        switch (element.nodeType) {
                            case Node.TEXT_NODE:
                                comp.name = 'text()';
                                break;
                            case Node.ATTRIBUTE_NODE:
                                comp.name = '@' + element.nodeName;
                                break;
                            case Node.PROCESSING_INSTRUCTION_NODE:
                                comp.name = 'processing-instruction()';
                                break;
                            case Node.COMMENT_NODE:
                                comp.name = 'comment()';
                                break;
                            case Node.ELEMENT_NODE:
                                comp.name = element.nodeName;
                                break;
                        }
                        comp.position = getPos(element);
                    }
                    for (var i = comps.length - 1; i >= 0; i--) {
                        comp = comps[i];
                        xpath += '/' + comp.name.toLowerCase();
                        if (comp.position != null) {
                            xpath += '[' + comp.position + ']';
                        }
                    }
                    return xpath;
                }
                return absoluteXPath(arguments[0]);
            """, iframe)

            result.append({
                "index": idx,
                "src": src,
                "name": name,
                "xpath": xpath
            })
        except Exception as e:
            result.append({"index": idx, "error": str(e)})

    return {"status": "success", "iframes": result}            

@app.post("/switch_iframe")
def switch_iframe(xpath: str = None, index: int = None):
    try:
        if xpath:
            iframe = driver.find_element(By.XPATH, xpath)
            driver.switch_to.frame(iframe)
            return {"status": "success", "message": f"Cambiado al iframe con XPath: {xpath}"}
        elif index is not None:
            driver.switch_to.frame(index)
            return {"status": "success", "message": f"Cambiado al iframe con índice: {index}"}
        else:
            return {"status": "error", "message": "Debes enviar un XPath o un índice"}
    except (NoSuchElementException, NoSuchFrameException) as e:
        return {"status": "error", "message": str(e)}

@app.get("/switch_default")
def switch_default():
    """Regresa al contexto principal (fuera de cualquier iframe)."""
    driver.switch_to.default_content()
    return {"status": "success", "message": "Regresado al contexto principal"}
    
@app.post("/click_actionchains")
def click_actionchains(req: ClickRequest):
    try:
        elem = driver.find_element(By.XPATH, req.xpath)
        actions = ActionChains(driver)
        actions.move_to_element(elem).click().perform()
        return {"status": "ok", "tipo": "click_actionchains", "xpath": req.xpath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))   

@app.post("/click_js")
def click_js(req: ClickRequest):
    try:
        elem = driver.find_element(By.XPATH, req.xpath)
        driver.execute_script("arguments[0].click();", elem)
        return {"status": "ok", "tipo": "click_js", "xpath": req.xpath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/click_touch")
def click_touch(req: ClickRequest):
    try:
        elem = driver.find_element(By.XPATH, req.xpath)
        actions = ActionChains(driver)
        actions.click(elem).perform()
        return {"status": "ok", "tipo": "click_touch", "xpath": req.xpath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        
@app.post("/scrape_iframe_click")
def scrape_iframe_click(req: ClickRequest):
    # 1. Esperar a que el elemento esté listo para clic
    element = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, req.xpath))
    )

    # 2. Ejecutar el click
    element.click()

    # 3. Esperar a que aparezca el iframe
    iframe = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
    )

    # 4. Cambiar contexto al iframe
    driver.switch_to.frame(iframe)

    # 5. Capturar todos los elementos dentro del iframe
    elements = driver.find_elements(By.XPATH, "//*")

    result = []
    for el in elements:
        try:
            xpath = get_xpath(driver, el)
            text = el.text.strip()
            tag = el.tag_name
            result.append({
                "tag": tag,
                "xpath": xpath,
                "descripcion": text
            })
        except Exception:
            continue

    # 6. Volver al documento principal
    driver.switch_to.default_content()

    return {"iframe_elements": result}        
        
@app.post("/chat")
async def chat_endpoint(
    prompt: str = Form(...),
    image_url: Optional[str] = Form(None)
):
    try:
        # Construir mensajes: texto + imagen si existe
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

        if image_url:
            messages[0]["content"].append({"type": "image_url", "image_url": {"url": image_url}})

        response = client_ia.chat.completions.create(
            model="openai/gpt-oss-20b",  # ajusta al modelo que Groq soporte
            messages=messages
        )

        reply = response.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        return {"error": str(e)}

@app.get("/models")
async def list_models():
    try:
        modelos = []
        for m in client.models.list():
            modelos.append({
                "name": m.name,
                "methods": m.supported_methods
            })
        return JSONResponse({"models": modelos})
    except Exception as e:
        return JSONResponse({"error": str(e)})        
        
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Guardar el archivo en el directorio de uploads
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Aquí deberías reemplazar con tu dominio real o IP pública
    public_url = f"https://srelemium-scraper-1.onrender.com/{UPLOAD_DIR}/{file.filename}"
    
    return JSONResponse(content={"url": public_url})

@app.get("/clean_uploads")
async def clean_uploads():
    # Eliminar todo el contenido dentro de la carpeta uploads
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            return PlainTextResponse(f"Error al limpiar la carpeta: {e}", status_code=500)

    return PlainTextResponse("Carpeta Upload ha sido limpiada")
    
@app.post("/escribir_fijo")
def escribir_texto(texto: str):
    try:
        # Esperar a que el input esté presente
        elemento = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, XPATH_INPUT))
        )
        elemento.clear()
        elemento.send_keys(texto)
        requests.post("https://srelemium-scraper-1.onrender.com/click_js",params={"xpath": "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/p[1]/button[2]"})
        return {"status": "ok", "mensaje": f"Texto '{texto}' escrito en el input"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}


@app.post("/escribir_y_click")
def escribir_y_click(texto: str = Query(..., description="Texto a escribir en el input")):
    try:
        # Esperar y obtener el input
        input_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, XPATH_INPUT))
        )

        # Escribir texto mediante JS y disparar eventos
        driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, input_element, texto)

        # Esperar y obtener el botón
        boton_element = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, XPATH_BOTON))
        )

        # Click sencillo con Selenium
        boton_element.click()

        return {"status": "ok", "mensaje": f"Texto '{texto}' escrito y botón clicado"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}

@app.get("/sol_xcap")
def iframe_click():
    try:
        # 1. Cambiar a un iframe predeterminado (ejemplo: primer iframe encontrado)
        iframe = driver.find_element(By.XPATH, "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/div[1]/iframe[1]")
        driver.switch_to.frame(iframe)

        # 2. Click con JavaScript sobre un elemento predeterminado
        element = driver.find_element(By.XPATH, "/html[1]/body[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]")
        driver.execute_script("arguments[0].click();", element)
        time.sleep(1)  # pequeña espera para que se procese el click

        # 3. Salir del iframe
        driver.switch_to.default_content()

        return {"status": "success", "message": "Click ejecutado dentro del iframe y salida realizada"}
    except Exception as e:
        return {"status": "error", "message": str(e)}       
        
        
@app.get("/click_cancelar")
def click_js():
    try:
        xpath_cancelar = "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/p[1]/button[1]"
        elem = driver.find_element(By.XPATH, xpath_cancelar)
        driver.execute_script("arguments[0].click();", elem)
        return {"status": "ok", "tipo": "click_js", "xpath": req.xpath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))        
        
@app.post("/scroll")
async def scroll_page(request: Request):
    try:
        data = await request.json()
        direction = data.get("direction", "down")  # "up" o "down"
        pixels = int(data.get("pixels", 500))      # cantidad de píxeles

        if direction == "up":
            driver.execute_script(f"window.scrollBy(0, -{pixels});")
            return {"status": "success", "message": f"Scrolled up {pixels}px"}
        else:
            driver.execute_script(f"window.scrollBy(0, {pixels});")
            return {"status": "success", "message": f"Scrolled down {pixels}px"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
        
@app.post("/escribir_js")
def escribir_js(xpath: str, texto: str):
    try: 
        input_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        driver.execute_script("""
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, input_element, texto)
    except Exception as e:
        return {"error al escribir en input: ": e}
            

    
@app.post("/dos_cap")
def dos_cap(req: SecuenciaModel):
    try:
        log("Cambiando de IFRAME")
        time.sleep(1)
        driver.switch_to.frame("_2cFrame2")
    except Exception as e:
        log(f"error al cambiar frame: {str(e)}")
        raise HTTPException(status_code=404, detail=f"No se encontró el iframe: {str(e)}")
    
    for clave in req.secuencia:
        log("Intentado clicar elementos")
        try:
            elem_aclicar = driver.find_element(By.XPATH, Iframe_dos_cap[clave])
            elem_aclicar.click()
        except Exception as e:
            log(f"El Xpath servido no se pudo encontrar en el iFrame actual o no se pudo Clicar: {str(e)}")
        time.sleep(1)
            
    try:
        log("Intentando Clicar Confirm")
        button_confirm = "/html/body/div[1]/div[1]/div[1]/div[1]/footer[1]/button[1]"
        elem_confirm= driver.find_element(By.XPATH, button_confirm)
        elem_confirm.click()
    except Exception as e:
        log(f"No se puedo clicar: {str(e)}")
    
    log("saliendo del IFRAME")
    driver.switch_to.default_content()
    
@app.get("/saltar_captcha")
def saltar_captcha():
    respuesta = {"status": 0, "error": "Sin errores de ejecución"}
    runing_err = list[dict]
    xpath_cancel = "/html[1]/body[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/form[1]/p[1]/button[1]"
    
    try:
        elem_cancel = WebDriverWait(driver,10).until(EC.element_to_be_clickable(By.XPATH, elem_cancel))
    except Exception as e:
        log(f"No se encontró el elemento en el frame actual")
        log(f"error: {str(e)}")
        runing_err.append({"1": str(e)})
        
    try:
        driver.execute_script("arguments[0].click();", elem_cancel)
    except Exception as e:
        log(f"Error al intentar clicar el botón")
        log(f"error: {str(e)}")
        runing_err.append({"2": str(e)})
    if len(runing_err) != 0:
        respuesta["status"] = 1
        respuesta["error"] = runing_err
    else:
    	pass
    
    return respuesta
        
    
    
# ------------------- KEEP ALIVE -------------------

def keep_alive():
    url = "https://srelemium-scraper-1.onrender.com"
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