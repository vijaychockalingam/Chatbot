from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import datetime
import random
import math
import json
import requests
from urllib.parse import quote
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, async_mode='threading')

# Thread-safe storage for user sessions
user_sessions = {}
session_lock = Lock()

class PydroidChatBot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_name = "User"  # Default name, can be customized per user
        self.jokes = [
            "Why don't scientists trust atoms? They make up everything!",
            "Parallel lines have so much in common... it's a shame they'll never meet.",
            "I told my computer I needed a break... now it won't stop sending me vacation ads."
        ]
        self.fun_facts = [
            "Octopuses have three hearts and blue blood.",
            "Honey never spoils - edible after 3000 years!",
            "Venus has a day longer than its year."
        ]
        self.web_services = {
            'g': 'https://www.google.com/search?q=',
            'google': 'https://www.google.com/search?q=',
            'w': 'https://en.wikipedia.org/wiki/',
            'wikipedia': 'https://en.wikipedia.org/wiki/',
            'yt': 'https://www.youtube.com/results?search_query=',
            'youtube': 'https://www.youtube.com/results?search_query=',
            'ddg': 'https://duckduckgo.com/?q=',
            'duckduckgo': 'https://duckduckgo.com/?q='
        }
        
        # Initialize memory for each user
        self.memory_file = f"user_memory_{user_id}.json"
        self.load_memory()

    def load_memory(self):
        try:
            with open(self.memory_file, "r") as f:
                self.memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.memory = {}

    def save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=4)

    def get_time(self):
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self):
        return datetime.datetime.now().strftime("%B %d, %Y")

    def calculate(self, expr):
        try:
            return str(eval(expr))
        except:
            return "I can't solve that."

    def get_web_search_url(self, service, query):
        if service in self.web_services:
            return self.web_services[service] + quote(query)
        return None

    def get_weather(self, location):
        try:
            url = f"https://wttr.in/{location}?format=%C+%t"
            response = requests.get(url)
            if response.status_code == 200:
                weather = response.text.strip()
                return f"Weather in {location}: {weather}"
            return "Weather service unavailable"
        except:
            return "Weather service unavailable"

    def ask_deepseek(self, prompt):
        # Return cached answer if available
        if prompt in self.memory:
            return f"(From Memory) {self.memory[prompt]}"

        # Otherwise, send to DeepSeek
        api_key = "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"
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yourwebsite.com",
            "X-Title": "PydroidBot"
        }

        data = {
            "model": "deepseek/deepseek-r1-zero:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                self.memory[prompt] = answer
                self.save_memory()
                return answer
            else:
                return f"Error: {response.status_code}, {response.text}"
        except Exception as e:
            return f"Exception occurred: {e}"

    def process_input(self, user_input):
        user_input = user_input.lower().strip()

        if not user_input:
            return "Please enter something."

        if 'hello' in user_input or 'hi' in user_input:
            return f"Hello {self.user_name}! How can I help you?"
        elif 'how are you' in user_input:
            return "I'm doing well, thanks for asking!"
        elif 'what is your name' in user_input:
            return "My name is PydroidBot."
        elif 'who created you' in user_input:
            return "I was created by Vijay Chockalingam."
        elif 'thank you' in user_input or 'thanks' in user_input:
            return "You're welcome!"
        elif 'time' in user_input:
            return f"Current time: {self.get_time()}"
        elif 'date' in user_input:
            return f"Today's date: {self.get_date()}"
        elif 'joke' in user_input:
            return random.choice(self.jokes)
        elif 'fact' in user_input:
            return random.choice(self.fun_facts)
        elif user_input.startswith('math '):
            expr = user_input[5:]
            return f"Result: {self.calculate(expr)}"
        elif user_input.startswith('search '):
            parts = user_input[7:].split(' ', 1)
            if len(parts) == 2:
                service, query = parts
                url = self.get_web_search_url(service, query)
                if url:
                    return {
                        'response': f"Searching {service} for: {query}",
                        'url': url
                    }
                else:
                    return "Unknown service. Try g/w/yt/ddg or google/wikipedia/youtube/duckduckgo"
            else:
                return "Usage: search [service] [query]"
        elif user_input.startswith('ask '):
            question = user_input[4:]
            return self.ask_deepseek(question)
        elif user_input.startswith('weather '):
            location = user_input[8:]
            return self.get_weather(location)
        elif 'help' in user_input:
            return self.get_help_text()
        elif any(op in user_input for op in ['+','-','*','/','^']):
            return f"Math result: {self.calculate(user_input)}"
        else:
            return "I didn't understand that. Try 'help' for options."

    def get_help_text(self):
        return """
Available Commands:

hello/hi: Greet the bot
how are you: Ask how the bot is doing
what is your name: Bot's name
who created you: Credits
time: Show current time
date: Show today's date
joke: Tell a joke
fact: Share a fun fact
math [expression]: Calculate math (e.g., 2+2)
search [service] [query]: Search online
(g/w/yt/ddg or google/wikipedia/youtube/duckduckgo)
ask [question]: Ask DeepSeek AI
weather [location]: Check weather
help: Show help menu
"""

# Web Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_id = request.form.get('user_id', 'default_user')
    message = request.form.get('message', '')
    
    with session_lock:
        if user_id not in user_sessions:
            user_sessions[user_id] = PydroidChatBot(user_id)
        bot = user_sessions[user_id]
    
    response = bot.process_input(message)
    
    # Handle search responses that include URLs
    if isinstance(response, dict):
        return jsonify(response)
    return jsonify({'response': response})

# WebSocket support
@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)

@socketio.on('message')
def handle_message(data):
    user_id = data.get('user_id', 'default_user')
    message = data.get('message', '')
    
    with session_lock:
        if user_id not in user_sessions:
            user_sessions[user_id] = PydroidChatBot(user_id)
        bot = user_sessions[user_id]
    
    response = bot.process_input(message)
    
    # Handle search responses that include URLs
    if isinstance(response, dict):
        socketio.emit('response', response, room=request.sid)
    else:
        socketio.emit('response', {'response': response}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)