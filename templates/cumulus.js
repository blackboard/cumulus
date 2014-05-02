
var autoScalingGroups = eval({
% for group in groups:
    "${group.name}": [
    % for instance in group.instances:
        "${instance.instance_id}",
    %endfor
    ],
% endfor
});

function drawInstanceChart(namespace, metric, statistics, unit, group, handler) {
    var queries = [];
    var instances = autoScalingGroups[group];

    for (var i = 0; i < instances.length; i++) {
        var query =  {
            "prefix": instances[i]+" ",
            "dimensions": {"InstanceId": instances[i] }
        };
        queries.push(query);
    }

    var qa = {
                "namespace": namespace,       // CloudWatch namespace (string
                "metric": metric,   // CloudWatch metric (string)
                "unit": unit,            // CloudWatch unit (string)
                "statistics": statistics,      // CloudWatch statistics (list of strings)
                "period": 60,                // CloudWatch period (int)
                "cloudwatch_queries": queries        // (list of dictionaries)
             };

    var qs = JSON.stringify(qa);
    var url = '${request_base}/data?qs=' + qs;
    var query = new google.visualization.Query(url);
    query.send(handler);
}

function drawGroupChart(namespace, metric, statistics, unit, group, handler) {
    var qa = {
                "namespace": namespace,       // CloudWatch namespace (string
                "metric": metric,   // CloudWatch metric (string)
                "unit": unit,            // CloudWatch unit (string)
                "statistics": statistics,      // CloudWatch statistics (list of strings)
                "period": 60,                // CloudWatch period (int)
                "cloudwatch_queries":         // (list of dictionaries)
                [
                    {
                        "prefix": group+" ",   // label prefix for associated data sets (string)
                        "dimensions": { "AutoScalingGroupName": group } // CloudWatch dimensions (dictionary)
                    }
                ]
             };

    var qs = JSON.stringify(qa);
    var url = '${request_base}/data?qs=' + qs;
    var query = new google.visualization.Query(url);
    query.send(handler);
}

function registerInstanceChart(elementId, group, options) {
   var container = document.getElementById(elementId);

   var handler = function(response) {
        if (response.isError()) {
            return;
        }

        var data = response.getDataTable();
        var visualization = new google.visualization.AnnotationChart(container);
        visualization.draw(data, options);
    }

    drawInstanceChart(container.getAttribute("cumulus:namespace"),
                      container.getAttribute("cumulus:metric"),
                      container.getAttribute("cumulus:statistics").split(","),
                      container.getAttribute("cumulus:unit"),
                      group,
                      handler);
}
