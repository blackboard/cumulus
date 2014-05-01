"""
settings.py
Contains AWS credentials and default values for expected parameters

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

from datetime import datetime, timedelta
from operator import itemgetter

# Uncomment and set to your Amazon credentials:
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

# Default values to use if a given parameter is not passed
DEFAULTS = {'calc_rate': True,
            # 'period': 60,
            # 'start_time': datetime.now() - timedelta(days=1),
            # 'end_time': datetime.now(),
            'range': 6,
            }

## CloudWatch variables
# The maximum number of datapoints CloudWatch will return for a given query
CW_MAX_DATA_POINTS = 1440
# The minimum allowable period
CW_MIN_PERIOD = 60
