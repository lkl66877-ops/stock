import os
import discord
import google.generativeai as genai
import asyncio
from datetime import datetime
import pytz  # 시간대를 다루기 위한 라이브러리

# --- Secrets 설정 ---
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
# --------------------

# --- 🧠 대화 메모리 ---
conversation_history = {}
# --------------------

# Gemini AI 모델 설정
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini 모델이 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"❌ Gemini 모델 초기화 중 오류 발생: {e}")

# 디스코드 봇 권한 설정
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- ⏰ 새로운 기능: 자동 브리핑 스케줄러 ---
async def daily_briefing_scheduler():
    await client.wait_until_ready() # 봇이 완전히 준비될 때까지 기다립니다.

    # Secrets에서 브리핑을 보낼 채널 ID를 불러옵니다.
    channel_id = int(os.environ['DISCORD_CHANNEL_ID'])
    channel = client.get_channel(channel_id)

    # 브리핑 질문 내용
    briefing_prompt = "오늘의 투자 브리핑을 시작해줘. 어젯밤 미국 증시 마감 상황과 오늘 아침 나온 국내외 주요 증권사 리포트, 그리고 핵심 경제 뉴스를 종합적으로 분석해서, 오늘 내가 취해야 할 구체적인 투자 전략과 주목할 만한 섹터를 알려줘."

    last_briefing_date = None # 마지막으로 브리핑한 날짜를 저장할 변수

    while not client.is_closed():
        # 한국 시간대를 기준으로 현재 시간을 확인합니다.
        korea_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(korea_tz)

        # 매일 아침 8시에, 그리고 하루에 한 번만 실행되도록 조건을 확인합니다.
        if now.hour == 8 and now.minute == 0 and now.date() != last_briefing_date:
            print(f"⏰ 지금은 {now.strftime('%Y-%m-%d %H:%M:%S')}. 자동 브리핑을 시작합니다...")
            if channel:
                # 봇이 스스로에게 브리핑을 요청하는 메시지를 채널에 보냅니다.
                await channel.send(briefing_prompt)
            last_briefing_date = now.date() # 오늘 브리핑했음을 기록

        # 1분(60초)마다 시간을 확인합니다.
        await asyncio.sleep(60)
# ---------------------------------------------

@client.event
async def on_ready():
    print(f'🚀 {client.user} (으)로 로그인 성공!')
    print("🤖 (메모리&알람 장착!) 디스코드에서 메시지를 기다립니다...")
    # ⏰ 새로운 기능: 봇이 켜지면 스케줄러를 백그라운드에서 실행
    client.loop.create_task(daily_briefing_scheduler())

@client.event
async def on_message(message):
    if message.author == client.user:
        # 봇 자신이 보낸 메시지라도, 브리핑 요청이면 처리하도록 허용
        if message.content != "오늘의 투자 브리핑을 시작해줘. 어젯밤 미국 증시 마감 상황과 오늘 아침 나온 국내외 주요 증권사 리포트, 그리고 핵심 경제 뉴스를 종합적으로 분석해서, 오늘 내가 취해야 할 구체적인 투자 전략과 주목할 만한 섹터를 알려줘.":
            return

    channel_id = message.channel.id
    user_message = message.content
    print(f"📥 [{message.channel.name} 채널에서 메시지 수신]: {user_message}")

    if channel_id not in conversation_history:
        conversation_history[channel_id] = model.start_chat(history=[])
        print(f"✨ [{message.channel.name}] 새로운 대화 세션을 시작합니다.")

    chat = conversation_history[channel_id]

    async with message.channel.typing():
        response = chat.send_message(user_message)
        await message.channel.send(response.text)
        print(f"📤 [Gemini 답변 전송 완료]")

# 봇 실행
try:
    client.run(DISCORD_TOKEN)
except Exception as e:
    print(f"❌ 봇 실행 중 오류 발생: {e}")
