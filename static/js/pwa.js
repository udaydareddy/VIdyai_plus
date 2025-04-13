// static/js/pwa.js
// Register service worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
      navigator.serviceWorker.register('/service-worker.js')
        .then(function(registration) {
          console.log('Service Worker registered with scope:', registration.scope);
        })
        .catch(function(error) {
          console.error('Service Worker registration failed:', error);
        });
    });
  }
  
  // Handle PWA installation prompt
  let deferredPrompt = null;
  const installButton = document.getElementById('install-app');
  
  window.addEventListener('beforeinstallprompt', function(event) {
    event.preventDefault();
    deferredPrompt = event;
    if (installButton) {
      installButton.classList.remove('d-none');
      installButton.addEventListener('click', function() {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          deferredPrompt.userChoice.then(function(choiceResult) {
            if (choiceResult.outcome === 'accepted') {
              console.log('User accepted the install prompt');
            } else {
              console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
            installButton.classList.add('d-none');
          });
        }
      });
    }
  });
  
  // Notify user if offline
  window.addEventListener('offline', function() {
    console.log('App is offline');
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
      statusElement.innerHTML = '<span class="badge bg-warning">Offline</span>';
    }
  });
  
  window.addEventListener('online', function() {
    console.log('App is online');
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
      statusElement.innerHTML = '<span class="badge bg-success">Online</span>';
    }
  });
  
  // Expose addPendingAction globally (used by other scripts)
  function addPendingAction(url, method, headers, body) {
    const pendingActions = JSON.parse(localStorage.getItem('pendingActions') || '[]');
    pendingActions.push({
      url,
      method,
      headers,
      body,
      retries: 0
    });
    localStorage.setItem('pendingActions', JSON.stringify(pendingActions));
  }