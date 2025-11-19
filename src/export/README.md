# BACOWR Google Workspace Export

Export BACOWR articles to Google Sheets and Google Docs automatically.

## Features

- ✅ **Google Sheets Export**: Create spreadsheets with job metadata (publisher, anchor, QC score, cost)
- ✅ **Google Docs Export**: Full article text with formatting and clickable backlinks
- ✅ **Batch Export**: Export 100+ jobs to a single spreadsheet with linked documents
- ✅ **Automatic Linking**: Sheet rows link directly to Google Docs
- ✅ **Sharing**: Auto-share spreadsheets/docs with team members
- ✅ **Authentication**: Support for both Service Account (production) and OAuth (development)

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-api-python-client` - Google Sheets & Docs API
- `google-auth` - Authentication
- `google-auth-oauthlib` - OAuth 2.0
- `google-auth-httplib2` - HTTP client

### 2. Setup Google Service Account

#### Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create new project: "BACOWR Export"
3. Note the Project ID

#### Enable APIs
1. Go to **APIs & Services > Library**
2. Enable:
   - Google Sheets API
   - Google Docs API
   - Google Drive API

#### Create Service Account
1. Go to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
   - Name: `bacowr-export`
   - ID: `bacowr-export`
3. Grant role: **Editor**
4. Click **Done**

#### Create Key
1. Click on the service account
2. Go to **Keys** tab
3. Click **Add Key > Create new key**
4. Choose **JSON**
5. Download file (e.g., `bacowr-service-account.json`)

#### Save Credentials
```bash
mkdir -p credentials
mv ~/Downloads/bacowr-service-account.json credentials/google_credentials.json
```

#### Configure Environment
```bash
# Add to .env
GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
USE_SERVICE_ACCOUNT=true
```

### 3. Share Spreadsheet

**IMPORTANT**: Service Accounts have their own email address. You must share your Google Sheets/Folders with this email.

Find the service account email in `credentials/google_credentials.json`:
```json
{
  "client_email": "bacowr-export@your-project.iam.gserviceaccount.com"
}
```

Share your Google Sheet or Drive folder with this email (Editor permission).

---

## Usage

### Export Single Job

#### Via API

```bash
# Export to Google Sheets + Docs
curl -X POST http://localhost:8000/api/v1/export/jobs/{job_id}/google-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "create_doc": true,
    "share_with_email": "team@example.com"
  }'

# Export to Google Docs only
curl -X POST http://localhost:8000/api/v1/export/jobs/{job_id}/google-docs \
  -H "Content-Type: application/json" \
  -d '{
    "share_with_email": "team@example.com"
  }'
```

#### Via Python

```python
from src.export import GoogleAuthManager, GoogleSheetsExporter, GoogleDocsExporter

# Initialize
auth = GoogleAuthManager()
sheets_exporter = GoogleSheetsExporter(auth)
docs_exporter = GoogleDocsExporter(auth)

# Export job
job_data = {
    'id': 'job_123',
    'publisher_domain': 'aftonbladet.se',
    'anchor_text': 'best tools',
    'target_url': 'https://example.com',
    'article_text': '...',
    'status': 'delivered',
    'qc_report': {'score': 92},
    'actual_cost': 0.12
}

# Create Google Doc
doc_info = docs_exporter.export_job_to_doc(job_data)
print(f"Document created: {doc_info['document_url']}")

# Create/update Google Sheet
sheet_info = sheets_exporter.create_spreadsheet(
    title="BACOWR Articles - Nov 2025",
    share_with_email="team@example.com"
)
spreadsheet_id = sheet_info['spreadsheet_id']

# Add job to sheet
sheets_exporter.export_job(
    spreadsheet_id=spreadsheet_id,
    job_data=job_data,
    doc_url=doc_info['document_url']
)
print(f"Sheet updated: {sheet_info['spreadsheet_url']}")
```

---

### Export Batch

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/export/batches/{batch_id}/google-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "batch_name": "Swedish News Sites - Dec 2025",
    "create_docs": true,
    "share_with_email": "team@example.com"
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Batch exported successfully: 175/175 jobs",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/abc123",
  "jobs_exported": 175
}
```

#### Via Python

```python
# Export batch
batch_jobs = [...]  # List of job data dicts

export_result = sheets_exporter.export_batch(
    batch_jobs=batch_jobs,
    batch_name="Swedish News Sites - Dec 2025",
    doc_urls={},  # Will be populated if create_docs=True
    share_with_email="team@example.com"
)

print(f"Exported: {export_result['exported']}/{export_result['total_jobs']}")
print(f"Spreadsheet: {export_result['spreadsheet_url']}")
```

---

## Google Sheets Structure

**Sheet 1: BACOWR Articles**

| Job ID | Created | Publisher | Target URL | Anchor | Status | QC Score | Word Count | Cost | Article (Link) | Notes |
|--------|---------|-----------|------------|--------|--------|----------|------------|------|----------------|-------|
| job_abc | 2025-11-19 | aftonbladet.se | https://... | best tools | DELIVER | 92 | 1247 | $0.12 | [View Doc](link) | |
| job_xyz | 2025-11-19 | svd.se | https://... | top software | DELIVER | 88 | 1103 | $0.10 | [View Doc](link) | |

**Sheet 2: Batch Summary**

```
BACOWR Batch Export Summary

Batch Name:          Swedish News Sites - Dec 2025
Export Date:         2025-11-19 14:30:00

Total Jobs:          175
Exported Successfully: 175
Failed:              0
Success Rate:        100.0%
```

---

## Google Docs Structure

**Document Title**: `{publisher_domain} - {anchor_text}`

