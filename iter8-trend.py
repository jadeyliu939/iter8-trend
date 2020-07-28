#!/usr/local/Cellar/python/3.7.6_1/bin/python3.7
##!/usr/bin/python

from __future__ import print_function
from kubernetes import client, config
from dateutil.parser import parse
from datetime import datetime, timezone
from string import Template
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from http.server import HTTPServer, BaseHTTPRequestHandler
from signal import signal, SIGINT
import requests
import json
import time
import threading
import logging
import os
import argparse
import sys

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filemode='a')
logger = logging.getLogger(__name__)

# Represents an Iter8 Experiment Custom Resource
class Experiment:
    def __init__(self, e=None):
        if e is None:
            return

        if 'metadata' in e and 'namespace' in e['metadata']:
            self.namespace = e['metadata']['namespace']
        if 'metadata' in e and 'name' in e['metadata']:
            self.name = e['metadata']['name']
        if 'status' in e and 'phase' in e['status']:
            self.phase = e['status']['phase']

        if 'spec' in e and 'service' in e['spec']:
            if 'baseline' in e['spec']['service']:
                self.baseline = e['spec']['service']['baseline']
            if 'candidates' in e['spec']['service']:
                self.candidates = e['spec']['service']['candidates']
            if 'name' in e['spec']['service']:
                self.service_name = e['spec']['service']['name']
            else:
                # supporting service-based experiment no longer guarantees
                # 'service.name` always exists
                if 'hosts' in e['spec']['service']:
                    self.service_name = e['spec']['service']['hosts'][0]['name']
                else:
                    # this should never happen
                    logger.warning(f"Cannot identify a unique identifier for this experiment {e['spec']['service']}")
                    self.service_name = "unidentified"

        # Defaults winner to baseline
        self.winner = self.baseline
        self.winner_found = False
        self.winner_data = {}
        self.is_completed_and_successful = False
        if 'status' in e:
            self.start_time = e['status']['startTimestamp']
            self.end_time = e['status']['endTimestamp']

            if 'assessment' in e['status']:
                if 'winner' in e['status']['assessment']:
                    winner = e['status']['assessment']['winner']
                    if winner['winning_version_found'] == True and self.phase == 'Completed':
                        # Only a Completed and Successful experiment is promoted
                        self.is_completed_and_successful = True
                        if 'current_best_version' in winner:
                            self.winner = winner['current_best_version']

                    # Find winner amongst baseline and candidates
                    if 'baseline' in e['status']['assessment']:
                        if 'name' in e['status']['assessment']['baseline']:
                            if e['status']['assessment']['baseline']['name'] == self.winner:
                                self.populate_winner_data(e['status']['assessment']['baseline']['criterion_assessments'])
                                self.winner_found = True

                    if not self.winner_found and 'candidates' in e['status']['assessment']:
                        for candidate in e['status']['assessment']['candidates']:
                            if candidate['name'] == self.winner:
                                self.populate_winner_data(candidate['criterion_assessments'])
                                break

        # Used by Kiali only. Initialize to unknown since this data is populated
        # by Istio and put into Prometheus
        self.winner_app = 'unknown'
        self.winner_version = 'unknown'

    # Populates self.winner_data
    def populate_winner_data(self, assessments):
        for assessment in assessments:
            id = assessment['id']
            data = assessment['statistics']['value']
            self.winner_data[id] = data

    # Prints an Experiment Custom Resource
    def __str__(self):
        s = f"{self.namespace}.{self.name}(service:{self.service_name}, " \
            f"baseline:{self.baseline}, candidates:{self.candidates}): " \
            f"{self.phase} ({self.start_time} - {self.end_time}) [{self.winner_data}]"
        return s

    # We also get resource utilization data along with metric data, and
    # this function generates the prometheus query string
    def get_resource_query_str(self, query_template, podname):
        start = parse(self.start_time)
        end = parse(self.end_time)
        now = datetime.now(timezone.utc)
        interval = end-start
        interval_str = str(int(interval.total_seconds())) + 's'
        offset = now-end
        offset_str = str(int(offset.total_seconds())) + 's'

        kwargs = {
            "interval": interval_str,
            "offset_str": f" offset {offset_str}",
            "podname": f"{podname}",
            "namespace": self.namespace,
        }
        query_template = Template(query_template)
        query = query_template.substitute(**kwargs)
        return query

