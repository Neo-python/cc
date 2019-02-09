from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
import smtplib
import config


def send(mode: str = 'database or message', message: str = None, to: str = "1026486983@qq.com") -> bool:
    server_ip = 'smtp.163.com'
    uid = config.emailId
    password = config.emailPassword

    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    if mode == 'database':
        msg = MIMEMultipart()
        msg.attach(MIMEText('这是来自数据库的备份文件', 'plain', 'utf-8'))
        with open('./model/DPM.db', 'rb') as f:
            # 设置附件的MIME和文件名，这里是png类型:
            mime = MIMEBase('database', 'db', filename='DPM.db')
            # 加上必要的头信息:
            mime.add_header('Content-Disposition', 'attachment', filename='DPM.db')
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            # 把附件的内容读进来:
            mime.set_payload(f.read())
            # 用Base64编码:
            encoders.encode_base64(mime)
            # 添加到MIMEMultipart:
            msg.attach(mime)
    elif mode == 'message':
        if message:
            msg = MIMEText(message, 'plain', 'utf-8')
        else:
            msg = MIMEText('数据备份功能已开启', 'plain', 'utf-8')
    else:
        return False
    msg['From'] = _format_addr(f'CC <{config.emailId}>')
    msg['To'] = _format_addr(f'管理员 <{to}>')
    msg['Subject'] = Header('CC服务器发来的信息……', 'utf-8').encode()
    try:
        server = smtplib.SMTP_SSL(server_ip, 465)
        server.set_debuglevel(1)
        server.login(uid, password)
        server.sendmail(uid, to, msg.as_string())
        server.quit()
        return True
    except BaseException as err:
        print(err)
        return False


one = {"status": True}


def send_jpg(uuid, status, qrcode, one=one, path="/var/www/myflask/wxpy.jpg", filename="wxpy.jpg",
             to="602049338@qq.com"):
    if one["status"]:
        with open("wxpy.jpg", "wb") as f:
            f.write(qrcode)
            f.close()
        serverip = 'smtp.163.com'
        uid = config.emailId
        password = config.emailPassword

        def _format_addr(s):
            name, addr = parseaddr(s)
            return formataddr((Header(name, 'utf-8').encode(), addr))

        msg = MIMEMultipart()
        msg.attach(MIMEText('这是来自数据库的备份文件', 'plain', 'utf-8'))
        with open(path, 'rb') as f:
            # 设置附件的MIME和文件名，这里是png类型:
            # 加上必要的头信息:
            mime = MIMEImage(f.read())
            mime.add_header('Content-Disposition', 'attachment', filename=filename)
            mime.add_header('Content-ID', '<0>')
            mime.add_header('X-Attachment-Id', '0')
            # 把附件的内容读进来:
            # 添加到MIMEMultipart:
            msg.attach(mime)

        msg['From'] = _format_addr('CC <g602049338@163.com>')
        msg['To'] = _format_addr('管理员 <602049338@qq.com>')
        msg['Subject'] = Header('CC服务器发来的信息……', 'utf-8').encode()

        server = smtplib.SMTP_SSL()
        server.set_debuglevel(1)
        server.connect(serverip, 465)
        server.login(uid, password)
        server.sendmail(uid, to, msg.as_string())
        server.quit()
        one["status"] = False
