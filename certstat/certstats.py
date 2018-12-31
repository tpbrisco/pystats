#!/usr/bin/env python
import getopt
import os, sys
import ssl, socket
from flask import Flask, json, request, Response


def get_cmd_opts(argv):
    # check command line -- only used if running interactively
    conf_details = {}
    # command line items accrue as encountered: "name", host, port
    try:
        options, remainder = getopt.getopt(argv, 'n:h:p:c:',
                                           ['name=', 'host=', 'port=', 'cert='])
    except getopt.GetoptError as err:
        print('ERROR:', err)
        sys.exit(1)
    for opt, arg in options:
        if opt in ('-n', '--name'):
            conf_details[arg] = {}
            sect = arg
            # initialize fields to default
            conf_details[arg]['hostname'] = ''
            conf_details[arg]['port'] = 443
            conf_details[arg]['cert'] = ''
        elif opt in ('-h', '--host'):
            conf_details[sect]['hostname'] = arg
        elif opt in ('-p', '--port'):
            conf_details[sect]['port'] = int(arg)
        elif opt in ('-c', '--cert'):
            conf_details[sect]['cert'] = arg
    return conf_details


from OpenSSL import crypto
def view_cert_details(hostname, port, cert):
    ctx = ssl.create_default_context()  # get default SSL paths
    remote_cert_pem = ssl.get_server_certificate((hostname, port))
    remote_cert = ssl.load_certificate(crypto.FILETYPE_PERM, remote_cert_pem)
    local_ca_pem = crypto.load_certificate(crypto.FILETYPE_PEM,
                                           '/etc/pki/tls/cert.pem')


def get_cert_stats(hostname, port, certpath):
    # setting capath= in create_default_context doesn't appear to work ...
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # if a CA cert path is specified, load any files in there - do it manually
    if certpath != '':
        if os.path.isdir(certpath):
            print "%s path found" % (certpath)
        else:
            print "certpath %s - directory not found" % (certpath)
            return {'state': "error", 'data': "certpath %s not found" % (certpath)}
        for f in os.listdir(certpath):
            cafile = certpath + "/" + f
            print "adding ca %s" % (cafile)
            ctx.load_verify_locations(cafile=cafile)
    ctx.verify_mode = ssl.CERT_REQUIRED
    s = ctx.wrap_socket(socket.socket(), server_hostname=hostname)
    try:
        s.connect((hostname, port))
    except (socket.gaierror, socket.error, TypeError) as e:
        return {'state': "error", 'data': "%s" % (e)}
    except ssl.CertificateError as e:
        return {'state': "error", 'data': "%s" % (e)}
    cert = s.getpeercert()
    return {'state': 'ok', 'data': cert}


app = Flask(__name__)


@app.route('/')
def usage():
    return '{"state": "error", "data": "maybe you want /ccheck?"}'


@app.route('/ccheck', methods=['POST', 'GET'])
def ccheck():
    hostname = request.args.get('hostname')
    port = request.args.get('port')
    certpath = request.args.get('certpath')
    if hostname is None:
        return '{"state": "error", "data": "no hostname=?[&port=?][&certpath=?]"}'
    if port is None:
        port = 443
    else:
        port = int(port)
    if certpath is None:
        if os.path.isdir('tls'):
            # locally supplied cert
            certpath = 'tls'
        elif os.path.isdir('/etc/pki/tls'):
            # system cert fedora
            certpath = '/etc/pki/tls/'
        elif os.path.isdir('/etc/ssl/certs'):
            # system cert ubuntu
            certpath = '/etc/ssl/certs'
        else:
            certpath = ''
    print "ccheck hostname=%s port=%d certpath=%s" % (hostname, port, certpath)
    return Response(json.dumps(get_cert_stats(hostname, port, certpath),
                               indent=2),
                    mimetype='application/json')


conf = get_cmd_opts(sys.argv[1:])
# print json.dumps(conf, indent=2)

if __name__ == '__main__'  and len(sys.argv[1:]) == 0:
    port = os.getenv("PORT", default=5000)
    debug = os.isatty(sys.stdout.fileno())  # set debug true if we're interactive
    print "Running with debug=%s" % (debug)
    app.run(host='0.0.0.0', port=port, debug=debug)

for item in conf:
    stats = get_cert_stats(conf[item]['hostname'], conf[item]['port'], conf[item]['cert'])
    stats['name'] = "%s" % (item)
    stats['hostname'] = "%s" % (conf[item]['hostname'])
    stats['port'] = "%d" % (conf[item]['port'])
    print json.dumps(stats, indent=2)
