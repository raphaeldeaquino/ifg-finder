from flask import Blueprint

bp = Blueprint('dashboard', __name__)

from ifg_finder.dashboard import routes



