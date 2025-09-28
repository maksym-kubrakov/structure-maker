import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_page_info_requests(url):
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    try:
        time.sleep(1)
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        time.sleep(2)

        if any(phrase in response.text.lower() for phrase in ['cloudflare', 'captcha', 'blocked', 'just a moment', 'access denied']):
            st.warning(f"Block detected for {url}: possible anti-bot protection")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.text.strip()
                if (text and len(text) > 3 and 
                    not any(keyword in text.lower() for keyword in ['footer', 'menu', 'nav', 'copyright', 'sign up', 'log in'])):
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
- Бути лаконічною: максимум 5-6 H2, H3 лише для ключових підтем (H4 можна використовувати, але це буде рідкістю).
- Починатися з H2 (без H1).
- Мати логічну послідовність: вступ, основний контент, підсумки.
- Бути SEO-оптимізованою: природне включення ключових слів, привабливі заголовки, чітка ієрархія.
- Уникати дублювання: об'єднуй схожі теми, залишай лише найважливіше.
- Формат:
  H2: [Підзаголовок]
  Опис: [Короткий опис]

  H3: [Підпідзаголовок, якщо потрібно]
  Опис: [Короткий опис]

Згенеруй структуру, яка буде релевантною, компактною та кращою за конкурентів за користувацьким досвідом.
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
- Формат:
  H2: [Підзаголовок]
  Опис: [Короткий опис]

  H3: [Підпідзаголовок, якщо потрібно]
  Опис: [Короткий опис]

Приклад структури:
  H2: Що таке казино без верифікації
  Опис: Визначення та особливості казино без підтвердження особи.

  H2: Переваги гри без верифікації
  Опис: Швидкість, анонімність, простота.

  H2: Ризики та обмеження
  Опис: Потенційні проблеми з безпекою та лімітами.

  H2: Методи платежів
  Опис: Огляд криптовалют, карток, гаманців.

  H2: Як обрати надійне казино
  Опис: Критерії вибору: ліцензія, відгуки.

  H2: Підсумки
  Опис: Короткий огляд переваг і ризиків.

Згенеруй структуру, яка буде релевантною, компактною та оптимізованою для SEO.
"""

st.title("Парсер HTML-структур конкурентів")

urls_input = st.text_area("Вставте URLи (один в лінію):", height=200)

if st.button("Перевірити конкурентів"):
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]
    html_structures = []
    for url in urls:
        structure = fetch_page_info_requests(url)
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
        st.subheader("Базовий промпт для ТЗ:")
        st.text_area("Копіюйте звідси:", generate_default_prompt(), height=400)
