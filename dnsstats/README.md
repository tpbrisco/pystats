# pystats/dnsstats

Part of the pystats collection, DNS-STATS provides a Prometheus
interface into DNS statistics.

## Getting Started

This is designed for Cloud Foundry implementations, but the
application can be run locally for testing, or harnessed under
gunicorn rather simply.

### Prerequisites
dns-stats requires the pythondns and prometheus-client libraries.
Specific versions used during development are indicated in the
requirements.txt file.  Using pip can ready the environment for
deployment, or virtualenv can be used for debugging/testing.

### Running locally or deploying
```bash
# for development
virtualenv dev
pip install -r requirements.txt
python3 dnsstats.py

# for pushing into cloud foundry
bash vendor.sh
cf push
```

