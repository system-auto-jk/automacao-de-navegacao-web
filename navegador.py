
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os, shutil, subprocess, re

def _versao_chrome_local():
    try:
        out = subprocess.check_output(
            r'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version',
            shell=True, text=True
        )
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
        return m.group(1) if m else None
    except Exception:
        return None

def iniciar_navegador(headless: bool=False):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--log-level=3")
    if headless:
        options.add_argument("--headless=new")

    os.environ["WDM_LOG_LEVEL"] = "0"
    os.environ["WDM_ARCHITECTURE"] = "x64"

    versao = _versao_chrome_local()
    print(f"🔍 Chrome detectado: {versao or 'não identificado'} (x64)")

    try:
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print("⚠️ Falha inicial:", e)
        print("🔄 Reinstalando ChromeDriver compatível...")
        try:
            wdm_cache = os.path.expanduser("~/.wdm")
            if os.path.exists(wdm_cache):
                try: shutil.rmtree(wdm_cache)
                except Exception: pass
            driver_path = ChromeDriverManager().install()
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e2:
            raise RuntimeError(f"❌ Falha ao iniciar Chrome automaticamente: {e2}")
