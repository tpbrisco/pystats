# a very simple query point to check mysql galera status and return json
import os, sys
import getopt
import requests
from flask import Flask, render_template, json, request, Response
from flaskext.mysql import MySQL
import pymysql

# parse command line opts - return dictionary with basic params
# priority for settings variables:
#  - environment variables
#  - command line
def get_cmd_opts():
    '''get command options - look in environment or command line for parameters'''
    # Environment variables (e.g. STAT_DBSVC) are best in cloud foundry environments,
    # while CLI flags are best in debugging environment (-u,-p,-h)
    #
    # set variables based on environment variables first
    stat_dbsvc=os.getenv('STAT_DBSVC')
    # next are really only used if no database service is discovered
    stat_dbusr=os.getenv('STAT_DBUSR')
    stat_dbpwd=os.getenv('STAT_DBPWD')
    stat_dbdb=os.getenv('STAT_DBDB')
    stat_dbhost=os.getenv('STAT_DBHOST')
    # get variables from config file
    # "pass" for now
    # get variables from command line, which override environment variables
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 's:u:p:d:h:', ['service=',
                                                                   'username=',
                                                                   'password=',
                                                                   'database=',
                                                                   'host='])
    except getopt.GetoptError as err:
        print('ERROR:', err)
        sys.exit(1)
    
    for opt, arg in options:
        if opt in ('-s', '--service'):
            stat_dbsvc = arg
        elif opt in ('-u', '--username'):
            stat_dbusr = arg
        elif opt in ('-p', '--password'):
            stat_dbpwd = arg
        elif opt in ('-d', '--database'):
            stat_dbdb = arg
        elif opt in ('-h', '--host'):
            stat_dbhost = arg

    return (stat_dbsvc, stat_dbusr, stat_dbpwd, stat_dbdb, stat_dbhost)

app = Flask(__name__)
mysql = MySQL()

# get service or command options for specifying database
(db_service, db_username, db_password, db_database, db_host) = get_cmd_opts()

# get service instance information, and go
vcap_svc = os.getenv("VCAP_SERVICES", "")
print "vcap_svc:", vcap_svc
if vcap_svc == '':
    print "No service bindings, defaulting to local/debug configuration"
    app.config['MYSQL_DATABASE_USER'] = db_username # 'your_test_user'
    app.config['MYSQL_DATABASE_PASSWORD'] = db_password # 'your_test_pass'
    app.config['MYSQL_DATABASE_DB'] = db_database # ''
    app.config['MYSQL_DATABASE_HOST'] = db_host # 'your_test_host'
else:
    # examples: cleardb, p-mysql, core-mysql - whatever you bind your service
    # as, or "mysql" if you use the supplied shell script
    vcap = json.loads(vcap_svc)
    if db_service in vcap:
        # using the "cleardb" service in pivotal web services
        print("Using %s bindings" % (db_service))
        db_parm = vcap[db_service][0]
        app.config['MYSQL_DATABASE_USER'] = db_parm['credentials']['username']
        app.config['MYSQL_DATABASE_PASSWORD'] = db_parm['credentials']['password']
        app.config['MYSQL_DATABASE_DB'] = db_parm['credentials']['name']
        app.config['MYSQL_DATABASE_HOST'] = db_parm['credentials']['hostname']
        app.config['MYSQL_DATABASE_PORT'] = int(db_parm['credentials']['port'])
    else:
        print("Could not find service %s in VCAP" % (db_service))
        sys.exit(1)

mysql.init_app(app)

'''
demo code for interactive troubleshooting
conn = mysql.connect()
cursor = conn.cursor()
query = 'show global status like \'wsrep_%\''
cursor.execute(query)
data = cursor.fetchall()
'''

def cvt_data(d):
    '''convert data from list-of-lists into dictionary'''
    r = dict()
    for i in d:
        a = i[0]
        b = [str(x) for x in i[1:]]
        r[a] = b
    return r

def key_filter(d, m):
    '''return dictionary keys found in list m'''
    r = dict()
    r = {k_key: d[k_key] for k_key in m}
    return r

def nway_equal(ek, dl):
    equal_state = False
    last_val = ''
    for k in dl:
        if last_val == '':
            last_val = dl[k][ek]
        else:
            if dl[k][ek] != last_val:
                return False
    return True

def nway_delta(ck, dv, mv, dl):
    '''check differences between key ck - max delta (dv) and max value (mv)'''
    delta_state = False
    last_val = ''
    for k in dl:
        if last_val == '':
            last_val = float(dl[k][ck])
            if last_val > mv:
                return False
        else:
            cur_val = float(dl[k][ck])
            if cur_val > mv:
                return False
            if abs(cur_val - last_val) > dv:
                return False
    return True
        

@app.route("/")
def main():
    return "Welcome! Maybe you meant /wsrep_status?"

