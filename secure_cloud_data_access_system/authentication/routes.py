from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from ..database.extensions import db
from ..forms import (
    ForgotPasswordForm,
    ImageLoginForm,
    LoginForm,
    ProfileForm,
    RegistrationForm,
    ResetPasswordForm,
)
from ..models import Admin, ImageAuthentication, User
from ..utils import (
    decrypt_pattern,
    encrypt_pattern,
    hash_password,
    log_access,
    make_reset_token,
    verify_password,
)


auth_bp = Blueprint("auth", __name__, template_folder="../templates")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    image_choices = current_app.config["IMAGE_AUTH_IMAGES"]

    if form.validate_on_submit():
        selected_images = request.form.get("image_pattern", "")
        pattern = [item for item in selected_images.split(",") if item]
        min_items = current_app.config["IMAGE_AUTH_MIN"]
        max_items = current_app.config["IMAGE_AUTH_MAX"]

        if len(pattern) < min_items or len(pattern) > max_items:
            flash(f"Select between {min_items} and {max_items} images in sequence.", "danger")
            return render_template("auth/register.html", form=form, image_choices=image_choices)

        if len(set(pattern)) != len(pattern):
            flash("Each graphical password image must be unique.", "danger")
            return render_template("auth/register.html", form=form, image_choices=image_choices)

        existing_user = User.query.filter(
            or_(User.username == form.username.data, User.email == form.email.data)
        ).first()
        if existing_user:
            flash("A user with this username or email already exists.", "danger")
            return render_template("auth/register.html", form=form, image_choices=image_choices)

        encrypted_pattern = encrypt_pattern(",".join(pattern))
        user = User(
            full_name=form.full_name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            password_hash=hash_password(form.password.data),
            image_pattern_encrypted=encrypted_pattern,
            image_pattern_hint=" > ".join(pattern),
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            ImageAuthentication(
                user_id=user.id,
                pattern_preview="Secure image sequence configured",
                image_count=len(pattern),
            )
        )
        db.session.commit()
        log_access(user.id, "register", "success", details="New user registration completed.")
        flash("Account created. Sign in to complete secure multi-stage authentication.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, image_choices=image_choices)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        identity = form.identity.data.strip()
        user = User.query.filter(or_(User.username == identity, User.email == identity.lower())).first()

        if not user or not verify_password(form.password.data, user.password_hash):
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                db.session.commit()
            flash("Invalid credentials.", "danger")
            return render_template("auth/login.html", form=form)

        if user.is_locked:
            flash("Your account is temporarily locked due to failed login attempts.", "danger")
            return render_template("auth/login.html", form=form)

        user.failed_login_attempts = 0
        db.session.commit()
        session["stage1_user_id"] = user.id
        session["stage1_passed_at"] = datetime.utcnow().isoformat()
        flash("Stage 1 passed. Complete image-based verification.", "info")
        return redirect(url_for("auth.image_login"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/image-login", methods=["GET", "POST"])
def image_login():
    user_id = session.get("stage1_user_id")
    if not user_id:
        flash("Please complete password authentication first.", "warning")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)
    form = ImageLoginForm()
    image_choices = current_app.config["IMAGE_AUTH_IMAGES"]

    if form.validate_on_submit():
        selected_images = request.form.get("image_pattern", "")
        if selected_images == decrypt_pattern(user.image_pattern_encrypted):
            login_user(user)
            session.pop("stage1_user_id", None)
            session.pop("stage1_passed_at", None)
            session.permanent = True
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            log_access(user.id, "login", "success", details="Multi-stage authentication successful.")
            flash("Secure login complete.", "success")
            return redirect(url_for("main.dashboard"))

        user.failed_login_attempts += 1
        db.session.commit()
        log_access(user.id, "login", "failed", details="Incorrect image authentication sequence.")
        flash("Incorrect image sequence. Access denied.", "danger")

    return render_template("auth/image_login.html", form=form, image_choices=image_choices, user=user)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    reset_url = None

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token, expiry = make_reset_token()
            user.reset_token = token
            user.reset_token_expiry = expiry
            db.session.commit()
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            log_access(user.id, "password_reset_requested", "success")
        flash("If the account exists, a reset link has been generated.", "info")

    return render_template("auth/forgot_password.html", form=form, reset_url=reset_url)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    user = User.query.filter_by(reset_token=token).first_or_404()
    if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash("Reset link has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = hash_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        user.failed_login_attempts = 0
        user.is_locked = False
        db.session.commit()
        log_access(user.id, "password_reset_completed", "success")
        flash("Password reset complete. Please sign in again.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if getattr(current_user, "role", "") == "admin":
        return redirect(url_for("admin.dashboard"))

    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip().lower()
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    actor_id = getattr(current_user, "id", None)
    if actor_id:
        try:
            log_access(actor_id, "logout", "success")
        except Exception:
            db.session.rollback()
    logout_user()
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))
