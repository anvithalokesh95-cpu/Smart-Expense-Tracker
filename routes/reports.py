import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, Response, session
from database import query_db
from routes import login_required

reports_bp = Blueprint('reports', __name__)

def fetch_filtered_records(user_id, start_date=None, end_date=None, category_id=None, tx_type='all'):
    """
    Helper function to query combined expenses and income records with filtering.
    """
    records = []

    # 1. Fetch Expenses if tx_type in ('all', 'expense')
    if tx_type in ('all', 'expense'):
        sql = """
            SELECT e.id, 'Expense' AS type, e.expense_date AS tx_date,
                   c.name AS category_source, e.payment_method, e.amount, e.description,
                   c.icon, c.color
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = %s
        """
        params = [user_id]
        if start_date:
            sql += " AND e.expense_date >= %s"
            params.append(start_date)
        if end_date:
            sql += " AND e.expense_date <= %s"
            params.append(end_date)
        if category_id and category_id.isdigit():
            sql += " AND e.category_id = %s"
            params.append(int(category_id))

        sql += " ORDER BY e.expense_date DESC"
        expenses = query_db(sql, tuple(params))
        records.extend(expenses)

    # 2. Fetch Incomes if tx_type in ('all', 'income')
    if tx_type in ('all', 'income'):
        # Incomes don't have categories, only if category_id is NOT specified
        if not category_id or not category_id.isdigit():
            sql = """
                SELECT id, 'Income' AS type, income_date AS tx_date,
                       source AS category_source, 'Bank / Cash' AS payment_method,
                       amount, description, 'wallet' AS icon, '#10B981' AS color
                FROM incomes
                WHERE user_id = %s
            """
            params = [user_id]
            if start_date:
                sql += " AND income_date >= %s"
                params.append(start_date)
            if end_date:
                sql += " AND income_date <= %s"
                params.append(end_date)

            sql += " ORDER BY income_date DESC"
            incomes = query_db(sql, tuple(params))
            records.extend(incomes)

    # Sort combined records by date descending
    records.sort(key=lambda x: x['tx_date'], reverse=True)
    return records

@reports_bp.route('/reports')
@login_required
def index():
    user_id = session['user_id']
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    category_id = request.args.get('category_id', '').strip()
    tx_type = request.args.get('type', 'all').strip()

    records = fetch_filtered_records(user_id, start_date, end_date, category_id, tx_type)

    total_expense = sum(float(r['amount']) for r in records if r['type'] == 'Expense')
    total_income = sum(float(r['amount']) for r in records if r['type'] == 'Income')
    net_savings = total_income - total_expense

    categories = query_db("""
        SELECT id, name FROM categories
        WHERE type = 'expense' AND (user_id IS NULL OR user_id = %s)
        ORDER BY name ASC
    """, (user_id,))

    return render_template(
        'reports.html',
        records=records,
        total_expense=total_expense,
        total_income=total_income,
        net_savings=net_savings,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        tx_type=tx_type
    )

@reports_bp.route('/reports/export')
@login_required
def export_csv():
    user_id = session['user_id']
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    category_id = request.args.get('category_id', '').strip()
    tx_type = request.args.get('type', 'all').strip()

    records = fetch_filtered_records(user_id, start_date, end_date, category_id, tx_type)

    # Create CSV in memory
    si = io.StringIO()
    writer = csv.writer(si)

    # Write CSV Header
    writer.writerow(['Date', 'Type', 'Category / Source', 'Amount', 'Payment Method', 'Description'])

    for r in records:
        writer.writerow([
            r['tx_date'].strftime('%Y-%m-%d') if hasattr(r['tx_date'], 'strftime') else str(r['tx_date']),
            r['type'],
            r['category_source'],
            f"{float(r['amount']):.2f}",
            r.get('payment_method', 'N/A'),
            r.get('description', '') or ''
        ])

    output = si.getvalue()
    filename = f"expense_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
