from datetime import datetime, timedelta

from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests

app = Flask(__name__)

# Définir les clés d'API NutritionX
API_KEY = '558ec7ea28757afd9afae48b2eb057c0'
API_ID = '056d15f6'

# Chemin vers le fichier de base de données dans le dossier instance
database_path = os.path.join('C:', os.sep, 'Users', 'chaki_oyvbka2', 'OneDrive' ,'Documents', 'KCAL', 'instance', 'foods.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Food(db.Model):
    __tablename__ = 'food'  # Spécifie le nom de la table
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.Date, default=datetime.utcnow)

class DailyGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False, unique=True)
    protein = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    tonnage = db.Column(db.Float, nullable=False)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_type = db.Column(db.String(50), nullable=False)

class Tonnage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()

def get_nutrition_data(food_name):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": API_ID,
        "x-app-key": API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "query": food_name,
        "timezone": "US/Eastern"
    }
    response = requests.post(url, json=body, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Erreur lors de la récupération des données : ", response.status_code)
        return None

@app.route('/')
def index():
    foods = Food.query.filter_by(date_added=datetime.utcnow().date()).all()
    daily_calories_sum = sum(food.calories for food in foods)
    weekly_calories = get_weekly_calories()
    daily_goal = get_daily_goal()
    remaining_goal = get_remaining_goal()
    return render_template('index.html',
                           foods=foods,
                           daily_calories_sum=daily_calories_sum,
                           weekly_calories=weekly_calories,
                           daily_goal=daily_goal,
                           remaining_goal=remaining_goal)

@app.route('/chart_data')
def chart_data():
    data = {
        'labels': ['2021-01-01', '2021-01-02', '2021-01-03'],  # Exemple de dates
        'calories': [2000, 2100, 1800],
        'protein': [100, 120, 110],
        'carbohydrates': [250, 260, 240],
        'fat': [70, 75, 65]
    }
    return jsonify(data)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_food(id):
    food = Food.query.get_or_404(id)
    db.session.delete(food)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/history')
def history():
    all_foods = Food.query.order_by(Food.date_added.desc()).all()
    return render_template('history.html', all_foods=all_foods)

@app.route('/get_exercises', methods=['GET'])
def get_exercises():
    day_type = request.args.get('day_type', type=str)
    exercises = Exercise.query.filter_by(day_type=day_type).all()
    exercises_list = [{'id': exercise.id, 'name': exercise.name} for exercise in exercises]
    return jsonify({'exercises': exercises_list})

@app.route('/goals', methods=['GET', 'POST'])
@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if request.method == 'POST':
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            protein = float(request.form[f'{day}_protein'])
            carbohydrates = float(request.form[f'{day}_carbohydrates'])
            fat = float(request.form[f'{day}_fat'])
            goal = DailyGoal.query.filter_by(day=day).first()
            if goal:
                goal.protein = protein
                goal.carbohydrates = carbohydrates
                goal.fat = fat
            else:
                new_goal = DailyGoal(day=day, protein=protein, carbohydrates=carbohydrates, fat=fat)
                db.session.add(new_goal)
        db.session.commit()
        return redirect(url_for('goals'))
    
    goals = {day: DailyGoal.query.filter_by(day=day).first() for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    return render_template('goals.html', goals=goals)


@app.route('/add_food', methods=['POST'])
def add_food():
    food_name = request.form['food_name']
    servings = int(request.form['servings'])
    print(f"Adding food: {food_name}, Servings: {servings}")  # Debugging statement

    nutrition_data = get_nutrition_data(food_name)
    if not nutrition_data:
        print("Erreur lors de la récupération des données nutritionnelles.")  # Debugging statement
        return render_template('index.html', error="Erreur lors de la récupération des données nutritionnelles.")

    print("Nutrition data received: ", nutrition_data)  # Debugging statement

    total_calories = nutrition_data['foods'][0]['nf_calories'] * servings
    total_protein = nutrition_data['foods'][0]['nf_protein'] * servings
    total_carbohydrates = nutrition_data['foods'][0]['nf_total_carbohydrate'] * servings
    total_fat = nutrition_data['foods'][0]['nf_total_fat'] * servings

    print(f"Total: {total_calories} kcal, {total_protein}g protein, {total_carbohydrates}g carbohydrates, {total_fat}g fat")  # Debugging statement

    new_food = Food(name=food_name, calories=total_calories, protein=total_protein, carbohydrates=total_carbohydrates, fat=total_fat)
    db.session.add(new_food)
    db.session.commit()

    print("Food added to the database.")  # Debugging statement

    return redirect(url_for('index'))

@app.route('/calculate_calories', methods=['GET', 'POST'])
def calculate_calories():
    if request.method == ['POST']:
        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        activity_level = request.form['activity_level']

        activity_levels = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extra_active': 1.9
        }

        if activity_level not in activity_levels:
            return "Niveau d'activité invalide"

        bmr = 10 * weight + 6.25 * height - 5 * age + 5  # BMR pour hommes
        daily_calories = bmr * activity_levels[activity_level]

        return render_template('index.html', daily_calories=round(daily_calories))

    return render_template('calculate_calories.html')

@app.route('/calculate_tonnage', methods=['GET', 'POST'])
def calculate_tonnage():
    if request.method == 'POST':
        category = request.form['category']
        day_of_week = request.form['day_of_week']
        exercises = Exercise.query.filter_by(day_type=category).all()
        tonnage = calculate_tonnage_logic(category, day_of_week) # type: ignore
        return render_template('calculate_tonnage.html', tonnage=tonnage, exercises=exercises)
    return render_template('calculate_tonnage.html')

@app.route('/workouts', methods=['GET', 'POST'])
def workouts():
    if request.method == ['POST']:
        exercise = request.form['exercise']
        sets = int(request.form['sets'])
        reps = int(request.form['reps'])
        weight = float(request.form['weight'])
        tonnage = sets * reps * weight
        workout = Workout(exercise=exercise, sets=sets, reps=reps, weight=weight, tonnage=tonnage)
        db.session.add(workout)
        db.session.commit()
        return redirect(url_for('workouts'))
    return render_template('workouts.html', workouts=Workout.query.all(), exercises=Exercise.query.all())

@app.route('/workouts/delete/<int:id>', methods=['POST'])
def delete_workout(id):
    workout = Workout.query.get_or_404(id)
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for('workouts'))

