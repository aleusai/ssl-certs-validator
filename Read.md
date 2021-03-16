* Usecase/Motivation

The validator is an ssl certificate verification service, which exposes several restful api endpoints to verify a particular url and its ssl certificate chain ( in a broad sense). It is also a wrapper of the widely used Prometheus Blackbox exporter, and is itself also a Prometheus exporter as it re-exports the (modified) Blackbox metrics. 

You can do the following:
1. validate a url/ssl certificate chain  with a POST request to the validator server which is forwarded to a running instance of the Prometheus Blackbox exporter
2. you can do the same as above, but the validator server itself does the validation, which allows for the use of ad hoc root anchors

Both requests can also include that in case of an invalid certificate chain, an ephemeral event be submitted to the running Prometheus Pushgateway, which is scraped by the Prometheus Server (all these components are created in docker containers, see below).
This expands on the Prometheus Blackbox exporter main functionality, allowing ssl checks alerts without pre-configuring the targets in the Prometheus Server configuration file.

Furthermore, the Blackbox exporter does not validate the certificates against an OCSP, which is instead carried out by the validator. 

The validator backend is based on Flask, which lends itself very well for quick development/deployment, but should be run in production together with e.g. Gunicorn and Nginx (!not included here!).

* Components

Validator (Flask based backend), Prometheus Pushgateway,  Prometheus Server

All the components are deployed in Docker containers. 

* Installation and Configuration

Clone the repository and change accordingly the Prometheus configuration files and `docker-compose.yml`. You can then run the script `dc-up.sh` which will build the validator backend (form its Dockerfile) and start all the relevant containers.

* Testing

Run the script `pytest.sh` to execute the pytest tests for some of the functionalities offered by the service.

* Usage

Once the containers are all up and running, the service can be used e.g. with curl calls to the api endpoints:

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"url": "https://expired.badssl.com", "toPrometheus": "True" }' -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/blackbox`  
The request is forwarded to the Prometheus Blackbox and an event is submitted to the Pushgateway if the ssl chain is invalid.
The returned json payload includes the following fields of the leaf ssl certificate in the chain: isValid, issuer, subject. 
The isValid field refers to the overall validity of the ssl certificate chain e.g. valid self signd certificates are considered invalid. 

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"url": "https://expired.badssl.com", "toPrometheus": "True" }' -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/local`  
The url and its ssl chain is checked by the validator and an event is submitted to the Pushgateway if the ssl chain is invalid.
The same payload as above is returned to the client.

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X GET  -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/data`
The `GET` route returns the submitted queries (shown in a list only up to a maximum of 1K). 

The payload for the two `POST` routes may include a `debug` option, which triggers the returning of extra information about the ssl validation outcome. 

The `local` route may also include the path to a root anchors file, which can then be used for the ssl validation (via an environment variable)


