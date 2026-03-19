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