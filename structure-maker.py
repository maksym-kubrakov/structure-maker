import streamlit as st
import cloudscraper
from bs4 import BeautifulSoup
import time

# === Ініціалізація cloudscraper ===
@st.cache_resource
def get_scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
        delay=10
    )

# === Парсинг через cloudscraper ===
def fetch_page_info(url):
    scraper = get_scraper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'Accept-Language': 'uk-UA,uk;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        time.sleep(1.5)
        response = scraper.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            st.warning(f"HTTP {response.status_code} для {url}")
            return None

        text = response.text.lower()
        if any(block in text for block in ['cloudflare', 'captcha', 'checking your browser', 'attention required']):
            st.warning(f"Cloudflare блокує {url} (навіть через cloudscraper)")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        headings = []

        for tag in ['h2', 'h3', 'h4']:
            for h in soup.find_all(tag):
                txt = h.get_text(strip=True)
                if (txt and len(txt) > 3 and 
                    not any(kw in txt.lower() for kw in ['footer', 'menu', 'nav', 'cookie', 'sign up', 'log in', 'реєстрація'])):
                    headings.append(f"<{tag.upper()}>{txt}")

        return "\n".join(headings) if headings else "No relevant headings"

    except Exception as e:
        st.warning(f"Помилка для {url}: {str(e)[:80]}...")
        return None

# === Генерація промпту ===
def generate_prompt(structures):
    competitors = "\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(structures)])
    return f"""
Створи оптимізовану SEO-структуру (H2, H3) на основі конкурентів:

{competitors}

Вимоги:
- Тільки H2 (5–6 шт), H3 — рідко
- Початок з H2
- Логіка: вступ → переваги → ризики → вибір → висновок
- Без FAQ, без дублів
- Ключі: "казино без верифікації", "анонімні казино"

Формат — таблиця:

| Заголовок | О чем описать |
|----------|----------------|
| H2: ...  | ...            |
"""

def generate_default_prompt():
    return """
| Заголовок | О чем описать |
|----------|----------------|
| <H2> Казино без верифікації: що це | Визначення, як працює |
| <H2> Переваги гри без паспорта | Анонімність, швидкість |
| <H2> Ризики та мінуси | Безпека, шахраї |
| <H2> Як обрати надійне казино | Ліцензія, крипта |
| <H2> Висновок | Кому підходить |
"""

# === Streamlit UI ===
st.set_page_config(page_title="Парсер Конкурентів", layout="wide")
st.title("Парсер структур конкурентів")
st.success("Використовується **cloudscraper** — обходить Cloudflare **без драйверів**")

urls_input = st.text_area("Вставте URLи (по одному на рядок):", height=150, value="https://estorg.org.ua/ua/g21398956-derevyannye-bani-sauny\nhttps://epicentrk.ua/ua/shop/hotovi-sauny/\nhttps://artkamin.ua/bani-bochki/")

if st.button("Перевірити конкурентів", type="primary"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    results = []
    progress = st.progress(0)

    for i, url in enumerate(urls):
        with st.spinner(f"Парсимо {i+1}/{len(urls)}: {url}"):
            structure = fetch_page_info(url)
            if structure:
                results.append(structure)
            time.sleep(1)
        progress.progress((i + 1) / len(urls))

    if results:
        output = "\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(results)])
        prompt = generate_prompt(results)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Структури конкурентів")
            st.code(output)
        with col2:
            st.subheader("Промпт для копірайтерів")
            st.code(prompt, language="markdown")
    else:
        st.error("Не вдалося спарсити жодного конкурента.")
        st.code(generate_default_prompt(), language="markdown")
