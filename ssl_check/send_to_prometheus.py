import requests
import urllib.parse
import os
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def to_prometheus_pushgateway(prometheus_pushgateway, url):
    try:
        timeout = 1 if not os.getenv('PUSH_GATEWAY_TIMEOUT') else os.getenv('PUSH_GATEWAY_TIMEOUT') 
        
        pg_server = os.getenv('PUSH_GATEWAY_SERVER') if os.getenv('PUSH_GATEWAY_SERVER') \
            else 'localhost'
        pg_port = os.getenv('PUSH_GATEWAY_PORT') if os.getenv('PUSH_GATEWAY_PORT') \
            else '9091'  
        pg_url=''.join(['http://', pg_server,':',pg_port])

        job_name='cert_validity_alert'

        instance_name = urllib.parse.urlparse(url).netloc
        team_name = 'certTeam'
        payload_key = 'cert_verification_error_code'
        payload_value = '1'  # different error codes might signal different poblems
        endpoint = '{pg_url}/metrics/job/{j}/instance/{i}/team/{t}'.format(pg_url=pg_url, j=job_name, i=instance_name, t=team_name)
        response = requests.post(endpoint, data='{k} {v}\n'.format(k=payload_key, v=payload_value), timeout=timeout)
        print('Prometheus pushgateway response status code: ', response.status_code)
        return response.status_code
    except Exception as e:
        print(e)
        return 440

