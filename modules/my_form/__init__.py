from flask import Blueprint
form_bp = Blueprint('form_bp', __name__)
from modules.my_form.views import *