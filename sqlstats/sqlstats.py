# a very simple query point to check mysql galera status and return json
import os, sys
import getopt
import requests
from flask import Flask, render_template, json, request, jsonify, Response
from flaskext.mysql import MySQL

# parse command line opts - return dictionary with basic params
# priority for settings variables:
#  - command line
#  - config file
#  - environment variables
# -f config.txt
# and set variables based on environment variables
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
        app.config['MYSQL_DATABASE_DB'] = ''
        app.config['MYSQL_DATABASE_HOST'] = db_parm['credentials']['hostname']
        app.config['MYSQL_DATABASE_PORT'] = int(db_parm['credentials']['port'])
    else:
        print("Could not find service %s in VCAP" % (db_service))

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
    r = {}
    for i in d:
        a,b = i
        r[a] = b
    return r

def key_match(d, m):
    '''match (m) key in dictionary (d)'''
    r = {}
    for k in d:
        if k.startswith(m):
            r[k] = d[k]
    return r

@app.route("/")
def main():
    return "Welcome! Maybe you meant /wsrep_status?"

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
    conn = mysql.connect()
    cursor = conn.cursor()
    query = 'show global status like \'%s\'' % (filter)
    print("query: %s" % (query))
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    d = cvt_data(data)
    return Response(json.dumps(d, indent=4), mimetype='application/json')
    

if __name__ == "__main__":
    port = int(os.getenv("PORT",  default=5000))
    print "starting on port",port
    app.run(host='0.0.0.0', port=port)
