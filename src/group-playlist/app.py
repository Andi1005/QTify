import os

from flask import Flask

from secret import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY

    db_path = os.path.join(app.instance_path, "instance/gp.sqlite3")
    db_path = "gp.sqlite3"
    app.config ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    from models import db
    db.init_app(app)
    with app.app_context():
        db.create_all()

    from views import views
    app.register_blueprint(views)

    return app


if __name__ == "__main__":
    # TODO: delete database
    app = create_app()
    app.run(debug=True)
