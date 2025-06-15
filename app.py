import os
import re
import gradio as gr
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import threading
import schedule
import time

DART_API_KEY = os.getenv("DART_API_KEY") or "4bada9597f370d2896444b492c3a92ff9c2d8f96"
TRADE_API_KEY = os.getenv("TRADE_API_KEY") or "PShKdxdOkJXLjBKTVLAbh2c2V5RrX3klIRXv"

scenarios = []
news_log = []

# Add scenario and record investment

def add_scenario(desc, amount, keywords, symbol):
    scenario = {
        "desc": desc,
        "amount": amount,
        "keywords": keywords,
        "symbol": symbol,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    scenarios.append(scenario)
    schedule.every().day.at("08:00").do(check_news, scenario)
    trade_msg = execute_trade(symbol, amount)
    return (
        f"Scenario added:\n{desc}\nInvest: {amount} in {symbol}\n"
        f"Keywords: {keywords}\n{trade_msg}"
    )

# Fetch latest news from Google News

def fetch_news(keywords):
    """Return the top 3 news articles for the given keywords."""
    api_key = os.getenv("NEWS_API_KEY")
    if api_key:
        url = (
            f"https://newsapi.org/v2/everything?q={keywords}&language=en&sortBy=publishedAt&apiKey={api_key}"
        )
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
        except Exception as e:
            return f"Request error: {e}"
        articles = data.get("articles", [])[:3]
        if not articles:
            return "No news found"
        return "\n\n".join(
            f"{a.get('title')}\n{a.get('url')}" for a in articles
        )
    url = "https://news.google.com/search"
    params = {"q": keywords, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except Exception as e:
        return f"Request error: {e}"
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("article h3 a")
    output = []
    for item in items[:3]:
        title = item.text.strip()
        href = item.get("href", "")
        link = "https://news.google.com" + href[1:] if href.startswith("/") else href
        output.append(f"{title}\n{link}")
    return "\n\n".join(output) if output else "No news found"


def check_news(scenario):
    news = fetch_news(scenario["keywords"])
    news_log.append({"scenario": scenario["desc"], "news": news, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    print(f"News update for {scenario['desc']}:\n{news}")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Simple feature query interpretation (placeholder)

def analyze_query(query):
    """Very naive interpretation of a natural language query."""
    m = re.search(r"배당률.*?(\d+)\D*위", query)
    if m:
        n = m.group(1)
        return f"배당률 상위 {n}개 기업을 찾습니다. 맞습니까?"
    if "자사주" in query and "소각" in query:
        return "자사주 보유가 많고 소각하지 않는 회사를 찾습니다. 맞습니까?"
    return "요청을 이해하지 못했습니다."

# Provide example results for feature search

def get_dart_data(query):
    """Query DART for company information by name."""
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_name": query,
    }
    url = "https://opendart.fss.or.kr/api/company.json"
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
    except Exception as e:
        return f"Request error: {e}"
    if data.get("status") != "000":
        return data.get("message", "DART error")
    items = data.get("list", [])
    if not items:
        return "No results"
    return "\n".join(
        f"{item.get('corp_name')} ({item.get('corp_code')})" for item in items[:3]
    )


def execute_trade(symbol, amount):
    """Execute a mock trade using the provided API key."""
    url = "https://example.com/trade"
    payload = {"symbol": symbol, "amount": amount, "key": TRADE_API_KEY}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return f"Trade executed for {symbol}: {amount}"
        return f"Trade API error: {r.status_code}"
    except Exception as e:
        return f"Request error: {e}"


def example_results(query):
    """Return placeholder search results using DART."""
    data = get_dart_data(query)
    return f"검색 결과 예시\n{data}\n회사A\n회사B\n회사C"

with gr.Blocks() as demo:
    gr.Markdown("## 간단한 로보 어드바이저 예제")
    with gr.Tab("시나리오 투자"):
        scenario_text = gr.Textbox(label="시나리오 내용")
        amount = gr.Textbox(label="투자 금액 (원)")
        symbol = gr.Textbox(label="종목 코드")
        keywords = gr.Textbox(label="뉴스 검색 키워드")
        add_btn = gr.Button("시나리오 추가")
        scenario_out = gr.Textbox(label="상태")
        add_btn.click(add_scenario, [scenario_text, amount, keywords, symbol], scenario_out)
        news_btn = gr.Button("최신 뉴스 확인")
        news_out = gr.Textbox(label="뉴스 결과")
        news_btn.click(fetch_news, keywords, news_out)
    with gr.Tab("특징 검색"):
        feature_query = gr.Textbox(label="검색 프롬프트")
        analyze_btn = gr.Button("프롬프트 해석")
        analysis = gr.Textbox(label="해석 결과")
        analyze_btn.click(analyze_query, feature_query, analysis)
        confirm_btn = gr.Button("해석 확인 후 검색")
        results = gr.Textbox(label="검색 결과")
        confirm_btn.click(example_results, feature_query, results)

    gr.Markdown(
        "NEWS_API_KEY가 있으면 뉴스API를 사용하고, DART_API_KEY와 TRADE_API_KEY는 기본값이 제공되어 바로 테스트할 수 있습니다."
    )

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    demo.launch(share=True)
