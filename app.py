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
    category = db.Column(db.String(100), nullable=False)  # Ejemplo: "Alimentos", "Renta"
    type = db.Column(db.String(10), nullable=False)       # "Ingreso" o "Gasto"
    payment_method = db.Column(db.String(50), nullable=False)  # Ejemplo: "Efectivo", "Tarjeta"

# Crear la base de datos
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Cálculo de totales
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Ingreso").scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto").scalar() or 0
    balance = total_income - total_expense

    # Crear gráfico de gastos por categoría
    categories = ['Alimentos', 'Renta', 'Transporte', 'Entretenimiento', 'Salario']
    expenses_by_category = {
        category: db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto", Transaction.category == category).scalar() or 0
        for category in categories
    }

    # Crear gráfico con Plotly
    expense_categories = list(expenses_by_category.keys())
    expense_values = list(expenses_by_category.values())

    expense_graph = {
        'data': [
            go.Pie(labels=expense_categories, values=expense_values, hole=0.3, name="Gastos por Categoría")
        ],
        'layout': {
            'title': 'Gastos por Categoría',
            'showlegend': True
        }
    }

    # Obtener historial de transacciones
    all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()

    return render_template('index.html', 
                           total_income=total_income, 
                           total_expense=total_expense, 
                           balance=balance, 
                           expense_graph=expense_graph,
                           transactions=all_transactions)

@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    if request.method == 'POST':
        # Obtener los datos del formulario
        amount = request.form['amount']
        date = request.form['date']
        description = request.form['description']
        category = request.form['category']
        type_ = request.form['type']
        payment_method = request.form['payment_method']

        # Convertir la fecha en formato 'YYYY-MM-DD' a un objeto de tipo 'date'
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        # Crear una nueva transacción
        new_transaction = Transaction(
            amount=amount,
            date=date_obj,  # Usar el objeto 'date'
            description=description,
            category=category,
            type=type_,
            payment_method=payment_method
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        return redirect(url_for('transactions'))

    # Mostrar historial de transacciones
    all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=all_transactions)

@app.route('/chart-data', methods=['GET'])
def chart_data():
    # Consulta dinámica desde la base de datos
    categories = ['Income', 'Expenses']
    income_total = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Ingreso").scalar() or 0
    expense_total = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto").scalar() or 0
    totals = [income_total, expense_total]

    # Crear gráfico con Plotly
    figure = {
        'data': [
            go.Bar(name='Totals', x=categories, y=totals)
        ],
        'layout': {
            'title': 'Income vs Expenses',
            'barmode': 'group'
        }
    }

    return jsonify(figure)

if __name__ == '__main__':
    app.run(debug=True)
