/*

Template:  Webmin - Bootstrap 4 & Angular 5 Admin Dashboard Template
Author: potenzaglobalsolutions.com
Design and Developed by: potenzaglobalsolutions.com

NOTE: 

*/

 (function($){
  "use strict";
// Line Stacked

   //Check if function exists
    $.fn.exists = function () {
        return this.length > 0;
    };

/*************************
  Line Chart
*************************/ 
    var MONTHS = ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای", "اگوست", "سپتامبر", "اوکتبر", "نوامبر", "دسامبر"];
     var config = {
        type: 'line',
        data: {
          labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
          datasets: [{
            label: "فیسبوک",
            borderColor: window.chartColors.red,
            backgroundColor: window.chartColors.red,
            data: [
                     randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor()
                  ],
      }, {
        label: "توییتر",
        borderColor: window.chartColors.blue,
        backgroundColor: window.chartColors.blue,
        data: [
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor()
                  ],
      }, {
        label: "لینکداین",
        borderColor: window.chartColors.green,
        backgroundColor: window.chartColors.green,
        data: [
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor()
                  ],
      }, {
        label: "گوگل+",
        borderColor: window.chartColors.yellow,
        backgroundColor: window.chartColors.yellow,
        data: [
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor(),
                      randomScalingFactor()
                  ],
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      title:{
        display:false,
        text:"نمودار خط - منطقه انباشته شده"
      },
      tooltips: {
        mode: 'index',
      },
      hover: {
        mode: 'index'
      },
      scales: {
        xAxes: [{
          scaleLabel: {
            display: true,
            labelString: 'ماه'
          }
        }],
        yAxes: [{
          stacked: true,
          scaleLabel: {
            display: true,
            labelString: 'قیمت'
          }
        }]
      }
    }
  };

/*************************
     Line Styles
*************************/ 
var config2 = {
            type: 'line',
            data: {
                labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
                datasets: [{
                    label: "تکمیل نشده",
                    fill: false,
                    backgroundColor: window.chartColors.blue,
                    borderColor: window.chartColors.blue,
                    data: [
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor()
                    ],
                }, {
                    label: "خرد شده",
                    fill: false,
                    backgroundColor: window.chartColors.green,
                    borderColor: window.chartColors.green,
                    borderDash: [5, 5],
                    data: [
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor()
                    ],
                }, {
                    label: "پر شده",
                    backgroundColor: window.chartColors.red,
                    borderColor: window.chartColors.red,
                    data: [
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor(),
                        randomScalingFactor()
                    ],
                    fill: true,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                title:{
                    display:true,
                    text:'خط خط - سبک خط'
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                },
                scales: {
                    xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'ماه'
                        }
                    }],
                    yAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'مقدار'
                        }
                    }]
                }
            }
        };

/*************************
     doughnut
*************************/ 
        var config3 = {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                ],
                backgroundColor: [
                    window.chartColors.red,
                    window.chartColors.orange,
                    window.chartColors.yellow,
                    window.chartColors.green,
                    window.chartColors.blue,
                ],
                label: 'مجموعه داده 1'
            }],
            labels: [
                "قرمز",
                "نارنجی",
                "زرد",
                "سبز",
                "ابی"
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            legend: {
                position: 'bottom',
            },
            title: {
                display: false,
                text: 'نمودار دونات'
            },
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
     };
 

