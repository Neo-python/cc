from flask import request, render_template, jsonify, redirect, url_for
from sqlalchemy import desc
from modules.manage import manage
from modules.login import logging_in
from model.models import Article, REMARK
from project_init import db


@manage.route('/manage/')
@logging_in
def manage_func():
    """管理页主页"""
    return render_template("manage.html")


@manage.route('/manage/article_name/')
@logging_in
def article_name():
    """物品名清单"""
    # 获取所有物品名
    articles = Article.query.order_by(Article.sorting).order_by(Article.sorting).all()
    return jsonify([article.to_dict_() for article in articles])


@manage.route('/manage/sorting/', methods=["POST"])
@logging_in
def article_sorting():
    """物品名排列顺序调整
    防止顺序冲突.先清空所有物品顺序编号
    更新物品顺序编号
    """
    sorting = request.get_json(force=True)  # 获取ajax传回来的物品排列顺序
    for i in Article.query.all():
        i.sorting = None
        db.session.add(i)
    db.session.commit()

    for i in Article.query.all():
        i.sorting = sorting.get(str(i.id))
        db.session.add(i)
    db.session.commit()
    return 'ok', 200


@manage.route('/manage/add_article/')
@logging_in
def add_article():
    """添加新的物品
    通过计算物总数,得到当前新增物品的排序编号.
    :return 返回最新物品列表
    """
    sorting = Article.query.count()
    name = request.args.get('NewProductName')
    Article(name=name, sorting=sorting).direct_commit_()
    return article_name()


@manage.route('/manage/delete_article/', methods=["POST"])
@logging_in
def delete_article():
    """删除物品"""
    delete_id = request.get_json(force=True).get('ProductName')  # 获取物品编号
    db.session.delete(Article.query.filter(Article.id == delete_id).first())
    db.session.commit()
    return article_name()


@manage.route('/manage/remark/sorting/', methods=["GET", "POST"])
@logging_in
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
