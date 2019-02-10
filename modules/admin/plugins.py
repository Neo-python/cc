"""管理员模块插件库"""
import rsa, datetime, base64
from plugins import common
from model.models import Admin


class Token:
    """登录缓存秘钥"""

    def __init__(self, original_text: str, deadline: datetime.datetime):
        """
        :param original_text: token信息,一般情况为账户
        :param deadline:token过期时限,一般情况下,可以使用set_deadline快速设置
        """
        self.original_text = original_text
        self.deadline = deadline
        self.model = None

    @staticmethod
    def set_deadline(deadline: dict) -> datetime.datetime:
        """快速设置期限
        :param deadline: dict类型,example:{'days':-1} or {'seconds':10}
        :return:
        """
        return datetime.datetime.now() + datetime.timedelta(**deadline)

    def encryption(self) -> bytes:
        """加密"""
        keys = common.RsaKeys()
        message = f'{self.original_text},{self.deadline.strftime("%Y-%m-%d %H:%M:%S")}'
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
        original_text, deadline = message.split(',')
        return Token(original_text=original_text, deadline=datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S"))

    @staticmethod
    def string_decrypt(token: str):
        """utf8格式内容解密"""
        return Token.decrypt(base64.b64decode(token.encode()))

    def verify_account(self) -> bool:
        """cookie登录状态缓存验证:验证账户与期限"""
        now = datetime.datetime.now()
        if now < self.deadline:
            self.model = Admin.query.filter_by(account=self.original_text).first()
            return True
        else:
            return False

    def verify_salt(self, salt: str = '') -> bool:
        """验证二级密码修改权限
        :param salt: 不同事务,需要加上事务专有的salt,以防止token调换破解程序.
        """
        now = datetime.datetime.now()

        if now < self.deadline:
            self.model = Admin.query.filter_by(account=self.original_text.replace(salt, '')).first()
            return True
        else:
            return False
