from flask import Flask, render_template, session, redirect, url_for
from login import login_required
from mail.qqmail import send




app = Flask(__name__)
app.secret_key = "my name is neo"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./models/DPM.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_ECHO'] = False
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
from admin import admin_bp
from my_form import form_bp
from manage import manage
from reconciliation import reconciliation_bp
app.register_blueprint(admin_bp)
app.register_blueprint(form_bp)
app.register_blueprint(manage)
app.register_blueprint(reconciliation_bp, url_prefix="/reconciliation")


@app.route('/')
def hello_world():
    print('ok')
    username = session.get('admin')
    if username:
        return render_template('base.html', login=username)
    else:
        return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=False)
