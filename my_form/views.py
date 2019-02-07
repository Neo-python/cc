from models.model import CITYS, MY_FORM, ORDER_DETALILS, PDN, ORDER_FORM, REMARK, ErrorLog
from my_form import form_bp
from flask import render_template, request, jsonify, session, flash, redirect, url_for
from login import login_required
from run import db
from sqlalchemy import desc, or_, text
from my_form.form import OrderForm, TestForm
from datetime import datetime, date
import datetime as dt
from error_log.mylog import write_error
import pickle


@form_bp.route('/form/', methods=['GET', 'POST'])  # 表单页面
@login_required
def my_form():
    of = OrderForm()  # 表单
    if request.method == "GET":
        pn = PDN.query.order_by(PDN.sorting).all()  # 获取产品名
        remarks = REMARK.query.order_by(REMARK.sorting).all()
        return render_template('form.html', login=session.get('admin'), pn=pn, of=of, remarks=remarks)
    else:
        form = request.form.to_dict()  # 提取表单内容 转为dict类型数据
        status = form.pop('status', None)  # 判断第二栏货物信息有没有展开,展开即可获得数据
        d = {'pid': form.pop('productname'), 'measure': form.pop('measure'),
             'measureunit': form.pop('measureunit'), 'count': form.pop('count')}
        # 将货物信息整理到单独的dict,再存入独立的productname数据库
        if status:
            d2 = {'pid': form.pop('productname1'), 'measure': form.pop('measure1'),
                  'measureunit': form.pop('measureunit1'), 'count': form.pop('count1')}

        if of.validate_on_submit():
            v = MY_FORM()
            date = form.get('date')
            if date == '':
                v.createtime = datetime.now()
            else:
                v.createtime = datetime.strptime(date, '%Y-%m-%d')
            if not of.price.data:
                of.price.data = 0
            of.populate_obj(v)
            try:
                db.session.add(v)
                db.session.commit()
                oid = v.id
                d.update({'oid': oid})
                db.session.add(ORDER_DETALILS(**d))
                if status:
                    d2.update({'oid': oid})
                    db.session.add(ORDER_DETALILS(**d2))
            except BaseException as err:
                print(err)
                write_error(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}----func> my_form:{err.__repr__()}\n')
                db.session.rollback()
                return err.__repr__()
            db.session.commit()
            db.session.close()
            return render_template('jump.html', id=oid)
        else:
            print(of.errors)
            return str(of.errors)


@form_bp.route('/recording/', methods=['GET', 'POST'])
def recording():
    number = request.get_json('number')
    obj = MY_FORM.query.filter(MY_FORM.phone == number.get('number')).order_by(desc(MY_FORM.createtime)). \
        with_entities(MY_FORM.province, MY_FORM.city, MY_FORM.area, MY_FORM.user, MY_FORM.phone, MY_FORM.client,
                      MY_FORM.payment, MY_FORM.receipt).first()
    if obj:
        d = {"province": obj.province, "city": obj.city, "area": obj.area, "user": obj.user, "phone": obj.phone,
             "client": obj.client, "payment": obj.payment, "receipt": obj.receipt}
        return jsonify(d)
    else:
        return 'no', 400


@form_bp.route('/detection/', methods=['GET'])
@login_required
def detection():
    phone = request.args.get('phone')
    return 'ok'


@form_bp.route('/province/', methods=['POST', "GET"])
@login_required
def province():
    id = request.get_json('area_id')['area_id']
    data = CITYS.query.with_entities(CITYS.area_id, CITYS.area_name) \
        .filter(CITYS.parent_id == id).all()  # 从数据库获取已选地址的子地址
    dbs = [{'id': i.area_id, 'name': i.area_name} for i in data]  # 打包数据准备交给jsonify函数转成json格式数据
    return jsonify(dbs)


