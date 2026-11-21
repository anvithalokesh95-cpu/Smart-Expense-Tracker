from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import query_db, execute_db
from routes import login_required

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/budgets')
@login_required
def index():
    user_id = session['user_id']
    now = datetime.now()

    # Allow filtering by month/year (default to current month)
    selected_month_str = request.args.get('month', now.strftime('%Y-%m'))
    try:
        cur_year, cur_month = map(int, selected_month_str.split('-'))
    except ValueError:
        cur_year, cur_month = now.year, now.month
        selected_month_str = now.strftime('%Y-%m')

    # 1. Fetch Overall Budget for this month
    overall_budget_row = query_db("""
        SELECT id, amount FROM budgets
        WHERE user_id = %s AND category_id IS NULL AND month = %s AND year = %s
    """, (user_id, cur_month, cur_year), one=True)

    # 2. Total spending for this month
    total_month_spent_row = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s AND YEAR(expense_date) = %s AND MONTH(expense_date) = %s
    """, (user_id, cur_year, cur_month), one=True)
    total_month_spent = float(total_month_spent_row['total']) if total_month_spent_row else 0.0

    overall_budget = None
    if overall_budget_row:
        b_amount = float(overall_budget_row['amount'])
        spent_pct = round((total_month_spent / b_amount) * 100, 1) if b_amount > 0 else 0
        status = 'danger' if spent_pct >= 100 else ('warning' if spent_pct >= 80 else 'success')
        overall_budget = {
            'id': overall_budget_row['id'],
            'amount': b_amount,
            'spent': total_month_spent,
            'remaining': b_amount - total_month_spent,
            'percentage': spent_pct,
            'status': status
        }

    # 3. Fetch Category Budgets for this month with actual spending
    category_budgets = query_db("""
        SELECT b.id, b.category_id, b.amount AS budget_amount,
               c.name AS category_name, c.icon AS category_icon, c.color AS category_color,
               COALESCE((
                   SELECT SUM(e.amount)
                   FROM expenses e
                   WHERE e.user_id = %s AND e.category_id = b.category_id
                     AND YEAR(e.expense_date) = %s AND MONTH(e.expense_date) = %s
               ), 0) AS spent_amount
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.user_id = %s AND b.month = %s AND b.year = %s
        ORDER BY c.name ASC
    """, (user_id, cur_year, cur_month, user_id, cur_month, cur_year))

    budget_items = []
    has_exceeded_budget = False
    has_warning_budget = False

    for item in category_budgets:
        b_amt = float(item['budget_amount'])
        spent = float(item['spent_amount'])
        pct = round((spent / b_amt) * 100, 1) if b_amt > 0 else 0
        rem = b_amt - spent

        if pct >= 100:
            status = 'danger'
            has_exceeded_budget = True
        elif pct >= 80:
            status = 'warning'
            has_warning_budget = True
        else:
            status = 'success'

        budget_items.append({
            'id': item['id'],
            'category_id': item['category_id'],
            'category_name': item['category_name'],
            'category_icon': item['category_icon'],
            'category_color': item['color'],
            'budget_amount': b_amt,
            'spent_amount': spent,
            'remaining': rem,
            'percentage': pct,
            'status': status
        })

    # Available categories for adding category-specific budget
    categories = query_db("""
        SELECT id, name FROM categories
        WHERE type = 'expense' AND (user_id IS NULL OR user_id = %s)
        ORDER BY name ASC
    """, (user_id,))

    return render_template(
        'budgets.html',
        selected_month_str=selected_month_str,
        selected_month=cur_month,
        selected_year=cur_year,
        overall_budget=overall_budget,
        category_budgets=budget_items,
        categories=categories,
        has_exceeded_budget=has_exceeded_budget,
        has_warning_budget=has_warning_budget
    )

@budgets_bp.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    user_id = session['user_id']
    budget_type = request.form.get('budget_type', 'overall') # 'overall' or 'category'
    category_id = request.form.get('category_id') if budget_type == 'category' else None
    amount = request.form.get('amount', '').strip()
    month_str = request.form.get('month_str', '').strip()

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            flash('Budget amount must be greater than zero.', 'danger')
            return redirect(url_for('budgets.index', month=month_str))
    except ValueError:
        flash('Please enter a valid numeric budget amount.', 'danger')
        return redirect(url_for('budgets.index', month=month_str))

    try:
        yr, mo = map(int, month_str.split('-'))
    except Exception:
        now = datetime.now()
        yr, mo = now.year, now.month

    # If category_id is empty string, convert to None for SQL NULL
    if category_id == '' or category_id == 'none':
        category_id = None

    try:
        # Insert or update
        if category_id is None:
            # Check existing overall budget
            existing = query_db("""
                SELECT id FROM budgets
                WHERE user_id = %s AND category_id IS NULL AND month = %s AND year = %s
            """, (user_id, mo, yr), one=True)
            if existing:
                execute_db("UPDATE budgets SET amount = %s WHERE id = %s", (amount_val, existing['id']))
            else:
                execute_db("""
                    INSERT INTO budgets (user_id, category_id, amount, month, year)
                    VALUES (%s, NULL, %s, %s, %s)
                """, (user_id, amount_val, mo, yr))
        else:
            existing = query_db("""
                SELECT id FROM budgets
                WHERE user_id = %s AND category_id = %s AND month = %s AND year = %s
            """, (user_id, category_id, mo, yr), one=True)
            if existing:
                execute_db("UPDATE budgets SET amount = %s WHERE id = %s", (amount_val, existing['id']))
            else:
                execute_db("""
                    INSERT INTO budgets (user_id, category_id, amount, month, year)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, category_id, amount_val, mo, yr))

        flash('Budget configured successfully!', 'success')
    except Exception as e:
        flash('Failed to save budget settings.', 'danger')

    return redirect(url_for('budgets.index', month=month_str))

@budgets_bp.route('/budgets/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete(budget_id):
    user_id = session['user_id']
    try:
        execute_db("DELETE FROM budgets WHERE id = %s AND user_id = %s", (budget_id, user_id))
        flash('Budget deleted successfully.', 'info')
    except Exception as e:
        flash('Error deleting budget.', 'danger')

    return redirect(url_for('budgets.index'))
