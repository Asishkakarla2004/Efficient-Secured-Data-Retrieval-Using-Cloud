from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import AccessLog, EncryptionLog, UploadedFile, User


admin_bp = Blueprint("admin", __name__, template_folder="../templates")


@admin_bp.route("/")
@login_required
def dashboard():
    if getattr(current_user, "role", "") != "admin":
        return render_template("admin/forbidden.html"), 403

    users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_uploads = UploadedFile.query.order_by(UploadedFile.created_at.desc()).limit(10).all()
    recent_logs = AccessLog.query.order_by(AccessLog.created_at.desc()).limit(12).all()
    encryption_logs = EncryptionLog.query.order_by(EncryptionLog.created_at.desc()).limit(12).all()

    metrics = {
        "total_users": User.query.count(),
        "total_files": UploadedFile.query.count(),
        "failed_attempts": AccessLog.query.filter_by(action="login", status="failed").count(),
        "avg_encryption_ms": round(
            sum(log.duration_ms for log in encryption_logs) / len(encryption_logs), 2
        )
        if encryption_logs
        else 0,
    }
    return render_template(
        "admin/dashboard.html",
        users=users,
        recent_uploads=recent_uploads,
        recent_logs=recent_logs,
        encryption_logs=encryption_logs,
        metrics=metrics,
    )
