// Settings -> CybICS-mgmt (templates/settings.html, #mgmt).
//
// Optional: until the user connects (or a board's uplink is on the default
// network cybics-mgmt), the landing page makes no network calls to any
// server. Every string from the server is inserted as text, never as HTML.
//
// The markup is static. A poll only updates text and visibility, so a field
// being typed in or a focused button survives it.
(function () {
    'use strict';

    const {el, setMsg, setBusy, request, post} = window.cybicsSettings;
    const $ = id => document.getElementById(id);
    const physical = document.body.dataset.platform === 'physical';

    const STATE_LABELS = {
        draft: 'Waiting for start',
        running: 'Running',
        paused: 'Paused',
        finished: 'Finished',
    };

    // The actions landing offers (snapshot.available), in words for the switches.
    const ACTIONS = {
        identify: ['Identify', 'Show a banner with this device\'s name on the dashboard, so the organiser can find it.'],
        message: ['Messages', 'Show a message from the organiser on the dashboard.'],
        restart: ['Restart services', 'Restart one CybICS service, or all of them. Running attacks or captures stop.'],
        reset_progress: ['Reset CTF progress', 'Clear the local CTF progress on this device.'],
        collect_logs: ['Collect logs', 'Send the CybICS container logs to the organiser, for troubleshooting.'],
    };

    // The client's transport errors, in words a participant can act on. The
    // server's own messages are written for end users and shown as they are.
    function explain(error) {
        if (error.code === 'unreachable') {
            return physical
                ? 'Cannot reach the server. Check the address, and that the event Wi-Fi is connected.'
                : 'Cannot reach the server. Check the address, and that this computer is on the event network.';
        }
        if (error.code === 'bad_response') {
            return 'Something answered at that address, but not a CybICS-mgmt server. Check the address and port.';
        }
        return error.message;
    }

    function fail(id, error) {
        const text = explain(error);
        setMsg(id, text, 'error', text === error.message ? '' : error.message);
    }

    function ago(seconds) {
        if (!seconds) return 'never';
        const delta = Math.max(0, Math.round(Date.now() / 1000 - seconds));
        if (delta < 60) return `${delta} s ago`;
        if (delta < 3600) return `${Math.round(delta / 60)} min ago`;
        return new Date(seconds * 1000).toLocaleString();
    }

    function setField(root, name, value) {
        const node = root.querySelector(`[data-field="${name}"]`);
        if (node && node.textContent !== value) node.textContent = value;
    }

    function setRow(root, name, visible) {
        root.querySelectorAll(`[data-row="${name}"]`).forEach(node => { node.hidden = !visible; });
    }

    function prefill(input, value) {
        if (input && value && !input.value && document.activeElement !== input) input.value = value;
    }

    // ---------- rendering ----------

    function renderStatus(snap) {
        const card = $('mgmtStatus');
        const device = snap.device || {};
        const error = snap.last_error;
        const forged = !!error && error.code === 'bad_signature';
        setField(card, 'label', device.label || 'This device');
        setRow(card, 'group', !!device.group);
        if (device.group) setField(card, 'group', device.group);
        const pill = card.querySelector('[data-field="link"]');
        const trouble = !!error && !forged;
        setField(card, 'link', trouble ? 'Problem' : (snap.last_contact ? 'Online' : 'Connecting'));
        pill.className = 'state-pill ' + (trouble ? 'warn' : (snap.last_contact ? 'ok' : 'draft'));
        setField(card, 'server', snap.server_url || '–');
        setField(card, 'contact', ago(snap.last_contact));
        setField(card, 'fingerprint', snap.key_fingerprint || '–');
        $('forgedNote').hidden = !forged;
        setRow(card, 'error', trouble);
        if (trouble) setField(card, 'error', explain(error));
    }

    let newsKey = '';

    function renderEvent(snap) {
        const card = $('eventCard');
        const ctf = snap.ctf || {};
        const inEvent = !!(ctf.joined || ctf.removed);
        setRow(card, 'in-event', inEvent);
        setRow(card, 'no-event', !inEvent);
        if (!inEvent) {
            prefill($('teamName'), (ctf.team || {}).name);
            return;
        }
        const event = ctf.event || {};
        const standing = ctf.standing || {};
        const state = event.state || 'unknown';
        setField(card, 'event', event.name || event.slug || 'Event');
        setField(card, 'team', (ctf.team || {}).name || '–');
        const pill = card.querySelector('[data-field="state"]');
        setField(card, 'state', STATE_LABELS[state] || state);
        pill.className = 'state-pill ' + state;
        setRow(card, 'removed', !!ctf.removed);
        setField(card, 'score', standing.rank ? String(standing.score) : '–');
        setField(card, 'rank', standing.rank ? `${standing.rank} / ${standing.teams}` : '–');
        setField(card, 'pending', String(ctf.pending || 0));

        const news = (ctf.announcements || []).slice().reverse();
        const key = news.map(a => a.id).join(',');
        setRow(card, 'news', news.length > 0);
        if (key !== newsKey) {
            newsKey = key;
            card.querySelector('[data-field="news"]').replaceChildren(...news.map(a => el('li', {}, [
                el('time', {text: ago(a.created_at)}),
                document.createTextNode(a.message || ''),
            ])));
        }
    }

    let actionsKey = '';

    function renderActions(snap) {
        const available = snap.available || [];
        const allowed = new Set(snap.allowed || []);
        const list = $('actionList');
        const key = available.join(',');
        if (key !== actionsKey) {
            actionsKey = key;
            list.replaceChildren(...available.map(action => {
                const [title, hint] = ACTIONS[action] || [action, ''];
                const button = el('button', {
                    type: 'button', class: 'switch', role: 'switch', 'aria-checked': 'false',
                    'aria-labelledby': `action-${action}-label`, 'aria-describedby': `action-${action}-hint`,
                    'data-allow': action,
                }, [el('span', {class: 'switch-thumb', 'aria-hidden': 'true'})]);
                return el('div', {class: 'switch-row'}, [
                    el('div', {}, [
                        el('h4', {id: `action-${action}-label`, text: title}),
                        el('p', {class: 'muted', id: `action-${action}-hint`, text: hint}),
                    ]),
                    button,
                ]);
            }));
        }
        list.querySelectorAll('[data-allow]').forEach(button => {
            if (!button.hasAttribute('aria-busy')) {
                button.setAttribute('aria-checked', String(allowed.has(button.dataset.allow)));
            }
        });
    }

    let jobsKey = '';

    function renderJobs(snap) {
        const history = (snap.history || []).slice().reverse();
        const queued = (snap.queue || []).length + (snap.running ? 1 : 0);
        $('jobsEmpty').hidden = history.length > 0 || queued > 0;
        $('jobsQueued').hidden = queued === 0;
        $('jobsQueued').textContent = queued ? `${queued} job${queued === 1 ? '' : 's'} waiting or running.` : '';
        const key = history.map(j => `${j.id}:${j.state}`).join(',');
        if (key === jobsKey) return;
        jobsKey = key;
        $('jobList').replaceChildren(...history.map(job => {
            const title = (ACTIONS[job.action] || [job.action])[0];
            const params = job.params && Object.keys(job.params).length
                ? ' (' + Object.entries(job.params).map(([k, v]) => `${k}: ${v}`).join(', ') + ')' : '';
            return el('li', {}, [
                el('span', {}, [el('span', {class: 'job-action', text: title + params}),
                                el('span', {class: 'job-time', text: ' · ' + ago(job.time)})]),
                el('span', {class: 'state-pill ' + (job.state || ''), text: job.state || '?'}),
                job.detail ? el('span', {class: 'job-detail', text: job.detail}) : null,
            ]);
        }));
    }

    function renderUplink(snap) {
        const card = $('uplinkCard');
        if (!card) return;
        const uplink = snap.uplink;
        card.hidden = !uplink;
        if (!uplink) return;
        const status = uplink.status || {};
        const connect = card.querySelector('[data-action="uplink-on"]');
        const off = card.querySelector('[data-action="uplink-off"]');
        if (!uplink.available) {
            setField(card, 'adapter', 'Not available: the hwio service does not share its settings volume');
            connect.disabled = off.disabled = true;
            return;
        }
        setField(card, 'adapter', status.present ? `Found (${uplink.interface})` : 'No USB Wi-Fi adapter plugged in');
        setField(card, 'network', status.ssid || '–');
        setField(card, 'connection', uplink.pending ? 'Applying…'
            : (status.state || (status.enabled ? 'Enabled' : 'Off')));
        setRow(card, 'ip', !!status.ip);
        if (status.ip) setField(card, 'ip', status.ip);
        setRow(card, 'uerror', !!status.error);
        if (status.error) setField(card, 'uerror', status.error);
        if (!connect.hasAttribute('aria-busy')) connect.disabled = !status.present;
        if (!off.hasAttribute('aria-busy')) off.disabled = !(status.enabled || uplink.pending);
        $('uplinkHint').hidden = !!status.present;
        prefill($('uplinkSsid'), status.ssid);
    }

    function renderNavPill(snap) {
        const pill = $('mgmtNavPill');
        if (!snap.enabled) {
            pill.hidden = true;
            return;
        }
        const ctf = snap.ctf || {};
        const state = (ctf.event || {}).state;
        const rank = (ctf.standing || {}).rank;
        const trouble = !!snap.last_error;
        pill.hidden = false;
        pill.className = 'nav-pill ' + (trouble ? 'warn' : (state === 'running' ? 'running' : ''));
        pill.textContent = trouble ? 'Problem'
            : (ctf.joined && rank ? `#${rank}` : (ctf.joined ? (STATE_LABELS[state] || 'Joined') : 'Connected'));
    }

    function render(snap) {
        const flow = $('mgmtFlow');
        const connected = !!snap.enabled;
        $('mgmtLoading').hidden = true;
        flow.setAttribute('aria-busy', 'false');
        flow.classList.toggle('is-enrolled', connected);
        ['mgmtStatus', 'eventCard', 'actionsCard', 'jobsCard'].forEach(id => { $(id).hidden = !connected; });
        $('serverCard').hidden = connected;
        $('connectCard').hidden = connected;
        if (connected) {
            renderStatus(snap);
            renderEvent(snap);
            renderActions(snap);
            renderJobs(snap);
        } else {
            $('revokedNote').hidden = !snap.revoked;
            $('optedOutNote').hidden = !(physical && snap.opted_out);
            prefill($('serverUrl'), snap.server_url);
        }
        renderUplink(snap);
        renderNavPill(snap);
    }

    async function refresh() {
        try {
            render(await request('/api/settings/mgmt'));
        } catch (e) {
            // The landing page itself is unreachable; the next poll tries again.
        }
    }

    // ---------- actions: not connected ----------

    function serverUrl() {
        const value = $('serverUrl').value.trim();
        if (!value) {
            setMsg('serverMsg', 'Enter the server address the organiser gave you.', 'error');
            $('serverUrl').focus();
        }
        return value;
    }

    $('serverForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = event.submitter || $('serverForm').querySelector('[data-action="test"]');
        const server_url = serverUrl();
        if (!server_url) return;
        setBusy(button, true);
        setMsg('serverMsg', 'Contacting the server…');
        try {
            const info = (await post('/api/settings/mgmt/test', {server_url})).info || {};
            setMsg('serverMsg', `Reached ${info.name || 'CybICS-mgmt'}${info.version ? ' ' + info.version : ''}. Continue with the code below.`, 'ok');
        } catch (e) {
            fail('serverMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    $('connectForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = $('connectForm').querySelector('[data-action="connect"]');
        const server_url = serverUrl();
        if (!server_url) return;
        const body = {server_url, code: $('mgmtCode').value.trim(), label: $('mgmtLabel').value.trim()};
        if (!body.code) {
            setMsg('connectMsg', 'Enter the code from the organiser.', 'error');
            $('mgmtCode').focus();
            return;
        }
        setBusy(button, true);
        setMsg('connectMsg', 'Connecting…');
        try {
            const snap = (await post('/api/settings/mgmt/connect', body)).snapshot || {};
            $('mgmtCode').value = '';
            setMsg('connectMsg', '');
            render(snap);
            setMsg('statusMsg', `Connected as ${(snap.device || {}).label || 'this device'}. No action is allowed yet.`, 'ok');
            const heading = $('mgmtStatus').querySelector('[data-field="label"]');
            heading.setAttribute('tabindex', '-1');
            heading.focus();
        } catch (e) {
            fail('connectMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    // ---------- actions: connected ----------

    $('joinForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = $('joinForm').querySelector('[data-action="join"]');
        const body = {
            join_code: $('joinCode').value.trim(),
            team_name: $('teamName').value.trim(),
            team_password: $('teamPassword').value,
        };
        const missing = [['join_code', 'joinCode'], ['team_name', 'teamName'], ['team_password', 'teamPassword']]
            .find(([key]) => !body[key]);
        if (missing) {
            setMsg('joinMsg', 'Fill in the join code, team name and team password.', 'error');
            $(missing[1]).focus();
            return;
        }
        setBusy(button, true);
        setMsg('joinMsg', 'Joining the event…');
        try {
            const snap = (await post('/api/settings/mgmt/join', body)).snapshot || {};
            $('teamPassword').value = '';
            $('joinCode').value = '';
            setMsg('joinMsg', '');
            render(snap);
            const ctf = snap.ctf || {};
            setMsg('eventMsg', `Joined ${(ctf.event || {}).name || 'the event'} as ${(ctf.team || {}).name || 'your team'}.`, 'ok');
        } catch (e) {
            fail('joinMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    function closeBox(name) {
        const box = document.querySelector(`[data-confirm="${name}"]`);
        box.querySelector('.confirm-box').hidden = true;
        box.querySelector(`[data-action="${name}-ask"]`).hidden = false;
    }

    document.querySelector('[data-action="leave"]').addEventListener('click', async event => {
        const button = event.currentTarget;
        setBusy(button, true);
        try {
            const snap = (await post('/api/settings/mgmt/leave-event')).snapshot || {};
            closeBox('leave');
            setMsg('eventMsg', '');
            render(snap);
            setMsg('joinMsg', 'Left the event. Solves made from now on stay local.', 'ok');
        } catch (e) {
            fail('eventMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    document.querySelector('[data-action="disconnect"]').addEventListener('click', async event => {
        const button = event.currentTarget;
        setBusy(button, true);
        try {
            const snap = (await post('/api/settings/mgmt/disconnect')).snapshot || {};
            closeBox('disconnect');
            setMsg('statusMsg', '');
            render(snap);
            setMsg('serverMsg', 'Disconnected. Solves made from now on stay local.', 'ok');
            $('serverUrl').focus();
        } catch (e) {
            fail('statusMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    $('actionList').addEventListener('click', async event => {
        const button = event.target.closest('[data-allow]');
        if (!button) return;
        const on = button.getAttribute('aria-checked') !== 'true';
        const actions = [...$('actionList').querySelectorAll('[data-allow]')]
            .filter(b => (b === button ? on : b.getAttribute('aria-checked') === 'true'))
            .map(b => b.dataset.allow);
        setBusy(button, true);
        try {
            const data = await post('/api/settings/mgmt/allowed', {actions});
            setMsg('actionsMsg', '');
            render(data.snapshot || {});
        } catch (e) {
            fail('actionsMsg', e);
        } finally {
            setBusy(button, false);
            refresh();
        }
    });

    const uplinkForm = $('uplinkForm');
    if (uplinkForm) {
        const save = async (enabled, button) => {
            setBusy(button, true);
            setMsg('uplinkMsg', enabled ? 'Handing the Wi-Fi settings to the board…' : 'Switching the event Wi-Fi off…');
            try {
                await post('/api/settings/mgmt/uplink', {
                    enabled, ssid: $('uplinkSsid').value, psk: $('uplinkPsk').value,
                });
                $('uplinkPsk').value = '';
                setMsg('uplinkMsg', enabled
                    ? 'The board is connecting. The address appears above once it has one, usually within half a minute.'
                    : 'Event Wi-Fi switched off.', 'ok');
            } catch (e) {
                fail('uplinkMsg', e);
            } finally {
                setBusy(button, false);
                refresh();
            }
        };
        uplinkForm.addEventListener('submit', event => {
            event.preventDefault();
            save(true, uplinkForm.querySelector('[data-action="uplink-on"]'));
        });
        uplinkForm.querySelector('[data-action="uplink-off"]').addEventListener('click', event => {
            save(false, event.currentTarget);
        });
    }

    // ---------- polling ----------
    // Every 5 s while the page is visible: the dashboard unloads this iframe
    // when another view is opened, so nothing polls in the background.

    let timer = null;
    function start() {
        refresh();
        if (!timer) timer = setInterval(refresh, 5000);
    }
    function stop() {
        clearInterval(timer);
        timer = null;
    }
    document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
    start();
})();
