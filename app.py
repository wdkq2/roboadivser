import gradio as gr
import requests
from bs4 import BeautifulSoup
from datetime import datetime

scenarios = []

# Add scenario and record investment

def add_scenario(desc, amount, keywords):
    scenario = {
        "desc": desc,
        "amount": amount,
        "keywords": keywords,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    scenarios.append(scenario)
    return f"Scenario added:\n{desc}\nInvest: {amount}\nKeywords: {keywords}"

# Fetch latest news from Google News

def fetch_news(keywords):
    url = f"https://news.google.com/search?q={keywords}&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, timeout=10)
    except Exception as e:
        return f"Request error: {e}"
    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select("article h3 a")
    output = []
    for item in items[:3]:
        title = item.text.strip()
        link = "https://news.google.com" + item.get("href", "")[1:]
        output.append(f"{title}\n{link}")
    return "\n\n".join(output) if output else "No news found"

# Simple feature query interpretation (placeholder)

def analyze_query(query):
    if "배당" in query:
        return "Request: top dividend yield companies"
    if "자사주" in query and "소각" in query:
        return "Request: companies with high treasury stock not cancelled"
    return "Request not recognized"

# Provide example results for feature search

def example_results(query):
    # This is placeholder logic. Replace with actual DART queries.
    return "Example Companies:\n회사A\n회사B\n회사C"

with gr.Blocks() as demo:
    gr.Markdown("## 간단한 로보 어드바이저 예제")
    with gr.Tab("시나리오 투자"):
        scenario_text = gr.Textbox(label="시나리오 내용")
        amount = gr.Textbox(label="투자 금액 (원)")
        keywords = gr.Textbox(label="뉴스 검색 키워드")
        add_btn = gr.Button("시나리오 추가")
        scenario_out = gr.Textbox(label="상태")
        add_btn.click(add_scenario, [scenario_text, amount, keywords], scenario_out)
        news_btn = gr.Button("최신 뉴스 확인")
        news_out = gr.Textbox(label="뉴스 결과")
        news_btn.click(fetch_news, keywords, news_out)
    with gr.Tab("특징 검색"):
        feature_query = gr.Textbox(label="검색 프롬프트")
        analyze_btn = gr.Button("프롬프트 해석")
        analysis = gr.Textbox(label="해석 결과")
        analyze_btn.click(analyze_query, feature_query, analysis)
        search_btn = gr.Button("예시 데이터 출력")
        results = gr.Textbox(label="검색 결과")
        search_btn.click(example_results, feature_query, results)

    gr.Markdown("작동 예시이므로 실제 매매나 DART 연결 기능은 구현되어 있지 않습니다.")

if __name__ == "__main__":
    # share=True enables a public link for environments like Colab
    demo.launch(share=True)
