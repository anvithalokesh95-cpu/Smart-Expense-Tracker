from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from database import query_db
from routes import login_required
from services.insights_service import generate_smart_insights

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']
    now = datetime.now()
    cur_year = now.year
    cur_month = now.month

    # 1. All-time Totals
    all_income = query_db(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM incomes WHERE user_id = %s",
        (user_id,), one=True
    )['total']

    all_expenses = query_db(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s",
        (user_id,), one=True
    )['total']

    current_balance = float(all_income) - float(all_expenses)

    # 2. Current Month Totals
    cur_month_expenses = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s AND YEAR(expense_date) = %s AND MONTH(expense_date) = %s
    """, (user_id, cur_year, cur_month), one=True)['total']

    cur_month_income = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM incomes
        WHERE user_id = %s AND YEAR(income_date) = %s AND MONTH(income_date) = %s
    """, (user_id, cur_year, cur_month), one=True)['total']

    # 3. Monthly Budget & Warning state
    budget_row = query_db("""
        SELECT amount FROM budgets
        WHERE user_id = %s AND category_id IS NULL AND month = %s AND year = %s
    """, (user_id, cur_month, cur_year), one=True)

    monthly_budget = float(budget_row['amount']) if budget_row else 0.0
    budget_pct = 0
    budget_status = 'normal' # 'normal', 'warning' (>=80%), 'danger' (>=100%)
    if monthly_budget > 0:
        budget_pct = min(round((float(cur_month_expenses) / monthly_budget) * 100, 1), 100)
        actual_ratio = (float(cur_month_expenses) / monthly_budget) * 100
        if actual_ratio >= 100:
            budget_status = 'danger'
        elif actual_ratio >= 80:
            budget_status = 'warning'

    # 4. Recent Transactions (Unified list of latest 7 expenses and incomes)
    recent_expenses = query_db("""
        SELECT e.id, 'expense' AS type, e.amount, e.expense_date AS tx_date,
               e.description, e.payment_method, c.name AS category_name,
               c.icon AS category_icon, c.color AS category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
        ORDER BY e.expense_date DESC, e.id DESC
        LIMIT 6
    """, (user_id,))

    recent_incomes = query_db("""
        SELECT id, 'income' AS type, amount, income_date AS tx_date,
               description, 'Deposit' AS payment_method, source AS category_name,
               'wallet' AS category_icon, '#10B981' AS category_color
        FROM incomes
        WHERE user_id = %s
        ORDER BY income_date DESC, id DESC
        LIMIT 6
    """, (user_id,))

    # Merge and sort
    all_recent = list(recent_expenses) + list(recent_incomes)
    all_recent.sort(key=lambda x: x['tx_date'], reverse=True)
    recent_transactions = all_recent[:7]

    # 5. Smart Insights summary
    insights = generate_smart_insights(user_id)

    return render_template(
        'dashboard.html',
        total_income=float(all_income),
        total_expenses=float(all_expenses),
        current_balance=current_balance,
        monthly_spending=float(cur_month_expenses),
        monthly_income=float(cur_month_income),
        monthly_budget=monthly_budget,
        budget_pct=budget_pct,
        budget_status=budget_status,
        recent_transactions=recent_transactions,
        insights=insights
    )

@dashboard_bp.route('/api/chart-data')
@login_required
def chart_data():
    user_id = session['user_id']
    now = datetime.now()

    # 1. Category-wise Spending (Current Month)
    category_spending = query_db("""
        SELECT c.name, c.color, COALESCE(SUM(e.amount), 0) AS total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s AND YEAR(e.expense_date) = %s AND MONTH(e.expense_date) = %s
        GROUP BY c.id, c.name, c.color
        HAVING total > 0
        ORDER BY total DESC
    """, (user_id, now.year, now.month))

    cat_labels = [row['name'] for row in category_spending]
    cat_values = [float(row['total']) for row in category_spending]
    cat_colors = [row['color'] for row in category_spending]

    # 2. Monthly Trend (Last 6 Months: Expenses and Incomes)
    # Generate labels for past 6 months
    months_labels = []
    months_keys = []
    for i in range(5, -1, -1):
        # calculate year and month
        m = (now.month - i - 1) % 12 + 1
        y = now.year + ((now.month - i - 1) // 12)
        months_keys.append((y, m))
        months_labels.append(datetime(y, m, 1).strftime('%b %Y'))

    exp_by_month = {key: 0.0 for key in months_keys}
    inc_by_month = {key: 0.0 for key in months_keys}

    # Fetch last 6 months expenses
    exp_rows = query_db("""
        SELECT YEAR(expense_date) AS yr, MONTH(expense_date) AS mo, COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s AND expense_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY yr, mo
    """, (user_id,))
    for row in exp_rows:
        key = (row['yr'], row['mo'])
        if key in exp_by_month:
            exp_by_month[key] = float(row['total'])

    # Fetch last 6 months income
    inc_rows = query_db("""
        SELECT YEAR(income_date) AS yr, MONTH(income_date) AS mo, COALESCE(SUM(amount), 0) AS total
        FROM incomes
        WHERE user_id = %s AND income_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY yr, mo
    """, (user_id,))
    for row in inc_rows:
        key = (row['yr'], row['mo'])
        if key in inc_by_month:
            inc_by_month[key] = float(row['total'])

    monthly_expenses_values = [exp_by_month[k] for k in months_keys]
    monthly_incomes_values = [inc_by_month[k] for k in months_keys]

    return jsonify({
        'categories': {
            'labels': cat_labels,
            'values': cat_values,
            'colors': cat_colors
        },
        'trends': {
            'labels': months_labels,
            'expenses': monthly_expenses_values,
            'incomes': monthly_incomes_values
        }
    })
