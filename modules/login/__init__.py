from flask import session, request, redirect, render_template


def logging_in(func):
    def inner(*args, **kwargs):
        if session.get('admin'):  # 判断登入状态,如果session有admin则正常执行函数
            return func(*args, **kwargs)
        else:
            u = request.cookies.get('username')  # 判断是否有cookie,如果有,修改登入状态,然后正常执行函数
            if u:
                session['admin'] = u
                session['userid'] = request.cookies.get('userid')
                return func()
            else:  # 没有登入状态,又没有cookie.则转跳到登入页面
                return redirect('/login/')

    inner.__name__ = func.__name__  # 改变函数名inner为所装饰函数的函数名,使得前台url_for函数能正确区分
    return inner


def reconciliation_verification(func):
    def inner(*args, **kwargs):
        if session.get("verification"):
            return func(*args, **kwargs)
        else:
            return render_template('reconciliation-verification.html', login=session.get("admin"))

    inner.__name__ = func.__name__
    return inner
