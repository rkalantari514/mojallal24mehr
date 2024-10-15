/*

Template:  Webmin - Bootstrap 4 & Angular 5 Admin Dashboard Template
Author: potenzaglobalsolutions.com
Design and Developed by: potenzaglobalsolutions.com

NOTE: 

*/

 (function($){
  "use strict";
  $(function () {
      $('#lobilist-demo').lobiList({
          
          lists: [
        {
            title: 'انجام دادن',
            defaultStyle: 'lobilist-info',
            items: [
                {
                    title: 'درختان سرد سرد',
                    description: 'تندر سفر مسافرانی را با احتیاط انجام داد، دریاچه، دریاچه.',
                    dueDate: '2015-01-31'
                },
                {
                    title: 'دوره غرور',
                    description: 'پذیرفته نرم بود',
                    done: true
                },
                {
                    title: 'پرچم بهتر کبوتر را می سوزاند',
                    description: 'شکافته ردیف جست و خیز در نتیجه، حسرت لباس شب غریبه مزاحم شوخی خائنانه در تیرگی.'
                },
                {
                    title: 'پذیرفته نرم بود',
                    description: 'شکافته ردیف جست و خیز در نتیجه، حسرت لباس شب غریبه مزاحم شوخی خائنانه در تیرگی.',
                    dueDate: '2015-02-02'
                }
            ]
        },
        {
            title: 'در حال انجام',
            items: [
                {
                    title: 'سینی های کامپوزیتی',
                    description: 'هری رطوبت را تحریک می کند. شلوارهای شلوارهای شلوار جلب توجه می کند. چادر به آرامی مطابقت می کند دختران برجسته تسلیحات اسلاید ضخیم دختران.'
                },
                {
                    title: 'برگ شیک'
                },
                {
                    title: 'حدس زده است که ارتش های بین المللی اغراق می کنند',
                    description: 'هر وقت که بخواهید قورباغه را بخوانید می بینید چامپلین، لئوپارد زنده گرگ و میش است.',
                    dueDate: '2015-02-04',
                    done: true
                }
            ]
        }
    ]
  });
 
 $('#lobilist-demo-02').lobiList({
    lists: [
        {
            title: 'انجام دادن',
            defaultStyle: 'lobilist-info',
            items: [
                {
                    title: 'درختان سرد سرد',
                    description: 'تندر سفر مسافرانی را با احتیاط انجام داد، دریاچه، دریاچه.',
                    dueDate: '2015-01-31'
                }
            ]
        }
    ],
    afterListAdd: function(lobilist, list){
        var $dueDateInput = list.$el.find('form [name=dueDate]');
        $dueDateInput.datepicker();
    }
   });
 
  $('#lobilist-demo-03').lobiList({
   lists: [
        {
            title: 'انجام دادن',
            defaultStyle: 'lobilist-info',
            controls: ['edit', 'styleChange'],
            items: [
                {
                    title: 'درختان سرد سرد',
                    description: 'تندر سفر مسافرانی را با احتیاط انجام داد، دریاچه، دریاچه.',
                    dueDate: '2015-01-31'
                }
            ]
        },
        {
            title: 'کادرهای سفارشی غیرفعال شده',
            defaultStyle: 'lobilist-danger',
            controls: ['edit', 'add', 'remove'],
            useLobicheck: false,
            items: [
                {
                    title: 'دوره غرور',
                    description: 'پذیرفته نرم بود',
                    done: true
                }
            ]
        },
        {
            title: 'کنترل غیرفعال ',
            controls: false,
            items: [
                {
                    title: 'سینی های کامپوزیتی',
                    description: 'هری رطوبت را تحریک می کند. ' +
                    'شلوارهای شلوارهای شلوار جلب توجه می کند. چادر به راحتی با ساندویچ اسلحه با مضمون ضخیم مطابقت دارد ' +
                    'دختران مشهور پرتوها.'
                }
            ]
        },
        {
            title: 'غیر فعال به ویرایش / حذف',
            enableTodoRemove: false,
            enableTodoEdit: false,
            items: [
                {
                    title: 'سینی های کامپوزیتی',
                    description: 'هری رطوبت را تحریک می کند. ' +
                    'شلوارهای شلوارهای شلوار جلب توجه می کند. چادر به راحتی با ساندویچ اسلحه با مضمون ضخیم مطابقت دارد ' +
                    'دختران مشهور پرتوها.'
                }
            ]
        }
    ]


   });
 
  $('#lobilist-demo-04').lobiList({
  sortable: false,
    lists: [
        {
            title: 'انجام دادن',
            defaultStyle: 'lobilist-info',
            controls: ['edit', 'styleChange'],
            items: [
                {
                    title: 'درختان سرد سرد',
                    description: 'تندر سفر مسافرانی را با احتیاط انجام داد، دریاچه، دریاچه.',
                    dueDate: '2015-01-31'
                }
            ]
        },
        {
            title: 'کنترل غیرفعال ',
            controls: false,
            items: [
                {
                    title: 'سینی های کامپوزیتی',
                    description: 'هری رطوبت را تحریک می کند. شلوارهای شلوارهای شلوار جلب توجه می کند. چادر به آرامی مطابقت می کند دختران برجسته تسلیحات اسلاید ضخیم دختران.'
                }
            ]
        }
    ]
   });
 });

 })(jQuery);