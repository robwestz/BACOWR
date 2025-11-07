# BACOWR Frontend Design System

**Complete design specification and component documentation**

## Design Philosophy

BACOWR Frontend follows these core principles:

1. **Speed First**: Instant-feeling interactions, optimistic updates
2. **Beautiful by Default**: Figma-quality design out of the box
3. **Accessible**: WCAG AA compliant, keyboard-first
4. **Consistent**: Design tokens ensure visual harmony
5. **Extensible**: Plugin-ready architecture for future tools

Inspired by: Linear, Vercel Dashboard, Notion, Stripe

## Color System

### Light Mode

```css
/* Primary - Brand Blue */
--primary: 221.2 83.2% 53.3%
--primary-foreground: 210 40% 98%

/* Secondary - Subtle Gray */
--secondary: 210 40% 96.1%
--secondary-foreground: 222.2 47.4% 11.2%

/* Destructive - Error Red */
--destructive: 0 84.2% 60.2%
--destructive-foreground: 210 40% 98%

/* Success - Green */
--success: 142 76% 36%
--success-foreground: 0 0% 100%

/* Warning - Yellow */
--warning: 38 92% 50%
--warning-foreground: 0 0% 0%

/* Muted - Background */
--muted: 210 40% 96.1%
--muted-foreground: 215.4 16.3% 46.9%

/* Accent - Highlight */
--accent: 210 40% 96.1%
--accent-foreground: 222.2 47.4% 11.2%

/* Background/Foreground */
--background: 0 0% 100%
--foreground: 222.2 84% 4.9%

/* Border/Input/Ring */
--border: 214.3 31.8% 91.4%
--input: 214.3 31.8% 91.4%
--ring: 221.2 83.2% 53.3%
```

### Dark Mode

```css
--background: 222.2 84% 4.9%
--foreground: 210 40% 98%

--primary: 217.2 91.2% 59.8%
--primary-foreground: 222.2 47.4% 11.2%

--secondary: 217.2 32.6% 17.5%
--secondary-foreground: 210 40% 98%

--muted: 217.2 32.6% 17.5%
--muted-foreground: 215 20.2% 65.1%

--border: 217.2 32.6% 17.5%
--input: 217.2 32.6% 17.5%
--ring: 224.3 76.3% 48%
```

### Usage

```tsx
// Tailwind classes automatically use design tokens
<div className="bg-primary text-primary-foreground" />
<div className="border-border bg-background" />
```

## Typography

### Font Stack

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Scale

| Name | Size | Line Height | Usage |
|------|------|-------------|-------|
| xs | 12px | 16px | Captions, labels |
| sm | 14px | 20px | Body text, buttons |
| base | 16px | 24px | Default body |
| lg | 18px | 28px | Large body |
| xl | 20px | 28px | Small headings |
| 2xl | 24px | 32px | Section headings |
| 3xl | 30px | 36px | Page headings |
| 4xl | 36px | 40px | Hero headings |

### Weights

- **Regular** (400): Body text
- **Medium** (500): Emphasis, labels
- **Semibold** (600): Subheadings
- **Bold** (700): Headings

### Usage

```tsx
<h1 className="text-3xl font-bold">Page Title</h1>
<p className="text-sm text-muted-foreground">Description</p>
```

## Spacing

### Scale (Tailwind)

```
0   = 0px
0.5 = 2px
1   = 4px
2   = 8px
3   = 12px
4   = 16px
5   = 20px
6   = 24px
8   = 32px
10  = 40px
12  = 48px
16  = 64px
20  = 80px
24  = 96px
```

### Layout Spacing

- **Page padding**: `p-6` (24px)
- **Card padding**: `p-6` (24px)
- **Stack spacing**: `space-y-4` or `space-y-6`
- **Inline spacing**: `gap-2` or `gap-4`

### Usage

```tsx
<div className="space-y-6">        {/* Vertical stack */}
  <Card className="p-6">           {/* Card padding */}
    <div className="flex gap-4">   {/* Inline items */}
      ...
    </div>
  </Card>
</div>
```

## Components

### Button

