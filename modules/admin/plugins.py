"""管理员模块插件库"""
import rsa, datetime, base64
from plugins import common
from model.models import Admin


class CookieToken:
    """登录缓存秘钥"""

    def __init__(self, account: str, deadline: datetime.datetime):
        self.account = account
        self.deadline = deadline

    def encryption(self) -> bytes:
        """加密"""
        keys = common.RsaKeys()
        message = f'{self.account},{self.deadline.strftime("%Y-%m-%d %H:%M:%S")}'
        token = rsa.encrypt(message.encode(), keys.public)
        return token

    def encryption_to_string(self) -> str:
        """返回utf8格式内容"""
        return base64.b64encode(self.encryption()).decode()

    @staticmethod
    def decrypt(token: bytes):
        """解密"""
        keys = common.RsaKeys()
        message = rsa.decrypt(crypto=token, priv_key=keys.private).decode()
        account, deadline = message.split(',')
        return CookieToken(account=account, deadline=datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def string_decrypt(token: str):
        """utf8格式内容解密"""
        return CookieToken.decrypt(base64.b64decode(token.encode()))

    def verify(self):
        """验证账户与期限"""
        now = datetime.datetime.now()
        if now < self.deadline:
            return Admin.query.filter_by(account=self.account).first()
        else:
            return False
