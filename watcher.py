#!/usr/local/Cellar/python/3.7.6_1/bin/python3.7
##!/usr/bin/python

from __future__ import print_function
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from dateutil.parser import parse
from datetime import datetime, timezone, timedelta
from string import Template
import requests
import json

class Experiment:
	def __init__(self, e):
		if 'metadata' in e and 'namespace' in e['metadata']:
			self.namespace = e['metadata']['namespace']
		if 'metadata' in e and 'name' in e['metadata']:
			self.name = e['metadata']['name']
		if 'status' in e and 'phase' in e['status']:
			self.phase = e['status']['phase']

		if 'spec' in e and 'targetService' in e['spec']:
			if 'baseline' in e['spec']['targetService']:
				self.baseline = e['spec']['targetService']['baseline']
			if 'candidate' in e['spec']['targetService']:
				self.candidate = e['spec']['targetService']['candidate']

		if 'status' in e and 'conditions' in e['status']:
			for c in e['status']['conditions']:
				if 'type' in c:
					if c['type'] == 'RoutingRulesReady':
						self.startTime = c['lastTransitionTime']
					if c['type'] == 'ExperimentSucceeded':
						self.endTime = c['lastTransitionTime']

		if 'metrics' in e:
			for m in e['metrics']:
				# TODO: for now, we assume there is only one metric defined
				self.queryTemplate = e['metrics'][m]['query_template']
				break

	def __str__(self):
		s = "%s.%s(%s,%s): %s (%s - %s) [ %f ]" % ( \
			self.namespace, \
			self.name, \
			self.baseline, \
			self.candidate, \
			self.phase, \
			self.startTime, \
			self.endTime, \
			float(self.candidateData))
		return s

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

	def startTime(self):
		return self.startTime

	def endTime(self):
		return self.endTime

	def queryTemplate(self):
		return queryTemplate

class Iter8Watcher:
	def __init__(self, prometheusURL):
		self.prometheusURL = prometheusURL + '/api/v1/query'

		# Initialize kubernetes.client.configuration from kubeconfig
		config.load_kube_config()
		self.kubeapi = client.CustomObjectsApi()

		# All experiments in the cluster
		self.experiments = dict()

	def loadDataFromCluster(self):
		try:
			response = self.kubeapi.list_cluster_custom_object(
				group = 'iter8.tools',
				version = 'v1alpha1',
				plural = 'experiments')
			results = json.loads(json.dumps(response, ensure_ascii=False))
			for e in results['items']:
				exp = Experiment(e)
				if exp.phase == 'Completed':
					self.experiments[exp.namespace + ':' + exp.name] = exp
	
		except ApiException as e:
			print("Exception when calling CustomObjectApi->get_cluster_custom_object: %s\n" % e)

	def printDataFromCluster(self):
		for exp in self.experiments:
			print(self.experiments[exp])
	
	def queryPrometheus(self):
		for exp in self.experiments:
			params = {'query': self.experiments[exp].getQueryStr()}
			response = requests.get(self.prometheusURL, params=params).json()
			if 'data' in response and 'result' in response['data']:
				for res in response['data']['result']:
					if 'metric' in res and 'value' in res:
						m = res['metric']
						v = res['value']
						if m['destination_workload'] == self.experiments[exp].baseline:
							self.experiments[exp].setBaselineData(v[1])
						if m['destination_workload'] == self.experiments[exp].candidate:
							self.experiments[exp].setCandidateData(v[1])

	def run(self):
		self.loadDataFromCluster()
		self.queryPrometheus()
		self.printDataFromCluster()
		pass

if __name__ == '__main__':
	watcher = Iter8Watcher('http://localhost:9090')
	watcher.run()
