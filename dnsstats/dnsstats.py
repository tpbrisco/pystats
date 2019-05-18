# a very simple prometheus exporter for DNS lookup times
import sys, os
import dns.resolver, dns.name
from prometheus_client import start_http_server, Summary, Gauge
import time
import configparser

def dns_lookup(resolver_ip, resolver, hostname):
    '''return the time it took to look up a hostname'''
    print('Looking up %s with %s' % (hostname, resolver_ip))
    resolver.nameservers = [ resolver_ip ]
    start = time.time()
    try:
        answers = resolver.query(hostname, 'A')
    except dns.exception.Timeout as e:
        print("%s" % str(e)) # ignore this, we just need the timing
    except dns.resolver.NXDOMAIN as e:
        print("NXDOMAIN %s" % str(e)) # ignore this, we just need the timing
    end = time.time()
    return end - start

def conf_load():
    '''load configuration file'''
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'DEFAULT' in config:
        raise KeyError("No [DEFAULT] section in configuration")
    return config['DEFAULT']

# figure out how many dns servers are configured
resolver = dns.resolver.Resolver()
resolvers = resolver.nameservers.copy()
no_resolvers = len(resolver.nameservers)

# Set up data structures for prometheus
# We have an array of a dictionary.
# Stats
# 	The index of the 'stats' array is the index of the nameserver.
# 	The dictionary contains
#     	good/bad relative/fqdn lookup
# 			name: the hostname to look up
# 			summary: the prometheus summary object for it
stats = []
conf = conf_load()
print("{0} resolvers".format(no_resolvers))
for i in range(0, no_resolvers):
    new_stat = {}
    name = 'ip_%s_dns_' % resolvers[i]
    name = name.replace('.', '_')   # make acceptable prometheus metric name
    new_stat['good_fqdn'] = {'name':  conf['good_fqdn'],
                             'summary': Gauge(name + 'good_fqdn_time',
                                                'Time spent on good FQDN DNSlookup')}
    new_stat['bad_fqdn'] = {'name': conf['bad_fqdn'],
                            'summary': Gauge(name + 'bad_fqdn_time',
                                               'Time spent on bad FQDN DNS lookup')}
    new_stat['good_rel'] = {'name': conf['good_rel'],
                            'summary': Gauge(name + 'good_rel_time',
                                               'Time spent on good relative DNS lookup')}
    new_stat['bad_rel'] = {'name': conf['bad_rel'],
                           'summary': Gauge(name + 'bad_rel_time',
                                              'Time spent on bad relative DNS lookup')}
    stats.append(new_stat.copy())
    print("\t{0}".format(resolver.nameservers[i]))
print("Len of stats -> {0}".format(len(stats)))

if __name__ == '__main__':
    # find assigned port number
    port = os.getenv("PORT", default=8005)
    # start up the server to expose metrics
    start_http_server(int(port))
    # generate some data
    while True:
        for nr in range(0, no_resolvers):
            rip = resolvers[nr]
            stats[nr]['good_fqdn']['summary'].set(dns_lookup(rip, resolver, stats[nr]['good_fqdn']['name']))
            stats[nr]['bad_fqdn']['summary'].set(dns_lookup(rip, resolver, stats[nr]['bad_fqdn']['name']))
            stats[nr]['good_rel']['summary'].set(dns_lookup(rip, resolver, stats[nr]['good_rel']['name']))
            stats[nr]['bad_rel']['summary'].set(dns_lookup(rip, resolver, stats[nr]['bad_rel']['name']))
        time.sleep(30)
        
