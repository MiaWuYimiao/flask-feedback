from flask import Flask, redirect, render_template, session, flash, url_for
from flask_debugtoolbar import DebugToolbarExtension
from models import User, connect_db, db, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///user_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "12345"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/register', methods=["GET", "POST"])
def register_page():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another')
            return render_template('user_create_form.html', form=form)
        session['username'] = new_user.username
        flash(f"{new_user.username} added.")
        return redirect(url_for('user_detail_page', username=new_user.username))
    
    else:
        return render_template("user_create_form.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome back, {user.username}!", "primary")
            session['username'] = user.username
            return redirect(url_for('user_detail_page', username = user.username))
        else:
            form.username.errors = ['Invalid username/password.']
    
    return render_template("user_login_form.html", form=form)


@app.route('/logout')
def logout_user():
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')


@app.route('/users/<username>')
def user_detail_page(username):
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login_page'))

    user = User.query.get_or_404(username)
    return render_template("user_detail.html", user=user)

@app.route('/users/<username>/delete')
def delete_user(username):
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login_page'))

    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()

    return redirect('/')


# Feedback routes
@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login_page'))

    form = FeedbackForm()
    if form.validate_on_submit():
        new_feedback = Feedback(title=form.title.data, content=form.content.data, username=username)

        db.session.add(new_feedback)
        db.session.commit()

        flash(f"New feedback added.", "info")
        return redirect(url_for('user_detail_page', username=username))
    
    else:
        return render_template("add_feedback_form.html", form=form, username=username)


@app.route('/feedback/<int:feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):
    # Check1 -- Is there a login user?
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login_page'))

    # Check2 -- Is the user try to edit his/her own feedback?
    feedback = Feedback.query.get_or_404(feedback_id)
    username = session['username']
    if feedback.username != username:
        flash(f"You can not edit others feedback.", "danger")
        return redirect(url_for('home_page'))

    # Once two checks passed, we can render edit form or submit edit form
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        flash(f"Feedback {feedback.title} updated.", "info")
        return redirect(url_for('user_detail_page', username = username))
    
    return render_template("update_feedback_form.html", form=form)


@app.route('/feedback/<int:feedback_id>/delete', methods=["POST"])
def delete_feedback(feedback_id):
    
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for('login_page'))

    feedback = Feedback.query.get_or_404(feedback_id)
    username = session['username']
    if feedback.username == username:
        db.session.delete(feedback)
        db.session.commit()
        flash(f"Feedback {feedback.title} deleted.", "info")
    else: 
        flash(f"You can not delete others feedback.", "danger")

    return redirect(url_for('user_detail_page', username = username))
