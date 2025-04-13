// service-worker.js (update ASSETS_TO_CACHE)
const CACHE_NAME = 'vidyai-app-v1';
const OFFLINE_URL = '/offline.html';

// Assets to cache for offline usage
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/dashboard',
  '/dashboard.html',
  '/learning.html',
  '/quiz.html',
  '/offline.html',
  '/static/css/styles.css',
  '/static/js/pwa.js',
  '/static/js/login.js',
  '/static/js/dashboard.js',
  '/static/js/learning.js',
  '/static/js/quiz.js',
  '/static/images/logo.png',
  '/static/images/favicon.png',
  '/static/manifest.json'
];

// ... (rest of the service-worker.js remains unchanged)

// Content types to cache when requested
const CACHE_CONTENT_TYPES = [
  'text/html',
  'text/css',
  'text/javascript',
  'application/javascript',
  'application/json',
  'image/png',
  'image/jpeg',
  'image/svg+xml',
  'font/woff',
  'font/woff2'
];



// Install event - cache core assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing Service Worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Pre-caching app shell');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Pre-cache error:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating Service Worker...');
  
  event.waitUntil(
    caches.keys()
      .then((keyList) => {
        return Promise.all(keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache:', key);
            return caches.delete(key);
          }
        }));
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - handle network requests with cache-first strategy for assets,
// network-first for API requests
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }
  
  // Handle API requests - network first, then cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithBackgroundSync(event));
    return;
  }
  
  // Regular assets - cache first
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        
        return fetch(event.request)
          .then((networkResponse) => {
            // Check if we should cache this response
            if (shouldCache(event.request, networkResponse.clone())) {
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, networkResponse.clone());
                });
            }
            return networkResponse;
          })
          .catch((error) => {
            console.log('[Service Worker] Fetch failed, serving offline page', error);
            
            // For navigation requests, serve the offline page
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            
            // For image requests, you could return a placeholder
            if (event.request.destination === 'image') {
              return caches.match('/static/images/offline-placeholder.png');
            }
            
            // Return a basic error for everything else
            return new Response('Network error occurred', {
              status: 408,
              headers: { 'Content-Type': 'text/plain' }
            });
          });
      })
  );
});

// Background sync for submitting data while offline
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-quiz-results') {
    event.waitUntil(syncQuizResults());
  } else if (event.tag === 'sync-learning-progress') {
    event.waitUntil(syncLearningProgress());
  }
});

// Push notification handling for reminders and updates
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received:', event);
  
  const data = event.data.json();
  const title = data.title || 'VidyAI++';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/static/images/logo.png',
    badge: '/static/images/favicon.png',
    data: data.additionalData || {}
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification click received:', event);
  
  event.notification.close();
  
  // Determine where to navigate based on notification data
  const urlToOpen = event.notification.data.url || '/dashboard';
  
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // If no window/tab is open or matching our URL, open one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Helper function - Should we cache this response?
function shouldCache(request, response) {
  // Only cache successful responses
  if (!response || response.status !== 200) {
    return false;
  }
  
  // Don't cache if response indicates not to
  const cacheControl = response.headers.get('Cache-Control');
  if (cacheControl && cacheControl.includes('no-store')) {
    return false;
  }
  
  // Check if content type is in our list of cacheable types
  const contentType = response.headers.get('Content-Type') || '';
  return CACHE_CONTENT_TYPES.some(type => contentType.includes(type));
}

