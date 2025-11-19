"""
Google Docs Exporter

Exports BACOWR articles to Google Docs with formatting.
Creates properly formatted documents with headings, paragraphs, and highlighted backlinks.
"""

from typing import Dict, Any, Optional, List
from googleapiclient.errors import HttpError

from .google_auth import GoogleAuthManager


class GoogleDocsExporter:
    """
    Handles export of BACOWR articles to Google Docs.

    Creates documents with:
    - Formatted title
    - Structured headings (H1, H2, H3)
    - Paragraphs with proper spacing
    - Highlighted backlink
    - Metadata footer
    """

    def __init__(self, auth_manager: Optional[GoogleAuthManager] = None):
        """
        Initialize Google Docs Exporter.

        Args:
            auth_manager: GoogleAuthManager instance (creates new if None)
        """
        self.auth_manager = auth_manager or GoogleAuthManager()
        self.docs_service = None
        self.drive_service = None

    def _ensure_authenticated(self):
        """Ensure Google APIs are authenticated."""
        if not self.docs_service:
            self.docs_service = self.auth_manager.get_docs_service()
        if not self.drive_service:
            self.drive_service = self.auth_manager.get_drive_service()

    def create_document(
        self,
        title: str,
        content: str,
        backlink_info: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        share_with_email: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a new Google Doc with article content.

        Args:
            title: Document title
            content: Article content (plain text or simple markdown)
            backlink_info: Dict with 'anchor_text' and 'target_url'
            metadata: Optional metadata to add as footer
            share_with_email: Optional email to share with

        Returns:
            Dictionary with document_id and document_url
        """
        self._ensure_authenticated()

        # Create empty document
        try:
            doc = self.docs_service.documents().create(
                body={'title': title}
            ).execute()

            document_id = doc['documentId']
            document_url = f"https://docs.google.com/document/d/{document_id}"

            # Add content with formatting
            self._add_formatted_content(
                document_id,
                title,
                content,
                backlink_info,
                metadata
            )

            # Share if email provided
            if share_with_email:
                self._share_document(document_id, share_with_email)

            return {
                'document_id': document_id,
                'document_url': document_url
            }

        except HttpError as e:
            raise Exception(f"Failed to create document: {str(e)}")

    def _add_formatted_content(
        self,
        document_id: str,
        title: str,
        content: str,
        backlink_info: Optional[Dict[str, str]],
        metadata: Optional[Dict[str, Any]]
    ):
        """Add formatted content to document."""
        requests = []

        # Parse and format content
        sections = self._parse_content(content)

        # Build text insertion requests (in reverse order for indexing)
        text_to_insert = []

        # Add metadata footer if provided
        if metadata:
            text_to_insert.append('\n\n---\n')
            text_to_insert.append('BACOWR Metadata:\n')
            for key, value in metadata.items():
                text_to_insert.append(f'{key}: {value}\n')

        # Add main content
        for section in sections:
            if section['type'] == 'heading':
                text_to_insert.append(f"\n{section['text']}\n\n")
            elif section['type'] == 'paragraph':
                text_to_insert.append(f"{section['text']}\n\n")

        # Insert all text at once
        full_text = ''.join(text_to_insert)
        requests.append({
            'insertText': {
                'location': {'index': 1},
                'text': full_text
            }
        })

        # Execute text insertion
        self.docs_service.documents().batchUpdate(
            documentId=document_id,
            body={'requests': requests}
        ).execute()

        # Apply formatting (headings, bold, links, etc.)
        formatting_requests = self._create_formatting_requests(
            sections,
            backlink_info
        )

        if formatting_requests:
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': formatting_requests}
            ).execute()

    def _parse_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse article content into structured sections.

        Supports simple markdown:
        - # Heading 1
        - ## Heading 2
        - ### Heading 3
        - Regular paragraphs

        Args:
            content: Article text

        Returns:
            List of section dictionaries
        """
        sections = []
        lines = content.split('\n')
        current_paragraph = []

        for line in lines:
            line = line.strip()

            if not line:
                # Empty line - finish current paragraph
                if current_paragraph:
                    sections.append({
                        'type': 'paragraph',
                        'text': ' '.join(current_paragraph)
                    })
                    current_paragraph = []
                continue

            # Check for headings
            if line.startswith('### '):
                if current_paragraph:
                    sections.append({
                        'type': 'paragraph',
                        'text': ' '.join(current_paragraph)
                    })
                    current_paragraph = []
                sections.append({
                    'type': 'heading',
                    'level': 3,
                    'text': line[4:]
                })
            elif line.startswith('## '):
                if current_paragraph:
                    sections.append({
                        'type': 'paragraph',
                        'text': ' '.join(current_paragraph)
                    })
                    current_paragraph = []
                sections.append({
                    'type': 'heading',
                    'level': 2,
                    'text': line[3:]
                })
            elif line.startswith('# '):
                if current_paragraph:
                    sections.append({
                        'type': 'paragraph',
                        'text': ' '.join(current_paragraph)
                    })
                    current_paragraph = []
                sections.append({
                    'type': 'heading',
                    'level': 1,
                    'text': line[2:]
                })
            else:
                # Regular paragraph line
                current_paragraph.append(line)

        # Add final paragraph if exists
        if current_paragraph:
            sections.append({
                'type': 'paragraph',
                'text': ' '.join(current_paragraph)
            })

        return sections

    def _create_formatting_requests(
        self,
        sections: List[Dict[str, Any]],
        backlink_info: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Create formatting requests for document.

        Args:
            sections: Parsed content sections
            backlink_info: Backlink anchor and target URL

        Returns:
            List of Google Docs API requests
        """
        requests = []
        current_index = 1  # Google Docs index starts at 1

        for section in sections:
            text = section['text']
            text_length = len(text)

            if section['type'] == 'heading':
                # Style as heading
                heading_style = f"HEADING_{section['level']}"
                requests.append({
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + text_length
                        },
                        'paragraphStyle': {
                            'namedStyleType': heading_style
                        },
                        'fields': 'namedStyleType'
                    }
                })

            # Highlight backlink if present
            if backlink_info:
                anchor_text = backlink_info.get('anchor_text', '')
                target_url = backlink_info.get('target_url', '')

                if anchor_text and anchor_text in text:
                    # Find anchor position in text
                    anchor_start = text.find(anchor_text)
                    if anchor_start != -1:
                        anchor_index = current_index + anchor_start
                        anchor_end = anchor_index + len(anchor_text)

                        # Add link
                        requests.append({
                            'updateTextStyle': {
                                'range': {
                                    'startIndex': anchor_index,
                                    'endIndex': anchor_end
                                },
                                'textStyle': {
                                    'link': {'url': target_url},
                                    'bold': True,
                                    'foregroundColor': {
                                        'color': {
                                            'rgbColor': {
                                                'red': 0.0,
                                                'green': 0.4,
                                                'blue': 0.8
                                            }
                                        }
                                    }
                                },
                                'fields': 'link,bold,foregroundColor'
                            }
                        })

            # Move index forward (text + newlines)
            current_index += text_length + 2  # +2 for \n\n

        return requests

    def _share_document(
        self,
        document_id: str,
        email: str,
        role: str = 'writer'
    ):
        """
        Share document with email.

        Args:
            document_id: Document ID
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
                fileId=document_id,
                body=permission,
                fields='id'
            ).execute()
        except HttpError as e:
            print(f"Warning: Could not share document: {str(e)}")

    def export_job_to_doc(
        self,
        job_data: Dict[str, Any],
        share_with_email: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Export a BACOWR job to Google Doc.

        Args:
            job_data: Job data dictionary from database
            share_with_email: Optional email to share with

        Returns:
            Dictionary with document_id and document_url
        """
        # Extract data
        publisher = job_data.get('publisher_domain', 'Unknown')
        anchor_text = job_data.get('anchor_text', '')
        article_text = job_data.get('article_text', '')
        target_url = job_data.get('target_url', '')
        job_id = job_data.get('id', '')

        # Generate title
        title = f"{publisher} - {anchor_text[:50]}"

        # Prepare backlink info
        backlink_info = {
            'anchor_text': anchor_text,
            'target_url': target_url
        }

        # Prepare metadata
        metadata = {
            'Job ID': job_id,
            'Publisher': publisher,
            'Created': str(job_data.get('created_at', '')),
            'Status': job_data.get('status', ''),
            'QC Score': str(job_data.get('qc_report', {}).get('score', 'N/A'))
        }

        # Create document
        return self.create_document(
            title=title,
            content=article_text,
            backlink_info=backlink_info,
            metadata=metadata,
            share_with_email=share_with_email
        )

    def get_document_url(self, document_id: str) -> str:
        """Get shareable URL for document."""
        return f"https://docs.google.com/document/d/{document_id}"
