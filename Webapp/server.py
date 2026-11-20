import http.server
import json
import os
import urllib.error
import urllib.request

HOST = "127.0.0.1"
PORT = 8501

AAS_API_URL = os.environ.get(
    "AAS_API_URL",
    "https://aas-workflow-engine.servicesessentials.ibm.com/api/v1/run/3ae4fcef-7ec8-4269-8e10-319e1430ebb0"
)
AAS_API_KEY = os.environ.get(
    "AAS_API_KEY",
    "{
  "mcpServers": {
    "lf-lf_proj_09217e0ec4e6": {
      "command": "cmd",
      "args": [
        "/c",
        "uvx",
        "mcp-proxy",
        "--transport",
        "streamablehttp",
        "--headers",
        "x-api-key",
        "sk-Mit5c-K9mFrtEmGgOMQEtrvex76CF37mRAMXpHibf0Q",
        "https://aas-workflow-engine.servicesessentials.ibm.com/api/v1/mcp/project/219df1e6-2461-4230-987f-f7c0e4291bbd/streamable"
      ]
    }
  }
}"
)

class EligibilityHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/check-eligibility":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                body = json.loads(post_data.decode("utf-8"))
                name = str(body.get("name", "")).strip()
                age = body.get("age", 0)
                country = str(body.get("country", "")).strip()
                hours = body.get("hours", 0)

                input_val = f"{name},{age},{country},{hours}"
                
                # Forward to Workflow Engine / MCP API
                upstream_payload = {
                    "input_value": input_val,
                    "output_type": "chat",
                    "input_type": "chat"
                }
                upstream_data = json.dumps(upstream_payload).encode("utf-8")
                headers = {
                    "x-api-key": AAS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EligibilityChecker/1.0"
                }

                req = urllib.request.Request(AAS_API_URL, data=upstream_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_body = resp.read().decode("utf-8")
                    res_json = json.loads(resp_body)

                    message_text = ""
                    try:
                        outputs = res_json.get("outputs", [])
                        if outputs:
                            first_output = outputs[0].get("outputs", [])
                            if first_output:
                                msgs = first_output[0].get("messages", [])
                                if msgs:
                                    message_text = msgs[0].get("message", "")
                                if not message_text:
                                    results_data = first_output[0].get("results", {}).get("message", {}).get("data", {})
                                    message_text = results_data.get("text", "")
                    except Exception:
                        message_text = str(res_json)

                    if not message_text:
                        message_text = resp_body

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "message": message_text}).encode("utf-8"))

            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if e.fp else str(e)
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": f"Upstream error {e.code}: {err_text}"}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()
        else:
            return super().do_GET()

if __name__ == "__main__":
    print(f"Starting server on http://{HOST}:{PORT}")
    server = http.server.HTTPServer((HOST, PORT), EligibilityHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