@form_bp.route('/showlist/', methods=["GET", "POST"])
@login_required
def show_list():
    if request.method == "GET":
        remarks = REMARK.query.order_by(REMARK.sorting).all()
        return render_template('showlist.html', login=session.get('admin'), remarks=remarks)
    else:
        page = int(request.get_json('page')['page'])
        print_list = request.get_json().get('PrintList', [])
        d = MY_FORM.query.order_by(desc(MY_FORM.id)).paginate(page, per_page=10).items
        s = ''''''

        for v, i in enumerate(d, 1):
            s += f'''<tr {(f'style="background-color: #{(v*9)+1}d{v-1}{(v*9)+1}"') if i.print_status  else ''}>
            <td>{(f"""<input type="checkbox" {"checked='checked'" if str(i.id) in print_list else ''} 
val="{i.id}">{i.id}""") if not i.reconciliation_id else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+str(i.id)}</td>
            <td>{i.province_name.area_name} {i.city_name.area_name if i.city_name else ''}
            {i.area_name.area_name if i.area_name  else ''}'''
            s += '''</td><td>'''
            for ii in i.oids:
                s += f'''{ii.productname} ({ii.count}件 {ii.measure}{
('吨) 'if ii.measureunit == 0  else '方) ') if ii.measure else ')'}'''
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
    obj = MY_FORM.query.filter(MY_FORM.id == uid).first()
    try:
        price = int(obj.price)
    except TypeError:
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
    obj = MY_FORM.query.filter(MY_FORM.id == uid).first()
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
        oid = ORDER_FORM(lists={int(i) for i in d})
        db.session.add(oid)
        db.session.commit()
        obj = MY_FORM.query.filter(text(' or '.join(['my_form.id = ' + x for x in d]))).all()
        for i in obj:
            i.print_status = True
            i.reconciliation_id = oid.id
            db.session.add(i)
        db.session.commit()
        return render_template('printer2.html', objs=obj)
    else:
        return redirect(url_for('form_bp.show_list'))


@form_bp.route('/del/<int:uid>/')
@login_required
def list_del(uid=None):
    """
    obj: 准备的删除对象
    order: 订单货物详情对象集合
    orders: 对账集合对象
    :param uid:
    :return:
    """
    try:
        obj = MY_FORM.query.filter(MY_FORM.id == uid).first()
        order = ORDER_DETALILS.query.filter(ORDER_DETALILS.oid == uid).all()
        if order:
            for i in order:
                db.session.delete(i)
        orders = ORDER_FORM.query.filter(ORDER_FORM.id == obj.reconciliation_id).first()
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
@login_required
def list_modify(uid=None):
    if request.method == "GET":
        try:
            obj = MY_FORM.query.filter(MY_FORM.id == uid).first()
            pn = PDN.query.order_by(PDN.sorting).all()
            remarks = REMARK.query.order_by(REMARK.sorting).all()
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
            d2_obj = ORDER_DETALILS.query.filter(ORDER_DETALILS.oid == uid).offset(1).first()
            d2_obj.pid = d2['pid']
            d2_obj.measure = d2['measure']
            d2_obj.measureunit = d2['measureunit']
            d2_obj.count = d2['count']
        obj = MY_FORM.query.filter(MY_FORM.id == uid).first()
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
        d_obj = ORDER_DETALILS.query.filter(ORDER_DETALILS.oid == uid).first()
        d_obj.pid = d['pid']
        d_obj.measure = d['measure']
        d_obj.measureunit = d['measureunit']
        d_obj.count = d['count']
        db.session.commit()
        db.session.close()
        return redirect(url_for('form_bp.show_list'))


