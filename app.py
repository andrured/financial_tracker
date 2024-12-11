from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import plotly.graph_objs as go

# Crear instancia de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:\Users\Andres\Desktop\financial_tracker\database\finances.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la instancia de SQLAlchemy
db = SQLAlchemy(app)

# Modelo de base de datos para las transacciones financieras
class Transaction(db.Model):
    # Definición de las columnas de la tabla Transaction
    id = db.Column(db.Integer, primary_key=True)  # Identificador único de cada transacción
    amount = db.Column(db.Float, nullable=False)  # Monto de la transacción (obligatorio)
    date = db.Column(db.Date, default=datetime.date.today)  # Fecha de la transacción, por defecto es la fecha actual
    description = db.Column(db.String(255), nullable=False)  # Descripción de la transacción (obligatorio)
    category = db.Column(db.String(100), nullable=False)  # Categoría de la transacción (obligatorio)
    type = db.Column(db.String(10), nullable=False)  # Tipo de transacción: "Ingreso" o "Gasto"
    payment_method = db.Column(db.String(50), nullable=False)  # Método de pago utilizado

# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

# Ruta principal: mostrar resumen de ingresos, gastos, balance y listado de transacciones
@app.route('/')
def index():
    # Cálculo de totales de ingresos y gastos
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Ingreso").scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto").scalar() or 0
    balance = total_income - total_expense  # Calcular el balance actual

    # Obtener todas las transacciones ordenadas por fecha (de más reciente a más antigua)
    all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()

    # Renderizar la plantilla con los datos calculados
    return render_template('index.html', 
                           total_income=total_income, 
                           total_expense=total_expense, 
                           balance=balance, 
                           transactions=all_transactions)

# Ruta para obtener datos de gráficos de gastos por categoría
@app.route('/chart-data', methods=['GET'])
def chart_data():
    # Obtener categorías únicas de los gastos
    categories = db.session.query(Transaction.category).filter(Transaction.type == "Gasto").distinct().all()
    categories = [category[0] for category in categories]  # Extraer solo los nombres de las categorías

    # Calcular el total gastado en cada categoría
    expenses_by_category = {
        category: db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type == "Gasto", Transaction.category == category).scalar() or 0
        for category in categories
    }

    # Preparar los datos del gráfico
    expense_categories = list(expenses_by_category.keys())
    expense_values = list(expenses_by_category.values())

    # Colores para las categorías
    colors = ['#FF6347', '#66CDAA', '#FFD700', '#8A2BE2', '#D2691E', '#DC143C']

    # Crear un gráfico de torta usando Plotly
    figure = go.Figure(
        data=[go.Pie(
            labels=expense_categories,
            values=expense_values,
            hole=0.3,  # Estilo de gráfico de dona
            marker=dict(colors=colors)  # Asignación de colores
        )]
    )
    figure.update_layout(title='Gastos por Categoría', showlegend=True)

    # Devolver los datos del gráfico en formato JSON
    return jsonify(figure.to_dict())

# Ruta para mostrar historial completo de transacciones
@app.route('/historial')
def historial():
    # Obtener todas las transacciones ordenadas por fecha
    all_transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('historial.html', transactions=all_transactions)

# Ruta para agregar una nueva transacción
@app.route('/add-transaction', methods=['POST'])
def add_transaction():
    # Obtener datos del formulario enviado por el usuario
    amount = float(request.form['amount'])
    date = request.form['date']
    description = request.form['description']
    category = request.form['category']
    type_ = request.form['type']
    payment_method = request.form['payment_method']

    # Convertir la fecha de texto a un objeto de fecha
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    # Crear una nueva instancia de transacción
    new_transaction = Transaction(
        amount=amount,
        date=date_obj,
        description=description,
        category=category,
        type=type_,
        payment_method=payment_method
    )
    
    # Guardar la nueva transacción en la base de datos
    db.session.add(new_transaction)
    db.session.commit()

    # Redirigir a la página principal después de agregar la transacción
    return redirect(url_for('index'))

# Ruta para eliminar una transacción
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_transaction(id):
    # Buscar la transacción con el ID proporcionado
    transaction_to_delete = Transaction.query.get(id)
    if transaction_to_delete:
        # Eliminar la transacción si existe
        db.session.delete(transaction_to_delete)
        db.session.commit()
    return redirect(url_for('historial'))  # Redirigir al historial después de eliminar

# Ruta para editar una transacción existente
@app.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
def edit_transaction(id):
    # Buscar la transacción en la base de datos o devolver un error 404 si no existe
    transaction = Transaction.query.get_or_404(id)

    if request.method == 'POST':
        # Actualizar la transacción con los datos del formulario
        transaction.amount = float(request.form['amount'])
        transaction.date = datetime.datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        transaction.description = request.form['description']
        transaction.category = request.form['category']
        transaction.type = request.form['type']
        transaction.payment_method = request.form['payment_method']

        # Guardar los cambios en la base de datos
        db.session.commit()

        # Redirigir a la página principal después de la edición
        return redirect(url_for('index'))

    # Renderizar la plantilla de edición con los datos actuales de la transacción
    return render_template('edit_transaction.html', transaction=transaction)

# Ejecutar la aplicación en modo de depuración
if __name__ == '__main__':
    app.run(debug=True)
