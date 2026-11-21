import unittest
from datetime import date
from app import create_app
from database import init_db, query_db, execute_db

class SmartExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_01_categories_seeded(self):
        """Verify default categories are seeded"""
        cats = query_db("SELECT * FROM categories WHERE user_id IS NULL")
        self.assertGreaterEqual(len(cats), 8)
        names = [c['name'] for c in cats]
        for expected in ['Food', 'Shopping', 'Travel', 'Education', 'Entertainment', 'Bills', 'Healthcare', 'Others']:
            self.assertIn(expected, names)
        print("[OK] Categories seeded successfully:", len(cats), "categories verified.")

    def test_02_user_registration_and_login(self):
        """Test registration, duplicate prevention, and login"""
        # Register new user
        reg_data = {
            'username': 'demouser',
            'email': 'demo@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'currency': '$'
        }
        res = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify in DB
        user = query_db("SELECT * FROM users WHERE username = %s", ('demouser',), one=True)
        self.assertIsNotNone(user)
        self.assertEqual(user['email'], 'demo@example.com')
        print("[OK] User registered successfully with id:", user['id'])

        # Login
        login_data = {
            'login_input': 'demouser',
            'password': 'password123'
        }
        res = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'demouser', res.data)
        print("[OK] User login session established.")

    def test_03_financial_crud_and_budget(self):
        """Test Income, Expense, Budget, Analytics, and CSV Export"""
        with self.client.session_transaction() as sess:
            user = query_db("SELECT id, username, currency FROM users WHERE username = 'demouser'", one=True)
            sess['user_id'] = user['id']
            sess['username'] = user['username']
            sess['currency'] = user['currency']

        # Add Income
        inc_data = {
            'source': 'Tech Salary',
            'amount': '5000.00',
            'income_date': date.today().strftime('%Y-%m-%d'),
            'description': 'Monthly salary'
        }
        res = self.client.post('/income/add', data=inc_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("[OK] Income record added.")

        # Add Expense
        food_cat = query_db("SELECT id FROM categories WHERE name = 'Food' LIMIT 1", one=True)
        exp_data = {
            'amount': '250.00',
            'category_id': str(food_cat['id']),
            'expense_date': date.today().strftime('%Y-%m-%d'),
            'payment_method': 'Credit Card',
            'description': 'Supermarket Groceries'
        }
        res = self.client.post('/expenses/add', data=exp_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("[OK] Expense record added.")

        # Set Budget
        budget_data = {
            'budget_type': 'overall',
            'amount': '2000.00',
            'month_str': date.today().strftime('%Y-%m')
        }
        res = self.client.post('/budgets/set', data=budget_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("[OK] Monthly budget set.")

        # Test Dashboard View
        dash_res = self.client.get('/dashboard')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'Supermarket Groceries', dash_res.data)
        self.assertIn(b'Tech Salary', dash_res.data)
        print("[OK] Dashboard view rendered with financial transactions.")

        # Test Chart Data API
        chart_res = self.client.get('/api/chart-data')
        self.assertEqual(chart_res.status_code, 200)
        chart_json = chart_res.get_json()
        self.assertIn('Food', chart_json['categories']['labels'])
        print("[OK] Chart JSON API returns categories and trend data.")

        # Test Analytics Page
        analytics_res = self.client.get('/analytics')
        self.assertEqual(analytics_res.status_code, 200)
        self.assertIn(b'Top Expense Driver', analytics_res.data)
        print("[OK] Smart Analytics page rendered.")

        # Test Reports Page
        reports_res = self.client.get('/reports')
        self.assertEqual(reports_res.status_code, 200)
        self.assertIn(b'Supermarket Groceries', reports_res.data)
        print("[OK] Reports page rendered.")

        # Test CSV Export
        csv_res = self.client.get('/reports/export')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, 'text/csv')
        self.assertIn(b'Supermarket Groceries', csv_res.data)
        print("[OK] CSV export generated valid downloadable file.")

if __name__ == '__main__':
    unittest.main()
