from flask import request
from . import api
from app.models import *
import json
from flask_login import login_user, logout_user
from ..util.custom_decorator import *


@api.route('/register', methods=['GET', 'POST'])
@admin_required
@login_required
def register():
    """ 注册用户 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    name = data.get('name')
    account = data.get('account')
    password = data.get('password')
    role_id = data.get('role_id')
    user_id = data.get('id')
    if user_id:
        old_data = User.query.filter_by(id=user_id).first()
        if User.query.filter_by(name=name).first() and name != old_data.name:
            return jsonify({'msg': '名字已存在', 'status': 0})
        elif User.query.filter_by(account=account).first() and account != old_data.account:
            return jsonify({'msg': '账号已存在', 'status': 0})
        elif not password:
            return jsonify({'msg': '密码不能为空', 'status': 0})
        else:
            old_data.name = name
            old_data.account = account
            old_data.password = password
            old_data.role_id = role_id
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if User.query.filter_by(name=name).first():
            return jsonify({'msg': '名字已存在', 'status': 0})
        elif User.query.filter_by(account=account).first():
            return jsonify({'msg': '账号已存在', 'status': 0})
        user = User(name=name, account=account, password=password, status=1, role_id=role_id)
        db.session.add(user)
        db.session.commit()
        return jsonify({'msg': '注册成功', 'status': 1})


@api.route('/logout', methods=['GET'])
@login_required
def logout():
    """ 登出 """
    logout_user()
    return jsonify({'msg': '登出成功', 'status': 1})


@api.route('/login', methods=['GET', 'POST'])
def login():
    """ 登录 """
    if request.json:
        data = request.json
    elif request.form:
        data = request.form
    else:
        data = request.data
        data = bytes.decode(data)
        data = json.loads(data)
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    account = data.get('account')
    password = data.get('password')
    user = User.query.filter_by(account=account).first()
    if user is None:
        return jsonify({'msg': '账号错误或不存在', 'status': 0})
    elif not user.verify_password(password):
        return jsonify({'msg': '密码错误', 'status': 0})
    elif user.status == 0:
        return jsonify({'msg': '该账号被冻结', 'status': 0})
    else:
        login_user(user, True)
        token = user.generate_reset_token()
        token = bytes.decode(token)
        return jsonify({'msg': '登录成功', 'status': 1, 'token': token,
                        'name': user.name, 'userId': user.id, 'roles': str(user.role_id)})


@api.route('/user/find', methods=['GET', 'POST'])
@login_required
def find_user():
    """ 查找用户 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    user_name = data.get('userName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 20
    if user_name:
        _users = User.query.filter(User.name.like('%{}%'.format(user_name))).all()
        if not _users:
            return jsonify({'msg': '没有该用户', 'status': 0})
    else:
        users = User.query
        pagination = users.order_by(User.id.asc()).paginate(page, per_page=per_page, error_out=False)
        _users = pagination.items
        total = pagination.total
    users = [{'userName': c.name, 'user_id': c.id, 'status': c.status} for c in _users]

    role_data = [{'role_id': r.id, 'role_name': r.name} for r in Role.query.all()]

    return jsonify({'data': users, 'total': total, 'status': 1, 'role_data': role_data})


@api.route('/user/edit', methods=['POST'])
@login_required
def edit_user():
    """ 返回待编辑用户信息 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    user_id = data.get('id')
    _edit = User.query.filter_by(id=user_id).first()
    _data = {'account': _edit.account, 'name': _edit.name, 'role_id': _edit.role_id}

    return jsonify({'data': _data, 'status': 1})


@api.route('/user/del', methods=['POST'])
@admin_required
@login_required
def del_user():
    """ 删除用户 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    ids = data.get('id')
    _edit = User.query.filter_by(id=ids).first()
    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/user/changeStatus', methods=['POST'])
@admin_required
@login_required
def change_status_user():
    """ 改变用户状态 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    ids = data.get('id')
    _edit = User.query.filter_by(id=ids).first()
    if _edit.status == 1:
        _edit.status = 0
    else:
        _edit.status = 1
    db.session.commit()
    return jsonify({'msg': '置换成功', 'status': 1})
