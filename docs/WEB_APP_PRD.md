# HifzDefend Web Application - Product Requirements Document

**Project:** HifzDefend Web Application (Phase 2)
**Branch:** feature/web-app
**Goal:** Convert HifzDefend CLI antivirus to a modern web application with REST API backend and React frontend

---

## Project Overview

Transform HifzDefend from a CLI-only antivirus tool into a full-featured web application with:
- FastAPI REST API backend
- React TypeScript frontend
- Real-time scan monitoring
- Dashboard with statistics
- Quarantine management UI
- Configuration management
- WebSocket support for live updates

---

## User Stories

### US-001: FastAPI Backend Setup
**As a** developer
**I want** a FastAPI backend with proper project structure
**So that** I can serve REST API endpoints for the web frontend

**Acceptance Criteria:**
- FastAPI project structure at `src/hifzdefend/api/`
- Main FastAPI app at `src/hifzdefend/api/main.py`
- CORS middleware configured for local development
- Health check endpoint at `/api/health`
- API documentation at `/api/docs` (Swagger)
- Pydantic models for request/response at `src/hifzdefend/api/models.py`
- API router structure at `src/hifzdefend/api/routers/`
- Environment configuration using pydantic-settings
- Typecheck passes
- Tests pass

**Priority:** 1
**Max Iterations:** 5

---

### US-002: Scan Management API Endpoints
**As a** web user
**I want** API endpoints to trigger and monitor scans
**So that** I can scan files and directories from the web interface

**Acceptance Criteria:**
- POST `/api/scans` - Start new scan (file or directory path)
- GET `/api/scans` - List all scans with pagination
- GET `/api/scans/{scan_id}` - Get scan details and results
- DELETE `/api/scans/{scan_id}` - Cancel running scan
- Scan job queue using background tasks
- Scan status: pending, running, completed, failed, cancelled
- Response includes: scan_id, status, path, threats_found, start_time, end_time
- Integration with existing scanner.py
- Typecheck passes
- Tests pass

**Priority:** 2
**Max Iterations:** 5

---

### US-003: Dashboard Statistics API
**As a** web user
**I want** API endpoints for dashboard statistics
**So that** I can view system health and scan history

**Acceptance Criteria:**
- GET `/api/stats/overview` - Total scans, threats found, quarantined items
- GET `/api/stats/recent-scans` - Last 10 scans with results
- GET `/api/stats/threats-timeline` - Threats detected over time (7 days)
- GET `/api/stats/system-status` - ClamAV status, definitions version, last update
- Response caching with 30-second TTL
- Database or file-based storage for scan history
- Typecheck passes
- Tests pass

**Priority:** 3
**Max Iterations:** 5

---

### US-004: Quarantine Management API
**As a** web user
**I want** API endpoints to manage quarantined files
**So that** I can view, restore, or delete quarantined threats

**Acceptance Criteria:**
- GET `/api/quarantine` - List all quarantined files with pagination
- GET `/api/quarantine/{file_id}` - Get quarantine file details
- POST `/api/quarantine/{file_id}/restore` - Restore file to original location
- DELETE `/api/quarantine/{file_id}` - Permanently delete quarantined file
- Response includes: file_id, original_path, quarantine_path, threat_name, quarantine_date, file_size
- Integration with existing quarantine system
- Secure file operations (no path traversal)
- Typecheck passes
- Tests pass

**Priority:** 4
**Max Iterations:** 5

---

### US-005: Configuration Management API
**As a** web user
**I want** API endpoints to view and update configuration
**So that** I can manage HifzDefend settings from the web interface

**Acceptance Criteria:**
- GET `/api/config` - Get current configuration (sanitized, no secrets)
- PUT `/api/config` - Update configuration settings
- POST `/api/config/validate` - Validate configuration without saving
- GET `/api/config/defaults` - Get default configuration values
- Configuration validation using existing Pydantic models
- Only allow updating safe settings (no ClamAV host/port from web)
- Audit log for configuration changes
- Typecheck passes
- Tests pass

**Priority:** 5
**Max Iterations:** 5

---

### US-006: WebSocket Real-Time Updates
**As a** web user
**I want** real-time updates via WebSocket
**So that** I can see scan progress and system events live

**Acceptance Criteria:**
- WebSocket endpoint at `/api/ws`
- Broadcast scan progress updates (files scanned, current file, percentage)
- Broadcast threat detection events
- Broadcast system status changes
- Client connection management
- Graceful disconnection handling
- Message format: JSON with event type and payload
- Typecheck passes
- Tests pass

**Priority:** 6
**Max Iterations:** 5

---

### US-007: React Frontend Setup with TypeScript
**As a** developer
**I want** a React TypeScript frontend with proper tooling
**So that** I can build a modern web UI

**Acceptance Criteria:**
- Create `frontend/` directory in project root
- Initialize Vite + React + TypeScript project
- Install dependencies: axios, react-router-dom, recharts, shadcn/ui
- Configure TypeScript with strict mode
- Setup Tailwind CSS for styling
- API client service at `frontend/src/services/api.ts`
- Environment configuration for API base URL
- Development server runs on port 5173
- Build command generates static files to `frontend/dist/`
- Typecheck passes (npm run typecheck)

**Priority:** 7
**Max Iterations:** 5

---

### US-008: Dashboard Page with Statistics
**As a** web user
**I want** a dashboard showing system overview
**So that** I can monitor HifzDefend at a glance

