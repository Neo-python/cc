import datetime
from flask import render_template, request, redirect, flash, session, make_response, url_for
from modules.admin import admin_bp
from model.models import Admin, VALID, Log
from mail.qqmail import send
from project_init import db
from modules.admin.plugins import Token
from plugins import common
from modules.login import logging_in


@admin_bp.route('/login/', methods=['GET'])
def login():
    """登入请求视图"""
    if session.get('admin'):
        return redirect('/')
    else:
        token = request.cookies.get('token')
        if token:  # 在未能获取cookie的情况下,直接返回登录页面
            token = Token.string_decrypt(token=token)  # 解密token, 得到account与deadline两项加密数据
            admin = token.verify_account()  # 验证account与deadline验证成功将返回Admin数据模型
            if admin:  # 证明验证完成
                session['admin'] = admin.to_dict_()  # 写入session状态
                return redirect('/')  # 跳转主页
        return render_template('login.html')  # 返回登录页


@admin_bp.route('/verify_account/', methods=['POST'])
def verify_account():
    """验证账户密码"""
    ip = request.remote_addr
    account = request.form.get('account')
    password = request.form.get('password')
    admin = Admin.query.filter(Admin.account == account, Admin.password == common.my_md5(password)).first()  # 验证数据

    if admin:  # 证明验证成功
        session['admin'] = admin.to_dict_()  # 写入session状态
        resp = make_response(redirect('/'))  # 构建响应
        if request.form.get('remember') == 'True':  # 用户需要记住密码
            deadline = Token.set_deadline({'days': 7})  # 过期时间为7天
            token = Token(admin.account, deadline=deadline)  # 将账户与cookie期限加密
            resp.set_cookie('token', token.encryption_to_string(), expires=deadline)  # cookie加入响应

        send('message', message=f"登入者帐号{account}已成功登入ip:{ip}")  # 发送邮件通知
        Log(f"登入者帐号{account}已成功登入"f"ip:{ip}").direct_commit_()  # 记录日志
        return resp
    else:
        flash('账号密码错误')
        send("message", message=f"登入者帐号密码输入错误.ip:{ip}")
        Log(f"登入者帐号密码输入错误.ip:{ip}\n尝试帐号:{account}\n尝试密码:{password}").direct_commit_()
        return render_template('login.html')


@admin_bp.route('/dropout/')
def drop_out():
    """退出登录状态"""
    session.pop('admin', None)  # 清除session状态
    resp = make_response(redirect('/login/'))  # 构建响应,跳转首页
    resp.set_cookie('token', '', max_age=-1)  # 主动退出,清除cookie.失去自动登录功能
    return resp


# csp:change sub password 更改二级密码
@admin_bp.route('/csp/verify/', methods=["GET"])
@logging_in
def csp_verify_page():
    """验证旧二级密码页"""
    return render_template('admin/admin-change-key.html')


@admin_bp.route('/csp/verify/', methods=['POST'])
@logging_in
def csp_verify():
    """验证旧二级密码"""
    original = request.form.get('original_pwd')  # 获取用户输入的旧的二级密码
    account = session['admin'].get('account')  # 获取当前用户账号信息
    if Admin.query.filter_by(account=account, verification=common.my_md5(original)).first():  # 确认旧二级密码
        # 设定token,防止用户使用登录cookie破解,account加入salt -> __csp__ token有效期为10分钟
        token = Token(f'__csp__{account}', deadline=Token.set_deadline({'minutes': 10}))
        return render_template('admin/admin-change-key-input.html', token=token.encryption_to_string())
    else:  # 校验失败 回到校验页面.
        return redirect(url_for('admin_bp.csp_verify_page'))


@admin_bp.route('/csp/change/', methods=['POST'])
@logging_in
def csp_change():
    """修改二级密码"""
    token = Token.string_decrypt(token=request.form.get('token'))
    if not token.verify_csp():  # 验证token,也获取加盐后的account
        return 'token invalid'
    pwd = request.form.get('new_pwd')

    account = token.original_text.replace('__csp__', '')  # 获得去盐后的账户
    assert account == session['admin']['account'], '申请账户与当前账户一致,防止篡改他人二级密码'
    # 修改二级密码,提交事务
    Admin.query.filter_by(account=account).update({'verification': common.my_md5(pwd)})
    db.session.commit()
    return common.TransitionPage(title='二级密码变更成功', head='操作完成', seconds=10).transition()


