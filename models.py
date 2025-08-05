# models.py (Versão Corrigida e Unificada)

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    tickets = db.relationship('Ticket', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='author', lazy='dynamic')
    # Adicionado o relacionamento com Appointment
    appointments = db.relationship('Appointment', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    advogados = db.relationship('Advogado', backref='owner_user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_code = db.Column(db.String(30), unique=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    case_number = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Em Análise')
    priority = db.Column(db.String(20), default='Média')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    delegado = db.Column(db.String(100))
    # AJUSTE: Adicionado 'cascade' para exclusão automática no banco de dados
    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    # --- NOVO RELACIONAMENTO ADICIONADO ---
    # Adiciona a relação com a nova tabela de tarefas
    todos = db.relationship('TodoItem', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")

    def update_status(self, new_status):
        self.status = new_status
        self.updated_at = datetime.utcnow()


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    # A relação agora aponta para o modelo 'Attachment' unificado
    attachments = db.relationship('Attachment', backref='comment', lazy='dynamic', cascade="all, delete-orphan")

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(200), nullable=False)  # A coluna se chama 'path'
    position = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Chaves estrangeiras que podem ser nulas, determinando a quem o anexo pertence
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    data_original = db.Column(db.Date, nullable=True)
    appointment_time = db.Column(db.String(5), nullable=True)  # Formato HH:MM
    priority = db.Column(db.String(20), nullable=False, default='Normal')
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    remarcada_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo_item.id'), nullable=True)
    todo = db.relationship('TodoItem', backref='appointment', uselist=False)
    source = db.Column(db.String(20), nullable=True)  # 'financeiro' ou 'triagem'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'date': self.appointment_date.strftime('%Y-%m-%d'),
            'time': self.appointment_time,
            'priority': self.priority,
            'recurring': self.is_recurring,  # Novo campo adicionado
            'todo_id': self.todo_id,
            'is_completed': self.todo.is_completed if self.todo_id and self.todo else False,
            'source': self.source
        }

    # --- NOVA CLASSE ADICIONADA ---


class TodoItem(db.Model):
    __tablename__ = 'todo_item'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=True)
    position = db.Column(db.Integer, default=0, nullable=False)
    was_rescheduled = db.Column(db.Boolean, default=False, nullable=False)
    # Chave estrangeira para ligar a tarefa a um ticket específico
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

    def __repr__(self):
        return f'<TodoItem {self.id}: {self.content[:20]}>'

class Advogado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Campos adicionais para o advogado
    nome = db.Column(db.String(150), nullable=False)
    estado_civil = db.Column(db.String(50), nullable=False)
    profissao = db.Column(db.String(100), nullable=False, default='advogado')
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=True)
    orgao_emissor = db.Column(db.String(20), nullable=True)
    # É melhor separar as OABs em campos distintos para facilitar a consulta
    oab_pr = db.Column(db.String(20), nullable=True)
    oab_ro = db.Column(db.String(20), nullable=True)
    #outros campos de OAB que você possa precisar no futuro
    oab_sp = db.Column(db.String(20), nullable=True)
    endereco_profissional = db.Column(db.String(255), nullable=False)
    is_principal = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Advogado {self.nome}>'

class Artigo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    imagem_capa = db.Column(db.String(255))
    autor = db.relationship('User', backref='artigos')
    anexos = db.relationship('Arquivo', backref='artigo', lazy='dynamic', cascade="all, delete-orphan")
    comentarios = db.relationship('Comentario', backref='artigo', lazy='dynamic', cascade="all, delete-orphan")

class Arquivo(db.Model):
    """Modelo para armazenar arquivos de guidelines/materiais"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)  # Nome do arquivo no disco
    descricao = db.Column(db.String(300), nullable=True)
    path = db.Column(db.String(500), nullable=False)      # Caminho completo do arquivo
    tamanho = db.Column(db.Integer, nullable=True)        # Tamanho em bytes
    tipo_mime = db.Column(db.String(100), nullable=True)  # Tipo MIME do arquivo
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artigo_id = db.Column(db.Integer, db.ForeignKey('artigo.id'), nullable=True)

    # Relacionamento com o usuário que fez upload
    uploader = db.relationship('User', backref='arquivos_uploaded')
    
    def __repr__(self):
        return f'<Arquivo {self.nome}>'

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    artigo_id = db.Column(db.Integer, db.ForeignKey('artigo.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    autor = db.relationship('User', backref='comentarios')


from sqlalchemy import Numeric

class LancamentoFinanceiro(db.Model):
    __tablename__ = "lancamento_financeiro"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)  # "Entrada" ou "Saída"
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(Numeric(12, 2), nullable=False)
    data = db.Column(db.Date, nullable=False, index=True)
    data_original = db.Column(db.Date, nullable=True)
    categoria = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Opcional, se quiser quem lançou
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)  # Opcional, se quiser associar a ticket/caso
    status = db.Column(db.String(20), nullable=False, default='Previsto')
    user = db.relationship('User', backref='lancamentos_financeiros')
    ticket = db.relationship('Ticket', backref='lancamentos_financeiros')

    def __repr__(self):
        return f"<LancamentoFinanceiro {self.id} - {self.tipo} - {self.valor}>"


