from flask import Blueprint, jsonify, request, url_for, session
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_identity, get_jwt,
    jwt_required, create_access_token
)
from email_validator import validate_email, EmailNotValidError
import re
import phonenumbers as pn
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from uuid import uuid4
from datetime import timedelta
from flask_mail import Mail, Message
from models import db, User
from config_settings import Config
from oauth_config import oauth

# Authentication Blueprint
auth_bp = Blueprint('auth', __name__)

def generate_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": str(user.role.value)  # Ensure the role is correctly retrieved
        },
        expires_delta=timedelta(days=30)
    )

@auth_bp.route('/login/google')
def google_login():
    state = str(uuid4())
    session["oauth_state"] = state
    session.modified = True
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    return oauth.google.authorize_redirect(redirect_uri, state=state)

@auth_bp.route("/callback/google")
def google_callback():
    try:
        received_state = request.args.get("state")
        stored_state = session.pop("oauth_state", None)

        if not stored_state or not received_state or stored_state != received_state:
            return jsonify({"error": "Invalid state, possible CSRF attack"}), 400

        token = oauth.google.authorize_access_token()
        user_info = oauth.google.get("userinfo").json()

        if not user_info or "email" not in user_info:
            return jsonify({"error": "Failed to retrieve user information"}), 400

        email = user_info["email"]
        name = user_info.get("name", "")
        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(email=email, userfullnames=name, role="PATIENT")
            db.session.add(user)
            db.session.commit()

        access_token = generate_token(user)
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_role"] = str(user.role.value)
        session.modified = True

        return jsonify({"msg": "Login successful", "access_token": access_token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            print(f"DEBUG: Claims retrieved: {claims}")  # Debugging

            if "role" not in claims or claims["role"] != required_role:
                return jsonify({"msg": "Forbidden: Access Denied"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def is_valid_email(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=True)
        return True
    except EmailNotValidError:
        return False

SAFARICOM_PREFIXES = {
    "0701", "0702", "0703", "0704", "0705", "0706", "0707", "0708", "0709",
    "0710", "0711", "0712", "0713", "0714", "0715", "0716", "0717", "0718", "0719",
    "0720", "0721", "0722", "0723", "0724", "0725", "0726", "0727", "0728", "0729",
    "0740", "0741", "0742", "0743", "0744", "0745", "0746", "0747", "0748", "0749",
    "0757", "0758", "0768", "0769", "0790", "0791", "0792", "0793", "0794", "0795",
    "0796", "0797", "0798", "0799", "0110", "0111", "0112", "0113", "0114", "0115"
}

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    phone = re.sub(r"\D", "", phone)
    if phone.startswith("+254"):
        phone = "0" + phone[4:]
    elif phone.startswith("254") and len(phone) == 12:
        phone = "0" + phone[3:]
    return phone

def is_valid_safaricom_phone(phone: str, region="KE") -> bool:
    phone = normalize_phone(phone)
    if not phone or len(phone) < 10:
        return False
    try:
        parsed_number = pn.parse(phone, region)
        if not pn.is_valid_number(parsed_number):
            return False
    except pn.phonenumberutil.NumberParseException:
        return False
    return phone[:4] in SAFARICOM_PREFIXES

def validate_password(password: str) -> bool:
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password))

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    userfullnames = data.get("userfullnames")
    role = "PATIENT"

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400

    if not phone or not is_valid_safaricom_phone(phone):
        return jsonify({"msg": "Invalid phone number. Must be a valid Safaricom number."}), 400

    if not validate_password(password):
        return jsonify({"msg": "Password must be at least 8 characters long, contain letters and numbers"}), 400

    if User.query.filter_by(email=email).first() or User.query.filter_by(phone_number=phone).first():
        return jsonify({"msg": "Email or phone number already registered"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, phone_number=phone, password=hashed_password, userfullnames=userfullnames, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User registered successfully"}), 201

@auth_bp.route('/admin/register-admin', methods=['POST'])
@role_required('ADMIN')
def register_admin():
    data = request.get_json()
    userfullnames = data.get("userfullnames")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400

    if not is_valid_safaricom_phone(phone):
        return jsonify({"msg": "Invalid phone number. Must be a valid Safaricom number."}), 400

    if not validate_password(password):
        return jsonify({"msg": "Password must be at least 8 characters long, contain letters and numbers"}), 400

    if User.query.filter_by(email=email).first() or User.query.filter_by(phone_number=phone).first():
        return jsonify({"msg": "Email or phone number already registered"}), 400

    hashed_password = generate_password_hash(password)
    new_admin = User(userfullnames=userfullnames, email=email, phone_number=phone, password=hashed_password, role="ADMIN")
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"msg": "Admin registered successfully"}), 201

@auth_bp.route('/admin/register-doctor', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def register_doctor():
    return register_user("DOCTOR")

@auth_bp.route('/admin/register-nurse', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def register_nurse():
    return register_user("NURSE")

@auth_bp.route('/admin/register-receptionist', methods=['POST'])
@jwt_required()
@role_required('ADMIN')
def register_receptionist():
    return register_user("RECEPTIONIST")

def register_user(role):
    data = request.get_json()
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    userfullnames = data.get("userfullnames")

    if not email or not phone or not password or not userfullnames:
        return jsonify({"msg": "Email, phone, password, and full names are required"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address"}), 400

    if not is_valid_safaricom_phone(phone):
        return jsonify({"msg": "Invalid phone number. Must be a valid Safaricom number."}), 400

    if not validate_password(password):
        return jsonify({"msg": "Password must be at least 8 characters long, contain letters and numbers"}), 400

    if User.query.filter_by(email=email).first() or User.query.filter_by(phone_number=phone).first():
        return jsonify({"msg": "Email or phone number already registered"}), 400

    try:
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, phone_number=phone, password=hashed_password, userfullnames=userfullnames, role=role)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": f"{role.capitalize()} registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Internal Server Error", "error": str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = generate_token(user)
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": str(user.role.value)
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    from app import mail
    from itsdangerous import URLSafeTimedSerializer

    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"msg": "Email not found"}), 404

    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    token = serializer.dumps(email, salt="reset-password-salt")
    reset_link = url_for('auth.reset_password', token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f"Click the link to reset your password: {reset_link}"
    mail.send(msg)

    return jsonify({"msg": "Reset link sent to your email"}), 200

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    try:
        email = serializer.loads(token, salt="reset-password-salt", max_age=3600)
    except:
        return jsonify({"msg": "Invalid or expired token"}), 400

    data = request.get_json()
    new_password = data.get("password")

    if not new_password or len(new_password) < 6:
        return jsonify({"msg": "Password must be at least 6 characters long"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"msg": "Password reset successful"}), 200
