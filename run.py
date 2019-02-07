from flask import Flask, render_template, session, redirect, url_for
from project_init import create_app, db

app = create_app()
db.init_app(app=app)

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
