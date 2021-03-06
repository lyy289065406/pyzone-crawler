# -*- coding: utf-8 -*-
__author__ = 'EXP (272629724@qq.com)'
__date__ = '2018-03-30 22:53'


import src.main.py.config as cfg
import re
import execjs
from abc import ABCMeta, abstractmethod # python不存在抽象类的概念， 需要引入abc模块实现


class _HttpCookie(object):
    '''
    HTTP Response 单个 Set-Cookie 容器对象
    '''

    name = ''               # cookie键名
    value = ''              # cookie键值
    DOMAIN = "Domain"       # cookie域名
    domain = ''             # cookie域值
    PATH = "Path"           # cookie路径名
    path = ''               # cookie路径值
    EXPIRE = "Expires"      # cookie有效期名
    expire = ''             # cookie有效期值（英文GMT格式, 如: Thu, 01-Jan-1970 08:00:00 GMT+08:00）
    SECURE = "Secure"       # cookie属性：若出现该关键字表示该cookie只会在HTTPS中进行会话验证
    is_secure = False       # 是否出现了Secure关键字
    HTTPONLY = "HttpOnly"   # cookie属性：若出现该关键字表示该cookie无法被JS等脚本读取, 可防止XSS攻击
    is_http_only = False    # 是否出现了HttpOnly关键字


    def __init__(self, set_cookie):
        '''
        构造函数：拆解set_cookie中的各个参数
        :param set_cookie: HTTP响应头中的 Set-Cookie, 格式如：JSESSIONID=4F12EEF0E5CC6E8B239906B29919D40E; Domain=www.baidu.com; Path=/; Expires=Mon, 29-Jan-2018 09:08:16 GMT+08:00; Secure; HttpOnly;
        :return: None
        '''
        self.name = ''
        self.value = ''
        self.domain = ''
        self.path = ''
        self.expire = ''
        self.is_secure = False
        self.is_http_only = False

        for idx, kvs in enumerate(set_cookie.split(';')):
            kv = kvs.split('=')
            size = len(kv)
            if size == 2 :
                key = kv[0].strip()
                val = kv[1].strip()

                if idx == 0 :
                    self.name = key
                    self.value = val

                else:
                    if self.DOMAIN.upper() == key.upper():
                        self.domain = val

                    elif self.PATH.upper() == key.upper():
                        self.path = val

                    elif self.EXPIRE.upper() == key.upper():
                        self.expire = val

            elif size == 1 :
                key = kv[0].strip()

                if self.SECURE.upper() == key.upper():
                    self.is_secure = True

                elif self.HTTPONLY.upper() == key.upper():
                    self.is_http_only = True


    def is_vaild(self):
        '''
        判断当前所解析的Cookie是否有效
        :return: True:有效, False:无效
        '''
        return not not self.name.strip()


    def to_nv(self):
        '''
        生成该Cookie的名值对.
        在与服务端校验cookie会话时, 只需对name与value属性进行校验, 其他属性无需校验, 保存在本地即可.
        :return: name=value
        '''
        return '%s=%s' % (self.name, self.value) if self.is_vaild() else ''


    def to_header(self):
        '''
        生成该cookie在Header中的字符串形式.
        :return: 形如：JSESSIONID=4F12EEF0E5CC6E8B239906B29919D40E; Domain=www.baidu.com; Path=/; Expires=Mon, 29-Jan-2018 09:08:16 GMT+08:00; Secure; HttpOnly;
        '''
        return '%(name)s=%(value)s; %(DOMAIN)s=%(domain)s; %(PATH)s=%(path)s; %(EXPIRE)s=%(expire)s; %(SECURE)s %(HTTPONLY)s' % {
            'name' : self.name,
            'value' : self.value,
            'DOMAIN' : self.DOMAIN,
            'domain' : self.domain,
            'PATH' : self.PATH,
            'path' : self.path,
            'EXPIRE' : self.EXPIRE,
            'expire' : self.expire,
            'SECURE' : ('%s;' % self.SECURE) if self.is_secure else '',
            'HTTPONLY' : ('%s;' % self.HTTPONLY) if self.is_http_only else ''
        }


    def __eq__(self, other):
        '''
        用于判断两个_HttpCookie对象是否相同（仅通过键名name判断）
        :return:
        '''
        return isinstance(other, _HttpCookie) and (self.name == other.name)


    def __repr__(self):
        '''
        相当于toString方法
        :return:
        '''
        return self.to_header()



class HttpCookie(object):
    '''
    HTTP Response 多个 Set-Cookie 容器对象
    '''
    __metaclass__ = ABCMeta # 定义为抽象类

    cookies = None    # 存储多个_HttpCookie的列表


    def __init__(self, set_cookies):
        '''
        构造函数：拆解set_cookies中的多个set_cookie并解析
        :param set_cookies: HTTP响应头中的 Set-Cookie集合, 使用 ;, 分隔
        :return: None
        '''
        self.cookies = []
        self.adds(set_cookies)


    def adds(self, set_cookies):
        '''
        拆解set_cookies中的多个set_cookie并解析
        :param set_cookies: HTTP响应头中的 Set-Cookie集合, 使用 ;, 分隔
        :return: None
        '''
        for set_cookie in set_cookies.split(';,'):
            self.add(set_cookie)


    def add(self, set_cookie):
        '''
        添加一个set-cookie串
        :param set_cookie: HTTP响应头中的 Set-Cookie, 格式如：JSESSIONID=4F12EEF0E5CC6E8B239906B29919D40E; Domain=www.baidu.com; Path=/; Expires=Mon, 29-Jan-2018 09:08:16 GMT+08:00; Secure; HttpOnly;
        :return: True:添加成功; False:添加失败
        '''
        is_ok = False
        cookie = _HttpCookie(set_cookie)
        if cookie.is_vaild() and (cookie not in self.cookies) :
            if self.take_cookie_nve(cookie.name, cookie.value, cookie.expire):
                self.cookies.append(cookie)
                is_ok = True
        return is_ok


    @abstractmethod
    def take_cookie_nve(self, name, value, expire):
        '''
        在添加新的set-cookie时会触发此方法, 用于提取某些特殊的名值对作为常量
        :param name: cookie键名
        :param value: cookie键值
        :param expire: cookie有效期
        :return: True:保留该cookie; False;丢弃该cookie
        '''
        # TODO in sub class
        return True


    def is_vaild(self):
        '''
        判断当前所解析的Cookie集是否有效
        :return: True:有效, False:无效
        '''
        return len(self.cookies) > 0


    def to_nv(self):
        '''
        生成所有cookie的名值对列表(分号分隔)
        :return: cookie的名值对列表(分号分隔)
        '''
        return '; '.join(cookie.to_nv() for cookie in self.cookies)


    def to_header(self):
        '''
        生成所有cookie在Header中的字符串形式(换行符分隔)
        :return: 形如：
                    sid=iji8r99z ; Domain=www.baidu.com ; Path=/ ; Expires=Thu, 31-Jan-2019 21:18:46 GMT+08:00 ;
                    JSESSIONID=87E6F83AD8F5EC3C1BF1B08736E8D28A ; Domain= ; Path=/ ; Expires=Wed, 31-Jan-2018 21:18:43 GMT+08:00 ; HttpOnly ;
                    DedeUserID__ckMd5=14ad42f429c3e8b7 ; Domain=www.baidu.com ; Path=/ ; Expires=Fri, 02-Mar-2018 21:18:46 GMT+08:00 ;
        '''
        return '\r\n'.join(cookie.to_header() for cookie in self.cookies)


    def __repr__(self):
        '''
        相当于toString方法
        :return:
        '''
        return self.to_header()



class QQCookie(HttpCookie):
    '''
    QQ空间Cookie专用解析器
    '''

    SIG_KEY = 'pt_login_sig'    # 用于登陆QQ的SIG属性键
    sig = ''                    # 用于登陆QQ的SIG码
    VCODE_KEY = "verifysession" # 登陆验证码的校验码的属性键
    verifysession = ''          # 登陆验证码的校验码
    UIN_KEY = "uin"             # 当前所登陆QQ号的cookie属性键
    uin = ''                    # 当前登陆账号(即登陆的QQ号)
    PSKEY_KEY = "p_skey"        # 用于生成GTK的cookie属性键
    gtk = ''                    # 每次登陆QQ空间都会通过p_skey生成一个固定的GTK, 用于其他页面操作
    qzone_token = ''            # 每次登陆QQ空间都会生成一个固定的qzonetoken, 用于其他页面操作
    nickName = ''               # QQ昵称


    def __init__(self, set_cookies=''):
        '''
        构造函数：拆解set_cookies中的多个set_cookie并解析
        :param set_cookies: HTTP响应头中的 Set-Cookie集合, 使用 ;, 分隔
        :return: None
        '''
        self.sig = ''
        self.verifysession = ''
        self.uin = ''
        self.gtk = ''
        self.qzone_token = ''
        nickName = ''

        super(QQCookie, self).__init__(set_cookies)


    def take_cookie_nve(self, name, value, expire):
        '''
        在添加新的set-cookie时会触发此方法, 用于提取某些特殊的名值对作为常量
        :param name: cookie键名
        :param value: cookie键值
        :param expire: cookie有效期
        :return: True:保留该cookie; False;丢弃该cookie
        '''
        is_keep = True

        if value.strip() == '' :
            is_keep = False

        elif self.SIG_KEY.upper() == name.upper():
            self.sig = value

        elif self.VCODE_KEY.upper() == name.upper():
            self.verifysession = value

        elif self.UIN_KEY.upper() == name.upper():
            self.uin = re.sub('^[o|O]', '', value)
            self.uin = re.sub('^0*', '', self.uin)
            self.nickName = self.uin

        elif self.PSKEY_KEY.upper() == name.upper():
            self.gtk = self.to_gtk(value)

        return is_keep


    def to_gtk(self, p_skey):
        '''
        通过 skey 计算GTK码.
        ---------------------------------
        先用 外置的JS算法 计算 GTK， 当使用 JS计算失败 时，才使用内置算法计算。
        外置JS算法主要是为了在QQ更新了GTK算法情况下，可以对应灵活修改。
        :param p_skey: 从登陆cookie中提取的标识(每次登陆时随机生成)
        :return: GTK码
        '''
        try:
            with open(cfg.GTK_JS_PATH, encoding=cfg.DEFAULT_CHARSET) as script :
                js = execjs.compile(script.read())
                gtk = js.call(cfg.GTK_METHOD, p_skey)
        except:
            hash = 5381
            for c in p_skey :
                hash += (hash << 5) + ord(c)
            gtk = str(hash & 0x7fffffff)

        return gtk
