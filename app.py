from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['forms_db']
users_col = db['users']

# ─── Helpers ───────────────────────────────────────────────────────────────

def get_user_by_email(email):
    return users_col.find_one({'email': {'$regex': f'^{email}$', '$options': 'i'}})

def get_user_by_id(user_id):
    try:
        return users_col.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None

def email_in_use(email, exclude_id=None):
    query = {'email': {'$regex': f'^{email}$', '$options': 'i'}}
    if exclude_id:
        query['_id'] = {'$ne': ObjectId(exclude_id)}
    return users_col.find_one(query) is not None

# ─── Routes ────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Show registration form; on POST, validate & save new user."""
    if request.method == 'POST':
        name  = request.form['name'].strip()
        email = request.form['email'].strip()

        # 1) Basic validation
        if not name or not email or '@' not in email:
            flash('Please enter a valid name and email.', 'danger')
            return redirect(url_for('register'))

        if get_user_by_email(email):
            flash('Email already registered!', 'warning')
            return redirect(url_for('register'))

        # 3) Assign ID, save, then redirect to profile
        user = {'name': name, 'email': email}
        result = users_col.insert_one(user)
        user_id = str(result.inserted_id)

        flash('Registration successful!', 'success')
        return redirect(url_for('profile', user_id=user_id))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO: Add login logic here (check email and password, set session, etc.)
        pass
    return render_template('login.html')

@app.route('/profile/<user_id>')
def profile(user_id):
    """Show a user's profile or redirect if not found."""
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('register'))
    # Convert _id to string for template
    user['id'] = str(user['_id'])
    return render_template('profile.html', user=user)


@app.route('/update/<user_id>', methods=['GET', 'POST'])
def update(user_id):
    """Preload form with existing data; validate & save updates."""
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        name  = request.form['name'].strip()
        email = request.form['email'].strip()

        # 1) Field validation
        if not name or not email or '@' not in email:
            flash('Please enter valid details.', 'danger')
            return redirect(url_for('update', user_id=user_id))

        # 2) Email-conflict check against OTHER users
        if email_in_use(email, user_id):
            flash('Email already in use by another user.', 'warning')
            return redirect(url_for('update', user_id=user_id))

        # 3) Commit changes
        users_col.update_one({'_id': ObjectId(user_id)}, {'$set': {'name': name, 'email': email}})
        flash('Profile updated successfully!', 'info')
        return redirect(url_for('profile', user_id=user_id))

    # GET request → show form with current values
    user['id'] = str(user['_id'])
    return render_template('updates.html', user=user)


# ─── Entry Point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Enables flask run via python app.py
    app.run(debug=True, use_reloader=False)
