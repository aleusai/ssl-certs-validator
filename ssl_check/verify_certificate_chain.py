from OpenSSL import crypto, SSL
from socket import socket, gaierror
import urllib.parse
import idna
import requests
import os
import requests
from ocspchecker import ocspchecker

def get_remote_chain(url):
    """
    :param url: target url
    :param port: target port
    :return: certficate, certificate chain

    We check that the certificate has the subject field 
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.netloc
        sock = socket()
        port = 443 if not parsed_url.port else parsed_url.port
        sock.connect((hostname, port))

        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.check_hostname = False
        ctx.verify_mode = SSL.VERIFY_NONE

        sock_ssl = SSL.Connection(ctx, sock)
        sock_ssl.set_connect_state()
        sock_ssl.set_tlsext_host_name(idna.encode(hostname))
        # this is important: without it and with the timeout the ssl handshake fails
        sock.setblocking(1)
        sock_ssl.do_handshake()
        peer = sock_ssl.get_peer_certificate()
        chain = sock_ssl.get_peer_cert_chain()
        sock_ssl.close()
        sock.close()
        return peer, chain
    except (SSL.WantReadError, SSL.Error, OSError, gaierror) as e:
        raise e

    except Exception as e:
        raise e

def verify_ocsp(url):
        ocsp_request = ocspchecker.get_ocsp_status(url) 
        return ocsp_request, (ocsp_request[-1].split(':')[-1] == ' GOOD')


def verify_certificate_chain(url):
    timeout = 1 if not os.getenv('URL_TIMEOUT') else os.getenv('URL_TIMEOUT') 
    try:
        try:
            if os.getenv('CA_PEM_FILE'):
                resp = requests.get(url, timeout=timeout, verify=os.getenv('CA_PEM_FILE'))
            else:
                resp = requests.get(url, timeout=timeout)
        except:
            resp = requests.get(url, timeout=timeout)
        # crl check
        ocsp_request, ocsp_response = verify_ocsp(url)
        return str(resp) + ' ' + str(ocsp_request), True and ocsp_response
    except Exception as e:
        print('ERROR verify_certificate_chain:', e)
        return str(e), False


def get_chain_without_leaf(leaf_certificate, chain):
    # important in case of self signed leaf certs
    new_chain = []
    for _ in chain:
        if _.get_subject() != leaf_certificate.get_subject():
            new_chain.append(_)
    print('chain without leaf', len(new_chain))
    return new_chain
        

def get_leaf_certificate(chain):
    """
    :param chain: certificate chain
    :return: leaf certificate
    """
    leaf_cert = chain[0]
    for cert in chain:
        for cert2 in chain:
            if leaf_cert.get_subject() == cert2.get_issuer():
                leaf_cert = cert2
    return leaf_cert


def blackbox_verify(url, port=443):
    """
    :param url: target url
    :param port: target port
    :return: certificate verified (boolean)

    """  

    blackbox_server = os.getenv('BLACKBOX_SERVER') if os.getenv('BLACKBOX_SERVER') \
        else 'http://localhost'
    blackbox_port = os.getenv('BLACKBOX_PORT') if os.getenv('BLACKBOX_PORT') \
        else '9115'  
    blackbox_url='http://' + blackbox_server + ':' + blackbox_port

    timeout = 1 if not os.getenv('BLACKBOX_TIMEOUT') else os.getenv('BLACKBOX_TIMEOUT') 
    r = requests.get(blackbox_url + '/probe?target=' \
        + url + '&module=http_200_module', timeout=timeout)
    
    # crl check
    ocsp_request, ocsp_response = verify_ocsp(url)

    r_split = r.text.split('\n')
    probe_success = 0
    new_response = ''
    for _ in r_split:
        line_array = _.split(' ')
        if line_array[0] == 'probe_success':
            probe_success = line_array[1]
            new_probe_success = "1" if probe_success == "1" and ocsp_response else "0"
            new_response = new_response + 'probe_success ' + new_probe_success + '\n' 
            continue
        new_response = new_response + _ + '\n' 
    return new_response, probe_success == "1" and ocsp_response