import streamlit as st
import pyperclip
import requests
from bs4 import BeautifulSoup
import traceback
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_page_info_requests(url):
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = session.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        if any(phrase in response.text.lower() for phrase in ['cloudflare', 'captcha', 'blocked', 'just a moment']):
            st.write(f"Block detected for {url}")
            return None

        soup = BeautifulSoup(response.content, 'lxml')

        headings = []
        for tag in ['h2', 'h3', 'h4']:
            for heading in soup.find_all(tag):
                text = heading.text.strip()
                # Фільтр: тільки заголовки довші за 3 символи, без "сміття" (навігація, футери)
                if text and len(text) > 3 and not any(keyword in text.lower() for keyword in ['footer', 'menu', 'nav', 'copyright', 'sign up']):
                    headings.append(f"<{tag.upper()}>{text}")

        return "\n".join(headings) if headings else None

    except Exception as e:
        st.write(f"Error for {url}: {str(e)}")
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
        structure = fetch_page_info_requests(url)
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
        st.info("У веб-версії Streamlit копіювання може не працювати. Виділіть текст і скопіюйте вручну (Cmd+C).")

    if st.button("Скопіювати промт"):
        pyperclip.copy(st.session_state['prompt'])
        st.success("Промт скопійовано в буфер обміну!")
        st.info("У веб-версії Streamlit копіювання може не працювати. Виділіть текст і скопіюйте вручну (Cmd+C).")

st.info("Ця програма розгорнута на Streamlit. Для релізу на streamlit.io, завантажте цей код і requirements.txt на GitHub.")
