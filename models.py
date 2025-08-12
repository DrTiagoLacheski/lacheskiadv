# models.py (Corrigido - Relacionamentos desambiguados para delegado_id e user_id em Ticket)

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
from sqlalchemy import Numeric

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    associados = db.relationship('User', backref=db.backref('admin', remote_side=[id]), lazy='dynamic')

    # Tickets onde o user é autor
    tickets = db.relationship('Ticket', backref='author', lazy='dynamic',
                              cascade="all, delete-orphan", foreign_keys='Ticket.user_id')
    # Tickets onde o user é delegado
    delegated_tickets = db.relationship('Ticket', backref='delegado_user', lazy='dynamic',
                                        foreign_keys='Ticket.delegado_id')

    comments = db.relationship('Comment', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='author', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    advogados = db.relationship('Advogado', backref='owner_user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_advogado_principal(self):
        """Retorna o advogado principal deste usuário (sempre existe)"""
        return self.advogados.filter_by(is_principal=True).first()

    def get_advogados_colaboradores(self):
        """
        Para admin: retorna advogados colaboradores próprios.
        Para associado: retorna advogados colaboradores do admin.
        """
        if self.is_admin:
            return self.advogados.filter_by(is_principal=False).order_by(Advogado.nome).all()
        elif self.admin_id and self.admin:
            return self.admin.advogados.filter_by(is_principal=False).order_by(Advogado.nome).all()
        return []

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
    delegado_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    # Relacionamento explícito para acesso ao usuário delegado
    delegado = db.relationship('User', foreign_keys=[delegado_id])

    comments = db.relationship('Comment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic', cascade="all, delete-orphan")
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
    attachments = db.relationship('Attachment', backref='comment', lazy='dynamic', cascade="all, delete-orphan")

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    position = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    appointment_date = db.Column(db.Date, nullable=False, index=True)
    data_original = db.Column(db.Date, nullable=True)
    appointment_time = db.Column(db.String(5), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Normal')
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    remarcada_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    todo_id = db.Column(db.Integer, db.ForeignKey('todo_item.id'), nullable=True)
    todo = db.relationship('TodoItem', backref='appointment', uselist=False)
    source = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        # Se o appointment veio de tarefa, inclua o ticket id e título
        ticket_id = None
        ticket_title = None
        if self.todo_id and self.todo and self.todo.ticket:
            ticket_id = self.todo.ticket.id
            ticket_title = self.todo.ticket.title
        return {
            'id': self.id,
            'content': self.content,
            'date': self.appointment_date.strftime('%Y-%m-%d'),
            'time': self.appointment_time,
            'priority': self.priority,
            'recurring': self.is_recurring,
            'todo_id': self.todo_id,
            'is_completed': self.todo.is_completed if self.todo_id and self.todo else False,
            'source': self.source,
            'ticket_id': ticket_id,
            'ticket_title': ticket_title,
        }

class TodoItem(db.Model):
    __tablename__ = 'todo_item'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date = db.Column(db.Date, nullable=True)
    data_original = db.Column(db.Date, nullable=True)
    position = db.Column(db.Integer, default=0, nullable=False)
    was_rescheduled = db.Column(db.Boolean, default=False, nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    priority = db.Column(db.String(20), default='Normal')
    time = db.Column(db.String(8), nullable=True)
    remarcada_count = db.Column(db.Integer, default=0, nullable = True)

    def __repr__(self):
        return f'<TodoItem {self.id}: {self.content[:20]}>'

class Advogado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    estado_civil = db.Column(db.String(50), nullable=False)
    profissao = db.Column(db.String(100), nullable=False, default='advogado')
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20), nullable=True)
    orgao_emissor = db.Column(db.String(20), nullable=True)
    oabs = db.Column(MutableList.as_mutable(PickleType), default=[], nullable=False)
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
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.String(300), nullable=True)
    path = db.Column(db.String(500), nullable=False)
    tamanho = db.Column(db.Integer, nullable=True)
    tipo_mime = db.Column(db.String(100), nullable=True)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artigo_id = db.Column(db.Integer, db.ForeignKey('artigo.id'), nullable=True)
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


class LancamentoFinanceiro(db.Model):
    __tablename__ = "lancamento_financeiro"
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(Numeric(12, 2), nullable=False)
    data = db.Column(db.Date, nullable=False, index=True)
    data_original = db.Column(db.Date, nullable=True)
    categoria = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Previsto')
    user = db.relationship('User', backref='lancamentos_financeiros')
    ticket = db.relationship('Ticket', backref='lancamentos_financeiros')

    def __repr__(self):
        return f"<LancamentoFinanceiro {self.id} - {self.tipo} - {self.valor}>"

#poder criar seus prorios modelos de formulario
class ProcuracaoModelo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)  # Exemplo: texto com tags {{nome_completo}}, {{cpf}}, etc.
    criado_por_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    criado_por = db.relationship('User', backref='modelos_procuracao')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)