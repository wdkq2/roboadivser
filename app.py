import os
import re
import gradio as gr
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import schedule
import time
import json
import hashlib
=======

DART_API_KEY = (
    os.getenv("DART_API_KEY")
    or "4bada9597f370d2896444b492c3a92ff9c2d8f96"
)
TRADE_API_KEY = os.getenv(
    "TRADE_API_KEY", "PShKdxdOkJXLjBKTVLAbh2c2V5RrX3klIRXv"
)
TRADE_API_SECRET = os.getenv(
    "TRADE_API_SECRET",
    "Vt/gy4uGEAhWT2Tn0DE6IK2u+CBt752yHht/VXcjJUk7NzgZkx3lVoSDHvj/G2+RZNxBBjxEn2ReYQKquoh5BJi9f4KKomsYxJ3cyQ6noTyb0ep1OHD/xIe3w2Y9h+eb0PG7hxwhZBmWwPO6VQq9KRXZockUH5qNTbDosA6mfbKssmxWL2o=",
)
TRADE_API_URL = os.getenv(
    "TRADE_API_URL", "https://openapivts.koreainvestment.com:29443"
)
TRADE_ACCOUNT = os.getenv("TRADE_ACCOUNT", "")
TRADE_PRODUCT_CODE = os.getenv("TRADE_PRODUCT_CODE", "01")
=======
TRADE_API_KEY = (
    os.getenv("TRADE_API_KEY")
    or "PShKdxdOkJXLjBKTVLAbh2c2V5RrX3klIRXv"
)

scenarios = []
news_log = []
portfolio = {}


