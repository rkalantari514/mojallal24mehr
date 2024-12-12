function drawChart(canvasId, chartType, data, options) {
    var ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: chartType,
        data: data,
        options: options
    });
}
