import os
from flask import Flask, request, jsonify
import telebot
from openai import OpenAI, RateLimitError
from config import OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
chat_history = {}


@app.route('/webhook/chat', methods=['POST'])
def telegram():
    try:
        update = telebot.types.Update.de_json(request.get_json(force=True))
        if update.message:
            user_input = update.message.text
            print(user_input)
            chat_id = update.message.chat.id

            chat_history.setdefault(chat_id, [])
            chat_history[chat_id].append({"role": "user", "content": user_input})

            messages = [
                {"role": "system", "content": ""},
                {"role": "user", "content": user_input}
            ]
            for message in chat_history.get(chat_id, []):
                messages.append(message)

            try:
                response = client.chat.completions.create(model="gpt-4-1106-preview", messages=messages)
                content = response.choices[0].message.content

            except RateLimitError:
                content = "Error"

            chat_history[chat_id].append({"role": "assistant", "content": content})
            print(content)

            if user_input.lower() == 'clean':
                chat_history[chat_id].clear()
                bot.send_message(chat_id, 'Context cleared')

            bot.send_message(chat_id, content)

        return 'OK'
    except Exception as e:
        error_message = str(e)
        print("ERROR:", error_message)
        return jsonify({'error': error_message}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

    # update