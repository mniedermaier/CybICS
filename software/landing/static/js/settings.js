// Settings view (templates/settings.html): section navigation, the AI
// assistant and the system section. The CybICS-mgmt section is in mgmt.js
// and uses the helpers exported at the bottom.
//
// The page runs in the dashboard's iframe. It tells the dashboard which
// section is open (so #settings:<section> can be linked and restored) and
// when the chat button is switched; it works on its own as well.
(function () {
    'use strict';

    const SECTIONS = ['mgmt', 'assistant', 'system'];
    const loaded = new Set();
    const loaders = {};
    const $ = id => document.getElementById(id);

    // ---------- helpers shared with mgmt.js ----------

    function el(tag, attrs, children) {
        const node = document.createElement(tag);
        Object.entries(attrs || {}).forEach(([key, value]) => {
            if (value === undefined || value === null || value === false) return;
            if (key === 'text') node.textContent = value;
            else if (key === 'class') node.className = value;
            else node.setAttribute(key, value === true ? '' : value);
        });
        (children || []).forEach(child => child && node.appendChild(child));
        return node;
    }

    // Show a result under the control that caused it. `details` (the raw
    // error) goes into a disclosure, so the sentence on top stays readable.
    function setMsg(id, text, kind, details) {
        const box = $(id);
        if (!box) return;
        box.className = 'msg' + (kind ? ' ' + kind : '');
        box.replaceChildren();
        if (!text) return;
        box.appendChild(document.createTextNode(text));
        if (details && details !== text) {
            box.appendChild(el('details', {}, [el('summary', {text: 'Details'}), el('span', {text: details})]));
        }
    }

    function setBusy(button, busy) {
        if (!button) return;
        button.disabled = busy;
        if (busy) button.setAttribute('aria-busy', 'true');
        else button.removeAttribute('aria-busy');
    }

    async function request(url, options) {
        const response = await fetch(url, Object.assign({cache: 'no-store'}, options || {}));
        let data = {};
        try { data = await response.json(); } catch (e) { /* not JSON */ }
        if (!response.ok || data.success === false) {
            const error = new Error(data.message || data.error || `Request failed (HTTP ${response.status})`);
            error.code = data.code;
            error.status = response.status;
            throw error;
        }
        return data;
    }

    function post(url, body) {
        return request(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body || {}),
        });
    }

    function tellDashboard(message) {
        if (window.parent !== window) window.parent.postMessage(message, window.location.origin);
    }

    // ---------- sections ----------

    function sectionFromHash() {
        const name = window.location.hash.slice(1);
        return SECTIONS.includes(name) ? name : SECTIONS[0];
    }

    function show(name, fromUser) {
        // Section ids are prefixed, so #mgmt never makes the browser jump to an anchor.
        SECTIONS.forEach(section => { $('section-' + section).hidden = section !== name; });
        document.querySelectorAll('.subnav-link').forEach(link => {
            if (link.dataset.section === name) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
        if (window.location.hash !== '#' + name) history.replaceState(null, '', '#' + name);
        tellDashboard({type: 'settings-section', section: name});
        if (!loaded.has(name) && loaders[name]) {
            loaded.add(name);
            loaders[name]();
        }
        if (fromUser) $('section-' + name).querySelector('h2').focus({preventScroll: true});
        window.scrollTo(0, 0);
    }

    document.querySelectorAll('.subnav-link').forEach(link => {
        link.addEventListener('click', event => {
            event.preventDefault();
            show(link.dataset.section, true);
        });
    });
    window.addEventListener('hashchange', () => show(sectionFromHash()));
    document.querySelectorAll('.section h2').forEach(h => h.setAttribute('tabindex', '-1'));

    // ---------- inline confirmations ----------
    // A destructive button opens a confirmation box next to it instead of a
    // native confirm(), so the consequences can be spelled out.

    function openConfirm(container) {
        container.querySelector('[data-action$="-ask"]').hidden = true;
        const box = container.querySelector('.confirm-box');
        box.hidden = false;
        // The confirming button may still be disabled while its details load.
        box.querySelector('button:not(:disabled)').focus();
        container.dispatchEvent(new CustomEvent('confirm-open'));
    }

    function closeConfirm(container) {
        const ask = container.querySelector('[data-action$="-ask"]');
        container.querySelector('.confirm-box').hidden = true;
        ask.hidden = false;
        ask.focus();
    }

    document.addEventListener('click', event => {
        const button = event.target.closest('[data-action]');
        if (!button) return;
        const container = button.closest('[data-confirm]');
        if (!container) return;
        if (button.dataset.action.endsWith('-ask')) openConfirm(container);
        else if (button.dataset.action === 'confirm-cancel') closeConfirm(container);
    });

    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        const box = event.target.closest && event.target.closest('.confirm-box');
        if (box && !box.hidden) closeConfirm(box.closest('[data-confirm]'));
    });

    // ---------- theme (same bridge as the other dashboard views) ----------

    function applyTheme(theme) {
        document.documentElement.classList.toggle('light-mode', theme === 'light');
    }
    fetch('/api/settings/theme').then(r => r.json()).then(d => applyTheme(d.theme || 'dark')).catch(() => {});
    window.addEventListener('message', event => {
        if (event.origin === window.location.origin && event.data && event.data.type === 'theme') {
            applyTheme(event.data.theme);
        }
    });

    // ---------- AI assistant ----------

    const agentSwitch = $('agentSwitch');

    async function loadAgentSwitch() {
        try {
            const data = await request('/api/settings/agent');
            agentSwitch.setAttribute('aria-checked', String(data.enabled !== false));
        } catch (e) { /* keep the default */ }
    }

    agentSwitch.addEventListener('click', async () => {
        const enabled = agentSwitch.getAttribute('aria-checked') !== 'true';
        agentSwitch.disabled = true;
        try {
            await post('/api/settings/agent', {enabled});
            agentSwitch.setAttribute('aria-checked', String(enabled));
            tellDashboard({type: 'agent-enabled', enabled});
            setMsg('modelMsg', '');
        } catch (e) {
            setMsg('modelMsg', 'The setting could not be saved.', 'error', e.message);
        } finally {
            agentSwitch.disabled = false;
            agentSwitch.focus();
        }
    });

    let models = null;

    function renderModels() {
        const list = $('modelList');
        list.querySelectorAll('.model').forEach(node => node.remove());
        const available = new Set(models.available_models || []);
        (models.recommended_models || []).forEach(model => {
            const id = 'model-' + model.name.replace(/[^a-z0-9]+/gi, '-');
            const quality = Math.max(0, Math.min(5, parseInt(model.quality, 10) || 0));
            const badges = [];
            if (model.recommended) badges.push(el('span', {class: 'badge accent', text: 'Recommended'}));
            badges.push(available.has(model.name)
                ? el('span', {class: 'badge ok', text: 'On this instance'})
                : el('span', {class: 'badge', text: 'Download ' + (model.size || '')}));
            const input = el('input', {type: 'radio', name: 'model', id, value: model.name,
                                       checked: model.name === models.current_model});
            list.appendChild(el('label', {class: 'model', for: id}, [
                input,
                el('span', {}, [
                    el('span', {class: 'model-name', text: model.name}),
                    el('span', {class: 'sr-only', text: `, ${model.size}, quality ${quality} of 5`}),
                ]),
                el('span', {class: 'badges'}, badges),
                el('span', {class: 'model-desc', text:
                    `${model.description || ''}${model.description ? ' · ' : ''}${model.size || ''} · quality ${'●'.repeat(quality)}${'○'.repeat(5 - quality)}`}),
            ]));
        });
    }

    async function loadModels() {
        $('modelLoading').hidden = false;
        try {
            models = await request('/api/agent/model');
            renderModels();
            $('modelList').hidden = false;
            $('modelUnavailable').hidden = true;
        } catch (e) {
            $('modelList').hidden = true;
            $('modelUnavailable').hidden = false;
        } finally {
            $('modelLoading').hidden = true;
        }
    }

    function setModelsDisabled(disabled) {
        $('modelList').querySelectorAll('input').forEach(input => { input.disabled = disabled; });
        $('modelList').setAttribute('aria-busy', String(disabled));
    }

    async function waitForModel(name) {
        // A download can outlast the POST (and the proxy's patience); the
        // model list tells when it is there and active.
        const until = Date.now() + 35 * 60 * 1000;
        while (Date.now() < until) {
            await new Promise(resolve => setTimeout(resolve, 5000));
            try {
                const data = await request('/api/agent/model');
                if (data.current_model === name && (data.available_models || []).includes(name)) {
                    models = data;
                    return true;
                }
            } catch (e) { /* the agent may be busy; keep waiting */ }
        }
        return false;
    }

    $('modelList').addEventListener('change', async event => {
        const name = event.target.value;
        if (!models || name === models.current_model) return;
        const info = (models.recommended_models || []).find(m => m.name === name) || {};
        const download = !(models.available_models || []).includes(name);
        setModelsDisabled(true);
        setMsg('modelMsg', download
            ? `Downloading ${name} (${info.size || 'unknown size'}). This can take several minutes; you can leave this page.`
            : `Switching to ${name}…`);
        let ok = false;
        try {
            // The agent answers once the model is pulled and active, so this
            // can take minutes. Only a proxy timeout leaves it unfinished.
            await post('/api/agent/model', {model: name});
            models = await request('/api/agent/model');
            ok = true;
        } catch (e) {
            if (e.status === 504) ok = await waitForModel(name);
            else setMsg('modelMsg', `Could not switch to ${name}.`, 'error', e.message);
        }
        if (ok) {
            setMsg('modelMsg', `The assistant now uses ${name}.`, 'ok');
            tellDashboard({type: 'agent-model-changed', model: name});
        } else if (!$('modelMsg').classList.contains('error')) {
            setMsg('modelMsg', `${name} is not active yet. Check again later.`, 'error');
        }
        renderModels();
        setModelsDisabled(false);
    });

    loaders.assistant = () => { loadAgentSwitch(); loadModels(); };

    // ---------- system ----------

    async function loadSystem() {
        const facts = $('systemFacts');
        const rows = [];
        try {
            const d = await request('/api/settings/system/info');
            const board = d.hardware || {};
            rows.push(['Platform', document.body.dataset.platform === 'physical' ? 'CybICS board' : 'Virtual (Docker)']);
            if (document.body.dataset.platform === 'physical') {
                rows.push(['Board revision', board.detected
                    ? board.revision + (board.straps_present ? '' : ' (straps not fitted)')
                    : (board.description || 'unknown')]);
            }
            rows.push(['Running containers', String(d.running_containers)]);
            rows.push(['Docker', d.docker_version]);
            rows.push(['Docker Compose', d.compose_version]);
            rows.push(['Python', d.python_version]);
            rows.push(['Operating system', d.platform]);
        } catch (e) {
            rows.push(['Error', 'The system information is not available: ' + e.message]);
        }
        facts.replaceChildren(...rows.filter(([, value]) => value).flatMap(([label, value]) => [
            el('dt', {text: label}), el('dd', {text: value}),
        ]));
        facts.setAttribute('aria-busy', 'false');
    }

    document.querySelector('[data-action="logs"]').addEventListener('click', async event => {
        event.preventDefault();
        const link = event.currentTarget;
        if (link.getAttribute('aria-busy') === 'true') return;
        link.setAttribute('aria-busy', 'true');
        link.setAttribute('aria-disabled', 'true');
        setMsg('logsMsg', 'Collecting the logs. This takes a few seconds…');
        try {
            const response = await fetch(link.href, {cache: 'no-store'});
            if (!response.ok) {
                let message = `HTTP ${response.status}`;
                try { message = (await response.json()).error || message; } catch (e) { /* not JSON */ }
                throw new Error(message);
            }
            const name = (/filename="?([^";]+)"?/.exec(response.headers.get('Content-Disposition') || '') || [])[1]
                || 'cybics_logs.txt';
            const url = URL.createObjectURL(await response.blob());
            const a = el('a', {href: url, download: name});
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => URL.revokeObjectURL(url), 10000);
            setMsg('logsMsg', `Downloaded ${name}.`, 'ok');
        } catch (e) {
            setMsg('logsMsg', 'The logs could not be collected.', 'error', e.message);
        } finally {
            link.removeAttribute('aria-busy');
            link.removeAttribute('aria-disabled');
        }
    });

    const restartBox = document.querySelector('[data-confirm="restart"]');
    const restartNow = restartBox.querySelector('[data-action="restart"]');

    restartBox.addEventListener('confirm-open', async () => {
        restartNow.disabled = true;
        $('restartPlan').textContent = 'Checking which containers would restart…';
        try {
            const plan = await request('/api/settings/containers/restart?plan=1');
            if (plan.error) throw new Error(plan.error);
            if (plan.running) throw new Error('A restart is already in progress.');
            $('restartPlan').replaceChildren(
                document.createTextNode(`These ${plan.containers.length} containers of “${plan.project}” restart, this page last:`),
                el('ul', {}, plan.containers.map(name => el('li', {text: name}))));
            restartNow.disabled = false;
        } catch (e) {
            $('restartPlan').textContent = 'Nothing can be restarted from here: ' + e.message;
        }
    });

    restartNow.addEventListener('click', async () => {
        setBusy(restartNow, true);
        restartBox.querySelector('[data-action="confirm-cancel"]').disabled = true;
        let data;
        try {
            data = await post('/api/settings/containers/restart');
        } catch (e) {
            setBusy(restartNow, false);
            restartBox.querySelector('[data-action="confirm-cancel"]').disabled = false;
            setMsg('restartMsg', 'The restart did not start.', 'error', e.message);
            return;
        }
        setMsg('restartMsg', `Restarting ${data.containers.length} services. The dashboard reloads when the lab is back, in about a minute.`);
        // landing goes down for less than the poll interval, so wait for a
        // new process (boot ID) rather than for an outage.
        const started = Date.now();
        const poll = async () => {
            if (Date.now() - started > 5 * 60 * 1000) {
                setBusy(restartNow, false);
                restartBox.querySelector('[data-action="confirm-cancel"]').disabled = false;
                setMsg('restartMsg', 'The lab did not come back within 5 minutes. Check ./cybics.sh status on the host.', 'error');
                return;
            }
            try {
                const status = await request('/api/settings/containers/restart',
                                             {signal: AbortSignal.timeout(5000)});
                if (status.boot_id && status.boot_id !== data.boot_id) {
                    // The sandboxed iframe may not navigate the dashboard itself.
                    if (window.parent !== window) tellDashboard({type: 'reload'});
                    else window.location.reload();
                    return;
                }
            } catch (e) { /* landing is restarting */ }
            setTimeout(poll, 2000);
        };
        setTimeout(poll, 2000);
    });

    loaders.system = loadSystem;

    // ---------- start ----------

    window.cybicsSettings = {el, setMsg, setBusy, request, post, tellDashboard};
    document.addEventListener('DOMContentLoaded', () => show(sectionFromHash()));
})();
