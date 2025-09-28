import streamlit as st
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import traceback

def fetch_page_info_selenium(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        
        try:
            WebDriverWait(driver, 20).until(
                lambda d: "Just a moment..." not in d.page_source and 
                          "Checking your browser before accessing" not in d.page_source
            )
        except TimeoutException:
            driver.quit()
            return None  # Повертаємо None, якщо помилка завантаження

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                headings.append(f"<{tag.upper()}>{heading.text.strip()}")

        return "\n".join(headings) if headings else None

    except Exception as e:
        return None  # Повертаємо None у разі будь-якої помилки

def generate_prompt(html_structures):
    competitors_structures = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
    
    prompt = f"""
Створи оптимізовану SEO-структуру для тексту копірайтингу на основі структур конкурентів. 

Конкуренти' структури (враховуй лише релевантні SEO-заголовки з контенту, ігноруй нерелевантні елементи як футери, сайдбари чи навігацію):
{competitors_structures}

Наша структура повинна:
- Врахувати загальний інтент пошуку: аналізуй спільні теми, послідовність заголовків у конкурентів, щоб структура відповідала користувацьким запитам і була логічною.
- Використовувати лише H2 та H3 (рідко H4, тільки якщо це необхідно для глибокої деталізації підрозділу).
- Починатися з H1 (головний заголовок), який має бути унікальним, але натхненним конкурентами.
- Мати логічну послідовність: вступні розділи, основний контент, висновки, FAQ тощо, якщо це пасує до інтенту.
- Оптимізувати для SEO: включати ключові слова природно в заголовки, робити їх привабливими для кліків, забезпечувати ієрархію (H3 під H2).
- Бути всебічною: охоплювати всі ключові аспекти теми, базуючись на конкурентах, але додавати унікальні елементи для диференціації.
- Враховувати довжину: структура повинна підтримувати достатній обсяг тексту (орієнтуйся на середній word count конкурентів, але не вказуй його тут).
- Уникати дублювання: комбінуй подібні розділи, роби структуру стислою, але інформативною.
- Формат: 
  H1: [Заголовок]
  Опис: [Короткий опис, про що описати в цьому розділі]

  H2: [Підзаголовок]
  Опис: [Короткий опис]

  H3: [Підпідзаголовок]
  Опис: [Короткий опис]

  І так далі.

Згенеруй структуру, яка буде кращою за конкурентів за релевантністю, повнотою та користувацьким досвідом.
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
        
        st.text_area("HTML-структури конкурентів:", st.session_state['output_structures'], height=400)
    else:
        st.error("Не вдалося спарсити жодного конкурента.")

if 'output_structures' in st.session_state:
    if st.button("Скопіювати HTML-структури"):
        pyperclip.copy(st.session_state['output_structures'])
        st.success("HTML-структури скопійовано в буфер обміну!")

    if st.button("Скопіювати промт"):
        pyperclip.copy(st.session_state['prompt'])
        st.success("Промт скопійовано в буфер обміну!")

st.info("Ця програма розгорнута на Streamlit. Для релізу на streamlit.app, завантажте цей код на GitHub і налаштуйте репозиторій для Streamlit sharing.")