#!/usr/bin/python

from __future__ import print_function
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import json

class Experiments:

	def __init__(self):
		self.experiments = dict()

	def add(self, e):
		self.experiments[e.namespace + ':' + e.name] = e

	def delete(self, namespace, name):
		if namespace + ':' + name in self.experiments:
			del self.experiments[namespace + ':' + name]

class Experiment:
	def __init__(self, namespace, name, phase):
		self.namespace = namespace
		self.name = name
		self.phase = phase

	def __str__(self):
		return self.namespace + "." + self.name + ": " + self.phase

	def namespace(self):
		return self.namespace

	def name(self):
		return self.name

	def phase(self):
		return self.phase

class Iter8Watcher:
	def __init__(self):

		# Initialize kubernetes.client.configuration from kubeconfig
		config.load_kube_config()
		self.kubeapi = client.CustomObjectsApi()

	def loadDataFromCluster(self):

		# All experiments in the cluster
		experiments = dict()

		try:
			response = self.kubeapi.list_cluster_custom_object(
				group = 'iter8.tools',
				version = 'v1alpha1',
				plural = 'experiments')
			results = json.loads(json.dumps(response, ensure_ascii=False))
			for experiment in results['items']:
				e = Experiment(experiment['metadata']['namespace'], experiment['metadata']['name'], experiment['status']['phase'])
				experiments[e.namespace+'.'+e.name] = e
				print(e)
	
		except ApiException as e:
			print("Exception when calling CustomObjectApi->get_cluster_custom_object: %s\n" % e)
		

	def run(self):
		self.loadDataFromCluster()
		pass

if __name__ == '__main__':
	watcher = Iter8Watcher()
	watcher.run()
