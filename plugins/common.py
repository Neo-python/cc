import rsa
import hashlib
from flask import render_template


def my_md5(content):
    """便捷版MD5加密"""
    try:
        m = hashlib.md5()
        m.update(content.encode('utf8'))
    except BaseException as err:
        print('common.my_md5:', err)
        return False
    return m.hexdigest()


class RsaKeys:
    """rsa加密 公私秘钥对象"""

    def __init__(self, public_filename='public.pem', private_filename='private.pem'):
        """还原公私秘钥"""
        with open(public_filename, 'r', encoding='utf-8') as pem:
            self.public = rsa.PublicKey.load_pkcs1(pem.read().encode())
        with open(private_filename, 'r', encoding='utf-8') as pem:
            self.private = rsa.PrivateKey.load_pkcs1(pem.read().encode())


class TransitionPage:

    def __init__(self, title='服务器发生错误', head='错误未知', tail='秒后,回到首页.', url='/', seconds=3):
        self.title = title
        self.head = head
        self.tail = tail if not url else '秒后,回到上一个页面.'
        self.url = url if url else '/'
        self.seconds = seconds

    def transition(self):
        err = {
            'title': self.title,
            'text_head': self.head,
            'text_tail': self.tail,
            'url': self.url,
            'seconds': self.seconds
        }
        return render_template('404.html', err=err)


def page_generator(current_page_num: int, max_num: int, url: str, url_args: dict = None, style: str = 'action'):
    """分页生成器
    :param current_page_num: 当前页,页数
    :param max_num: 最大页数
    :param url: 分页地址,带问号.例:www.python.org/?
    :param url_args: 地址参数
    :param style:选中页样式.
    :return: 渲染后的分页html内容.
    """
    if not url_args:
        url_args = {}
    args = ''
    for k, v in url_args.items():
        args += f'&{k}={v}'
    page_info = {
        'max_num': max_num,
        'url': url,
        'url_args': args,
        'current_page_num': current_page_num,
        'action': style
    }
    return render_template('page.html', data=page_info)


