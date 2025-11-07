# BACOWR Frontend

**Production-Ready SEO Content Generation Platform**

A beautiful, modern, and lightning-fast frontend for BACOWR - the advanced backlink content generation engine.

## Overview

BACOWR Frontend is a Next.js 14-based web application that provides an intuitive interface for:

- **Quick Start Widget**: Generate your first article in under 60 seconds
- **Job Creation Wizard**: 4-step guided flow for creating content generation jobs
- **Real-Time Monitoring**: Live WebSocket updates for job progress
- **Backlinks Library**: Browse and analyze 3000+ historical backlinks
- **Cost Tracking**: Comprehensive analytics and cost visualization
- **Settings Management**: Easy API key configuration and defaults

## Tech Stack

- **Framework**: Next.js 14 (App Router) + TypeScript
- **Styling**: Tailwind CSS + Custom Design System
- **State Management**: Zustand + TanStack Query
- **Real-Time**: Socket.io Client
- **Charts**: Recharts
- **UI Components**: Radix UI + Custom Components
- **Markdown**: React Markdown

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- BACOWR Backend running (see main README)

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

## Features

### Dashboard

- **Quick Start Widget**: Single-form job creation
- **Live Jobs Monitor**: Real-time WebSocket updates
- **Stats Cards**: Total jobs, delivered, cost, duration
- **Cost Chart**: 30-day spending visualization
- **Recent Jobs**: Gallery of recent results

### Job Creation Wizard

4-step guided flow:

1. **Input**: Publisher, target URL, anchor text
2. **Provider**: Choose LLM (Claude, GPT, Gemini)
3. **Strategy**: Multi-stage vs Single-shot
4. **Review**: Summary and cost estimate

### Job Details

- **Article Viewer**: Beautiful markdown rendering
- **QC Report**: Issues, AutoFix logs, scores
- **Job Package**: Full JSON inspector
- **Execution Log**: Step-by-step trace
- **Export**: MD, PDF, HTML formats

### Backlinks Library

- **Search**: Filter by publisher, target, anchor
- **Analytics**: Total count, cost, QC scores
- **Generate Similar**: One-click similar content
- **Historical Data**: 3000+ backlinks browsing

### Settings

- **API Keys**: Configure Claude, GPT, Gemini, Ahrefs
- **Defaults**: Set default provider, strategy, country
- **Cost Limits**: Daily and per-job spending limits
- **Notifications**: Email and webhook alerts (coming soon)

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Dashboard
│   │   ├── jobs/
│   │   │   ├── new/          # Job creation wizard
│   │   │   └── [id]/         # Job details
│   │   ├── backlinks/        # Backlinks library
│   │   └── settings/         # Settings page
│   ├── components/
│   │   ├── ui/               # Base UI components
│   │   ├── dashboard/        # Dashboard components
│   │   ├── jobs/             # Job-related components
│   │   ├── backlinks/        # Backlinks components
│   │   ├── settings/         # Settings components
│   │   └── layout/           # Layout components
│   ├── lib/
│   │   ├── api/              # API client + WebSocket
│   │   ├── store/            # Zustand stores
│   │   └── utils/            # Utility functions
│   ├── types/                # TypeScript types
│   └── styles/               # Global styles
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Design System

### Colors

```css
--primary: 221.2 83.2% 53.3%      /* Blue */
--secondary: 210 40% 96.1%        /* Light Gray */
--destructive: 0 84.2% 60.2%      /* Red */
--success: 142 76% 36%            /* Green */
--warning: 38 92% 50%             /* Yellow */
--muted: 210 40% 96.1%            /* Muted */
```

### Typography

- **Font**: Inter (system font)
- **Headings**: Bold, tight tracking
- **Body**: Regular, readable line-height
- **Code**: Monospace for technical content

### Spacing

- **Base**: 4px (0.25rem)
- **Scale**: 4, 8, 12, 16, 24, 32, 48, 64, 96px

### Components

All components follow Radix UI patterns with custom styling:

