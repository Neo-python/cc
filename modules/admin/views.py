from flask import render_template, request, redirect, flash, session, make_response, url_for
from modules.admin import admin_bp
from model.models import Admin, Log
from mail.qqmail import send
from modules.admin.plugins import Token
from modules.login import logging_in
from plugins import common
from project_init import Redis
import config


@admin_bp.route('/login/', methods=['GET'])
def login():
    """登入请求视图"""
    if session.get('admin'):
        return redirect('/')
    else:
        token = request.cookies.get('token')
        if token:  # 在未能获取cookie的情况下,直接返回登录页面
            token = Token.string_decrypt(token=token)  # 解密token, 得到account与deadline两项加密数据
            token.verify_account()  # 验证account与deadline验证成功,token.model将为->Admin数据模型
            if token.model:  # 证明验证完成
                session['admin'] = token.model.to_dict_()  # 写入session状态
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

        # send('message', message=f"登入者帐号{account}已成功登入ip:{ip}", to=config.recipient)  # 发送邮件通知
        Log(f"登入者帐号{account}已成功登入"f"ip:{ip}").direct_commit_()  # 记录日志
        return resp
    else:
        flash('账号密码错误')
        # send("message", message=f"登入者帐号密码输入错误.ip:{ip}", to=config.recipient)
        Log(f"登入者帐号密码输入错误.ip:{ip}\n尝试帐号:{account}\n尝试密码:{password}").direct_commit_()
        return render_template('login.html')


@admin_bp.route('/sign_out/')
def sign_out():
    """退出登录状态
    清除redis二级密码缓存
    清除session状态
    清除cookie
    :return:
    """
    admin_id = session['admin']['numbering']
    Redis.set(f'sub_password_{admin_id}', '', ex=1)

    session.clear()  # 清除session状态

    resp = make_response(redirect('/login/'))  # 构建响应,跳转首页
    resp.set_cookie('token', '', max_age=-1)  # 主动退出,清除cookie.失去自动登录功能
    return resp


# csp:change sub password 更改二级密码
# __csp__:找回二级密码这部分使用的token,都统一加上的salt
@admin_bp.route('/csp/verify/', methods=["GET"])
@logging_in
def csp_verify_page():
    """验证旧二级密码页"""
    return render_template('admin/change_key.html')


@admin_bp.route('/csp/verify/', methods=['POST'])
@logging_in
def csp_verify():
    """验证旧二级密码 -> 生成token -> 植入新密码设置页"""
    original = request.form.get('original_pwd')  # 获取用户输入的旧的二级密码
    account = session['admin'].get('account')  # 获取当前用户账号信息

    if Admin.query.filter_by(account=account, verification=common.my_md5(original)).first():  # 确认旧二级密码
        # 设定token,防止用户使用登录cookie破解,account加入salt -> __csp__ token有效期为10分钟
        token = Token(f'__csp__{account}', deadline=Token.set_deadline({'minutes': 10}))
        return render_template('admin/change_key_input.html', token=token.encryption_to_string())
    else:  # 校验失败 回到校验页面.
        return redirect(url_for('admin_bp.csp_verify_page'))


@admin_bp.route('/csp/change/', methods=['POST'])
@logging_in
def csp_change():
    """修改二级密码"""
    token = Token.string_decrypt(token=request.form.get('token'))
    if not token.verify_salt(salt='__csp__'):  # 验证token,也获取加盐后的account
        return 'token invalid'
    pwd = request.form.get('new_pwd')

    account = token.original_text.replace('__csp__', '')  # 获得去盐后的账户
    assert account == session['admin']['account'], '申请账户与当前账户一致,防止篡改他人二级密码'

    # 修改二级密码,提交事务
    token.model.verification = common.my_md5(pwd)
    token.model.direct_update()
    return common.TransitionPage(title='二级密码变更成功', head='操作完成', seconds=10).transition()


@admin_bp.route('/csp/retrieve/input/', methods=['GET'])
def csp_retrieve_input():
    """通过邮件链接进入,忘记二级密码,输入新二级密码页面"""
    return render_template('admin/change_key_input.html', token=request.args.get('token'))


