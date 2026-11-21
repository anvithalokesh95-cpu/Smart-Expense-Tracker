from datetime import datetime
from flask import Blueprint, render_template, session
from database import query_db
from routes import login_required
from services.insights_service import generate_smart_insights

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
@login_required
def index():
    user_id = session['user_id']
    now = datetime.now()

    # Generate complete smart insights
    insights = generate_smart_insights(user_id)

    # Detailed category breakdown for current month table
    category_breakdown = query_db("""
        SELECT c.id, c.name, c.icon, c.color,
               COALESCE(SUM(e.amount), 0) AS total_amount,
               COUNT(e.id) AS transaction_count
        FROM categories c
        JOIN expenses e ON e.category_id = c.id
        WHERE e.user_id = %s AND YEAR(e.expense_date) = %s AND MONTH(e.expense_date) = %s
        GROUP BY c.id, c.name, c.icon, c.color
        ORDER BY total_amount DESC
    """, (user_id, now.year, now.month))

    total_cur_month = insights['current_expenses']
    for cat in category_breakdown:
        amt = float(cat['total_amount'])
        cat['percentage'] = round((amt / total_cur_month * 100), 1) if total_cur_month > 0 else 0

    return render_template(
        'analytics.html',
        insights=insights,
        category_breakdown=category_breakdown,
        current_month_name=now.strftime('%B %Y')
    )
