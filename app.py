from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pantry.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    expiration_date = db.Column(db.String(50))

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.relationship('RecipeIngredient', backref='recipe', lazy=True)
    
class RecipeIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', name='fk_recipeingredient_recipe'), nullable=False)
    ingredient_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)

@app.route('/dispensa')
def dispensa():
    ingredients = Ingredient.query.all()
    return render_template('dispensa.html', ingredients=ingredients)

@app.route('/social')
def social():
    return render_template('social.html')

@app.route('/add_ingredient', methods=['POST'])
def add_ingredient():
    code = request.form.get('code')
    product_data = fetch_product(code)
    if product_data:
        product_id = product_data['id']
        product_name = product_data['product_name']
        quantity = product_data['quantity']
        
        # Normalize the quantity input
        normalized_quantity = normalize_quantity(quantity)
        
        # Fetch the ingredient by its unique id
        existing_ingredient = Ingredient.query.filter_by(id=product_id).first()
        
        if existing_ingredient:
            # Ingredient exists, update quantity
            try:
                # Split and parse the quantities
                existing_quantity_value, existing_quantity_unit = existing_ingredient.quantity.split()
                new_quantity_value, new_quantity_unit = normalized_quantity.split()
                
                # Ensure the units match (they should all be in grams now)
                if existing_quantity_unit != new_quantity_unit:
                    flash('Unit mismatch. Cannot add quantities with different units.', 'error')
                    return redirect(url_for('dispensa'))
                
                # Update the quantity
                updated_quantity_value = int(existing_quantity_value) + int(new_quantity_value)
                existing_ingredient.quantity = f"{updated_quantity_value} {new_quantity_unit}"
                db.session.commit()
                flash('Ingredient quantity updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating ingredient: {str(e)}', 'error')
        else:
            # No existing ingredient, create a new one
            expiration_date = product_data.get('expiration_date', 'Unknown')
            new_ingredient = Ingredient(
                id=product_id,
                name=product_name,
                quantity=normalized_quantity,
                expiration_date=expiration_date
            )
            db.session.add(new_ingredient)
            try:
                db.session.commit()
                flash('New ingredient added successfully!', 'success')
            except SQLAlchemy.exc.IntegrityError as e:
                db.session.rollback()
                flash(f'There was an issue adding the ingredient: {str(e)}', 'error')
        
        return redirect(url_for('dispensa'))
    else:
        flash('Failed to fetch product data', 'error')
        return redirect(url_for('add_ingredient'))


@app.route('/add_ingredient_manual', methods=['POST'])
def add_ingredient_manual():
    name = request.form.get('name')
    quantity = request.form.get('quantity')
    
    # Normalize the quantity input
    normalized_quantity = normalize_quantity(quantity)
    
    # Check if the ingredient with the same name exists
    existing_ingredient = Ingredient.query.filter_by(name=name).first()
    
    if existing_ingredient:
        try:
            # Split and parse the quantities
            existing_quantity_value, existing_quantity_unit = existing_ingredient.quantity.split()
            new_quantity_value, new_quantity_unit = normalized_quantity.split()
            
            # Ensure the units match (they should all be in grams now)
            if existing_quantity_unit != new_quantity_unit:
                flash('Unit mismatch. Cannot add quantities with different units.', 'error')
                return redirect(url_for('dispensa'))
            
            # Update the quantity
            updated_quantity_value = int(existing_quantity_value) + int(new_quantity_value)
            existing_ingredient.quantity = f"{updated_quantity_value} {new_quantity_unit}"
            db.session.commit()
            flash('Ingredient quantity updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating ingredient: {str(e)}', 'error')
    else:
        # No existing ingredient, create a new one
        new_ingredient = Ingredient(
            name=name,
            quantity=normalized_quantity,
            expiration_date='Unknown'  # Default value for expiration date
        )
        db.session.add(new_ingredient)
        try:
            db.session.commit()
            flash('New ingredient added successfully!', 'success')
        except SQLAlchemy.exc.IntegrityError as e:
            db.session.rollback()
            flash(f'There was an issue adding the ingredient: {str(e)}', 'error')
    
    return redirect(url_for('dispensa'))


def normalize_quantity(quantity):
    # Split the quantity into value and unit
    parts = quantity.split()
    
    # If the unit is attached to the value (like "300g"), separate them
    if len(parts) == 1:
        value = ''.join(filter(str.isdigit, parts[0]) + '.' if ',' in parts[0] else filter(str.isdigit, parts[0]))
        unit = ''.join(filter(str.isalpha, parts[0]))
    else:
        value, unit = parts

    # Replace commas with periods in the value
    value = value.replace(',', '.')
    
    # Convert value to float for calculations
    value = float(value)
    unit = unit.strip().lower()
    if unit in ['litros', 'l', 'L']:
        value *= 1  # Convert l to L
        unit = 'L'
    if unit in ['kg', 'kilogram', 'kilograms']:
        value *= 1000  # Convert kg to g
        unit = 'g'

    # Ensure there's a space between the value and unit
    return f"{int(value)} {unit}"

def fetch_product(code):
    url = f"https://world.openfoodfacts.org/api/v2/product/{code}.json"
    response = requests.get(url)
    if response.ok:
        data = response.json()
        product = data.get('product', {})
        product_name = product.get('product_name')
        quantity = product.get('quantity')
        product_id = product.get('id')  # Fetch the unique id of the product
        # Return a dictionary with the data
        return {'id': int(product_id), 'product_name': product_name, 'quantity': quantity}
    else:
        return None

    
