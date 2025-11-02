import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os

# === Налаштування Selenium для Streamlit Cloud ===
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

    # Для Streamlit Cloud — використовуємо webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Приховуємо, що це автоматизація
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
    return driver

# === Парсинг сторінки через Selenium ===
def fetch_page_info_selenium(url):
    driver = None
    try:
        driver = get_driver()
        driver.get(url)

        # Чекаємо, поки завантажиться хоча б body
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Додаткова пауза для JS

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Перевірка на блокування
        page_text = page_source.lower()
        if any(phrase in page_text for phrase in ['cloudflare', 'captcha', 'blocked', 'just a moment', 'access denied']):
            st.warning(f"Блокування виявлено для {url} (Cloudflare/антибот)")
            return None

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.text.strip()
                if (text and len(text) > 3 and 
                    not any(keyword in text.lower() for keyword in ['footer', 'menu', 'nav', 'copyright', 'sign up', 'log in', 'cookie'])):
                    headings.append(f"<{tag.upper()}>{text}")

        return "\n".join(headings) if headings else "No relevant headings found"

    except Exception as e:
        st.warning(f"Помилка для {url}: {str(e)[:100]}...")
        return None
    finally:
        if driver:
            driver.quit()

# === Генерація промпту ===
def generate_prompt(html_structures):
    competitors_structures = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
    
    prompt = f"""
Створи компактну та оптимізовану SEO-структуру для тексту копірайтингу на основі структур конкурентів.

Конкуренти' структури (враховуй лише релевантні SEO-заголовки з контенту, ігноруй нерелевантні елементи як футери, сайдбари чи навігацію):
{competitors_structures}

Наша структура повинна:
- Врахувати загальний інтент пошуку: аналізуй спільні теми та послідовність заголовків у конкурентів, щоб відповідати користувацьким запитам.
- Бути лаконічною: максимум 5-6 H2, H3 лише для ключових підтем (H4 можна використовувати, але це буде рідкістю).
- Починатися з H2 (без H1).
- Мати логічну послідовність: вступ, основний контент, підсумки.
- Бути SEO-оптимізованою: природне включення ключових слів, привабливі заголовки, чітка ієрархія.
- Уникати дублювання: об'єднуй схожі теми, залишай лише найважливіше.
- Не додавай FAQ

Згенеруй структуру у вигляді таблиці з колонками "Заголовок" і "О чем описать", де заголовки (H2, H3, H4) вказані в рядках.

Приклад таблиці:
| Заголовок        | О чем описать                    |
|------------------|-----------------------------------|
| H2: ……          | ……                               |
| H2: ……          | ……                               |
| H3: ……          | ……                               |
| H3: ……          | ……                               |
| H2: ……          | ……                               |

Згенеруй таблицю, яка буде релевантною, компактною та кращою за конкурентів за користувацьким досвідом.
"""
    return prompt

def generate_default_prompt():
    return """
Створи компактну та оптимізовану SEO-структуру для тексту копірайтингу на тему "онлайн-казино без верифікації".

Наша структура повинна:
- Бути лаконічною: максимум 5-6 H2, H3 лише для ключових підтем (H4 можна використовувати, але це буде рідкістю).
- Починатися з H2 (без H1).
- Мати логічну послідовність: вступ, основний контент, підсумки.
- Бути SEO-оптимізованою: природне включення ключових слів (наприклад, "казино без верифікації", "анонімні казино"), привабливі заголовки, чітка ієрархія.
- Уникати дублювання: об'єднуй схожі теми, залишай лише найважливіше.

Згенеруй структуру у вигляді таблиці з колонками "Заголовок" і "О чем описать", де заголовки (H2, H3, H4) вказані в рядках.

Приклад таблиці:
| Заголовок        | О чем описать                    |
|------------------|-----------------------------------|
| <H2> Що таке казино без верифікації | Визначення та особливості казино без підтвердження особи |
| <H2> Переваги гри без верифікації  | Швидкість, анонімність, простота |
| <H2> Ризики та обмеження           | Потенційні проблеми з безпекою та лімітами |
| <H2> Методи платежів               | Огляд криптовалют, карток, гаманців |
| <H2> Як обрати надійне казино      | Критерії вибору: ліцензія, відгуки |
| <H2> Підсумки                       | Короткий огляд переваг і ризиків |
"""

# === Streamlit UI ===
st.set_page_config(page_title="SEO Структура Конкурентів", layout="wide")
st.title("Парсер HTML-структур конкурентів (Selenium)")

st.info("Використовується **Selenium + Chrome** — обходить Cloudflare, JS, антиботи")

urls_input = st.text_area("Вставте URLи (один в лінію):", height=200, placeholder="https://example.com/page1\nhttps://example.com/page2")

if st.button("Перевірити конкурентів", type="primary"):
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    
    if not urls:
        st.error("Введіть хоча б один URL")
    else:
        with st.spinner(f"Парсимо {len(urls)} сайтів..."):
            html_structures = []
            successful = 0
            for i, url in enumerate(urls):
                with st.status(f"Парсимо {i+1}/{len(urls)}: {url}") as status:
                    structure = fetch_page_info_selenium(url)
                    if structure:
                        html_structures.append(structure)
                        successful += 1
                        status.update(label=f"Успішно: {url}", state="complete")
                    else:
                        status.update(label=f"Пропущено: {url}", state="error")
                    time.sleep(1)  # Пауза між запитами

            if html_structures:
                st.session_state['html_structures'] = html_structures
                st.session_state['output_structures'] = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
                st.session_state['prompt'] = generate_prompt(html_structures)

                st.success(f"Успішно спаршено {successful} з {len(urls)} сайтів")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("HTML-структури конкурентів:")
                    st.text_area("Копіюйте звідси:", st.session_state['output_structures'], height=400, key="structures")

                with col2:
                    st.subheader("Промт для ТЗ:")
                    st.text_area("Копіюйте звідси:", st.session_state['prompt'], height=400, key="prompt")

            else:
                st.error("Не вдалося спарсити жодного конкурента.")
                st.subheader("Базовий промпт для ТЗ:")
                st.text_area("Копіюйте звідси:", generate_default_prompt(), height=400)