/*************************
        combo
*************************/ 
    var timeFormat = 'MM/DD/YYYY HH:mm';
    function newDateString(days) {
      return moment().add(days, 'd').format(timeFormat);
    }
    var color = Chart.helpers.color;
    var config4 = {
      type: 'bar',
      data: {
        labels: [
          newDateString(0), 
          newDateString(1), 
          newDateString(2), 
          newDateString(3), 
          newDateString(4), 
          newDateString(5), 
          newDateString(6)
        ],
        datasets: [{
          type: 'bar',
          label: 'مجموعه داده 1',
          backgroundColor: color(window.chartColors.red).alpha(0.5).rgbString(),
          borderColor: window.chartColors.red,
          data: [
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor()
          ],
        }, {
          type: 'bar',
          label: 'مجموعه داده 2',
          backgroundColor: color(window.chartColors.blue).alpha(0.5).rgbString(),
          borderColor: window.chartColors.blue,
          data: [
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor()
          ],
        }, {
          type: 'line',
          label: 'مجموعه داده 3',
          backgroundColor: color(window.chartColors.green).alpha(0.5).rgbString(),
          borderColor: window.chartColors.green,
          fill: false,
          data: [
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor(), 
            randomScalingFactor()
          ],
        }, ]
      },
      options: {
        maintainAspectRatio: false,
        responsive:true,
                title: {
                    text:"مقیاس زمان کمبو"
                },
        scales: {
          xAxes: [{
            type: "time",
            display: true,
            time: {
              format: timeFormat
            }
          }],
        },
      }
    };
 
 /*************************
        Custom Points
*************************/ 
 var customTooltips = function (tooltip) {
      $(this._chart.canvas).css("cursor", "pointer");
      var positionY = this._chart.canvas.offsetTop;
      var positionX = this._chart.canvas.offsetLeft;
      $(".chartjs-tooltip").css({
        opacity: 0,
      });
      if (!tooltip || !tooltip.opacity) {
        return;
      }
      if (tooltip.dataPoints.length > 0) {
        tooltip.dataPoints.forEach(function (dataPoint) {
          var content = [dataPoint.xLabel, dataPoint.yLabel].join(": ");
          var $tooltip = $("#tooltip-" + dataPoint.datasetIndex);

          $tooltip.html(content);
          $tooltip.css({
            opacity: 1,
            top: positionY + dataPoint.y + "px",
            left: positionX + dataPoint.x + "px",
          });
        });
      }
    };
    var color = Chart.helpers.color;
    var lineChartData = {
      labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
      datasets: [{
        label: "مجموعه داده اول من",
        backgroundColor: color(window.chartColors.red).alpha(0.2).rgbString(),
        borderColor: window.chartColors.red,
        pointBackgroundColor: window.chartColors.red,
        data: [
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor()
        ]
      }, {
        label: "مجموعه داده دوم من",
        backgroundColor: color(window.chartColors.blue).alpha(0.2).rgbString(),
        borderColor: window.chartColors.blue,
        pointBackgroundColor: window.chartColors.blue,
        data: [
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor(), 
          randomScalingFactor()
        ]
      }]
    };

 /*************************
      Chart Basic
*************************/ 
    var config6 = {
      type: 'line',
      data: {
          labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
          datasets: [{
              label: "مجموعه داده اول من",
              backgroundColor: window.chartColors.red,
              borderColor: window.chartColors.red,
              data: [
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor()
              ],
              fill: false,
          }, {
              label: "مجموعه داده دوم من",
              fill: false,
              backgroundColor: window.chartColors.blue,
              borderColor: window.chartColors.blue,
              data: [
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor(),
                  randomScalingFactor()
              ],
          }]
      },
      options: {
          maintainAspectRatio: false,
          responsive:true,
          title:{
              display:true,
              text:'نمودار خط - پایه'
          },
          tooltips: {
              mode: 'index',
              intersect: false,
          },
          hover: {
              mode: 'nearest',
              intersect: true
          },
          scales: {
              xAxes: [{
                  display: true,
                  scaleLabel: {
                      display: true,
                      labelString: 'ماه'
                  }
              }],
              yAxes: [{
                  display: true,
                  scaleLabel: {
                      display: true,
                      labelString: 'مقدار'
                  }
              }]
          }
      }
  };

 /*************************
     Different Point Sizes
*************************/
 var config7 = {
        type: 'line',
        data: {
            labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
            datasets: [{
                label: "مجموعه داده - نقاط بزرگ",
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ],
                backgroundColor: window.chartColors.red,
                borderColor: window.chartColors.red,
                fill: false,
                borderDash: [5, 5],
                pointRadius: 15,
                pointHoverRadius: 10,
            }, {
                label: "مجموعه داده - اندازه های فردی",
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ],
                backgroundColor: window.chartColors.blue,
                borderColor: window.chartColors.blue,
                fill: false,
                borderDash: [5, 5],
                pointRadius: [2, 4, 6, 18, 0, 12, 20],
            }, {
                label: "مجموعه داده - large pointHoverRadius",
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ],
                backgroundColor: window.chartColors.green,
                borderColor: window.chartColors.green,
                fill: false,
                pointHoverRadius: 30,
            }, {
                label: "مجموعه داده - large pointHitRadius",
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ],
                backgroundColor: window.chartColors.yellow,
                borderColor: window.chartColors.yellow,
                fill: false,
                pointHitRadius: 20,
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive:true,
            legend: {
                position: 'bottom',
            },
            hover: {
                mode: 'index'
            },
            scales: {
                xAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'ماه'
                    }
                }],
                yAxes: [{
                    display: true,
                    scaleLabel: {
                        display: true,
                        labelString: 'Value'
                    }
                }]
            },
            title: {
                display: true,
                text: 'نمودار خط - اندازه های مختلف نقطه'
            }
        }
    };   

