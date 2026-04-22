import http.server
import socketserver
import os
import webbrowser
import socket

PORT = 8765
# Muda para o diretório onde o HTML está localizado
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler

# Descobre o IP local da máquina na rede
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

local_ip = get_local_ip()

print(f"Servidor rodando localmente em: http://localhost:{PORT}/resumo_dashboard.html")
print(f"Para acessar de outros PCs na rede, use: http://{local_ip}:{PORT}/resumo_dashboard.html")
print("Pressione Ctrl+C para parar o servidor.")

# Abre o navegador automaticamente
webbrowser.open(f"http://localhost:{PORT}/resumo_dashboard.html")

# O uso de "" em TCPServer já permite conexões de qualquer IP na rede local (0.0.0.0)
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
        httpd.server_close()
