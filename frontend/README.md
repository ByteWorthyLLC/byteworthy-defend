# HifzDefend Web Dashboard

Modern React-based web dashboard for HifzDefend antivirus with real-time monitoring and control.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Beautiful component library
- **React Router** - Client-side routing
- **React Query** - Server state management
- **Zustand** - Client state management
- **Recharts** - Data visualization
- **Radix UI** - Accessible primitives
- **Lucide React** - Icon library

## Features

### ✅ Implemented

- **Dashboard** - Real-time system overview with threat statistics
- **Monitors** - Control all 13 security monitors with pause/resume/restart
- **Layout** - Responsive sidebar navigation with live status
- **API Client** - Full REST API integration
- **WebSocket** - Real-time event streaming
- **Dark Mode** - Built-in theme support

### 🚧 Coming Soon

- Scanner page with progress tracking
- Quarantine management
- AI Assistant chat interface
- Log viewer with search
- Settings configuration UI

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- HifzDefend backend running on `http://localhost:8080`

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server with hot reload:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Build for Production

Build optimized static files:

```bash
npm run build
```

Output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client
│   │   └── client.ts     # REST API wrapper
│   ├── components/       # Reusable components
│   │   ├── ui/           # shadcn/ui components
│   │   └── Layout.tsx    # Main layout with sidebar
│   ├── hooks/            # React hooks
│   │   ├── useAPI.ts     # React Query hooks
│   │   └── useWebSocket.ts  # WebSocket hook
│   ├── lib/              # Utilities
│   │   └── utils.ts      # cn() helper
│   ├── pages/            # Page components
│   │   ├── Dashboard.tsx # Main dashboard
│   │   ├── Monitors.tsx  # Monitor management
│   │   └── ...           # Other pages
│   ├── stores/           # Zustand stores (future)
│   ├── types/            # TypeScript types
│   │   └── api.ts        # API type definitions
│   ├── App.tsx           # Root component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
├── tsconfig.json         # TypeScript configuration
└── package.json          # Dependencies
```

## API Integration

The dashboard connects to the HifzDefend FastAPI backend:

- **Base URL**: `http://localhost:8080/api/v1`
- **WebSocket**: `ws://localhost:8080/api/v1/ws`

All API calls are proxied through Vite in development mode.

## WebSocket Events

Real-time updates are received via WebSocket:

- `service_started` / `service_stopped`
- `monitor_started` / `monitor_stopped`
- `scan_started` / `scan_completed`
- `threat_detected`
- `config_changed`
- `system_update`

## Component Library

Built with shadcn/ui for consistent, accessible UI:

```bash
# Add new components
npx shadcn-ui@latest add [component-name]
```

Available components:
- button, card, badge, switch
- dialog, dropdown-menu, popover
- tabs, tooltip, separator
- And more...

## Styling

Uses Tailwind CSS with custom design tokens:

- **Primary**: Blue (#3b82f6)
- **Success**: Green (#22c55e)
- **Warning**: Orange (#f97316)
- **Destructive**: Red (#ef4444)

Dark mode is configured and ready to use.

## Performance

- **Code Splitting**: Automatic route-based splitting
- **Lazy Loading**: Components loaded on demand
- **React Query**: Smart caching and refetching
- **WebSocket**: Efficient real-time updates

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Development Tips

### Hot Reload

Vite provides instant hot module replacement (HMR). Changes appear immediately without full page reload.

### Type Safety

All API calls are fully typed. If backend models change, update `src/types/api.ts`.

### State Management

- **Server State**: React Query (API calls, caching)
- **Client State**: Zustand (future use for UI state)
- **URL State**: React Router (page navigation)

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout.tsx`

### Adding New API Endpoints

1. Add method to `src/api/client.ts`
2. Create React Query hook in `src/hooks/useAPI.ts`
3. Use hook in component

## Troubleshooting

### Backend Not Reachable

Ensure HifzDefend backend is running:
```bash
cd ../
python -m uvicorn src.hifzdefend.api.main:app --reload --port 8080
```

### WebSocket Connection Failed

Check that WebSocket endpoint is accessible:
```
ws://localhost:8080/api/v1/ws
```

### Build Errors

Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

## License

Part of HifzDefend - See main project LICENSE
