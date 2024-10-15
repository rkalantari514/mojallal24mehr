/*

Template:  Webmin - Bootstrap 4 & Angular 5 Admin Dashboard Template
Author: potenzaglobalsolutions.com
Design and Developed by: potenzaglobalsolutions.com

NOTE: 

*/

 (function($){
  "use strict";

  $('#sweetalert-01').click(function(e) {
     swal('هر کس می تواند از کامپیوتر استفاده کند')
  });

 
  $('#sweetalert-02').click(function(e) {
  swal(
  'اینترنت؟',
  'این چیز هنوز در اطراف است؟',
  'question'
    )
  });

  $('#sweetalert-03').click(function(e) {
      swal({
      type: 'error',
      title: 'اوه...',
      text: 'چیزی اشتباه رفت!',
      footer: '<a href>چرا این مسئله را دارم؟</a>',
    })
  });

  $('#sweetalert-04').click(function(e) {
    swal({
    imageUrl: 'images/profile-avatar.jpg',
    imageHeight: 596,
    imageAlt: 'A tall image'
  })
  });

  $('#sweetalert-05').click(function(e) {
    swal({
    title: '<i>مثال</i> <u>اچ تی ام ال</u>',
    type: 'info',
    html:
      'شما می توانید استفاده کنید <b>متن ضخیم</b>, ' +
      '<a href="//github.com">links</a> ' +
      'و سایر تگ های HTML',
    showCloseButton: true,
    showCancelButton: true,
    focusConfirm: false,
    confirmButtonText:
      '<i class="fa fa-thumbs-up"></i> عالی!',
    confirmButtonAriaLabel: 'شگفت انگیز، عالی!',
    cancelButtonText:
    '<i class="fa fa-thumbs-down"></i>',
    cancelButtonAriaLabel: 'Thumbs down',
  })
  });

  $('#sweetalert-06').click(function(e) {
  swal({
    position: 'top-end',
    type: 'success',
    title: 'کار شما ذخیره شده است',
    showConfirmButton: false,
    timer: 1500
  })
  });

  $('#sweetalert-07').click(function(e) {
  swal({
      title: 'انیمیشن سفارشی با Animate.css',
      animation: false,
      customClass: 'animated tada'
    })
  });

  $('#sweetalert-08').click(function(e) {
      swal({
      title: 'شما مطمئن هستید؟',
      text: "شما قادر نخواهید بود این را دوباره برگردانید!",
      type: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'بله، آن را حذف کنید!'
    }).then((result) => {
      if (result.value) {
        swal(
          'حذف شده!',
          'فایل شما پاک شده است.',
          'success'
        )
      }
    })
  });

  $('#sweetalert-09').click(function(e) {
      swal({
      title: 'صورت وضعیت را حذف می کنید؟',
      text: "شما قادر نخواهید بود این را دوباره برگردانید!",
      type: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'بله، آن را حذف کنید!',
      cancelButtonText: 'نه، لغو!',
      confirmButtonClass: 'btn btn-success',
      cancelButtonClass: 'btn btn-danger',
      buttonsStyling: false,
      reverseButtons: true
    }).then((result) => {
      if (result.value) {
        swal(
          'حذف شده!',
          'فایل شما پاک شده است.',
          'success'
        )
      } else if (
        // Read more about handling dismissals
        result.dismiss === swal.DismissReason.cancel
      ) {
        swal(
          'لغو شده',
          'فایل خیالی شما امن است :)',
          'error'
        )
      }
    })
  });

  $('#sweetalert-10').click(function(e) {
    swal({
    title: 'شیرین!',
    text: 'مدال با یک تصویر سفارشی.',
    imageUrl: 'https://unsplash.it/400/200',
    imageWidth: 400,
    imageHeight: 200,
    imageAlt: 'Custom image',
    animation: false
  })
  });

  $('#sweetalert-11').click(function(e) {
    swal({
    title: 'عرض سفارشی، پس زمینه، پس زمینه.',
    width: 600,
    padding: 100,
    background: '#fff url(/images/trees.png)',
    backdrop: `
      rgba(0,0,123,0.4)
      url("/images/nyan-cat.gif")
      center left
      no-repeat
    `
  })
  });

  $('#sweetalert-12').click(function(e) {
   swal({
      title: 'هشدار خودکار بستن!',
      text: 'من در 5 ثانیه بسته خواهم شد.',
      timer: 5000,
      onOpen: () => {
        swal.showLoading()
      }
    }).then((result) => {
      if (
        // Read more about handling dismissals
        result.dismiss === swal.DismissReason.timer
      ) {
        console.log('من با تایمر بسته شدم')
      }
    })
  });


  $('#sweetalert-13').click(function(e) {
      swal({
      title: 'هل تريد الاستمرار؟',
      confirmButtonText:  'نعم',
      cancelButtonText:  'لا',
      showCancelButton: true,
      showCloseButton: true,
      target: document.getElementById('rtl-container')
    })
  });

  $('#sweetalert-14').click(function(e) {
      swal({
      title: 'ارسال ایمیل به اجرا درخواست آژاکس',
      input: 'email',
      showCancelButton: true,
      confirmButtonText: 'ارسال',
      showLoaderOnConfirm: true,
      preConfirm: (email) => {
        return new Promise((resolve) => {
          setTimeout(() => {
            if (email === 'taken@example.com') {
              swal.showValidationError(
                'این ایمیل قبلا گرفته شده است.'
              )
            }
            resolve()
          }, 2000)
        })
      },
      allowOutsideClick: () => !swal.isLoading()
    }).then((result) => {
      if (result.value) {
        swal({
          type: 'success',
          title: 'درخواست آژاکس به پایان رسید!',
          html: 'Submitted email: ' + result.value
        })
      }
    })
  });
  
  $('#sweetalert-15').click(function(e) {
    swal.setDefaults({
    input: 'text',
    confirmButtonText: 'بعدی &rarr;',
    showCancelButton: true,
    progressSteps: ['1', '2', '3']
  })

  var steps = [
    {
      title: 'سوال 1',
      text: 'زنجیر زغالسنگ 2 مودل آسان است'
    },
    'سوال 2',
    'سوال 3'
  ]

  swal.queue(steps).then((result) => {
    swal.resetDefaults()

    if (result.value) {
      swal({
        title: 'همه انجام شده است!',
        html:
          'جواب شما: <pre>' +
            JSON.stringify(result.value) +
          '</pre>',
        confirmButtonText: 'دوست داشتني!'
      })
    }
  })
  });

  $('#sweetalert-16').click(function(e) {
    const ipAPI = 'https://api.ipify.org?format=json'
    swal.queue([{
      title: 'IP عمومی شما',
      confirmButtonText: 'نمایش عمومی من IP',
      text:
        'IP عمومی شما دریافت خواهد شد ' +
        'از طریق درخواست آژاکس',
      showLoaderOnConfirm: true,
      preConfirm: () => {
        return fetch(ipAPI)
          .then(response => response.json())
          .then(data => swal.insertQueueStep(data.ip))
          .catch(() => {
            swal.insertQueueStep({
              type: 'error',
              title: 'قادر به دریافت IP عمومی شما نیست'
            })
          })
      }
    }])
  });

 })(jQuery);