def get_access_token():
    """Retrieve an access token for the trading API."""
    token_url = f"{TRADE_API_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": TRADE_API_KEY,
        "appsecret": TRADE_API_SECRET,
    }
    try:
        r = requests.post(
            token_url,
            headers={"content-type": "application/json; charset=utf-8"},
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("access_token")
    except Exception as e:
        print("Token error", e)
        return None


def make_hashkey(data):
    """Compute hash key using the hashkey endpoint."""
    url = f"{TRADE_API_URL}/uapi/hashkey"
    try:
        r = requests.post(
            url,
            headers={
                "content-type": "application/json; charset=utf-8",
                "appkey": TRADE_API_KEY,
                "appsecret": TRADE_API_SECRET,
            },
            json=data,
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("HASH")
    except Exception as e:
        print("Hashkey error", e)
        body = json.dumps(data, separators=(",", ":"))
        return hashlib.sha256(body.encode()).hexdigest()

=======
# sample financial data for dividend yield calculation (예시)
sample_financials = [
    {"corp_name": "삼성전자", "symbol": "005930", "corp_code": "005930", "dps": 361, "price": 70000},
    {"corp_name": "현대차", "symbol": "005380", "corp_code": "005380", "dps": 3000, "price": 200000},
    {"corp_name": "NAVER", "symbol": "035420", "corp_code": "035420", "dps": 667, "price": 150000},
    {"corp_name": "카카오", "symbol": "035720", "corp_code": "035720", "dps": 0, "price": 60000},
    {"corp_name": "LG화학", "symbol": "051910", "corp_code": "051910", "dps": 12000, "price": 350000},
]

# analyzed query state
analysis_state = {}

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
    return (
        f"Scenario added:\n{desc}\nInvest: {amount} in {symbol}\n"
        f"Keywords: {keywords}\nPress '매매 실행' to trade"
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
    url = "https://news.google.com/rss/search"
    params = {"q": keywords, "hl": "en-US", "gl": "US", "ceid": "US:en"}
    try:
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except Exception as e:
        return f"Request error: {e}"
    root = ET.fromstring(r.text)
    items = root.findall("./channel/item")
    output = []
    for item in items[:3]:
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
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
        n = int(m.group(1))
        analysis_state['query'] = query
        analysis_state['type'] = 'dividend'
        analysis_state['count'] = n
        return f"배당률 상위 {n}개 기업을 찾습니다. 맞습니까?"
    if "자사주" in query and "소각" in query:
        analysis_state['query'] = query
        analysis_state['type'] = 'buyback'
        return "자사주 보유가 많고 소각하지 않는 회사를 찾습니다. 맞습니까?"
    return "요청을 이해하지 못했습니다."

def dividend_rank(n):
    ranked = sorted(
        sample_financials,
        key=lambda x: (x['dps'] / x['price'] if x['price'] else 0),
        reverse=True,
    )
    out = []
    for comp in ranked[:n]:
        pct = comp['dps'] / comp['price'] * 100 if comp['price'] else 0
        out.append(f"{comp['corp_name']}({comp['symbol']}): {pct:.2f}%")
    return "\n".join(out)

# Provide example results for feature search

corp_map = {item["corp_name"]: item["corp_code"] for item in sample_financials}

def get_dart_data(name):
    """Fetch company information from the DART API."""
    code = corp_map.get(name)
    if not code:
        return "Company not found"
    try:
        resp = requests.get(
            "https://opendart.fss.or.kr/api/company.json",
            params={"crtfc_key": DART_API_KEY, "corp_code": code},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Request error: {e}"


def execute_trade(symbol, qty):
    """Send an order to the trading API using the Korea Investment mock endpoint."""
    try:
        q = int(float(qty))
    except ValueError:
        return "Invalid amount"

    token = get_access_token()
    if not token:
        return "Failed to get access token"

    body = {
        "CANO": TRADE_ACCOUNT,
        "ACNT_PRDT_CD": TRADE_PRODUCT_CODE,
        "PDNO": symbol,
        "ORD_DVSN": "01",  # market order
        "ORD_QTY": str(q),
        "ORD_UNPR": "0",
    }
    hashkey = make_hashkey(body)
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": TRADE_API_KEY,
        "appsecret": TRADE_API_SECRET,
        "tr_id": "VTTC0012U",
        "custtype": "P",
        "hashkey": hashkey,
    }
    try:
        resp = requests.post(
            f"{TRADE_API_URL}/uapi/domestic-stock/v1/trading/order-cash",
            json=body,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        portfolio[symbol] = portfolio.get(symbol, 0) + q
        msg = data.get("msg1", "trade executed")
        return f"{msg} 현재 보유 {portfolio[symbol]}주"
    except Exception as e:
        return f"Trade error: {e}"
=======
def get_dart_data(query):
    """Return company info from sample data matching the query."""
    results = []
    for item in sample_financials:
        if query in item["corp_name"]:
            results.append(f"{item['corp_name']} ({item['corp_code']})")
    return "\n".join(results) if results else "No results"


def execute_trade(symbol, amount):
    """Record a mock trade locally."""
    try:
        amt = float(amount)
    except ValueError:
        return "Invalid amount"
    portfolio[symbol] = portfolio.get(symbol, 0) + amt
    return f"매매 완료: {symbol} {amt}원 보유량 {portfolio[symbol]}원"


def example_results(query):
    """Return search results using sample DART data."""
    return get_dart_data(query)

def perform_query(_=None):
    if analysis_state.get('type') == 'dividend':
        n = analysis_state.get('count', 0)
        return dividend_rank(n)
    elif analysis_state.get('type') == 'buyback':
        return "자사주 보유량 데이터 예시"
    return "분석된 내용이 없습니다."

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
        trade_btn = gr.Button("매매 실행")
        trade_result = gr.Textbox(label="매매 결과")
        trade_btn.click(execute_trade, [symbol, amount], trade_result)
        news_btn = gr.Button("최신 뉴스 확인")
        news_out = gr.Textbox(label="뉴스 결과")
        news_btn.click(fetch_news, keywords, news_out)
    with gr.Tab("특징 검색"):
        feature_query = gr.Textbox(label="검색 프롬프트")
        analyze_btn = gr.Button("프롬프트 해석")
        analysis = gr.Textbox(label="해석 결과")
        analyze_btn.click(analyze_query, feature_query, analysis)
        confirm_btn = gr.Button("해석 확인")
        cancel_btn = gr.Button("취소")
        results = gr.Textbox(label="검색 결과")
        confirm_btn.click(perform_query, None, results)
        cancel_btn.click(lambda: "취소되었습니다.", None, results)

    gr.Markdown(
        "NEWS_API_KEY가 있으면 뉴스API를 사용하고, DART_API_KEY와 TRADE_API_KEY, TRADE_API_URL을 설정하면 실 거래 API를 호출합니다."
=======
        "NEWS_API_KEY가 있으면 뉴스API를 사용하고, DART_API_KEY와 TRADE_API_KEY는 기본값이 제공되어 바로 테스트할 수 있습니다."

    )

if __name__ == "__main__":
    threading.Thread(target=run_scheduler, daemon=True).start()
    demo.launch(share=True)
