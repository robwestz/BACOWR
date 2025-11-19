# Hoppscotch API Collections

Pre-configured API collections for testing BACOWR endpoints with [Hoppscotch](https://hoppscotch.io/).

## Quick Start

### 1. Install Hoppscotch

**Web Version:** https://hoppscotch.io/
**Desktop App:** https://hoppscotch.io/download

### 2. Import Collections

1. Open Hoppscotch
2. Click **"My Collections"** in sidebar
3. Click **"Import/Export"**
4. Click **"Import"**
5. Select one of the JSON files from this directory

### 3. Configure API Key

Before sending requests, replace `YOUR_API_KEY_HERE` with your actual API key:

1. Open imported collection
2. Click on any request
3. Go to **Headers** tab
4. Update `X-API-Key` value

**Get your API key:**
```bash
cd api
cat .api_key
```

Or create a new user via API and get the API key from response.

### 4. Set Environment Variables

For easier testing, set up environment variables:

1. Click **Environments** in Hoppscotch
2. Create new environment (e.g., "Local Development")
3. Add variables:

```
BASE_URL = http://localhost:8000
API_KEY = your-api-key-here
JOB_ID = (will be filled from responses)
BATCH_ID = (will be filled from responses)
ITEM_ID = (will be filled from responses)
USER_ID = (will be filled from responses)
```

4. Use variables in requests:
   - Endpoint: `<<BASE_URL>>/api/v1/jobs`
   - Header: `X-API-Key: <<API_KEY>>`

## Available Collections

### BACOWR_Jobs.json
Test job creation and management:
- Create Job
- List Jobs
- Get Job by ID
- Get Job Article
- Delete Job

### BACOWR_Batches.json
Test batch review workflow (Day 2 QA):
- Create Batch
- List Batches
- Get Batch Details
- Get Batch Items
- Approve Item
- Reject Item
- Request Regeneration
- Execute Regeneration
- Export Batch
- Get Batch Stats

### BACOWR_Analytics_Audit.json
Test analytics and audit endpoints:

**Analytics:**
- Cost Estimate
- Analytics Summary
- Provider Stats

**Audit (Admin Only):**
- List Audit Logs
- Get User Activity
- Get Security Events
- Get Failed Actions
- Get Audit Stats

## Testing Workflow

### Test Single Job Creation

1. Open **BACOWR_Jobs** collection
2. Send **"Create Job"** request
3. Copy `job_id` from response
4. Paste into `{{JOB_ID}}` placeholder in other requests
5. Send **"Get Job by ID"** to check status
6. Send **"Get Job Article"** to view generated article

### Test Batch Review

1. Create 2-3 jobs first (see above)
2. Open **BACOWR_Batches** collection
3. Send **"Create Batch"** with job IDs
4. Copy `batch_id` from response
5. Send **"Get Batch Items"** to list items
6. Copy an `item_id` from response
7. Send **"Approve Item"** or **"Reject Item"**
8. Send **"Get Batch Stats"** to see updated statistics
9. Send **"Export Batch"** to export approved items

## Tips

### Use Test Scripts

Hoppscotch supports test scripts for automation:

```javascript
// After "Create Job" request
pw.env.set("JOB_ID", pm.response.json().id);

// After "Create Batch" request
pw.env.set("BATCH_ID", pm.response.json().id);
```

### Check Response Status

Verify successful requests:
- `201 Created` - Resource created
- `200 OK` - Request successful
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid/missing API key
- `404 Not Found` - Resource doesn't exist

### Enable Mock Mode

For testing without LLM API keys:
```bash
export BACOWR_LLM_MODE=mock
```

Then start the API server. All jobs will complete instantly with mock data.

## Troubleshooting

### "Invalid API Key"
- Check that API key is correct
- Ensure `X-API-Key` header is set
- Verify API server is running

### "Connection Refused"
- Ensure API server is running: `cd api && python -m app.main`
- Check BASE_URL is correct: `http://localhost:8000`

### "Job not found"
- Wait a few seconds for job to complete
- Verify JOB_ID is correct
- Check job list to see all jobs

### Rate Limiting
If you see rate limit errors, wait a minute or adjust rate limits in server config.

## Alternative Tools

These collections can also be imported into:
- **Postman** - Convert JSON format or use OpenAPI import
- **Insomnia** - Import as Postman collection
- **Thunder Client** (VS Code) - Manual setup
- **REST Client** (VS Code) - See `.http` example below

### VS Code REST Client Example

Create `test.http`:
```http
### Variables
@baseUrl = http://localhost:8000
@apiKey = your-api-key-here

### Health Check
GET {{baseUrl}}/health

### Create Job
POST {{baseUrl}}/api/v1/jobs
X-API-Key: {{apiKey}}
Content-Type: application/json

{
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://sv.wikipedia.org/wiki/AI",
  "anchor_text": "AI"
}
```

## Support

For API documentation, see:
- Swagger UI: http://localhost:8000/docs
- OpenAPI spec: `docs/api/openapi.json`
- API Guide: `API_GUIDE.md`