@app.route("/proclist", methods=['GET', 'POST'])
def get_processlist():
    '''query data for process list'''
    
    try:
        conn = mysql.connect()
    except pymysql.err.OperationalError as e:
        print("exception type:",type(e)," e:",e)
        answer = {"summary": {'replication_ok': False, 'cluster_ok': False},
                  "ready": "false",
                  "message": str(e)}
        return Response(json.dumps(answer, indent=4), mimetype='application/json')
    cursor = conn.cursor()
    query = "show processlist"
    cursor.execute(query)
    data = cursor.fetchall()
    print("data:", data)
    conn.close()
    d = cvt_data(data)
    return Response(json.dumps(d, indent=4), mimetype='application/json')

@app.route("/wsrep_all", methods=['GET', 'POST'])
def get_galera_all():
    '''query database for ALL galera members'''
    
    try:
        conn = mysql.connect()
    except pymysql.err.OperationalError as e:
        print("exception type:",type(e)," e:",e)
        answer = {"summary": {'replication_ok': False, 'cluster_ok': False},
                  "ready": "false",
                  "message": str(e)}
        return Response(json.dumps(answer, indent=4), mimetype='application/json')
    cursor = conn.cursor()
    query = "show global status like \'wsrep_%'"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    d = cvt_data(data)
    if 'wsrep_incoming_addresses' not in d:
        r = {"ready": False,
             "status": "connection to %s failed" % (app.config['MYSQL_DATABASE_HOST'])}
        return json.dumps(r, indent=4), 404  # not found
    host_list = d['wsrep_incoming_addresses']
    host_vars = {}
    for hp in host_list.split(','):
        h,p = hp.split(':')
        if h == '127.0.0.1':
            continue
        odb = pymysql.Connection(host=h,
                              user=app.config['MYSQL_DATABASE_USER'],
                              passwd=app.config['MYSQL_DATABASE_PASSWORD'],
                              db=app.config['MYSQL_DATABASE_DB'])
        cur = odb.cursor()
        cur.execute("show global status like \'wsrep_%\'")
        host_vars[h] = cvt_data(cur.fetchall())
        odb.close()
    # check if cluster is on
    if 'wsrep_ready' in d:
        if d['wsrep_ready'] != "ON":
            return json.dumps({"status": json.dumps(d, indent=4), "ready": False}, indent=4)
    # filter the results in "host_vars" down to those we're interested in for
    # cluster formation and replication performance
    cluster_health = {}
    cluster_keys = [ 'wsrep_cluster_size', 'wsrep_cluster_status',
                    'wsrep_cluster_conf_id', 'wsrep_cluster_state_uuid',
                    'wsrep_ready', 'wsrep_connected', 'wsrep_local_state_comment'  ]
    for h in host_vars:
        cluster_health[h] = key_filter(host_vars[h], cluster_keys)
    rep_health = {}
    rep_keys = ['wsrep_local_recv_queue_avg', 'wsrep_flow_control_paused',
                'wsrep_cert_deps_distance', 'wsrep_local_send_queue_avg'  ]
    for h in host_vars:
        rep_health[h] = key_filter(host_vars[h], rep_keys)
    # generate a summary message
    summary = {}
    cluster_ok = True
    for k in cluster_keys:
        if not nway_equal(k, host_vars):
            cluster_ok = False
            break
    summary['cluster_ok'] =  cluster_ok
    replication_ok = True
    for k in rep_keys:
        if not nway_delta(k, 0.2, 2.0, host_vars):
            replication_ok = False
            break
    summary['replication_ok'] = replication_ok
    # finally, convert all the hashes cluster_health and rep_health data into arrays
    cluster_list = []
    rep_list = []
    for h in cluster_health:
        cluster_list.append({'host': h, 'status': cluster_health[h]})
    for r in rep_health:
        rep_list.append({'host': r, 'status': rep_health[r]})
    answer = {"summary": summary,
              "cluster": cluster_list,
              "replication": rep_list,
              "ready": True  }
    return Response(json.dumps(answer, indent=4), mimetype='application/json')

@app.route("/wsrep_status", methods=['GET', 'POST'])
def get_mysql_galera():
    '''query database for galera wsrep_status, default filter=wsrep_cluster_%'''
    filter = 'wsrep_cluster_%'
    if request.method == 'POST':
        if 'filter' in request.form:
            filter = request.form['filter']
    elif request.method == 'GET':
        new_filter = request.args.get('filter')
        if new_filter != None:
            filter = new_filter
    try:
        conn = mysql.connect()
    except pymysql.err.OperationalError as e:
        print("exception type:",type(e)," e:",e)
        answer = {"summary": {'replication_ok': False, 'cluster_ok': False},
                  "ready": "false",
                  "message": str(e)}
        return Response(json.dumps(answer, indent=4), mimetype='application/json')
    cursor = conn.cursor()
    query = 'show global status like \'%s\'' % (filter)
    print("query: %s" % (query))
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    d = cvt_data(data)
    d['ready'] = True
    return Response(json.dumps(d, indent=4), mimetype='application/json')
    

if __name__ == "__main__":
    port = int(os.getenv("PORT",  default=5000))
    print "starting on port",port
    app.run(host='0.0.0.0', port=port)
