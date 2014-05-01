import cherrypy

import sys
import re
import json
import urllib2
import datetime

from boto.ec2 import autoscale
from boto.ec2 import cloudwatch
from boto.utils import get_instance_metadata

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['../html'])

aws_access_key_id='AKIAJ43KYETRXUDPLSJA'
aws_secret_access_key='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'

def binary_search(data,date,low=0,hi=len(a)):
    index = int((hi - low) / 2);
    if ()
    if i == 0:
        return -1
    elif a[i-1] == x:
        return i-1
    else:
        return -1

def get_instance_metrics(metric_name, instance, region, namespace='Learn/Instance', statistics=['Average'], period=60):
    cherrypy.log(instance.instance_id)
    stats = cw.get_metric_statistics(
        period,
        datetime.datetime.utcnow() - datetime.timedelta(hours=3),
        datetime.datetime.utcnow(),
        metric_name,
        namespace,
        statistics,
        dimensions = {'InstanceId':[instance]}
    )

    cherrypy.log(','.join(stats))
    if (len(stats) > 0):
        return stats

    return []

def get_asg_metrics(asg, metric_name, region, namespace='Learn/Instance', statistic='Average', period=60):
    asc = autoscale.connect_to_region(region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    instances = asc.get_all_groups([asg])[0].instances

    data = []
    cw = cloudwatch.connect_to_region(region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    end = datetime.datetime.now()
    start = end - datetime.timedelta(hours=3)
    instance_index = 0;
    for instance in instances:
        metrics = cw.list_metrics(metric_name=metric_name, dimensions={'InstanceId': [str(instance.instance_id)]})
        points = metrics[0].query(start, end, statistic)

        for point in points:
            time_diff = point['Timestamp'] - start
            date_index = time_diff.total_seconds()
            data[int(date_index)][instance_index] = point[statistic]

        instance_index += 1

    return data


class CloudWatch(object):
    @cherrypy.expose
    def index(self):
        template = lookup.get_template('index.html')
        data = get_asg_metrics('mooc-fleet98-LearnAutoScalingGroup-QS7FYOU14AVK', 'RequestThreadUtilization', 'us-east-1')
        return template.render(data=data)

cherrypy.quickstart(CloudWatch())