def get_daily_goal():
    today = datetime.now().strftime('%A')
    print(f"Fetching goal for today: {today}")  # Debugging statement
    goal = DailyGoal.query.filter_by(day=today).first()
    if goal:
        print(f"Goal found: {goal.protein}g protein, {goal.carbohydrates}g carbohydrates, {goal.fat}g fat")  # Debugging statement
        return {'protein': goal.protein, 'carbohydrates': goal.carbohydrates, 'fat': goal.fat}
    print("No goal found for today.")  # Debugging statement
    return {'protein': 0, 'carbohydrates': 0, 'fat': 0}


def get_remaining_goal():
    goal = get_daily_goal()
    today_foods = Food.query.filter_by(date_added=datetime.utcnow().date()).all()
    consumed = {'protein': 0, 'carbohydrates': 0, 'fat': 0}
    for food in today_foods:
        consumed['protein'] += food.protein
        consumed['carbohydrates'] += food.carbohydrates
        consumed['fat'] += food.fat

    remaining = {key: goal[key] - consumed[key] for key in goal}

    for key in remaining:
        if remaining[key] < 0:
            remaining[key] = 0

    return remaining

def get_daily_calories():
    today_foods = Food.query.filter_by(date_added=datetime.utcnow().date()).all()
    return today_foods  # Retourne la liste des aliments au lieu du total des calories

def get_weekly_calories():
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    week_foods = Food.query.filter(Food.date_added >= start_of_week).all()
    return sum(food.calories for food in week_foods)

if __name__ == '__main__':
    app.run(debug=True)
print(f"Database path: {database_path}")

input("Appuie sur Entrée pour continuer...")