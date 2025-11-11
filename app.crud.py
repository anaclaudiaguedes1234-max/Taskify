from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuração do Banco de Dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo Task 
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # título obrigatório
    description = db.Column(db.Text, nullable=True)  # descrição opcional
    status = db.Column(db.String(20), default="pendente")  # pendente ou concluída
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # data automática


@app.route('/')
def home():
    return 'API Taskify conectada ao banco de dados com SQLAlchemy'


# Criar nova tarefa
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


# Listar todas as tarefas
@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    tasks_list = []

    for task in tasks:
        tasks_list.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at
        })

    return jsonify(tasks_list)


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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Criando o banco e a tabela se ainda não existirem
    app.run(debug=True)
