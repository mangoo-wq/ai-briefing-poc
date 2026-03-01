from datetime import datetime


def generate_mock_briefing() -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        f"[AI Briefing] {now}",
        "1) OpenAI/Gemini 경쟁 심화, 기업 도입 속도 가속.",
        "2) 반도체/클라우드 수요 기대 유지, 변동성은 확대.",
        "3) 규제 이슈는 단기 노이즈, 중장기 생산성 수혜는 유효.",
        "NASDAQ 영향: 중립~긍정",
        "오늘 행동: 큰 추격매수보다 분할 접근 + 리스크 한도 유지",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_mock_briefing())
