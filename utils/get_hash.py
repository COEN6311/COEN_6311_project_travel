'''get_hash函数，这个函数用来避免存储明文密码. 在User/model中使用'''
'''此处用用sha3替代sha1以实现更高安全性'''

# from hashlib import sha1
from hashlib import sha3_256
def get_hash(str):
    '''取一个字符串的hash值'''
    sh = sha3_256()
    sh.update(str.encode('utf8'))
    return sh.hexdigest()