import sys, os
import traceback
import random
import string
import io

from flask import Flask, make_response, request, send_file
from flask_cors import CORS, cross_origin
import json

import shakyou


api = Flask(__name__)
CORS(api)


res_json = {
    'status' : 'success',
    'msg-jp' : '',
    'zip-id' : '',
    'filename' : ''
}
UPLOAD_DIR = 'upload_files'
ZIP_DIR = 'archive_files'


def random_str(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)


@api.route('/convert-pdf', methods=["GET", "POST", "OPTIONS"])
@cross_origin()
def convert_pdf():
    global UPLOAD_DIR
    global ZIP_DIR

    if request.method == "GET":
        return send_req_error('許可されていないメソッドです', 405)

    if 'file' not in request.files:
        return send_req_error('ファイルがアップロードされていません', 200)

    file = request.files['file']
    if file.filename == '':
        send_req_error('ファイル名が存在しません', 200)

    zip_id = random_str(32)
    pdf_path = os.path.join(UPLOAD_DIR, random_str(32) + '.pdf')
    zip_path = os.path.join(ZIP_DIR, zip_id +'-'+ get_filename(file.filename) + '.zip')
    file.save(pdf_path)
    project = 'Unknown'

    try:
        project, formatDict = shakyou.parseShakyouPDF(pdf_path)
        shakyou.getZipArchive(project, formatDict, zip_path)
    except Exception as e:
        os.remove(pdf_path)
        return send_req_error(str(e), 200)

    return send_req_success('解析が終了しました。ダウンロードを押して、写経を手に入れよう！',  get_filename(file.filename), zip_id)


@api.route('/download', methods=["GET", "POST", "OPTIONS"])
@cross_origin()
def download():
    global UPLOAD_DIR
    global ZIP_DIR

    if request.args.get('id') is None or request.args.get('name') is None:
        return send_req_error('無効なページです', 404)

    zip_path = os.path.join(ZIP_DIR, request.args.get('id') +'-'+ request.args.get('name') + '.zip')
    if (not os.path.isfile(zip_path)):
        return send_req_error('存在しないパスです: '+ zip_path, 404)

    return send_file(zip_path, as_attachment=True, attachment_filename=get_filename(request.args.get('name'))+'.zip', mimetype='application/zip')


@api.errorhandler(404)
def not_found(error):
    return send_req_error('無効なページです', 404)


def send_req_error(msg, code):
    global res_json
    res_json['status'] = 'error'
    res_json['msg-jp'] = msg
    return make_response(json.dumps(res_json, ensure_ascii=False), code)

def send_req_success(msg, filename, zip_id):
    global res_json
    res_json['status'] = 'success'
    res_json['msg-jp'] = msg
    res_json['zip-id'] = zip_id
    res_json['filename'] = filename
    return make_response(json.dumps(res_json, ensure_ascii=False), 201)
    
 
def get_filename(path):
    return os.path.splitext(os.path.basename(path))[0]
 


if __name__ == '__main__':
    api.run(host='0.0.0.0', port=45829, debug=True)