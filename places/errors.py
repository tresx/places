from flask import Blueprint, render_template

bp = Blueprint('errors', __name__, url_prefix='/error')


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    # TODO: Explicitly rollback database here?
    return render_template('500.html'), 500


# Cause a 500 error for testing purposes
@bp.route('/err500')
def err500():
    return abort(500)
