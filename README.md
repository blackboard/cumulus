Cumulus
-----

Cumulus is a CloudWatch dashboard project to simplify monitoring of ASGs in AWS.  Through CloudWatch itself, aggregating information is rather difficult.  

1. You can only have one graph at a time.  
2. Finding the servers in an ever-changing ASG is not easy. 
3. It takes a lot of clicks to get there. 

Cumulus aims to simplify that through the CloudWatch APIs.  

Installation
-------

1. Install Python
2. Install dependencies
** pip install boto
** pip install pytz
** pip install -U -f https://code.google.com/p/google-visualization-python/ gviz-api-py
3. Clone this repo
4. python cumulus.py

Cumulus will run on port 8080 (configurable).

Customization
-----
To customize the charts, you only need to edit the main HTML page.  There are two ways to do this: modify _templates/cumulus.html_ or create an "offline" HTML page.

#### Updating cumulus.html
Cumulus uses a combination of DIV container attributes and a registration method to register a chart.  A container should include the following attributes to support a chart:

	<div id="processingTime" style="width: 600px; height: 300px;"
		cumulus:namespace="Learn/Instance" 
		cumulus:metric="AverageRequestProcessingTime" 
		cumulus:statistics="Average" 
		cumulus:unit="Milliseconds">
	</div>

* cumulus:namespace - The namespace of the metric.
* cumulus:metric - The name of the metric.
* cumulus:statistics - Comma-separated list of the statistics to run on the metrics.
* cumulus:unit - The unit of the metrics.

Next, you need to register the containers:

        function registerCharts() {
            registerInstanceChart( "processingTime", "mooc-fleet98-LearnAutoScalingGroup-QS7FYOU14AVK", 
				   {displayZoomButtons: false, 'min': 0, 'allValuesSuffix': 'ms'} );
        }

        google.setOnLoadCallback(registerCharts);

_registerInstanceChart()_ takes three parameters:

1. elementId - The ID of the element in the document that is the container for the chart. 
2. group - The name of the Auto Scaling Group. 
3.  options - Dictionary of options to apply to the Google chart (see Google docs about these). 

Optionally, you can create a local HTML file, based on the current cumulus.html and change it there.  The file does *not* need to be hosted on the server serving the Cumulus data.

