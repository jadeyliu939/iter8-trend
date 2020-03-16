#!/usr/local/Cellar/python/3.7.6_1/bin/python3.7
##!/usr/bin/python

from __future__ import print_function
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from dateutil.parser import parse
from datetime import datetime, timezone, timedelta
from string import Template
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY
import requests
import json
import time
import threading
import logging

logging.basicConfig(level=logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
		filemode='a')
logger = logging.getLogger(__name__)

# Represents an Iter8 Experiment Custom Resource
class Experiment:
	def __init__(self, e):
		if 'metadata' in e and 'namespace' in e['metadata']:
			self.namespace = e['metadata']['namespace']
		if 'metadata' in e and 'name' in e['metadata']:
			self.name = e['metadata']['name']
		if 'metadata' in e and 'resourceVersion' in e['metadata']:
			self.resourceVersion = e['metadata']['resourceVersion']
		if 'status' in e and 'phase' in e['status']:
			self.phase = e['status']['phase']

		if 'spec' in e and 'targetService' in e['spec']:
			if 'baseline' in e['spec']['targetService']:
				self.baseline = e['spec']['targetService']['baseline']
			if 'candidate' in e['spec']['targetService']:
				self.candidate = e['spec']['targetService']['candidate']
			if 'name' in e['spec']['targetService']:
				self.serviceName = e['spec']['targetService']['name']

		if 'status' in e:
			if 'conditions' in e['status']:
				for c in e['status']['conditions']:
					if 'type' in c:
						if c['type'] == 'RoutingRulesReady':
							self.startTime = c['lastTransitionTime']
						if c['type'] == 'ExperimentSucceeded':
							self.endTime = c['lastTransitionTime']

			self.completedAndSuccessful = False
			if 'assessment' in e['status'] and 'conclusions' in e['status']['assessment']:
				if len(e['status']['assessment']['conclusions']) == 1 and \
					e['status']['assessment']['conclusions'][0] == 'All success criteria were  met' and \
					self.phase == 'Completed':
					# Only a Completed and Successful experiment is promoted
					self.completedAndSuccessful = True

		if 'metrics' in e:
			for m in e['metrics']:
				# TODO: for now, we assume there is only one metric defined (does for loop return items in order?)
				self.queryTemplate = e['metrics'][m]['query_template']
				break

		# These are pre-defined to deal with the situation that metric data is
		# no longer retained in Prometheus
		self.candidateData = 0
		self.baselineData = 0

	# Prints an Experiment Custom Resource
	def __str__(self):
		s = "%s.%s(service:%s, baseline:%s, candidate:%s): %s (%s - %s) [%f]" % ( \
			self.namespace, \
			self.name, \
			self.serviceName, \
			self.baseline, \
			self.candidate, \
			self.phase, \
			self.startTime, \
			self.endTime, \
			float(self.candidateData))
		return s

	# Convert a query template from an Experiment Custom Resource
	# to a Prometheus query used to query for a summary metric
	def getQueryStr(self):
		start = parse(self.startTime)
		end = parse(self.endTime)
		now = datetime.now(timezone.utc)
		interval = end-start
		intervalStr = str(int(interval.total_seconds())) + 's'
		offset = now-end
		offsetStr = str(int(offset.total_seconds())) + 's'
		entityLabels = 'destination_service_namespace, destination_workload'

		kwargs = {
            "interval": intervalStr,
            "offset_str": f" offset {offsetStr}" if offsetStr else "",
            "entity_labels": entityLabels,
        }
		qt = Template(self.queryTemplate)
		query = qt.substitute(**kwargs)
		return query

	def namespace(self):
		return self.namespace

	def name(self):
		return self.name

	def phase(self):
		return self.phase

	def completedAndSuccessful(self):
		return self.completedAndSuccessful

	def resourceVersion(self):
		return self.resourceVersion

	def baseline(self):
		return self.baseline

	def setBaselineData(self, data):
		self.baselineData = data

	def getBaselineData(self):
		return self.baselineData

	def candidate(self):
		return self.candidate

	def setCandidateData(self, data):
		self.candidateData = data

	def getCandidateData(self):
		return self.candidateData

	def serviceName(self):
		return self.serviceName

	def startTime(self):
		return self.startTime

	def endTime(self):
		return self.endTime

	def queryTemplate(self):
		return queryTemplate

