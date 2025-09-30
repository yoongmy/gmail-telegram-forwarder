Gmail to Telegram Forwarder
A Python script that periodically checks a Gmail account for new emails matching a specific subject filter and forwards them as notifications to a Telegram chat.

This is useful for getting instant alerts for important emails, such as account confirmations, monitoring alerts, or any other automated messages. The script is designed to be run as a persistent background service on a Linux server.

Features
Gmail Integration: Uses the official Gmail API to securely access your inbox.

Subject Filtering: Only forwards emails that contain a specific keyword in the subject line.

Telegram Notifications: Sends well-formatted messages to a specified Telegram chat or channel.

Secure Authentication: Uses Google's OAuth 2.0 flow, so it never needs to store your password.

State Management: Marks emails as "read" after forwarding to avoid duplicate notifications.

Robust Logging: Logs all activities, successes, and errors to both a log file and the console.

Requirements
Python 3.6+

A Linux server/machine to run the service.

Google API Client Library for Python

Google Auth Library for Python

Requests

Setup and Configuration
Follow these steps to set up and configure the script.

Step 1: Get the Code and Install Dependencies
First, get the code onto your machine and install the required Python packages.
```
# Clone your repository (if you have one)
# git clone <your-repo-url>
# cd <your-repo-directory>

# Install the required packages
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib requests
```
Step 2: Configure Google API (Gmail)
You need to enable the Gmail API and get credentials to allow the script to access your account.

Go to the Google Cloud Console: https://console.cloud.google.com/

Create a new project or select an existing one.

Enable the Gmail API: In the navigation menu, go to APIs & Services > Library, search for "Gmail API", and click Enable.

Create Credentials:

Go to APIs & Services > Credentials.

Click Create Credentials and select OAuth client ID.

If prompted, configure the consent screen first. Select External and provide a name for the app.

For the Application type, select Desktop app.

Click Create.

Download Credentials: A popup will appear. Click DOWNLOAD JSON. Rename the downloaded file to credentials.json and place it in the same directory as your Python script.

Step 3: Configure Telegram Bot
Create a Bot: Open Telegram and chat with the BotFather. Send the /newbot command and follow the instructions. BotFather will give you a token.

Get Your Chat ID: Send a message to your new bot. Then, open your browser and go to the following URL, replacing <YOUR_BOT_TOKEN> with the token you received:
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
Look for the "chat": {"id": ...} field in the JSON response. This is your Chat ID.

Step 4: Configure the Script
Open your Python script and edit the configuration section at the top with the credentials you just obtained.
```
# Configuration
...
TELEGRAM_BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID_HERE'
CHECK_INTERVAL = 60  # Check every 60 seconds
SUBJECT_FILTER = 'Disney' # Change this to the keyword you want to filter by
```
Usage and Deployment
First-Time Authentication
Before you can run the script as a service, you must run it once manually to authorize its access to your Gmail account.

Run the script from your terminal:
```
python3 gmail-telegram-forwarder.py
```
The script will print a URL. Copy this URL and paste it into your web browser.

Choose your Google account and grant the requested permissions.

After authorization is complete, a token.json file will be created in the project directory. This file stores your authorization token.

Now you can stop the script with Ctrl+C. You are ready to run it as a service.

Deploying as a Systemd Service (Recommended)
Running the script as a systemd service ensures it runs automatically in the background and restarts on failure or reboot.

Create a service file:
```
sudo nano /etc/systemd/system/gmail-forwarder.service
```
This file should be created in /etc/systemd/system/, which is the standard location for custom service definitions by a system administrator.

Paste the following configuration. Be sure to update the User and the path in ExecStart to match your system. To find your username, run whoami. To find the full path to your script, navigate to its directory and run pwd.
```
[Unit]
Description=Gmail to Telegram Forwarder Service
After=network.target

[Service]
User=your_linux_username
Type=simple
Restart=always
ExecStart=/usr/bin/python3 /path/to/your/script.py
WorkingDirectory=/path/to/your/script_directory/

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```
# Reload the systemd manager configuration
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable gmail-forwarder.service

# Start the service immediately
sudo systemctl start gmail-forwarder.service
```
Check the service status:
```
sudo systemctl status gmail-forwarder.service
```
Logging and Permissions
The script logs its activity to /var/log/gmail_telegram_forwarder.log. The systemd service may not have permission to write to this file by default.

To fix this, create the log file and give your user ownership of it:
```
# Create the log file
sudo touch /var/log/gmail_telegram_forwarder.log

# Change its ownership to your user
# Replace 'your_username' with the result of the `whoami` command
sudo chown your_username:your_username /var/log/gmail_telegram_forwarder.log
```