@form_bp.route('/search/', methods=["POST"])
@login_required
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
    obj = MY_FORM.query.filter(MY_FORM.province == d['province'] if d['province'] != '0' else MY_FORM != 0,
                               MY_FORM.city == d['city'] if d['city'] != '0' else MY_FORM.city != 0,
                               MY_FORM.area == d['area'] if d['area'] != '0' and MY_FORM.area != 0 else
                               MY_FORM.area != '',
                               MY_FORM.user.like('%' + d['user'] + '%'),
                               or_(MY_FORM.phone.like('%' + phone + '%'), MY_FORM.telephone.like('%' + phone + '%'),
                                   MY_FORM.client.like('%' + phone + '%')),
                               MY_FORM.payment == payment if payment else MY_FORM.payment != '',
                               MY_FORM.receipt == receipt if receipt else MY_FORM.receipt != '',
                               MY_FORM.oids.any(ORDER_DETALILS.count == count) if count else MY_FORM.id != '',
                               MY_FORM.price == d['price'] if d.get('price', None) else MY_FORM.id != '',
                               MY_FORM.remarks.like('%' + remarks + '%') if remarks else MY_FORM.id != '',
                               MY_FORM.createtime >= start_date,
                               MY_FORM.createtime <= end_date)
    try:
        pages_max = [i for i in obj.paginate(p, per_page=10).iter_pages()][-1]
    except IndexError as err:
        pages_max = 0
    s = ''''''
    for v, i in enumerate(obj.order_by(desc(MY_FORM.id)).paginate(p, per_page=10).items, 1):
        s += f'''<tr {(f'style="background-color: #{(v*9)+1}d{v-1}{(v*9)+1}"') if i.print_status  else ''}>
        <td>{(f"""<input type="checkbox" {"checked='checked'" if str(i.id) in print_list else ''} 
val="{i.id}">{i.id}""") if not i.reconciliation_id else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+str(i.id)}</td>
        <td>{i.province_name.area_name} {i.city_name.area_name}
                {i.area_name.area_name if i.area_name else ''}'''
        s += '''</td><td>'''
        for ii in i.oids:
            s += f'''{ii.productname} ({ii.count}件 {ii.measure}{
('吨) 'if ii.measureunit == 0  else '方) ') if ii.measure else ')'}'''
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
        pages += f"""<li ><a id={p-2} onclick="c(this.id)">{p-2}</a></li>"""
        pages += f"""<li ><a id={p-1} onclick="c(this.id)">{p-1}</a></li>"""
        pages += f"""<li class="active"><a id={p} onclick="c(this.id)">{p}</a></li>"""
        pages += f"""<li ><a id={p+1} onclick="c(this.id)">{p+1}</a></li>""" if p <= pages_max - 1 else ''
        pages += f"""<li ><a id={p+2} onclick="c(this.id)">{p+2}</a></li>""" if p <= pages_max - 2 else ''
    pages += f"""<li><a id="{pages_max}" onclick="c(this.id)">»</a></li>"""
    phones = []
    if len(phone) > 4:
        for i in obj.with_entities(MY_FORM.phone, MY_FORM.telephone, MY_FORM.client).limit(5):
            for ii in i:
                if phone in ii:
                    phones.append(ii)
    else:
        phones = ['']
    user = obj.with_entities(MY_FORM.user).all()
    count = obj.count()
    return jsonify([s, pages, user, phones, count])


@form_bp.route('/page/')
@login_required
def page():
    page = int(request.args.get('page'))
    pages_max = [i for i in MY_FORM.query.paginate(page, per_page=10).iter_pages()][-1]
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
        s += f"""<li ><a id={page-2}>{page-2}</a></li>"""
        s += f"""<li ><a id={page-1}>{page-1}</a></li>"""
        s += f"""<li class="active"><a id={page}>{page}</a></li>"""
        s += f"""<li ><a id={page+1}>{page+1}</a></li>""" if page <= pages_max - 1 else ''
        s += f"""<li ><a id={page+2}>{page+2}</a></li>""" if page <= pages_max - 2 else ''
    s += f"""<li><a id="{pages_max}">»</a></li>"""
    return s


@form_bp.route('/fuzzysearch/')
@login_required
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
    err = ErrorLog.query.filter(ErrorLog.status).all()
    return render_template('errlog.html', err=err)
