from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from email.header import Header
from email.mime.base import MIMEBase
import config

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))
msg = MIMEMultipart()
msg['From'] = _format_addr('Neo <g602049338@163.com>')
msg['To'] = _format_addr('管理员 <602049338@qq.com>')
msg['Subject'] = Header('数据库备份文件……', 'utf-8').encode()
msg.attach(MIMEText('这是来自数据库的备份文件', 'plain', 'utf-8'))

with open('../models/DPM.db', 'rb') as f:
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


import smtplib
server = smtplib.SMTP()
server.connect('smtp.163.com', 25)
server.set_debuglevel(1)
server.login(config.emailId, config.emailPassword)
server.sendmail(config.emailId, "602049338@qq.com", msg.as_string())
server.quit()
