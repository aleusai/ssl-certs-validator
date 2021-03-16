from OpenSSL import SSL
from socket import socket, setdefaulttimeout, gaierror
import sys
import validators
from ssl_check import verify_certificate_chain as vcc

# socket timeout (to avoid blocking connections)
setdefaulttimeout(2)


def get_certificate_info(url, blackbox=True, debug=False):
    """
    :param url: target url
    :param debug: debug option
    :return: certficate, result (dictionary)
    """
    if not validators.url(url):
        return '', {
            'subject': '',
            'issuer': '',
            'isValid': None,
            'Error': 'There was an Error with your request: invalid url'
        }
   
    try: 
        cert, chain = vcc.get_remote_chain(url)
        leaf_cert = vcc.get_leaf_certificate(chain)
        # issuer
        issuer = cert.get_issuer()
        # leaf_issuer = leaf_cert.get_issuer()
        issuer_str = "".join("/{0:s}={1:s}".format(name.decode(), value.decode())
                            for name, value in issuer.get_components())
        # leaf_issuer_str = "".join("/{0:s}={1:s}".format(name.decode(), value.decode())
        #                    for name, value in leaf_issuer.get_components())
        # subject
        subject = cert.get_subject()
        # leaf_subject = leaf_cert.get_subject()
        subject_str = "".join("/{0:s}={1:s}".format(name.decode(), value.decode())
                            for name, value in subject.get_components())
        # leaf_subject_str = "".join("/{0:s}={1:s}".format(name.decode(), value.decode())
        #                    for name, value in leaf_subject.get_components())

        # leaf_common_name_str = "".join("{1:s}".format(name.decode(), value.decode())
        #                    for name, value in leaf_subject.get_components() if name.decode() == 'CN')        
        
        # validity    
        if blackbox:    
            blackbox_info, is_valid = vcc.blackbox_verify(url)         
        else: 
            info, is_valid = vcc.verify_certificate_chain(url)   

        if debug:
            if blackbox:
                print('DEBUG')
                return cert, {
                    'subject': subject_str,
                    'issuer': issuer_str,
                    'isValid': is_valid,
                    "debug": blackbox_info
                } 
            else:
                return cert, {
                    'subject': subject_str,
                    'issuer': issuer_str,
                    'isValid': is_valid,
                    'debug': info
                }                            
        else:
            return cert, {
                'subject': subject_str,
                'issuer': issuer_str,
                'isValid': is_valid
            }


    except (SSL.WantReadError, SSL.Error, OSError, gaierror):
        if debug:
            return '',  {
            'subject': '',
            'issuer': '',
            'isValid': None,
            'debug': 'The connection could not be established or ssl handshake failed or timeout ended or hostname does not exist)'
            }
        else:
            return '',  {
            'subject': '',
            'issuer': '',
            'isValid': None
            }          
    
    except Exception as e:
        error = sys.exc_info()[0]
        #print(error)
        if debug:
            return '', {
            'subject': '',
            'issuer': '',
            'isValid': None,
            'debug': 'There was an Error with your request'
        }
        else:
            return '', {
            'subject': '',
            'issuer': '',
            'isValid': None
            }
