"""
===========================================
📧 Gmail Email Agent using Google ADK
===========================================

This program creates an AI agent that can send emails using Gmail.

How it works:
1. Uses Gmail API for sending emails.
2. Uses credentials.json from Google Cloud for permission.
3. Saves login information in token.json so you don't log in every time.
4. Creates an AI agent that asks for:
   - Recipient email
   - Subject
   - Email body
5. The AI always asks for confirmation before sending the email.
"""

# Import modules used in the project
import os                 
import base64              
from email.message import EmailMessage  

from dotenv import load_dotenv         
from google.adk.agents import Agent    
from google.adk.models.lite_llm import LiteLlm  

# Google authentication libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API
from googleapiclient.discovery import build


# --------------------------------------------------
# Gmail permission (Scope)
# --------------------------------------------------
# This permission allows the program to SEND emails only.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


# Load environment variables from .env file
load_dotenv()

# File that contains Google OAuth credentials
CREDENTIALS_FILE = "credentials.json"

# File that stores the user's login token
TOKEN_FILE = "token.json"


# --------------------------------------------------
# Connect to Gmail API
# --------------------------------------------------
def _get_gmail_service():
    """
    Connect to Gmail.

    If token.json already exists:
        -> Use saved login.

    If token.json doesn't exist:
        -> Open browser for Google login.
        -> Save login in token.json.
    """

    creds = None

    # Check if token.json already exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If credentials don't exist or are invalid
    if not creds or not creds.valid:

        # Refresh expired login automatically
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:

            # Check if credentials.json exists
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Download an OAuth Desktop App "
                    "credential from Google Cloud Console."
                )

            # Open browser for Google login
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            # User signs into Google here
            creds = flow.run_local_server(port=0)

        # Save login token so user doesn't need to login again
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    # Return Gmail service object
    return build("gmail", "v1", credentials=creds)


# --------------------------------------------------
# Send Email Function
# --------------------------------------------------
def send_email(to: str, subject: str, body: str) -> dict:
    """
    Sends an email using Gmail.

    Parameters:
        to      -> Receiver email address
        subject -> Email subject
        body    -> Email message

    Returns:
        Success or error message.
    """

    try:

        service = _get_gmail_service()

        message = EmailMessage()

        message.set_content(body)

        message["To"] = to

        message["Subject"] = subject

        # Gmail API requires Base64 encoding
        encoded = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        # Send email
        sent = (
            service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": encoded}
            )
            .execute()
        )

        # Return success message
        return {
            "status": "success",
            "message_id": sent.get("id"),
            "detail": f"Email sent to {to}."
        }

    except Exception as e:

        # Return error if something goes wrong
        return {
            "status": "error",
            "detail": str(e)
        }


# --------------------------------------------------
# Create AI Email Agent
# --------------------------------------------------
root_agent = Agent(

    # Agent name
    name="email_agent",

    model=LiteLlm(
        model="groq/llama-3.3-70b-versatile"
    ),

    # Short description
    description=(
        "An AI assistant that sends Gmail emails."
    ),

    # Instructions for the AI
    instruction=(
        "You are a helpful email assistant.\n\n"

        "Ask the user for:\n"
        "- Recipient email\n"
        "- Subject\n"
        "- Email body\n\n"

        "If any information is missing, ask for it.\n\n"

        "Before sending, ALWAYS show the email draft and ask for confirmation.\n"

        "Only send the email after the user clearly says Yes.\n"

        "After sending, tell the user whether it succeeded or failed."
    ),

    # Tool that the AI can use
    tools=[send_email]
)