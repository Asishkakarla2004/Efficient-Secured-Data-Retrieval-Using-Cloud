from datetime import datetime

from flask_login import UserMixin

from .database.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    image_pattern_encrypted = db.Column(db.Text, nullable=False)
    image_pattern_hint = db.Column(db.String(255))
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)

    files = db.relationship("UploadedFile", backref="owner", lazy=True)

    def get_id(self):
        return f"user-{self.id}"


class Admin(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime)

    def get_id(self):
        return f"admin-{self.id}"


class ImageAuthentication(TimestampMixin, db.Model):
    __tablename__ = "image_authentication"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    pattern_preview = db.Column(db.String(255), nullable=False)
    image_count = db.Column(db.Integer, nullable=False)


class UploadedFile(TimestampMixin, db.Model):
    __tablename__ = "uploaded_files"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(20), nullable=False, index=True)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    storage_path = db.Column(db.String(255), nullable=False)
    encryption_status = db.Column(db.String(20), default="encrypted", nullable=False)
    encryption_speed_ms = db.Column(db.Float)
    decryption_speed_ms = db.Column(db.Float)
    access_scope = db.Column(db.String(30), default="private", nullable=False)


class EncryptionLog(TimestampMixin, db.Model):
    __tablename__ = "encryption_logs"

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    operation = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    algorithm = db.Column(db.String(50), default="Optimized Blowfish", nullable=False)
    duration_ms = db.Column(db.Float, nullable=False)
    details = db.Column(db.Text)


class AccessLog(TimestampMixin, db.Model):
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey("uploaded_files.id"))
    action = db.Column(db.String(30), nullable=False)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text)