**Content**:
- Formatted article text (H1, H2, H3, paragraphs)
- **Highlighted backlink** (bold, blue, clickable)
- Metadata footer (Job ID, Publisher, Created, Status, QC Score)

---

## Authentication Methods

### Service Account (Recommended for Production)

✅ **Pros**:
- Server-to-server (no user interaction)
- Works in automated workflows
- No token expiration
- Better for multi-user systems

❌ **Cons**:
- Requires sharing spreadsheets with service account email
- Slightly more setup

**Use when**: Production, automation, APIs

### OAuth 2.0 (For Development)

✅ **Pros**:
- Works with personal Google account
- No need to share spreadsheets
- Simpler for testing

❌ **Cons**:
- Requires browser consent on first use
- Token expires (needs refresh)
- Not suitable for automation

**Use when**: Local development, testing

---

## API Endpoints

### POST /api/v1/export/jobs/{job_id}/google-sheets

Export single job to Google Sheets.

**Request Body**:
```json
{
  "spreadsheet_id": "optional_existing_sheet_id",
  "share_with_email": "team@example.com",
  "create_doc": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Job exported successfully",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/...",
  "document_url": "https://docs.google.com/document/d/...",
  "jobs_exported": 1
}
```

---

### POST /api/v1/export/jobs/{job_id}/google-docs

Export single job to Google Docs only.

**Request Body**:
```json
{
  "share_with_email": "team@example.com"
}
```

---

### POST /api/v1/export/batches/{batch_id}/google-sheets

Export batch of jobs.

**Request Body**:
```json
{
  "batch_name": "Batch Name",
  "create_docs": true,
  "share_with_email": "team@example.com",
  "job_ids": ["job_1", "job_2"]  // optional - exports all if omitted
}
```

---

### GET /api/v1/export/google/auth/status

Check Google authentication status and get setup instructions.

**Response**:
```json
{
  "credentials_path": "credentials/google_credentials.json",
  "validation": {
    "valid": true,
    "type": "service_account",
    "email": "bacowr-export@project.iam.gserviceaccount.com",
    "project_id": "bacowr-export"
  },
  "instructions": "..."
}
```

---

## Troubleshooting

### Error: "Credentials file not found"

**Solution**: Create Service Account and save credentials JSON:
```bash
mkdir -p credentials
# Place google_credentials.json in credentials/
export GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
```

---

### Error: "The caller does not have permission"

**Problem**: Service Account email not shared on spreadsheet/folder.

**Solution**:
1. Open `credentials/google_credentials.json`
2. Copy `client_email` value
3. Share your Google Sheet/Folder with this email
4. Grant "Editor" permission

---

### Error: "Invalid credentials format"

**Problem**: Wrong credentials file or corrupted JSON.

**Solution**:
1. Validate JSON: `python -m json.tool credentials/google_credentials.json`
2. Re-download credentials from Google Cloud Console
3. Ensure file contains `client_email` and `private_key` (Service Account)

---

### Error: "Access blocked: OAuth client"

**Problem**: OAuth app not verified (only for OAuth flow).

**Solution**:
- Use Service Account instead (recommended)
- Or verify your OAuth app in Google Cloud Console

---

## Examples

### Example 1: Bulk Export After Batch Processing

```python
# After batch processing
batch_id = "batch_abc123"
jobs = Job.query.filter_by(status="delivered").all()

# Export to Google
auth = GoogleAuthManager()
sheets = GoogleSheetsExporter(auth)
docs = GoogleDocsExporter(auth)

# Create docs for each job
doc_urls = {}
for job in jobs:
    doc_info = docs.export_job_to_doc(job.__dict__)
    doc_urls[job.id] = doc_info['document_url']

# Export to sheet
result = sheets.export_batch(
    batch_jobs=[job.__dict__ for job in jobs],
    batch_name=f"Batch {batch_id}",
    doc_urls=doc_urls
)

print(f"✅ Exported {result['exported']} jobs")
print(f"📊 Spreadsheet: {result['spreadsheet_url']}")
```

---

### Example 2: Update Job Status in Existing Sheet

```python
# Update job status after manual review
sheets.update_job_status(
    spreadsheet_id="your_sheet_id",
    job_id="job_123",
    status="APPROVED",
    qc_score=95,
    notes="Manually reviewed and approved"
)
```

---

## Security Best Practices

1. **Never commit credentials to Git**:
   ```bash
   # .gitignore
   credentials/
   *.json
   ```

2. **Use Service Account in production** (not OAuth)

3. **Limit Service Account permissions**:
   - Only grant "Editor" on specific folders
   - Don't use "Owner" role

4. **Rotate keys periodically**:
   - Delete old keys in Google Cloud Console
   - Generate new key every 90 days

5. **Environment variables for paths**:
   ```python
   GOOGLE_CREDENTIALS_PATH=credentials/google_credentials.json
   ```

---

## Performance

- **Single job export**: ~2-3 seconds
- **Batch export (100 jobs)**: ~2-3 minutes (with docs)
- **Batch export (100 jobs, sheets only)**: ~30 seconds

**Tips for faster exports**:
- Create docs in parallel (async)
- Use batch API methods when available
- Cache auth tokens (already handled)

---

## Support

**Issues**: https://github.com/bacowr/bacowr/issues
**Docs**: https://docs.bacowr.com
**Google API Docs**: https://developers.google.com/sheets/api

---

**Module Status**: ✅ Production Ready

**Dependencies**:
- google-api-python-client >= 2.100.0
- google-auth >= 2.23.0
- google-auth-oauthlib >= 1.1.0

**Maintained by**: Module Q (Vision & Quality) + Delta Team (Integrations)
