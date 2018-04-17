# a very simple query point to check mysql galera status and return json
import os, sys
from flask import Flask, render_template, json, request, jsonify, Response
from flask.ext.mysql import MySQL

app = Flask(__name__)
mysql = MySQL()

# get service instance information, and go
vcap_svc = os.getenv("VCAP_SERVICES", "")
print "vcap_svc:", vcap_svc
if vcap_svc == '':
    print "No service bindings, defaulting to local/debug configuration"
    app.config['MYSQL_DATABASE_USER'] = 'testuser'
    app.config['MYSQL_DATABASE_PASSWORD'] = 'test123'
    app.config['MYSQL_DATABASE_DB'] = ''
    app.config['MYSQL_DATABASE_HOST'] = 'npm.inmyshorts.org'
else:
    vcap = json.loads(vcap_svc)
    db_svc = ''
    if 'cleardb' in vcap:
        # using the "cleardb" service in pivotal web services
        print "Using PWS cleardb bindings"
        db_parm = vcap['cleardb'][0]
        db_svc = 'cleardb'
    elif 'p-mysql' in vcap:
        print "Using p-mysql bindings"
        db_parm = vcap['p-mysql'][0]
        db_svc = 'p-mysql'
    elif 'core-mysql' in vcap:
        db_parm = vcap['core-mysql'][0]
        db_svc = 'core-mysql'
    app.config['MYSQL_DATABASE_USER'] = db_parm['credentials']['username']
    app.config['MYSQL_DATABASE_PASSWORD'] = db_parm['credentials']['password']
    app.config['MYSQL_DATABASE_DB'] = ''
    app.config['MYSQL_DATABASE_HOST'] = db_parm['credentials']['hostname']

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
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    d = cvt_data(data)
    return Response(json.dumps(d, indent=4), mimetype='application/json')
    

if __name__ == "__main__":
    port = int(os.getenv("PORT",  default=5000))
    print "starting on port",port
    app.run(host='0.0.0.0', port=port)
