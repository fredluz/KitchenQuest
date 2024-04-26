import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pantry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model for your ingredients
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    expiration_date = db.Column(db.String(100), nullable=False)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    ingredients = db.relationship('Ingredient', secondary='recipe_ingredient', backref='recipes')

# Define association table for many-to-many relationship
recipe_ingredient = db.Table('recipe_ingredient',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True),
    db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
)

def recommend_recipes():
    available_ingredients = set(Ingredient.query.all())
    recommended_recipes = []
    for recipe in Recipe.query.all():
        if available_ingredients.issuperset(recipe.ingredients):
            recommended_recipes.append(recipe)
    return recommended_recipes

# Route to display recommended recipes
""" @app.route('/receitas')
def receitas():
    # Make a request to the recipe API (replace 'API_KEY' and 'INGREDIENTS' with your actual API key and parameters)
    ingredients = 'INGREDIENTS'
    url = f'www.themealdb.com/api/json/v1/1/filter.php?i={ingredients}'
    
    response = requests.get(url)

    # Parse JSON response
    if response.status_code == 200:
        data = response.json()
        recipes = data['recipes']
    else:
        recipes = []

    # Render template with recipe data
    return render_template('receitas.html', recipes=recipes) """

@app.route('/receitas', methods=['GET', 'POST'])
def receitas():
    if request.method == 'GET':
        # Get the ingredient entered by the user from the form
        query = request.args.get('query')

        # Make a request to the recipe API with the new ingredient parameter
        api_url = f'https://api.api-ninjas.com/v1/recipe?query={query}'
        headers = {'X-Api-Key': 'fu5PEROkHGyBvuAVmwP2fg==2Vzh8WiMIidH9W80'}  # Replace 'YOUR_API_KEY' with your actual API key
        response = requests.get(api_url, headers=headers)

        # Parse JSON response
        if response.status_code == 200:
            data = response.json()
            print(data)  # Inspect the JSON response
            recipes_data = data.get('results', [])  # Get the list of recipes

            # Format recipe data
            recipes = []
            for recipe_data in recipes_data:
                recipe = {
                    'title': recipe_data.get('title', ''),
                    'ingredients': recipe_data.get('ingredients', ''),
                    'servings': recipe_data.get('servings', ''),
                    'instructions': recipe_data.get('instructions', '')
                }
                recipes.append(recipe)
        else:
            recipes = []

    else:
        # If method is not GET, render the template without making an API request
        recipes = []

    # Render template with updated recipe data
    return render_template('receitas.html', recipes=recipes)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dispensa')
def dispensa():
    ingredients = Ingredient.query.all()
    return render_template('dispensa.html', ingredients=ingredients)
# Route to add new ingredient
@app.route('/add', methods=['POST'])
def add_ingredient():
    name = request.form.get('name')
    quantity = request.form.get('quantity')
    expiration_date = request.form.get('expiration_date')

    # Create new Ingredient object
    ingredient = Ingredient(name=name, quantity=quantity, expiration_date=expiration_date)
    db.session.add(ingredient)
    db.session.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables for our data models
    app.run(debug=True)
