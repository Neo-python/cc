from modules.manage import manage
from flask import request, render_template, session, jsonify, redirect ,url_for
from modules.login import login_required
from model.models import *
from sqlalchemy import desc


@manage.route('/manage/')
@login_required
def manage_func():
    return render_template("manage.html", login=session.get('admin'))


@manage.route('/manage/productname/')
@login_required
def product_name():
    productname =PDN.query.order_by(PDN.sorting).all()
    obj = {}
    for i in productname:
        obj.update({i.id: i.name})
    return jsonify(obj)


@manage.route('/manage/sorting/', methods=["GET", "POST"])
@login_required
def productname_sorting():
    if request.method == "GET":
        sorting = PDN.query.with_entities(PDN.name, PDN.sorting, PDN.id).order_by(PDN.sorting).all()
        return jsonify(sorting)
    else:
        obj = request.get_json(' ')
        for i in PDN.query.all():
            i.sorting = None
            db.session.add(i)
        db.session.commit()
        for i in PDN.query.all():
            i.sorting = obj.get(str(i.id))
            db.session.add(i)
        db.session.commit()
        return 'ok', 200


@manage.route('/manage/newproductname/')
@login_required
def new_product():
    sorting = PDN.query.order_by(desc(PDN.sorting)).first().sorting + 1
    new_product_name = request.args.get('NewProductName')
    obj = PDN(new_product_name, sorting)
    db.session.add(obj)
    db.session.commit()
    return product_name()


@manage.route('/manage/productdelete/', methods=["POST"])
@login_required
def product_delete():
    delete_id = request.get_json('ProductName')
    db.session.delete(PDN.query.filter(PDN.id == delete_id.get('ProductName')).first())
    db.session.commit()
    return product_name()


@manage.route('/manage/remark/sorting/', methods=["GET", "POST"])
@login_required
def remark_sorting():
    if request.method == "GET":
        objs = REMARK.query.with_entities(REMARK.id, REMARK.text, REMARK.sorting).order_by(REMARK.sorting).all()
        return jsonify(objs)
    else:
        obj = request.get_json(' ')
        for i in REMARK.query.all():
            i.sorting = None
            db.session.add(i)
        db.session.commit()
        for i in REMARK.query.all():
            i.sorting = obj.get(str(i.id))
            db.session.add(i)
        db.session.commit()
        return 'ok', 200


@manage.route('/manage/remark/delete/<int:id>/')
def remark_del(id=None):
    db.session.delete(REMARK.query.filter(REMARK.id == id).first())
    db.session.commit()
    return redirect(url_for("manage.manage_func"))


@manage.route('/manage/remark/add/<text>/')
@manage.route('/manage/remark/add/')
def remark_add(text=None):
    if text:
        remark_obj = REMARK.query.order_by(desc(REMARK.sorting)).first()
        if remark_obj:
            db.session.add(REMARK(text, remark_obj.sorting + 1))
        else:
            db.session.add(REMARK(text, 0))
        db.session.commit()
        return redirect(url_for("manage.manage_func"))
    else:
        err = {'title': '服务器错误', 'text_head': "因输入的内容产生错误", 'text_tail': '秒后自动跳转回管理页面',
               'url': url_for("manage.manage_func")}
        return render_template("404.html", err=err)
