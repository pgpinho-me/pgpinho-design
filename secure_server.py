import http.server
import socketserver
import base64
import json
import os
import cgi

PORT = 8080
DIRECTORY = "public_html"
USERNAME = "admin"
PASSWORD = "lightbox"

class CMSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

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
        if not self.is_authenticated():
            self.do_AUTHHEAD()
            return

        # Helper para salvar JSON
        def save_json(filename):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                with open(os.path.join(DIRECTORY, filename), 'w') as f:
                    json.dump(data, f, indent=4)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_error(500, str(e))

        if self.path == '/api/save-projects':
            save_json('projects.json')
            return

        if self.path == '/api/save-settings':
            save_json('settings.json')
            return

        # Endpoint: Upload de Imagem
        if self.path == '/api/upload':
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                if 'file' not in form:
                    self.send_error(400, "No file field")
                    return

                fileitem = form['file']
                if not fileitem.filename:
                    self.send_error(400, "No filename")
                    return

                # Garantir que a pasta images existe
                images_dir = os.path.join(DIRECTORY, 'images')
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)

                # Salvar ficheiro
                filename = os.path.basename(fileitem.filename)
                filepath = os.path.join(images_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(fileitem.file.read())

                self.send_response(200)
                self.end_headers()
                response = {"status": "ok", "url": f"images/{filename}"}
                self.wfile.write(bytes(json.dumps(response), 'utf-8'))
            except Exception as e:
                self.send_error(500, str(e))
            return

        self.send_error(404, "Endpoint not found")

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CMSHandler) as httpd:
        print(f"CMS Server with Cache Busting running on port {PORT}")
        httpd.serve_forever()
