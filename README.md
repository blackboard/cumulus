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

### Updating cumulus.html