# This is the main engine that watches a K8s cluster for Iter8 Experiment
# Custom Resources and query Prometheus for summary performance metrics
# It also provides a Prometheus scrape target endpoint
class Iter8Watcher:
    def __init__(self, args):

        # Prometheus URL that is used to gather metrics data
        self.prometheus_url = args.prometheus_url + '/api/v1/query'

        # Port used for Prometheus to scrape trend data
        self.scrape_port = args.scrape_port

        # Port used for Kubernetes health checking
        self.healthcheck_port = args.healthcheck_port

        # Number of seconds between listing Iter8 Experiment CRs in K8s cluster
        self.k8s_freq = args.k8s_freq

        # Initialize kubernetes.client.configuration either from a config file or
        # when running within a pod using a service account
        try:
            config.load_kube_config()
        except:
            config.load_incluster_config()
        self.kubeapi = client.CustomObjectsApi()

        # All experiments in the cluster
        self.experiments = dict()

    # At the start, we read existing iter8_trend data from Prometheus so
    # we don't end up re-calculating metric data for existing experiments
    def load_data_from_prometheus(self):
        logger.info("Loading data from Prometheus...")
        data = self.query_prometheus('iter8_trend')
        for res in data:
            if 'metric' in res and 'value' in res:
                m = res['metric']
                v = res['value']
                if 'namespace' in m and 'name' in m:
                    exp = None
                    key = m['namespace'] + ':' + m['name']
                    if key in self.experiments:
                        exp = self.experiments[key]
                    else:
                        exp = Experiment()
                        exp.winner_data = {}
                        exp.namespace = m['namespace']
                        exp.name = m['name']

                        if 'baseline' in m:
                            exp.baseline = m['baseline']
                        else:
                            exp.baseline = 'unknown'

                        if 'winner' in m:
                            exp.winner = m['winner']
                        else:
                            exp.winner = 'unknown'

                        if 'phase' in m:
                            exp.phase = m['phase']
                        else:
                            exp.phase = 'unknown'

                        if 'start_time' in m:
                            exp.start_time = m['start_time']
                        else:
                            exp.start_time = 'unknown'

                        if 'app' in m:
                            exp.winner_app = m['app']
                        else:
                            exp.winner_app = 'unknown'

                        if 'version' in m:
                            exp.winner_version = m['version']
                        else:
                            exp.winner_version = 'unknown'

                        if 'service_name' in m:
                            exp.service_name = m['service_name']
                        else:
                            exp.service_name = 'unknown'

                        if 'time' in m:
                            exp.end_time = m['time']
                        else:
                            exp.end_time = 'unknown'

                        self.experiments[key] = exp
                    if 'metric' in m:
                        exp.winner_data[m['metric']] = float(v[1])
                    else:
                        exp.winner_data[m['metric']] = float(-1)

        for exp in self.experiments:
            print(self.experiments[exp])

    # At the start, we read all the Experiment Custom Resources in
    # the cluster and query Prometheus for their summary metric data
    def load_exp_from_cluster(self):
        logger.info("Loading data from Kubernetes cluster...")
        try:
            response = self.kubeapi.list_cluster_custom_object(
                group='iter8.tools',
                version='v1alpha2',
                plural='experiments')
            results = json.loads(json.dumps(response, ensure_ascii=False))
            for e in results['items']:
                exp = Experiment(e)
                if exp.namespace + ':' + exp.name in self.experiments:
                    continue
                if exp.is_completed_and_successful:
                    self.experiments[exp.namespace + ':' + exp.name] = exp
                    exp.winner_data['cpu'] = self.query_prometheus_cpu(exp.winner, exp)
                    exp.winner_data['mem'] = self.query_prometheus_mem(exp.winner, exp)
                    exp.winner_data['diskreadbytes'] = self.query_prometheus_disk_read_bytes(exp.winner, exp)
                    exp.winner_data['diskwritebytes'] = self.query_prometheus_disk_write_bytes(exp.winner, exp)
                    exp.winner_data['networkreadbytes'] = self.query_prometheus_network_read_bytes(exp.winner, exp)
                    exp.winner_data['networkwritebytes'] = self.query_prometheus_network_write_bytes(exp.winner, exp)
                    logger.info(exp)
        except client.rest.ApiException as e:
            logger.error(f"Exception when calling CustomObjectApi->list_cluster_custom_object: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)

    def query_prometheus(self, query):
        params = {'query': query}
        try:
            response = requests.get(self.prometheus_url, params=params).json()
            if 'data' in response and 'result' in response['data']:
                return response['data']['result']
            logger.warning(f"Prometheus query returned no result ({params}, {response})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Problem querying Prometheus ({self.prometheus_url}): {e}")
        return None


    # Calls Prometheus to retrieve resource utilization data
    def query_prometheus_resource(self, query_template, podname, exp):
        params = {'query': exp.get_resource_query_str(query_template, podname)}
        try:
            response = requests.get(self.prometheus_url, params=params).json()
            if 'data' in response and 'result' in response['data']:
                res = response['data']['result']
                if len(res) == 1:
                    v = res[0]['value']
                    return v[1]
            else:
                logger.warning(f"Prometheus query returned no result ({params}, {response})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Problem querying Prometheus ({self.prometheus_url}): {e}")
        return -1

    def query_prometheus_cpu(self, podname, exp):
        query_template = 'sum(rate(container_cpu_usage_seconds_total{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def query_prometheus_mem(self, podname, exp):
        query_template = 'sum(avg_over_time(container_memory_working_set_bytes{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def query_prometheus_disk_read_bytes(self, podname, exp):
        query_template = 'sum(rate(container_fs_reads_bytes_total{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def query_prometheus_disk_write_bytes(self, podname, exp):
        query_template = 'sum(rate(container_fs_writes_bytes_total{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def query_prometheus_network_read_bytes(self, podname, exp):
        query_template = 'sum(rate(container_network_receive_bytes_total{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def query_prometheus_network_write_bytes(self, podname, exp):
        query_template = 'sum(rate(container_network_transmit_bytes_total{pod=~"$podname.*", container!~"istio-proxy", namespace="$namespace", image=~".+"}[$interval]$offset_str))'
        return self.query_prometheus_resource(query_template, podname, exp)

    def start_healthcheck(self):
        class HttpHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/api/v1/health/health_check':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(bytes(json.dumps({'status': 'OK'}), 'utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()
        httpd = HTTPServer(('', self.healthcheck_port), HttpHandler)
        httpd.serve_forever()

    # Start a Prometheus scrape target endpoint
    def start_scrape_target(self):
        start_http_server(self.scrape_port)
        REGISTRY.register(self)
        logger.info("Starting Prometheus scrape target...")
        while True:
            time.sleep(1)

    def collect(self):
        g = GaugeMetricFamily('iter8_trend', '', labels=['namespace',
                                                         'name',
                                                         'service_name',
                                                         'baseline',
                                                         'winner',
                                                         'phase',
                                                         'start_time',
                                                         'time',
                                                         'app',
                                                         'version',
                                                         'metric'])
        for exp in self.experiments:
            for metric in self.experiments[exp].winner_data:
                g.add_metric([self.experiments[exp].namespace,
                              self.experiments[exp].name,
                              self.experiments[exp].service_name,
                              self.experiments[exp].baseline,
                              self.experiments[exp].winner,
                              self.experiments[exp].phase,
                              self.experiments[exp].start_time,
                              self.experiments[exp].end_time,
                              self.experiments[exp].winner_app,
                              self.experiments[exp].winner_version,
                              metric],
                             float(self.experiments[exp].winner_data[metric]))
        yield g

    # Monitors for new Experiments in the cluster and retrieves their
    # summary metrics data from Prometheus
    def watch_exp_from_cluster(self):
        logger.info("Starting to watch Kubernetes cluster...")
        while True:
            try:
                response = self.kubeapi.list_cluster_custom_object(
                    group='iter8.tools',
                    version='v1alpha2',
                    plural='experiments')
                results = json.loads(json.dumps(response, ensure_ascii=False))
                for e in results['items']:
                    exp = Experiment(e)
                    if exp.namespace + ':' + exp.name in self.experiments:
                        continue
                    if exp.is_completed_and_successful:
                        self.experiments[exp.namespace + ':' + exp.name] = exp
                        exp.winner_data['cpu'] = self.query_prometheus_cpu(exp.winner, exp)
                        exp.winner_data['mem'] = self.query_prometheus_mem(exp.winner, exp)
                        exp.winner_data['diskreadbytes'] = self.query_prometheus_disk_read_bytes(exp.winner, exp)
                        exp.winner_data['diskwritebytes'] = self.query_prometheus_disk_write_bytes(exp.winner, exp)
                        exp.winner_data['networkreadbytes'] = self.query_prometheus_network_read_bytes(exp.winner, exp)
                        exp.winner_data['networkwritebytes'] = self.query_prometheus_network_write_bytes(exp.winner, exp)
                        logger.info(exp)

            except client.rest.ApiException as e:
                logger.error(f"Exception when calling CustomObjectApi->list_cluster_custom_object: {e}")
            except Exception as e:
                # In case we are having problem connecting to K8s, we just quit
                logger.error(f"Unexpected error: {e}")
                os.kill(os.getpid(), SIGINT)

            time.sleep(self.k8s_freq)

    def run(self):
        # Handles ctrl-c signal
        signal(SIGINT, sighandler)

        self.load_data_from_prometheus()
        self.load_exp_from_cluster()

        threads = list()
        t0 = threading.Thread(target=self.start_healthcheck, daemon=True, args=())
        t0.start()
        threads.append(t0)

        # Start Prometheus scrape target endpoint
        t1 = threading.Thread(target=self.start_scrape_target, daemon=True, args=())
        t1.start()
        threads.append(t1)

        # Start monitoring Iter8 Experiment Custom Resources
        t2 = threading.Thread(target=self.watch_exp_from_cluster, daemon=True, args=())
        t2.start()
        threads.append(t2)

        for t in threads:
            t.join()

def sighandler(signal_received, frame):
    logger.warning('signal %d received: %s' % (signal_received, frame))
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape-port", default=8888, type=int, help="Target port number for Prometheus scraping")
    parser.add_argument("--healthcheck-port", default=8889, type=int, help="Health checking port for K8s")
    parser.add_argument("--prometheus-url", default="http://prometheus.istio-system:9090", help="Prometheus URL to get summary metrics data")
    parser.add_argument("--k8s-freq", default=30, type=int, help="Frequency to monitor K8s cluster for Iter8 Experiment Custom Resources")
    args = parser.parse_args()
    logger.info(args)
    return args

if __name__ == '__main__':
    args = parse_args()
    watcher = Iter8Watcher(args)
    watcher.run()
