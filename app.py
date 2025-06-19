from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://user:pass@localhost/evaluations')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class EvaluationForm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seafarer_id = db.Column(db.Integer)
    vessel_id = db.Column(db.Integer)
    quarter = db.Column(db.String(2))
    year = db.Column(db.SmallInteger)
    pdf_path = db.Column(db.String(255))
    status = db.Column(db.String(30), default='Received')
    signed_pdf_path = db.Column(db.String(255))


@app.route('/')
def index():
    forms = EvaluationForm.query.all()
    return render_template('index.html', forms=forms)


@app.route('/review/<int:eval_id>', methods=['POST'])
def review(eval_id):
    # placeholder sign integration
    form = EvaluationForm.query.get_or_404(eval_id)
    form.status = 'Signed'
    db.session.commit()
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run(debug=True)