# This is the main engine that watches a K8s cluster for Iter8 Experiment 
# Custom Resources and query Prometheus for summary performance metrics
# It also provides a Prometheus scrape target endpoint
class Iter8Watcher:
	def __init__(self, prometheusURL):
		self.prometheusURL = prometheusURL + '/api/v1/query'

		# Initialize kubernetes.client.configuration from kubeconfig
		config.load_kube_config()
		self.kubeapi = client.CustomObjectsApi()

		# All experiments in the cluster
		self.experiments = dict()

	# At the start, we read all the Experiment Custom Resources in 
	# the cluster and query Prometheus for their summary metric data
	def loadExpFromCluster(self):
		try:
			response = self.kubeapi.list_cluster_custom_object(
				group = 'iter8.tools',
				version = 'v1alpha1',
				plural = 'experiments')
			results = json.loads(json.dumps(response, ensure_ascii=False))
			for e in results['items']:
				exp = Experiment(e)
				if exp.completedAndSuccessful:
					self.experiments[exp.namespace + ':' + exp.name] = exp
					self.queryPrometheus(exp)
					logger.info(exp)
	
		except ApiException as e:
			logger.error("Exception when calling CustomObjectApi->list_cluster_custom_object: %s\n" % e)

	# Calls Prometheus to retrieve summary metric data for an Experiment
	def queryPrometheus(self, exp):
		params = {'query': exp.getQueryStr()}
		response = requests.get(self.prometheusURL, params=params).json()
		if 'data' in response and 'result' in response['data']:
			for res in response['data']['result']:
				if 'metric' in res and 'value' in res:
					m = res['metric']
					v = res['value']
					if m['destination_workload'] == exp.baseline:
						exp.setBaselineData(v[1])
					if m['destination_workload'] == exp.candidate:
						exp.setCandidateData(v[1])

	# Start a Prometheus scrape target endpoint
	def startServer(self):
		start_http_server(8888)
		REGISTRY.register(self)
		logger.info("Prometheus scrape target started")
		while True:
			time.sleep(1)

	def collect(self):
		g = GaugeMetricFamily('iter8_trend', '', labels=['namespace', 'name', 'service_name', 'time'])
		for exp in self.experiments:
			g.add_metric([self.experiments[exp].namespace, 
						self.experiments[exp].name,
						self.experiments[exp].serviceName,
						self.experiments[exp].endTime],
						float(self.experiments[exp].candidateData))
						#parse(self.experiments[exp].endTime).timestamp())
		yield g

	# Monitors for new Experiments in the cluster and retrieves their
	# summary metrics data from Prometheus
	def watchExpFromCluster(self):
		logger.info("Starting to watch Kubernetes cluster...")
		while True:
			try:
				response = self.kubeapi.list_cluster_custom_object(
					group = 'iter8.tools',
					version = 'v1alpha1',
					plural = 'experiments')
				results = json.loads(json.dumps(response, ensure_ascii=False))
				for e in results['items']:
					exp = Experiment(e)
					if exp.namespace + ':' + exp.name in self.experiments:
						continue
					if exp.completedAndSuccessful:
						self.experiments[exp.namespace + ':' + exp.name] = exp
						self.queryPrometheus(exp)
						logger.info(exp)
		
			except ApiException as e:
				logger.error("Exception when calling CustomObjectApi->list_cluster_custom_object: %s\n" % e)

			time.sleep(30)

	def run(self):
		threads = list()
		self.loadExpFromCluster()

		# Start Prometheus scrape target endpoint
		t1 = threading.Thread(target=self.startServer, args=())
		t1.start()
		threads.append(t1)

		# Start monitoring Iter8 Experiment Custom Resources
		t2 = threading.Thread(target=self.watchExpFromCluster, args=())
		t2.start()
		threads.append(t2)

		for t in threads:
			t.join()

# TODO: Parameterize hostname, port number, monitoring period, etc.
if __name__ == '__main__':
	watcher = Iter8Watcher('http://localhost:9090')
	watcher.run()
