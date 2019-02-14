from model.models import CITYS, Order, OrderDetail, Article, Bill, Remark, Log
from modules.business import form_bp
from flask import render_template, request, jsonify, session, redirect, url_for
from modules.permission import logging_in
from run import db
from sqlalchemy import desc, or_, text
from modules.business.form import OrderForm
from datetime import datetime
import datetime as dt
from error_log.mylog import write_error


@form_bp.route('/form/', methods=['GET'])  # 表单录入页面
@logging_in
def my_form():
    """订单录入"""
    of = OrderForm()  # 表单
    articles = Article.query.order_by(Article.sorting).all()  # 获取产品名
    remarks = Remark.query.order_by(Remark.sorting).all()  # 获取预设备注
    return render_template('form.html', articles=articles, of=of, remarks=remarks)


@form_bp.route('/form/', methods=['POST'])
def entry():
    """表单提交入库
    构建订单 -> 添加订单详情 -> 返回跳转页
    """
    of = OrderForm()  # 表单
    if not of.validate_on_submit(): # 验证表单
        return str(of.errors)

    form = request.form.to_dict()  # 提取表单内容 转为dict类型数据
    status = form.pop('status', None)  # 判断第二栏货物信息有没有展开,展开即可获得数据
    # 创建订单
    order = Order()
    date = form.get('date', None)
    if not date:
        order.create_time = None
    else:
        order.create_time = datetime.strptime(date, '%Y-%m-%d')

    if not of.price.data:
        of.price.data = 0
    of.populate_obj(order)
    order.direct_commit_()

    # 添加订单详情
    try:
        OrderDetail(oid=order.id, article_id=form.pop('article'), measure=form.pop('measure'),
                    unit=form.pop('unit'), count=form.pop('count')).direct_add_()
        if status:
            OrderDetail(oid=order.id, article_id=form.pop('article1'), measure=form.pop('measure1'),
                        unit=form.pop('unit1'), count=form.pop('count1')).direct_add_()
        db.session.commit()
    except BaseException as err:
        print(err)
        write_error(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}----func> business:{err.__repr__()}\n')
        db.session.rollback()
        return err.__repr__()
    return render_template('jump.html', id=order.id)


@form_bp.route('/recording/', methods=['GET', 'POST'])
def recording():
    number = request.get_json(force=True)
    obj = Order.query.filter(Order.phone == number.get('number')).order_by(desc(Order.create_time)). \
        with_entities(Order.province, Order.city, Order.area, Order.user, Order.phone, Order.client,
                      Order.payment, Order.receipt).first()
    if obj:
        d = {"province": obj.province, "city": obj.city, "area": obj.area, "user": obj.user, "phone": obj.phone,
             "client": obj.client, "payment": obj.payment, "receipt": obj.receipt}
        return jsonify(d)
    else:
        return 'no', 400


@form_bp.route('/detection/', methods=['GET'])
@logging_in
def detection():
    phone = request.args.get('phone')
    return 'ok'


@form_bp.route('/province/', methods=['POST', "GET"])
@logging_in
def province():
    id = request.get_json('area_id')['area_id']
    data = CITYS.query.with_entities(CITYS.area_id, CITYS.area_name) \
        .filter(CITYS.parent_id == id).all()  # 从数据库获取已选地址的子地址
    dbs = [{'id': i.area_id, 'name': i.area_name} for i in data]  # 打包数据准备交给jsonify函数转成json格式数据
    return jsonify(dbs)


@form_bp.route('/showlist/', methods=["GET", "POST"])
@logging_in
def show_list():
    if request.method == "GET":
        remarks = Remark.query.order_by(Remark.sorting).all()
        return render_template('showlist.html', login=session.get('admin'), remarks=remarks)
    else:
        page = int(request.get_json('page')['page'])
        print_list = request.get_json().get('PrintList', [])
        d = Order.query.order_by(desc(Order.id)).paginate(page, per_page=10).items
        s = ''''''

        for v, i in enumerate(d, 1):
            s += f'''<tr {(f'style="background-color: #{(v * 9) + 1}d{v - 1}{(v * 9) + 1}"') if i.print_status else ''}>
            <td>{(f"""<input type="checkbox" {"checked='checked'" if str(i.id) in print_list else ''} 
val="{i.id}">{i.id}""") if not i.reconciliation_id else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + str(i.id)}</td>
            <td>{i.province_name.area_name} {i.city_name.area_name if i.city_name else ''}
            {i.area_name.area_name if i.area_name else ''}'''
            s += '''</td><td>'''
            for ii in i.oids:
                s += f'''{ii.productname} ({ii.count}件 {ii.measure}{
                ('吨) ' if ii.measureunit == 0 else '方) ') if ii.measure else ')'}'''
            s += f'''</td><td>{i.user}</td><td>{i.createtime.strftime('%Y-%m-%d %H:%M')}</td>
            <td>
            <a href="/printer2/{i.id}" class="btn btn-info btn-xs"><i class="fa fa-print"></i></a>
            <a href="/printer/{i.id}" class="btn btn-success btn-xs"><i class="fa fa-search"></i></a>
            <a href="/modify/{i.id}" class="btn btn-primary btn-xs"><i class="fa fa-pencil"></i></a>
            <a href="/del/{i.id}" class="btn btn-danger btn-xs" ''' + '''onclick="if(confirm('确认删除吗?')){return true}else{return false}"><i class="fa fa-trash-o "></i></a>
            </td></tr>"'''
        return s


