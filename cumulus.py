#!/usr/bin/python

"""
cloudviz.py
This script exposes Amazon EC2 CloudWatch as a data source for the Google Visualization API

Requirements:
- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, read in from settings.py
- boto, a Python interface for Amazon Web Services (http://code.google.com/p/boto/)
- gviz_api, a Python library for creating Google Visualization API data sources 
  (http://code.google.com/p/google-visualization-python/)
- pytz, world timezone definitions for Python (http://pytz.sourceforge.net/)

Cloudviz project maintained here: http://github.com/mbabineau/cloudviz
--------
Copyright 2010 Bizo, Inc. (Mike Babineau <michael.babineau@gmail.com>)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import operator
from datetime import datetime, timedelta
from django.utils import simplejson
from pytz import timezone
import pytz

# Google Visualization API
import gviz_api

import boto.ec2.cloudwatch
from boto.ec2.cloudwatch.metric import Metric

import cherrypy

from boto.ec2 import autoscale

from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['templates'])

from settings import DEFAULTS, CW_MAX_DATA_POINTS, CW_MIN_PERIOD

# def merge_data(data):
#     merged = []
#
#     current_date = None
#     for row in data:
#         if current_date != row[0]:
#
#
#     return merged;

def get_cloudwatch_data(cloudviz_query, request_id, aws_access_key_id=None, aws_secret_access_key=None):
    """
    Query CloudWatch and return the results in a Google Visualizations API-friendly format

    Arguments:
    `cloudviz_query` -- (dict) parameters and values to be passed to CloudWatch (see README for more information)
    `request_id` -- (int) Google Visualizations request ID passed as part of the "tqx" parameter
    """
    # Initialize data description, columns to be returned, and result set
    description = { "Timestamp": ("datetime", "Timestamp")}
    columns = ["Timestamp"]
    rs = []
    current_timezone = timezone('UTC')
    utc = pytz.utc

    # Build option list
    opts = ['unit','metric','namespace','statistics','period', 'dimensions', 'prefix', 
            'start_time', 'end_time', 'calc_rate', 'region', 'range', 'timezone']
    
    # Set default parameter values from config.py
    qa = DEFAULTS.copy()
    
    # Set passed args
    for opt in opts:
        if opt in cloudviz_query: qa[opt] = cloudviz_query[opt]
    
    # Convert timestamps to datetimes if necessary
    for time in ['start_time','end_time']:
        if time in qa:
            if type(qa[time]) == str or type(qa[time]) == unicode: 
                qa[time] = datetime.strptime(qa[time].split(".")[0], '%Y-%m-%dT%H:%M:%S')

    # If both start_time and end_time are specified, do nothing.  
    if 'start_time' in qa and 'end_time' in qa:
        pass
    # If only one of the times is specified, fill in the other based on range
    elif 'start_time' in qa and 'range' in qa:
        qa['end_time'] = qa['start_time'] + timedelta(hours=qa['range'])
    elif 'range' in qa and 'end_time' in qa:
        qa['start_time'] = qa['end_time'] - timedelta(hours=qa['range'])
    # If neither is specified, use range leading up to current time
    else:
        qa['end_time'] = datetime.now()
        qa['start_time'] = qa['end_time'] - timedelta(hours=qa['range'])
    
    if 'timezone' in qa:
        current_timezone = timezone(qa['timezone'])

    data_map = {}

    # Parse, build, and run each CloudWatch query
    cloudwatch_opts = ['unit', 'metric', 'namespace', 'statistics', 'period', 'dimensions', 'prefix', 'calc_rate', 'region']
    for cloudwatch_query in cloudviz_query['cloudwatch_queries']:
        args = qa.copy()
        # Override top-level vars
        for opt in cloudwatch_opts:
            if opt in cloudwatch_query: args[opt] = cloudwatch_query[opt]
        
        # Calculate time range for period determination/sanity-check
        delta = args['end_time'] - args['start_time']
        delta_seconds = ( delta.days * 24 * 60 * 60 ) + delta.seconds + 1 #round microseconds up

        # Determine min period as the smallest multiple of 60 that won't result in too many data points
        min_period = 60 * int(delta_seconds / CW_MAX_DATA_POINTS / 60)
        if ((delta_seconds / CW_MAX_DATA_POINTS) % 60) > 0:
            min_period += 60
        
        if 'period' in qa:
            if args['period'] < min_period:
                args['period'] = min_period
        else:
            args['period'] = min_period
        
        # Make sure period isn't smaller than CloudWatch allows
        if args['period'] < CW_MIN_PERIOD: 
            args['period'] = CW_MIN_PERIOD
        
        # Defaulting AWS region to us-east-1
        if not 'region' in args: 
            args['region'] = 'us-east-1'
        
        # Use AWS keys if provided, otherwise just let the boto look it up
        if aws_access_key_id and aws_secret_access_key:
            c = boto.ec2.cloudwatch.connect_to_region(  args['region'], aws_access_key_id=aws_access_key_id,
                                                        aws_secret_access_key=aws_secret_access_key, is_secure=False)
        else:
            c = boto.ec2.cloudwatch.connect_to_region(args['region'], is_secure=False)
        
        # Pull data from EC2
        results = c.get_metric_statistics(  args['period'], args['start_time'], args['end_time'], 
                                            args['metric'], args['namespace'], args['statistics'],
                                            args['dimensions'], args['unit'])
        # Format/transform results
        for d in results:
            # Convert timestamps to datetime objects
            d.update({u'Timestamp': d[u'Timestamp']})
            utc_dt = utc.localize(d[u'Timestamp'])
            loc_dt = utc_dt.astimezone(current_timezone)
            d['Timestamp'] = loc_dt

            try:
                data_obj = data_map[loc_dt]
            except KeyError:
                data_obj = d
                data_map[loc_dt] = d

            # If desired, convert Sum to a per-second Rate
            if args['calc_rate'] == True and 'Sum' in args['statistics']: d.update({u'Rate': d[u'Sum']/args['period']})
            # Change key names
            keys = d.keys()
            keys.remove('Timestamp')
            for k in keys:
                new_k = args['prefix']+k
                data_obj[new_k] = d[k]
                del d[k]
    
        # rs.extend(results)
        
        # Build data description and columns to be return
        description[args['prefix']+'Samples'] = ('number', args['prefix']+'Samples')
        description[args['prefix']+'Unit'] = ('string', args['unit']) 
        for stat in args['statistics']:
            # If Rate is desired, update label accordingly
            if stat == 'Sum' and args['calc_rate'] == True:
                stat = 'Rate'
            description[args['prefix']+stat] = ('number', args['prefix']+stat)
            columns.append(args['prefix']+stat)       
    
    # Sort data and present    
    data = sorted(data_map.values(), key=operator.itemgetter(u'Timestamp'))

    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)

    results = data_table.ToJSonResponse(columns_order=columns, order_by="Timestamp", req_id=request_id)
    return results


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


class Script(object):
    def index(self):
        asc = autoscale.connect_to_region("us-east-1")
        groups = asc.get_all_groups()

        template = lookup.get_template('cumulus.js')
        return template.render(groups=groups)

    index.exposed = True

class Data(object):
    def index(self, qs, tqx):
        cloudviz_query = simplejson.loads(qs)

        tqx_hash = {}
        for s in tqx.split(';'):
            key = s.split(':')[0]
            value = s.split(':')[1]
            tqx_hash.update({key:value})

        request_id = tqx_hash["reqId"]
        results = get_cloudwatch_data(cloudviz_query, request_id)
        cherrypy.response.headers['Content-Type'] = "text/plain"
        return results

    index.exposed = True

class Root(object):
    data = Data()
    js = Script()

    def index(self):
        group = 'mooc-fleet98-LearnAutoScalingGroup-QS7FYOU14AVK'
        asc = autoscale.connect_to_region("us-east-1")
        instances = asc.get_all_groups([group])[0].instances

        template = lookup.get_template('cumulus.html')
        return template.render(instances=instances, group=group)

    index.exposed = True


cherrypy.quickstart(Root())