/**
 * SMART EXPENSE TRACKER - MAIN FRONTEND SCRIPTS
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // 2. Mobile Sidebar Navigation Toggle
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');

    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 900 && sidebar.classList.contains('open')) {
                if (!sidebar.contains(e.target) && e.target !== mobileToggle) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // 3. Auto dismiss Flash Toasts after 5 seconds
    const toasts = document.querySelectorAll('.flash-toast');
    toasts.forEach((toast) => {
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, 5000);
    });

    // 4. Modal Backdrop Close Handlers
    document.querySelectorAll('.modal-overlay').forEach((modal) => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });

    // 5. Budget Type Toggle (Overall vs Category) in Budget Modal
    const budgetTypeSelect = document.getElementById('budget_type_select');
    const categorySelectGroup = document.getElementById('budget_category_group');
    if (budgetTypeSelect && categorySelectGroup) {
        budgetTypeSelect.addEventListener('change', () => {
            if (budgetTypeSelect.value === 'category') {
                categorySelectGroup.style.display = 'block';
            } else {
                categorySelectGroup.style.display = 'none';
            }
        });
    }
});

// Helper: Open Modal by ID
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

// Helper: Close Modal by ID
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Helper: Edit Expense Modal dynamic fetch
async function openEditExpenseModal(expenseId) {
    try {
        const response = await fetch(`/api/expenses/${expenseId}`);
        if (!response.ok) throw new Error('Could not fetch expense details');
        const data = await response.json();

        // Populate fields
        const form = document.getElementById('edit-expense-form');
        form.action = `/expenses/edit/${expenseId}`;
        
        document.getElementById('edit_expense_amount').value = data.amount;
        document.getElementById('edit_expense_category').value = data.category_id;
        document.getElementById('edit_expense_date').value = data.expense_date;
        document.getElementById('edit_expense_payment').value = data.payment_method;
        document.getElementById('edit_expense_description').value = data.description || '';

        openModal('modal-edit-expense');
    } catch (err) {
        alert('Failed to load expense data: ' + err.message);
    }
}

// Helper: Edit Income Modal dynamic fetch
async function openEditIncomeModal(incomeId) {
    try {
        const response = await fetch(`/api/income/${incomeId}`);
        if (!response.ok) throw new Error('Could not fetch income details');
        const data = await response.json();

        const form = document.getElementById('edit-income-form');
        form.action = `/income/edit/${incomeId}`;

        document.getElementById('edit_income_source').value = data.source;
        document.getElementById('edit_income_amount').value = data.amount;
        document.getElementById('edit_income_date').value = data.income_date;
        document.getElementById('edit_income_description').value = data.description || '';

        openModal('modal-edit-income');
    } catch (err) {
        alert('Failed to load income data: ' + err.message);
    }
}

// Helper: Confirmation before deletion
function confirmDelete(message = 'Are you sure you want to delete this record?') {
    return confirm(message);
}
