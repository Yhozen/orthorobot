/* Evaluated inside the pinned love.js factory, where FS and IDBFS are available. */
if (typeof ENVIRONMENT_IS_PTHREAD === 'undefined' || !ENVIRONMENT_IS_PTHREAD) {
  Module.addRunDependency('IDBFS_sync');
  let available = false, busy = false, pending = false, waiters = [];
  const warn = error => {
    console.warn('Persistent storage unavailable:', error);
    if (Module.onStorageWarning) Module.onStorageWarning(error);
  };
  function flush() {
    if (!available) return Promise.resolve(false);
    return new Promise(resolve => {
      waiters.push(resolve);
      pending = true;
      pump();
    });
  }
  function pump() {
    if (busy || !pending) return;
    pending = false; busy = true;
    const batch = waiters; waiters = [];
    function done(error) {
      busy = false;
      if (error) { available = false; warn(error); }
      batch.forEach(resolve => resolve(!error));
      if (!available) { waiters.splice(0).forEach(resolve => resolve(false)); pending = false; }
      else pump();
    }
    try { FS.syncfs(false, done); } catch (error) { done(error); }
  }
  Module.flushSaves = flush;
  function hydrated(error) {
    available = !error;
    if (error) warn(error);
    Module.removeRunDependency('IDBFS_sync');
    if (available) {
      setInterval(flush, 2000);
      document.addEventListener('visibilitychange', () => { if (document.hidden) flush(); });
      window.addEventListener('pagehide', flush);
    }
  }
  try {
    FS.mkdirTree('/home/web_user/love');
    FS.mount(IDBFS, {}, '/home/web_user/love');
    FS.syncfs(true, hydrated);
  } catch (error) { hydrated(error); }
}
