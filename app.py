from flask import Flask, render_template
import subprocess
import platform
import re
import socket
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)


def check_ping(host="8.8.8.8"):
    """Check network latency and packet loss."""

    import socket
    import time

    latencies = []
    successful = 0
    total = 4

    for _ in range(total):
        try:
            start = time.time()

            connection = socket.create_connection(
                (host, 53),
                timeout=3
            )

            connection.close()

            latency = round((time.time() - start) * 1000, 2)
            latencies.append(latency)
            successful += 1

        except Exception:
            pass

    if successful > 0:
        average_latency = round(
            sum(latencies) / len(latencies), 2
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

# def check_speed():
#     import speedtest

#     st = speedtest.Speedtest()
#     st.get_best_server()

#     download_speed = st.download() / 1_000_000
#     upload_speed = st.upload() / 1_000_000

#     return round(download_speed, 2), round(upload_speed, 2)

def check_speed():
    return 0, 0

def get_network_info():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    operating_system = platform.system()

    return hostname, local_ip, operating_system

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

@app.route("/")
def home():

    latency, packet_loss, ping_output = check_ping()
    
    download_speed, upload_speed = check_speed()
    
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

# Save test result to database
    test = NetworkTest(
    latency=latency,
    packet_loss=packet_loss,
    download_speed=download_speed,
    upload_speed=upload_speed,
    status=status
    )

    db.session.add(test)
    db.session.commit()

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
    operating_system=operating_system,

)
    
@app.route("/history")
def history():
    tests = NetworkTest.query.order_by(NetworkTest.timestamp.desc()).all()

    return render_template("history.html", tests=tests)

   
if __name__ == "__main__":
    app.run(debug=True)
    
