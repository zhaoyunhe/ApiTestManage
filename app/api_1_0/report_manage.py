import json
import copy
from flask import jsonify, request
from . import api, login_required
from app.models import *
from ..util.http_run import RunCase
from ..util.global_variable import *
from ..util.report.report import render_html_report


@api.route('/report/run', methods=['POST'])
@login_required
def run_cases():
    """ 跑接口 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    if not data.get('projectName'):
        return jsonify({'msg': '请选择项目', 'status': 0})
    if not data.get('sceneIds'):
        return jsonify({'msg': '请选择用例', 'status': 0})
    run_case = RunCase(data.get('projectName'), data.get('sceneIds'))
    if data.get('reportStatus'):
        run_case.make_report = False
    run_case.run_type = True
    res = json.loads(run_case.run_case())
    return jsonify({'msg': '测试完成', 'status': 1, 'data': {'report_id': run_case.new_report_id, 'data': res}})


@api.route('/report/list', methods=['POST'])
@login_required
def get_report():
    """ 查看报告 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    report_id = data.get('reportId')
    state = data.get('state')
    _address = REPORT_ADDRESS + str(report_id) + '.txt'

    if not os.path.exists(_address):
        report_data = Report.query.filter_by(id=report_id).first()
        report_data.read_status = '异常'
        db.session.commit()
        return jsonify({'msg': '报告还未生成、或生成失败', 'status': 0})

    report_data = Report.query.filter_by(id=report_id).first()
    report_data.read_status = '已读'
    db.session.commit()
    with open(_address, 'r') as f:
        d = json.loads(f.read())

    if state == 'success':
        _d = copy.deepcopy(d['details'])
        d['details'].clear()
        for d1 in _d:
            if d1['success']:
                d['details'].append(d1)
    elif state == 'error':
        _d = copy.deepcopy(d['details'])
        d['details'].clear()
        for d1 in _d:
            if not d1['success']:
                d['details'].append(d1)
    return jsonify(d)


@api.route('/report/download', methods=['POST'])
@login_required
def download_report():
    """ 报告下载 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    report_id = data.get('reportId')
    data_or_report = data.get('dataOrReport')
    _address = REPORT_ADDRESS + str(report_id) + '.txt'
    with open(_address, 'r') as f:
        res = json.loads(f.read())
    d = render_html_report(res,
                           html_report_name='接口自动化测试报告',
                           html_report_template=r'{}/extent_report_template.html'.format(TEMP_REPORT),
                           data_or_report=data_or_report)
    return jsonify({'data': d, 'status': 1})


@api.route('/report/del', methods=['POST'])
@login_required
def del_report():
    """ 删除报告 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    address = data.get('address') + '.txt'
    _edit = Report.query.filter_by(data=address).first()
    db.session.delete(_edit)
    address = address.split('/')[-1]
    if not os.path.exists(REPORT_ADDRESS + address):
        return jsonify({'msg': '删除成功', 'status': 1})
    else:
        os.remove(REPORT_ADDRESS + address)
        return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/report/find', methods=['POST'])
@login_required
def find_report():
    """ 查找报告 """
    data = request.json
    current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, data))
    project_name = data.get('projectName')
    project_id = Project.query.filter_by(name=project_name).first().id
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    report_data = Report.query.filter_by(project_id=project_id)
    pagination = report_data.order_by(Report.timestamp.desc()).paginate(page, per_page=per_page, error_out=False)
    report = pagination.items
    total = pagination.total
    report = [{'name': c.case_names, 'project_name': project_name, 'id': c.id, 'read_status': c.read_status,
               'address': c.data.replace('.txt', '')} for c in report]
    return jsonify({'data': report, 'total': total, 'status': 1})


# END
