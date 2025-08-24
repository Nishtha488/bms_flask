from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
import mysql.connector
from mysql.connector import Error
import secrets
import re

app = Flask(__name__)
# Generate a secure random secret key
app.secret_key = secrets.token_hex(16)

# Helper function to validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        if not all([username, password, full_name, email]):
            flash('Please fill all fields!', 'error')
            return render_template('register.html')
        
        if len(username) < 4:
            flash('Username must be at least 4 characters long!', 'error')
            return render_template('register.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
            
        if not is_valid_email(email):
            flash('Please enter a valid email address!', 'error')
            return render_template('register.html')
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if conn is None:
                flash('Database connection error. Please try again later.', 'error')
                return render_template('register.html')
                
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists!', 'error')
                return render_template('register.html')
            
            # Check if email already exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered!', 'error')
                return render_template('register.html')
            
            # Insert new user
            cursor.execute(
                "INSERT INTO users (username, password, full_name, email) VALUES (%s, %s, %s, %s)",
                (username, password, full_name, email)
            )
            conn.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Error as err:
            flash(f'Database error: {err}', 'error')
            return render_template('register.html')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password!', 'error')
            return render_template('login.html')
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if conn is None:
                flash('Database connection error. Please try again later.', 'error')
                return render_template('login.html')
                
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
                return render_template('login.html')
                
        except Error as err:
            flash(f'Database error: {err}', 'error')
            return render_template('login.html')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('index'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user accounts
        cursor.execute(
            "SELECT * FROM accounts WHERE user_id = %s",
            (session['user_id'],)
        )
        accounts = cursor.fetchall()
        
        # Get total balance
        total_balance = sum(account['balance'] for account in accounts) if accounts else 0
        
    except Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
    return render_template('dashboard.html', 
                          full_name=session['full_name'], 
                          accounts=accounts, 
                          total_balance=total_balance)

# Accounts page
@app.route('/accounts')
def accounts():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('dashboard'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user accounts
        cursor.execute(
            "SELECT * FROM accounts WHERE user_id = %s",
            (session['user_id'],)
        )
        accounts = cursor.fetchall()
        
    except Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
    return render_template('accounts.html', accounts=accounts)

# Create new account
@app.route('/create_account', methods=['POST'])
def create_account():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    account_type = request.form.get('account_type', 'Savings')
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('accounts'))
            
        cursor = conn.cursor()
        
        # Generate account number (simple implementation)
        cursor.execute("SELECT COUNT(*) as count FROM accounts")
        count_result = cursor.fetchone()
        count = count_result[0] if count_result else 0
        account_number = f"ACC{10000 + count + 1}"
        
        # Create new account
        cursor.execute(
            "INSERT INTO accounts (user_id, account_number, account_type) VALUES (%s, %s, %s)",
            (session['user_id'], account_number, account_type)
        )
        conn.commit()
        
        flash(f'Account {account_number} created successfully!', 'success')
        
    except Error as err:
        flash(f'Database error: {err}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
    return redirect(url_for('accounts'))

# Transactions page
@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    account_id = request.args.get('account_id')
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('dashboard'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Get user accounts for dropdown
        cursor.execute(
            "SELECT * FROM accounts WHERE user_id = %s",
            (session['user_id'],)
        )
        accounts = cursor.fetchall()
        
        transactions = []
        if account_id:
            # Verify the account belongs to the user
            cursor.execute(
                "SELECT * FROM accounts WHERE id = %s AND user_id = %s",
                (account_id, session['user_id'])
            )
            account = cursor.fetchone()
            
            if account:
                # Get transactions for the account
                cursor.execute(
                    "SELECT * FROM transactions WHERE account_id = %s ORDER BY transaction_date DESC",
                    (account_id,)
                )
                transactions = cursor.fetchall()
            else:
                flash('Account not found or access denied.', 'error')
        
    except Error as err:
        flash(f'Database error: {err}', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
    return render_template('transactions.html', 
                          accounts=accounts, 
                          transactions=transactions,
                          selected_account=account_id)

# Perform transaction (deposit/withdraw)
@app.route('/perform_transaction', methods=['POST'])
def perform_transaction():
    if 'user_id' not in session:
        flash('Please login to access this page.', 'error')
        return redirect(url_for('login'))
    
    account_id = request.form.get('account_id')
    transaction_type = request.form.get('transaction_type')
    amount_str = request.form.get('amount', '')
    description = request.form.get('description', '').strip()
    
    # Validation
    if not account_id or not transaction_type or not amount_str:
        flash('Missing required fields!', 'error')
        return redirect(url_for('transactions'))
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            flash('Amount must be greater than zero!', 'error')
            return redirect(url_for('transactions'))
    except ValueError:
        flash('Invalid amount!', 'error')
        return redirect(url_for('transactions'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if conn is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('transactions'))
            
        cursor = conn.cursor(dictionary=True)
        
        # Verify the account belongs to the user
        cursor.execute(
            "SELECT * FROM accounts WHERE id = %s AND user_id = %s",
            (account_id, session['user_id'])
        )
        account = cursor.fetchone()
        
        if not account:
            flash('Account not found or access denied!', 'error')
            return redirect(url_for('transactions'))
        
        # Check if withdrawal amount is available
        if transaction_type == 'withdraw' and account['balance'] < amount:
            flash('Insufficient balance!', 'error')
            return redirect(url_for('transactions'))
        
        # Update account balance
        new_balance = account['balance'] + amount if transaction_type == 'deposit' else account['balance'] - amount
        cursor.execute(
            "UPDATE accounts SET balance = %s WHERE id = %s",
            (new_balance, account_id)
        )
        
        # Record transaction
        cursor.execute(
            "INSERT INTO transactions (account_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s)",
            (account_id, transaction_type, amount, description)
        )
        
        conn.commit()
        flash('Transaction completed successfully!', 'success')
        
    except Error as err:
        flash(f'Database error: {err}', 'error')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
    return redirect(url_for('transactions') + f'?account_id={account_id}')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)