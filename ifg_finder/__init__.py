from flask import Flask

app = Flask(__name__, template_folder='templates/', static_folder='static/')

# Register blueprints here
from ifg_finder.main import bp as main_bp
app.register_blueprint(main_bp)

from ifg_finder.dashboard import bp as dashboard_bp
app.register_blueprint(dashboard_bp, url_prefix='/painel')
