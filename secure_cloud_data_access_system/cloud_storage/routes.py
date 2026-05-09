import os
import tempfile
from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from ..database.extensions import db
from ..encryption.blowfish_service import OptimizedBlowfishService, detect_file_type
from ..forms import UploadForm
from ..models import EncryptionLog, UploadedFile
from ..utils import allowed_filename, log_access


files_bp = Blueprint("files", __name__, template_folder="../templates")
crypto_service = OptimizedBlowfishService()


@files_bp.route("/")
@login_required
def list_files():
    query = UploadedFile.query.filter_by(user_id=current_user.id)
    search = request.args.get("search", "").strip()
    file_type = request.args.get("type", "").strip()
    date_filter = request.args.get("date", "").strip()

    if search:
        query = query.filter(UploadedFile.original_filename.ilike(f"%{search}%"))
    if file_type:
        query = query.filter_by(file_type=file_type)
    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(db.func.date(UploadedFile.created_at) == selected_date)
        except ValueError:
            flash("Invalid date filter.", "warning")

    files = query.order_by(UploadedFile.created_at.desc()).all()
    return render_template("files/list.html", files=files)


@files_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm()
    latest_stats = None

    if form.validate_on_submit():
        upload = form.file.data
        original_filename = upload.filename
        stored_filename = allowed_filename(original_filename)
        raw_temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"tmp_{stored_filename}")
        encrypted_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{stored_filename}.bf")
        upload.save(raw_temp_path)

        try:
            latest_stats = crypto_service.encrypt_file(raw_temp_path, encrypted_path)
            file_record = UploadedFile(
                user_id=current_user.id,
                original_filename=original_filename,
                stored_filename=f"{stored_filename}.bf",
                file_type=detect_file_type(original_filename),
                mime_type=upload.mimetype or "application/octet-stream",
                file_size=os.path.getsize(raw_temp_path),
                storage_path=encrypted_path,
                encryption_speed_ms=latest_stats["duration_ms"],
                access_scope=form.access_scope.data,
            )
            db.session.add(file_record)
            db.session.flush()
            db.session.add(
                EncryptionLog(
                    file_id=file_record.id,
                    user_id=current_user.id,
                    operation="encrypt",
                    status="success",
                    duration_ms=latest_stats["duration_ms"],
                    details=(
                        f"Input: {latest_stats['input_size']} bytes | "
                        f"Output: {latest_stats['output_size']} bytes"
                    ),
                )
            )
            db.session.commit()
            log_access(current_user.id, "upload", "success", file_id=file_record.id)
            flash("File encrypted and uploaded successfully.", "success")
            return render_template("files/upload.html", form=form, latest_stats=latest_stats)
        finally:
            if os.path.exists(raw_temp_path):
                os.remove(raw_temp_path)

    return render_template("files/upload.html", form=form, latest_stats=latest_stats)


@files_bp.route("/download/<int:file_id>")
@login_required
def download(file_id: int):
    file_record = UploadedFile.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    fd, temp_path = tempfile.mkstemp(prefix="decrypted_", suffix=f"_{file_record.original_filename}")
    os.close(fd)

    stats = crypto_service.decrypt_file(file_record.storage_path, temp_path)
    file_record.decryption_speed_ms = stats["duration_ms"]
    db.session.add(
        EncryptionLog(
            file_id=file_record.id,
            user_id=current_user.id,
            operation="decrypt",
            status="success",
            duration_ms=stats["duration_ms"],
            details=f"Output: {stats['output_size']} bytes",
        )
    )
    db.session.commit()
    log_access(current_user.id, "download", "success", file_id=file_record.id)

    return send_file(
        temp_path,
        as_attachment=True,
        download_name=file_record.original_filename,
        mimetype=file_record.mime_type,
    )
