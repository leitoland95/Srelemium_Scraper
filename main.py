from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import uvicorn

app = FastAPI()

# Inicializar Selenium al arrancar
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

@app.post("/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "No URL provided"}

    driver.get(url)

    # Agrupar elementos por categorías
    elements = {
        "inputs": [el.get_attribute("xpath") for el in driver.find_elements(By.XPATH, "//input")],
        "buttons": [el.get_attribute("xpath") for el in driver.find_elements(By.XPATH, "//button")],
        "links": [el.get_attribute("xpath") for el in driver.find_elements(By.XPATH, "//a")],
        "divs": [el.get_attribute("xpath") for el in driver.find_elements(By.XPATH, "//div")],
        "spans": [el.get_attribute("xpath") for el in driver.find_elements(By.XPATH, "//span")],
    }

    # Si el atributo xpath no existe, lo generamos manualmente
    def build_xpath(el):
        try:
            return driver.execute_script(
                "function absoluteXPath(element){"
                "var comp, comps = [];"
                "var parent = null;"
                "var xpath = '';"
                "var getPos = function(element){"
                "var position = 1, curNode;"
                "if (element.nodeType == Node.ATTRIBUTE_NODE){"
                "return null;"
                "}"
                "for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling){"
                "if (curNode.nodeName == element.nodeName){"
                "++position;"
                "}"
                "}"
                "return position;"
                "};"
                "if (element instanceof Document){return '/';}"
                "for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode){"
                "comp = comps[comps.length] = {};"
                "switch (element.nodeType){"
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
                "for (var i = comps.length - 1; i >= 0; i--){"
                "comp = comps[i];"
                "xpath += '/' + comp.name.toLowerCase();"
                "if (comp.position !== null){"
                "xpath += '[' + comp.position + ']';"
                "}"
                "}"
                "return xpath;"
                "} return absoluteXPath(arguments[0]);", el)
        except:
            return None

    # Reemplazar los None con XPaths calculados
    for category, els in elements.items():
        new_list = []
        for el in driver.find_elements(By.XPATH, f"//{category[:-1]}") if category != "links" else driver.find_elements(By.XPATH, "//a"):
            new_list.append(build_xpath(el))
        elements[category] = new_list

    return {"url": url, "elements": elements}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)