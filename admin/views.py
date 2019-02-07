from admin import admin_bp
from flask import render_template, request, redirect, flash, session, make_response, url_for
from models.model import ADMIN, VALID, ErrorLog
from models import MD5
from datetime import datetime, timedelta
from mail.qqmail import send
from mail.myipaddress import ipaddress
from run import db, app
from error_log.mylog import error404, SetError
from login import login_required
from sqlalchemy import desc


@admin_bp.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get('admin'):
            return redirect('/')
        else:
            u = request.cookies.get('username')
            userid = request.cookies.get('userid')
            if u and userid:
                session['admin'] = u
                session['userid'] = userid
                return redirect('/')
            else:
                return render_template('login.html')
    else:
        ip = request.remote_addr
        uid = request.form.get('userid')
        password = request.form.get('password')
        remember = request.form.get('remember')
        user = ADMIN.query.filter(ADMIN.userid == uid, ADMIN.password == MD5(password)).first()
        if user:
            session['admin'] = user.username
            session['userid'] = user.id
            resp = make_response(redirect('/'))
            if remember == 'True':
                resp.set_cookie('username', user.username, expires=datetime.now()+timedelta(days=7))
                resp.set_cookie('userid', str(user.id), expires=datetime.now()+timedelta(days=7))
            else:
                pass
            #send('message', message=f"登入者帐号{uid}已成功登入ip:{ip},ip地址:{ipaddress(ip)}")
            #error_log = ErrorLog(f"登入者帐号{uid}已成功登入"f"ip:{ip},ip地址:{ipaddress(ip)}")
            #db.session.add(error_log)
            #db.session.commit()
            return resp
        else:
            flash('账号密码错误')
            send("message", message=f"登入者帐号密码输入错误.ip:{ip},ip地址:{ipaddress(ip)}")
            error_log = ErrorLog(f"登入者帐号密码输入错误.ip:{ip},ip地址:{ipaddress(ip)}\n尝试帐号{uid}")
            db.session.add(error_log)
            db.session.commit()
            return render_template('login.html')


@admin_bp.route('/dropout/')
def drop_out():
    session.pop('admin', None)
    session.pop('userid', None)
    resp = make_response(redirect('/login/'))
    resp.set_cookie('username', '', max_age=-1)
    return resp


@admin_bp.route('/change/key/', methods=["GET", "POST"])
@login_required
def change_key():
    """
    id:admin表id号,在登入时已经存在session
    original_pwd: 原来的密码
    new_pwd:新密码
    modify_obj:准备修改的数据库对象
    :return:
    """
    if request.method == "GET":
        return render_template('admin-change-key.html', login=session.get('admin'))
    else:
        id = session.get('userid')
        new_pwd = request.form.get('new_pwd')
        key = request.form.get('key')
        if key:
            v_obj = VALID.query.filter(VALID.id == id).first()
            if v_obj.text == key and (datetime.now() - v_obj.createtime).seconds < 600:
                modify_obj = ADMIN.query.filter(ADMIN.id == id).first()
                modify_obj.verification = MD5(new_pwd)
                v_obj.createtime = v_obj.createtime - timedelta(seconds=601)
                db.session.commit()
                session.pop('verification', None)
                return render_template('success.html')
            return SetError().err404()
        else:
            err = SetError(url=url_for('admin_bp.change_key'))
            original_pwd = request.form.get("original_pwd")
            if original_pwd and new_pwd:
                pwd = MD5(original_pwd)
                modify_obj = ADMIN.query.filter(ADMIN.id == id, ADMIN.verification == pwd).first()
                if modify_obj:
                    modify_obj.verification = MD5(new_pwd)
                    db.session.commit()
                    session.pop('verification', None)
                    return render_template('success.html')
                else:
                    err.head = '原口令错误,请重试'
                    return err.err404()
            else:
                return err.err404()


