import streamlit as st
import pyperclip
import requests
from bs4 import BeautifulSoup
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_page_info_requests(url):
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=2)  # Збільшено backoff для повторних спроб
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
        'Referer': 'https://www.google.com/'  # Додано Referer для правдоподібності
    }
    
    try:
        # Затримка перед запитом для імітації людської поведінки
        time.sleep(1)  # 1 секунда затримки
        response = session.get(url, headers=headers, timeout=30)  # Збільшено таймаут
        response.raise_for_status()
        
        # Затримка після запиту для "стабілізації" сторінки
        time.sleep(2)
        
        # Перевірка на блокування (Cloudflare, CAPTCHA тощо)
        block_indicators = ['cloudflare', 'captcha', 'blocked', 'just a moment', 'access denied']
        if any(indicator in response.text.lower() for indicator in block_indicators):
            st.warning(f"Block detected for {url}: possible anti-bot protection")
            return None

        # Використовуємо html.parser замість lxml, якщо lxml недоступний
        soup = BeautifulSoup(response.content, 'html.parser')

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.text.strip()
                # Фільтр: тільки релевантні заголовки, без сміття
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
- Враховувати довжину: структура повинна підтримувати достатній обсяг тексту (орієнтуйся на середній обсяг контенту конкурентів).
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
        structure = fetch_page_info_requests(url)
        if structure:
            html_structures.append(structure)
    
    if html_structures:
        st.session_state['html_structures'] = html_structures
        st.session_state['output_structures'] = "\n\n".join([f"Конкурент {i+1}:\n{structure}" for i, structure in enumerate(html_structures)])
        st.session_state['prompt'] = generate_prompt(html_structures)
        
        st.text_area("HTML-структури конкурентів:", st.session_state['output_structures'], height=400)
    else:
        st.error("Не вдалося спарсити жодного конкурента. Можливо, сайти захищені від парсингу.")

if 'output_structures' in st.session_state:
    if st.button("Скопіювати HTML-структури"):
        try:
            pyperclip.copy(st.session_state['output_structures'])
            st.success("HTML-структури скопійовано в буфер обміну!")
        except:
            st.warning("Копіювання не підтримується у веб-версії. Виділіть текст і скопіюйте вручну (Cmd+C).")
            st.text_area("HTML-структури для копіювання:", st.session_state['output_structures'], height=200)

    if st.button("Скопіювати промт"):
        try:
            pyperclip.copy(st.session_state['prompt'])
            st.success("Промт скопійовано в буфер обміну!")
        except:
            st.warning("Копіювання не підтримується у веб-версії. Виділіть текст і скопіюйте вручну (Cmd+C).")
            st.text_area("Промт для копіювання:", st.session_state['prompt'], height=200)

st.info("Ця програма розгорнута на Streamlit. Для релізу на streamlit.io, завантажте цей код і requirements.txt на GitHub.")
