import pickle
import datetime
from flask import request, render_template, redirect, url_for, session, jsonify
from sqlalchemy import text, desc
from modules.reconciliation import reconciliation_bp
from modules.login import logging_in, reconciliation_verification
from model.models import ORDER_FORM, db, MY_FORM, Admin, PDN
from error_log.mylog import error404
from plugins import common


@reconciliation_bp.route('/<int:id>/')
@reconciliation_bp.route('/')
@logging_in
@reconciliation_verification
def index(id=1):
    db_obj = ORDER_FORM.query.order_by(
        desc(ORDER_FORM.create_time)).paginate(id, per_page=10)
    obj = db_obj.items
    page = db_obj.iter_pages(left_edge=0, left_current=2,
                             right_current=3, right_edge=0)
    pages = [i for i in page if i]
    page_max = db_obj.pages
    if page_max >= 5:
        if id <= 3:
            pages = [i for i in range(1, 6)]
        if page_max - id <= 2:
            pages = [page_max - i for i in range(5)]
        pages.sort()
    for i in obj:
        i.lists = pickle.loads(i.lists)
    db.session.close()
    return render_template('reconciliation-index.html', login=session.get("admin"), obj=obj, pages=pages,
                           page_max=page_max, current=id)


@reconciliation_bp.route('/calculation/<int:uid>/')
@logging_in
@reconciliation_verification
def calculation(uid=None):
    """
    :param uid:
    :return:
    obj_db: 对账单对象
    obj:订单列表[1,2,3]
    mdb:obj查询到的对象
    """
    if uid:
        obj_db = ORDER_FORM.query.filter(ORDER_FORM.id == uid).first()
        obj = pickle.loads(obj_db.lists)
        if len(obj) <= 0:
            db.session.delete(obj_db)
            db.session.commit()
            db.session.close()
            return redirect(url_for("reconciliation_bp.index"))
        mdb = MY_FORM.query.filter(
            text(' or '.join([" MY_FORM.id ==" + str(i) for i in obj]))).all()
    return render_template('reconciliation-calculation.html', login=session.get('admin'), db=mdb, uid=uid,
                           lists=[i for i in obj], obj=obj_db)


@reconciliation_bp.route('/result/', methods=["POST"])
@logging_in
@reconciliation_verification
def reconciliation_result():
    obj = request.form.to_dict()
    lists = eval(obj.get('lists'))
    for i in lists:
        m = MY_FORM.query.filter(MY_FORM.id == i).first()
        m.remarks = obj.get(f"remark{i}")
        m.reprice = obj.get(f"payment0{i}")
        m.price = obj.get(f"payment1{i}")
        m.other = obj.get(f"other{i}")
        m.income = obj.get(f"count{i}")
        m.reconciliation_status = True
    o_obj = ORDER_FORM.query.filter(
        ORDER_FORM.id == int(obj.get("uid"))).first()
    o_obj.remarks = obj.get("remarks")
    o_obj.price_sum = obj.get("sum")
    o_obj.modify_time = datetime.datetime.now()
    o_obj.status = 1
    db.session.commit()
    return redirect(url_for("reconciliation_bp.index"))


@reconciliation_bp.route("/del/<int:uid>/")
@reconciliation_verification
def reconciliation_del(uid=None):
    if uid:
        for i in MY_FORM.query.filter(MY_FORM.reconciliation_id == uid).all():
            i.reconciliation_id = None
        db.session.delete(ORDER_FORM.query.filter(
            ORDER_FORM.id == uid).first())
        db.session.commit()
        return redirect(url_for("reconciliation_bp.index"))
    else:
        return "no"


@reconciliation_bp.route("/add/", methods=["POST"])
@reconciliation_verification
def reconciliation_add():
    """
    obj:前台表单对象
    oid:order_form id 对账表id
    addid: MY_FORM id 新增id
    err: 在404页面的错误提示 text_head与text_tail拼接成跳转倒计时
    lists: 对账单,单号集合.在lists完成增删改后再覆盖oid_obj.lists
    :return:
    """
    obj = request.form.to_dict()
    oid = int(obj.get("oid"))
    if not obj.get("addid"):
        return error404()
    addid = int(obj.get("addid"))
    oid_obj = ORDER_FORM.query.filter(ORDER_FORM.id == oid).first()
    add_obj = MY_FORM.query.filter(MY_FORM.id == addid).first()

    if not add_obj or add_obj.reconciliation_id:
        err = {'title': "操作错误.", 'text_head': "单号不存在,或已存在对账单中.请核对!!!", 'text_tail': '秒后自动跳转回对账单',
               'url': f'{url_for("reconciliation_bp.calculation", uid=oid)}'}
        return error404(err)
    lists = pickle.loads(oid_obj.lists)
    lists.add(addid)
    oid_obj.lists = pickle.dumps(lists)
    add_obj.reconciliation_id = oid
    db.session.commit()
    db.session.close()
    return redirect(url_for("reconciliation_bp.calculation", uid=oid))


@reconciliation_bp.route('/clear/')
@reconciliation_verification
def clear():
    """
    获取对账单id和订单id,删除对账单对象中的订单id,删除订单对象中的对账id
    ids: 对账单与订单id集合
    oid: order_id
    oid_obj: 通过oid在order_form数据库中查到的对象
    mid: my_form_id
    mid_obj: 通过mid在my_form数据库中查到的对象
    :return:
    """
    ids = request.args.to_dict()
    oid = ids.get("orderform")
    mid = ids.get("myform")
    if oid and mid:
        oid_obj = ORDER_FORM.query.filter(ORDER_FORM.id == int(oid)).first()
        mid_obj = MY_FORM.query.filter(MY_FORM.id == int(mid)).first()
        if oid_obj and mid_obj:
            lists = pickle.loads(oid_obj.lists)
            lists.remove(int(mid))
            oid_obj.lists = pickle.dumps(lists)
            mid_obj.reconciliation_id = None
            db.session.commit()
            db.session.close()
            return redirect(url_for("reconciliation_bp.calculation", uid=oid))
        else:
            err = {'title': 'id错误', 'text_head': '对象不存在', 'text_tail': '秒后自动跳转回首页',
                   'url': f'{url_for("hello_world")}'}
            return render_template("404.html", err=err)
    else:
        err = {'title': '清除错误', 'text_head': f'{ids}', 'text_tail': '秒后自动跳转回首页',
               'url': f'{url_for("hello_world")}'}
        return render_template('404.html', err=err)


