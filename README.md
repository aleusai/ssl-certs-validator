# ssl-certs-validator

## Use case/Motivation

The validator is an ssl certificate verification service, which exposes several restful api endpoints to verify a particular url and its ssl certificate chain ( in a broad sense). It is also a wrapper of the widely used Prometheus Blackbox exporter, and is itself also a Prometheus exporter as it re-exports the (modified) Blackbox metrics. 

You can do the following:
1. validate a url/ssl certificate chain  with a POST request to the validator server which is forwarded to a running instance of the Prometheus Blackbox exporter; the result is the ANDed with the OCSP check from the validator
2. you can do the same as above, but the validator server itself does the whole validation, which also allows for the use of ad hoc root anchors

Both requests can also include that in case of an invalid certificate chain, an ephemeral event be submitted to the running Prometheus Pushgateway, which is scraped by the Prometheus Server (all these components are created in docker containers, see below).
This expands on the Prometheus Blackbox exporter main functionality, allowing ssl checks alerts without pre-configuring the targets in the Prometheus Server configuration file.

As a further xtension, the Blackbox exporter does not validate the certificates against an OCSP (it does not have this functionality), which is instead carried out by the validator. 

The validator backend is based on Flask, which lends itself very well for quick development/deployment, but should be run in production together with e.g. Gunicorn and Nginx (!not included here!).

## Installation and Configuration

Clone the repository and change accordingly the Prometheus configuration files and `docker-compose.yml`. 
The environment setting requires the existance of a `.env` file with the setting of the environment variables USERNAME and PASSWORD, which are then passed to the docker-file: they are used to authenticate with the Flask backend. Other environment variables that can be set are:
- PUSH_GATEWAY_SERVER  the hostname of the Pushgateway server
- PUSH_GATEWAY_PORT  the port the Pushgateway server is listening to (default value is 9091)
- PUSH_GATEWAY_TIMEOUT  the timeout for the connection to the Pushgateway server (default value is 1s)
- BLACKBOX_SERVER the hostname of the Blackbox server
- BLACKBOX_PORT the port the Blackbox server is listening to (default value is 9115)
- BLACKBOX_TIMEOUT the timeout for the connection to the Blackbox server (default value is 1s)
- CA_PEM_FILE this optional variable allows you to use your own ad hoc certificate anchors for the ssl chain validation (instead of the ones installed with the OS on the disk); it must point to your own file (in the root directory of the repository, so that is copied into the Docker container) containing your root ca anchors, and will be used by the validator when using the `local` endpoint (see below). The file will be copied to `/app` in the container and so this environment variable must be set to `/app/<YOUR_ANCHORS_FILE>` 

You can then run the script `dc-up.sh` which will build the validator backend (from its Dockerfile) and start the other containers.

The following docker containers will be created:
- The Prometheus server, which is confgured (see the file `prometheus/prometheus.orig.yml`) to scrape the Pushgateway server and the Flask based validator: this latter one is scraped as if it were a Blackbox server, with some example urls
- The Pushgateway server, which can receive in push mode events to be scraped (from the validator)
- The Flask based validator, which can validate certificates "locally" or via an external Blackbox server; it can push events to the Pushgateway, and can be scraped directly by the Prometheus server
- The Blackbox exporter, which is used by the validator (it is NOT scraped directly by the Prometheus server in this setup)

## Testing

Run the script `pytest.sh` to execute the pytest tests for some of the functionalities offered by the service. You will need to set the USERNAME and PASSWORD variables (see above) as well as optionally DOCKERUP, which triggers also the tests against the Blackbox and Pushgateway services.

## Usage

Once the containers are all up and running, the service can be used e.g. with curl calls to the api endpoints:

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"url": "https://expired.badssl.com", "toPrometheus": "True" }' -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/blackbox`  

The request in this case is forwarded to the Prometheus Blackbox server and an event is submitted to the Pushgateway (flag `toPrometheus`) if the ssl chain is found to be invalid. Notice that the validator adds the OCSP check to the overall result from the Prometheus Blackbox i.e. the two are ANDed and for a certificate chain to be considered valid both must be successful.
The returned json payload includes the following fields of the leaf ssl certificate in the chain: `isValid`, `issuer`, `subject`. 
The `isValid` field refers to the overall validity of the ssl certificate chain e.g. valid self signd certificates are considered invalid. Also, the `subject` field may or not refer to the leaf certificate, e.g. if the chain order is not respected.

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{"url": "https://expired.badssl.com", "toPrometheus": "True" }' -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/local`  

The url and its ssl chain are checked by the validator and an event is submitted to the Pushgateway if the ssl chain is invalid.
The same payload as above is returned to the client.

`curl -v -H "Accept: application/json" -H "Content-type: application/json" -X GET  -u <USERNAME>:<PASSWORD> http://127.0.0.1:5000/api/data`

The `GET` route returns the submitted queries (shown in a list up to a maximum of 1K). 

The payload for the two `POST` routes may include a `debug` option, which triggers the returning of extra information about the ssl validation outcome. 

When starting the server, a file with ad hoc root anchors can be passed (see the `docker-compose.yml` file), via the environment variable `CA_PEM_FILE`. The file should be present in the root directory at start time, so that it can be copied into the Flask docker container. The ad hoc root anchors will then be used for the ssl validation when using the `local` route.

One final endpoint `/api/sb` can be used to scrape the validator server, as a Prometheus exporter: the scraped information is the same as the Blackbox server, with the addition of the OCSP validation: this endpoint can be used by the Prometheus server for predefined targets to scrape, as is usually done with the Blackbox exporter. 

Once all the containers are up and running, you will be able to open the browser at http://localhost:9090 which will show the Prometheus Server page: three types of alerts are defined i.e. `Node Down`, `CertProblem` and `StaticBlackboxCertProblem`. The first one will be triggered if a static target is not reachable (see the targets under 'Status' in case in the page), the second one is triggered by the scraping of the Pushgateway and refers to the 'dynamic' cert validation failures, while the third refers still to the scraped static ones, when a cert failure was registered. These are just examples, and can be changed as desired via the configuration files.