// Helper function - Network first with background sync fallback
function networkFirstWithBackgroundSync(event) {
  // Try network first
  return fetch(event.request.clone())
    .then((response) => {
      // Cache the response if valid
      if (response.ok) {
        caches.open(CACHE_NAME)
          .then((cache) => {
            cache.put(event.request, response.clone());
          });
      }
      return response;
    })
    .catch((error) => {
      console.log('[Service Worker] API fetch failed, falling back to cache', error);
      
      // Try to get from cache
      return caches.match(event.request)
        .then((cacheResponse) => {
          if (cacheResponse) {
            return cacheResponse;
          }
          
          // If it's a POST request, store it for later sync
          if (event.request.method === 'POST') {
            // Clone the request before consuming it
            const requestClone = event.request.clone();
            return requestClone.json()
              .then((requestData) => {
                // Store in IndexedDB for later sync
                storeForSync(event.request.url, requestData);
                
                // Return a mock successful response to the app
                return new Response(JSON.stringify({
                  success: true,
                  offline: true,
                  message: 'Your data has been saved and will be synced when you\'re back online.'
                }), {
                  headers: { 'Content-Type': 'application/json' }
                });
              })
              .catch(() => {
                // If we can't parse the request JSON, return error
                return new Response(JSON.stringify({
                  success: false,
                  offline: true,
                  message: 'Network error. Please try again when online.'
                }), {
                  status: 503,
                  headers: { 'Content-Type': 'application/json' }
                });
              });
          }
          
          // For GET requests without cache, return an appropriate offline message
          return new Response(JSON.stringify({
            success: false,
            offline: true,
            message: 'You are offline and this content is not available offline.'
          }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
          });
        });
    });
}

// Store data for later synchronization using IndexedDB
function storeForSync(url, data) {
  // Open (or create) the "offline-sync" database
  const openRequest = indexedDB.open('offline-sync', 1);
  
  // Create object stores if needed
  openRequest.onupgradeneeded = (event) => {
    const db = event.target.result;
    if (!db.objectStoreNames.contains('pending-requests')) {
      db.createObjectStore('pending-requests', { keyPath: 'id', autoIncrement: true });
    }
  };
  
  openRequest.onsuccess = (event) => {
    const db = event.target.result;
    const transaction = db.transaction('pending-requests', 'readwrite');
    const store = transaction.objectStore('pending-requests');
    
    // Store the request details
    store.add({
      url: url,
      data: data,
      method: 'POST',
      timestamp: new Date().getTime()
    });
    
    transaction.oncomplete = () => {
      console.log('[Service Worker] Stored request for later sync');
      // Register for sync if supported
      if ('SyncManager' in self) {
        if (url.includes('quiz')) {
          self.registration.sync.register('sync-quiz-results');
        } else {
          self.registration.sync.register('sync-learning-progress');
        }
      }
    };
  };
}

// Sync quiz results when online
function syncQuizResults() {
  return syncPendingRequests((url) => url.includes('quiz'));
}

// Sync learning progress when online
function syncLearningProgress() {
  return syncPendingRequests((url) => !url.includes('quiz'));
}

// Process pending requests from IndexedDB
function syncPendingRequests(urlFilter) {
  return new Promise((resolve, reject) => {
    const openRequest = indexedDB.open('offline-sync', 1);
    
    openRequest.onsuccess = (event) => {
      const db = event.target.result;
      const transaction = db.transaction('pending-requests', 'readwrite');
      const store = transaction.objectStore('pending-requests');
      const requests = [];
      
      // Get all pending requests
      store.openCursor().onsuccess = (event) => {
        const cursor = event.target.result;
        if (cursor) {
          const request = cursor.value;
          // Filter by URL if needed
          if (!urlFilter || urlFilter(request.url)) {
            requests.push({
              id: cursor.key,
              request: request
            });
          }
          cursor.continue();
        } else {
          // Process all matched requests
          Promise.all(
            requests.map((item) => {
              return fetch(item.request.url, {
                method: item.request.method,
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(item.request.data)
              })
              .then((response) => {
                if (response.ok) {
                  // Remove from store if successful
                  const deleteTransaction = db.transaction('pending-requests', 'readwrite');
                  const deleteStore = deleteTransaction.objectStore('pending-requests');
                  return deleteStore.delete(item.id);
                }
              })
              .catch((error) => {
                console.error('[Service Worker] Sync failed for request:', error);
                // Will be retried on next sync
              });
            })
          )
          .then(() => {
            console.log('[Service Worker] Sync completed');
            resolve();
          })
          .catch((error) => {
            console.error('[Service Worker] Sync error:', error);
            reject(error);
          });
        }
      };
    };
    
    openRequest.onerror = (event) => {
      console.error('[Service Worker] IndexedDB error:', event.target.error);
      reject(event.target.error);
    };
  });
}