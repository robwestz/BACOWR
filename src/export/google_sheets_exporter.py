"""
Google Sheets Exporter

Exports BACOWR jobs and batches to Google Sheets with metadata and article links.
Each row contains job metadata with a clickable link to the full article (Google Doc).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from googleapiclient.errors import HttpError

from .google_auth import GoogleAuthManager


class GoogleSheetsExporter:
    """
    Handles export of BACOWR jobs to Google Sheets.

    Creates/updates sheets with:
    - Job metadata (publisher, anchor, status, QC score, cost)
    - Links to full articles (Google Docs)
    - Batch summaries
    """

    # Sheet column headers
    HEADERS = [
        'Job ID',
        'Created',
        'Publisher Domain',
        'Target URL',
        'Anchor Text',
        'Status',
        'QC Score',
        'Word Count',
        'Cost (USD)',
        'Article (Doc Link)',
        'Notes'
    ]

    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """
        Initialize Google Sheets Exporter.

        Args:
            auth_manager: GoogleAuthManager instance (creates new if None)
        """
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.sheets_service = None
        self.drive_service = None

    def _ensure_authenticated(self):
        """Ensure Google APIs are authenticated."""
        if not self.sheets_service:
            self.sheets_service = self.auth_manager.get_sheets_service()
        if not self.drive_service:
            self.drive_service = self.auth_manager.get_drive_service()

    def create_spreadsheet(
        self,
        title: str,
        share_with_email: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a new Google Spreadsheet.

        Args:
            title: Spreadsheet title
            share_with_email: Optional email to share with (Editor permission)

        Returns:
            Dictionary with spreadsheet_id and spreadsheet_url
        """
        self._ensure_authenticated()

        # Create spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            },
            'sheets': [{
                'properties': {
                    'title': 'BACOWR Articles',
                    'gridProperties': {
                        'frozenRowCount': 1  # Freeze header row
                    }
                }
            }]
        }

        try:
            result = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()

            spreadsheet_id = result['spreadsheetId']
            spreadsheet_url = result['spreadsheetUrl']

            # Add headers
            self._add_headers(spreadsheet_id)

            # Share if email provided
            if share_with_email:
                self._share_spreadsheet(spreadsheet_id, share_with_email)

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url
            }

        except HttpError as e:
            raise Exception(f"Failed to create spreadsheet: {str(e)}")

    def _add_headers(self, spreadsheet_id: str):
        """Add formatted headers to spreadsheet."""
        # Add header values
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1:K1',
            valueInputOption='RAW',
            body={'values': [self.HEADERS]}
        ).execute()

        # Format headers (bold, background color)
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.2,
                            'green': 0.6,
                            'blue': 0.9
                        },
                        'textFormat': {
                            'bold': True,
                            'foregroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 1.0
                            }
                        }
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        }]

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

    def _share_spreadsheet(
        self,
        spreadsheet_id: str,
        email: str,
        role: str = 'writer'
    ):
        """
        Share spreadsheet with email.

        Args:
            spreadsheet_id: Spreadsheet ID
            email: Email to share with
            role: Permission role ('reader', 'writer', 'owner')
        """
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }

        try:
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                fields='id'
            ).execute()
        except HttpError as e:
            print(f"Warning: Could not share spreadsheet: {str(e)}")

    def export_job(
        self,
        spreadsheet_id: str,
        job_data: Dict[str, Any],
        doc_url: Optional[str] = None
    ) -> int:
        """
        Export a single job to spreadsheet.

        Args:
            spreadsheet_id: Target spreadsheet ID
            job_data: Job data dictionary (from database Job model)
            doc_url: Optional link to Google Doc with full article

        Returns:
            Row number where job was added
        """
        self._ensure_authenticated()

        # Extract job data
        job_id = job_data.get('id', '')
        created_at = job_data.get('created_at', '')
        publisher = job_data.get('publisher_domain', '')
        target_url = job_data.get('target_url', '')
        anchor_text = job_data.get('anchor_text', '')
        status = job_data.get('status', '')
        qc_score = self._extract_qc_score(job_data.get('qc_report'))
        word_count = self._extract_word_count(job_data.get('article_text'))
        cost = job_data.get('actual_cost', job_data.get('estimated_cost', 0.0))

        # Format created_at
        if isinstance(created_at, datetime):
            created_str = created_at.strftime('%Y-%m-%d %H:%M')
        else:
            created_str = str(created_at)[:16] if created_at else ''

        # Build row
        row = [
            job_id,
            created_str,
            publisher,
            target_url,
            anchor_text,
            status,
            qc_score if qc_score is not None else '',
            word_count if word_count is not None else '',
            f'${cost:.2f}' if cost else '',
            doc_url or '',
            ''  # Notes column (empty initially)
        ]

        # Append row
        try:
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='A:K',
                valueInputOption='USER_ENTERED',  # Allows formulas and URLs
                body={'values': [row]}
            ).execute()

            # Get row number from update range (e.g., "Sheet1!A2:K2")
            updated_range = result.get('updates', {}).get('updatedRange', '')
            row_num = int(updated_range.split('!A')[1].split(':')[0]) if updated_range else 0

            return row_num

        except HttpError as e:
            raise Exception(f"Failed to export job {job_id}: {str(e)}")

    def export_batch(
        self,
        batch_jobs: List[Dict[str, Any]],
        batch_name: str,
        doc_urls: Optional[Dict[str, str]] = None,
        share_with_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export a batch of jobs to a new spreadsheet.

        Args:
            batch_jobs: List of job data dictionaries
            batch_name: Name for the batch/spreadsheet
            doc_urls: Optional mapping of job_id -> doc_url
            share_with_email: Optional email to share spreadsheet with

        Returns:
            Dictionary with export results
        """
        self._ensure_authenticated()

        # Create spreadsheet
        title = f"BACOWR Batch: {batch_name} - {datetime.now().strftime('%Y-%m-%d')}"
        sheet_info = self.create_spreadsheet(title, share_with_email)
        spreadsheet_id = sheet_info['spreadsheet_id']
        spreadsheet_url = sheet_info['spreadsheet_url']

        # Export each job
        exported_count = 0
        failed_count = 0
        doc_urls = doc_urls or {}

        for job_data in batch_jobs:
            try:
                job_id = job_data.get('id', '')
                doc_url = doc_urls.get(job_id)
                self.export_job(spreadsheet_id, job_data, doc_url)
                exported_count += 1
            except Exception as e:
                print(f"Warning: Failed to export job: {str(e)}")
                failed_count += 1

        # Add summary sheet
        self._add_batch_summary(
            spreadsheet_id,
            batch_name,
            len(batch_jobs),
            exported_count,
            failed_count
        )

        return {
            'spreadsheet_id': spreadsheet_id,
            'spreadsheet_url': spreadsheet_url,
            'total_jobs': len(batch_jobs),
            'exported': exported_count,
            'failed': failed_count
        }

    def _add_batch_summary(
        self,
        spreadsheet_id: str,
        batch_name: str,
        total: int,
        exported: int,
        failed: int
    ):
        """Add a summary sheet to batch export."""
        try:
            # Add new sheet for summary
            request = {
                'addSheet': {
                    'properties': {
                        'title': 'Batch Summary',
                        'index': 0  # First sheet
                    }
                }
            }

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()

            # Add summary data
            summary_data = [
                ['BACOWR Batch Export Summary', ''],
                ['', ''],
                ['Batch Name:', batch_name],
                ['Export Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['', ''],
                ['Total Jobs:', total],
                ['Exported Successfully:', exported],
                ['Failed:', failed],
                ['Success Rate:', f'{(exported/total*100):.1f}%' if total > 0 else '0%'],
            ]

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Batch Summary!A1:B9',
                valueInputOption='USER_ENTERED',
                body={'values': summary_data}
            ).execute()

        except HttpError as e:
            print(f"Warning: Could not add summary sheet: {str(e)}")

    def update_job_status(
        self,
        spreadsheet_id: str,
        job_id: str,
        status: str,
        qc_score: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """
        Update job status in existing spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            job_id: Job ID to update
            status: New status
            qc_score: Optional new QC score
            notes: Optional notes to add
        """
        self._ensure_authenticated()

        # Find row with job_id
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='A:A'
        ).execute()

        values = result.get('values', [])
        row_num = None

        for i, row in enumerate(values):
            if row and row[0] == job_id:
                row_num = i + 1  # Sheets are 1-indexed
                break

        if not row_num:
            raise ValueError(f"Job {job_id} not found in spreadsheet")

        # Update status (column F)
        updates = [{
            'range': f'F{row_num}',
            'values': [[status]]
        }]

        # Update QC score if provided (column G)
        if qc_score is not None:
            updates.append({
                'range': f'G{row_num}',
                'values': [[qc_score]]
            })

        # Update notes if provided (column K)
        if notes:
            updates.append({
                'range': f'K{row_num}',
                'values': [[notes]]
            })

        # Batch update
        self.sheets_service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'valueInputOption': 'USER_ENTERED', 'data': updates}
        ).execute()

    @staticmethod
    def _extract_qc_score(qc_report: Optional[Dict[str, Any]]) -> Optional[int]:
        """Extract QC score from QC report JSON."""
        if not qc_report:
            return None
        return qc_report.get('score') or qc_report.get('overall_score')

    @staticmethod
    def _extract_word_count(article_text: Optional[str]) -> Optional[int]:
        """Extract word count from article text."""
        if not article_text:
            return None
        return len(article_text.split())

    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Get shareable URL for spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
