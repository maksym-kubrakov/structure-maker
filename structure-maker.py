import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from selenium_stealth import stealth

def fetch_page_info_selenium(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        driver.get(url)
        time.sleep(2)  # Затримка перед перевіркою
        
        try:
            WebDriverWait(driver, 30).until(
                lambda d: all(phrase not in d.page_source.lower() for phrase in [
                    "just a moment...", "checking your browser", "cloudflare", "captcha", "blocked"
                ])
            )
        except TimeoutException:
            st.warning(f"Block or timeout detected for {url}")
            driver.quit()
            return None

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.text.strip()
                if text and len(text) > 3 and not any(keyword in text.lower() for keyword in ['footer', 'menu', 'nav', 'copyright', 'sign up', 'log in']):
                    headings.append(f"<{tag.upper()}>{text}")

        return "\n".join(headings) if headings else None

    except Exception as e:
        st.warning(f"Error for {url}: {str(e)}")
        return None

def generate_prompt(html_structures):
    competitors_structures = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
    
    prompt = f"""
Створи компактну та оптимізовану SEO-структуру для тексту копірайтингу на основі структур конкурентів.

Конкуренти' структури (враховуй лише релевантні SEO-заголовки з контенту, ігноруй нерелевантні елементи як футери, сайдбари чи навігацію):
{competitors_structures}

Наша структура повинна:
- Врахувати загальний інтент пошуку: аналізуй спільні теми та послідовність заголовків у конкурентів, щоб відповідати користувацьким запитам.
- Бути лаконічною: максимум 5-6 H2, H3 лише для ключових підтем (уникай надмірної деталізації, H4 не використовувати).
- Починатися з H1 (унікальний, але натхненний конкурентами).
- Мати логічну послідовність: вступ, основний контент, висновок, за потреби FAQ.
- Бути SEO-оптимізованою: природне включення ключових слів, привабливі заголовки, чітка ієрархія.
- Уникати дублювання: об'єднуй схожі теми, залишай лише найважливіше.
- Формат:
  H1: [Заголовок]
  Опис: [Короткий опис]

  H2: [Підзаголовок]
  Опис: [Короткий опис]

  H3: [Підпідзаголовок, якщо потрібно]
  Опис: [Короткий опис]

Згенеруй структуру, яка буде релевантною, компактною та кращою за конкурентів за користувацьким досвідом.
"""
    return prompt

st.title("Парсер HTML-структур конкурентів")

urls_input = st.text_area("Вставте URLи (один в лінію):", height=200)

if st.button("Перевірити конкурентів"):
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    html_structures = []
    for url in urls:
        structure = fetch_page_info_selenium(url)
        if structure:
            html_structures.append(structure)
    
    if html_structures:
        st.session_state['html_structures'] = html_structures
        st.session_state['output_structures'] = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
        st.session_state['prompt'] = generate_prompt(html_structures)
        
        st.subheader("HTML-структури конкурентів:")
        st.text_area("Копіюйте звідси:", st.session_state['output_structures'], height=400)
        
        st.subheader("Промт для ТЗ:")
        st.text_area("Копіюйте звідси:", st.session_state['prompt'], height=400)
    else:
        st.error("Не вдалося спарсити жодного конкурента. Можливо, сайти захищені від парсингу.")
