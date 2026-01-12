---
allowed-tools: Bash(make backend-dev:*), Bash(make frontend-dev:*), Bash(lsof:*), Bash(curl:*), Bash(sleep:*), Bash(kill:*), Grep
description: Manage development servers (start, stop, restart)
---

## Command Arguments

$ARGUMENTS

## Your Task

Manage development servers based on the argument above.

### Step 1: Detect Ports (ALWAYS do this first)

Use the **Grep tool** (not Bash grep) to find PORT configuration:
- Search `backend/.env` for pattern `^PORT=` → extract the port number (default: 8000)
- Search `frontend/.env.local` for pattern `^PORT=` → extract the port number (default: 3000)

### If argument is "start" (or empty/missing):

1. Check if servers are already running:
   - `curl -s http://localhost:{backend_port}/health` → backend running if responds
   - `curl -s -o /dev/null -w "%{http_code}" http://localhost:{frontend_port}` → frontend running if 200
2. If backend not running:
   - Run `make backend-dev` with `run_in_background: true`
   - Wait 3-5 seconds, verify with health check
3. If frontend not running:
   - Run `make frontend-dev` with `run_in_background: true`
   - Wait 3-5 seconds, verify it responds
4. Report final status

### If argument is "stop":

1. Find PIDs: `lsof -ti:{port}` for each port
2. Kill processes if PIDs exist
3. Wait 1-2 seconds, verify stopped
4. Report status

### If argument is "restart":

1. Execute stop logic
2. Wait 2 seconds for ports to release
3. Execute start logic

### If argument is anything else:

Report: "Unknown command. Usage: /dev start | stop | restart"

## Status Report

| Server   | Status          | URL                              |
|----------|-----------------|----------------------------------|
| Backend  | Running/Stopped | http://localhost:{backend_port}  |
| Frontend | Running/Stopped | http://localhost:{frontend_port} |

If running: **Chat interface:** http://localhost:{frontend_port}/chat

## Notes

- Use `run_in_background: true` when starting servers
- Backend should start before frontend
- If kill fails, process may already be stopped - that's OK
- IMPORTANT: Use the Grep tool (Claude's built-in), not Bash grep command
