from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import plotly.graph_objs as go

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:\Users\Andres\Desktop\financial_tracker\database\finances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de base de datos
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)
    description = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)

# Crear la base de datos
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Cálculo de totales
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Ingreso").scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto").scalar() or 0
    balance = total_income - total_expense

    # Obtener historial de transacciones
    all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()

    # Pasar los datos de las transacciones al frontend
    return render_template('index.html', 
                           total_income=total_income, 
                           total_expense=total_expense, 
                           balance=balance, 
                           transactions=all_transactions)

@app.route('/chart-data', methods=['GET'])
def chart_data():
    # Consultar las categorías de gastos dinámicamente desde la base de datos
    categories = db.session.query(Transaction.category).filter(Transaction.type == "Gasto").distinct().all()
    categories = [category[0] for category in categories]  # Extraer los nombres de categoría

    # Obtener los totales de cada categoría
    expenses_by_category = {
        category: db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto", Transaction.category == category).scalar() or 0
        for category in categories
    }

    # Preparar los datos para el gráfico
    expense_categories = list(expenses_by_category.keys())
    expense_values = list(expenses_by_category.values())

    # Crear el gráfico como un objeto Plotly Figure
    figure = go.Figure(
        data=[
            go.Pie(labels=expense_categories, values=expense_values, hole=0.3)  # Pie chart con agujero
        ]
    )
    figure.update_layout(title='Gastos por Categoría', showlegend=True)

    # Convertir la figura a un diccionario JSON serializable
    return jsonify(figure.to_dict())




@app.route('/add-transaction', methods=['POST'])
def add_transaction():
    amount = float(request.form['amount'])
    date = request.form['date']
    description = request.form['description']
    category = request.form['category']
    type_ = request.form['type']
    payment_method = request.form['payment_method']

    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    new_transaction = Transaction(
        amount=amount,
        date=date_obj,
        description=description,
        category=category,
        type=type_,
        payment_method=payment_method
    )
    
    db.session.add(new_transaction)
    db.session.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
