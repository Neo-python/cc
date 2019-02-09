from flask import render_template


def write_error(err):
    from mail.qqmail import send
    with open('./error_log/ErrorLog.txt', "a+", encoding="utf-8") as f:
        f.write(err)
    send('message', err)


def error404(err=None):
    from flask import render_template, url_for
    if err:
        return render_template("404.html", err=err)
    else:
        err = {"title": "服务器错误", "text_head": "请检查您的操作是否正确", "text_tail": "秒后自动跳转回首页",
               'url': f'{url_for("hello_world")}'}
        return render_template("404.html", err=err)
