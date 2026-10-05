from flask import Flask, render_template, request, jsonify
import platform
import socket
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# -----------------------------
# Database Configuration
# -----------------------------

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///network_tests.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class NetworkTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    latency = db.Column(db.Float)
    packet_loss = db.Column(db.Float)
    download_speed = db.Column(db.Float)
    upload_speed = db.Column(db.Float)
    status = db.Column(db.String(50))


with app.app_context():
    db.create_all()


# -----------------------------
# Network Test
# -----------------------------

def check_ping(host="8.8.8.8"):

    latencies = []
    successful = 0
    total = 4

    for _ in range(total):

        try:
            start = datetime.now().timestamp()

            connection = socket.create_connection(
                (host, 53),
                timeout=3
            )

            connection.close()

            latency = round(
                (datetime.now().timestamp() - start) * 1000,
                2
            )

            latencies.append(latency)
            successful += 1

        except Exception:
            pass

    if successful > 0:
        average_latency = round(
            sum(latencies) / len(latencies),
            2
        )
    else:
        average_latency = None

    packet_loss = round(
        ((total - successful) / total) * 100,
        2
    )

    output = (
        f"Tests: {total}\n"
        f"Successful: {successful}\n"
        f"Packet Loss: {packet_loss}%\n"
        f"Latencies: {latencies} ms"
    )

    return average_latency, packet_loss, output


# -----------------------------
# Network Information
# -----------------------------

def get_network_info():

    hostname = socket.gethostname()

    try:

        local_ip = socket.gethostbyname(hostname)

        if local_ip.startswith("127."):

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            )

            s.connect(("8.8.8.8", 80))

            local_ip = s.getsockname()[0]

            s.close()

    except Exception:

        local_ip = "Unavailable"

    operating_system = platform.system()

    return hostname, local_ip, operating_system


# -----------------------------
# Dashboard
# -----------------------------

@app.route("/")
def home():

    latency, packet_loss, ping_output = check_ping()

    hostname, local_ip, operating_system = get_network_info()

    if latency is not None:

        if latency < 50:
            status = "Excellent"

        elif latency < 100:
            status = "Good"

        elif latency < 200:
            status = "Average"

        else:
            status = "Poor"

    else:

        status = "Connection Failed"

    # Speed is measured in the browser,
    # not on the Render server.
    download_speed = None
    upload_speed = None


    return render_template(
        "index.html",
        latency=latency,
        packet_loss=packet_loss,
        status=status,
        download_speed=download_speed,
        upload_speed=upload_speed,
        ping_output=ping_output,
        hostname=hostname,
        local_ip=local_ip,
        operating_system=operating_system
    )


# -----------------------------
# Test History
# -----------------------------

@app.route("/history")
def history():

    tests = NetworkTest.query.order_by(
        NetworkTest.timestamp.desc()
    ).all()

    return render_template(
        "history.html",
        tests=tests
    )

@app.route("/save-speed-test", methods=["POST"])
def save_speed_test():
    data = request.get_json()

    latency = data.get("latency")
    packet_loss = data.get("packet_loss")
    download_speed = data.get("download_speed")
    upload_speed = data.get("upload_speed")

    if latency is not None:
        if latency < 50:
            status = "Excellent"
        elif latency < 100:
            status = "Good"
        elif latency < 200:
            status = "Average"
        else:
            status = "Poor"
    else:
        status = "Connection Failed"

    test = NetworkTest(
        latency=latency,
        packet_loss=packet_loss,
        download_speed=download_speed,
        upload_speed=upload_speed,
        status=status
    )

    db.session.add(test)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Test result saved successfully"
    })


# -----------------------------
# Application Start
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