@form_bp.route('/printer/<int:uid>/', methods=["GET"])
def printer(uid=None):
    obj = Order.query.filter(Order.id == uid).first()
    try:
        price = int(obj.price)
    except TypeError as err:
        price = 0
        write_error(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}----func> printer:{err.__repr__()}\n')
    w = ['个', '十', '百', '千', '万', '十万']
    u = ['零', '壹', '贰', '叄', '肆', '伍', '陆', '柒', '捌', '玖']
    f = {'个': 'None', '十': 'None', '百': 'None', '千': 'None', '万': 'None'}
    for i in range(len(str(price))):
        p = int((price / 10 ** i) % 10)
        f.update({w[i]: u[p]})
    return render_template('printer.html', obj=obj, price=f)


@form_bp.route('/printer2/<int:uid>/', methods=["GET"])
def printer2(uid=None):
    obj = Order.query.filter(Order.id == uid).first()
    obj.print_status = True
    db.session.add(obj)
    db.session.commit()
    return render_template('printer2.html', objs=[obj])


@form_bp.route('/printer/', methods=["POST"])
def printer_list():
    """
    d: 前台出单,单号集合,通过str.split(',')拆分成list
    obj:通过单号集合查询出的 数据库 数据对象

    :return:
    """
    d = request.form.get('FormList', '').split(',')
    if d[0] != '':
        oid = Bill(lists={int(i) for i in d})
        db.session.add(oid)
        db.session.commit()
        obj = Order.query.filter(text(' or '.join(['business.id = ' + x for x in d]))).all()
        for i in obj:
            i.print_status = True
            i.reconciliation_id = oid.id
            db.session.add(i)
        db.session.commit()
        return render_template('printer2.html', objs=obj)
    else:
        return redirect(url_for('form_bp.show_list'))


@form_bp.route('/del/<int:uid>/')
@logging_in
def list_del(uid=None):
    """
    obj: 准备的删除对象
    order: 订单货物详情对象集合
    orders: 对账集合对象
    :param uid:
    :return:
    """
    try:
        obj = Order.query.filter(Order.id == uid).first()
        order = OrderDetail.query.filter(OrderDetail.oid == uid).all()
        if order:
            for i in order:
                db.session.delete(i)
        orders = Bill.query.filter(Bill.id == obj.reconciliation_id).first()
        if orders:
            errtext = {'title': '单号不可删除!!!', 'text': f"请先在 <strong>{orders.id}号 </strong> 对账单 内删除 "
            f"<strong>{uid}号 </strong>订单 ",
                       'url': f'/reconciliation/calculation/{orders.id}/'}
            return render_template('showlist.html', login=session.get("admin"),
                                   errtext=errtext)
        else:
            db.session.delete(obj)
    except BaseException as err:
        print(err)
        write_error(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}----func> list_del:{err.__repr__()}\n')
        db.session.rollback()
        return redirect('/showlist/')
    db.session.commit()
    db.session.close()
    return redirect('/showlist/')


