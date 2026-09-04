#!/bin/bash
# Samanvaya — One-Command Full-Stack Launcher (Linux/macOS)
# Usage: bash start.sh

set -e

CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "  ${CYAN}${BOLD}🌙 Samanvaya (समान्वय) — Full-Stack Launcher${NC}"
echo -e "  ${CYAN}═══════════════════════════════════════════${NC}"
echo -e "  ${YELLOW}🧠  ML FastAPI       → http://localhost:8001${NC}"
echo -e "  ${CYAN}🛰️   Core Reg API    → http://localhost:8000${NC}"
echo -e "  ${MAGENTA}🛡️   Node.js Gateway → http://localhost:3000${NC}"
echo -e "  ${GREEN}🚀  React Dashboard → http://localhost:5173${NC}"
echo ""

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Activate virtualenv if present
if [ -f "$ROOT/venv/bin/activate" ]; then
  source "$ROOT/venv/bin/activate"
elif [ -f "$ROOT/ml_service/venv/bin/activate" ]; then
  source "$ROOT/ml_service/venv/bin/activate"
fi

# 1. ML FastAPI Service
echo -e "${YELLOW}[1/4] Starting ML Telemetry Microservice (FastAPI + IsolationForest)...${NC}"
(cd "$ROOT/ml_service" && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload) &
ML_PID=$!
sleep 1

# 2. Samanvaya Core Registration API
echo -e "${CYAN}[2/4] Starting Samanvaya Core Registration API (FastAPI)...${NC}"
(cd "$ROOT" && python -m uvicorn ch2_lunar_reg.interfaces.api:app --host 0.0.0.0 --port 8000) &
CORE_PID=$!
sleep 1

# 3. Node.js Gateway
echo -e "${MAGENTA}[3/4] Starting Node.js Gateway (Express)...${NC}"
(cd "$ROOT/backend" && npx tsx src/index.ts) &
NODE_PID=$!
sleep 1

# 4. React Vite Frontend
echo -e "${GREEN}[4/4] Starting React Dashboard (Vite)...${NC}"
(cd "$ROOT/frontend" && npm run dev) &
REACT_PID=$!

echo ""
echo -e "${GRAY}  Waiting for Vite to compile (5s)...${NC}"
sleep 5

# Open browser
if command -v xdg-open &> /dev/null; then
  xdg-open "http://localhost:5173"
elif command -v open &> /dev/null; then
  open "http://localhost:5173"
fi

echo ""
echo -e "${GREEN}  ✅ All 4 services running!${NC}"
echo -e "${GRAY}  PIDs: ML=$ML_PID  Core=$CORE_PID  Node=$NODE_PID  React=$REACT_PID${NC}"
echo -e "${GRAY}  Press Ctrl+C to stop all.${NC}"
echo ""

# Keep alive — stop all on Ctrl+C
trap "kill $ML_PID $CORE_PID $NODE_PID $REACT_PID 2>/dev/null; echo 'All services stopped.'; exit 0" INT
wait
