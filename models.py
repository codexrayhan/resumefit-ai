from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(120))
    picture = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=_now)
    analyses = db.relationship(
        "Analysis", backref="user", cascade="all, delete-orphan"
    )


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), index=True, nullable=False
    )
    label = db.Column(db.String(120))       # resume name, used for grouping
    jd_title = db.Column(db.String(200))    # target job title
    score = db.Column(db.Float, nullable=False)
    missing_count = db.Column(db.Integer)
    missing_keywords = db.Column(db.JSON)
    predicted_roles = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=_now, index=True)