**Acceptance Criteria:**
- Dashboard route at `/` (home page)
- Display overview statistics cards: Total Scans, Threats Found, Files Quarantined, System Status
- Recent scans list with status badges
- Threats timeline chart (last 7 days) using recharts
- ClamAV status indicator (online/offline)
- Last virus definitions update timestamp
- Responsive design (mobile-friendly)
- Auto-refresh statistics every 30 seconds
- Loading states and error handling
- Typecheck passes

**Priority:** 8
**Max Iterations:** 5

---

### US-009: Scan Management Page
**As a** web user
**I want** a page to start and monitor scans
**So that** I can scan files and directories via the web UI

**Acceptance Criteria:**
- Scan page route at `/scans`
- Form to start new scan: path input, scan button
- Scans list table with columns: ID, Path, Status, Threats, Start Time, Duration, Actions
- Status badges with colors: pending (gray), running (blue), completed (green), failed (red)
- Real-time scan progress updates via WebSocket
- Cancel button for running scans
- View details button to see scan results
- File path validation (no empty paths)
- Loading states and error handling
- Typecheck passes

**Priority:** 9
**Max Iterations:** 5

---

### US-010: Quarantine Management Page
**As a** web user
**I want** a page to manage quarantined files
**So that** I can restore or delete threats from the web UI

**Acceptance Criteria:**
- Quarantine page route at `/quarantine`
- Quarantine files table with columns: File Name, Original Path, Threat Name, Date, Size, Actions
- Restore button with confirmation dialog
- Delete button with confirmation dialog
- Empty state message when no quarantined files
- Pagination for large lists (10 items per page)
- Search/filter by filename or threat name
- Loading states and error handling
- Typecheck passes

**Priority:** 10
**Max Iterations:** 5

---

### US-011: Settings Page
**As a** web user
**I want** a settings page to configure HifzDefend
**So that** I can customize behavior from the web UI

**Acceptance Criteria:**
- Settings page route at `/settings`
- Form sections: Scanning Settings, Quarantine Settings
- Toggle switches for: Auto-quarantine, Scan archives
- Input fields for: Max file size, Excluded paths (textarea)
- Save button with validation
- Reset to defaults button
- Show current values on page load
- Success/error notifications
- Form validation with error messages
- Loading states and error handling
- Typecheck passes

**Priority:** 11
**Max Iterations:** 5

---

### US-012: Navigation and Layout
**As a** web user
**I want** consistent navigation and layout
**So that** I can easily navigate the web application

**Acceptance Criteria:**
- Main layout component with sidebar navigation
- Navigation items: Dashboard, Scans, Quarantine, Settings
- Active route highlighting
- HifzDefend logo and branding
- Responsive mobile menu (hamburger icon)
- Footer with version number and copyright
- Consistent spacing and typography
- Dark mode toggle (optional)
- Typecheck passes

**Priority:** 12
**Max Iterations:** 5

---

### US-013: Backend-Frontend Integration
**As a** developer
**I want** FastAPI to serve the React frontend
**So that** the application runs as a single deployable unit

**Acceptance Criteria:**
- FastAPI serves static files from `frontend/dist/` at root path
- API routes at `/api/*` prefix
- WebSocket at `/api/ws`
- Frontend build integrated into backend startup
- Single command to run full stack: `python -m hifzdefend web`
- New CLI command: `hifzdefend web --host 0.0.0.0 --port 8000`
- Browser automatically opens to http://localhost:8000
- README updated with web app usage instructions
- Typecheck passes
- Tests pass

**Priority:** 13
**Max Iterations:** 5

---

### US-014: Error Handling and Validation
**As a** developer
**I want** comprehensive error handling
**So that** the web app provides clear feedback to users

**Acceptance Criteria:**
- FastAPI exception handlers for common errors (404, 500, validation)
- Consistent error response format: `{error: string, detail?: string, code: string}`
- Frontend error boundary component
- Toast notifications for user actions (success/error)
- Form validation with inline error messages
- API error handling in frontend with user-friendly messages
- Loading spinners during async operations
- Network error detection and retry suggestions
- Typecheck passes
- Tests pass

**Priority:** 14
**Max Iterations:** 5

---

### US-015: Documentation and Deployment
**As a** user
**I want** clear documentation for running the web app
**So that** I can easily deploy and use HifzDefend

**Acceptance Criteria:**
- Update README.md with web app section
- New doc: `docs/WEB_APP.md` with architecture and API reference
- Installation instructions for web app dependencies
- Development setup: running backend and frontend separately
- Production deployment: building and running as single app
- Environment variables documentation
- API endpoint reference
- Screenshots of web interface
- Troubleshooting section
- Update CHANGELOG.md with v0.2.0 features

**Priority:** 15
**Max Iterations:** 5

---

## Technical Stack

**Backend:**
- FastAPI 0.109+
- Uvicorn (ASGI server)
- WebSockets (fastapi.websockets)
- SQLite or JSON file storage for scan history
- Existing HifzDefend core modules

**Frontend:**
- React 18+ with TypeScript
- Vite (build tool)
- React Router v6 (routing)
- Axios (HTTP client)
- Recharts (charts)
- Shadcn/UI + Tailwind CSS (components & styling)
- WebSocket client for real-time updates

---

## Success Criteria

- All 15 user stories completed and verified
- Web application runs on single command: `hifzdefend web`
- Dashboard displays real-time statistics
- Scans can be triggered and monitored via web UI
- Quarantine management works from web interface
- Settings can be updated via web UI
- All typechecks pass (backend and frontend)
- All tests pass (backend and frontend)
- Documentation complete and accurate

---

## Notes

- This PRD focuses on web application (Phase 2)
- Desktop application (Electron/Tauri) will be Phase 3
- Real-time file monitoring will be integrated in Phase 3
- Production deployment (Docker, Windows service) in Phase 4
