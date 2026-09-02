from wsgiref.simple_server import make_server
from cubeai.api.health import application

with make_server("127.0.0.1", 8000, application) as server:
    print("CubeAI health server listening on http://127.0.0.1:8000/health")
    server.serve_forever()
