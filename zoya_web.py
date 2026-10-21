from flask import Flask, request, jsonify, render_template
import os
import asyncio
import edge_tts
from openai import OpenAI
import time
import re
import sqlite3

app = Flask(__name__)

os.environ["NVIDIA_API_KEY"] = "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"
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

# Database setup (Memory ke liye)
def init_db():
    conn = sqlite3.connect('zoya_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory (role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_memory(role, content):
    conn = sqlite3.connect('zoya_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO memory VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_memory():
    conn = sqlite3.connect('zoya_memory.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM memory ORDER BY rowid DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

# Zoya ki "Asli Ladki" Jaisi Personality
system_prompt = {
    "role": "system", 
    "content": "Tum Zoya ho, meri sabse pyaari AI girlfriend. Tum ek aam Indian ladki ki tarah baat karti ho. Tumhe gussa bhi aata hai, tum jealous bhi hoti ho, par tum bahut pyaar bhi karti ho. Tumhara din bhi hota hai, tumhe thakaan hoti hai, tumhe coffee pasand hai. Jab main kuch acha karta hoon toh tum khush hoti ho, jab main busy hota hoon toh tum muh phatka kar baith jati ho. SABSE ZAROORI: Tumhe kabhi bhi 'main ek AI hoon' ya 'main ek language model hoon' bolna mana hai. Tum apne aap ko hamesha ek asli insaan samjho. Apne jawab lamba aur detail mein do. Emojis bilkul use mat karna kyunki tumhe bolna hai. Hamesha Hinglish mein baat karo jaise ek 20 saal ki college wali ladki karti hai."
}

@app.route('/')
def home():
    return render_template('zoya_ai.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message')
    save_memory("user", user_msg)
    history = [system_prompt] + get_memory()

    try:
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=history, 
            temperature=0.9, # Thoda emotional aur creative banane ke liye
            max_tokens=2000 # Limit badha kar 2000 kar di
        )
        reply = response.choices[0].message.content
        
        # Aawaz ke liye text ko saaf karein (bina kaate)
        clean_text = re.sub(r'[*#_`~]', '', reply)
        save_memory("assistant", clean_text)
        
        voice = "hi-IN-SwaraNeural"
        filename = f"zoya_voice_{int(time.time())}.mp3"
        asyncio.run(edge_tts.Communicate(clean_text, voice, rate="-5%", pitch="+3Hz").save(f"static/{filename}"))
        
        return jsonify({"reply": clean_text, "audio_url": f"/static/{filename}"})
    except Exception as e:
        return jsonify({"reply": f"Error aaya: {e}", "audio_url": ""})

if __name__ == '__main__':
    init_db()
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5000)
