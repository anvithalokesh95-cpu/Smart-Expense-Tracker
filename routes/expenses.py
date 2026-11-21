from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import query_db, execute_db
from routes import login_required

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/expenses')
@login_required
def index():
    user_id = session['user_id']
    category_filter = request.args.get('category', '').strip()
    month_filter = request.args.get('month', '').strip()
    search_query = request.args.get('search', '').strip()

    # Base query
    sql = """
        SELECT e.id, e.amount, e.expense_date, e.description, e.payment_method,
               c.id AS category_id, c.name AS category_name, c.icon AS category_icon, c.color AS category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s
    """
    params = [user_id]

    if category_filter and category_filter.isdigit():
        sql += " AND e.category_id = %s"
        params.append(int(category_filter))

    if month_filter:
        try:
            yr, mo = month_filter.split('-')
            sql += " AND YEAR(e.expense_date) = %s AND MONTH(e.expense_date) = %s"
            params.extend([int(yr), int(mo)])
        except ValueError:
            pass

    if search_query:
        sql += " AND (e.description LIKE %s OR c.name LIKE %s OR e.payment_method LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term, like_term])

    sql += " ORDER BY e.expense_date DESC, e.id DESC"

    expenses = query_db(sql, tuple(params))
    total_spent = sum(float(item['amount']) for item in expenses)

    # Categories list for dropdown (system defaults + user created)
    categories = query_db("""
        SELECT id, name, icon, color
        FROM categories
        WHERE type = 'expense' AND (user_id IS NULL OR user_id = %s)
        ORDER BY name ASC
    """, (user_id,))

    return render_template(
        'expenses.html',
        expenses=expenses,
        total_spent=total_spent,
        categories=categories,
        selected_category=category_filter,
        selected_month=month_filter,
        search_query=search_query,
        today=date.today().strftime('%Y-%m-%d')
    )

@expenses_bp.route('/expenses/add', methods=['POST'])
@login_required
def add():
    user_id = session['user_id']
    amount = request.form.get('amount', '').strip()
    category_id = request.form.get('category_id', '').strip()
    expense_date = request.form.get('expense_date', '').strip()
    description = request.form.get('description', '').strip()
    payment_method = request.form.get('payment_method', 'Cash').strip()

    # Validation
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('expenses.index'))
    except ValueError:
        flash('Please enter a valid numeric amount.', 'danger')
        return redirect(url_for('expenses.index'))

    if not category_id:
        flash('Please select an expense category.', 'danger')
        return redirect(url_for('expenses.index'))

    if not expense_date:
        expense_date = date.today().strftime('%Y-%m-%d')

    try:
        execute_db("""
            INSERT INTO expenses (user_id, category_id, amount, expense_date, description, payment_method)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, category_id, amount_val, expense_date, description, payment_method))
        flash('Expense recorded successfully!', 'success')
    except Exception as e:
        flash('Could not record expense. Please try again.', 'danger')

    return redirect(url_for('expenses.index'))

@expenses_bp.route('/api/expenses/<int:expense_id>')
@login_required
def get_expense(expense_id):
    user_id = session['user_id']
    expense = query_db("""
        SELECT id, category_id, amount, expense_date, description, payment_method
        FROM expenses
        WHERE id = %s AND user_id = %s
    """, (expense_id, user_id), one=True)

    if not expense:
        return jsonify({'error': 'Expense not found'}), 404

    # Convert date to string for JSON serialization
    expense['expense_date'] = expense['expense_date'].strftime('%Y-%m-%d')
    expense['amount'] = float(expense['amount'])
    return jsonify(expense)

@expenses_bp.route('/expenses/edit/<int:expense_id>', methods=['POST'])
@login_required
def edit(expense_id):
    user_id = session['user_id']
    amount = request.form.get('amount', '').strip()
    category_id = request.form.get('category_id', '').strip()
    expense_date = request.form.get('expense_date', '').strip()
    description = request.form.get('description', '').strip()
    payment_method = request.form.get('payment_method', 'Cash').strip()

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('expenses.index'))
    except ValueError:
        flash('Please enter a valid numeric amount.', 'danger')
        return redirect(url_for('expenses.index'))

    try:
        rows = execute_db("""
            UPDATE expenses
            SET category_id = %s, amount = %s, expense_date = %s, description = %s, payment_method = %s
            WHERE id = %s AND user_id = %s
        """, (category_id, amount_val, expense_date, description, payment_method, expense_id, user_id))
        
        if rows:
            flash('Expense updated successfully!', 'success')
        else:
            flash('Expense could not be updated or was not found.', 'warning')
    except Exception as e:
        flash('Error updating expense.', 'danger')

    return redirect(url_for('expenses.index'))

@expenses_bp.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete(expense_id):
    user_id = session['user_id']
    try:
        rows = execute_db("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user_id))
        if rows:
            flash('Expense deleted successfully.', 'info')
        else:
            flash('Expense not found or unauthorized.', 'warning')
    except Exception as e:
        flash('Error deleting expense.', 'danger')

    return redirect(url_for('expenses.index'))
