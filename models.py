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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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

# Modelo de anexo unificado. A classe CommentAttachment foi removida.
class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    path = db.Column(db.String(200), nullable=False) # A coluna se chama 'path'
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
    appointment_time = db.Column(db.String(5), nullable=False)  # Formato HH:MM
    priority = db.Column(db.String(20), nullable=False, default='Normal')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'date': self.appointment_date.strftime('%Y-%m-%d'),
            'time': self.appointment_time,
            'priority': self.priority
        }