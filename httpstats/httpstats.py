
import os, sys
import time
import requests
import logging
from prometheus_client import start_http_server, Gauge
from argparse import ArgumentParser

logging.basicConfig(level=logging.DEBUG)

def get_cmd_opts():
    TARGET_URL = os.getenv('TARGET_URL')
    logging.info("default={}".format(TARGET_URL))
    parser = ArgumentParser(
        description='Show transaction time to a URL')
    parser.add_argument('-u', '--url',
                        action='store',
                        dest='url',
                        default=TARGET_URL,
                        help='a URL to probe')
    return parser.parse_args()



def do_transact(url):
    logging.info('url:{}'.format(url))
    start = time.time()
    try:
        r = requests.get(url)
    except Exception as e:
        logging.warning("url fetch error:{}".format(e))
        return -1
    end = time.time()
    return end - start

args = get_cmd_opts()
xact_time = Gauge('http_get_time', 'Time to look up URL {}'.format(args.url))

if __name__ == "__main__":
    port = int(os.getenv("PORT", default=8000))
    logging.info("Starting; listening on {} target is {}".format(port, args.url))
    xact_time.set(do_transact(args.url))
    start_http_server(port)
    while True:
        time.sleep(30)
        xact_time.set(do_transact(args.url))
