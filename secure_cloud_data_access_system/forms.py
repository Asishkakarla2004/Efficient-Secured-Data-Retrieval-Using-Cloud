from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp


class RegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=4, max=80), Regexp(r"^[A-Za-z0-9_.-]+$")],
    )
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=64),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$",
                message="Use upper, lower, number, and special character.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create Secure Account")


class LoginForm(FlaskForm):
    identity = StringField("Username or Email", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Continue to Stage 2")


class ImageLoginForm(FlaskForm):
    submit = SubmitField("Verify & Access Dashboard")


class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Generate Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, max=64),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$",
                message="Use upper, lower, number, and special character.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")


class UploadForm(FlaskForm):
    file = FileField(
        "Secure File",
        validators=[
            FileRequired(),
            FileAllowed(
                ["pdf", "docx", "png", "jpg", "jpeg", "gif", "zip", "txt"],
                "Supported formats: PDF, DOCX, images, ZIP, TXT.",
            ),
        ],
    )
    access_scope = SelectField(
        "Access Scope",
        choices=[("private", "Private"), ("shared", "Shared"), ("restricted", "Restricted")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Encrypt & Upload")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("Update Profile")
