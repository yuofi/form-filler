import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)

def fetch_page_source(url: str) -> tuple[str, str]:
    """
    Использует Selenium для получения HTML-кода страницы, включая динамически загружаемые элементы, и текущего URL.
    
    :param url: URL страницы, которую нужно загрузить.
    :return: HTML-код страницы и текущий URL после редиректа.
    """
    options = Options()
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service('C:\\Program Files\\chromedriver\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        logging.info(f"Открываем URL: {url}")
        driver.get(url)
        time.sleep(2) 
        html = driver.page_source
        current_url = driver.current_url 
        return html, current_url
    finally:
        driver.quit()