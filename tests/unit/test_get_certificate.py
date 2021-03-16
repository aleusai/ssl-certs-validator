from ssl_check.get_certificate_info import get_certificate_info
from ssl_check.send_to_prometheus import to_prometheus_pushgateway 
import pytest
import os

@pytest.mark.parametrize("arg, expected", [ 
    ( 'https://example.test/', {'subject': '', 'issuer': '', 'isValid': None} ), # not reachable
    ( 'self-signed.badssl.com/', {'subject': '', 'issuer': '', 'isValid': None, 
        'Error': 'There was an Error with your request: invalid url'} ) # invalid url (no http/s prefix)
])
def test_invalid_preconditions(arg, expected):
    cert, result = get_certificate_info(arg, blackbox=False)
    assert result == expected
    if os.getenv('DOCKERUP'):
        cert, result2 = get_certificate_info(arg, blackbox=True)
        assert result2 == expected

@pytest.mark.parametrize("invalid_certificate", [
    'https://self-signed.badssl.com', # self signed
    'https://expired.badssl.com', # expired
    'https://incomplete-chain.badssl.com/', # incomplete chain
    'https://wrong.host.badssl.com/', # wrong host
    'https://untrusted-root.badssl.com/', # untrusted root
    'https://revoked.badssl.com/', # revoked
    'https://pinning-test.badssl.com/', # pinning test
    'https://no-common-name.badssl.com/', # no common name
    'https://reversed-chain.badssl.com/', # reversed chain
])
def test_invalid_cert(invalid_certificate):
    cert, result = get_certificate_info(invalid_certificate, blackbox=False)
    assert result['isValid'] is False
    if os.getenv('DOCKERUP'):
        cert, result2 = get_certificate_info(invalid_certificate, blackbox=True)
        assert result2['isValid'] is False

def test_valid_leaf_certificate():
    """
    We check that the function returns correctly if a leaf certificate is valid
    """
    cert, result =  get_certificate_info('https://google.com', blackbox=False)
    assert result['isValid'] is True
    if os.getenv('DOCKERUP'):
        cert, result2 =  get_certificate_info('https://google.com', blackbox=True)
        assert result2['isValid'] is True
    

def test_bad_leaf_certificate_no_subject():
    """
    We check that the certificate has the subject field 
    """
    if os.getenv('DOCKERUP'):
        cert, result =  get_certificate_info('https://no-subject.badssl.com/', blackbox=True)
        assert result['subject'] == '' 
    cert, result2 =  get_certificate_info('https://no-subject.badssl.com/', blackbox=False)
    assert result2['subject'] == ''  
 
def test_to_pushgateway():
    """
    We check that the we can register an event with the Pushgateway server
    """
    if os.getenv('DOCKERUP'):
        status_code = to_prometheus_pushgateway(os.getenv('PUSH_GATEWAY'), 'https://google.com')
        assert status_code == 200
