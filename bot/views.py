import os
import json
import sqlite3
import requests
from django.conf import settings
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

# --- DATABASE SETUP ---
# Creates a simple SQLite database to store user tokens
def init_db():
    # Use the absolute path defined in your Django settings to prevent errors
    db_path = settings.DATABASES['default']['NAME']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_users (
            telegram_id TEXT PRIMARY KEY,
            refresh_token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db() # Create the table when the app starts

# --- HELPER: Send Telegram Message ---
def send_telegram_message(chat_id, text):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={'chat_id': chat_id, 'text': text})


# --- Views for static pages ---
def home(request: HttpRequest):
    return HttpResponse("<h1>GD Uploader Home (Django)</h1><p><a href='/policy'>Privacy Policy</a> | <a href='/terms'>Terms of Service</a></p>")

def policy(request: HttpRequest):
    return HttpResponse("<h1>Privacy Policy</h1><p>Your data is safe with us.</p>")

def terms(request: HttpRequest):
    return HttpResponse("<h1>Terms of Service</h1><p>Use this service responsibly.</p>")

# --- View for starting login ---
def login(request: HttpRequest):
    user_id = request.GET.get('user')
    if not user_id:
        return HttpResponse("Error: Missing user identifier.", status=400)

    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'),
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email',
        'access_type': 'offline',
        'state': user_id,
    }
    auth_url = requests.Request('GET', 'https://accounts.google.com/o/oauth2/v2/auth', params=params).prepare().url
    return redirect(auth_url)

# --- View for Google's callback ---
def oauth_callback(request: HttpRequest):
    code = request.GET.get('code')
    telegram_user_id = request.GET.get('state')

    # 1. Exchange the code for tokens
    response = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'),
        'grant_type': 'authorization_code',
    })
    
    tokens = response.json()
    refresh_token = tokens.get('refresh_token')
    access_token = tokens.get('access_token')

    if not refresh_token:
        return HttpResponse("Error: Could not retrieve refresh token from Google.", status=400)

    # 2. Store the refresh token in the database
    db_path = settings.DATABASES['default']['NAME']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO bot_users (telegram_id, refresh_token) VALUES (?, ?)",
        (telegram_user_id, refresh_token)
    )
    conn.commit()
    conn.close()
    
    # 3. Get user's email to show a friendly message
    user_info_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo',
                                      headers={'Authorization': f'Bearer {access_token}'})
    user_info = user_info_response.json()
    
    return HttpResponse(f"✅ Authentication successful for {user_info.get('email')}! You can now return to Telegram.")

# --- View for Telegram's webhook ---
@csrf_exempt # Important: Disables CSRF protection for this specific URL
def telegram_webhook(request: HttpRequest):
    if request.method != 'POST':
        return HttpResponse("OK")

    try:
        data = json.loads(request.body)
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        user_id = message.get('from', {}).get('id')
        text = message.get('text')

        if not user_id:
            return JsonResponse({}, status=200)

        # Handle the /start command
        if text and text.strip() == '/start':
            login_url = f"https://{request.get_host()}/login?user={user_id}"
            reply_text = f"Welcome! To upload files to Google Drive, please connect your account using this link:\n\n{login_url}"
            send_telegram_message(chat_id, reply_text)
        
        # TODO: Handle file uploads
        # You would add logic here to check for `message.get('document')` etc.
        # and then call a function to handle the upload process.

    except json.JSONDecodeError:
        print("Error decoding JSON from Telegram webhook")
    
    return JsonResponse({}, status=200) # Always return a 200 OK to Telegram