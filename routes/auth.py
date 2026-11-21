import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, execute_db
from routes import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        currency = request.form.get('currency', '$').strip()

        # Validation
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('auth/register.html', username=username, email=email)
        
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', username=username, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', username=username, email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', username=username, email=email)

        # Check existing username or email
        existing_user = query_db(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email), one=True
        )
        if existing_user:
            flash('Username or email is already registered. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        # Hash password and create user
        password_hash = generate_password_hash(password)
        try:
            user_id = execute_db(
                "INSERT INTO users (username, email, password_hash, currency) VALUES (%s, %s, %s, %s)",
                (username, email, password_hash, currency), return_id=True
            )
            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred during registration. Please try again.', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')

        if not login_input or not password:
            flash('Please provide both username/email and password.', 'warning')
            return render_template('auth/login.html')

        user = query_db(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (login_input, login_input.lower()), one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['currency'] = user['currency'] or '$'
            session.permanent = True
            flash(f"Welcome back, {user['username']}!", 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_settings':
            currency = request.form.get('currency', '$').strip()
            execute_db("UPDATE users SET currency = %s WHERE id = %s", (currency, user_id))
            session['currency'] = currency
            flash('Preferences updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
            
        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            if not check_password_hash(user['password_hash'], old_password):
                flash('Current password does not match.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
            else:
                new_hash = generate_password_hash(new_password)
                execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
                flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', user=user)