/*************************
    Chart Stacked
*************************/
          var barChartData = {
            labels: ["ژانویه", "فوریه", "مارس", "اوریل", "مه", "ژوئن", "ژولای"],
            datasets: [{
                label: 'مجموعه داده 1',
                backgroundColor: window.chartColors.red,
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ]
            }, {
                label: 'مجموعه داده 2',
                backgroundColor: window.chartColors.blue,
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ]
            }, {
                label: 'مجموعه داده 3',
                backgroundColor: window.chartColors.green,
                data: [
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor(),
                    randomScalingFactor()
                ]
            }]
        };       

 /*************************
    window onload
*************************/
        window.onload = function() {
          if ($('#canvas1').exists()) {
           var ctx1 = document.getElementById("canvas1").getContext("2d");
            window.myLine1 = new Chart(ctx1, config);
          }
         if ($('#canvas2').exists()) {
           var ctx2 = document.getElementById("canvas2").getContext("2d");
            window.myLine2 = new Chart(ctx2, config2);
          }
           if ($('#canvas3').exists()) {
            var ctx3 = document.getElementById("canvas3").getContext("2d");
            window.myLine3 = new Chart(ctx3, config3);
          }
           if ($('#canvas4').exists()) {
            var ctx4 = document.getElementById("canvas4").getContext("2d");
            window.myLine4 = new Chart(ctx4, config4);
          }
          if ($('#canvas5').exists()) {
           var chartEl = document.getElementById("canvas5");
              var chart = new Chart(chartEl, {
                type: "line",
                data: lineChartData,
                options: {
                  maintainAspectRatio: false,
                  responsive:true,
                  title:{
                    display: true,
                    text: "راهنمایی های سفارشی با استفاده از امتیازات داده"
                  },
                  tooltips: {
                    enabled: false,
                    mode: 'index',
                    intersect: false,
                    custom: customTooltips
                  }
                }
              });
            };
          }
           if ($('#canvas6').exists()) {   
            var ctx6 = document.getElementById("canvas6").getContext("2d");
            window.myLine6 = new Chart(ctx6, config6);
          }
          if ($('#canvas7').exists()) {
            var ctx7 = document.getElementById("canvas7").getContext("2d");
            window.myLine7 = new Chart(ctx7, config7);
          }
          if ($('#canvas8').exists()) {
            var ctx8 = document.getElementById("canvas8").getContext("2d");
            window.myBar = new Chart(ctx8, {
                type: 'bar',
                data: barChartData,
                options: {
                  maintainAspectRatio: false,
                  responsive:true,
                    title:{
                        display:true,
                        text:"نمودار بار - انباشته شده"
                    },
                    tooltips: {
                        mode: 'index',
                        intersect: false
                    },
                    responsive: true,
                    scales: {
                        xAxes: [{
                            stacked: true,
                        }],
                        yAxes: [{
                            stacked: true
                        }]
                    }
                }
            });
          }

 })(jQuery);

