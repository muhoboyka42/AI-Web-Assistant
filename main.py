import os
import uuid

from openai import OpenAI
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session


client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)
instruction = "ты чат бот которому пользователи могут задавать вопросы, а также вести биседу с тобой"

app = Flask(__name__)
app.secret_key = "super secret key"

@app.route('/', methods=['GET', 'POST'])
def home():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send':
            user_message = request.form.get('message', '').strip()
            if user_message:
                start_chat(user_id, user_message)
        elif action == 'clear':
            clear_user_history(user_id)
        return redirect(url_for('home'))

    db_history = get_user_history(user_id)
    chat_history = []
    for msg in db_history:
        if msg['role'] == 'user':
            chat_history.append(f"Пользователь: {msg['content']}")
        elif msg['role'] == 'assistant':
            chat_history.append(f"AI: {msg['content']}")

    return render_template('index.html', history=chat_history)


def init_db():
    with sqlite3.connect("chat_history.db") as db:
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_ID INTEGER,
        role TEXT,
        content TEXT)
        """)
def clear_user_history(user_ID):
    with sqlite3.connect("chat_history.db") as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM messages WHERE user_ID=?", (user_ID,))
def get_user_history(user_ID):
    history = []
    with sqlite3.connect("chat_history.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT role,content FROM messages WHERE user_ID=? ORDER BY id ASC", (user_ID,))
        rows = cursor.fetchall()
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
    return history

def add_message_to_history(user_ID, role, content):
    with sqlite3.connect("chat_history.db") as db:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO messages (user_ID, role, content) VALUES (?, ?, ?)",
            (user_ID, role, content)
        )


def start_chat(user_id, user_input):
    history_chat = get_user_history(user_id)
    if not history_chat:
        add_message_to_history(user_id,"system", instruction)
        history_chat.append({"role": "system", "content": instruction})
    add_message_to_history(user_id,"user", user_input)
    history_chat.append({"role": "user", "content": user_input})
    try:
        chat_completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=history_chat,
            temperature=0.7
        )
        bot_response = chat_completion.choices[0].message.content

        add_message_to_history(user_id,"assistant", bot_response)

        history_chat.append({"role": "assistant", "content": bot_response})

        return bot_response

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return "Извините, произошла ошибка при обработке запроса."


init_db()

if __name__ == '__main__':
    app.run(debug=True)
