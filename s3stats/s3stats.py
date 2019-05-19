# a very simple prometheus exporter for S3 I/O times
import os
from prometheus_client import start_http_server, Summary
import boto3
import time, configparser
import random, string		# for generating data for object storage


def conf_load():
    '''load configuration file'''
    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'DEFAULT' not in config:
        raise KeyError("No [DEFAULT] section in configuration")
    return config['DEFAULT']


def s3_initialize(conf):
    '''initialize s3 session parameters'''
    # rely on AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in
    # the environment for boto.  This is about the worst way to do this - but this
    # is just the prototype.
    k = os.getenv('AWS_ACCESS_KEY_ID')
    s = os.getenv('AWS_SECRET_ACCESS_KEY')
    if k is None or k == '' or \
       s is None or s == '':
        raise KeyError('No AWS access and secret keys in the environment')
    if 's3uri' in conf:
        s3 = boto3.client('s3', endpoint_url=conf['s3uri'])
    else:
        s3 = boto3.client('s3')
    return s3


def s3_bucket_create(s3):
    start = time.time()
    name = '%dmybucket' % (os.getpid())
    s3.create_bucket(Bucket=name)
    end = time.time()
    return end - start, name


def s3_bucket_delete(s3, name):
    start = time.time()
    s3.delete_bucket(Bucket=name)
    end = time.time()
    return end - start


def s3_put_object(s3, bname, size):
    # generate random string of 'size' length
    noise = ''.join(random.choice(string.hexdigits) for i in range(size))
    obj_name = '%d_obj' % (os.getpid())
    start = time.time()
    s3.put_object(Body=noise, Key=obj_name, Bucket=bname)
    end = time.time()
    return end - start, obj_name


def s3_delete_object(s3, bname, oname):
    start = time.time()
    s3.delete_object(Bucket=bname, Key=oname)
    end = time.time()
    return end - start


stats = []
conf = conf_load()
# initialize
if 'sleep_time' in conf:
    stats_sleep_time = int(conf['sleep_time'])
else:
    stats_sleep_time = 30
s3 = s3_initialize(conf)

print('sleeping %d seconds' % (stats_sleep_time))
if 's3uri' in conf:
    print('using s3 target %s' % (conf['s3uri']))
ctime, b_name = s3_bucket_create(s3)
print('create bucket name: %s time: %f' % (b_name, ctime))
dtime,  o_name = s3_put_object(s3, b_name, 4096)
print('4K object put %f' % (dtime))
dtime,  o_name = s3_put_object(s3, b_name, 8192)
print('8K object put %f' % (dtime))
dtime,  o_name = s3_put_object(s3, b_name, 16384)
print('16K object put %f' % (dtime))
dtime = s3_delete_object(s3, b_name, o_name)
print('object %s del %f' % (o_name, dtime))
dtime = s3_bucket_delete(s3, b_name)
print('delete bucket name: %s time: %f' % (b_name, dtime))

new_stat = {}
new_stat['bucket_create'] = {
    'name': 'bucket_create',
    'summary': Summary('bucket_create', 'Time to create a new bucket')}
new_stat['bucket_delete'] = {
    'name': 'bucket_delete',
    'summary': Summary('bucket_delete', 'Time to destroy bucket')}
new_stat['object_create_4k'] = {
    'name': 'object_create_4k',
    'summary': Summary('object_create_4k', 'Time to create 4K object')}
new_stat['object_create_8k'] = {
    'name': 'object_create_8k',
    'summary': Summary('object_create_8k', 'Time to create 8K object')}
new_stat['object_create_16k'] = {
    'name': 'object_create_16k',
    'summary': Summary('object_create_16k', 'Time to create 18K object')}
new_stat['object_delete'] = {
    'name': 'object_delete',
    'summary': Summary('object_delete', 'Time to create delete object')}
# eventually, we want multiple s3 targets
stats.append(new_stat.copy())

if __name__ == '__main__':
    port = os.getenv("PORT", default=8005)
    start_http_server(int(port))
    #
    while True:
        c_time, b_name = s3_bucket_create(s3)
        stats[0]['bucket_create']['summary'].observe(c_time)
        d_time, o_name = s3_put_object(s3, b_name, 4096)
        stats[0]['object_create_4k']['summary'].observe(d_time)
        d_time, o_name = s3_put_object(s3, b_name, 8192)
        stats[0]['object_create_8k']['summary'].observe(d_time)
        d_time, o_name = s3_put_object(s3, b_name, 16384)
        stats[0]['object_create_16k']['summary'].observe(d_time)
        d_time = s3_delete_object(s3, b_name, o_name)
        stats[0]['object_delete']['summary'].observe(d_time)
        d_time = s3_bucket_delete(s3, b_name)
        stats[0]['bucket_delete']['summary'].observe(d_time)
        time.sleep(stats_sleep_time)
