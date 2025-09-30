#!/usr/bin/env python3

import os
import time
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import logging

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID_HERE'
CHECK_INTERVAL = 60  # Check every 60 seconds
SUBJECT_FILTER = 'Disney'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/gmail_telegram_forwarder.log'),
        logging.StreamHandler()
    ]
)

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def send_telegram_message(message):
    """Send message to Telegram channel."""
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        logging.info(f"Message sent to Telegram successfully")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to Telegram: {e}")
        return False

def get_message_details(service, msg_id):
    """Get email details from message ID."""
    try:
        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown Date')
        
        # Get email body
        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        # Truncate body if too long
        if len(body) > 500:
            body = body[:500] + '...'
        
        return {
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body
        }
    except Exception as e:
        logging.error(f"Error getting message details: {e}")
        return None

def check_new_emails(service, last_history_id):
    """Check for new emails with specific subject."""
    try:
        # Search for unread emails with subject filter
        query = f'subject:{SUBJECT_FILTER} is:unread'
        results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])
        
        if messages:
            logging.info(f"Found {len(messages)} new email(s) with '{SUBJECT_FILTER}' in subject")
            
            for msg in messages:
                msg_details = get_message_details(service, msg['id'])
                
                if msg_details:
                    # Format message for Telegram
                    telegram_msg = f"""
📧 <b>New Email Received</b>

<b>From:</b> {msg_details['sender']}
<b>Subject:</b> {msg_details['subject']}
<b>Date:</b> {msg_details['date']}

<b>Preview:</b>
{msg_details['body']}
"""
                    send_telegram_message(telegram_msg)
                    
                    # Mark as read
                    service.users().messages().modify(
                        userId='me',
                        id=msg['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    logging.info(f"Processed email: {msg_details['subject']}")
        
        return True
    except HttpError as error:
        logging.error(f"Gmail API error: {error}")
        return False

def main():
    """Main service loop."""
    logging.info("Gmail to Telegram Forwarder Service Started")
    
    try:
        service = get_gmail_service()
        logging.info("Gmail authentication successful")
        
        # Send startup notification
        send_telegram_message("🚀 Gmail to Telegram Forwarder Service Started")
        
        while True:
            try:
                check_new_emails(service, None)
                time.sleep(CHECK_INTERVAL)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(CHECK_INTERVAL)
                
    except KeyboardInterrupt:
        logging.info("Service stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()