@admin_bp.route('/change/password/', methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template('admin-change-password.html', login=session.get('admin'))
    else:
        key = request.form.get('key')
        mail = request.form.get("mail")
        new_pwd = request.form.get('new_pwd')
        if key and mail:
            modify_obj = ADMIN.query.filter(ADMIN.mail == mail).first()
            v_obj = VALID.query.filter(VALID.userid == modify_obj.id).first()
            if v_obj.text == key and (datetime.now() - v_obj.createtime).seconds < 600:
                modify_obj.password = MD5(new_pwd)
                v_obj.createtime = v_obj.createtime - timedelta(seconds=601)
                db.session.commit()
                session.pop('admin', None)
                session.pop('userid', None)
                resp = make_response(render_template("success.html"))
                resp.set_cookie('username', '', max_age=-1)
                return resp
            else:
                return SetError(head="'链接超时,请重新请求.'").err404()
        else:
            err = SetError(url=url_for('admin_bp.change_password'))
            id = session.get('userid')
            original_pwd = request.form.get("original_pwd")
            if original_pwd and new_pwd:
                pwd = MD5(original_pwd)
                modify_obj = ADMIN.query.filter(ADMIN.id == id, ADMIN.password == pwd).first()
                if modify_obj:
                    modify_obj.password = MD5(new_pwd)
                    db.session.commit()
                    session.pop('admin', None)
                    session.pop('userid', None)
                    resp = make_response(render_template("success.html"))
                    resp.set_cookie('username', '', max_age=-1)
                    return resp
                else:
                    err.head = '原密码错误,请重试'
                    err.url = url_for("admin_bp.change_password")
                    return err.err404()
            else:
                return err.err404()


@admin_bp.route('/forget/key/')
@admin_bp.route('/forget/key/<key>/')
@login_required
def forget_key(key=None):
    userid = session.get('userid')
    err = SetError()
    if key:
        v_obj = VALID.query.filter(VALID.userid == userid).first()
        if v_obj:
            if v_obj.text == key and (datetime.now() - v_obj.createtime).seconds < 600:
                return render_template('admin-forget-key.html', login=session.get('admin'), key=key)
            else:
                err.head = '链接超时,请重新请求.'
                return err.err404()
        else:
            return err.err404()
    else:
        import random
        text = ""
        for i in range(27):
            text += chr(random.randint(97, 122))
        v_obj = VALID.query.filter(VALID.userid == userid).first()
        if v_obj:
            v_obj.text = text
            v_obj.createtime = datetime.now()
        else:
            v_obj = VALID(userid=userid, text=text, createtime=datetime.now())
            db.session.add(v_obj)
        send('message', "http://gocini.com"+url_for("admin_bp.forget_key")+text,
             to=ADMIN.query.filter(ADMIN.id == userid).first().mail)
        db.session.commit()
        return render_template('success.html')


@admin_bp.route('/forget/pwd/', methods=["GET", "POST"])
@admin_bp.route('/forget/<mail>/<pwd>/')
def forget_pwd(pwd=None, mail=None):
    if request.method == "POST":
        mail = request.form.get('mail')
        mail_obj = ADMIN.query.filter(ADMIN.mail == mail).first()
        if mail and mail_obj:
            import random
            text = ""
            for i in range(27):
                text += chr(random.randint(97, 122))
            v_obj = VALID.query.filter(VALID.id == mail_obj.id).first()
            if v_obj:
                v_obj.text = text
                v_obj.createtime = datetime.now()
            else:
                v_obj = VALID(userid=mail_obj.id, text=text, createtime=datetime.now())
                db.session.add(v_obj)
            send('message', "http://gocini.com/forget/" + f"{mail}/" + text, to=mail)
            db.session.commit()
            return render_template('success.html')
        else:
            return SetError(head="邮箱错误,请确认后重试.").err404()
    else:
        if pwd and mail:
            mail_obj = ADMIN.query.filter(ADMIN.mail == mail).first()
            v_obj = VALID.query.filter(VALID.userid == mail_obj.id).first()
            if v_obj.text == pwd and (datetime.now() - v_obj.createtime).seconds < 600:
                return render_template('admin-change-password.html', key=pwd, forget=True, mail=mail)
            else:
                return SetError(head='链接超时,请重新请求.').err404()
        else:
            return render_template("admin-forget-pwd.html")