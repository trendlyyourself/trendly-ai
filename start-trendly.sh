#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home/trendly-ai || exit 1

pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite --host 0.0.0.0 --port 3000" 2>/dev/null

(cd backend && source .venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/trendly-backend.log 2>&1 &) 
(cd frontend && npm run dev -- --host 0.0.0.0 --port 3000 > /tmp/trendly-frontend.log 2>&1 &)

echo "Trendly started"
echo "Frontend: http://127.0.0.1:3000"
echo "Backend:  http://127.0.0.1:8000"
