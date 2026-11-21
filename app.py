import os
from flask import Flask, render_template, session
from config import Config
from database import init_db, query_db

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.expenses import expenses_bp
from routes.incomes import incomes_bp
from routes.budgets import budgets_bp
from routes.analytics import analytics_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize MySQL Database & Tables
    with app.app_context():
        init_db()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(incomes_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)

    # Custom Jinja Filters
    @app.template_filter('currency')
    def currency_filter(amount):
        """Formats numbers into standard currency string with user's symbol"""
        sym = session.get('currency', '$')
        try:
            val = float(amount)
            return f"{sym} {val:,.2f}"
        except (ValueError, TypeError):
            return f"{sym} 0.00"

    @app.template_filter('format_date')
    def format_date_filter(d, fmt='%b %d, %Y'):
        """Formats date object or ISO string into readable format"""
        if not d:
            return ''
        if hasattr(d, 'strftime'):
            return d.strftime(fmt)
        try:
            from datetime import datetime
            return datetime.strptime(str(d), '%Y-%m-%d').strftime(fmt)
        except Exception:
            return str(d)

    # Global Context Processor
    @app.context_processor
    def inject_user_context():
        user = None
        if 'user_id' in session:
            user = {
                'id': session['user_id'],
                'username': session.get('username', 'User'),
                'email': session.get('email', ''),
                'currency': session.get('currency', '$')
            }
        return dict(current_user=user)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Default port 5000, host 127.0.0.1
    print("\n" + "=" * 60)
    print("  Smart Expense Tracker Web Application")
    print("  URL: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(host='127.0.0.1', port=5000, debug=True)
