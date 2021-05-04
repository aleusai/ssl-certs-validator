from flask import Flask, Blueprint, request, make_response, jsonify
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask import abort
import os
from datetime import datetime
from collections import deque
from ssl_check.get_certificate_info import get_certificate_info
from ssl_check.send_to_prometheus import to_prometheus_pushgateway 
from flasgger import Swagger

def create_app():
    app = Flask(__name__)   
    CORS(app)
    swagger = Swagger(app)

    auth = HTTPBasicAuth()
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
        """ 
        This is using docstrings for specifications.
        ---
        parameters:
          - name: url
            in: query
            type: string
            description: example payload
            default: "https://incomplete-chain.badssl.com/"
          - name: toPrometheus
            in: query
            type: string
            description: example payload
            default: true
          - name: debug
            in: query
            type: string
            default: true
        responses:
          200:
            description: ssl validation result in json
            examples:
              response: {
  "debug": "HTTPSConnectionPool(host='incomplete-chain.badssl.com', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1076)')))", 
  "isValid": false, 
  "issuer": "/C=US/O=DigiCert Inc/CN=DigiCert SHA2 Secure Server CA", 
  "subject": "/C=US/ST=California/L=Walnut Creek/O=Lucas Garron Torres/CN=*.badssl.com"
}
        """
        try:
            url = '' # Compulsory parameter
            debug = False

            if not request.json and not request.args:
                abort(400)
                
            if request.json: 
                if "url" not in request.json:
                     abort(400)
                else:
                    url = request.json['url'] 
                debug = False if not 'debug' in request.json else True
                toPrometheus = False if not 'toPrometheus' in request.json else True

            if request.args: 
                if "url" not in request.args:
                     abort(400)
                else:
                    url = request.args['url'] 
                debug = False if not 'debug' in request.args else True
                toPrometheus = False if not 'toPrometheus' in request.args else True
            
            if request.endpoint == 'api.blackbox':
                blackbox = True
            else:
                blackbox = False
            cert, result = get_certificate_info(url, blackbox, debug)
            if result['isValid']:
                valid_certs_urls.append((url, datetime.now()))
            else:
                invalid_certs_urls.append((url, datetime.now()))
                if toPrometheus and os.getenv('PUSH_GATEWAY_SERVER'):
                    to_prometheus_pushgateway(os.getenv('PUSH_GATEWAY_SERVER'), url)

            return result
        except Exception as e:
            print(e)
            return {'isValid': None, 'subject': '', 'issuer': ''}

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
