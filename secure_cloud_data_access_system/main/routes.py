from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import AccessLog, EncryptionLog, UploadedFile


main_bp = Blueprint("main", __name__, template_folder="../templates")


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if getattr(current_user, "role", "") == "admin":
        return render_template("admin_redirect.html")

    files = UploadedFile.query.filter_by(user_id=current_user.id).order_by(UploadedFile.created_at.desc()).limit(5).all()
    access_logs = AccessLog.query.filter_by(user_id=current_user.id).order_by(AccessLog.created_at.desc()).limit(8).all()
    encryption_logs = EncryptionLog.query.filter_by(user_id=current_user.id).order_by(EncryptionLog.created_at.desc()).limit(6).all()

    metrics = {
        "files": UploadedFile.query.filter_by(user_id=current_user.id).count(),
        "downloads": AccessLog.query.filter_by(user_id=current_user.id, action="download", status="success").count(),
        "security_events": AccessLog.query.filter_by(user_id=current_user.id).count(),
        "avg_encrypt_ms": round(
            sum(log.duration_ms for log in encryption_logs) / len(encryption_logs), 2
        )
        if encryption_logs
        else 0,
    }
    return render_template(
        "dashboard.html",
        files=files,
        access_logs=access_logs,
        encryption_logs=encryption_logs,
        metrics=metrics,
    )
