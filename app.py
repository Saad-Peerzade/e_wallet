import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = '123456789'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/e_wallet'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Directory for profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize MongoDB
mongo = PyMongo(app)

def allowed_file(filename):
    """Check if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        prn = request.form['prn']

        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'prn': prn,
            'balance': 0,
            'profile_pic': 'default.png'
        })

        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = mongo.db.users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session['user_email'] = email
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "error")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'email': session['user_email']})
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user = mongo.db.users.find_one({'email': session['user_email']})

    if request.method == 'POST':
        update_data = {}
        fields = ['name', 'prn', 'mobile', 'gmail', 'upi', 'department', 'dob', 'course', 'gender', 'blood_group']
        
        # Update text fields
        for field in fields:
            new_value = request.form.get(field)
            if new_value:  
                update_data[field] = new_value

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)  # Save file to static/uploads/
                update_data['profile_pic'] = filename

        # Update database if any changes were made
        if update_data:
            mongo.db.users.update_one({'email': session['user_email']}, {'$set': update_data})
            flash("Profile updated successfully!", "success")

        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    email = session['user_email'].strip().lower()
    user = mongo.db.users.find_one({'email': email})

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            amount = int(request.form['amount'])
            if amount <= 0:
                flash("Invalid amount. Enter a positive number.", "error")
                return redirect(url_for('deposit'))

            # Update balance
            new_balance = user.get('balance', 0) + amount
            mongo.db.users.update_one({'email': email}, {'$set': {'balance': new_balance}})

            # Log transaction
            mongo.db.transactions.insert_one({
                "user_email": email,
                "type": "deposit",
                "amount": amount,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            flash(f"Deposit successful! 🍊 New Balance: {new_balance}", "success")
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        except ValueError:
            flash("Invalid input. Enter a valid number.", "error")
            return redirect(url_for('deposit'))

    return render_template('deposit.html', user=user)

    # if 'user' not in session:
    #     return redirect(url_for('login'))

    # email = session['user'].strip().lower()
    # user = mongo.db.users.find_one({'email': email})

    # if not user:
    #     flash("User not found!", "error")
    #     return redirect(url_for('login'))

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             flash("Invalid amount. Enter a positive number.", "error")
    #             return redirect(url_for('deposit'))

    #         # ✅ Update balance
    #         new_balance = user.get('balance', 0) + amount
    #         mongo.db.users.update_one({'email': email}, {'$set': {'balance': new_balance}})

    #         # ✅ Log transaction
    #         mongo.db.transactions.insert_one({
    #             "user_email": email,
    #             "type": "deposit",
    #             "amount": amount,
    #             "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         })

    #         flash(f"Oranges deposited successfully! 🍊 New Balance: {new_balance}", "success")
    #         return redirect(url_for('deposit'))  # Stay on deposit page
    #     except ValueError:
    #         flash("Invalid input. Enter a valid number.", "error")
    #         return redirect(url_for('deposit'))

    # return render_template('deposit.html', user=user)


    # if 'user' not in session:
    #     return redirect(url_for('login'))

    # email = session['user'].strip().lower()
    # user = mongo.db.users.find_one({'email': email})  

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             flash("❌ Invalid amount! Please enter a positive number.", "error")
    #             return redirect(url_for('deposit'))  

    #         current_balance = user.get('balance', 0)  
    #         new_balance = current_balance + amount  

    #         result = mongo.db.users.update_one(
    #             {'email': email}, 
    #             {'$set': {'balance': new_balance}}
    #         )

    #         if result.modified_count > 0:
    #             flash(f"✅ Successfully deposited {amount} 🍊 Oranges!", "success")
    #         else:
    #             flash("⚠️ Deposit failed! Try again.", "error")

    #         return redirect(url_for('dashboard'))  
    #     except ValueError:
    #         flash("❌ Invalid input! Please enter a valid number.", "error")
    #         return redirect(url_for('deposit'))  

    # return render_template('deposit.html', user=user)

    # if 'user' not in session:
    #     return redirect(url_for('login'))

    # user = mongo.db.users.find_one({'email': session['user']})  
    # print(f"Before Deposit: {user}")  # Debugging: Check user before deposit

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             return "Invalid amount. Please enter a positive number.", 400  
            
    #         # Ensure user has a balance field
    #         current_balance = user.get('balance', 0)
    #         new_balance = current_balance + amount  

    #         # 🔥 Fix: Normalize email before updating
    #         email = session['user'].strip().lower()
    #         result = mongo.db.users.update_one(
    #             {'email': email}, 
    #             {'$set': {'balance': new_balance}}
    #         )
            
    #         print(f"MongoDB Update Result: {result.matched_count} matched, {result.modified_count} modified")
    #         print(f"After Deposit: {mongo.db.users.find_one({'email': email})}")  

    #         return redirect(url_for('dashboard'))  
    #     except ValueError:
    #         return "Invalid input. Please enter a valid number.", 400  

    # return render_template('deposit.html', user=user)

    # if 'user' not in session:
    #     return redirect(url_for('login'))

    # user = mongo.db.users.find_one({'email': session['user']})  
    # print(f"Before Deposit: {user}")  # Debugging: Check user before deposit

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             return "Invalid amount. Please enter a positive number.", 400  
            
    #         # Ensure user has a balance field
    #         current_balance = user.get('balance', 0)
    #         new_balance = current_balance + amount  

    #         # 🔥 Fix: Ensure update_one uses `$set`
    #         result = mongo.db.users.update_one(
    #             {'email': session['user']}, 
    #             {'$set': {'balance': new_balance}}
    #         )
            
    #         print(f"MongoDB Update Result: {result.matched_count} matched, {result.modified_count} modified")
    #         print(f"After Deposit: {mongo.db.users.find_one({'email': session['user']})}")  

    #         return redirect(url_for('dashboard'))  
    #     except ValueError:
    #         return "Invalid input. Please enter a valid number.", 400  

    # return render_template('deposit.html', user=user)

    # if 'user' not in session:
    #     return redirect(url_for('login'))

    # user = mongo.db.users.find_one({'email': session['user']})  # Fetch user details
    # print(f"Before Deposit: {user}")  # Debugging: See user data before deposit

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             return "Invalid amount. Please enter a positive number.", 400  # Handle invalid amounts
            
    #         # Ensure user has a balance field
    #         current_balance = user.get('balance', 0)
    #         new_balance = current_balance + amount  # Update balance
            
    #         # Update balance in MongoDB
    #         mongo.db.users.update_one(
    #             {'email': session['user']}, 
    #             {'$set': {'balance': new_balance}}
    #         )

    #         print(f"After Deposit: {mongo.db.users.find_one({'email': session['user']})}")  # Debugging

    #         return redirect(url_for('dashboard'))  # Redirect after deposit
    #     except ValueError:
    #         return "Invalid input. Please enter a valid number.", 400  # Handle non-numeric input

    # return render_template('deposit.html', user=user)

    # if 'user' not in session:  # Ensure user is logged in
    #     return redirect(url_for('login'))

    # user = mongo.db.users.find_one({'email': session['user']})  # Fetch user by email

    # if request.method == 'POST':
    #     try:
    #         amount = int(request.form['amount'])
    #         if amount <= 0:
    #             return "Invalid amount. Please enter a positive number.", 400  # Handle invalid amounts

    #         mongo.db.users.update_one(
    #             {'email': session['user']}, 
    #             {'$inc': {'balance': amount}}  # Increment user's balance
    #         )

    #         return redirect(url_for('dashboard'))  # Redirect after successful deposit
    #     except ValueError:
    #         return "Invalid input. Please enter a valid number.", 400  # Handle non-numeric input

    # return render_template('deposit.html', user=user)  # Render deposit form
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_email' not in session:  # ✅ Standardized session key
        return redirect(url_for('login'))

    email = session['user_email']
    user = mongo.db.users.find_one({'email': email})

    if not user:
        flash("User not found!", "error")
        return redirect(url_for('dashboard'))

    current_balance = user.get('balance', 0)

    if request.method == 'POST':
        try:
            amount = int(request.form['amount'])
            if amount <= 0:
                flash("Invalid amount. Enter a positive number.", "error")
                return redirect(url_for('withdraw'))

            if amount > current_balance:
                flash("Insufficient balance! 🚫", "error")
                return redirect(url_for('withdraw'))

            # ✅ Update balance
            new_balance = current_balance - amount
            mongo.db.users.update_one({'email': email}, {'$set': {'balance': new_balance}})

            # ✅ Log transaction
            mongo.db.transactions.insert_one({
                "user_email": email,
                "type": "Withdraw",
                "amount": amount,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            flash(f"Withdrawal successful! 🍊 Amount Withdrawn: {amount}. New Balance: {new_balance}", "success")
            return redirect(url_for('withdraw'))  # Stay on withdraw page
        except ValueError:
            flash("Invalid input. Enter a valid number.", "error")
            return redirect(url_for('withdraw'))

    return render_template('withdraw.html', user=user, balance=current_balance)


@app.route('/transactions')
def transactions():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    transactions = list(mongo.db.transactions.find({'user_email': user_email}))  
    
    return render_template('history.html', transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True)
