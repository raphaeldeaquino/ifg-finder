from flask import Flask
from ifg_finder.main import bp as main_bp


app = Flask(__name__, template_folder='templates/', static_folder='static/')

# Register blueprints here
app.register_blueprint(main_bp)