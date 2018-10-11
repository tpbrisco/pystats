# very simple redis test
#
import sys, os
import redis
import time
import getopt
import random, string
import configparser
from flask import Flask, json, request, Response

def get_cmd_opts():
    '''get command options - look in environment or command line for parameters'''
    stat_redis_svc = os.getenv('STAT_REDIS_SVC')
    # next are only used if no service is discovered or specified
    stat_redis_pass = os.getenv('STAT_REDIS_PASS')
    stat_redis_host = os.getenv('STAT_REDIS_HOST')
    stat_redis_port = os.getenv('STAT_REDIS_PORT')

    # get variables from command line
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 's:p:h:o:', [
            'service=', 'password=', 'host=', 'port='])
    except getopt.GetoptError as err:
        print('ERROR:', err)
        sys.exit(1)

    for opt, arg in options:
        if opt in ('-s', '--service'):
            stat_redis_svc = arg
        elif opt in ('-p', '--password'):
            stat_redis_pass = arg
        elif opt in ('-h', '--host', '--hostname'):
            stat_redis_host = arg
        elif opt in ('-o', '--port'):
            stat_redis_port = arg

    vcap_svc = os.getenv('VCAP_SERVICES', '')
    print("vcap_svc:", vcap_svc)
    if vcap_svc == '':
        print("No service bindings, defaulting to local/debug configuration")
    else:
        vcap = json.loads(vcap_svc)
        print("Using %s bindings" % (stat_redis_svc))
        if stat_redis_svc in vcap:
            r_svc = vcap[stat_redis_svc][0]['credentials']
            print ("bindings: %s" % (json.dumps(r_svc)))
            stat_redis_pass = r_svc['password']
            stat_redis_host = r_svc['host']
            stat_redis_port =  r_svc['port']
        else:
            # can't find service in environment
            stat_redis_pass = stat_redis_host = stat_redis_port = None
    print ("svc: %s pass: %s host: %s port: %s\n" %
           (stat_redis_svc, stat_redis_pass, stat_redis_host, stat_redis_port))
    return (stat_redis_svc, stat_redis_pass,
            stat_redis_host, stat_redis_port)

(r_service, r_password, r_host, r_port) = get_cmd_opts()
if (r_host == '') or (r_password == '') or (r_port == ''):
    print("Need to supply a redis host, password and port\n")
    sys.exit(1)

app = Flask(__name__)
print ("Redis svc: %s pass: %s host: %s port: %s\n" %
           (r_service, r_password, r_host, r_port))
app.config['REDIS_DATABASE_PASS'] = r_password
app.config['REDIS_DATABASE_HOST'] = r_host
app.config['REDIS_DATABASE_PORT'] = int(r_port)

@app.route("/")
def main():
    return "Welcome! Things arent quite ready yet"

@app.route("/bench")
def bench():
    ans = dict()
    r = redis.Redis(host=app.config['REDIS_DATABASE_HOST'],
                    port=app.config['REDIS_DATABASE_PORT'],
                    password=app.config['REDIS_DATABASE_PASS'])

    for noise_len in [ 5, 128, 512, 1024, 4096 ]:
        noise = ''.join(random.choice(string.hexdigits) for i in range(noise_len))
        start = time.time()
        r.set('foo', noise)
        value = r.get('foo')
        end = time.time()
        ans['string%d' % (noise_len)] = end - start

    # r.release()
    return Response(json.dumps(ans, indent=2),
                    mimetype='application/json')

if __name__ == "__main__":
    port = int(os.getenv("PORT", default=5000))
    print("starting on %d" % (port))
    app.run(host='0.0.0.0', port=port)
