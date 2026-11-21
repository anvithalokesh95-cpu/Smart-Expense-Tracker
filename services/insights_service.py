from datetime import datetime, date
from database import query_db

def generate_smart_insights(user_id):
    """
    Analyzes user financial transactions and generates dynamic insights,
    spending trends, highest categories, and actionable saving suggestions.
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    days_in_month = 30 # standard approximation
    day_of_month = now.day

    # 1. Total Current Month Expenses
    cur_exp_res = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s AND YEAR(expense_date) = %s AND MONTH(expense_date) = %s
    """, (user_id, current_year, current_month), one=True)
    current_expenses = float(cur_exp_res['total']) if cur_exp_res else 0.0

    # 2. Total Current Month Income
    cur_inc_res = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM incomes
        WHERE user_id = %s AND YEAR(income_date) = %s AND MONTH(income_date) = %s
    """, (user_id, current_year, current_month), one=True)
    current_income = float(cur_inc_res['total']) if cur_inc_res else 0.0

    # 3. Previous Month Expenses & Income for Comparison
    prev_month = 12 if current_month == 1 else current_month - 1
    prev_year = current_year - 1 if current_month == 1 else current_year

    prev_exp_res = query_db("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s AND YEAR(expense_date) = %s AND MONTH(expense_date) = %s
    """, (user_id, prev_year, prev_month), one=True)
    prev_expenses = float(prev_exp_res['total']) if prev_exp_res else 0.0

    # 4. Spending change percentage
    if prev_expenses > 0:
        spending_change_pct = round(((current_expenses - prev_expenses) / prev_expenses) * 100, 1)
    else:
        spending_change_pct = 0.0

    # 5. Highest Expense Category (Current Month)
    top_cat = query_db("""
        SELECT c.name, c.icon, c.color, COALESCE(SUM(e.amount), 0) AS total_amount
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = %s AND YEAR(e.expense_date) = %s AND MONTH(e.expense_date) = %s
        GROUP BY c.id, c.name, c.icon, c.color
        ORDER BY total_amount DESC
        LIMIT 1
    """, (user_id, current_year, current_month), one=True)

    top_category_info = None
    if top_cat and top_cat['total_amount'] > 0:
        top_cat_amount = float(top_cat['total_amount'])
        top_cat_pct = round((top_cat_amount / current_expenses) * 100, 1) if current_expenses > 0 else 0
        top_category_info = {
            'name': top_cat['name'],
            'icon': top_cat['icon'],
            'color': top_cat['color'],
            'amount': top_cat_amount,
            'percentage': top_cat_pct
        }

    # 6. Savings Rate calculation
    net_savings = current_income - current_expenses
    savings_rate = round((net_savings / current_income * 100), 1) if current_income > 0 else 0.0

    # 7. Overall Monthly Budget Check
    budget_res = query_db("""
        SELECT amount FROM budgets
        WHERE user_id = %s AND category_id IS NULL AND month = %s AND year = %s
    """, (user_id, current_month, current_year), one=True)
    monthly_budget = float(budget_res['amount']) if budget_res else None

    budget_used_pct = None
    if monthly_budget and monthly_budget > 0:
        budget_used_pct = round((current_expenses / monthly_budget) * 100, 1)

    # 8. Generate dynamic suggestions and insights
    suggestions = []

    # Check budget health
    if monthly_budget and monthly_budget > 0:
        if budget_used_pct >= 100:
            suggestions.append({
                'type': 'danger',
                'icon': 'alert-triangle',
                'title': 'Budget Exceeded!',
                'message': f"You've exceeded your monthly budget of ${monthly_budget:,.2f} by ${current_expenses - monthly_budget:,.2f} ({budget_used_pct}%). Consider halting non-essential purchases."
            })
        elif budget_used_pct >= 80:
            suggestions.append({
                'type': 'warning',
                'icon': 'alert-circle',
                'title': 'Approaching Budget Limit',
                'message': f"You have utilized {budget_used_pct}% of your monthly budget with {max(0, 30 - day_of_month)} days left in the month."
            })
        elif budget_used_pct < 60 and day_of_month > 20:
            suggestions.append({
                'type': 'success',
                'icon': 'check-circle-2',
                'title': 'Excellent Budget Control',
                'message': f"You have only used {budget_used_pct}% of your monthly budget near the end of the month. Great financial discipline!"
            })

    # Savings rate suggestions
    if current_income > 0:
        if savings_rate >= 30:
            suggestions.append({
                'type': 'success',
                'icon': 'trending-up',
                'title': f'Superb Savings Rate ({savings_rate}%)',
                'message': 'You are well above the recommended 20% savings rule! Consider allocating surplus to high-yield savings or investments.'
            })
        elif savings_rate < 10 and current_expenses > 0:
            suggestions.append({
                'type': 'warning',
                'icon': 'shield-alert',
                'title': 'Low Savings Rate',
                'message': f'Your savings rate is currently {savings_rate}%. Try adopting the 50/30/20 rule (50% Needs, 30% Wants, 20% Savings).'
            })

    # Month over month trend advice
    if prev_expenses > 0 and spending_change_pct > 20:
        suggestions.append({
            'type': 'info',
            'icon': 'arrow-up-right',
            'title': f'Spending Increased by {spending_change_pct}%',
            'message': f'You have spent {spending_change_pct}% more compared to last month (${current_expenses:,.2f} vs ${prev_expenses:,.2f}). Review non-essential categories.'
        })
    elif prev_expenses > 0 and spending_change_pct < -15:
        suggestions.append({
            'type': 'success',
            'icon': 'arrow-down-right',
            'title': f'Spending Decreased by {abs(spending_change_pct)}%',
            'message': f'Awesome! You cut your expenses by {abs(spending_change_pct)}% compared to last month.'
        })

    # Top category specific recommendations
    if top_category_info:
        cat_name = top_category_info['name'].lower()
        if 'food' in cat_name and top_category_info['percentage'] > 30:
            suggestions.append({
                'type': 'info',
                'icon': 'utensils',
                'title': 'High Dining & Food Expenditure',
                'message': f"Food represents {top_category_info['percentage']}% (${top_category_info['amount']:,.2f}) of your monthly spend. Meal prepping or cutting takeouts twice a week could save 15-20%."
            })
        elif 'shopping' in cat_name and top_category_info['percentage'] > 25:
            suggestions.append({
                'type': 'info',
                'icon': 'shopping-bag',
                'title': 'Shopping Spree Detected',
                'message': f"Shopping accounts for {top_category_info['percentage']}% of your expenses. Try using the '48-Hour Rule' before making impulsive purchases."
            })
        elif 'entertainment' in cat_name and top_category_info['percentage'] > 20:
            suggestions.append({
                'type': 'info',
                'icon': 'film',
                'title': 'Subscription & Entertainment Review',
                'message': f"Entertainment takes {top_category_info['percentage']}% of your budget. Review recurring streaming subscriptions and cancel unused ones."
            })

    # Fallback suggestion if new or no warnings
    if not suggestions:
        suggestions.append({
            'type': 'info',
            'icon': 'lightbulb',
            'title': 'Smart Financial Tip',
            'message': 'Keep logging your transactions daily. Consistent tracking is the single most effective habit to reach financial freedom!'
        })

    return {
        'current_expenses': current_expenses,
        'current_income': current_income,
        'prev_expenses': prev_expenses,
        'spending_change_pct': spending_change_pct,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'top_category': top_category_info,
        'monthly_budget': monthly_budget,
        'budget_used_pct': budget_used_pct,
        'suggestions': suggestions
    }
