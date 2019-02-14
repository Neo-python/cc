from functools import wraps
from flask import session, request, redirect, render_template, url_for
from modules.admin.plugins import Token
from project_init import Redis


def logging_in(func):
    """登录状态权限验证装饰器"""

    @wraps(func)
    def inner(*args, **kwargs):
        if session.get('admin'):  # 判断登入状态,如果session有admin则正常执行函数
            return func(*args, **kwargs)
        else:
            # 从cookie中解密token,验证.
            token = request.cookies.get('token')
            if token:
                token = Token.string_decrypt(token)
                if token.verify_account():  # 验证token是否过期
                    session['admin'] = token.model.to_dict_()  # 写入用户信息至session状态
                    return func()
        return redirect(url_for('admin_bp.permission'))  # 没有登入状态,又没有cookie.则转跳到登入页面

    return inner


def reconciliation_verification(func):
    """二级密码权限装饰器,被装饰后的视图,需要通过二级密码验证后才可访问
    二级权限存储在redis中
    """

    @wraps(func)
    def inner(*args, **kwargs):
        admin_id = session['admin']['numbering']
        if Redis.get(f'sub_password_{admin_id}'):
            return func(*args, **kwargs)
        else:
            return render_template('reconciliation/verification.html')

    return inner
