/* Interactive widgets for the Theory Path. Each one fills a
   <div data-widget="name"> placeholder in an article; the catalogue and the
   attributes are in training/theory/AUTHORING.md. Only plant-live talks to
   the stack. Every other widget is a self-contained model, so it works on a
   laptop with nothing running. */
(function () {
    'use strict';
    const { register, util } = window.TheoryWidgets;
    const { el, escapeHtml, inline } = util;
    const CHALLENGES = window.TheoryWidgets.challenges || {};

    function frame(node, title, note) {
        const box = el('div', { class: 'w', role: 'region', 'aria-label': title });
        box.appendChild(el('div', { class: 'w-head' }, `<span class="w-title">${escapeHtml(title)}</span>`));
        const body = el('div', { class: 'w-body' });
        if (note) body.appendChild(el('p', { class: 'w-note' }, note));
        box.appendChild(body);
        node.replaceWith(box);
        return { box, body, head: box.firstChild };
    }
    const hex = (n, width) => n.toString(16).toUpperCase().padStart(width, '0');
    const u16 = n => [(n >> 8) & 0xff, n & 0xff];
    const clampInt = (v, lo, hi, fallback) => {
        const n = parseInt(v, 10);
        return Number.isFinite(n) ? Math.min(hi, Math.max(lo, n)) : fallback;
    };

    // Shared by the Modbus and S7 widgets: a strip of byte groups, each of
    // which explains itself when clicked or focused.
    function byteStrip(groups, explain) {
        const strip = el('div', { class: 'bytes', role: 'list' });
        groups.forEach(function (g, i) {
            const b = el('button', { class: `byte-group c${g.colour ?? i % 6}`, type: 'button', role: 'listitem',
                'aria-label': `${g.label}: ${g.bytes.map(x => hex(x, 2)).join(' ')}` });
            b.innerHTML = `<span class="hex">${g.bytes.map(x => hex(x, 2)).join(' ')}</span><span class="lbl">${escapeHtml(g.label)}</span>`;
            const show = function () {
                strip.querySelectorAll('.byte-group').forEach(x => x.classList.remove('active'));
                b.classList.add('active');
                explain.innerHTML = `<b>${escapeHtml(g.label)}</b> &mdash; ${inline(g.help)}`;
            };
            b.addEventListener('click', show);
            b.addEventListener('focus', show);
            strip.appendChild(b);
        });
        return strip;
    }

    // ------------------------------------------------------------------
    // plant-live: what the PLC holds right now
    // ------------------------------------------------------------------
    const PLANT_FIELDS = {
        gst: { name: 'Gas storage tank (GST)', src: 'holding register 1124', unit: 'bar', max: 255 },
        hpt: { name: 'High-pressure tank (HPT)', src: 'holding register 1126', unit: 'bar', max: 255 },
        compressor: { name: 'Compressor', src: 'coil 1', bool: ['running', 'off'] },
        systemValve: { name: 'System valve', src: 'coil 2', bool: ['open', 'closed'] },
        gstSig: { name: 'GST refill', src: 'coil 3', bool: ['filling', 'idle'] },
        heartbeat: { name: 'PLC heartbeat', src: 'coil 0', bool: ['on', 'off'] },
        sysSen: { name: 'System sensor', src: 'holding register 1132', bool: ['1', '0'] },
        boSen: { name: 'Blow-out sensor', src: 'holding register 1134', bool: ['1', '0'] },
    };
    register('plant-live', function (node) {
        const fields = (node.dataset.fields || Object.keys(PLANT_FIELDS).join(','))
            .split(',').map(s => s.trim()).filter(f => PLANT_FIELDS[f]);
        const { body, head } = frame(node, 'Live: the plant as the PLC sees it',
            'These are the values the PLC holds right now, read over Modbus once a second. Start a challenge in another tab and watch them change.');
        const status = el('span', { class: 'w-note', 'aria-live': 'polite' }, '<span class="live-dot"></span>connecting…');
        head.appendChild(status);
        const grid = el('div', { class: 'plant' });
        const history = {};
        const cells = {};
        fields.forEach(function (f) {
            const meta = PLANT_FIELDS[f];
            const cell = el('div', { class: 'gauge' },
                `<div class="name">${meta.name}</div><div class="val">–</div><div class="src">${meta.src}</div>` +
                (meta.bool ? '' : '<div class="meter"><div style="width:0"></div></div><svg class="spark" viewBox="0 0 60 28" preserveAspectRatio="none" aria-hidden="true"><polyline fill="none" stroke="currentColor" stroke-width="1.5" points=""/></svg>'));
            cells[f] = cell; history[f] = [];
            grid.appendChild(cell);
        });
        body.appendChild(grid);
        let timer = null;
        function paint(values) {
            fields.forEach(function (f) {
                const meta = PLANT_FIELDS[f], cell = cells[f], v = values[f];
                const val = cell.querySelector('.val');
                if (meta.bool) {
                    const on = Boolean(v);
                    val.innerHTML = `<span class="w-pill ${on ? 'on' : 'off'}">${on ? meta.bool[0] : meta.bool[1]}</span>`;
                    return;
                }
                val.textContent = `${v} ${meta.unit}`;
                cell.querySelector('.meter > div').style.width = Math.min(100, v / meta.max * 100) + '%';
                const h = history[f]; h.push(v); if (h.length > 60) h.shift();
                const points = h.map((x, i) => `${i},${(28 - x / meta.max * 26 - 1).toFixed(1)}`).join(' ');
                cell.querySelector('polyline').setAttribute('points', points);
            });
        }
        function poll() {
            if (document.hidden) return;
            fetch('/theory/api/plant').then(r => r.json()).then(function (data) {
                if (!data.ok) throw new Error('offline');
                paint(data.values);
                status.innerHTML = '<span class="live-dot on"></span>live';
            }).catch(function () {
                status.innerHTML = '<span class="live-dot"></span>plant not reachable &ndash; is the stack running?';
            });
        }
        poll();
        timer = setInterval(poll, 1000);
        window.addEventListener('pagehide', () => clearInterval(timer));
    });

    // ------------------------------------------------------------------
    // modbus-frame: build a request, or take one apart
    // ------------------------------------------------------------------
    const FUNCTION_CODES = {
        1: { name: 'Read Coils', kind: 'read', table: 'coils' },
        3: { name: 'Read Holding Registers', kind: 'read', table: 'holding registers' },
        5: { name: 'Write Single Coil', kind: 'coil' },
        6: { name: 'Write Single Register', kind: 'register' },
        16: { name: 'Write Multiple Registers', kind: 'multi' },
    };
    function modbusGroups(f) {
        const fc = FUNCTION_CODES[f.fc];
        let pdu;
        if (fc.kind === 'read') {
            pdu = [
                { label: 'Function code', bytes: [f.fc], help: `\`${hex(f.fc, 2)}\` = ${fc.name}. The function code tells the PLC *what* to do. Codes 01-04 read, 05, 06, 15 and 16 write.` },
                { label: 'Start address', bytes: u16(f.address), help: `The first of the ${fc.table} to read: ${f.address} (\`0x${hex(f.address, 4)}\`). Addresses on the wire start at 0.` },
                { label: 'Quantity', bytes: u16(f.count), help: `How many ${fc.table} to read: ${f.count}.` },
            ];
        } else if (fc.kind === 'coil') {
            pdu = [
                { label: 'Function code', bytes: [f.fc], help: `\`05\` = ${fc.name}: switch one coil (an on/off output) on or off.` },
                { label: 'Coil address', bytes: u16(f.address), help: `Which coil: ${f.address}. On CybICS coil 1 is the compressor.` },
                { label: 'Value', bytes: f.value ? [0xff, 0x00] : [0x00, 0x00], help: 'Modbus spells "on" as `FF 00` and "off" as `00 00`. Any other value is invalid.' },
            ];
        } else if (fc.kind === 'register') {
            pdu = [
                { label: 'Function code', bytes: [f.fc], help: `\`06\` = ${fc.name}: overwrite one 16-bit register.` },
                { label: 'Register address', bytes: u16(f.address), help: `Which register: ${f.address} (\`0x${hex(f.address, 4)}\`). On CybICS 1126 holds the HPT pressure.` },
                { label: 'Value', bytes: u16(f.value), help: `The new value: ${f.value} (\`0x${hex(f.value, 4)}\`). Nothing checks who sent it.` },
            ];
        } else {
            const values = f.values.length ? f.values : [f.value];
            pdu = [
                { label: 'Function code', bytes: [f.fc], help: `\`10\` (16) = ${fc.name}: overwrite several registers in one go.` },
                { label: 'Start address', bytes: u16(f.address), help: `The first register to write: ${f.address}.` },
                { label: 'Quantity', bytes: u16(values.length), help: `How many registers follow: ${values.length}.` },
                { label: 'Byte count', bytes: [values.length * 2], help: `How many data bytes follow: two per register, so ${values.length * 2}.` },
                { label: 'Values', bytes: values.flatMap(u16), help: `The register values, two bytes each, high byte first: ${values.join(', ')}.` },
            ];
        }
        const pduLen = pdu.reduce((n, g) => n + g.bytes.length, 0);
        return [
            { label: 'Transaction ID', bytes: u16(f.tid), help: 'Chosen by the client so it can match the reply to the request. The PLC copies it into its answer.', colour: 0 },
            { label: 'Protocol ID', bytes: [0, 0], help: 'Always `00 00` for Modbus. Anything else is not a Modbus frame.', colour: 0 },
            { label: 'Length', bytes: u16(pduLen + 1), help: `How many bytes follow this field: the unit ID plus the ${pduLen}-byte PDU = ${pduLen + 1}.`, colour: 0 },
            { label: 'Unit ID', bytes: [f.unit], help: 'Which device behind a gateway is meant. A PLC reached directly over TCP usually ignores it; CybICS uses 1.', colour: 0 },
            ...pdu.map(g => ({ ...g, colour: 3 })),
        ];
    }
    function parseModbus(text) {
        const clean = text.replace(/0x/gi, '').replace(/[^0-9a-f]/gi, '');
        if (clean.length % 2) throw new Error('An odd number of hex digits: every byte is two digits.');
        const b = clean.match(/../g)?.map(h => parseInt(h, 16)) || [];
        if (b.length < 8) throw new Error(`Only ${b.length} bytes. A Modbus TCP request has at least 8 (7 header bytes and a function code).`);
        const word = i => (b[i] << 8) | b[i + 1];
        if (word(2) !== 0) throw new Error(`Protocol ID is ${hex(word(2), 4)}, not 0000, so this is not Modbus.`);
        if (word(4) !== b.length - 6) throw new Error(`The length field says ${word(4)} bytes follow, but ${b.length - 6} do.`);
        const f = { tid: word(0), unit: b[6], fc: b[7], address: 0, count: 1, value: 0, values: [] };
        if (!FUNCTION_CODES[f.fc]) throw new Error(`Function code ${hex(f.fc, 2)} is valid Modbus, but this example only explains 01, 03, 05, 06 and 10.`);
        if (b.length < 12) throw new Error('The PDU is too short for this function code.');
        f.address = word(8);
        const kind = FUNCTION_CODES[f.fc].kind;
        if (kind === 'read') f.count = word(10);
        if (kind === 'coil') {
            if (word(10) !== 0xff00 && word(10) !== 0) throw new Error('A coil value must be FF00 (on) or 0000 (off).');
            f.value = word(10) === 0xff00 ? 1 : 0;
        }
        if (kind === 'register') f.value = word(10);
        if (kind === 'multi') {
            const n = word(10);
            if (b[12] !== n * 2 || b.length !== 13 + n * 2) throw new Error('The byte count does not match the number of registers.');
            for (let i = 0; i < n; i++) f.values.push(word(13 + i * 2));
            f.value = f.values[0];
        }
        return f;
    }
    register('modbus-frame', function (node) {
        const d = node.dataset;
        const f = {
            tid: 1, unit: 1, count: 2, values: [],
            fc: FUNCTION_CODES[d.fc] ? Number(d.fc) : 6,
            address: clampInt(d.address, 0, 65535, 1126),
            value: clampInt(d.value, 0, 65535, 90),
        };
        const { body } = frame(node, 'Modbus frame builder',
            'Change the fields and watch the bytes, or paste bytes from Wireshark and see what they mean. Click any byte group for an explanation.');
        const form = el('div', { class: 'w-row' });
        form.innerHTML = `
            <label>Function <select data-k="fc">${Object.entries(FUNCTION_CODES).map(([k, v]) => `<option value="${k}">${hex(Number(k), 2)} ${v.name}</option>`).join('')}</select></label>
            <label>Address <input type="number" min="0" max="65535" data-k="address"></label>
            <label data-show="value">Value <input type="number" min="0" max="65535" data-k="value"></label>
            <label data-show="count">Quantity <input type="number" min="1" max="125" data-k="count"></label>
            <label>Transaction <input type="number" min="0" max="65535" data-k="tid"></label>`;
        body.appendChild(form);
        const strip = el('div');
        const explain = el('div', { class: 'explain', 'aria-live': 'polite' }, 'Click a byte group to see what it means.');
        const hexOut = el('textarea', { rows: '2', 'aria-label': 'The frame as hex. Edit or paste bytes here.', spellcheck: 'false' });
        const err = el('div', { class: 'w-err', 'aria-live': 'polite' });
        const summary = el('p', { class: 'w-note' });
        body.append(strip, explain, el('label', {}, 'The whole frame as hex &ndash; edit it or paste your own:'), hexOut, err, summary);
        function sync(fromHex) {
            const fc = FUNCTION_CODES[f.fc];
            form.querySelector('[data-show=value]').style.display = fc.kind === 'read' ? 'none' : '';
            form.querySelector('[data-show=count]').style.display = fc.kind === 'read' ? '' : 'none';
            form.querySelectorAll('[data-k]').forEach(function (input) {
                if (document.activeElement !== input) input.value = f[input.dataset.k];
            });
            if (fc.kind === 'coil') form.querySelector('[data-k=value]').max = 1;
            const groups = modbusGroups(f);
            strip.replaceChildren(byteStrip(groups, explain));
            if (!fromHex) hexOut.value = groups.flatMap(g => g.bytes).map(x => hex(x, 2)).join(' ');
            const what = fc.kind === 'read' ? `read ${f.count} ${fc.table} starting at ${f.address}`
                : fc.kind === 'coil' ? `switch coil ${f.address} ${f.value ? 'on' : 'off'}`
                : fc.kind === 'register' ? `set register ${f.address} to ${f.value}`
                : `write ${(f.values.length || 1)} register(s) starting at ${f.address}`;
            summary.innerHTML = `In words: <b>“Unit ${f.unit}, please ${escapeHtml(what)}.”</b> Note what is missing: no user, no password, no signature.`;
        }
        form.addEventListener('input', function (e) {
            const k = e.target.dataset.k;
            if (!k) return;
            const limits = { fc: [1, 16], address: [0, 65535], value: [0, f.fc === 5 ? 1 : 65535], count: [1, 125], tid: [0, 65535] };
            f[k] = clampInt(e.target.value, limits[k][0], limits[k][1], f[k]);
            if (k === 'fc') { f.values = []; if (f.fc === 5) f.value = f.value ? 1 : 0; }
            if (k === 'value') f.values = [];
            err.textContent = '';
            sync(false);
        });
        hexOut.addEventListener('input', function () {
            try {
                Object.assign(f, parseModbus(hexOut.value));
                err.textContent = '';
                sync(true);
            } catch (e) {
                err.textContent = e.message;
                summary.textContent = '';
                strip.replaceChildren();
            }
        });
        sync(false);
    });

    // ------------------------------------------------------------------
    // s7-layers: one S7comm request, layer by layer
    // ------------------------------------------------------------------
    const S7_SAMPLES = {
        setup: {
            title: 'Setup Communication (the first S7 message of every session)',
            layers: [
                { name: 'TPKT', what: 'Packet framing over TCP (RFC 1006)', fields: [
                    ['03', 'Version', 'Always 3.'], ['00', 'Reserved', ''],
                    ['00 19', 'Length', 'The whole packet is 25 bytes, TPKT header included.']] },
                { name: 'COTP', what: 'ISO transport layer: "this is data"', fields: [
                    ['02', 'Length', '2 more header bytes follow.'], ['F0', 'PDU type', 'DT = data transfer. (The earlier connect request had type E0.)'],
                    ['80', 'Last unit', 'This is the last (and only) fragment.']] },
                { name: 'S7 header', what: 'Siemens S7comm: who asks, and how long the parts are', fields: [
                    ['32', 'Protocol ID', 'Always 0x32 for S7comm. This is how Wireshark and the IDS recognise it.'],
                    ['01', 'Message type', 'Job: a request from the client.'], ['00 00', 'Reserved', ''],
                    ['00 00', 'PDU reference', 'Chosen by the client to match the reply.'],
                    ['00 08', 'Parameter length', '8 bytes of parameters follow.'], ['00 00', 'Data length', 'No data part.']] },
                { name: 'Parameters', what: 'The actual request', fields: [
                    ['F0', 'Function', 'Setup Communication: agree on limits before anything else.'], ['00', 'Reserved', ''],
                    ['00 01', 'Max parallel jobs (calling)', 'How many requests the client may have open at once.'],
                    ['00 01', 'Max parallel jobs (called)', 'The same for the PLC.'],
                    ['01 E0', 'PDU length', 'The largest message either side may send: 480 bytes.']] },
            ],
        },
        szl: {
            title: 'Read SZL 0x0011 (module identification, what nmap\'s s7-info asks for)',
            layers: [
                { name: 'TPKT', what: 'Packet framing over TCP (RFC 1006)', fields: [
                    ['03', 'Version', 'Always 3.'], ['00', 'Reserved', ''], ['00 21', 'Length', '33 bytes in total.']] },
                { name: 'COTP', what: 'ISO transport layer: "this is data"', fields: [
                    ['02', 'Length', ''], ['F0', 'PDU type', 'DT = data transfer.'], ['80', 'Last unit', '']] },
                { name: 'S7 header', what: 'Siemens S7comm', fields: [
                    ['32', 'Protocol ID', 'S7comm.'], ['07', 'Message type', 'Userdata: the "extra" functions such as diagnostics and identification.'],
                    ['00 00', 'Reserved', ''], ['00 01', 'PDU reference', ''],
                    ['00 08', 'Parameter length', ''], ['00 08', 'Data length', '']] },
                { name: 'Parameters', what: 'Which userdata function', fields: [
                    ['00 01 12', 'Parameter head', 'Fixed start of a userdata parameter block.'], ['04', 'Parameter length', ''],
                    ['11', 'Method', 'Request.'], ['44', 'Type and group', '4 = request, group 4 = CPU functions.'],
                    ['01', 'Subfunction', 'Read SZL (the system status list: the PLC\'s self-description).'], ['00', 'Sequence', '']] },
                { name: 'Data', what: 'Which part of the SZL', fields: [
                    ['FF', 'Return code', 'FF = OK.'], ['09', 'Transport size', 'Octet string.'], ['00 04', 'Length', '4 bytes follow.'],
                    ['00 11', 'SZL ID', '0x0011 = module identification: order number and hardware version.'],
                    ['00 00', 'SZL index', 'All records.']] },
            ],
        },
    };
    register('s7-layers', function (node) {
        const sample = S7_SAMPLES[node.dataset.sample] || S7_SAMPLES.setup;
        const { body } = frame(node, 'S7comm, layer by layer', `${escapeHtml(sample.title)}. Open a layer to see its fields. S7comm rides inside two older protocols, like a letter in an envelope in a parcel.`);
        const allBytes = sample.layers.map(l => l.fields.map(f => f[0]).join(' ')).join(' ');
        body.appendChild(el('p', { class: 'mono w-note' }, `On the wire: ${allBytes}`));
        const layers = el('div', { class: 'layers' });
        sample.layers.forEach(function (layer, i) {
            const box = el('div', { class: 'layer' + (i === 2 ? ' open' : '') });
            const bytes = layer.fields.map(f => f[0]).join(' ');
            const btn = el('button', { type: 'button', 'aria-expanded': String(i === 2) },
                `<span><b>${escapeHtml(layer.name)}</b> &middot; ${escapeHtml(layer.what)}</span><span class="mono">${bytes}</span>`);
            btn.addEventListener('click', function () {
                const open = box.classList.toggle('open');
                btn.setAttribute('aria-expanded', String(open));
            });
            const fields = el('div', { class: 'fields' });
            fields.innerHTML = '<table>' + layer.fields.map(f =>
                `<tr><td>${f[0]}</td><td><b>${escapeHtml(f[1])}</b>${f[2] ? ' &ndash; ' + inline(f[2]) : ''}</td></tr>`).join('') + '</table>';
            box.append(btn, fields);
            layers.appendChild(box);
        });
        body.appendChild(layers);
    });

    // ------------------------------------------------------------------
    // register-decoder: 16-bit registers to bytes to text
    // ------------------------------------------------------------------
    register('register-decoder', function (node) {
        const initial = (node.dataset.values || '18533,27756,28416');
        const { body } = frame(node, 'Register decoder',
            'A register holds 16 bits: two bytes. Text is stored one character per byte, so each register carries two characters. Type register values, or type text to see how it would be stored.');
        const row = el('div', { class: 'w-row' });
        row.innerHTML = `<label style="flex:1;min-width:220px">Register values (decimal, comma separated)<br><input type="text" data-k="regs" style="width:100%"></label>
            <label>Text<br><input type="text" data-k="text" maxlength="32"></label>
            <label><input type="checkbox" data-k="swap"> swap bytes (low byte first)</label>`;
        const table = el('div', { style: 'overflow-x:auto' });
        const out = el('p', { 'aria-live': 'polite' });
        body.append(row, table, out);
        const regsIn = row.querySelector('[data-k=regs]'), textIn = row.querySelector('[data-k=text]'), swapIn = row.querySelector('[data-k=swap]');
        regsIn.value = initial;
        const printable = c => (c >= 32 && c < 127 ? String.fromCharCode(c) : null);
        function decode() {
            const regs = regsIn.value.split(/[\s,;]+/).filter(Boolean).map(Number);
            if (regs.some(r => !Number.isInteger(r) || r < 0 || r > 65535)) {
                out.innerHTML = '<span class="w-err">Every register is a whole number from 0 to 65535.</span>';
                table.innerHTML = ''; return;
            }
            let text = '';
            const rows = regs.map(function (r) {
                let bytes = u16(r); if (swapIn.checked) bytes = bytes.reverse();
                const chars = bytes.map(printable);
                chars.forEach(c => { text += c ?? ''; });
                return `<tr><td>${r}</td><td class="mono">0x${hex(r, 4)}</td><td class="mono">${bytes.map(b => hex(b, 2)).join(' ')}</td>` +
                    `<td class="mono">${chars.map(c => c === null ? '·' : escapeHtml(c === ' ' ? '␠' : c)).join(' ')}</td></tr>`;
            });
            table.innerHTML = `<table class="flows"><tr><th>Register</th><th>Hex</th><th>Bytes</th><th>Characters</th></tr>${rows.join('')}</table>`;
            out.innerHTML = `Reads as: <b class="mono">${escapeHtml(text) || '(nothing printable)'}</b>` +
                (regs.some(r => (r & 0xff) === 0 || r >> 8 === 0) ? ' <span class="w-note">(a 00 byte, shown as ·, pads the last register or ends the text)</span>' : '');
        }
        regsIn.addEventListener('input', () => { textIn.value = ''; decode(); });
        swapIn.addEventListener('change', decode);
        textIn.addEventListener('input', function () {
            const codes = [...textIn.value].map(c => c.charCodeAt(0) & 0xff);
            if (codes.length % 2) codes.push(0);
            const regs = [];
            for (let i = 0; i < codes.length; i += 2) {
                regs.push(swapIn.checked ? (codes[i + 1] << 8) | codes[i] : (codes[i] << 8) | codes[i + 1]);
            }
            regsIn.value = regs.join(',');
            decode();
        });
        decode();
    });

    // ------------------------------------------------------------------
    // purdue-explorer: the CybICS network on the Purdue levels
    // ------------------------------------------------------------------
    const PURDUE = [
        { level: 'Level 3', name: 'Operations', hint: 'Engineering, historians, site services', hosts: [
            { id: 'engineeringws', name: 'Engineering workstation', ip: '172.18.0.10', ports: '6080 (noVNC), 5901 (VNC)',
              role: 'The PC an engineer uses to program the PLC and look at the plant. Whoever controls it can change the PLC program.',
              attacks: ['plc_programming'], ids: 'Allowlisted as a known host.' },
            { id: 'cybicsagent', name: 'AI assistant', ip: '172.18.0.11', ports: '5000 (web), 11434 (Ollama)',
              role: 'The CybICS help assistant. Not part of a real plant, but it shows that every extra service on the network is one more thing to protect.',
              attacks: [], ids: 'Allowlisted as a known host.' },
        ] },
        { level: 'Level 2', name: 'Supervisory control', hint: 'HMI, SCADA, gateways', hosts: [
            { id: 'fuxa', name: 'FUXA HMI', ip: '172.18.0.4', ports: '1881 (web HMI)',
              role: 'The operators\' screen. It polls the PLC over Modbus and writes set points when an operator presses a button.',
              attacks: ['password_attack', 'mitm'], ids: 'Known Modbus writer: its writes are expected. Watched for HTTP login brute force.' },
            { id: 'opcua', name: 'OPC-UA server', ip: '172.18.0.5', ports: '4840 (OPC-UA)',
              role: 'A gateway that offers the plant values to other systems over OPC-UA, a modern protocol with built-in security options.',
              attacks: ['opcua'], ids: 'OPC-UA sessions from hosts that are not expected clients raise an alert.' },
        ] },
        { level: 'Level 1', name: 'Basic control', hint: 'PLCs and controllers', hosts: [
            { id: 'openplc', name: 'OpenPLC', ip: '172.18.0.3', ports: '502 (Modbus), 8080 (web), 102 (S7), 20000 (DNP3), 44818 (EtherNet/IP)',
              role: 'The PLC: it runs the control program every 50 ms, reads the sensors and switches the compressor and valves.',
              attacks: ['flood_overwrite', 'fuzzingMB', 'password_openplc', 'scanning'], ids: 'Modbus write floods, unauthorised writes and diagnostic function codes raise alerts.' },
            { id: 's7com', name: 'S7 server', ip: '172.18.0.6', ports: '1102 (S7comm)',
              role: 'Plays a Siemens S7 PLC, so you can practise S7comm enumeration.',
              attacks: ['scanning2'], ids: 'Every S7comm access raises an enumeration alert.' },
        ] },
        { level: 'Level 0', name: 'Physical process', hint: 'Sensors, actuators, the plant itself', hosts: [
            { id: 'hwio', name: 'Plant simulation (hwio)', ip: '172.18.0.2', ports: '8090 (3D view)',
              role: 'Simulates the tanks, the compressor and the valves, and writes the sensor values into the PLC about 50 times a second.',
              attacks: ['physical_process'], ids: 'Known Modbus writer.' },
            { id: 'stm32', name: 'STM32 (on the board)', ip: '172.18.0.7', ports: 'UART, I²C',
              role: 'On the real board, the microcontroller that runs the physical model and drives the LEDs and the display.',
              attacks: ['uart_basic'], ids: 'Allowlisted as a known host.' },
        ] },
    ];
    const ATTACKER = { id: 'attack', name: 'Attack machine', ip: '172.18.0.100', ports: '6081 (noVNC)',
        role: 'Your Kali machine, playing a compromised office PC. It sits on the same flat network as everything else, so it can reach every level directly. That is the most important lesson of this picture.',
        attacks: ['scanning', 'mitm', 'flood_overwrite'], ids: 'A known host, but not an expected Modbus writer or OPC-UA client, so its writes and sessions are flagged.' };
    register('purdue-explorer', function (node) {
        const { body } = frame(node, 'Purdue explorer: the CybICS network',
            'The Purdue model sorts the devices of a plant into levels, from the physical process (0) up to the business network (4 and 5). Click a host to see what it does and how it is attacked.');
        const wrap = el('div', { class: 'purdue' });
        const detail = el('div', { class: 'p-detail', 'aria-live': 'polite' });
        const buttons = [];
        function show(host, button) {
            buttons.forEach(b => b.classList.remove('active'));
            button.classList.add('active');
            const links = host.attacks.length ? host.attacks.map(a => `<a href="/ctf/challenge/${a}">${escapeHtml(CHALLENGES[a] || a)}</a>`).join(', ') : 'none';
            detail.innerHTML = `<h4>${escapeHtml(host.name)}</h4><dl>
                <dt>Address</dt><dd class="mono">${host.ip}</dd><dt>Ports</dt><dd>${escapeHtml(host.ports)}</dd>
                <dt>Role</dt><dd>${escapeHtml(host.role)}</dd><dt>Challenges</dt><dd>${links}</dd>
                <dt>IDS</dt><dd>${escapeHtml(host.ids)}</dd></dl>`;
        }
        function hostButton(host, extra) {
            const b = el('button', { type: 'button', class: 'p-host' + (extra || '') }, `${escapeHtml(host.name)}<small>${host.ip}</small>`);
            b.addEventListener('click', () => show(host, b));
            buttons.push(b);
            return b;
        }
        // The attack machine stands in for a compromised office PC, so it sits
        // at the enterprise levels, but it is wired straight into the plant
        // network: there is no DMZ (level 3.5) in the lab.
        const top = el('div', { class: 'p-level' }, `<div class="p-name"><b>Levels 4-5</b>Enterprise &middot; office IT, internet</div>`);
        const topHosts = el('div', { class: 'p-hosts' });
        topHosts.appendChild(hostButton(ATTACKER, ' attacker'));
        topHosts.appendChild(el('span', { class: 'w-note' }, 'stands in for a compromised office PC. In a real plant a firewall and a DMZ (level 3.5) would separate it from everything below; here it sits on 172.18.0.0/24 like every other host.'));
        top.appendChild(topHosts);
        wrap.appendChild(top);
        PURDUE.forEach(function (lvl) {
            const row = el('div', { class: 'p-level' }, `<div class="p-name"><b>${lvl.level}</b>${escapeHtml(lvl.name)} &middot; ${escapeHtml(lvl.hint)}</div>`);
            const hosts = el('div', { class: 'p-hosts' });
            lvl.hosts.forEach(h => hosts.appendChild(hostButton(h)));
            row.appendChild(hosts);
            wrap.appendChild(row);
        });
        body.append(wrap, detail);
        show(PURDUE[2].hosts[0], buttons[5]);
    });

    // ------------------------------------------------------------------
    // scan-cycle: the CybICS PLC program, one scan at a time
    // ------------------------------------------------------------------
    // The same decisions as software/OpenPLC/cybICS.st in automatic mode.
    function plcScan(inputs, state) {
        const next = { ...state };
        const notes = [];
        if (inputs.stop) {
            return { state: { compressorState: 0, gstState: 0 }, outputs: { compressor: false, systemValve: false, gstSig: false },
                notes: ['stop is set: everything switches off, whatever the pressures are.'] };
        }
        if (inputs.gst < 60 && state.gstState === 0) { next.gstState = 1; notes.push('GST below 60: start refilling the storage tank.'); }
        else if (inputs.gst < 240 && state.gstState === 1) { next.gstState = 1; notes.push('GST still below 240: keep refilling.'); }
        else { next.gstState = 0; }
        if (inputs.hpt < 60 && state.compressorState === 0 && inputs.gst > 50) { next.compressorState = 1; notes.push('HPT below 60 and enough gas in the GST: start the compressor.'); }
        else if (inputs.hpt < 90 && state.compressorState === 1 && inputs.gst > 50) { next.compressorState = 1; notes.push('Compressor is running and HPT is still below 90: keep it running.'); }
        else {
            if (state.compressorState === 1) notes.push(inputs.gst > 50 ? 'HPT reached 90: stop the compressor.' : 'GST is nearly empty (50 or less): stop the compressor to protect it.');
            next.compressorState = 0;
        }
        const systemValve = inputs.hpt > 50 && inputs.hpt < 100;
        notes.push(systemValve ? 'HPT between 50 and 100: the system valve is open and gas flows to the consumer.' : 'HPT outside 50-100: the system valve stays closed.');
        return { state: next, outputs: { compressor: next.compressorState === 1, systemValve, gstSig: next.gstState === 1 }, notes };
    }
    register('scan-cycle', function (node) {
        const { body } = frame(node, 'Scan cycle: think like the PLC',
            'Every 50 ms the CybICS PLC reads its inputs, runs its program and writes its outputs. Set the pressures, then step through one scan. Notice that the compressor remembers whether it was running: the same HPT of 75 can mean "on" or "off".');
        const controls = el('div');
        controls.innerHTML = `
            <div class="w-row"><label for="sc-hpt">HPT pressure <b data-o="hpt"></b></label><input id="sc-hpt" type="range" min="0" max="250" data-k="hpt"></div>
            <div class="w-row"><label for="sc-gst">GST pressure <b data-o="gst"></b></label><input id="sc-gst" type="range" min="0" max="250" data-k="gst"></div>
            <div class="w-row"><label><input type="checkbox" data-k="stop"> stop (register 1128) set</label></div>`;
        const cycle = el('div', { class: 'cycle' });
        const steps = ['1 · Read inputs', '2 · Run the program', '3 · Write outputs'].map(function (t) {
            const s = el('div', { class: 'cycle-step' }, `<b>${t}</b><div></div>`); cycle.appendChild(s); return s;
        });
        const actions = el('div', { class: 'w-row' });
        const stepBtn = el('button', { class: 't-btn primary', type: 'button' }, 'Next step');
        const autoBtn = el('button', { class: 't-btn', type: 'button' }, 'Run 20 scans');
        const reset = el('button', { class: 't-btn', type: 'button' }, 'Reset');
        actions.append(stepBtn, autoBtn, reset);
        const log = el('p', { class: 'w-note', 'aria-live': 'polite' });
        body.append(controls, cycle, actions, log);
        let inputs = { hpt: 75, gst: 180, stop: false }, state = { compressorState: 0, gstState: 0 };
        let snapshot = null, phase = -1, result = null;
        const pill = (on, a, b) => `<span class="w-pill ${on ? 'on' : 'off'}">${on ? a : b}</span>`;
        function paintControls() {
            controls.querySelector('[data-k=hpt]').value = inputs.hpt;
            controls.querySelector('[data-k=gst]').value = inputs.gst;
            controls.querySelector('[data-o=hpt]').textContent = inputs.hpt;
            controls.querySelector('[data-o=gst]').textContent = inputs.gst;
        }
        function paint() {
            steps.forEach((s, i) => s.classList.toggle('active', i === phase));
            steps[0].lastChild.innerHTML = snapshot ? `HPT = ${snapshot.hpt}, GST = ${snapshot.gst}${snapshot.stop ? ', stop = 1' : ''}<br><small>copied into memory; changes now wait for the next scan</small>` : '';
            steps[1].lastChild.innerHTML = result && phase >= 1 ? result.notes.map(escapeHtml).join('<br>') : '';
            steps[2].lastChild.innerHTML = result && phase >= 2 ? `Compressor ${pill(result.outputs.compressor, 'on', 'off')}<br>System valve ${pill(result.outputs.systemValve, 'open', 'closed')}<br>GST refill ${pill(result.outputs.gstSig, 'on', 'off')}` : '';
            stepBtn.textContent = phase === 2 || phase === -1 ? 'Start a scan' : 'Next step';
        }
        function step() {
            phase = (phase + 1) % 3;
            if (phase === 0) { snapshot = { ...inputs }; result = null; }
            if (phase === 1) { result = plcScan(snapshot, state); }
            if (phase === 2) { state = result.state; log.textContent = `Memory after this scan: compressor ${state.compressorState ? 'was running' : 'was off'}.`; }
            paint();
        }
        controls.addEventListener('input', function (e) {
            const k = e.target.dataset.k;
            if (k === 'stop') inputs.stop = e.target.checked; else if (k) inputs[k] = Number(e.target.value);
            paintControls();
        });
        stepBtn.addEventListener('click', step);
        // A crude plant so 20 scans show the hysteresis: the compressor fills the
        // HPT and drains the GST, the consumer drains the HPT.
        autoBtn.addEventListener('click', function () {
            const lines = [];
            for (let i = 0; i < 20; i++) {
                const r = plcScan(inputs, state); state = r.state;
                inputs.hpt = Math.max(0, Math.min(250, inputs.hpt + (r.outputs.compressor ? 3 : 0) - (r.outputs.systemValve ? 1 : 0)));
                inputs.gst = Math.max(0, Math.min(250, inputs.gst - (r.outputs.compressor ? 1 : 0) + (r.outputs.gstSig ? 4 : 0)));
                lines.push(r.outputs.compressor ? '▲' : '·');
            }
            phase = 2; snapshot = { ...inputs }; result = plcScan(inputs, state);
            paintControls(); paint();
            log.textContent = `20 scans (1 second of PLC time): compressor ${lines.join('')} → HPT is now ${inputs.hpt}. ▲ = compressor on.`;
        });
        reset.addEventListener('click', function () {
            inputs = { hpt: 75, gst: 180, stop: false }; state = { compressorState: 0, gstState: 0 };
            snapshot = null; result = null; phase = -1; log.textContent = '';
            controls.querySelector('[data-k=stop]').checked = false;
            paintControls(); paint();
        });
        paintControls(); paint();
    });

    // ------------------------------------------------------------------
    // ids-threshold: tune a rate rule, count hits and false alarms
    // ------------------------------------------------------------------
    // 120 s of Modbus writes. The engineer downloads a recipe in two bursts;
    // the attacker either floods or writes "low and slow".
    const IDS_SCENARIOS = {
        flood: { name: 'Attacker floods the HPT register', attacker: Array.from({ length: 40 }, (_, i) => 70 + i * 0.25) },
        slow: { name: 'Attacker writes low and slow', attacker: Array.from({ length: 12 }, (_, i) => 10 + i * 9) },
    };
    const ENGINEER = [...Array.from({ length: 8 }, (_, i) => 25 + i * 0.6), ...Array.from({ length: 6 }, (_, i) => 95 + i * 0.8)];
    register('ids-threshold', function (node) {
        const { body } = frame(node, 'Tune an IDS rule',
            'The rule: “alert when one host sends at least N Modbus writes within W seconds”. Blue marks are an engineer downloading a recipe (legitimate), red marks the attacker. CybICS uses N = 10 and W = 30 s for hosts that are not expected writers.');
        const controls = el('div');
        controls.innerHTML = `
            <div class="w-row"><label>Scenario <select data-k="scenario">${Object.entries(IDS_SCENARIOS).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join('')}</select></label>
            <label><input type="checkbox" data-k="allow"> allowlist the engineer's workstation</label></div>
            <div class="w-row"><label for="ids-n">Threshold N <b data-o="n"></b> writes</label><input id="ids-n" type="range" min="2" max="30" data-k="n"></div>
            <div class="w-row"><label for="ids-w">Window W <b data-o="w"></b> s</label><input id="ids-w" type="range" min="1" max="60" data-k="w"></div>`;
        const timeline = el('div', { class: 'timeline', role: 'img' });
        const legend = el('div', { class: 'legend' }, '<span><i style="background:var(--info)"></i>engineer write</span><span><i style="background:var(--bad)"></i>attacker write</span><span><i style="background:rgba(251,191,36,.5)"></i>alert raised</span><span>0 s → 120 s</span>');
        const score = el('div', { class: 'score', 'aria-live': 'polite' });
        const verdict = el('p', { class: 'w-note' });
        body.append(controls, timeline, legend, score, verdict);
        const cfg = { scenario: 'flood', n: 10, w: 30, allow: false };
        function alerts(times) {
            const out = []; let last = -Infinity;
            times.forEach(function (t, i) {
                const inWindow = times.filter(x => x <= t && x > t - cfg.w).length;
                if (inWindow >= cfg.n && t - last >= cfg.w) { out.push(t); last = t; }
            });
            return out;
        }
        function paint() {
            controls.querySelector('[data-o=n]').textContent = cfg.n;
            controls.querySelector('[data-o=w]').textContent = cfg.w;
            controls.querySelector('[data-k=n]').value = cfg.n;
            controls.querySelector('[data-k=w]').value = cfg.w;
            const atk = IDS_SCENARIOS[cfg.scenario].attacker;
            const atkAlerts = alerts(atk);
            const engAlerts = cfg.allow ? [] : alerts(ENGINEER);
            const x = t => (t / 120 * 100).toFixed(2) + '%';
            timeline.innerHTML = [...atkAlerts, ...engAlerts].map(t => `<div class="alarm" style="left:${x(t)};width:${x(Math.min(cfg.w, 120 - t))}"></div>`).join('') +
                ENGINEER.map(t => `<div class="ev hmi" style="left:${x(t)}"></div>`).join('') +
                atk.map(t => `<div class="ev atk" style="left:${x(t)}"></div>`).join('');
            const detected = atkAlerts.length > 0;
            const delay = detected ? (atkAlerts[0] - atk[0]).toFixed(1) + ' s' : '–';
            timeline.setAttribute('aria-label', `${atk.length} attacker writes, ${ENGINEER.length} engineer writes, ${atkAlerts.length + engAlerts.length} alerts`);
            score.innerHTML = `<div><b>${detected ? 'yes' : 'no'}</b>attack detected</div><div><b>${delay}</b>time to detect</div>` +
                `<div><b>${engAlerts.length}</b>false alarms</div><div><b>${atk.length}</b>attacker writes</div>`;
            verdict.innerHTML = !detected ? '<b>The attack goes unnoticed.</b> Lower N or widen W, but watch the false alarms.'
                : engAlerts.length ? '<b>Caught, but the engineer\'s legitimate work also raises alarms.</b> Too many of those and operators start ignoring the IDS. Try the allowlist, and think about what an attacker who spoofs that address could do.'
                : '<b>Caught, with no false alarms.</b> Now switch the scenario: does the same setting still work?';
        }
        controls.addEventListener('input', function (e) {
            const k = e.target.dataset.k;
            if (!k) return;
            cfg[k] = k === 'allow' ? e.target.checked : (k === 'scenario' ? e.target.value : Number(e.target.value));
            paint();
        });
        paint();
    });

    // ------------------------------------------------------------------
    // firewall-rules: first match wins
    // ------------------------------------------------------------------
    const FW_HOSTS = { any: 'any host', hwio: 'hwio (plant) .2', fuxa: 'FUXA HMI .4', opcua: 'OPC-UA .5', ews: 'Engineering WS .10', attacker: 'Attack machine .100' };
    const FW_FLOWS = [
        { src: 'hwio', port: 502, what: 'plant writes sensor values', needed: true },
        { src: 'fuxa', port: 502, what: 'HMI polls and controls', needed: true },
        { src: 'opcua', port: 502, what: 'OPC-UA gateway mirrors values', needed: true },
        { src: 'ews', port: 8080, what: 'engineer uploads a PLC program', needed: true },
        { src: 'attacker', port: 502, what: 'attacker writes registers', needed: false },
        { src: 'attacker', port: 8080, what: 'attacker logs in to the PLC web UI', needed: false },
        { src: 'ews', port: 502, what: 'engineering WS writes registers', needed: false },
        { src: 'attacker', port: 44818, what: 'attacker probes EtherNet/IP', needed: false },
    ];
    register('firewall-rules', function (node) {
        const { body } = frame(node, 'Firewall in front of the PLC',
            'These rules protect OpenPLC (172.18.0.3). They are checked from top to bottom and the first rule that matches decides. Make every needed connection pass and block everything else.');
        let rules = [{ action: 'allow', src: 'any', port: 'any' }];
        let policy = 'allow';
        const list = el('ul', { class: 'rules' });
        const add = el('div', { class: 'w-row' });
        add.innerHTML = `<select data-a="action"><option value="allow">allow</option><option value="deny">deny</option></select>
            from <select data-a="src">${Object.entries(FW_HOSTS).map(([k, v]) => `<option value="${k}">${v}</option>`).join('')}</select>
            to port <select data-a="port"><option value="any">any</option><option>502</option><option>8080</option><option>44818</option></select>
            <button class="t-btn" type="button" data-a="add">Add rule</button>
            <label>Otherwise <select data-a="policy"><option value="allow">allow</option><option value="deny">deny</option></select></label>`;
        const table = el('div', { style: 'overflow-x:auto' });
        const verdict = el('p', { 'aria-live': 'polite' });
        body.append(list, add, table, verdict);
        const matches = (r, f) => (r.src === 'any' || r.src === f.src) && (r.port === 'any' || Number(r.port) === f.port);
        function decide(f) {
            const i = rules.findIndex(r => matches(r, f));
            return i === -1 ? { pass: policy === 'allow', by: 'default policy' } : { pass: rules[i].action === 'allow', by: `rule ${i + 1}` };
        }
        function paint() {
            list.innerHTML = '';
            rules.forEach(function (r, i) {
                const li = el('li', { class: 'rule' },
                    `<span class="mono">${i + 1}</span><span class="act ${r.action}">${r.action}</span><span class="grow">from ${escapeHtml(FW_HOSTS[r.src])} to port ${r.port}</span>`);
                [['↑', -1, 'Move up'], ['↓', 1, 'Move down']].forEach(function ([label, dir, aria]) {
                    const b = el('button', { type: 'button', 'aria-label': `${aria}: rule ${i + 1}` }, label);
                    b.disabled = (dir < 0 && i === 0) || (dir > 0 && i === rules.length - 1);
                    b.addEventListener('click', function () { const j = i + dir; [rules[i], rules[j]] = [rules[j], rules[i]]; paint(); });
                    li.appendChild(b);
                });
                const del = el('button', { type: 'button', 'aria-label': `Delete rule ${i + 1}` }, '✕');
                del.addEventListener('click', function () { rules.splice(i, 1); paint(); });
                li.appendChild(del);
                list.appendChild(li);
            });
            if (!rules.length) list.appendChild(el('li', { class: 'w-note' }, 'No rules: the default policy decides everything.'));
            let good = 0;
            const rows = FW_FLOWS.map(function (f) {
                const d = decide(f);
                const right = d.pass === f.needed; good += right;
                return `<tr class="${right ? '' : (f.needed ? 'good-miss' : 'bad-miss')}"><td>${escapeHtml(FW_HOSTS[f.src])}</td><td>${f.port}</td><td>${escapeHtml(f.what)}</td>` +
                    `<td>${f.needed ? 'needed' : 'not needed'}</td><td class="verdict ${d.pass ? 'pass' : 'block'}">${d.pass ? 'passes' : 'blocked'}</td><td class="w-note">${d.by}</td></tr>`;
            });
            table.innerHTML = `<table class="flows"><tr><th>From</th><th>Port</th><th>What</th><th>Should it pass?</th><th>Result</th><th>Decided by</th></tr>${rows.join('')}</table>`;
            const brokeNeeded = FW_FLOWS.some(f => f.needed && !decide(f).pass);
            verdict.innerHTML = good === FW_FLOWS.length
                ? '<b class="w-ok">All eight connections are handled correctly.</b> Notice that you allowed what is needed and denied the rest, rather than trying to list every bad host: that is “default deny”.'
                : brokeNeeded ? `<b class="w-err">${FW_FLOWS.length - good} of ${FW_FLOWS.length} wrong, and the plant is affected:</b> a needed connection is blocked. In OT that can stop production, which is why firewall changes are tested first.`
                : `<b>${good} of ${FW_FLOWS.length} correct.</b> Some unwanted connections still pass. Hint: allow the four needed flows, then deny everything else.`;
        }
        add.addEventListener('click', function (e) {
            if (e.target.dataset.a !== 'add') return;
            rules.push({ action: add.querySelector('[data-a=action]').value, src: add.querySelector('[data-a=src]').value, port: add.querySelector('[data-a=port]').value });
            paint();
        });
        add.querySelector('[data-a=policy]').addEventListener('change', function (e) { policy = e.target.value; paint(); });
        paint();
    });
})();
