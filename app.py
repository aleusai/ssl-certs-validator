from flask import Flask, Blueprint, request, make_response, jsonify
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask import abort
import os
from datetime import datetime
from collections import deque
from ssl_check.get_certificate_info import get_certificate_info
from ssl_check.send_to_prometheus import to_prometheus_pushgateway 


def create_app():
    app = Flask(__name__)
    auth = HTTPBasicAuth()
    CORS(app)
    api = Blueprint('api', __name__)

    valid_certs_urls = deque([], maxlen=1000)
    invalid_certs_urls = deque([], maxlen=1000)

    @auth.get_password
    def get_password(username):
        if username == os.getenv('USERNAME'):
            return os.getenv('PASSWORD')
        #if username == 'admin':
        #    return 'admin'
        return None

    @auth.error_handler
    def unauthorized():
        return make_response(jsonify( { 'error': 'Unauthorized access' } ), 401)
        # return 403 instead of 401 to prevent browsers from displaying the default auth dialog

    @app.errorhandler(400)
    def not_found(error):
        return make_response(jsonify( { 'error': 'Bad request' } ), 400)

    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify( { 'error': 'Not found' } ), 404)

    @api.route('/local', endpoint='local', methods=['POST'])
    @api.route('/blackbox', endpoint='blackbox', methods=['POST'])
    @auth.login_required
    def handle_submit():
        try:
            if not request.json:
                print(request.json)
                abort(400)
            debug = False
            url = request.json['url']
            debug = False if not 'debug' in request.json else bool(request.json['debug'])
            if request.endpoint == 'api.blackbox':
                blackbox = True
            else:
                blackbox = False
            cert, result = get_certificate_info(url, blackbox, debug)
            if result['isValid']:
                valid_certs_urls.append((url, datetime.now()))
            else:
                invalid_certs_urls.append((url, datetime.now()))
                if 'toPrometheus' in request.json and os.getenv('PUSH_GATEWAY_SERVER'):
                    to_prometheus_pushgateway(os.getenv('PUSH_GATEWAY_SERVER'), url)

            return result
        except Exception as e:
            print(e)
            return {'isValid': None, 'subkect': '', 'issuer': ''}

    @api.route('/sb', methods=['POST', 'GET'])
    @auth.login_required
    def handle_submit_sb():
        try:
            debug = True
            url = request.args.get('target')

            blackbox = True
            cert, result = get_certificate_info(url, blackbox, debug)
            if result['isValid']:
                valid_certs_urls.append((url, datetime.now()))
            else:
                invalid_certs_urls.append((url, datetime.now()))
            return result['debug']
        except Exception as e:
            print(e)
            return ''


    @api.route('/data', methods=['GET'])
    @auth.login_required
    def get_data():
            return jsonify({
                "invalid_certs_urls": list(invalid_certs_urls),
                "valid_certs_urls": list(valid_certs_urls)
            })

    app.register_blueprint(api, url_prefix='/api')
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True, port=5000)
