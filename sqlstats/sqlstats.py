# a very simple query point to check mysql galera status and return json
import os, sys
from flask import Flask, render_template, json, request, jsonify
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
    if 'cleardb' in vcap:
        # using the "cleardb" service in pivotal web services
        print "Using PWS cleardb bindings"
        db_parm = vcap['cleardb'][0]
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

@app.route("/")
def main():
    return "Welcome! Maybe you meant /wsrep_status?"

def cvt_data(d):
    '''convert data from list-of-lists into dictionary'''
    r = {}
    for i in d:
        a,b = i
        r[a] = b
    return r

@app.route("/wsrep_status")
def get_mysql_galera():
    conn = mysql.connect()
    cursor = conn.cursor()
    query = 'show global status like \'wsrep_%\''
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    d = cvt_data(data)
    return json.dumps(d)
    

if __name__ == "__main__":
    port = int(os.getenv("PORT",  default=5000))
    print "starting on port",port
    app.run(host='0.0.0.0', port=port)