**Variants**: default, destructive, outline, secondary, ghost, link

**Sizes**: default (h-10), sm (h-9), lg (h-11), icon (h-10 w-10)

```tsx
// Primary action
<Button>Create Job</Button>

// Secondary action
<Button variant="outline">Cancel</Button>

// Destructive action
<Button variant="destructive">Delete</Button>

// Loading state
<Button isLoading>Processing...</Button>

// With icon
<Button>
  <Plus className="h-4 w-4 mr-2" />
  New Job
</Button>
```

### Card

**Structure**: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter

```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    {/* Actions */}
  </CardFooter>
</Card>
```

**Hover Effects**:
```tsx
<Card className="hover:shadow-md transition-shadow">
```

### Badge

**Variants**: default, secondary, destructive, outline, success, warning

```tsx
<Badge>Default</Badge>
<Badge variant="success">Delivered</Badge>
<Badge variant="destructive">Blocked</Badge>
<Badge variant="warning">Processing</Badge>
```

### Input

**Types**: text, email, url, number, password

```tsx
// Basic input
<Input placeholder="Enter text..." />

// With label
<div>
  <label className="text-sm font-medium mb-2 block">
    Email
  </label>
  <Input type="email" placeholder="you@example.com" />
</div>

// With icon
<div className="relative">
  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" />
  <Input className="pl-10" placeholder="Search..." />
</div>
```

### Progress

**Usage**: Job progress, loading states

```tsx
// Basic progress
<Progress value={60} max={100} />

// With label
<Progress value={60} showLabel />

// Styled
<div className="space-y-2">
  <div className="flex justify-between text-sm">
    <span>Generating...</span>
    <span>60%</span>
  </div>
  <Progress value={60} />
</div>
```

### Tabs

**Structure**: Tabs, TabsList, TabsTrigger, TabsContent

```tsx
<Tabs defaultValue="article">
  <TabsList>
    <TabsTrigger value="article">Article</TabsTrigger>
    <TabsTrigger value="qc">QC Report</TabsTrigger>
    <TabsTrigger value="details">Details</TabsTrigger>
  </TabsList>

  <TabsContent value="article">
    {/* Article content */}
  </TabsContent>

  <TabsContent value="qc">
    {/* QC content */}
  </TabsContent>
</Tabs>
```

## Custom Components

### JobCard

**Purpose**: Display job summary in lists

**Props**:
- `job: JobPackage` - Job data
- `onViewDetails?: () => void` - View callback
- `onDelete?: () => void` - Delete callback

```tsx
<JobCard
  job={job}
  onViewDetails={() => router.push(`/jobs/${job.job_meta.job_id}`)}
/>
```

### JobProgressBar

**Purpose**: Real-time job progress

**Props**:
- `jobId: string` - Job ID
- `status: JobStatus` - Current status
- `progress: number` - 0-100
- `message?: string` - Status message
- `compact?: boolean` - Compact mode

```tsx
// Full version
<JobProgressBar
  jobId="job_123"
  status="RUNNING"
  progress={45}
  message="Generating article..."
/>

// Compact version
<JobProgressBar
  jobId="job_123"
  status="RUNNING"
  progress={45}
  compact
/>
```

### QCBadge

**Purpose**: QC status indicator

**Props**:
- `status: QCStatus` - PASS, PASS_WITH_AUTOFIX, BLOCKED
- `score?: number` - QC score (0-100)
- `showIcon?: boolean` - Show icon (default: true)

```tsx
<QCBadge status="PASS" score={95} />
<QCBadge status="PASS_WITH_AUTOFIX" score={82} />
<QCBadge status="BLOCKED" />
```

### QuickStartWidget

**Purpose**: Single-form job creation on dashboard

**Features**:
- 3 input fields (publisher, target, anchor)
- Instant validation
- Real-time job creation
- Automatic navigation

```tsx
<QuickStartWidget />
```

### StatsCard

**Purpose**: Display key metrics

**Props**:
- `title: string` - Card title
- `value: string | number` - Main value
- `icon?: ReactNode` - Icon element
- `trend?: { value: number; label: string }` - Trend indicator

