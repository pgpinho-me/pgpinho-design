import http.server
import socketserver
import base64
import json
import os

PORT = 8080
DIRECTORY = "public_html"
USERNAME = "admin"
PASSWORD = "lightbox"

class CMSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def is_authenticated(self):
        auth_header = self.headers.get("Authorization")
        if not auth_header:
            return False
        key = base64.b64encode(bytes(f"{USERNAME}:{PASSWORD}", "utf-8")).decode("ascii")
        return auth_header == f"Basic {key}"

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Admin Area"')
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/admin'):
            if not self.is_authenticated():
                self.do_AUTHHEAD()
                self.wfile.write(b"Acesso restrito.")
                return
        super().do_GET()

    def do_POST(self):
        # Apenas admin pode fazer POST (salvar projetos)
        if not self.is_authenticated():
            self.do_AUTHHEAD()
            return

        if self.path == '/api/save-projects':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Recebe o JSON novo e salva no arquivo
                projects = json.loads(post_data)
                with open(os.path.join(DIRECTORY, 'projects.json'), 'w') as f:
                    json.dump(projects, f, indent=4)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(bytes(f'{{"error":"{str(e)}"}}', 'utf-8'))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CMSHandler) as httpd:
        print(f"CMS Server running on port {PORT}")
        httpd.serve_forever()
