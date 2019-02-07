from flask_wtf import FlaskForm
import wtforms
from wtforms.validators import DataRequired, Length, Optional, Regexp


class OrderForm(FlaskForm):
    province = wtforms.IntegerField('省', validators=[DataRequired(message='省信息未选择')])
    city = wtforms.IntegerField('市', validators=[DataRequired(message='市信息未选择')])
    area = wtforms.IntegerField('区')
    user = wtforms.StringField('收货人', validators=[DataRequired(message='收货人信息未填写')])
    phone = wtforms.StringField('手机', validators=[Regexp(regex='^\d{8}$|^\d{11}$', message='号码内容有误,请检查')])
    userunit = wtforms.StringField('收货单位')
    telephone = wtforms.StringField('电话', validators=[Regexp(regex='^\d{8}$|^\d{11}$', message='号码有误,请检查'), Optional()])
    payment = wtforms.RadioField('付款方式', choices=[('1', '提付'), ('0', "现付")], validators=[Optional()], default=1)
    receipt = wtforms.RadioField('提货方式', choices=[('0', "自提"), ('1', '送货')], validators=[Optional()], default=0)
    client = wtforms.StringField('发货单位', validators=[Regexp(regex='^\d{8}$|^\d{11}$', message='号码有误,请检查'), Optional()])
    clientphone = wtforms.StringField('电话',
                                      validators=[Regexp(regex='^\d{8}$|^\d{11}$', message='号码有误,请检查'), Optional()])
    price = wtforms.IntegerField('价格', validators=[Optional()])
    remarks = wtforms.StringField('备注')


class TestForm(FlaskForm):
    user = wtforms.StringField('用户', validators=[DataRequired()])
    password = wtforms.StringField('密码')