@app.route('/remove_ingredient', methods=['POST'])
def remove_ingredient():
    ingredient_name = request.form.get('ingredient_name')
    quantity_to_remove = int(request.form.get('quantity_to_remove'))

    existing_ingredient = Ingredient.query.filter_by(name=ingredient_name).first()
    if existing_ingredient:
        current_quantity = int(existing_ingredient.quantity.split()[0])
        unit = existing_ingredient.quantity.split()[1]

        if current_quantity > quantity_to_remove:
            new_quantity = current_quantity - quantity_to_remove
            existing_ingredient.quantity = f"{new_quantity} {unit}"
            db.session.commit()
            flash('Ingredient quantity updated successfully!', 'success')
        elif current_quantity == quantity_to_remove:
            db.session.delete(existing_ingredient)
            db.session.commit()
            flash('Ingredient removed successfully!', 'success')
        else:
            flash('Quantity to remove exceeds current quantity!', 'error')
    else:
        flash('Ingredient not found!', 'error')

    return redirect(url_for('dispensa'))


@app.route('/rename_ingredient', methods=['POST'])
def rename_ingredient():
    current_name = request.form.get('current_name')
    new_name = request.form.get('new_name')

    existing_ingredient = Ingredient.query.filter_by(name=current_name).first()
    if existing_ingredient:
        existing_ingredient.name = new_name
        try:
            db.session.commit()
            flash('Ingredient renamed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error renaming ingredient: {str(e)}', 'error')
    else:
        flash('Ingredient not found!', 'error')

    return redirect(url_for('dispensa'))


@app.route('/clear_ingredients', methods=['POST'])
def clear_ingredients():
    try:
        num_rows_deleted = db.session.query(Ingredient).delete()
        db.session.commit()
        flash(f'Deleted {num_rows_deleted} rows from Ingredients.', 'info')
        return redirect(url_for('dispensa'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing table: {str(e)}', 'error')
        return redirect(url_for('dispensa'))



@app.route('/recipes')
def recipes():
    recipes = Recipe.query.all()
    ingredients_in_pantry = Ingredient.query.all()
    recipe_details = []
    for recipe in recipes:
        ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        status = 'sufficient'
        for recipe_ingredient in ingredients:
            ingredient = Ingredient.query.filter_by(name=recipe_ingredient.ingredient_name).first()
            if not ingredient or int(normalize_quantity(ingredient.quantity).split()[0]) < int(normalize_quantity(recipe_ingredient.quantity).split()[0]):
                status = 'insufficient'
                break
        recipe_details.append({'recipe': recipe, 'ingredients': ingredients, 'status': status})

    return render_template('recipes.html', recipe_details=recipe_details, ingredients=ingredients_in_pantry, normalize_quantity=normalize_quantity)

@app.route('/for-you')
def for_you():
    recipes = Recipe.query.all()
    ingredients_in_pantry = Ingredient.query.all()
    available_recipes = []

    for recipe in recipes:
        ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe.id).all()
        can_make = True
        for recipe_ingredient in ingredients:
            ingredient = Ingredient.query.filter_by(name=recipe_ingredient.ingredient_name).first()
            if not ingredient or int(normalize_quantity(ingredient.quantity).split()[0]) < int(normalize_quantity(recipe_ingredient.quantity).split()[0]):
                can_make = False
                break
        if can_make:
            available_recipes.append({'recipe': recipe, 'ingredients': ingredients})

    return render_template('for-you.html', available_recipes=available_recipes)

@app.route('/add_recipe', methods=['POST'])
def add_recipe():
    name = request.form.get('name')
    new_recipe = Recipe(name=name)
    db.session.add(new_recipe)
    db.session.commit()
    
    ingredients = request.form.getlist('ingredient_name')
    quantities = request.form.getlist('quantity')
    
    for ingredient_name, quantity in zip(ingredients, quantities):
        if ingredient_name and quantity:
            new_ingredient = RecipeIngredient(recipe_id=new_recipe.id, ingredient_name=ingredient_name, quantity=quantity)
            db.session.add(new_ingredient)
    
    db.session.commit()
    flash('Recipe added successfully!', 'success')
    return redirect(url_for('recipes'))

@app.route('/cook_recipe/<int:recipe_id>', methods=['POST'])
def cook_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    recipe_ingredients = RecipeIngredient.query.filter_by(recipe_id=recipe_id).all()
    for recipe_ingredient in recipe_ingredients:
        ingredient = Ingredient.query.filter_by(name=recipe_ingredient.ingredient_name).first()
        if ingredient:
            normalized_pantry_quantity = normalize_quantity(ingredient.quantity)
            normalized_recipe_quantity = normalize_quantity(recipe_ingredient.quantity)

            pantry_quantity_value, pantry_quantity_unit = normalized_pantry_quantity.split()
            recipe_quantity_value, recipe_quantity_unit = normalized_recipe_quantity.split()

            if pantry_quantity_unit != recipe_quantity_unit:
                flash('Unit mismatch in recipe and pantry ingredients.', 'error')
                return redirect(url_for('recipes'))

            updated_quantity_value = int(pantry_quantity_value) - int(recipe_quantity_value)
            if updated_quantity_value < 0:
                flash(f'Not enough {ingredient.name} to cook {recipe.name}.', 'error')
                return redirect(url_for('recipes'))

            if updated_quantity_value == 0:
                db.session.delete(ingredient)
            else:
                ingredient.quantity = f"{updated_quantity_value} {pantry_quantity_unit}"

            db.session.commit()
        else:
            flash(f'Ingredient {recipe_ingredient.ingredient_name} not found in pantry.', 'error')
            return redirect(url_for('recipes'))

    flash(f'Successfully cooked {recipe.name}!', 'success')
    return redirect(url_for('recipes'))




@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
