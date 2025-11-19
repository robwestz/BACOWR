"""
Google Authentication Manager

Handles OAuth 2.0 and Service Account authentication for Google APIs.
Supports both user-based OAuth and server-to-server Service Account flows.
"""

import os
import json
from typing import Optional, List
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleAuthManager:
    """
    Manages authentication with Google APIs.

    Supports two authentication methods:
    1. OAuth 2.0 (user consent) - for user-specific access
    2. Service Account - for server-to-server access
    """

    # Google API scopes required
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',  # Sheets read/write
        'https://www.googleapis.com/auth/documents',      # Docs read/write
        'https://www.googleapis.com/auth/drive.file',     # Drive file access
    ]

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        use_service_account: bool = True
    ):
        """
        Initialize Google Auth Manager.

        Args:
            credentials_path: Path to credentials JSON (OAuth client or Service Account)
            token_path: Path to store OAuth token (only for OAuth flow)
            use_service_account: If True, use Service Account; else use OAuth
        """
        self.credentials_path = credentials_path or os.getenv(
            'GOOGLE_CREDENTIALS_PATH',
            'credentials/google_credentials.json'
        )
        self.token_path = token_path or os.getenv(
            'GOOGLE_TOKEN_PATH',
            'credentials/google_token.json'
        )
        self.use_service_account = use_service_account
        self.credentials: Optional[Credentials] = None

    def authenticate(self) -> Credentials:
        """
        Authenticate with Google APIs.

        Returns:
            Google Credentials object

        Raises:
            FileNotFoundError: If credentials file not found
            ValueError: If authentication fails
        """
        if self.use_service_account:
            return self._authenticate_service_account()
        else:
            return self._authenticate_oauth()

    def _authenticate_service_account(self) -> Credentials:
        """
        Authenticate using Service Account (server-to-server).

        Best for:
        - Production environments
        - Automated workflows
        - No user interaction needed

        Returns:
            Service Account credentials
        """
        if not Path(self.credentials_path).exists():
            raise FileNotFoundError(
                f"Service Account credentials not found at {self.credentials_path}. "
                "Download from Google Cloud Console > IAM & Admin > Service Accounts."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.credentials = credentials
            return credentials
        except Exception as e:
            raise ValueError(f"Service Account authentication failed: {str(e)}")

    def _authenticate_oauth(self) -> Credentials:
        """
        Authenticate using OAuth 2.0 (user consent).

        Best for:
        - Development
        - User-specific access
        - Desktop applications

        Returns:
            OAuth credentials
        """
        credentials = None

        # Load existing token if available
        if Path(self.token_path).exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    self.token_path,
                    self.SCOPES
                )
            except Exception as e:
                print(f"Warning: Could not load existing token: {e}")

        # Refresh or obtain new credentials
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                # Refresh expired token
                credentials.refresh(Request())
            else:
                # Run OAuth flow
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(
                        f"OAuth credentials not found at {self.credentials_path}. "
                        "Download from Google Cloud Console > APIs & Services > Credentials."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    self.SCOPES
                )
                credentials = flow.run_local_server(port=0)

            # Save token for future use
            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(credentials.to_json())

        self.credentials = credentials
        return credentials

    def get_sheets_service(self):
        """
        Get authenticated Google Sheets API service.

        Returns:
            Google Sheets API service object
        """
        if not self.credentials:
            self.authenticate()

        return build('sheets', 'v4', credentials=self.credentials)

    def get_docs_service(self):
        """
        Get authenticated Google Docs API service.

        Returns:
            Google Docs API service object
        """
        if not self.credentials:
            self.authenticate()

        return build('docs', 'v1', credentials=self.credentials)

    def get_drive_service(self):
        """
        Get authenticated Google Drive API service.

        Returns:
            Google Drive API service object
        """
        if not self.credentials:
            self.authenticate()

        return build('drive', 'v3', credentials=self.credentials)

    @staticmethod
    def create_service_account_instructions() -> str:
        """
        Get instructions for creating a Service Account.

        Returns:
            Markdown-formatted instructions
        """
        return """
# How to Create Google Service Account

## Step 1: Create Project
1. Go to https://console.cloud.google.com
2. Create new project or select existing
3. Note the Project ID

## Step 2: Enable APIs
1. Go to "APIs & Services" > "Library"
2. Enable these APIs:
   - Google Sheets API
   - Google Docs API
   - Google Drive API

## Step 3: Create Service Account
1. Go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Name: "bacowr-export"
4. Grant role: "Editor" (or custom with Sheets/Docs/Drive access)
5. Click "Done"

## Step 4: Create Key
1. Click on the service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON"
5. Download file (e.g., `bacowr-service-account.json`)

## Step 5: Configure BACOWR
1. Save JSON file to `credentials/google_credentials.json`
2. Set environment variable:
   ```
   export GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
   ```

## Step 6: Share Spreadsheet (Important!)
- Service Accounts have their own email (in JSON file)
- Share your Google Sheet with service account email
- Give "Editor" permission
- Example: bacowr-export@project-id.iam.gserviceaccount.com

## Alternative: OAuth 2.0 (For Development)
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Desktop app"
4. Download JSON as `credentials/google_oauth_credentials.json`
5. First run will open browser for consent
"""

    @staticmethod
    def validate_credentials_file(file_path: str) -> dict:
        """
        Validate Google credentials JSON file.

        Args:
            file_path: Path to credentials file

        Returns:
            Dictionary with validation results
        """
        if not Path(file_path).exists():
            return {
                'valid': False,
                'error': f'File not found: {file_path}'
            }

        try:
            with open(file_path, 'r') as f:
                creds = json.load(f)

            # Check if Service Account
            if 'type' in creds and creds['type'] == 'service_account':
                required = ['client_email', 'private_key', 'project_id']
                missing = [k for k in required if k not in creds]
                if missing:
                    return {
                        'valid': False,
                        'type': 'service_account',
                        'error': f'Missing fields: {", ".join(missing)}'
                    }
                return {
                    'valid': True,
                    'type': 'service_account',
                    'email': creds['client_email'],
                    'project_id': creds['project_id']
                }

            # Check if OAuth client
            elif 'installed' in creds or 'web' in creds:
                return {
                    'valid': True,
                    'type': 'oauth_client',
                    'note': 'OAuth credentials - will require user consent on first use'
                }

            else:
                return {
                    'valid': False,
                    'error': 'Unknown credentials format'
                }

        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'error': f'Invalid JSON: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }
