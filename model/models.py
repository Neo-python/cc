from datetime import datetime
from plugins.common import my_md5
from project_init import db
import pickle


class Common(object):

    def direct_add_(self):
        """直接添加事务"""
        db.session.add(self)

    def direct_commit_(self):
        """直接提交"""
        self.direct_add_()
        db.session.commit()


class Admin(db.Model):
    """管理员模型"""
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(length=50), unique=True, comment='管理员账户')
    password = db.Column(db.String(50), comment='密码')
    nickname = db.Column(db.String(20), comment='昵称')
    mail = db.Column(db.String, unique=True, comment='邮箱账户')
    verification = db.Column(db.String, comment='相当于二级密码')
    create_time = db.Column(db.DATETIME, onupdate=datetime.now, comment='创建时间')

    def __init__(self, account, password, nickname, mail, verification=None):
        self.account = account
        self.password = password
        self.nickname = nickname
        self.mail = mail
        self.verification = verification

    def encryption_password(self):
        """加密密码"""
        self.password = my_md5(self.password)

    def to_dict_(self):
        """返回dict类型数据"""
        return {'numbering': self.id, 'account': self.account, 'nickname': self.nickname, 'mail': self.mail}

    def __repr__(self):
        return f'{self.id} {self.username}'


class VALID(db.Model):
    __tablename__ = 'valid'
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, unique=True)
    text = db.Column(db.String)
    createtime = db.Column(db.DateTime)

    def __inif__(self, userid, text, createtime):
        self.userid = userid
        self.text = text
        self.createtime = createtime

    def __repr__(self):
        return f'{self.id}:{self.text}:{self.createtime}'


class CITYS(db.Model):
    __tablename__ = 'citys'
    area_id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer)
    area_name = db.Column(db.String(30))
    area_type = db.Column(db.Integer)
    py_name = db.Column(db.String)

    def __init__(self, area_id, parent_id, area_name, area_type, py_name=None):
        self.area_id = area_id
        self.parent_id = parent_id
        self.area_name = area_name
        self.area_type = area_type
        self.py_name = py_name

    def __repr__(self):
        return f'area_id:{self.area_id},parent_id:{self.parent_id},area_name:{self.area_name}'


class MY_FORM(db.Model):
    __tablename__ = 'my_form'
    id = db.Column(db.Integer, primary_key=True)
    province = db.Column(db.Integer, db.ForeignKey('citys.area_id'))
    city = db.Column(db.Integer, db.ForeignKey('citys.area_id'))
    area = db.Column(db.Integer, db.ForeignKey('citys.area_id'))
    user = db.Column(db.String)
    phone = db.Column(db.String)
    userunit = db.Column(db.String)
    telephone = db.Column(db.String)
    payment = db.Column(db.Integer)
    receipt = db.Column(db.Integer)
    client = db.Column(db.String)
    clientphone = db.Column(db.String)
    price = db.Column(db.Integer)
    remarks = db.Column(db.String)
    print_status = db.Column(db.Boolean)
    other = db.Column(db.Integer)
    reprice = db.Column(db.Integer)
    income = db.Column(db.Integer)
    reconciliation_status = db.Column(db.Boolean)
    reconciliation_id = db.Column(db.Integer)
    createtime = db.Column(db.DateTime)

    province_name = db.relationship("CITYS", backref=db.backref('provinces', lazy='dynamic'), foreign_keys=[province])
    city_name = db.relationship("CITYS", backref=db.backref('citys', lazy='dynamic'), foreign_keys=[city])
    area_name = db.relationship("CITYS", backref=db.backref('areas', lazy='dynamic'), foreign_keys=[area])

    def __init__(self, province=None, city=None, area=None, user=None, phone=None, userunit=None, telephone=None,
                 payment=None, receipt=None, client=None, clientphone=None, price=None, remarks=None, print_status=0,
                 other=0, reprice=0, income=0, reconciliation_status=None, createtime=None):
        self.province = province
        self.city = city
        self.area = area
        self.user = user
        self.phone = phone
        self.userunit = userunit
        self.telephone = telephone
        self.payment = payment
        self.receipt = receipt
        self.client = client
        self.clientphone = clientphone
        self.price = price
        self.remarks = remarks
        self.print_status = print_status
        self.other = other
        self.reprice = reprice
        self.income = income
        self.reconciliation_status = reconciliation_status
        self.createtime = datetime.now() if not createtime else createtime

    def __repr__(self):
        return f'id:{self.id} user:{self.user} phone:{self.phone} ' \
            f'client:{self.client} clientphone:{self.clientphone}'


class PDN(db.Model):
    __tablename__ = 'productname'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    sorting = db.Column(db.Integer, unique=True)

    def __init__(self, name, sorting):
        self.name = name
        self.sorting = sorting

    def __repr__(self):
        return f'{self.name}'


class ORDER_DETALILS(db.Model):
    __tablename__ = 'orderdetalils'

    id = db.Column(db.Integer, primary_key=True)
    oid = db.Column(db.Integer, db.ForeignKey('my_form.id'))  # 订单id
    pid = db.Column(db.Integer, db.ForeignKey('productname.id'))  # 产品类型id
    count = db.Column(db.Integer)
    measure = db.Column(db.Integer)
    measureunit = db.Column(db.Integer)

    oder_id = db.relationship('MY_FORM', backref=db.backref('oids', lazy='dynamic'), foreign_keys=[oid])
    productname = db.relationship("PDN", backref=db.backref('pids', lazy='dynamic'), foreign_keys=[pid])

    def __init__(self, oid, pid, count, measure, measureunit):
        self.oid = oid
        self.pid = pid
        self.count = count
        self.measure = measure
        self.measureunit = measureunit

    def __repr__(self):
        return f'货物名称:{self.productname} 重量体积:{self.measure} 单位:{self.measureunit}'


class ORDER_FORM(db.Model):
    __tablename__ = 'oderform'

    id = db.Column(db.Integer, primary_key=True)
    lists = db.Column(db.String)
    status = db.Column(db.Integer)
    remarks = db.Column(db.String)
    price_sum = db.Column(db.Integer)
    modify_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime)

    def __init__(self, lists=None, status=0, modify_time=None, remarks="", price_sum=0):
        self.lists = pickle.dumps(lists)
        self.status = status
        self.modify_time = modify_time
        self.create_time = datetime.now()
        self.remarks = remarks
        self.price_sum = price_sum

    def __repr__(self):
        return f'id:{self.id} lists:{pickle.loads(self.lists)}'


class REMARK(db.Model):
    __tablename__ = "remark"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    sorting = db.Column(db.Integer, unique=True)

    def __init__(self, text, sorting):
        self.text = text
        self.sorting = sorting

    def __repr__(self):
        return f"id:{self.id} text:{self.text} sorting:{self.sorting}"


class Log(db.Model, Common):
    __tablename__ = "log"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String)
    create_time = db.Column(db.DateTime, default=datetime.now, comment='记录时间')
    status = db.Column(db.Boolean)
    genre = db.Column(db.SmallInteger, comment='日志类型,0:普通日志,1:错误日志')

    def __init__(self, content=None, status=True, genre=0, *args, **kwargs):
        super(Log, self).__init__(*args, **kwargs)
        self.content = content
        self.status = status
        self.genre = genre

    def __repr__(self):
        return f"{self.content} : {self.status}"
