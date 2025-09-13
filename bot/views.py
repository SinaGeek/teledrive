import os
import requests
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect

# Note: You'd set up a database in settings.py and create a model
# in models.py for storing users, but for a direct comparison,
# we'll use SQLite here like in the Flask example.
import sqlite3

def init_db():
    conn = sqlite3.connect('../db.sqlite3') # Django's default DB file
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

# --- Views for static pages ---
def home(request: HttpRequest):
    return HttpResponse("<h1>GD Uploader Home (Django)</h1>")

def policy(request: HttpRequest):
    return HttpResponse("<h1>Privacy Policy</h1>")

def terms(request: HttpRequest):
    return HttpResponse("<h1>Terms of Service</h1>")

# --- View for starting login ---
def login(request: HttpRequest):
    user_id = request.GET.get('user')
    if not user_id:
        return HttpResponse("Error: Missing user identifier.", status=400)

    params = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI'),
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/drive.file',
        'access_type': 'offline',
        'state': user_id,
    }
    auth_url = requests.Request('GET', 'https://accounts.google.com/o/oauth2/v2/auth', params=params).prepare().url
    return redirect(auth_url)

# --- View for Google's callback ---
def oauth_callback(request: HttpRequest):
    code = request.GET.get('code')
    telegram_user_id = request.GET.get('state')
    
    # ... Token exchange logic is the same as the Flask example ...
    # ... Store the refresh token in the database ...
    
    return HttpResponse("✅ Authentication successful! You can now return to Telegram.")

# --- View for Telegram's webhook ---
def telegram_webhook(request: HttpRequest):
    # Django requires CSRF protection, which we must disable for this webhook
    # This is done by a decorator just above the function definition.
    # from django.views.decorators.csrf import csrf_exempt
    # @csrf_exempt
    # def telegram_webhook(request: HttpRequest):

    if request.method == 'POST':
        # ... Your bot logic for handling messages ...
        pass
    
    return HttpResponse("OK")