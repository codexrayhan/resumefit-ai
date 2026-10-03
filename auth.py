import os

from authlib.integrations.flask_client import OAuth, OAuthError
from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import LoginManager, login_user, logout_user

from models import User, db

oauth = OAuth()
login_manager = LoginManager()
auth_bp = Blueprint("auth", __name__)


def init_auth(app):
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        server_metadata_url=(
            "https://accounts.google.com/.well-known/openid-configuration"
        ),
        client_kwargs={"scope": "openid email profile"},
    )
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "Login required.", "login_required": True}), 401
    return redirect(url_for("auth.login"))


@auth_bp.route("/login")
def login():
    return oauth.google.authorize_redirect(
        url_for("auth.callback", _external=True)
    )


@auth_bp.route("/auth/callback")
def callback():
    try:
        token = oauth.google.authorize_access_token()
    except OAuthError:
        return redirect("/")

    info = token["userinfo"]
    user = User.query.filter_by(google_id=info["sub"]).first()
    if user is None:
        user = User(
            google_id=info["sub"],
            email=info["email"],
            name=info.get("name"),
            picture=info.get("picture"),
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect("/")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect("/")