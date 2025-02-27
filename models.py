from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    date_posted = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f"Subscriber('{self.email}')"
