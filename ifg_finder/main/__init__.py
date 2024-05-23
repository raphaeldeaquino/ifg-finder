from flask import Blueprint

bp = Blueprint('main', __name__)

from ifg_finder.main import routes



