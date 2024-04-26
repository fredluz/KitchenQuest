import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pantry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/dispensa')
def dispensa():
    ingredients = Ingredient.query.all()
    return render_template('dispensa.html', ingredients=ingredients)

@app.route('/social')
def social():
    return render_template('social.html')

@app.route('/foryou')
def foryou():
    return render_template('foryou.html')

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(100), nullable=True)  # Allow NULL values

@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    code = request.form.get('code')
    product_data = fetch_product(code)
    if product_data:
        expiration_date = product_data.get('expiration_date')
        if expiration_date is None:
            expiration_date = 'Unknown'  # Or handle this however makes sense for your application
        ingredient = Ingredient(
            name=product_data['generic_name'],
            quantity=product_data['quantity'],
            expiration_date=expiration_date
        )
        db.session.add(ingredient)
        try:
         db.session.commit()
         return redirect(url_for('dispensa'))
        except SQLAlchemy.exc.IntegrityError as e:
            db.session.rollback()  # Roll back the session on error
            return "There was an issue adding the ingredient: {}".format(e), 500
    if product_data == None:
        return "Failed to fetch product data", 404
def fetch_product(code):
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}.json"
    response = requests.get(url)
    if response.ok:
     data = response.json()
     product = data.get('product', {})
     generic_name = product.get('generic_name')
     quantity = product.get('quantity')
     # Return a dictionary with the data
     return {'generic_name': generic_name, 'quantity': quantity} 
    else:
        return  None

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables for our data models
    app.run(debug=True)