- **Button**: 5 variants, 4 sizes, loading state
- **Card**: Header, content, footer sections
- **Badge**: Status indicators with colors
- **Progress**: Animated progress bars
- **Input**: Form inputs with validation

## API Integration

### REST API

All API calls use the centralized client in `src/lib/api/client.ts`:

```typescript
import { jobsAPI } from '@/lib/api/client'

// Create job
const job = await jobsAPI.create({
  publisher_domain: 'example.com',
  target_url: 'https://target.com',
  anchor_text: 'best solution',
})

// Get job
const job = await jobsAPI.get(jobId)

// List jobs
const { jobs, total } = await jobsAPI.list({ page: 1 })
```

### WebSocket

Real-time updates via Socket.io:

```typescript
import { useWebSocket } from '@/lib/api/websocket'

const { subscribeToJob, on } = useWebSocket()

// Subscribe to job updates
subscribeToJob(jobId)

// Listen for updates
on('job:update', (update) => {
  console.log(update.status, update.progress)
})
```

## State Management

### Zustand Stores

- **useJobsStore**: Recent jobs and active jobs
- **useToastStore**: Toast notifications
- **useSettingsStore**: User settings (persisted)
- **useUIStore**: UI state (sidebar, dark mode)
- **useCreateJobWizard**: Job creation wizard state

### TanStack Query

Used for server state management with caching:

```typescript
const { data, isLoading } = useQuery({
  queryKey: ['job', jobId],
  queryFn: () => jobsAPI.get(jobId),
})
```

## Performance

### Optimizations

- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Variable fonts with subsetting
- **CSS**: Tailwind with PurgeCSS
- **Bundle Size**: ~200KB gzipped

### Caching

- **API Responses**: 1 minute stale time
- **Static Assets**: Aggressive caching
- **Build Output**: Optimized chunks

## Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: ARIA labels and roles
- **Focus Management**: Visible focus indicators
- **Color Contrast**: WCAG AA compliant
- **Semantic HTML**: Proper heading structure

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Android)

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Production deployment
vercel --prod
```

### Environment Variables

Set in Vercel dashboard:

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_WS_URL`: WebSocket URL

### Custom Server

```bash
npm run build
npm start
```

Use nginx or similar as reverse proxy.

## Development

### Scripts

```bash
npm run dev        # Development server
npm run build      # Production build
npm run start      # Production server
npm run lint       # ESLint
npm run type-check # TypeScript check
```

### Code Quality

- **ESLint**: Code linting
- **TypeScript**: Type checking
- **Prettier**: Code formatting (optional)

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push origin feature/my-feature
```

## Testing

### Manual Testing

1. Start backend: `cd .. && python production_main.py ...`
2. Start frontend: `npm run dev`
3. Test all flows end-to-end

### E2E Testing (Future)

- Playwright or Cypress
- Critical user flows
- Visual regression testing

## Troubleshooting

### API Connection Issues

**Problem**: Cannot connect to backend

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check environment variables
echo $NEXT_PUBLIC_API_URL

# Update .env.local if needed
```

### WebSocket Not Connecting

**Problem**: Real-time updates not working

**Solution**:
```bash
# Verify WebSocket URL
echo $NEXT_PUBLIC_WS_URL

# Check browser console for errors
# Ensure backend WebSocket server is running
```

### Build Errors

**Problem**: `npm run build` fails

**Solution**:
```bash
# Clear cache and reinstall
rm -rf .next node_modules
npm install

# Run type check
npm run type-check

# Fix TypeScript errors before building
```

### Styling Issues

**Problem**: Styles not applying

**Solution**:
```bash
# Ensure Tailwind is configured
cat tailwind.config.ts

# Check globals.css is imported
# Clear Next.js cache
rm -rf .next
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

See main BACOWR LICENSE

## Support

- **Documentation**: See [DESIGN.md](DESIGN.md)
- **Issues**: GitHub Issues
- **Backend**: See main BACOWR README

---

**Built with ❤️ for production SEO workflows**

Version: 1.0.0
Last Updated: 2025-11-07
Status: Production Ready