@form_bp.route('/modify/<int:uid>/', methods=["GET", "POST"])
@logging_in
def list_modify(uid=None):
    if request.method == "GET":
        try:
            obj = Order.query.filter(Order.id == uid).first()
            pn = Article.query.order_by(Article.sorting).all()
            remarks = Remark.query.order_by(Remark.sorting).all()
            return render_template('modify.html', obj=obj, login=session.get('admin'), pnlist=pn, remarks=remarks)
        except BaseException as err:
            print(err)
            write_error(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}----func> list_modify:{err.__repr__()}\n')
        return redirect('/showlist/')
    else:
        form = request.form.to_dict()
        status = form.get('productname1', None)
        d = {'pid': form.pop('productname'), 'measure': form.pop('measure'),
             'measureunit': form.pop('measureunit'), 'count': form.pop('count')}
        if status:
            d2 = {'pid': form.pop('productname1'), 'measure': form.pop('measure1'),
                  'measureunit': form.pop('measureunit1'), 'count': form.pop('count1')}
            d2_obj = OrderDetail.query.filter(OrderDetail.oid == uid).offset(1).first()
            d2_obj.pid = d2['pid']
            d2_obj.measure = d2['measure']
            d2_obj.measureunit = d2['measureunit']
            d2_obj.count = d2['count']
        obj = Order.query.filter(Order.id == uid).first()
        obj.province = form['province']
        obj.city = form['city']
        obj.area = form['area']
        obj.user = form['user']
        obj.phone = form['phone']
        obj.userunit = form['userunit']
        obj.telephone = form['telephone']
        obj.payment = form['payment']
        obj.receipt = form['receipt']
        obj.client = form['client']
        obj.clientphone = form['clientphone']
        obj.price = form['price']
        obj.remarks = form['remarks']
        if form['date'] != '':
            obj.createtime = datetime.strptime(form['date'], "%Y-%m-%d")
        d_obj = OrderDetail.query.filter(OrderDetail.oid == uid).first()
        d_obj.pid = d['pid']
        d_obj.measure = d['measure']
        d_obj.measureunit = d['measureunit']
        d_obj.count = d['count']
        db.session.commit()
        db.session.close()
        return redirect(url_for('form_bp.show_list'))


@form_bp.route('/search/', methods=["POST"])
@logging_in
def search():
    form = request.get_json(force=True)
    d = {}
    for i in form:
        d.update({i['name']: i['value']})
    p = int(d['page'])
    phone = d['phone']
    payment = d.get('payment', None)
    receipt = d.get('receipt', None)
    count = d.get('count', None)
    remarks = d.get('remarks', None)
    print_list = d.get('PrintList', [])
    start_date = d.get('StartDate', None)
    start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date != '' else \
        datetime.today().date() - dt.timedelta(days=365)
    end_date = d.get('EndDate', datetime.today())
    end_date = datetime.strptime(end_date, '%Y-%m-%d') + dt.timedelta(hours=23, minutes=59) if end_date != '' else \
        datetime.today() + dt.timedelta(hours=23, minutes=59)
    obj = Order.query.filter(Order.province == d['province'] if d['province'] != '0' else Order != 0,
                             Order.city == d['city'] if d['city'] != '0' else Order.city != 0,
                             Order.area == d['area'] if d['area'] != '0' and Order.area != 0 else
                             Order.area != '',
                             Order.user.like('%' + d['user'] + '%'),
                             or_(Order.phone.like('%' + phone + '%'), Order.telephone.like('%' + phone + '%'),
                                 Order.client.like('%' + phone + '%')),
                             Order.payment == payment if payment else Order.payment != '',
                             Order.receipt == receipt if receipt else Order.receipt != '',
                             Order.oids.any(OrderDetail.count == count) if count else Order.id != '',
                             Order.price == d['price'] if d.get('price', None) else Order.id != '',
                             Order.remarks.like('%' + remarks + '%') if remarks else Order.id != '',
                             Order.createtime >= start_date,
                             Order.createtime <= end_date)
    try:
        pages_max = [i for i in obj.paginate(p, per_page=10).iter_pages()][-1]
    except IndexError as err:
        pages_max = 0
    s = ''''''
    for v, i in enumerate(obj.order_by(desc(Order.id)).paginate(p, per_page=10).items, 1):
        s += f'''<tr {(f'style="background-color: #{(v * 9) + 1}d{v - 1}{(v * 9) + 1}"') if i.print_status else ''}>
        <td>{(f"""<input type="checkbox" {"checked='checked'" if str(i.id) in print_list else ''} 
val="{i.id}">{i.id}""") if not i.reconciliation_id else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + str(i.id)}</td>
        <td>{i.province_name.area_name} {i.city_name.area_name}
                {i.area_name.area_name if i.area_name else ''}'''
        s += '''</td><td>'''
        for ii in i.oids:
            s += f'''{ii.productname} ({ii.count}件 {ii.measure}{
            ('吨) ' if ii.measureunit == 0 else '方) ') if ii.measure else ')'}'''
        s += f'''</td><td>{i.user}</td><td>{i.createtime.strftime('%Y-%m-%d %H:%M')}</td>
                <td>
                <a href="/printer2/{i.id}" class="btn btn-info btn-xs"><i class="fa fa-print"></i></a>
                <a href="/printer/{i.id}" class="btn btn-success btn-xs"><i class="fa fa-search"></i></a>
                <a href="/modify/{i.id}" class="btn btn-primary btn-xs"><i class="fa fa-pencil"></i></a>
                <a href="/del/{i.id}" class="btn btn-danger btn-xs"><i class="fa fa-trash-o "></i></a>
                </td></tr>'''
    pages = f"""<li><a id="{1}" onclick="c(this.id)">«</a></li>"""
    if p < 5:
        if pages_max > 5:
            for i in range(1, 6):
                if p == i:
                    pages += f"""<li class="active"><a id={i} onclick="c(this.id)">{i}</a></li>"""
                else:
                    pages += f"""<li><a id={i} onclick="c(this.id)">{i}</a></li>"""
        else:
            for i in range(1, pages_max + 1):
                if p == i:
                    pages += f"""<li class="active"><a id={i} onclick="c(this.id)">{i}</a></li>"""
                else:
                    pages += f"""<li><a id={i} onclick="c(this.id)">{i}</a></li>"""
    else:
        pages += f"""<li ><a id={p - 2} onclick="c(this.id)">{p - 2}</a></li>"""
        pages += f"""<li ><a id={p - 1} onclick="c(this.id)">{p - 1}</a></li>"""
        pages += f"""<li class="active"><a id={p} onclick="c(this.id)">{p}</a></li>"""
        pages += f"""<li ><a id={p + 1} onclick="c(this.id)">{p + 1}</a></li>""" if p <= pages_max - 1 else ''
        pages += f"""<li ><a id={p + 2} onclick="c(this.id)">{p + 2}</a></li>""" if p <= pages_max - 2 else ''
    pages += f"""<li><a id="{pages_max}" onclick="c(this.id)">»</a></li>"""
    phones = []
    if len(phone) > 4:
        for i in obj.with_entities(Order.phone, Order.telephone, Order.client).limit(5):
            for ii in i:
                if phone in ii:
                    phones.append(ii)
    else:
        phones = ['']
    user = obj.with_entities(Order.user).all()
    count = obj.count()
    return jsonify([s, pages, user, phones, count])


