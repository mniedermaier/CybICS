// Banners from CybICS-mgmt jobs on the dashboard (templates/index.html).
//
// An organiser's identify job shows "This is <label>", a message job the
// organiser's text. Both only arrive if the user allowed that action in
// Settings -> CybICS-mgmt. The text is inserted as text, never as HTML. A
// dismissed banner stays dismissed in this tab.
(function () {
    'use strict';

    const box = document.getElementById('mgmtBanners');
    if (!box) return;
    const KEY = 'cybics-mgmt-dismissed';
    const KICKER = {identify: 'CybICS-mgmt · identify', message: 'Message from the organiser'};
    let dismissed = new Set();
    try { dismissed = new Set(JSON.parse(sessionStorage.getItem(KEY) || '[]')); } catch (e) { /* private mode */ }
    let shownKey = '';

    // Banner ids restart with landing, so the text is part of the key.
    const keyOf = banner => `${banner.id}|${banner.text}`;

    function dismiss(banner) {
        dismissed.add(keyOf(banner));
        try { sessionStorage.setItem(KEY, JSON.stringify([...dismissed].slice(-50))); } catch (e) { /* ignore */ }
        poll();
    }

    function render(banners) {
        const visible = banners.filter(b => !dismissed.has(keyOf(b)));
        const key = visible.map(keyOf).join('\n');
        if (key === shownKey) return;
        shownKey = key;
        box.replaceChildren(...visible.map(banner => {
            const node = document.createElement('div');
            node.className = 'mgmt-banner ' + (banner.kind === 'identify' ? 'identify' : 'message');
            node.setAttribute('role', banner.kind === 'identify' ? 'alert' : 'status');
            const body = document.createElement('div');
            body.className = 'mgmt-banner-body';
            const kicker = document.createElement('span');
            kicker.className = 'mgmt-banner-kicker';
            kicker.textContent = KICKER[banner.kind] || KICKER.message;
            const text = document.createElement('div');
            text.className = 'mgmt-banner-text';
            text.textContent = banner.text;
            body.append(kicker, text);
            const close = document.createElement('button');
            close.type = 'button';
            close.className = 'mgmt-banner-close';
            close.setAttribute('aria-label', 'Dismiss');
            close.textContent = '✕';
            close.addEventListener('click', () => dismiss(banner));
            node.append(body, close);
            return node;
        }));
    }

    function poll() {
        fetch('/api/mgmt/banners', {cache: 'no-store'})
            .then(r => (r.ok ? r.json() : {banners: []}))
            .then(data => render(Array.isArray(data.banners) ? data.banners : []))
            .catch(() => {});
    }

    // Every 5 s while the dashboard is visible; one cheap in-memory lookup.
    let timer = null;
    function start() {
        poll();
        if (!timer) timer = setInterval(poll, 5000);
    }
    function stop() {
        clearInterval(timer);
        timer = null;
    }
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    start();
})();
