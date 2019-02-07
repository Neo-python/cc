import hashlib


def MD5(str):
    try:
        m = hashlib.md5()
        m.update(str.encode('utf8'))
    except BaseException as err:
        print(err)
        return False
    return m.hexdigest()