@form_bp.route('/page/')
@logging_in
def page():
    page = int(request.args.get('page'))
    pages_max = [i for i in Order.query.paginate(page, per_page=10).iter_pages()][-1]
    s = f"""<li><a id="{1}">«</a></li>"""
    if page < 5:
        if pages_max > 5:
            for i in range(1, 6):
                if page == i:
                    s += f"""<li class="active"><a id={i}>{i}</a></li>"""
                else:
                    s += f"""<li><a id={i}>{i}</a></li>"""
        else:
            for i in range(1, pages_max + 1):
                if page == i:
                    s += f"""<li class="active"><a id={i}>{i}</a></li>"""
                else:
                    s += f"""<li><a id={i}>{i}</a></li>"""
    else:
        s += f"""<li ><a id={page - 2}>{page - 2}</a></li>"""
        s += f"""<li ><a id={page - 1}>{page - 1}</a></li>"""
        s += f"""<li class="active"><a id={page}>{page}</a></li>"""
        s += f"""<li ><a id={page + 1}>{page + 1}</a></li>""" if page <= pages_max - 1 else ''
        s += f"""<li ><a id={page + 2}>{page + 2}</a></li>""" if page <= pages_max - 2 else ''
    s += f"""<li><a id="{pages_max}">»</a></li>"""
    return s


@form_bp.route('/fuzzysearch/')
@logging_in
def fuzzy_search():
    py = request.args.get('py')
    pys = CITYS.query.filter(CITYS.py_name.like(py + '%')).all()
    item = []
    for i in pys:
        parent = CITYS.query.filter(CITYS.area_id == i.parent_id).first()
        if parent:
            top = CITYS.query.filter(CITYS.area_id == parent.parent_id).first()
            if top:
                item.append([top.area_name + " < " + parent.area_name + ' < ' + i.area_name])
            else:
                item.append([parent.area_name + " < " + i.area_name])
        else:
            item.append([i])
    return jsonify(item)


@form_bp.route('/errlog/')
def errlog():
    err = Log.query.filter(Log.status).all()
    return render_template('errlog.html', err=err)