@admin_bp.route('/csp/retrieve/input/', methods=['GET'])
def csp_retrieve_input():
    """通过邮件链接进入,忘记二级密码,输入新二级密码页面"""
    return render_template('admin/admin-change-key-input.html', token=request.args.get('token'))


@admin_bp.route('/csp/retrieve/', methods=['GET'])
@logging_in
def csp_retrieve():
    """处理 -> 忘记二级密码,申请修改请求
    生成token -> 获取当前账户 -> 得到账户绑定邮箱 -> 发送修改页链接
    """
    account = session['admin'].get('account')  # 获取当前用户账号信息
    token = Token(f'__csp__{account}', deadline=Token.set_deadline({'minutes': 30})).encryption_to_string()
    send(mode='message', message=url_for('admin_bp.csp_retrieve_input', token=token, _external=True),
         to='g602049338@icloud.com')
    return common.TransitionPage(title='邮件发送成功,请到邮箱中查看', head='操作完成', seconds=15).transition()


@admin_bp.route('/change/password/', methods=["GET", "POST"])
def change_password():
    if request.method == "GET":
        return render_template('admin/admin-change-password.html', login=session.get('admin'))
    else:
        key = request.form.get('key')
        mail = request.form.get("mail")
        new_pwd = request.form.get('new_pwd')
        if key and mail:
            modify_obj = Admin.query.filter(Admin.mail == mail).first()
            v_obj = VALID.query.filter(VALID.userid == modify_obj.id).first()
            if v_obj.text == key and (datetime.now() - v_obj.createtime).seconds < 600:
                modify_obj.password = common.my_md5(new_pwd)
                v_obj.createtime = v_obj.createtime - datetime.timedelta(seconds=601)
                db.session.commit()
                session.pop('admin', None)
                session.pop('userid', None)
                resp = make_response(render_template("success.html"))
                resp.set_cookie('username', '', max_age=-1)
                return resp
            else:
                return common.TransitionPage(head="'链接超时,请重新请求.'").transition()
        else:
            err = common.TransitionPage(url=url_for('admin_bp.change_password'))
            id = session.get('userid')
            original_pwd = request.form.get("original_pwd")
            if original_pwd and new_pwd:
                pwd = common.my_md5(original_pwd)
                modify_obj = Admin.query.filter(Admin.id == id, Admin.password == pwd).first()
                if modify_obj:
                    modify_obj.password = common.my_md5(new_pwd)
                    db.session.commit()
                    session.pop('admin', None)
                    session.pop('userid', None)
                    resp = make_response(render_template("success.html"))
                    resp.set_cookie('username', '', max_age=-1)
                    return resp
                else:
                    err.head = '原密码错误,请重试'
                    err.url = url_for("admin_bp.change_password")
                    return err.transition()
            else:
                return err.transition()


@admin_bp.route('/forget/key/')
@admin_bp.route('/forget/key/<key>/')
@logging_in
def forget_key(key=None):
    userid = session.get('userid')
    err = common.TransitionPage()
    if key:
        v_obj = VALID.query.filter(VALID.userid == userid).first()
        if v_obj:
            if v_obj.text == key and (datetime.now() - v_obj.createtime).seconds < 600:
                return render_template('admin/admin-forget-key.html', login=session.get('admin'), key=key)
            else:
                err.head = '链接超时,请重新请求.'
                return err.transition()
        else:
            return err.transition()
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
        send('message', "http://gocini.com" + url_for("admin_bp.forget_key") + text,
             to=Admin.query.filter(Admin.id == userid).first().mail)
        db.session.commit()
        return render_template('success.html')


@admin_bp.route('/forget/pwd/', methods=["GET", "POST"])
@admin_bp.route('/forget/<mail>/<pwd>/')
def forget_pwd(pwd=None, mail=None):
    if request.method == "POST":
        mail = request.form.get('mail')
        mail_obj = Admin.query.filter(Admin.mail == mail).first()
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
            return common.TransitionPage(head="邮箱错误,请确认后重试.").transition()
    else:
        if pwd and mail:
            mail_obj = Admin.query.filter(Admin.mail == mail).first()
            v_obj = VALID.query.filter(VALID.userid == mail_obj.id).first()
            if v_obj.text == pwd and (datetime.now() - v_obj.createtime).seconds < 600:
                return render_template('admin/admin-change-password.html', key=pwd, forget=True, mail=mail)
            else:
                return common.TransitionPage(head='链接超时,请重新请求.').transition()
        else:
            return render_template("admin/admin-forget-pwd.html")
