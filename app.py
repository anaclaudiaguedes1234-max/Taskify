from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import bcrypt 

app = Flask(__name__)
app.secret_key = "uma-chave-super-segura-qualquer-coisa-aqui"  # necessária p/ login

# Configuração do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo Task 
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # título obrigatório
    description = db.Column(db.Text, nullable=True)  # descrição opcional
    status = db.Column(db.String(20), default="pendente")  # pendente ou concluida
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # data automática

# Modelo de Usuário (para login / autenticações futuras)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    senha = db.Column(db.String(200), nullable=False)

# -------------------- ROTAS --------------------

@app.route('/')
def home():
    # se já estiver logado, vai direto pro painel
    if 'user_id' in session:
        return redirect(url_for('get_tasks'))
    # se não, volta pro login
    return redirect(url_for('login_page'))

def login_required(func):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Criar tarefa
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'pendente')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Tarefa criada com sucesso!"}), 201

# Registrar usuário
@app.route('/register', methods=['POST'])
def register_user():
    if request.form:
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha_plana = request.form.get('senha', '')
    else:
        data = request.get_json(force=True, silent=True) or {}
        nome = (data.get('nome') or '').strip()
        email = (data.get('email') or '').strip().lower()
        senha_plana = data.get('senha') or ''

    if not nome or not email or not senha_plana:
        msg = {"error": "Preencha nome, email e senha."}
        return (jsonify(msg), 404) if request.is_json else (render_template('register.html'), 400)

    senha_hash = bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    novo_usuario = User(nome=nome, email=email, senha=senha_hash)
    db.session.add(novo_usuario)
    db.session.commit()

    if request.form:
        return redirect(url_for('login_page'))
    return jsonify({"message": "Usuário registrado com sucesso!"}), 201

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.form:
        email_digitado = request.form.get('email', '').strip().lower()
        senha_digitada = request.form.get('senha', '')
    else:
        data = request.get_json(force=True, silent=True) or {}
        email_digitado = (data.get('email') or '').strip().lower()
        senha_digitada = data.get('senha') or ''

    user = User.query.filter_by(email=email_digitado).first()
    if not user:
        msg = {"error": "Usuário não encontrado."}
        return (jsonify(msg), 404) if request.is_json else (msg, 404)

    if bcrypt.checkpw(senha_digitada.encode('utf-8'), user.senha.encode('utf-8')):
        session['user_id'] = user.id
        # Duração da sessão (1 hora logado)
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=1)
        if request.form:
            return redirect(url_for('get_tasks'))
        return jsonify({"message": "Login bem-sucedido!"}), 200
    else:
        msg = {"error": "Senha incorreta"}
        return (jsonify(msg), 404) if request.is_json else (msg, 401)

# Logout
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login_page'))

# Exibir tarefas
@app.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    tasks = Task.query.all()
    return render_template('tasks.html', tasks=tasks)

# Atualizar tarefa
@app.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = Task.query.get(id)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    data = request.get_json()
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.status = data.get('status', task.status)
    db.session.commit()
    return jsonify({"message": "Tarefa atualizada com sucesso!"})

# Deletar tarefa
@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get(id)
    if not task:
        return jsonify({"error": "Tarefa não encontrada"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Tarefa deletada com sucesso!"})

# Nova tarefa via formulário
@app.route('/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not title:
            return "Título é obrigatório", 400
        task = Task(title=title, description=description)
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('get_tasks'))
    return render_template('new_task.html')

# Inicialização
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
