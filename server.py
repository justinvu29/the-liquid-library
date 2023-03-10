from flask import (Flask, render_template, request, flash, session, url_for, redirect)
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from forms import LoginForm, RegisterForm
import requests
from model import connect_to_db, db, User, FavoriteCocktail
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)

app.config['SECRET_KEY'] = 'secret-key'
app.config['LOGIN_VIEW'] = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email address already exists.")
            return redirect(url_for("register"))

        new_user = User(email=email, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully.")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("homepage"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))

@app.route('/')
def homepage():
    if 'GO' in request.args:
        name = request.args.get('search').strip()
        url = f'https://www.thecocktaildb.com/api/json/v1/1/search.php?s={name}'
        res = requests.get(url)
        res = res.json()
        if not res['drinks']:
            return render_template('notfound.html')
        cocktail = res['drinks'][0]
        return render_template('home.html', cocktail=cocktail)
    elif 'Random' in request.args:
        url = 'https://www.thecocktaildb.com/api/json/v1/1/random.php'
        res = requests.get(url)
        res = res.json()
        cocktail = res['drinks'][0]
        return render_template('home.html', cocktail=cocktail)
    else:
        return render_template('search.html')

@app.route('/notfound')
def notfound():
    return render_template('notfound.html')


@app.route('/add_favorite', methods=['POST'])
@login_required
def add_favorite():
    user_id = current_user.id
    cocktail_id = request.form['cocktail_id']
    favorite = FavoriteCocktail(user_id=user_id, cocktail_id=cocktail_id)
    db.session.add(favorite)
    db.session.commit()
    flash('Cocktail added to favorites!')
    return redirect(request.referrer)

@app.route('/favorites')
@login_required
def favorites():
    user_id = current_user.id
    favorites = FavoriteCocktail.query.filter_by(user_id=user_id).all()
    cocktail_data = []

    for fav in favorites:
        response = requests.get(f"https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i={fav.cocktail_id}")
        data = response.json()['drinks'][0]
        cocktail_data.append(data)

    return render_template('favorites.html', cocktails=cocktail_data)

@app.route('/delete_favorite', methods=['POST'])
def delete_favorite():
    user_id = current_user.id
    cocktail_id = request.form['cocktail_id']
    favorite = FavoriteCocktail.query.filter_by(user_id=user_id, cocktail_id=cocktail_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash('Cocktail removed from favorites!')
    else:
        flash('Cocktail not found in favorites!')
    return redirect(url_for('favorites'))

if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)
