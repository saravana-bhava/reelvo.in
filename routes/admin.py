# ================================================
# File:         routes/admin.py
# Description:  Admin routes for managing Users and Reels
# Framework:    Flask + TailwindCSS
# Version:      1.0.0
# Last Updated: 18 August 2025
# Author:       Saravana Bhava
# Author URL:   https://SazM.in
# ================================================

from flask import Blueprint, render_template, redirect, url_for, request, flash
from models.user import User
from models.reel import Reel
from models import db
from functools import wraps
from utils.auth_utils import get_user_email

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# --- Config ---
ADMIN_EMAIL = "sabajobs@gmail.com"
PER_PAGE = 10


# --- Decorators ---
def admin_required(f):
    """Restrict route access to admin user (simple email-based check)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if get_user_email() != ADMIN_EMAIL:
            flash("❌ Unauthorized access", "danger")
            return redirect(url_for("auth.index"))
        return f(*args, **kwargs)
    return decorated


# --- Dashboard ---
@admin_bp.route("/")
@admin_required
def dashboard():
    """Admin dashboard showing quick stats."""
    users_count = User.query.count()
    reels_count = Reel.query.count()
    return render_template(
        "admin/dashboard.html",
        users_count=users_count,
        reels_count=reels_count
    )


# --- Users CRUD ---
@admin_bp.route("/users")
@admin_required
def users_list():
    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    search = request.args.get("search", "")

    query = User.query

    # Search filter
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.id.cast(db.String).ilike(f"%{search}%"))
        )

    # Sorting
    if hasattr(User, sort_by):
        order = db.desc if direction == "desc" else db.asc
        query = query.order_by(order(getattr(User, sort_by)))

    users = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        "admin/users_list.html",
        users=users,   # pass pagination object, not just .items
        sort_by=sort_by,
        direction=direction,
        search=search,
    )


@admin_bp.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    """Add new user by email."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            flash("⚠️ Email is required", "warning")
            return redirect(url_for("admin.add_user"))

        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already exists", "danger")
            return redirect(url_for("admin.add_user"))

        new_user = User(email=email)
        db.session.add(new_user)
        db.session.commit()

        flash("✅ User added successfully", "success")
        return redirect(url_for("admin.users_list"))

    return render_template("admin/add_user.html")


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    """Edit user details."""
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        new_email = request.form.get("email", "").strip()

        if not new_email:
            flash("⚠️ Email is required", "warning")
            return redirect(url_for("admin.edit_user", user_id=user.id))

        if User.query.filter(User.email == new_email, User.id != user.id).first():
            flash("⚠️ Email already exists", "danger")
            return redirect(url_for("admin.edit_user", user_id=user.id))

        user.email = new_email
        db.session.commit()

        flash("✅ User updated successfully", "success")
        return redirect(url_for("admin.users_list"))

    return render_template("admin/edit_user.html", user=user)


@admin_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Delete user (POST only for safety)."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("🗑️ User deleted successfully", "success")
    return redirect(url_for("admin.users_list"))


# --- Reels CRUD ---
@admin_bp.route("/reels")
@admin_required
def reels_list():
    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort", "id")
    direction = request.args.get("dir", "asc")
    search = request.args.get("search", "")

    query = Reel.query

    # Search filter
    if search:
        query = query.filter(
            (Reel.title.ilike(f"%{search}%")) |
            (Reel.status.ilike(f"%{search}%")) |
            (Reel.id.cast(db.String).ilike(f"%{search}%"))
        )

    # Sorting
    if hasattr(Reel, sort_by):
        order = db.desc if direction == "desc" else db.asc
        query = query.order_by(order(getattr(Reel, sort_by)))

    reels = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        "admin/reels_list.html",
        reels=reels,
        sort_by=sort_by,
        direction=direction,
        search=search,
    )


@admin_bp.route("/reels/add", methods=["GET", "POST"])
@admin_required
def add_reel():
    """Add a new reel (basic fields)."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        status = request.form.get("status", "").strip()

        if not title:
            flash("⚠️ Title is required", "warning")
            return redirect(url_for("admin.add_reel"))

        new_reel = Reel(title=title, status=status or "draft")
        db.session.add(new_reel)
        db.session.commit()

        flash("✅ Reel added successfully", "success")
        return redirect(url_for("admin.reels_list"))

    return render_template("admin/add_reel.html")


@admin_bp.route("/reels/edit/<int:reel_id>", methods=["GET", "POST"])
@admin_required
def edit_reel(reel_id):
    """Edit reel details."""
    reel = Reel.query.get_or_404(reel_id)

    if request.method == "POST":
        reel.title = request.form.get("title", "").strip()
        reel.status = request.form.get("status", "").strip() or "draft"
        db.session.commit()

        flash("✅ Reel updated successfully", "success")
        return redirect(url_for("admin.reels_list"))

    return render_template("admin/edit_reel.html", reel=reel)


@admin_bp.route("/reels/delete/<int:reel_id>", methods=["POST"])
@admin_required
def delete_reel(reel_id):
    """Delete reel (POST only for safety)."""
    reel = Reel.query.get_or_404(reel_id)
    db.session.delete(reel)
    db.session.commit()
    flash("🗑️ Reel deleted successfully", "success")
    return redirect(url_for("admin.reels_list"))
