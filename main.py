@app.post("/cookies/load")
async def load_cookies():
    try:
        # Leer archivo local con cookies y storages
        with open("telegram_cookies.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        cookies = data.get("cookies", [])
        local_storage = data.get("localStorage", {})
        session_storage = data.get("sessionStorage", {})

        
        # Restaurar cookies HTTP
        applied = 0
        for cookie in cookies:
            if "name" in cookie and "value" in cookie:
                try:
                    driver.add_cookie(cookie)
                    applied += 1
                except Exception:
                    try:
                        driver.add_cookie({"name": cookie["name"], "value": cookie["value"]})
                        applied += 1
                    except Exception as e:
                        log(f"No se pudo añadir cookie {cookie.get('name')}: {e}")

        # Restaurar localStorage
        for k, v in local_storage.items():
            driver.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", k, v)

        # Restaurar sessionStorage
        for k, v in session_storage.items():
            driver.execute_script("window.sessionStorage.setItem(arguments[0], arguments[1]);", k, v)

        # Refrescar la página para que tome efecto
        driver.refresh()

        log(f"Sesión restaurada: {applied} cookies, {len(local_storage)} claves localStorage, {len(session_storage)} claves sessionStorage")
        return {
            "status": "success",
            "applied_cookies": applied,
            "localStorage_keys": len(local_storage),
            "sessionStorage_keys": len(session_storage)
        }
    except Exception as e:
        log(f"Error al restaurar sesión: {e}")
        return {"status": "error", "message": str(e)}