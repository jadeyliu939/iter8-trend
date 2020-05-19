#!/bin/sh

# This is called after an Iter8 experiment is finished. We give an additional
# 60 seconds before testing if Iter8-trend is emitting data via its Prometheus
# scrape target
sleep 60
 
echo ""
echo "===================================="
echo "Verify results"
echo "===================================="

IP=`kubectl -n iter8 get services | grep iter8-trend | awk '{print $3}'`
PORT=`kubectl -n iter8 get services | grep iter8-trend | awk '{print $5}' | awk -F/ '{print $1}'`
DATA=`curl -s $IP:$PORT | grep "name=\"reviews-v3-rollout\""`
echo "Data from Prometheus scrape target: $DATA"
LINES=`echo "$DATA" | wc -l`
if [ "$LINES" -le 0 ]
then
	echo "Iter8-trend did not summarize metric data for successful experiment as expected!"
	exit 1
else
	echo "Iter8-trend correctly summarized metric data for successful experiment!"
	echo "$DATA"
fi
