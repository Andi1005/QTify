import os
from socket import gethostname

from flask import Flask

from .config import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db_path = os.path.join(app.instance_path, "db.sqlite3")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from . import models

    models.db.init_app(app)
    with app.app_context():
        models.db.create_all()
        models.delete_old_rows()

    from .views import views

    app.register_blueprint(views)

    return app


app = create_app()

if __name__ == "__main__":
    if "liveconsole" not in gethostname():
        app.run(debug=True)
