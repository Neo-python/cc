from flask import render_template


def write_error(err):
    from mail.qqmail import send
    from datetime import datetime
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


class SetError():

    def __init__(self, title='服务器发生错误', head='错误未知', tail='秒后,回到首页.', url=None, seconds=3):
        self.title = title
        self.head = head
        self.tail = tail if not url else '秒后,回到上一个页面.'
        self.url = url if url else '/'
        self.seconds = seconds

    def err404(self):
        err = {
            'title': self.title,
            'text_head': self.head,
            'text_tail': self.tail,
            'url': self.url,
            'seconds': self.seconds
        }
        return render_template('404.html', err=err)
