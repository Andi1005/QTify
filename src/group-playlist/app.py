import os

from flask import Flask

from models import init_db
from secret import secret_key
from views import views


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = secret_key

    db_path = os.path.join(app.instance_path, "instance/gp.sqlite3")
    app.config ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    from models import db
    db.init_app(app)
    db.create_all()

    from views import views
    app.register_blueprint(views)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
