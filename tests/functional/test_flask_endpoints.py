from app import create_app
import base64
import os
import json

def get_myauth():
    return bytes(os.getenv('USERNAME') + ':' + os.getenv('PASSWORD'), 'utf-8')

def test_get():
    myauth = get_myauth()
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        credentials = base64.b64encode(myauth).decode('utf-8')
        response = test_client.get('/api/data', headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 200
        assert b"invalid_certs_urls" in response.data 
        assert b"valid_certs_urls"in response.data 

def test_get_wrong_auth():
    flask_app = create_app()
    with flask_app.test_client() as test_client:
        credentials = base64.b64encode(b"wrong_user:wrong_password").decode('utf-8')
        response = test_client.get('/api/data', headers={"Authorization": f"Basic {credentials}"})
        assert response.status_code == 401

def test_post_local_debug():
    myauth = get_myauth()
    flask_app = create_app()
    credentials = base64.b64encode(myauth).decode('utf-8')
    data = {"url": "https://google.com", "debug": True}
    headers = {"Content-type": "application/json",
              "Accept": "application/json" ,
              "Authorization": f"Basic {credentials}" } 
    with flask_app.test_client() as test_client:
        response = test_client.post('/api/local', data=json.dumps(data) ,headers=headers)
        assert response.status_code == 200
        assert b"isValid" in response.data
        assert b"subject" in response.data
        assert b"issuer" in response.data  
        assert b"debug" in response.data 
        
def test_post_blackbox_debug():
    if os.getenv('DOCKERUP'):
        flask_app = create_app()
        myauth = get_myauth()
        credentials = base64.b64encode(myauth).decode('utf-8')
        data = {"url": "https://google.com", "debug": True}
        headers = {"Content-type": "application/json",
                "Accept": "application/json" ,
                "Authorization": f"Basic {credentials}" } 
        with flask_app.test_client() as test_client:
            response = test_client.post('/api/blackbox', data=json.dumps(data) ,headers=headers)
            assert response.status_code == 200
            assert b"isValid" in response.data
            assert b"subject" in response.data
            assert b"issuer" in response.data  
            assert b"debug" in response.data 
    else:
        pass