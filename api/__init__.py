from flask import Flask


def create_app():
    app = Flask(__name__)

    from .default_views import default_views
    from .catalog import catalog
    from .errors import errors
    from .keys import keys
    from .server import server

    app.register_blueprint(default_views)
    app.register_blueprint(catalog)
    app.register_blueprint(errors)
    app.register_blueprint(keys)
    app.register_blueprint(server)

    return app