```tsx
<StatsCard
  title="Total Jobs"
  value={142}
  icon={<FileText className="h-6 w-6" />}
  trend={{ value: 12, label: 'from last month' }}
/>
```

### LiveJobsMonitor

**Purpose**: Real-time WebSocket job monitoring

**Features**:
- Auto-connects to WebSocket
- Shows running/pending jobs
- Live progress updates
- Compact progress bars

```tsx
<LiveJobsMonitor />
```

### CostChart

**Purpose**: Cost visualization over time

**Props**:
- `data: Array<{ date: string; cost: number }>` - Timeline data

```tsx
<CostChart
  data={[
    { date: '2025-11-01', cost: 2.5 },
    { date: '2025-11-02', cost: 3.2 },
    // ...
  ]}
/>
```

## Layout

### Page Structure

```tsx
<div className="space-y-6">
  {/* Page Header */}
  <div>
    <h1 className="text-3xl font-bold">Page Title</h1>
    <p className="text-muted-foreground mt-1">
      Description text
    </p>
  </div>

  {/* Content Sections */}
  <Card>
    {/* ... */}
  </Card>

  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Card>{/* ... */}</Card>
    <Card>{/* ... */}</Card>
  </div>
</div>
```

### Sidebar

**Width**:
- Expanded: `w-64` (256px)
- Collapsed: `w-16` (64px)

**Navigation**:
- Dashboard (`/`)
- New Job (`/jobs/new`)
- Jobs (`/jobs`)
- Backlinks (`/backlinks`)
- Settings (`/settings`)

### Header

**Height**: `h-16` (64px)

**Features**:
- Search/Command palette (⌘K)
- Notifications
- Dark mode toggle
- Environment badge

### Responsive Grid

```tsx
// 1 column mobile, 2 tablet, 3 desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// 1 column mobile, 4 desktop
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
```

## Animations

### Transitions

**Default**: All color transitions are 200ms

```css
* {
  transition: colors 200ms;
}
```

### Keyframes

```css
/* Fade In */
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide In */
@keyframes slide-in {
  from {
    transform: translateY(10px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
```

### Usage

```tsx
<div className="animate-fade-in">Content</div>
<div className="animate-slide-in">Content</div>
<div className="animate-spin">{/* Loader */}</div>
```

## Icons

**Library**: Lucide React

**Size**: Typically `h-4 w-4` (16px) or `h-5 w-5` (20px)

```tsx
import { FileText, Plus, Search } from 'lucide-react'

<FileText className="h-4 w-4" />
<Plus className="h-5 w-5 text-primary" />
<Search className="h-4 w-4 text-muted-foreground" />
```

### Common Icons

| Icon | Usage |
|------|-------|
| `Zap` | Quick actions, branding |
| `FileText` | Documents, articles |
| `Plus` | Create actions |
| `Search` | Search inputs |
| `Settings` | Settings pages |
| `CheckCircle2` | Success states |
| `XCircle` | Error states |
| `AlertCircle` | Warning states |
| `Loader2` | Loading (with animate-spin) |
| `DollarSign` | Cost/pricing |
| `Clock` | Time/duration |
| `ExternalLink` | External links |

## Patterns

### Loading States

```tsx
// Full page loader
if (isLoading) {
  return (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
    </div>
  )
}

// Button loading
<Button isLoading>Processing...</Button>

// Skeleton (future)
<div className="animate-pulse bg-muted h-20 rounded-lg" />
```

### Empty States

```tsx
<div className="text-center py-12 text-muted-foreground">
  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
  <p>No jobs yet. Create your first one!</p>
  <Button className="mt-4">Get Started</Button>
</div>
```

### Error States

```tsx
<Card className="border-destructive">
  <CardContent className="pt-6">
    <div className="flex items-center gap-3 text-destructive">
      <XCircle className="h-5 w-5" />
      <div>
        <p className="font-semibold">Error</p>
        <p className="text-sm">{error.message}</p>
      </div>
    </div>
  </CardContent>
</Card>
```

### Forms

