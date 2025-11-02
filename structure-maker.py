import streamlit as st
import httpx
from bs4 import BeautifulSoup
import random
import time
from fake_useragent import UserAgent

# === Ініціалізація клієнта ===
@st.cache_resource
def get_client():
    return httpx.Client(
        follow_redirects=True,
        timeout=httpx.Timeout(30.0),
        verify=False  # допомагає обійти SSL-помилки (443)
    )

# === Функція запиту з ретраями ===
def safe_request(url, retries=3):
    client = get_client()
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    for attempt in range(retries):
        try:
            time.sleep(random.uniform(1.0, 2.5))
            response = client.get(url, headers=headers)

            # обробка відомих блокувань
            if response.status_code in [403, 429, 503]:
                st.warning(f"{url} — блок ({response.status_code}), спроба {attempt+1}")
                continue
            if any(x in response.text.lower() for x in ["cloudflare", "captcha", "checking your browser"]):
                st.warning(f"Cloudflare блокує {url}")
                continue

            return response.text

        except Exception as e:
            st.warning(f"{url} — помилка {str(e)[:70]}, спроба {attempt+1}")
            time.sleep(2)

    return None

# === Парсинг заголовків ===
def extract_headings(html):
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for tag in ["h2", "h3", "h4"]:
        for h in soup.find_all(tag):
            text = h.get_text(strip=True)
            if (text and len(text) > 3 and 
                not any(kw in text.lower() for kw in ["footer", "cookie", "menu", "nav", "signup", "реєстрація", "логін"])):
                headings.append(f"<{tag.upper()}> {text}")
    return "\n".join(headings) if headings else "— заголовків не знайдено —"

# === Формування промпту ===
def generate_prompt(structures, topic):
    competitors = "\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(structures)])
    return f"""
Створи оптимізовану SEO-структуру (H2, H3) для статті на тему **"{topic}"**, орієнтуючись на конкурентів:

{competitors}

Вимоги:
- Тільки H2 (5–7 шт), H3 — мінімум
- Починай із H2
- Побудуй логічну послідовність (вступ → переваги → етапи/поради → ризики → висновок)
- Без FAQ, без дублів
- Формат — таблиця:

| Заголовок | Про що описати |
|-----------|----------------|
| H2: ...   | ...            |
"""

# === Запасний шаблон ===
def default_prompt():
    return """
| Заголовок | Про що описати |
|-----------|----------------|
| <H2> Що це за тема | Поясни сутність і контекст |
| <H2> Основні переваги | Чому це варто використовувати |
| <H2> Недоліки або ризики | На що звернути увагу |
| <H2> Як правильно вибрати | Критерії або поради |
| <H2> Підсумки | Короткий висновок |
"""

# === Streamlit UI ===
st.set_page_config(page_title="Парсер структур конкурентів", layout="wide")
st.title("🔍 SEO Parser — генератор промпту для структури статті")
st.info("Парсер намагається обійти блокування (HTTPX + Fake UserAgent + retries)")

topic = st.text_input("Тема або ключова фраза для статті:", "Наприклад: дерев’яні лазні")
urls_input = st.text_area("Вставте URL конкурентів (по одному на рядок):", height=150)

if st.button("Проаналізувати конкурентів", type="primary"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
    if not urls:
        st.error("❗ Додайте хоча б один URL.")
        st.stop()

    results = []
    progress = st.progress(0)

    for i, url in enumerate(urls):
        with st.spinner(f"Парсимо {i+1}/{len(urls)}: {url}"):
            html = safe_request(url)
            if html:
                structure = extract_headings(html)
                results.append(structure)
            else:
                results.append("❌ Не вдалося отримати контент.")
        progress.progress((i + 1) / len(urls))

    if any("H2" in r or "H3" in r for r in results):
        prompt = generate_prompt(results, topic)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Структури конкурентів")
            st.code("\n\n".join([f"Конкурент {i+1}:\n{s}" for i, s in enumerate(results)]))
        with col2:
            st.subheader("Промпт для копірайтера")
            st.code(prompt, language="markdown")
    else:
        st.warning("Не вдалося знайти жодного релевантного заголовка.")
        st.code(default_prompt(), language="markdown")