@admin_bp.route('/csp/retrieve/', methods=['GET'])
@logging_in
def csp_retrieve():
    """处理 -> 忘记二级密码,申请修改请求
    生成token -> 获取当前账户 -> 得到账户绑定邮箱 -> 发送修改页链接
    """
    account = session['admin'].get('account')  # 获取当前用户账号信息
    # 直接得到加密后的token
    token = Token(f'__csp__{account}', deadline=Token.set_deadline({'minutes': 30})).encryption_to_string()
    send(mode='message', message=url_for('admin_bp.csp_retrieve_input', token=token, _external=True),
         to=config.recipient)

    return common.TransitionPage(title='邮件发送成功,请到邮箱中查看', head='操作完成', seconds=15).transition()


# cp:change password
# __cp__:找回二级密码这部分使用的token,都统一加上的salt
@admin_bp.route('/cp/application/', methods=["GET"])
@logging_in
def cp_application():
    """修改密码申请"""
    return render_template('admin/change_password-application.html')


@admin_bp.route('/cp/verify/', methods=['POST'])
def cp_verify():
    """验证旧密码
    验证完成 -> 生成token植入设置新密码页面"""

    account = session['admin']['account']  # 获取当前用户账户
    original = request.form.get('original')  # 从表单中获取用户输入的旧密码

    if Admin.query.filter_by(account=account, password=common.my_md5(original)).first():
        token = Token(f'__cp__{account}', deadline=Token.set_deadline({'minutes': 10})).encryption_to_string()
        return render_template('admin/change_password-set_new_password.html', token=token)
    else:
        return common.TransitionPage(title='原密码错误', head='请求被驳回', url=url_for('admin_bp.cp_application')).transition()


@admin_bp.route('/change_password/', methods=['POST'])
def change_password():
    """修改密码"""
    token = Token.string_decrypt(request.form.get('token'))  # 解密token,如果token是伪造的,这一步就会触发异常

    if token.verify_salt(salt='__cp__'):  # 解密并且验证token
        token.model.password = request.form.get('new_pwd')  # 修改密码
        token.model.encryption_password().direct_update()  # 加密并且保存操作

        return common.TransitionPage('密码修改完成,请重新登录', '操作完成', url=url_for('admin_bp.sign_out')).transition()
    else:
        return common.TransitionPage('请求时效已过期,请重新申请!', '操作失败', url=url_for('admin_bp.cp_application'),
                                     seconds=10).transition()


@admin_bp.route('/cp/retrieve/', methods=["GET"])
def cp_retrieve_application():
    """申请找回密码页"""
    return render_template('admin/retrieve_password.html')


@admin_bp.route('/cp/retrieve/', methods=['POST'])
def cp_retrieve_mail():
    """通过账户绑定邮箱发送修改密码链接"""
    mail_account = request.form.get('mail_account')
    admin = Admin.query.filter_by(mail=mail_account).first()

    if admin:
        # 生成修改密码必要的token,因为是邮件验证修改,token时效延长至30分钟
        token = Token(f'__cp__{admin.account}', deadline=Token.set_deadline({'minutes': 30})).encryption_to_string()
        message = '↓↓↓↓↓您正在申请通过邮件修改CC登录密码,修改链接↓↓↓↓↓\n'
        message += url_for('admin_bp.cp_retrieve_redirect', _external=True, token=token)
        send('message', message=message, to=mail_account)  # 修改链接

        return common.TransitionPage(title='邮件发送成功,请到邮箱中查看', head='操作完成', seconds=15).transition()
    else:
        return common.TransitionPage('请求时效已过期,请重新申请!', '操作失败', url=url_for('admin_bp.cp_retrieve_application'),
                                     seconds=10).transition()


@admin_bp.route('/cp/retrieve/email/', methods=['GET'])
def cp_retrieve_redirect():
    """邮件修改链接,通过这里植入新密码设置页"""
    return render_template('admin/change_password-set_new_password.html', token=request.args.get('token'))
