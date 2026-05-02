import warnings
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message=".*np.object.*"
)


import os
from flask import Flask, render_template
from flask_cors import CORS
import warnings
import logging

# ================= HARD SUPPRESSION =================
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"      # Hide TF C++ logs
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

warnings.filterwarnings("ignore")

logging.getLogger("tensorflow").setLevel(logging.ERROR)
# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

# --------------------------------------------------
# FLASK APP INIT
# --------------------------------------------------
app = Flask(
    __name__,
    template_folder=FRONTEND_DIR,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)

# --------------------------------------------------
# REGISTER BLUEPRINTS
# --------------------------------------------------
from routes.upload_route import upload_bp
from routes.verify_route import verify_bp
from routes.alerts_route import alerts_bp
from routes.dashboard_route import dashboard_bp   #  ADD THIS

app.register_blueprint(upload_bp, url_prefix="/api")
app.register_blueprint(verify_bp, url_prefix="/api")
app.register_blueprint(alerts_bp, url_prefix="/api")  #  ADD THIS
app.register_blueprint(dashboard_bp, url_prefix="/api")
# --------------------------------------------------
# FRONTEND PAGE ROUTES
# --------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/verify")
def verify_page():
    return render_template("verify.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/violations")
def violations_page():
    return render_template("violations.html")

# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
