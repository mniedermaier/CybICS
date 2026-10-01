// Settings -> Central CTF Server (templates/settings.html, #event).
//
// Optional: until the user joins an event, the landing page makes no network
// calls to any CTF server. Every string from the server is inserted as text,
// never as HTML.
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

    // The client's transport errors, in words a participant can act on. The
    // server's own messages are written for end users and shown as they are.
    function explain(error) {
        if (error.code === 'unreachable') {
            return physical
                ? 'Cannot reach the server. Check the address, and that the event Wi-Fi is connected.'
                : 'Cannot reach the server. Check the address, and that this computer is on the event network.';
        }
        if (error.code === 'bad_response') {
            return 'Something answered at that address, but not a CybICS CTF server. Check the address and port.';
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

    let newsKey = '';

    function renderStatus(snap) {
        const card = $('eventStatus');
        const event = snap.event || {};
        const standing = snap.standing || {};
        const state = event.state || 'unknown';
        setField(card, 'event', event.name || event.slug || 'Event');
        setField(card, 'team', (snap.team || {}).name || '–');
        const pill = card.querySelector('[data-field="state"]');
        setField(card, 'state', STATE_LABELS[state] || state);
        pill.className = 'state-pill ' + state;
        setField(card, 'score', standing.rank ? String(standing.score) : '–');
        setField(card, 'rank', standing.rank ? `${standing.rank} / ${standing.teams}` : '–');
        setField(card, 'pending', String(snap.pending || 0));
        setField(card, 'server', snap.server_url || '–');
        setField(card, 'contact', ago(snap.last_contact));
        const error = snap.last_error;
        setRow(card, 'error', !!error);
        if (error) setField(card, 'error', explain(error));

        const news = (snap.announcements || []).slice().reverse();
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
        const pill = $('eventNavPill');
        if (!snap.enabled) {
            pill.hidden = true;
            return;
        }
        const state = (snap.event || {}).state;
        const rank = (snap.standing || {}).rank;
        const trouble = !!snap.last_error;
        pill.hidden = false;
        pill.className = 'nav-pill ' + (trouble ? 'warn' : (state === 'running' ? 'running' : ''));
        pill.textContent = trouble ? 'Problem' : (rank ? `#${rank}` : (STATE_LABELS[state] || 'Joined'));
    }

    function render(snap) {
        const flow = $('eventFlow');
        $('eventLoading').hidden = true;
        flow.setAttribute('aria-busy', 'false');
        flow.classList.toggle('is-enrolled', !!snap.enabled);
        $('eventStatus').hidden = !snap.enabled;
        $('serverCard').hidden = !!snap.enabled;
        $('teamCard').hidden = !!snap.enabled;
        if (snap.enabled) {
            renderStatus(snap);
        } else {
            $('revokedNote').hidden = !snap.revoked;
            prefill($('serverUrl'), snap.server_url);
            prefill($('teamName'), (snap.team || {}).name);
        }
        renderUplink(snap);
        renderNavPill(snap);
    }

    async function refresh() {
        try {
            render(await request('/api/settings/central'));
        } catch (e) {
            // The landing page itself is unreachable; the next poll tries again.
        }
    }

    // ---------- actions ----------

    $('serverForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = event.submitter || $('serverForm').querySelector('[data-action="test"]');
        const server_url = $('serverUrl').value.trim();
        if (!server_url) {
            setMsg('serverMsg', 'Enter the server address the organiser gave you.', 'error');
            $('serverUrl').focus();
            return;
        }
        setBusy(button, true);
        setMsg('serverMsg', 'Contacting the server…');
        try {
            const info = (await post('/api/settings/central/test', {server_url})).info || {};
            setMsg('serverMsg', `Reached ${info.name || 'the CTF server'}${info.version ? ' ' + info.version : ''}. Continue with your team below.`, 'ok');
        } catch (e) {
            fail('serverMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    $('joinForm').addEventListener('submit', async event => {
        event.preventDefault();
        const button = $('joinForm').querySelector('[data-action="join"]');
        const body = {
            server_url: $('serverUrl').value.trim(),
            join_code: $('joinCode').value.trim(),
            team_name: $('teamName').value.trim(),
            team_password: $('teamPassword').value,
        };
        if (!body.server_url) {
            setMsg('serverMsg', 'Enter the server address first.', 'error');
            $('serverUrl').focus();
            return;
        }
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
            const snap = (await post('/api/settings/central/enroll', body)).snapshot || {};
            $('teamPassword').value = '';
            $('joinCode').value = '';
            setMsg('joinMsg', '');
            render(snap);
            setMsg('statusMsg', `Joined ${(snap.event || {}).name || 'the event'} as ${(snap.team || {}).name || 'your team'}.`, 'ok');
            $('eventStatus').querySelector('[data-field="event"]').setAttribute('tabindex', '-1');
            $('eventStatus').querySelector('[data-field="event"]').focus();
        } catch (e) {
            fail('joinMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    document.querySelector('[data-action="leave"]').addEventListener('click', async event => {
        const button = event.currentTarget;
        setBusy(button, true);
        try {
            const snap = (await post('/api/settings/central/leave')).snapshot || {};
            const box = document.querySelector('[data-confirm="leave"]');
            box.querySelector('.confirm-box').hidden = true;
            box.querySelector('[data-action="leave-ask"]').hidden = false;
            setMsg('statusMsg', '');
            render(snap);
            setMsg('joinMsg', 'Left the event. Solves made from now on stay local.', 'ok');
            $('serverUrl').focus();
        } catch (e) {
            fail('statusMsg', e);
        } finally {
            setBusy(button, false);
        }
    });

    const uplinkForm = $('uplinkForm');
    if (uplinkForm) {
        const save = async (enabled, button) => {
            setBusy(button, true);
            setMsg('uplinkMsg', enabled ? 'Handing the Wi-Fi settings to the board…' : 'Switching the event Wi-Fi off…');
            try {
                await post('/api/settings/central/uplink', {
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
