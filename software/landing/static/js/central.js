// Settings -> Central CTF server.
//
// Optional: until the user joins an event, the landing page makes no network
// calls to any CTF server. Every string from the server is inserted as text,
// never as HTML.
(function () {
    'use strict';

    const STATE_LABELS = {
        draft: 'waiting for start',
        running: 'running',
        paused: 'paused',
        finished: 'finished',
    };

    let pollTimer = null;

    function el(tag, attrs, children) {
        const node = document.createElement(tag);
        Object.entries(attrs || {}).forEach(([key, value]) => {
            if (key === 'text') node.textContent = value;
            else if (key === 'class') node.className = value;
            else node.setAttribute(key, value);
        });
        (children || []).forEach(child => child && node.appendChild(child));
        return node;
    }

    function ago(seconds) {
        if (!seconds) return 'never';
        const delta = Math.max(0, Math.round(Date.now() / 1000 - seconds));
        if (delta < 60) return `${delta} s ago`;
        if (delta < 3600) return `${Math.round(delta / 60)} min ago`;
        return new Date(seconds * 1000).toLocaleString();
    }

    function setMessage(text, kind) {
        const box = document.getElementById('centralMessage');
        if (!box) return;
        box.textContent = text || '';
        box.className = 'central-message' + (kind ? ' ' + kind : '');
    }

    async function post(url, body) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body || {}),
        });
        let data = {};
        try { data = await response.json(); } catch (e) { /* not JSON */ }
        if (!response.ok || data.success === false) {
            throw new Error(data.message || `Request failed (HTTP ${response.status})`);
        }
        return data;
    }

    function formValues() {
        const value = id => (document.getElementById(id) || {}).value || '';
        return {
            server_url: value('centralServer').trim(),
            join_code: value('centralJoinCode').trim(),
            team_name: value('centralTeam').trim(),
            team_password: value('centralPassword'),
        };
    }

    function setBusy(busy) {
        document.querySelectorAll('#centralSection button').forEach(b => { b.disabled = busy; });
    }

    function renderJoinForm(snap) {
        const panel = document.getElementById('centralPanel');
        // Keep what the user is typing when the poll re-renders.
        if (panel.dataset.view === 'form') return;
        panel.dataset.view = 'form';
        panel.replaceChildren();

        const intro = el('p', {class: 'central-intro', text:
            'Optional. In a workshop, the organiser runs a central CTF server with a shared scoreboard. ' +
            'Join its event to report the challenges you solve here. Flags are still checked locally, ' +
            'and CybICS keeps working if the server is unreachable.'});
        panel.appendChild(intro);
        if (snap.revoked) {
            panel.appendChild(el('p', {class: 'central-message error', text:
                'The organiser removed this instance from the event. Solves are kept and will be ' +
                'reported once you join again.'}));
        }

        const field = (label, id, type, placeholder, value) => el('label', {text: label}, [
            el('input', {id, type, placeholder, autocomplete: 'off', value: value || ''}),
        ]);
        const team = snap.team || {};
        panel.appendChild(el('div', {class: 'central-form'}, [
            field('Server address', 'centralServer', 'text', 'http://10.10.0.1:8000', snap.server_url),
            field('Join code', 'centralJoinCode', 'text', 'from the organiser'),
            field('Team name', 'centralTeam', 'text', 'a new or an existing team', team.name),
            field('Team password', 'centralPassword', 'password',
                  'at least 8 characters for a new team'),
            el('div', {class: 'central-buttons'}, [
                el('button', {class: 'action-btn', type: 'button', id: 'centralTestBtn', text: '🔌 Test connection'}),
                el('button', {class: 'action-btn', type: 'button', id: 'centralJoinBtn', text: '🚩 Join event'}),
            ]),
        ]));
        document.getElementById('centralTestBtn').addEventListener('click', testConnection);
        document.getElementById('centralJoinBtn').addEventListener('click', join);
    }

    function renderEnrolled(snap) {
        const panel = document.getElementById('centralPanel');
        panel.dataset.view = 'enrolled';
        panel.replaceChildren();

        const event = snap.event || {};
        const standing = snap.standing || {};
        const state = event.state || 'unknown';
        const error = snap.last_error;

        const rows = [
            ['Server', snap.server_url, 'mono'],
            ['Event', event.name || event.slug || '-'],
            ['Team', (snap.team || {}).name || '-'],
        ];
        const grid = el('dl', {class: 'central-grid'});
        rows.forEach(([label, value, cls]) => {
            grid.appendChild(el('dt', {text: label}));
            grid.appendChild(el('dd', {class: cls || '', text: value || '-'}));
        });
        grid.appendChild(el('dt', {text: 'State'}));
        grid.appendChild(el('dd', {}, [el('span', {class: `central-state ${state}`,
                                                    text: STATE_LABELS[state] || state})]));
        grid.appendChild(el('dt', {text: 'Score'}));
        grid.appendChild(el('dd', {class: 'mono', text: standing.rank
            ? `${standing.score} points, rank ${standing.rank} of ${standing.teams}` : '-'}));
        grid.appendChild(el('dt', {text: 'Pending reports'}));
        grid.appendChild(el('dd', {class: 'mono', text: String(snap.pending || 0)}));
        grid.appendChild(el('dt', {text: 'Last contact'}));
        grid.appendChild(el('dd', {text: ago(snap.last_contact)}));
        if (error) {
            grid.appendChild(el('dt', {text: 'Last error'}));
            grid.appendChild(el('dd', {}, [el('span', {class: 'central-state error', text: error.message || error.code})]));
        }
        panel.appendChild(grid);

        const news = (snap.announcements || []).slice().reverse();
        if (news.length) {
            panel.appendChild(el('ul', {class: 'central-announcements'}, news.map(a => el('li', {}, [
                el('time', {text: ago(a.created_at)}),
                document.createTextNode(a.message || ''),
            ]))));
        }

        panel.appendChild(el('div', {class: 'central-buttons'}, [
            el('button', {class: 'action-btn', type: 'button', id: 'centralLeaveBtn', text: '🚪 Leave event'}),
        ]));
        document.getElementById('centralLeaveBtn').addEventListener('click', leave);
    }

    // ---------- uplink Wi-Fi (board only) ----------

    function renderUplink(snap) {
        const box = document.getElementById('centralUplink');
        if (!box) return;
        const uplink = snap.uplink;
        if (snap.platform !== 'physical' || !uplink) {
            box.hidden = true;
            return;
        }
        box.hidden = false;
        const status = uplink.status || {};
        const grid = document.getElementById('centralUplinkStatus');
        grid.replaceChildren();
        const add = (label, value, cls) => {
            grid.appendChild(el('dt', {text: label}));
            grid.appendChild(el('dd', {class: cls || '', text: value}));
        };
        if (!uplink.available) {
            add('Status', 'not available: the hwio service does not share its settings volume');
            return;
        }
        add('Adapter', status.present ? `${uplink.interface} found` : `no USB Wi-Fi adapter (${uplink.interface})`);
        add('Network', status.ssid || '-');
        add('Connection', uplink.pending ? 'applying...' : (status.state || (status.enabled ? 'enabled' : 'off')));
        if (status.ip) add('Address', status.ip, 'mono');
        if (status.error) add('Error', status.error);

        const ssid = document.getElementById('centralUplinkSsid');
        if (ssid && !ssid.value && status.ssid && document.activeElement !== ssid) ssid.value = status.ssid;
    }

    async function saveUplink(enabled) {
        const ssid = document.getElementById('centralUplinkSsid').value;
        const psk = document.getElementById('centralUplinkPsk').value;
        setBusy(true);
        setMessage(enabled ? 'Connecting the uplink...' : 'Switching the uplink off...');
        try {
            await post('/api/settings/central/uplink', {enabled, ssid, psk});
            document.getElementById('centralUplinkPsk').value = '';
            setMessage(enabled ? 'Uplink settings handed to the board. This takes a few seconds.'
                               : 'Uplink switched off.', 'ok');
        } catch (e) {
            setMessage(e.message, 'error');
        } finally {
            setBusy(false);
            refresh();
        }
    }

    // ---------- actions ----------

    async function testConnection() {
        const {server_url} = formValues();
        setBusy(true);
        setMessage('Contacting the server...');
        try {
            const data = await post('/api/settings/central/test', {server_url});
            const info = data.info || {};
            setMessage(`Reached ${info.name || 'the CTF server'}${info.version ? ' ' + info.version : ''}.`, 'ok');
        } catch (e) {
            setMessage(e.message, 'error');
        } finally {
            setBusy(false);
        }
    }

    async function join() {
        setBusy(true);
        setMessage('Joining the event...');
        try {
            const data = await post('/api/settings/central/enroll', formValues());
            const snap = data.snapshot || {};
            setMessage(`Joined ${(snap.event || {}).name || 'the event'} as ${(snap.team || {}).name || 'your team'}.`, 'ok');
            render(snap);
        } catch (e) {
            setMessage(e.message, 'error');
        } finally {
            setBusy(false);
        }
    }

    async function leave() {
        if (!confirm('Leave the event? Your local progress stays, and solves already reported stay on the scoreboard.')) return;
        setBusy(true);
        try {
            const data = await post('/api/settings/central/leave');
            setMessage('Left the event.', 'ok');
            render(data.snapshot || {});
        } catch (e) {
            setMessage(e.message, 'error');
        } finally {
            setBusy(false);
        }
    }

    function render(snap) {
        if (snap.enabled) renderEnrolled(snap);
        else renderJoinForm(snap);
        renderUplink(snap);
    }

    async function refresh() {
        try {
            const response = await fetch('/api/settings/central');
            if (!response.ok) return;
            render(await response.json());
        } catch (e) {
            // The landing page itself is unreachable; the next poll tries again.
        }
    }

    function start() {
        refresh();
        if (!pollTimer) pollTimer = setInterval(refresh, 5000);
    }

    function stop() {
        clearInterval(pollTimer);
        pollTimer = null;
    }

    document.addEventListener('DOMContentLoaded', () => {
        const up = document.getElementById('centralUplinkConnect');
        const down = document.getElementById('centralUplinkOff');
        if (up) up.addEventListener('click', () => saveUplink(true));
        if (down) down.addEventListener('click', () => saveUplink(false));
    });

    window.centralCtf = {start, stop};
})();