```tsx
<form onSubmit={handleSubmit} className="space-y-4">
  <div>
    <label className="text-sm font-medium mb-2 block">
      Field Label *
    </label>
    <Input
      placeholder="Placeholder..."
      value={value}
      onChange={(e) => setValue(e.target.value)}
      required
    />
    <p className="text-xs text-muted-foreground mt-1">
      Helper text
    </p>
  </div>

  <Button type="submit" className="w-full">
    Submit
  </Button>
</form>
```

## Accessibility

### Keyboard Navigation

- **Tab**: Navigate between interactive elements
- **Enter/Space**: Activate buttons/links
- **Escape**: Close modals/dropdowns
- **⌘K**: Open command palette

### Focus Management

```tsx
// Focus visible styling is automatic
*:focus-visible {
  outline: none;
  ring: 2px solid var(--ring);
  ring-offset: 2px;
}
```

### ARIA Labels

```tsx
<button aria-label="Close dialog">
  <X className="h-4 w-4" />
</button>

<div role="status" aria-live="polite">
  Job completed successfully
</div>
```

### Color Contrast

All color combinations meet WCAG AA standards:
- Text on background: 4.5:1 minimum
- Large text: 3:1 minimum
- UI components: 3:1 minimum

## Responsive Design

### Breakpoints

```css
/* Tailwind defaults */
sm: 640px   /* Tablet */
md: 768px   /* Desktop */
lg: 1024px  /* Large desktop */
xl: 1280px  /* Extra large */
2xl: 1536px /* Ultra wide */
```

### Mobile-First Approach

```tsx
// Stack on mobile, 2 columns on tablet, 3 on desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// Hide on mobile, show on desktop
<div className="hidden md:block">Desktop only</div>

// Show on mobile, hide on desktop
<div className="block md:hidden">Mobile only</div>
```

### Sidebar Behavior

- **Desktop**: Fixed sidebar, always visible
- **Tablet**: Collapsible sidebar
- **Mobile**: Overlay sidebar (future)

## Best Practices

### Component Composition

```tsx
// ✅ Good - Composable
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>

// ❌ Bad - Monolithic
<CustomCard title="Title" content="Content" />
```

### State Management

```tsx
// ✅ Good - Use stores for shared state
const jobs = useJobsStore((state) => state.recentJobs)

// ✅ Good - Use React Query for server state
const { data } = useQuery({
  queryKey: ['job', id],
  queryFn: () => jobsAPI.get(id)
})

// ❌ Bad - useState for server state
const [job, setJob] = useState(null)
useEffect(() => {
  fetch(`/api/jobs/${id}`).then(r => r.json()).then(setJob)
}, [id])
```

### Error Handling

```tsx
// ✅ Good - User-friendly errors
try {
  await jobsAPI.create(input)
  addToast({ type: 'success', title: 'Job Created' })
} catch (error) {
  addToast({
    type: 'error',
    title: 'Failed to Create Job',
    message: error instanceof Error ? error.message : 'Unknown error'
  })
}
```

### Performance

```tsx
// ✅ Good - Lazy load heavy components
const ArticleViewer = lazy(() => import('./ArticleViewer'))

// ✅ Good - Memoize expensive calculations
const sortedJobs = useMemo(
  () => jobs.sort((a, b) => a.created_at - b.created_at),
  [jobs]
)

// ✅ Good - Debounce search inputs
const debouncedSearch = useDebouncedValue(search, 300)
```

## Future Enhancements

### Command Palette

Global search and command execution (⌘K):
- Search jobs, backlinks
- Quick actions (New Job, Settings)
- Navigation

### Dark Mode Toggle

Already implemented in Header and UIStore:
- Persisted preference
- System preference detection
- Smooth transitions

### Notifications

Toast system ready for:
- Success messages
- Error alerts
- Info notifications
- Warning prompts

### Batch Operations

UI for batch job creation:
- CSV/JSON upload
- Bulk editing
- Progress tracking

### Analytics Dashboard

Enhanced data visualization:
- Time-series charts
- Provider comparisons
- Cost breakdown
- Performance metrics

---

**Design System Version**: 1.0.0
**Last Updated**: 2025-11-07
**Status**: Production Ready
