import rsa
import hashlib


def my_md5(content):
    """便捷版MD5加密"""
    try:
        m = hashlib.md5()
        m.update(content.encode('utf8'))
    except BaseException as err:
        print(err)
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