@reconciliation_bp.route("/verification/", methods=["POST"])
def verification():
    password = request.form.get("password")
    admin = session.get("admin")
    user = Admin.query.filter(Admin.username == admin).first()
    if common.my_md5(password) == user.verification:
        session["verification"] = "verification"
        return redirect(url_for("reconciliation_bp.index"))
    else:
        err = {"title": "口令错误", "text_head": "请检查您的输入是否正确", "text_tail": "秒后自动跳转到上个页面",
               'url': f'{url_for("reconciliation_bp.index")}'}
        return error404(err)


@reconciliation_bp.route('/page/<int:id>/')
@reconciliation_bp.route('/page/')
def page(id=1):
    db_obj = ORDER_FORM.query.paginate(id, per_page=1)
    obj = db_obj.items
    page = db_obj.iter_pages(left_edge=0, left_current=2,
                             right_current=3, right_edge=0)
    pages = [i for i in page if i]
    page_max = db_obj.pages
    if page_max >= 5:
        if id <= 3:
            pages = [i for i in range(1, 6)]
        if page_max - id <= 2:
            pages = [page_max - i for i in range(5)]
        pages.sort()
    else:
        b = [1]
        for i in pages:
            b.append(i)
        b.append(page_max)
        pages = b
    return 'ok'


@reconciliation_bp.route("/all_income/", methods=["POST", "GET"])
@reconciliation_verification
def all_income():
    value = request.get_json(force=True).get("value")
    if not value:
        value = "week"
    now = datetime.datetime.now()

    days = {
        "year": 365,
        "month": 31,
        "week": 7
    }

    start = now - datetime.timedelta(days=days[value] - 1)
    table = {(now - datetime.timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in
             range(days[value]).__reversed__()}
    form = MY_FORM.query.filter(MY_FORM.createtime >= start).all()

    for i in form:
        if i.price:
            table[i.createtime.strftime("%Y-%m-%d")] += i.price
    lists = [[i[0], i[1]] for i in table.items()]
    return jsonify(lists)


@reconciliation_bp.route("/average/", methods=["POST"])
@reconciliation_verification
def average():
    obj = request.get_json(force=True)
    start, end = get_date(obj)
    lists = [(start + datetime.timedelta(days=i)).strftime("%Y/%m/%d") for i in range(3650) if
             (start + datetime.timedelta(days=i)) < end]
    count = {i: 0 for i in lists}

    price = count.copy()
    frequency = 0
    price_sum = 0
    for i in lists:
        time = datetime.datetime.strptime(i, "%Y/%m/%d")
        for ii in MY_FORM.query.filter(MY_FORM.createtime >= time, MY_FORM.createtime <
                        time + datetime.timedelta(days=1)).all():
            frequency += 1
            price_sum += ii.income
        days = (time - start).days
        if not days:
            days = 1
        count[i] += frequency / days
        price[i] += price_sum / days

    return jsonify(lists, [round(v, 1) for _, v in count.items()], [int(v) for _, v in price.items()])


@reconciliation_bp.route("/product/income/", methods=["POST"])
@reconciliation_verification
def product_income():
    obj = request.get_json(force=True)
    start, end = get_date(obj)
    product = {i.id: {"name": i.name, "value": 0} for i in PDN.query.all()}
    for i in MY_FORM.query.filter(MY_FORM.createtime >= start, MY_FORM.createtime < end).all():
        try:
            product[i.oids.first().pid]["value"] += i.income
        except KeyError:
            pass
    lists = [i for _, i in product.items()]
    return jsonify(lists)


@reconciliation_bp.route("/product/profit/", methods=["POST"])
@reconciliation_verification
def product_profit():
    obj = request.get_json(force=True)
    start, end = get_date(obj)
    product = {i.id: {"name": i.name, "price": 0, "income": 0} for i in PDN.query.all()}
    for i in MY_FORM.query.filter(MY_FORM.createtime >= start, MY_FORM.createtime < end).all():
        p = i.oids.first()
        try:
            product[p.pid]["price"] += i.price
            product[p.pid]["income"] += i.income
        except KeyError:
            pass
    import bisect
    int_list = []
    name_list = []
    profit = []
    for _, v in product.items():
        number = bisect.bisect(int_list, v["income"])
        int_list.insert(number, v["income"])
        name_list.insert(number, v["name"])
        profit.insert(number, round(v["income"] / (v["price"] if v["price"] else 1) * 100, 1))
    name_list.reverse()
    profit.reverse()
    name = []
    for i in name_list:
        s = ""
        for ii in i:
            s += ii + "\n"
        name.append(s)
    return jsonify({"name": name, "profit": profit})


def get_date(obj):
    start = obj.pop("start")
    end = obj.pop("end")
    if len(start) < 8:
        start = datetime.datetime.strptime("2017-9-17", "%Y-%m-%d")
    else:
        start = datetime.datetime.strptime(start, "%Y-%m-%d")
    if len(end) < 8:
        end = datetime.datetime.now()
    else:
        end = datetime.datetime.strptime(end, "%Y-%m-%d")
    return start, end
