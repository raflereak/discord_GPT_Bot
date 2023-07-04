import discord
from discord.ext import commands
import openai
import mysql.connector
import json
import os

nowdir = os.getcwd()

# OpenAI API 인증
with open(nowdir + '/environment/setting.json' , 'r') as f:
    envData = json.load(f)


openai.api_key = envData['token']['chatGPT_API_token']

# MySQL 연결 및 테이블 생성
connection = mysql.connector.connect(
    host=envData['database']['host'],
    port=envData['database']['port'],
    user=envData['database']['user'],
    password=envData['database']['password'],
    database=envData['database']['database']
)

cursor = connection.cursor()

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.event
async def on_message(message):
    # 봇이 보낸 메시지는 무시
    if message.author.bot:
        return
    
    # 사용자 정보 조회
    cursor.execute("SELECT * FROM userData WHERE user_id = %s", (str(message.author.id),))
    user_data = cursor.fetchone()
    
    resetCNT = 0

    # 새로운 사용자인 경우, 사용자 정보를 userData 테이블에 추가
    if user_data is None:
        cursor.execute("INSERT INTO userData (user_id, username, reset_count, useState) VALUES (%s, %s, 0, False)", (str(message.author.id), str(message.author.name)))
        connection.commit()
        return
    else:
        resetCNT = user_data[3]

    if message.content.lower() == '!help':
        embed = discord.Embed(
            title="# Thank you for visiting our chatbot",
            description='''

            ''',
            color=discord.Color.blue()
        )
        embed.add_field(name="!help", value="- show command list", inline=False)
        embed.add_field(name="!chat", value='''- turn on chatbot \n- turn off chatbot
        ''', inline=False)
        embed.add_field(name="!reset", value='''
        - reset dialog \n- can you start new chat session
        ''', inline=False)
        embed.add_field(name="Version", value="alpha.ver", inline=True)
        embed.add_field(name="[Visit GitHub](https://github.com/raflereak/discord_GPT_Bot)", value="", inline=False)

        await message.channel.send(embed=embed)

    if message.content.lower() == '!chat':
        if user_data[4] == 0: # false
            cursor.execute("UPDATE userData SET useState = 1 WHERE user_id = %s", (str(message.author.id),))
            connection.commit()
            await message.channel.send("Turn on ChatBot.")

        elif user_data[4] == 1: # true
            cursor.execute("UPDATE userData SET useState = 0 WHERE user_id = %s", (str(message.author.id),))
            connection.commit()
            await message.channel.send("Turn off ChatBot")

        else: # error
            cursor.execute("UPDATE userData SET useState = 0 WHERE user_id = %s", (str(message.author.id),))
            connection.commit()
        return
        
    if message.content.lower() == '!reset':
        # userData 테이블에서 reset_count 증가
        cursor.execute("UPDATE userData SET reset_count = reset_count + 1 WHERE user_id = %s", (str(message.author.id),))
        connection.commit()

        # chat_logs 테이블에서 사용자 대화 기록 삭제
        # cursor.execute("DELETE FROM chat_logs WHERE user_id = %s", (str(message.author.id),))
        # connection.commit()

        await message.channel.send("Your chat session is reset")
        return


    if user_data[4] == 0: # 사용 상태 체크
        return

    async with message.channel.typing():
        pass

    # 이전 대화 내역 조회
    cursor.execute("SELECT role, message FROM chat_logs WHERE user_id = %s AND resetCount = %s ORDER BY timestamp DESC LIMIT 10", (str(message.author.id), str(resetCNT)))
    results = cursor.fetchall()
    chat_history = [(result[0], result[1]) for result in results[::-1]]
    

    # 질문을 OpenAI API로 전송하여 답변 받기
    question = message.content
    chat_history.append(('user', question))

    # OpenAI로 대화 기록 전송
    # messages = [{'role': role, 'content': chat} for role, chat in chat_history]
    
    messages = [{'role' : 'user', 'content' : '''
    The maximum text you can send is 2000 characters. If the answer is more than 2000 characters, answer only the contents inside "", saying "The length of the answer is too long. Please visit the chatgpt site and use it. Visit to Site : https://chat.openai.com/" And send the language to the last input local language.
    '''}]
    for role, chat in chat_history:
        messages.append({'role': role, 'content': chat})
    

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )
    answer = response.choices[-1].message.content
    chat_history.append(('assistant', answer))

    # 데이터베이스 저장을 위한 temp값
    tempText=[]
    tempText.append(('user', question))
    tempText.append(('assistant', answer))

    # 답변을 디스코드 채널로 전송
    await message.channel.send(answer)

    # 대화 내용 저장
    values = [(str(message.author.id), role, chat, resetCNT) for role, chat in tempText]
    cursor.executemany("INSERT INTO chat_logs (user_id, role, message, resetCount) VALUES (%s, %s, %s, %s)", values)
    connection.commit()


# 디스코드 봇 실행
bot.run(envData['token']['discord_bot_token'])
