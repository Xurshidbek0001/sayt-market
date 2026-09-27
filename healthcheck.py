import threading
from flask import Flask

app = Flask(__name__)


@app.route("/")
def health():
    return "Sayt Market Bot ishlayapti!", 200


def start_health_server_in_background():
    thread = threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=10000,
            use_reloader=False,
        ),
        daemon=True,
    )
    thread.start()
