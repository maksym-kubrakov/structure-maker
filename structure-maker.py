import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import os
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# === Перевірка: чи є Selenium доступний (тільки локально) ===
def is_selenium_available():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options
        return True
    except:
        return False

# === Selenium парсер (тільки локально) ===
def fetch_with_selenium(url):
    if not is_selenium_available():
        return None

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        driver.get(url)

        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        return extract_headings(soup, url)
    except Exception as e:
        st.warning(f"Selenium помилка ({url}): {str(e)[:80]}...")
        return None

# === Requests парсер (працює на Streamlit Cloud) ===
def fetch_with_requests(url):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504, 429])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    try:
        time.sleep(1.5)
        response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()

        # Антибот перевірка
        text = response.text.lower()
        if any(block in text for block in ['cloudflare', 'captcha', 'blocked', 'just a moment', 'access denied', 'checking your browser']):
            st.warning(f"Cloudflare/антибот для {url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        return extract_headings(soup, url)

    except Exception as e:
        st.warning(f"Requests помилка ({url}): {str(e)[:80]}...")
        return None

# === Витяг заголовків (одна функція для обох методів) ===
def extract_headings(soup, url):
    headings = []
    for tag in ['h2', 'h3', 'h4']:
        for heading in soup.find_all(tag):
            text = heading.get_text(strip=True)
            if (text and len(text) > 3 and
                not any(kw in text.lower() for kw in ['footer', 'menu', 'nav', 'copyright', 'sign up', 'log in', 'cookie', 'privacy'])):
                headings.append(f"<{tag.upper()}>{text}")
    return "\n".join(headings) if headings else "No relevant headings"

# === Універсальний парсер ===
def fetch_page_info(url):
    # Спроба 1: Selenium (тільки локально)
    if os.getenv("STREAMLIT_CLOUD") != "true":  # або просто завжди пробувати
        result = fetch_with_selenium(url)
        if result:
            return result

    # Спроба 2: Requests (завжди)
    return fetch_with_requests(url)

# === Генерація промпту ===
def generate_prompt(html_structures):
    competitors = "\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(html_structures)])
    return f"""
Створи компактну та оптимізовану SEO-структуру для тексту копірайтингу на основі структур конкурентів.

Конкуренти' структури:
{competitors}

Наша структура повинна:
- Бути лаконічною: максимум 5-6 H2, H3 рідко.
- Починатися з H2.
- Логічна послідовність: вступ → основа → підсумок.
- SEO: природні ключі, привабливі заголовки.
- Без FAQ, без дублів.

Вивід — таблиця:

| Заголовок | О чем описать |
|----------|----------------|
| H2: ...  | ...            |
...
"""

def generate_default_prompt():
    return """
| Заголовок | О чем описать |
|----------|----------------|
| <H2> Що таке казино без верифікації | Визначення, як працює, відмінності від звичайних |
| <H2> Переваги анонімної гри | Швидкість, конфіденційність, доступність |
| <H2> Ризики та недоліки | Безпека, ліміти, шахрайство |
| <H2> Як обрати надійне казино | Ліцензія, відгуки, методи оплати |
| <H2> Підсумок | Кому підходить, основні висновки |
"""

# === Streamlit UI ===
st.set_page_config(page_title="SEO Парсер", layout="wide")
st.title("Парсер структур конкурентів")

# Авто-детект: чи це Streamlit Cloud
is_cloud = os.getenv("STREAMLIT_CLOUD") or "streamlit.io" in os.getenv("SERVER_NAME", "")

if is_cloud:
    st.warning("На Streamlit Cloud працює **requests** (Selenium недоступний). Для повного парсингу — запускай **локально**.")
else:
    st.success("Локальний запуск — використовується **Selenium** (обходить Cloudflare)")

urls_input = st.text_area("Введіть URLи (по одному на рядок):", height=150)

if st.button("Перевірити конкурентів", type="primary"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    if not urls:
        st.error("Введіть URLи")
        st.stop()

    results = []
    progress = st.progress(0)
    status_container = st.empty()

    for i, url in enumerate(urls):
        status_container.info(f"Парсимо {i+1}/{len(urls)}: {url}")
        structure = fetch_page_info(url)
        if structure:
            results.append(structure)
        time.sleep(1)
        progress.progress((i + 1) / len(urls))

    status_container.empty()

    if results:
        output = "\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(results)])
        prompt = generate_prompt(results)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Структури конкурентів")
            st.code(output, language="text")
        with col2:
            st.subheader("Промпт для ТЗ")
            st.code(prompt, language="markdown")
    else:
        st.error("Не вдалося отримати жодної структури.")
        st.subheader("Базовий шаблон")
        st.code(generate_default_prompt(), language="markdown")
