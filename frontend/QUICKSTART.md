# BACOWR Frontend - Quick Start Guide

Get your frontend up and running in 5 minutes!

## Prerequisites

- Node.js 18+ installed
- Backend running (see main BACOWR README)
- Terminal/command line access

## Step 1: Installation

```bash
cd /path/to/BACOWR/frontend
npm install
```

This will install all dependencies (~2 minutes).

## Step 2: Configuration

Create `.env.local`:

```bash
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
```

Or manually create the file with these values.

## Step 3: Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

You should see the BACOWR Dashboard!

## Step 4: Test the Quick Start Widget

1. On the Dashboard, find the "Quick Start" widget
2. Fill in:
   - **Publisher Domain**: `example.com`
   - **Target URL**: `https://wikipedia.org/wiki/AI`
   - **Anchor Text**: `learn about AI`
3. Click "Generate Article"
4. Watch real-time progress
5. View your article in ~30-60 seconds

## Common Issues

### Port Already in Use

If port 3000 is taken:

```bash
# Use different port
PORT=3001 npm run dev
```

### Cannot Connect to Backend

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check `.env.local` settings

3. Ensure no firewall blocking localhost

### TypeScript Errors

```bash
# Run type check
npm run type-check

# If issues persist, clear cache
rm -rf .next node_modules
npm install
```

## What's Next?

### Explore Features

- **Dashboard**: View stats, recent jobs, live monitoring
- **New Job**: 4-step wizard for detailed job creation
- **Jobs**: Browse all jobs with filters
- **Backlinks**: Library of 3000+ historical backlinks
- **Settings**: Configure API keys and defaults

### Configure API Keys

1. Go to Settings page
2. Add your LLM API keys:
   - Anthropic Claude
   - OpenAI GPT
   - Google Gemini
   - Ahrefs (optional)
3. Test each key
4. Save settings

### Create Your First Real Job

1. Click "New Job" in sidebar
2. Follow 4-step wizard:
   - Input your details
   - Choose LLM provider
   - Select strategy
   - Review and submit
3. Monitor real-time progress
4. View generated article with QC report

## Development Tips

### Hot Reload

Changes to files auto-reload the browser. No manual refresh needed!

### Component Development

```tsx
// Create new component
// src/components/mycomponent.tsx

import React from 'react'
import { Card } from '@/components/ui/card'

export function MyComponent() {
  return (
    <Card>
      <p>Hello BACOWR!</p>
    </Card>
  )
}
```

### Using API Client

```tsx
import { jobsAPI } from '@/lib/api/client'

// In component
const { data } = useQuery({
  queryKey: ['jobs'],
  queryFn: () => jobsAPI.list()
})
```

### Adding New Page

```tsx
// Create: src/app/mypage/page.tsx

'use client'

export default function MyPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold">My Page</h1>
    </div>
  )
}
```

Access at: [http://localhost:3000/mypage](http://localhost:3000/mypage)

## Production Deployment

### Build for Production

```bash
npm run build
npm start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

Set environment variables in Vercel dashboard.

## Resources

- **README.md**: Complete documentation
- **DESIGN.md**: Design system and components
- **Main BACOWR README**: Backend documentation

## Support

- GitHub Issues
- Check main BACOWR documentation
- Review browser console for errors

---

**Happy building with BACOWR!**
