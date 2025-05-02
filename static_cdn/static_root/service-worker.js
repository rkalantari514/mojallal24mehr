self.addEventListener('install', function(event) {
    console.log('Service Worker installing.');
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activating.');
});

self.addEventListener('fetch', function(event) {
    console.log('Fetching:', event.request.url);
});


const CACHE_NAME = 'my-cache-v1'; // نام کش
const URLs_TO_CACHE = [
    '/',
    '/site_statics/images/favicon.ico', // favicon
    '/site_statics/images/yassmojalal-192.png', // آیکون 192x192
    '/site_statics/images/yassmojalal-512.png', // آیکون 512x512
    '/css/style.css', // فایل CSS اصلی
    '/js/jquery-3.6.0.min.js', // jQuery
    '/js/popper.min.js', // Popper
    '/js/bootstrap.min.js', // Bootstrap
    '/js/bootstrap-select.min.js', // Bootstrap Select
    '/js/plugins-jquery.js', // پلاگین‌ها
    '/js/custom.js', // فایل JS سفارشی شما
    '/manifest.json', // فایل مانفیست
    // می‌توانید سایر فایل‌های CSS، JS و تصاویر مورد نیاز را به این لیست اضافه کنید
];

// هنگام نصب Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(URLs_TO_CACHE);
            })
    );
});

// هنگام فعال‌سازی Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// مدیریت درخواست‌های Fetch
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            // اگرCached response موجود باشد، آن را برگردانید.
            if (response) {
                return response;
            }
            // در غیر این صورت، درخواست را به شبکه ارسال کنید.
            return fetch(event.request);
        })
    );
});