import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8000"))

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_env()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

def json_response(handler, status, data):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[AI] {self.address_string()} - {fmt % args}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            return json_response(self, 200, {
                "status": "ok",
                "service": "trendly-ai",
                "openai": bool(OPENAI_API_KEY),
            })

        if self.path == "/":
            return json_response(self, 200, {
                "name": "Trendly AI API",
                "status": "running",
                "openai": bool(OPENAI_API_KEY),
            })

        return json_response(self, 404, {"detail": "Not found"})

    def do_POST(self):
        if self.path != "/ai/internal/generate":
            return json_response(self, 404, {"detail": "Not found"})

        if not INTERNAL_API_KEY:
            return json_response(self, 503, {
                "detail": "Internal AI service key is not configured"
            })

        supplied = self.headers.get("X-Internal-Service-Key")

        if supplied != INTERNAL_API_KEY:
            return json_response(self, 401, {
                "detail": "Invalid internal service key"
            })

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length > 120000:
                return json_response(self, 400, {
                    "detail": "Request too large"
                })

            payload = json.loads(self.rfile.read(length))

            prompt = payload.get("prompt")

            if not isinstance(prompt, str) or not prompt.strip():
                return json_response(self, 400, {
                    "detail": "Prompt is required"
                })

            prompt = prompt.strip()

            if len(prompt) > 12000:
                return json_response(self, 400, {
                    "detail": "Prompt must be 12000 characters or fewer"
                })

            if not OPENAI_API_KEY:
                return json_response(self, 503, {
                    "detail": "OpenAI API key is not configured"
                })

            request_body = json.dumps({
                "model": OPENAI_MODEL,
                "input": prompt,
            }).encode()

            request = urllib.request.Request(
                "https://api.openai.com/v1/responses",
                data=request_body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    result = json.loads(response.read().decode())
            except HTTPError as exc:
                detail = exc.read().decode(errors="replace")
                print(f"[AI] OpenAI HTTP {exc.code}: {detail}")
                return json_response(self, 502, {
                    "detail": "OpenAI request failed"
                })
            except URLError as exc:
                print(f"[AI] OpenAI connection error: {exc}")
                return json_response(self, 502, {
                    "detail": "Unable to reach OpenAI"
                })

            text = result.get("output_text")

            if not text:
                output = result.get("output", [])
                parts = []

                for item in output:
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            parts.append(content.get("text", ""))

                text = "".join(parts)

            if not text:
                return json_response(self, 502, {
                    "detail": "OpenAI returned no text"
                })

            return json_response(self, 200, {"text": text})

        except json.JSONDecodeError:
            return json_response(self, 400, {
                "detail": "Invalid JSON"
            })
        except Exception as exc:
            print(f"[AI] Server error: {exc}")
            return json_response(self, 500, {
                "detail": "AI service error"
            })

if __name__ == "__main__":
    print(f"Trendly AI local server listening on {HOST}:{PORT}")
    print(f"OpenAI configured: {bool(OPENAI_API_KEY)}")
    print("Internal API key configured:", bool(INTERNAL_API_KEY))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
