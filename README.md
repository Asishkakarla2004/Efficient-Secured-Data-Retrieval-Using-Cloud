# Secure Cloud Data Access System

Secure Cloud Data Access System is a full-stack Flask and MySQL application for protected cloud-style file storage and retrieval. It combines multi-stage authentication, image-based verification, optimized Blowfish file encryption, access monitoring, and a premium cybersecurity-inspired interface.

## Highlights

- Stage 1 authentication with username or email plus bcrypt-hashed passwords
- Stage 2 graphical password verification using a 3-5 image sequence
- Secure file upload with Blowfish encryption before storage
- Secure file decryption during retrieval with performance logging
- User dashboard for files, activity, and encryption telemetry
- Admin dashboard for users, uploads, authentication logs, and crypto metrics
- CSRF protection, strong password validation, secure sessions, and input handling
- Deployment-ready structure for Render, Railway, and PythonAnywhere

## Tech Stack

- Backend: Python, Flask, SQLAlchemy
- Database: PostgreSQL on Render (MySQL supported locally)
- Frontend: HTML, Tailwind CSS, JavaScript
- Security: bcrypt, Fernet, Blowfish via PyCryptodome

## Project Structure

```text
app.py
secure_cloud_data_access_system/
  admin/
  authentication/
  cloud_storage/
  database/
  encryption/
  main/
  static/
    assets/images/
    css/
    js/
  templates/
  uploads/
requirements.txt
.env.example
README.md
```

## Setup

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a MySQL database and apply the schema in [schema.sql](/c:/Users/ADMIN/Desktop/Efficient%20Secured%20Data%20Retrieval%20Using%20Cloud/secure_cloud_data_access_system/database/schema.sql:1).
4. Copy `.env.example` to `.env` and update the secrets and `DATABASE_URL`.
5. Start the app:

```bash
flask --app app run
```

## Authentication Flow

1. User registers with full name, username, email, and a strong password.
2. User selects 3-5 images in a secret order for graphical authentication.
3. During login, stage 1 validates the password.
4. Stage 2 requires the same image sequence in the same order.

## File Security Flow

1. User uploads a supported file.
2. The app stores a temporary raw copy briefly.
3. The optimized Blowfish service encrypts the file before storage.
4. Metadata and encryption timing are saved in MySQL.
5. On download, the encrypted file is decrypted and delivered securely.

## Admin Notes

- Admin dashboard expects a user with `role='admin'` to exist in the `users` table, or you can extend the current `admin` table login flow.
- Failed logins and encryption activity are tracked through `access_logs` and `encryption_logs`.

## Deployment

### Render

- Create a new Web Service from your GitHub repo
- Set build command: `pip install -r requirements.txt && flask db upgrade`
- Set start command: `gunicorn app:app`
- Add environment variables from `.env` (set `FLASK_APP=app.py` and `DATABASE_URL` to your Render PostgreSQL database URL)
- Create a Render PostgreSQL database and connect it
- The app will use PostgreSQL instead of MySQL on Render

### Railway

- Create a Python service
- Add MySQL plugin or external MySQL database
- Set the same environment variables
- Start with `gunicorn app:app`

### PythonAnywhere

- Upload the project
- Create a virtualenv and install `requirements.txt`
- Configure the WSGI file to point to `app:app`
- Set environment variables in the web app configuration

## Security Improvements You Can Add Next

- Email delivery for password reset links
- TOTP or WebAuthn as an additional factor
- Object storage integration such as S3 or Cloudinary
- Background task queue for large file processing
- Streaming decryption downloads for very large files
