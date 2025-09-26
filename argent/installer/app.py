<<<<<<< HEAD
import os
import asyncio
import logging
import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
from .telethon_manager import (
    validate_bot_token,
    TelethonAuthFlow,
    SessionStore,
    AuthError,
)
from .bot_runner import global_bot_runner
from ..security.owner_manager import OwnerManager

load_dotenv()

class SecureTokenManager:

    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv("MASTER_KEY", self._generate_master_key())

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'argent_userbot_salt_2024',
            iterations=100000,
        )
        self.encryption_key = kdf.derive(master_key.encode())
        fernet_key = base64.urlsafe_b64encode(self.encryption_key)
        self.cipher = Fernet(fernet_key)

        self.session_tokens = {}
        self.csrf_tokens = {}

    def _generate_master_key(self) -> str:
        return secrets.token_urlsafe(32)

    def encrypt_token(self, token: str) -> str:
        try:
            encrypted = self.cipher.encrypt(token.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logging.error(f"Ошибка шифрования токена: {e}")
            raise

    def decrypt_token(self, encrypted_token: str) -> str:
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
        except Exception as e:
            logging.error(f"Ошибка расшифровки токена: {e}")
            raise

    def store_token(self, session_id: str, token: str) -> None:
        encrypted_token = self.encrypt_token(token)
        self.session_tokens[session_id] = encrypted_token

    def get_token(self, session_id: str) -> str:
        encrypted_token = self.session_tokens.get(session_id)
        if encrypted_token:
            return self.decrypt_token(encrypted_token)
        return None

    def clear_token(self, session_id: str) -> None:
        if session_id in self.session_tokens:
            del self.session_tokens[session_id]
        if session_id in self.csrf_tokens:
            del self.csrf_tokens[session_id]

    def generate_csrf_token(self, session_id: str) -> str:
        csrf_token = secrets.token_urlsafe(32)
        signature = hmac.new(
            self.encryption_key[:32],
            csrf_token.encode(),
            hashlib.sha256
        ).hexdigest()
        full_token = f"{csrf_token}.{signature}"
        self.csrf_tokens[session_id] = full_token
        return full_token

    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        stored_token = self.csrf_tokens.get(session_id)
        if not stored_token or not token:
            return False

        try:
            if '.' not in token:
                return False

            token_part, signature = token.rsplit('.', 1)
            stored_part, stored_signature = stored_token.rsplit('.', 1)

            expected_signature = hmac.new(
                self.encryption_key[:32],
                token_part.encode(),
                hashlib.sha256
            ).hexdigest()

            return (hmac.compare_digest(signature, expected_signature) and
                    hmac.compare_digest(token, stored_token))
        except Exception:
            return False

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
        BRAND_NAME="Argent UserBot",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        WTF_CSRF_ENABLED=True,
    )

    token_manager = SecureTokenManager()

    csrf = CSRFProtect(app)

    if not os.getenv("DEBUG", "false").lower() == "true":
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    store = SessionStore(base_dir=os.getenv("ARGENT_DATA_DIR", ".argent_data"))

    def sanitize_input(data: str, max_length: int = 100) -> str:
        if not data:
            return ""
        import re
        cleaned = re.sub(r'[^\w\-:.]', '', data.strip())
        return cleaned[:max_length]

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())

    @app.after_request
    def after_request(response):
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none';"
        return response
    @app.route("/")
    def index():
        brand = app.config["BRAND_NAME"]
        try:
            owner_mgr = OwnerManager()
            install_success = owner_mgr.has_primary_owner()
            owner_id = owner_mgr.get_primary_owner() if install_success else None
        except Exception:
            install_success = False
            owner_id = None
        return render_template(
            "installer_step1.html",
            brand=brand,
            install_success=install_success,
            owner_id=owner_id,
        )

    @app.route("/setup/bot-token", methods=["POST"])
    def setup_bot_token():
        try:
            raw_token = request.form.get("bot_token", "").strip()

            if not raw_token or len(raw_token) > 100:
                app.logger.warning(f"Invalid token length from {request.remote_addr}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Неверная длина токена"
                ), 400

            if not validate_bot_token(raw_token):
                app.logger.warning(f"Invalid bot token format from {request.remote_addr}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Неверный формат токена бота"
                ), 400

            try:
                encrypted_token = token_manager.encrypt_token(raw_token)
                session['encrypted_token'] = encrypted_token
                session['token_timestamp'] = datetime.now().isoformat()
            except Exception as e:
                app.logger.error(f"Token encryption failed: {e}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Ошибка обработки токена. Попробуйте снова."
                ), 500

            global_bot_runner.start(bot_token=raw_token, store=store)
            username = global_bot_runner.get_username_sync(raw_token)

            if not username:
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Не удалось получить имя бота. Проверьте токен и попробуйте снова."
                ), 400

            raw_token = None

            app.logger.info(f"Successful bot token validation from {request.remote_addr}")
            return redirect(f"https://t.me/{username}?start=install")

        except Exception as e:
            app.logger.error(f"Unexpected error in setup_bot_token: {e}")
            return render_template(
                "installer_step1.html",
                brand=app.config["BRAND_NAME"],
                error="Произошла неожиданная ошибка. Попробуйте снова."
            ), 500

    @app.route("/setup/success")
    def setup_success():
        return render_template("installer_success.html", brand=app.config["BRAND_NAME"])

    @app.route("/menu")
    def main_menu():
        return render_template("main_menu.html", brand=app.config["BRAND_NAME"])

    @app.errorhandler(404)
    def not_found(error):
        return render_template("installer_step1.html",
                             brand=app.config["BRAND_NAME"],
                             error="Страница не найдена"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("installer_step1.html",
                             brand=app.config["BRAND_NAME"],
                             error="Внутренняя ошибка сервера"), 500

    return app

=======
import os
import asyncio
import logging
import secrets
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
from .telethon_manager import (
    validate_bot_token,
    TelethonAuthFlow,
    SessionStore,
    AuthError,
)
from .bot_runner import global_bot_runner
from ..security.owner_manager import OwnerManager

load_dotenv()

class SecureTokenManager:

    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv("MASTER_KEY", self._generate_master_key())

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'argent_userbot_salt_2024',
            iterations=100000,
        )
        self.encryption_key = kdf.derive(master_key.encode())
        fernet_key = base64.urlsafe_b64encode(self.encryption_key)
        self.cipher = Fernet(fernet_key)

        self.session_tokens = {}
        self.csrf_tokens = {}

    def _generate_master_key(self) -> str:
        return secrets.token_urlsafe(32)

    def encrypt_token(self, token: str) -> str:
        try:
            encrypted = self.cipher.encrypt(token.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logging.error(f"Ошибка шифрования токена: {e}")
            raise

    def decrypt_token(self, encrypted_token: str) -> str:
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_token.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
        except Exception as e:
            logging.error(f"Ошибка расшифровки токена: {e}")
            raise

    def store_token(self, session_id: str, token: str) -> None:
        encrypted_token = self.encrypt_token(token)
        self.session_tokens[session_id] = encrypted_token

    def get_token(self, session_id: str) -> str:
        encrypted_token = self.session_tokens.get(session_id)
        if encrypted_token:
            return self.decrypt_token(encrypted_token)
        return None

    def clear_token(self, session_id: str) -> None:
        if session_id in self.session_tokens:
            del self.session_tokens[session_id]
        if session_id in self.csrf_tokens:
            del self.csrf_tokens[session_id]

    def generate_csrf_token(self, session_id: str) -> str:
        csrf_token = secrets.token_urlsafe(32)
        signature = hmac.new(
            self.encryption_key[:32],
            csrf_token.encode(),
            hashlib.sha256
        ).hexdigest()
        full_token = f"{csrf_token}.{signature}"
        self.csrf_tokens[session_id] = full_token
        return full_token

    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        stored_token = self.csrf_tokens.get(session_id)
        if not stored_token or not token:
            return False

        try:
            if '.' not in token:
                return False

            token_part, signature = token.rsplit('.', 1)
            stored_part, stored_signature = stored_token.rsplit('.', 1)

            expected_signature = hmac.new(
                self.encryption_key[:32],
                token_part.encode(),
                hashlib.sha256
            ).hexdigest()

            return (hmac.compare_digest(signature, expected_signature) and
                    hmac.compare_digest(token, stored_token))
        except Exception:
            return False

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
        BRAND_NAME="Argent UserBot",
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
        WTF_CSRF_ENABLED=True,
    )

    token_manager = SecureTokenManager()

    csrf = CSRFProtect(app)

    if not os.getenv("DEBUG", "false").lower() == "true":
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    store = SessionStore(base_dir=os.getenv("ARGENT_DATA_DIR", ".argent_data"))

    def sanitize_input(data: str, max_length: int = 100) -> str:
        if not data:
            return ""
        import re
        cleaned = re.sub(r'[^\w\-:.]', '', data.strip())
        return cleaned[:max_length]

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())

    @app.after_request
    def after_request(response):
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none';"
        return response
    @app.route("/")
    def index():
        brand = app.config["BRAND_NAME"]
        try:
            owner_mgr = OwnerManager()
            install_success = owner_mgr.has_primary_owner()
            owner_id = owner_mgr.get_primary_owner() if install_success else None
        except Exception:
            install_success = False
            owner_id = None
        return render_template(
            "installer_step1.html",
            brand=brand,
            install_success=install_success,
            owner_id=owner_id,
        )

    @app.route("/setup/bot-token", methods=["POST"])
    def setup_bot_token():
        try:
            raw_token = request.form.get("bot_token", "").strip()

            if not raw_token or len(raw_token) > 100:
                app.logger.warning(f"Invalid token length from {request.remote_addr}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Неверная длина токена"
                ), 400

            if not validate_bot_token(raw_token):
                app.logger.warning(f"Invalid bot token format from {request.remote_addr}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Неверный формат токена бота"
                ), 400

            try:
                encrypted_token = token_manager.encrypt_token(raw_token)
                session['encrypted_token'] = encrypted_token
                session['token_timestamp'] = datetime.now().isoformat()
            except Exception as e:
                app.logger.error(f"Token encryption failed: {e}")
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Ошибка обработки токена. Попробуйте снова."
                ), 500

            global_bot_runner.start(bot_token=raw_token, store=store)
            username = global_bot_runner.get_username_sync(raw_token)

            if not username:
                return render_template(
                    "installer_step1.html",
                    brand=app.config["BRAND_NAME"],
                    error="Не удалось получить имя бота. Проверьте токен и попробуйте снова."
                ), 400

            raw_token = None

            app.logger.info(f"Successful bot token validation from {request.remote_addr}")
            return redirect(f"https://t.me/{username}?start=install")

        except Exception as e:
            app.logger.error(f"Unexpected error in setup_bot_token: {e}")
            return render_template(
                "installer_step1.html",
                brand=app.config["BRAND_NAME"],
                error="Произошла неожиданная ошибка. Попробуйте снова."
            ), 500

    @app.route("/setup/success")
    def setup_success():
        return render_template("installer_success.html", brand=app.config["BRAND_NAME"])

    @app.route("/menu")
    def main_menu():
        return render_template("main_menu.html", brand=app.config["BRAND_NAME"])

    @app.errorhandler(404)
    def not_found(error):
        return render_template("installer_step1.html",
                             brand=app.config["BRAND_NAME"],
                             error="Страница не найдена"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("installer_step1.html",
                             brand=app.config["BRAND_NAME"],
                             error="Внутренняя ошибка сервера"), 500

    return app

>>>>>>> 6baa4adf9f73b732ceaaaecf1d22014eadf81005
