from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import query_db, execute_db
from routes import login_required

incomes_bp = Blueprint('incomes', __name__)

@incomes_bp.route('/income')
@login_required
def index():
    user_id = session['user_id']
    month_filter = request.args.get('month', '').strip()
    search_query = request.args.get('search', '').strip()

    sql = "SELECT id, source, amount, income_date, description FROM incomes WHERE user_id = %s"
    params = [user_id]

    if month_filter:
        try:
            yr, mo = month_filter.split('-')
            sql += " AND YEAR(income_date) = %s AND MONTH(income_date) = %s"
            params.extend([int(yr), int(mo)])
        except ValueError:
            pass

    if search_query:
        sql += " AND (source LIKE %s OR description LIKE %s)"
        like_term = f"%{search_query}%"
        params.extend([like_term, like_term])

    sql += " ORDER BY income_date DESC, id DESC"

    incomes = query_db(sql, tuple(params))
    total_income = sum(float(item['amount']) for item in incomes)

    # Standard income sources recommendations
    common_sources = ['Salary', 'Freelance', 'Investments', 'Side Business', 'Bonus', 'Rental Income', 'Dividends', 'Gift', 'Other']

    return render_template(
        'income.html',
        incomes=incomes,
        total_income=total_income,
        selected_month=month_filter,
        search_query=search_query,
        common_sources=common_sources,
        today=date.today().strftime('%Y-%m-%d')
    )

@incomes_bp.route('/income/add', methods=['POST'])
@login_required
def add():
    user_id = session['user_id']
    source = request.form.get('source', '').strip()
    amount = request.form.get('amount', '').strip()
    income_date = request.form.get('income_date', '').strip()
    description = request.form.get('description', '').strip()

    if not source:
        flash('Income source is required.', 'danger')
        return redirect(url_for('incomes.index'))

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('incomes.index'))
    except ValueError:
        flash('Please enter a valid numeric amount.', 'danger')
        return redirect(url_for('incomes.index'))

    if not income_date:
        income_date = date.today().strftime('%Y-%m-%d')

    try:
        execute_db("""
            INSERT INTO incomes (user_id, source, amount, income_date, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, source, amount_val, income_date, description))
        flash('Income recorded successfully!', 'success')
    except Exception as e:
        flash('Could not record income. Please try again.', 'danger')

    return redirect(url_for('incomes.index'))

@incomes_bp.route('/api/income/<int:income_id>')
@login_required
def get_income(income_id):
    user_id = session['user_id']
    income = query_db("""
        SELECT id, source, amount, income_date, description
        FROM incomes
        WHERE id = %s AND user_id = %s
    """, (income_id, user_id), one=True)

    if not income:
        return jsonify({'error': 'Income not found'}), 404

    income['income_date'] = income['income_date'].strftime('%Y-%m-%d')
    income['amount'] = float(income['amount'])
    return jsonify(income)

@incomes_bp.route('/income/edit/<int:income_id>', methods=['POST'])
@login_required
def edit(income_id):
    user_id = session['user_id']
    source = request.form.get('source', '').strip()
    amount = request.form.get('amount', '').strip()
    income_date = request.form.get('income_date', '').strip()
    description = request.form.get('description', '').strip()

    if not source:
        flash('Income source is required.', 'danger')
        return redirect(url_for('incomes.index'))

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('incomes.index'))
    except ValueError:
        flash('Please enter a valid numeric amount.', 'danger')
        return redirect(url_for('incomes.index'))

    try:
        rows = execute_db("""
            UPDATE incomes
            SET source = %s, amount = %s, income_date = %s, description = %s
            WHERE id = %s AND user_id = %s
        """, (source, amount_val, income_date, description, income_id, user_id))

        if rows:
            flash('Income updated successfully!', 'success')
        else:
            flash('Income could not be updated or was not found.', 'warning')
    except Exception as e:
        flash('Error updating income.', 'danger')

    return redirect(url_for('incomes.index'))

@incomes_bp.route('/income/delete/<int:income_id>', methods=['POST'])
@login_required
def delete(income_id):
    user_id = session['user_id']
    try:
        rows = execute_db("DELETE FROM incomes WHERE id = %s AND user_id = %s", (income_id, user_id))
        if rows:
            flash('Income deleted successfully.', 'info')
        else:
            flash('Income not found or unauthorized.', 'warning')
    except Exception as e:
        flash('Error deleting income.', 'danger')

    return redirect(url_for('incomes.index'))
