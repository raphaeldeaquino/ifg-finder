from flask import render_template
from ifg_finder.main import bp


@bp.route('/')
def index():
    return render_template('index.html')
