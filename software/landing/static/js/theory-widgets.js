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
        if (f.fc >= 0x80) throw new Error(`This is an error reply from the PLC: function code ${hex(f.fc, 2)} is ${hex(f.fc - 0x80, 2)} + 80, and exception code ${hex(b[8] ?? 0, 2)} says why (01 = function not supported, 02 = bad address, 03 = bad value). This builder takes requests; paste the request that came before it.`);
        if (!FUNCTION_CODES[f.fc]) throw new Error(`Function code ${hex(f.fc, 2)} is valid Modbus, but this example only explains 01, 03, 05, 06 and 10.`);
        // A read reply is function code, byte count, data. Say so rather than
        // failing on it: replies are half of every capture.
        if (FUNCTION_CODES[f.fc].kind === 'read' && b[8] === b.length - 9 && b.length !== 12) {
            const data = b.slice(9);
            const shown = f.fc === 3 && data.length % 2 === 0
                ? 'register values ' + Array.from({ length: data.length / 2 }, (_, i) => (data[2 * i] << 8) | data[2 * i + 1]).join(', ')
                : 'data bytes ' + data.map(x => hex(x, 2)).join(' ');
            throw new Error(`This is the PLC's reply, not a request: function code ${hex(f.fc, 2)}, then a byte count of ${b[8]}, then the ${shown}. A reply has no address, so match it to its request by the transaction ID (${word(0)}). This builder takes requests.`);
        }
        if (f.fc === 16 && b.length === 12) {
            throw new Error(`This is the PLC's reply to a write: it confirms ${word(10)} register(s) written from address ${word(8)}. This builder takes requests.`);
        }
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
            form.querySelector('[data-k=value]').max = fc.kind === 'coil' ? 1 : 65535;
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
              attacks: ['plc_programming'], ids: 'Named in the IDS host table, but not an expected Modbus writer or OPC-UA client: its writes, scans and OPC-UA sessions raise alerts like anyone else\'s.' },
            { id: 'cybicsagent', name: 'AI assistant', ip: '172.18.0.11', ports: '5000 (web), 11434 (Ollama)',
              role: 'The CybICS help assistant. Not part of a real plant, but it shows that every extra service on the network is one more thing to protect.',
              attacks: [], ids: 'Named in the IDS host table, but exempt from no rule.' },
            { id: 'nginx-proxy', name: 'Web proxy', ip: '172.18.0.12', ports: '80 (8082 on the host), 443 and further web ports',
              role: 'Forwards the web interfaces of the other containers to ports on the CybICS host, so a browser can reach them. Lab plumbing rather than part of a plant.',
              attacks: [], ids: 'Named in the IDS host table, but exempt from no rule.' },
        ] },
        { level: 'Level 2', name: 'Supervisory control', hint: 'HMI, SCADA, gateways', hosts: [
            { id: 'fuxa', name: 'FUXA HMI', ip: '172.18.0.4', ports: '1881 (web HMI)',
              role: 'The operators\' screen. It polls the PLC over Modbus and writes set points when an operator presses a button.',
              attacks: ['password_attack', 'mitm'], ids: 'Expected Modbus writer: its writes raise no alert. Its sign-in (/api/signin) does not match the http_brute_force rule, so password guessing against it raises no alert.' },
            { id: 'opcua', name: 'OPC-UA server', ip: '172.18.0.5', ports: '4840 (OPC-UA)',
              role: 'A gateway that offers the plant values to other systems over OPC-UA, a modern protocol with built-in security options.',
              attacks: ['opcua'], ids: 'OPC-UA sessions from hosts that are not expected clients raise an alert.' },
        ] },
        { level: 'Level 1', name: 'Basic control', hint: 'PLCs and controllers', hosts: [
            { id: 'openplc', name: 'OpenPLC', ip: '172.18.0.3', ports: '502 (Modbus), 8080 (web), 102 (S7), 20000 (DNP3), 44818 (EtherNet/IP)',
              role: 'The PLC: it runs the control program every 50 ms, reads the sensors and switches the compressor and valves.',
              attacks: ['flood_overwrite', 'fuzzingMB', 'password_openplc', 'plc_programming', 'scanning'], ids: 'Modbus write floods, unauthorised writes and diagnostic function codes raise alerts, and so does any S7comm access on port 102. A program upload over the web interface raises none.' },
            { id: 's7com', name: 'S7 server', ip: '172.18.0.6', ports: '1102 (S7comm)',
              role: 'Plays a Siemens S7 PLC, so you can practise S7comm enumeration.',
              attacks: ['scanning2'], ids: 'Every S7comm access raises an enumeration alert.' },
        ] },
        { level: 'Level 0', name: 'Physical process', hint: 'Sensors, actuators, the plant itself', hosts: [
            { id: 'hwio', name: 'Plant simulation (hwio)', ip: '172.18.0.2', ports: '8090 (3D view)',
              role: 'Simulates the tanks, the compressor and the valves, and writes the sensor values into the PLC 30 to 50 times a second.',
              attacks: ['physical_process'], ids: 'Expected Modbus writer: its writes raise no alert.' },
            { id: 'stm32', name: 'STM32 (on the board)', ip: 'no IP address', ports: 'none: it talks I²C to the Raspberry Pi, plus a UART console',
              role: 'On the real board, the microcontroller that runs the physical model and drives the LEDs and the display.',
              attacks: ['uart_basic'], ids: 'Not on the network at all, so the network IDS never sees it. Its UART console is a wire on the board.' },
        ] },
    ];
    const ATTACKER = { id: 'attack', name: 'Attack machine', ip: '172.18.0.100', ports: '7681 (terminal), 6081 (noVNC)',
        role: 'Your attacker host: the attack shell, and on a PC the Kali desktop too, playing a compromised office PC. It sits on the same flat network as everything else, so it can reach every level directly. That is the most important lesson of this picture.',
        attacks: ['scanning', 'mitm', 'flood_overwrite'], ids: 'Named in the IDS host table, but not an expected Modbus writer or OPC-UA client, so its writes and sessions are flagged.' };
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
        show(PURDUE[2].hosts[0], buttons[6]);
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
        const autoBtn = el('button', { class: 't-btn', type: 'button' }, 'Run 60 seconds');
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
        // The plant at the average rates of hwio-virtual, which updates the
        // pressures about once a second: a running compressor moves 2 bar out
        // of the GST and 1 into the HPT; otherwise the consumer takes 0-2 bar
        // from the HPT while the system valve is open; the refill adds 0-3.
        // The PLC scans 20 times in each of those seconds, but sees the same
        // pressures, so one scan per second decides the same.
        autoBtn.addEventListener('click', function () {
            const marks = [];
            for (let t = 0; t < 60; t++) {
                const r = plcScan(inputs, state); state = r.state;
                if (r.outputs.compressor) {
                    if (inputs.hpt < 255 && inputs.gst >= 50) { inputs.gst -= 2; inputs.hpt += 1; }
                } else if (r.outputs.systemValve) {
                    inputs.hpt = Math.max(0, inputs.hpt - [0, 1, 2][t % 3]);
                }
                if (r.outputs.gstSig && inputs.gst < 251) inputs.gst = Math.min(255, inputs.gst + [0, 1, 2, 3][t % 4]);
                marks.push(r.outputs.compressor ? '▲' : '·');
            }
            phase = 2; snapshot = { ...inputs }; result = plcScan(inputs, state);
            paintControls(); paint();
            log.textContent = `60 seconds (about 1200 scans): compressor ${marks.join('')} → HPT is now ${inputs.hpt}, GST ${inputs.gst}. ▲ = compressor on during that second.`;
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
        burst: { name: 'Attacker writes a short burst (4 a second for 10 s)', attacker: Array.from({ length: 40 }, (_, i) => 70 + i * 0.25) },
        flood: { name: 'Attacker floods register 1126 (200 a second for 3 s)', attacker: Array.from({ length: 600 }, (_, i) => 70 + i * 0.005) },
        slow: { name: 'Attacker writes low and slow', attacker: Array.from({ length: 12 }, (_, i) => 10 + i * 9) },
    };
    const ENGINEER = [...Array.from({ length: 8 }, (_, i) => 25 + i * 0.6), ...Array.from({ length: 6 }, (_, i) => 95 + i * 0.8)];
    register('ids-threshold', function (node) {
        const { body } = frame(node, 'Tune an IDS rule',
            'The rule: “alert when one host sends at least N Modbus writes within W seconds”. Blue marks are the engineering workstation (172.18.0.10) downloading a recipe, which is legitimate but not an expected writer; red marks the attacker. For hosts that are not expected writers CybICS uses N = 10, W = 30 s (modbus_unauth_write) and N = 50, W = 5 s (modbus_flood).');
        const controls = el('div');
        controls.innerHTML = `
            <div class="w-row"><label>Scenario <select data-k="scenario">${Object.entries(IDS_SCENARIOS).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join('')}</select></label>
            <label><input type="checkbox" data-k="allow"> allowlist the engineering workstation</label></div>
            <div class="w-row"><label for="ids-n">Threshold N <b data-o="n"></b> writes</label><input id="ids-n" type="range" min="2" max="60" data-k="n"></div>
            <div class="w-row"><label for="ids-w">Window W <b data-o="w"></b> s</label><input id="ids-w" type="range" min="1" max="60" data-k="w"></div>`;
        const timeline = el('div', { class: 'timeline', role: 'img' });
        const legend = el('div', { class: 'legend' }, '<span><i style="background:var(--info)"></i>engineering workstation write</span><span><i style="background:var(--bad)"></i>attacker write</span><span><i style="background:rgba(251,191,36,.5)"></i>alert raised</span><span>0 s → 120 s</span>');
        const score = el('div', { class: 'score', 'aria-live': 'polite' });
        const verdict = el('p', { class: 'w-note' });
        body.append(controls, timeline, legend, score, verdict);
        // A lesson can start the widget on its own rule: data-scenario, data-n, data-w.
        const d = node.dataset;
        const cfg = { scenario: IDS_SCENARIOS[d.scenario] ? d.scenario : 'burst', n: clampInt(d.n, 2, 60, 10), w: clampInt(d.w, 1, 60, 30), allow: false };
        // Like the IDS: once a rule has fired for a host, it stays quiet for
        // that host for 30 s, whatever the window.
        const COOLDOWN = 30;
        function alerts(times) {
            const out = []; let last = -Infinity;
            times.forEach(function (t) {
                const inWindow = times.filter(x => x <= t && x >= t - cfg.w).length;
                if (inWindow >= cfg.n && t - last >= COOLDOWN) { out.push(t); last = t; }
            });
            return out;
        }
        function paint() {
            controls.querySelector('[data-o=n]').textContent = cfg.n;
            controls.querySelector('[data-o=w]').textContent = cfg.w;
            controls.querySelector('[data-k=n]').value = cfg.n;
            controls.querySelector('[data-k=w]').value = cfg.w;
            controls.querySelector('[data-k=scenario]').value = cfg.scenario;
            const atk = IDS_SCENARIOS[cfg.scenario].attacker;
            const atkAlerts = alerts(atk);
            const engAlerts = cfg.allow ? [] : alerts(ENGINEER);
            const x = t => (t / 120 * 100).toFixed(2) + '%';
            timeline.innerHTML = [...atkAlerts, ...engAlerts].map(t => `<div class="alarm" style="left:${x(t)};width:${x(Math.min(COOLDOWN, 120 - t))}"></div>`).join('') +
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
                return `<tr class="${right ? '' : (f.needed ? 'good-miss' : 'bad-miss')}"><td>${escapeHtml(FW_HOSTS[f.src])} &rarr; ${f.port}<br><small class="w-note">${escapeHtml(f.what)}</small></td>` +
                    `<td class="verdict ${d.pass ? 'pass' : 'block'}">${d.pass ? 'passes' : 'blocked'}<br><small class="w-note">${d.by}</small></td><td>${f.needed ? 'needed' : 'not needed'}</td></tr>`;
            });
            table.innerHTML = `<table class="flows"><tr><th>Connection</th><th>Result</th><th>Should it pass?</th></tr>${rows.join('')}</table>`;
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

    // ------------------------------------------------------------------
    // sequence: put the steps of a story in order, and name each one
    // ------------------------------------------------------------------
    // The steps come from "exercises" in the lesson's sidecar, in the right
    // order; the reader gets them shuffled.
    register('sequence', function (node) {
        const ex = window.TheoryWidgets.exercises[node.dataset.id];
        if (!ex || !ex.steps) throw new Error('no exercise ' + node.dataset.id);
        const labels = ex.labels || [];
        // "order": false turns it into a matching exercise: only the labels count.
        const ordered = ex.order !== false;
        const { body } = frame(node, ex.title || (ordered ? 'Put the steps in order' : 'Match each item'), inline(ex.intro || 'Move the steps into the right order with the arrows.'));
        const steps = ex.steps.map((st, i) => ({ ...st, key: i, chosen: '' }));
        let order = steps.slice();
        do {
            for (let i = order.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [order[i], order[j]] = [order[j], order[i]];
            }
        } while (ordered && order.length > 2 && order.every((st, i) => st.key === i));
        const list = el('ol', { class: 'rules seq' });
        const actions = el('div', { class: 'w-row' });
        const check = el('button', { class: 't-btn primary', type: 'button' }, 'Check');
        const solve = el('button', { class: 't-btn', type: 'button', hidden: '' }, 'Show the answer');
        actions.append(check, solve);
        const verdict = el('p', { 'aria-live': 'polite' });
        body.append(list, actions, verdict);
        let graded = false;
        function paint() {
            list.innerHTML = '';
            order.forEach(function (st, i) {
                const li = el('li', { class: 'rule' });
                const posOk = !ordered || st.key === i, labelOk = !labels.length || st.chosen === st.label;
                if (graded) li.classList.add(posOk && labelOk ? 'ok' : 'bad');
                if (ordered) li.appendChild(el('span', { class: 'mono' }, String(i + 1)));
                li.appendChild(el('span', { class: 'grow' }, inline(st.text)));
                if (labels.length) {
                    const select = el('select', { 'aria-label': `Label for step ${i + 1}` },
                        `<option value="">choose…</option>` + labels.map(l => `<option${l === st.chosen ? ' selected' : ''}>${escapeHtml(l)}</option>`).join(''));
                    select.addEventListener('change', function () { st.chosen = select.value; graded = false; verdict.textContent = ''; paint(); });
                    li.appendChild(select);
                }
                if (ordered) {
                    // On a phone a position picker beats tapping arrows five times.
                    const pos = el('select', { class: 'seq-pos', 'aria-label': `Position of step ${i + 1}` },
                        order.map((_, j) => `<option value="${j}"${j === i ? ' selected' : ''}>${j + 1}</option>`).join(''));
                    pos.addEventListener('change', function () {
                        const [item] = order.splice(i, 1);
                        order.splice(Number(pos.value), 0, item);
                        graded = false; verdict.textContent = ''; paint();
                    });
                    li.appendChild(pos);
                }
                if (ordered) [['↑', -1, 'Move up'], ['↓', 1, 'Move down']].forEach(function ([label, dir, aria]) {
                    const b = el('button', { type: 'button', class: 'seq-mv', 'aria-label': `${aria}: step ${i + 1}` }, label);
                    b.disabled = (dir < 0 && i === 0) || (dir > 0 && i === order.length - 1);
                    b.addEventListener('click', function () {
                        const j = i + dir; [order[i], order[j]] = [order[j], order[i]];
                        graded = false; verdict.textContent = ''; paint();
                        list.children[j].querySelectorAll('button')[dir < 0 ? 0 : 1].focus();
                    });
                    li.appendChild(b);
                });
                if (graded) {
                    const why = posOk && labelOk ? '' : !posOk ? 'Not in this position. ' : `${ordered ? 'Right place, but not' : 'Not'} “${escapeHtml(st.chosen || 'no label')}”. `;
                    li.appendChild(el('div', { class: 'seq-why' }, (why ? `<b>${why}</b>` : '') + (posOk && labelOk ? inline(st.explain || '') : '')));
                }
                list.appendChild(li);
            });
        }
        check.addEventListener('click', function () {
            graded = true;
            const right = order.filter((st, i) => (!ordered || st.key === i) && (!labels.length || st.chosen === st.label)).length;
            verdict.innerHTML = right === order.length
                ? `<b class="w-ok">All ${order.length} are right.</b> Read the explanations under each one.`
                : `<b>${right} of ${order.length} right.</b> The marked ones need another look; the explanation appears once one is right.`;
            solve.hidden = right === order.length;
            paint();
        });
        solve.addEventListener('click', function () {
            if (ordered) order = steps.slice().sort((a, b) => a.key - b.key);
            order.forEach(st => { st.chosen = st.label || ''; });
            graded = true; solve.hidden = true;
            verdict.innerHTML = ordered ? '<b>This is the order the lesson describes.</b> Read why each step comes where it does.' : '<b>These are the answers.</b> Read why each one fits.';
            paint();
        });
        paint();
    });

    // ------------------------------------------------------------------
    // arp-spoof: how an attacker gets between the HMI and the PLC
    // ------------------------------------------------------------------
    const ARP_HOSTS = {
        fuxa: { name: 'FUXA HMI', ip: '172.18.0.4', mac: '3a:5e:91:0c:27:b1' },
        attacker: { name: 'Attack machine', ip: '172.18.0.100', mac: 'c6:76:2b:3f:44:40' },
        plc: { name: 'OpenPLC', ip: '172.18.0.3', mac: 'd6:10:7c:61:8a:64' },
    };
    const ARP_STEPS = [
        { title: 'Normal operation', poisonFuxa: false, poisonPlc: false,
          text: 'FUXA polls the PLC once a second. Each host has learned the other\'s MAC address and keeps it in its ARP cache. The frames go straight from one to the other.' },
        { title: 'Poison FUXA', poisonFuxa: true, poisonPlc: false,
          text: 'The attacker sends FUXA an ARP reply nobody asked for: “172.18.0.3 is at c6:76:2b:3f:44:40”. FUXA believes the last reply it heard and overwrites its cache. Its requests now go to the attacker, but the PLC\'s answers still go straight back.' },
        { title: 'Poison the PLC', poisonFuxa: true, poisonPlc: true,
          text: 'The same lie to the PLC, about FUXA\'s address. Now both directions pass the attack machine. The IP addresses in the packets have not changed, so neither side sees anything unusual.' },
        { title: 'Relay or rewrite', poisonFuxa: true, poisonPlc: true, relay: true,
          text: 'The attacker has to pass the traffic on, or the HMI goes dark and someone notices at once. With forwarding on, a proxy can also rewrite the answers on their way back.' },
    ];
    register('arp-spoof', function (node) {
        const { body } = frame(node, 'ARP spoofing, step by step',
            'Step through the attack and watch the ARP caches, the path of the traffic and what the IDS sees.');
        const stage = el('div', { class: 'arp' });
        const story = el('div', { class: 'explain', 'aria-live': 'polite' });
        const relayRow = el('div', { class: 'w-row' }, `<label><input type="checkbox" data-k="forward" checked> IP forwarding on the attack machine</label>
            <label><input type="checkbox" data-k="rewrite"> rewrite the HPT reading on its way back</label>`);
        const nav = el('div', { class: 'w-row' });
        const prev = el('button', { class: 't-btn', type: 'button' }, '← Back');
        const next = el('button', { class: 't-btn primary', type: 'button' }, 'Next step →');
        const where = el('span', { class: 'w-note' });
        nav.append(prev, next, where);
        body.append(stage, story, relayRow, nav);
        let i = 0;
        const cfg = { forward: true, rewrite: false };
        const cache = (rows) => '<table class="flows arp-cache"><tr><th>IP</th><th>MAC in the cache</th></tr>' +
            rows.map(([ip, mac, bad]) => `<tr><td class="mono">${ip}</td><td class="mono${bad ? ' arp-bad' : ''}">${mac}${bad ? ' ⚠' : ''}</td></tr>`).join('') + '</table>';
        function paint() {
            const st = ARP_STEPS[i];
            const H = ARP_HOSTS;
            const viaReq = st.poisonFuxa, viaResp = st.poisonPlc;
            const broken = st.relay && !cfg.forward;
            const forged = st.relay && cfg.forward && cfg.rewrite;
            stage.innerHTML = `
                <div class="arp-host"><b>${H.fuxa.name}</b><small class="mono">${H.fuxa.ip}</small>${cache([[H.plc.ip, st.poisonFuxa ? H.attacker.mac : H.plc.mac, st.poisonFuxa]])}</div>
                <div class="arp-host attacker"><b>${H.attacker.name}</b><small class="mono">${H.attacker.ip} &middot; ${H.attacker.mac}</small>
                    <div class="w-note">${!viaReq ? 'Not involved yet.' : broken ? 'Receives the frames and drops them.' : viaResp ? (st.relay ? 'Relays every frame' + (cfg.rewrite ? ' and changes the HPT value in the answers.' : '.') : 'Sees both directions.') : 'Sees FUXA\'s requests.'}</div></div>
                <div class="arp-host"><b>${H.plc.name}</b><small class="mono">${H.plc.ip}</small>${cache([[H.fuxa.ip, st.poisonPlc ? H.attacker.mac : H.fuxa.mac, st.poisonPlc]])}</div>
                <div class="arp-path"><b>Request</b> FUXA → ${viaReq ? (broken ? '<span class="arp-bad">attacker ✕</span>' : 'attacker → ') : ''}${broken ? '' : 'PLC'}
                    &nbsp;&middot;&nbsp; <b>Answer</b> ${broken ? '<span class="w-note">none</span>' : `PLC → ${viaResp ? 'attacker → ' : ''}FUXA`}
                    &nbsp;&middot;&nbsp; <b>HMI shows</b> ${broken ? '<span class="arp-bad">no connection</span>' : forged ? 'HPT 75 bar <span class="arp-bad">(forged: the proxy sends 75, whatever the tank really holds)</span>' : 'the real HPT pressure'}</div>
                <div class="arp-ids"><b>IDS (arp_spoof)</b> ${st.poisonFuxa
                    ? `<span class="w-pill alert">alert</span> 172.18.0.3 seen with ${H.plc.mac} and ${H.attacker.mac}${st.poisonPlc ? '; 172.18.0.4 with two MACs as well' : ''}`
                    : '<span class="w-pill off">quiet</span> every IP address has one MAC'}</div>`;
            story.innerHTML = `<b>${i + 1}. ${escapeHtml(st.title)}.</b> ${escapeHtml(st.text)}` +
                (broken ? ' <b>Forwarding is off: the attacker swallows the frames and the HMI loses its connection.</b>' : '');
            relayRow.hidden = !st.relay;
            prev.disabled = i === 0; next.disabled = i === ARP_STEPS.length - 1;
            where.textContent = `Step ${i + 1} of ${ARP_STEPS.length}`;
        }
        prev.addEventListener('click', () => { i = Math.max(0, i - 1); paint(); });
        next.addEventListener('click', () => { i = Math.min(ARP_STEPS.length - 1, i + 1); paint(); });
        relayRow.addEventListener('change', function (e) { cfg[e.target.dataset.k] = e.target.checked; paint(); });
        paint();
    });

    // ------------------------------------------------------------------
    // keyspace: how long it takes to guess a password
    // ------------------------------------------------------------------
    const CHARSETS = [['lower', 'a-z', 26], ['upper', 'A-Z', 26], ['digits', '0-9', 10], ['symbols', 'symbols', 33]];
    const SPEEDS = [
        ['online', 'Online, at a web login', 10, '10'],
        ['parallel', 'Online, many connections', 1000, '1,000'],
        ['slowhash', 'Offline, stolen bcrypt hash', 1e4, '10,000'],
        ['fasthash', 'Offline, stolen MD5 hash', 1e10, '10 billion'],
    ];
    const sci = n => n.toExponential(1).replace(/e\+(\d+)/, ' × 10<sup>$1</sup>');
    function duration(seconds) {
        if (seconds < 1) return 'less than a second';
        const units = [['year', 31557600], ['day', 86400], ['hour', 3600], ['minute', 60], ['second', 1]];
        for (const [name, size] of units) {
            if (seconds >= size) {
                const n = seconds / size;
                if (name === 'year' && n >= 1e6) return `${sci(n)} years`;
                const r = n >= 10 ? Math.round(n) : Math.round(n * 10) / 10;
                return `${r.toLocaleString('en')} ${name}${r === 1 ? '' : 's'}`;
            }
        }
    }
    register('keyspace', function (node) {
        const { body } = frame(node, 'How long does guessing take?',
            'Choose what a password is made of and how fast the attacker can try. The result is how long it takes to try every possibility; on average the right one turns up after half of that.');
        const controls = el('div');
        controls.innerHTML = `
            <div class="w-row"><label><input type="radio" name="ks-kind" value="random" checked> random characters</label>
                <label><input type="radio" name="ks-kind" value="word"> a word from a leaked password list</label>
                <label><input type="radio" name="ks-kind" value="default"> the vendor's default password</label></div>
            <div class="w-row" data-show="random">${CHARSETS.map(([k, n, size]) => `<label><input type="checkbox" data-c="${k}"${k === 'lower' ? ' checked' : ''}> ${n} (${size})</label>`).join('')}</div>
            <div class="w-row" data-show="random"><label for="ks-len">Length <b data-o="len"></b> characters</label><input id="ks-len" type="range" min="1" max="20" value="6" data-k="len"></div>
            <div class="w-row"><label>Attacker <select data-k="speed">${SPEEDS.map(([k, n, , label]) => `<option value="${k}">${n}: ~${label} per second</option>`).join('')}</select></label></div>
            <p class="w-note">Online guesses each wait for the server's answer. Offline, the attacker has stolen the stored hash of the password and tests guesses on a graphics card (GPU) as fast as it can compute; bcrypt is built to be slow, MD5 is not.</p>`;
        const score = el('div', { class: 'score', 'aria-live': 'polite' });
        const verdict = el('p', { class: 'w-note' });
        body.append(controls, score, verdict);
        function paint() {
            const kind = controls.querySelector('[name=ks-kind]:checked').value;
            controls.querySelectorAll('[data-show=random]').forEach(r => { r.hidden = kind !== 'random'; });
            const len = Number(controls.querySelector('[data-k=len]').value);
            controls.querySelector('[data-o=len]').textContent = len;
            const pool = CHARSETS.filter(([k]) => controls.querySelector(`[data-c=${k}]`).checked).reduce((n, c) => n + c[2], 0);
            const [, speedName, rate] = SPEEDS.find(sp => sp[0] === controls.querySelector('[data-k=speed]').value);
            const total = kind === 'default' ? 1 : kind === 'word' ? 14e6 : Math.pow(pool || 0, len);
            const seconds = total / rate;
            const big = total >= 1e6 ? sci(total) : Math.round(total).toLocaleString('en');
            score.innerHTML = `<div><b>${pool || kind !== 'random' ? big : '0'}</b>${total === 1 ? 'possibility' : 'possibilities'}</div><div><b>${duration(seconds)}</b>to try them all</div><div><b>${duration(seconds / 2)}</b>on average</div>`;
            verdict.innerHTML = kind === 'default' ? '<b>One guess.</b> Default passwords are printed in the manual and collected in public lists. No length helps if nobody changed it.'
                : kind === 'word' ? '<b>A leaked list has about 14 million real passwords</b> (the RockYou list). Attackers try it first, so a password that is on it falls fast even if it looks long.'
                : !pool ? 'Pick at least one kind of character.'
                : seconds < 86400 ? '<b>Too short.</b> Every extra character multiplies the work; a bigger character set helps less than a longer password.'
                : rate <= 1000 ? '<b>Safe against online guessing</b>, especially with a lockout after a few failures. Now switch to an offline attacker with a stolen hash.'
                : '<b>Holds up even offline.</b> Length did most of that work.';
        }
        controls.addEventListener('input', paint);
        controls.addEventListener('change', paint);
        paint();
    });

    // ------------------------------------------------------------------
    // alert-log: triage a morning of IDS alerts
    // ------------------------------------------------------------------
    // A made-up morning in the CybICS IDS, in its own message formats
    // (software/ids/rules.py). Not the data of the IDS Forensics challenge.
    const ALERT_LOG = [
        ['09:58:40', 'low', 'opcua_access', '172.18.0.11', '172.18.0.5', 'OPC-UA access from non-service host 172.18.0.11'],
        ['10:02:11', 'medium', 'port_scan', '172.18.0.100', '172.18.0.3', 'Port scan detected: 5 ports probed on 172.18.0.3'],
        ['10:02:47', 'medium', 'port_scan', '172.18.0.100', '172.18.0.6', 'Port scan detected: 5 ports probed on 172.18.0.6'],
        ['10:03:30', 'medium', 's7_enumeration', '172.18.0.100', '172.18.0.6', 'S7comm access from 172.18.0.100 to port 1102'],
        ['10:06:10', 'high', 'http_brute_force', '172.18.0.100', '172.18.0.3', 'Brute force on OpenPLC: 9 login attempts in 30s'],
        ['10:09:47', 'high', 'modbus_unauth_write', '172.18.0.10', '172.18.0.3', 'Unauthorized Modbus writes from 172.18.0.10 (10 in 30s)'],
        ['10:12:15', 'medium', 'modbus_diagnostic', '172.18.0.100', '172.18.0.3', 'Modbus diagnostic function 0x08 from 172.18.0.100'],
        ['10:14:03', 'critical', 'arp_spoof', '172.18.0.3', '', "ARP spoofing: IP 172.18.0.3 seen with multiple MACs: {'d6:10:7c:61:8a:64', 'c6:76:2b:3f:44:40'}"],
        ['10:16:20', 'high', 'modbus_unauth_write', '172.18.0.100', '172.18.0.3', 'Unauthorized Modbus writes from 172.18.0.100 (10 in 30s)'],
        ['10:16:24', 'critical', 'modbus_flood', '172.18.0.100', '172.18.0.3', 'Modbus write flood: 50 writes in 5s'],
        ['10:16:55', 'critical', 'modbus_flood', '172.18.0.100', '172.18.0.3', 'Modbus write flood: 50 writes in 5s'],
        ['10:17:30', 'high', 'syn_flood', '172.18.0.100', '172.18.0.3', 'SYN flood detected: 100 SYN packets in 10s'],
    ];
    const ALERT_QUESTIONS = [
        { q: 'Which host is the attacker?', options: ['172.18.0.100', '172.18.0.3', '172.18.0.10', '172.18.0.11'], answer: 0,
          why: 'It raises most of the alerts and they follow the arc of an attack: scan, enumerate, guess passwords, then write to the PLC.' },
        { q: 'What did the attacker do first?', options: ['Flooded the PLC with Modbus writes', 'Scanned for open ports', 'Poisoned ARP caches', 'Guessed the OpenPLC password'], answer: 1,
          why: 'The two port_scan alerts at 10:02 are its first. Discovery comes before the attack itself, which is why scans are worth an alert.' },
        { q: 'The arp_spoof alert names 172.18.0.3, the PLC, as its source. What does that tell you?', options: ['The PLC is attacking the network', 'Someone claimed to be 172.18.0.3; the second MAC shows who', 'The IDS has made a mistake and the alert can be ignored'], answer: 1,
          why: 'An ARP alert is about the address that was impersonated. c6:76:2b:3f:44:40 is the attack machine\'s MAC, so the source column alone would have pointed you at the victim.' },
        { q: 'Which alerts would you check with the plant staff before calling them hostile?', options: ['Those from 172.18.0.10 and 172.18.0.11', 'All alerts from 172.18.0.100', 'Only the critical ones'], answer: 0,
          why: 'The engineering workstation and the AI assistant are known hosts that do odd things for good reasons, such as a maintenance download. Check first; an attacker who took over one of them would look the same.' },
    ];
    register('alert-log', function (node) {
        const { body } = frame(node, 'Triage an IDS alert log',
            'A morning of alerts from the CybICS IDS. Filter them, look at the counts, and answer the questions below the log.');
        const sources = [...new Set(ALERT_LOG.map(a => a[3]))];
        const rulesSeen = [...new Set(ALERT_LOG.map(a => a[2]))];
        const sevs = ['critical', 'high', 'medium', 'low'];
        const filters = el('div', { class: 'w-row' });
        const opt = (k, list) => `<select data-f="${k}"><option value="">all</option>${list.map(v => `<option>${v}</option>`).join('')}</select>`;
        filters.innerHTML = `<label>Source ${opt('src', sources)}</label><label>Rule ${opt('rule', rulesSeen)}</label><label>Severity ${opt('sev', sevs)}</label>
            <label>Text <input type="text" data-f="text" placeholder="e.g. 0x08"></label>`;
        const summary = el('div', { class: 'score' });
        const log = el('ol', { class: 'alog' });
        const quiz = el('div', { class: 'alog-q' });
        body.append(filters, summary, log, quiz);
        function paint() {
            const f = {};
            filters.querySelectorAll('[data-f]').forEach(i => { f[i.dataset.f] = i.value.trim().toLowerCase(); });
            const rows = ALERT_LOG.filter(a => (!f.src || a[3] === f.src) && (!f.rule || a[2] === f.rule) && (!f.sev || a[1] === f.sev) &&
                (!f.text || a.join(' ').toLowerCase().includes(f.text)));
            const count = (i) => rows.reduce((m, a) => (m[a[i]] = (m[a[i]] || 0) + 1, m), {});
            const top = Object.entries(count(3)).sort((a, b) => b[1] - a[1])[0];
            summary.innerHTML = `<div><b>${rows.length}</b>alerts shown</div><div><b>${Object.keys(count(2)).length}</b>different rules</div>` +
                `<div><b>${count(1).critical || 0}</b>critical</div><div><b class="mono">${top ? top[0] : '–'}</b>most alerts${top ? ` (${top[1]})` : ''}</div>`;
            log.innerHTML = rows.map(a => `<li class="sev-${a[1]}"><span class="mono">${a[0]}</span> <span class="w-pill">${a[1]}</span> <b>${a[2]}</b>` +
                `<br><span class="mono">${a[3]}${a[4] ? ' → ' + a[4] : ''}</span><br><span class="w-note">${escapeHtml(a[5])}</span></li>`).join('') ||
                '<li class="w-note">No alert matches these filters.</li>';
        }
        ALERT_QUESTIONS.forEach(function (q, n) {
            const box = el('div', { class: 'q' });
            box.innerHTML = `<div class="q-text">${escapeHtml(q.q)}</div>`;
            const row = el('div', { class: 'w-row' });
            const select = el('select', { 'aria-label': q.q }, '<option value="">choose…</option>' + q.options.map((o, i) => `<option value="${i}">${escapeHtml(o)}</option>`).join(''));
            const fb = el('div', { class: 'q-feedback', 'aria-live': 'polite' });
            select.addEventListener('change', function () {
                if (select.value === '') { fb.className = 'q-feedback'; return; }
                const ok = Number(select.value) === q.answer;
                fb.className = 'q-feedback show ' + (ok ? 'ok' : 'bad');
                fb.innerHTML = ok ? `<b>Correct.</b>${escapeHtml(q.why)}` : '<b>Not quite.</b>Use the filters to look again.';
            });
            row.appendChild(select);
            box.append(row, fb);
            quiz.appendChild(box);
        });
        filters.addEventListener('input', paint);
        paint();
    });

    // ------------------------------------------------------------------
    // opcua-security: the channel and the identity are two choices
    // ------------------------------------------------------------------
    // What software/opcua/opcua.py and user_manager.py do with each pair.
    const UA_IDENTITIES = {
        anonymous: { name: 'Anonymous', session: false, why: 'The server advertises the Anonymous token, but its user manager finds no user and ActivateSession fails with BadUserAccessDenied.' },
        wrong: { name: 'user1 with a wrong password', session: false, why: 'The password check fails, so ActivateSession is refused. Each try is a round trip the network can see.' },
        user: { name: 'user1 with the right password', session: true, role: 'User', write: false, why: 'Accepted with the role User: it may browse and read, but every write is refused.' },
        cert: { name: 'The registered admin certificate', session: true, role: 'Admin', write: true, why: 'The server registered this certificate as an administrator at start-up, so the session gets the role Admin and may write.' },
    };
    register('opcua-security', function (node) {
        const { body } = frame(node, 'OPC-UA: envelope and ID card',
            'Pick how the channel is protected and who the client claims to be, and see what the CybICS server (port 4840) does with it, and what someone listening on the network gets.');
        const controls = el('div', { class: 'w-row' });
        controls.innerHTML = `<label>Channel <select data-k="policy"><option value="none">Security policy None</option><option value="enc">Basic256Sha256, SignAndEncrypt</option></select></label>
            <label>Identity <select data-k="id">${Object.entries(UA_IDENTITIES).map(([k, v]) => `<option value="${k}">${escapeHtml(v.name)}</option>`).join('')}</select></label>`;
        const score = el('div', { class: 'score', 'aria-live': 'polite' });
        const detail = el('dl', { class: 'ua-detail' });
        body.append(controls, score, detail);
        function paint() {
            const enc = controls.querySelector('[data-k=policy]').value === 'enc';
            const ident = UA_IDENTITIES[controls.querySelector('[data-k=id]').value];
            const pill = (on, a, b) => `<span class="w-pill ${on ? 'on' : 'off'}">${on ? a : b}</span>`;
            score.innerHTML = `<div><b>${pill(ident.session, 'yes', 'refused')}</b>session</div><div><b>${ident.role || '–'}</b>role</div>` +
                `<div><b>${pill(ident.session, 'yes', 'no')}</b>may read</div><div><b>${pill(ident.write, 'yes', 'no')}</b>may write</div>`;
            const sniff = enc
                ? 'Scrambled bytes only. It still sees that this host talks to port 4840, when, and how much.'
                : 'Every request and every value in readable form' +
                  (ident === UA_IDENTITIES.anonymous ? '.' : ident === UA_IDENTITIES.cert ? ', and the client certificate (that is public; the private key never travels).'
                  : ', and the user name. The password itself is encrypted with the server\'s key, because this server\'s token policy asks for it; a server set up differently would send it readable.');
            const tamper = enc ? 'Detected: every message is signed, so a changed byte breaks the signature.'
                : 'Not detected: a man in the middle can change values in either direction.';
            detail.innerHTML = `<dt>Server</dt><dd>${escapeHtml(ident.why)}</dd><dt>A listener sees</dt><dd>${escapeHtml(sniff)}</dd>` +
                `<dt>A changed message</dt><dd>${escapeHtml(tamper)}</dd><dt>IDS</dt><dd>${escapeHtml('From the attack machine: an opcua_access alert (low), whatever the channel or identity. The rule only asks whether the host is an expected OPC-UA client.')}</dd>`;
        }
        controls.addEventListener('change', paint);
        paint();
    });

    // ------------------------------------------------------------------
    // rate-planner: stay under the IDS rate rules for two minutes
    // ------------------------------------------------------------------
    // The two Modbus write rules of software/ids/rules.py and the two-minute
    // evasion window of the IDS Evasion challenge.
    const RATE_RULES = [
        { rule: 'modbus_unauth_write', n: 10, w: 30 },
        { rule: 'modbus_flood', n: 50, w: 5 },
    ];
    register('rate-planner', function (node) {
        const { body } = frame(node, 'Plan a write rate',
            'Choose how many Modbus writes to send and how far apart, then watch the two write rules of the CybICS IDS count them over the two-minute window. Both count writes from one host in a sliding window.');
        const controls = el('div');
        controls.innerHTML = `
            <div class="w-row"><label for="rp-n">Writes <b data-o="n"></b></label><input id="rp-n" type="range" min="1" max="60" value="12" data-k="n"></div>
            <div class="w-row"><label for="rp-gap">Pause between writes <b data-o="gap"></b> s</label><input id="rp-gap" type="range" min="0" max="120" value="20" data-k="gap"></div>
            <div class="w-row"><label><input type="checkbox" data-k="jitter"> real timing: each pause up to 20% shorter</label>
                <label><input type="checkbox" data-k="scan"> a quick port scan “just to check”</label></div>`;
        const timeline = el('div', { class: 'timeline', role: 'img' });
        const legend = el('div', { class: 'legend' }, '<span><i style="background:var(--bad)"></i>your write</span><span><i style="background:rgba(251,191,36,.5)"></i>alert raised</span><span>0 s → 120 s</span>');
        const score = el('div', { class: 'score', 'aria-live': 'polite' });
        const verdict = el('p', { class: 'w-note' });
        body.append(controls, timeline, legend, score, verdict);
        function paint() {
            const k = name => controls.querySelector(`[data-k=${name}]`);
            const n = Number(k('n').value), gap = Number(k('gap').value) / 10;
            controls.querySelector('[data-o=n]').textContent = n;
            controls.querySelector('[data-o=gap]').textContent = gap.toFixed(1);
            const times = [];
            let t = 2;
            for (let i = 0; i < n && t <= 120; i++) {
                times.push(t);
                // A fixed pattern instead of random numbers, so the picture is stable.
                t += gap * (k('jitter').checked ? 1 - 0.2 * ((i * 7) % 5) / 4 : 1);
            }
            const maxIn = w => Math.max(0, ...times.map(x => times.filter(y => y <= x && y >= x - w).length));
            const alerts = [];
            RATE_RULES.forEach(function (r) {
                let last = -Infinity;
                times.forEach(function (x) {
                    if (times.filter(y => y <= x && y >= x - r.w).length >= r.n && x - last >= 30) { alerts.push([x, r.rule]); last = x; }
                });
            });
            if (k('scan').checked) alerts.push([60, 'port_scan']);
            const x = v => (v / 120 * 100).toFixed(2) + '%';
            timeline.innerHTML = alerts.map(([a]) => `<div class="alarm" style="left:${x(a)};width:${x(Math.min(30, 120 - a))}"></div>`).join('') +
                times.map(v => `<div class="ev atk" style="left:${x(v)}"></div>`).join('');
            timeline.setAttribute('aria-label', `${times.length} writes in two minutes, ${alerts.length} alerts`);
            score.innerHTML = `<div><b>${times.length}</b>writes sent</div><div><b>${maxIn(30)} / 10</b>most in any 30 s</div>` +
                `<div><b>${maxIn(5)} / 50</b>most in any 5 s</div><div><b>${alerts.length}</b>alerts${alerts.length ? ': ' + [...new Set(alerts.map(a => a[1]))].join(', ') : ''}</div>`;
            const close = maxIn(30) === 9;
            verdict.innerHTML = alerts.length
                ? (k('scan').checked && alerts.length === 1 ? '<b>Your writes stayed under the rules, but the scan did not.</b> Every rule counts, not only the one you planned for.' : '<b>The IDS fires.</b> Spread the writes out, or send fewer.')
                : times.length < n ? `<b>No alert, but only ${times.length} of ${n} writes fit into the two minutes.</b> A slow attack needs time, and the window is short.`
                : close ? '<b>No alert, with no margin at all.</b> Switch on real timing: a pause that is a little short tips you over.'
                : '<b>No alert.</b> A rate rule cannot tell this from a quiet network. That is why defenders add rules without a threshold, such as alerting on the first write from a host that never writes.';
        }
        controls.addEventListener('input', paint);
        paint();
    });

    // ------------------------------------------------------------------
    // uart-frame: one character on the wire, and what a wrong baud rate reads
    // ------------------------------------------------------------------
    const BAUDS = [9600, 19200, 57600, 115200];
    register('uart-frame', function (node) {
        const { body } = frame(node, 'One character on a UART wire',
            'Type a character to see its frame: the line rests high, a start bit pulls it low, eight data bits follow with the lowest bit first, and a stop bit returns it high. CybICS uses 115200 baud, 8N1.');
        const controls = el('div', { class: 'w-row' });
        controls.innerHTML = `<label>Character <input type="text" maxlength="1" value="C" data-k="ch" style="width:3rem"></label>
            <label>Sender <select data-k="tx">${BAUDS.map(b => `<option${b === 115200 ? ' selected' : ''}>${b}</option>`).join('')}</select> baud</label>
            <label>Receiver <select data-k="rx">${BAUDS.map(b => `<option${b === 115200 ? ' selected' : ''}>${b}</option>`).join('')}</select> baud</label>`;
        const wire = el('div', { class: 'uart', role: 'img' });
        const out = el('p', { 'aria-live': 'polite' });
        body.append(controls, wire, out);
        function paint() {
            const ch = controls.querySelector('[data-k=ch]').value || ' ';
            const code = ch.charCodeAt(0) & 0xff;
            const tx = Number(controls.querySelector('[data-k=tx]').value), rx = Number(controls.querySelector('[data-k=rx]').value);
            const data = Array.from({ length: 8 }, (_, i) => (code >> i) & 1);
            const bits = [['idle', 1], ['start', 0], ...data.map((b, i) => [`bit ${i}`, b]), ['stop', 1], ['idle', 1]];
            wire.innerHTML = bits.map(([name, v]) => `<div class="u-bit ${v ? 'hi' : 'lo'}${name.startsWith('bit') ? ' data' : ''}"><span class="u-v">${v}</span><small>${name}</small></div>`).join('');
            wire.setAttribute('aria-label', `Frame of ${ch}: start bit 0, data bits ${data.join(' ')} lowest first, stop bit 1`);
            // The receiver starts timing at the falling edge of the start bit and
            // samples each data bit in the middle of where it expects it.
            const level = t => { const i = Math.floor(t * tx); return i < 1 ? 0 : i <= 8 ? data[i - 1] : 1; };
            let got = 0;
            for (let i = 0; i < 8; i++) got |= level((1.5 + i) / rx) << i;
            const stopOk = level(9.5 / rx) === 1;
            const show = c => (c >= 32 && c < 127 ? `“${escapeHtml(String.fromCharCode(c))}”` : 'an unprintable byte');
            const bitUs = (1e6 / tx).toFixed(2);
            out.innerHTML = `Each bit lasts ${bitUs} µs at ${tx} baud; a whole character (10 bits) takes ${(10e6 / tx).toFixed(1)} µs.<br>` +
                (tx === rx ? `The receiver reads <b>${show(got)}</b> (0x${hex(got, 2)}), as sent.`
                : `The receiver reads <b>${show(got)}</b> (0x${hex(got, 2)}) instead of ${show(code)}${stopOk ? '' : ', and the stop bit is wrong (a framing error)'}. This garbage is the sign of a wrong baud rate: try the usual rates until the text becomes readable.`);
        }
        controls.addEventListener('input', paint);
        controls.addEventListener('change', paint);
        paint();
    });

    // ------------------------------------------------------------------
    // plant-predict: say what the plant will do, then watch it happen
    // ------------------------------------------------------------------
    // Read-only, like plant-live: the reader predicts from the state of the
    // compressor and the valve, and the real plant answers.
    const PREDICT_SECONDS = 20;
    register('plant-predict', function (node) {
        const { body } = frame(node, 'Predict, then watch the real plant',
            `Look at the plant as it is now and predict what the HPT pressure will do over the next ${PREDICT_SECONDS} seconds. Then the live plant gives the answer.`);
        const now = el('div', { class: 'score', 'aria-live': 'polite' }, '<div><b>…</b>connecting</div>');
        const choices = el('div', { class: 'w-row' });
        [['up', 'It will rise'], ['down', 'It will fall'], ['flat', 'It will stay about the same']].forEach(function ([k, label]) {
            const b = el('button', { class: 't-btn', type: 'button', 'data-k': k }, label);
            choices.appendChild(b);
        });
        const out = el('p', { 'aria-live': 'polite' });
        body.append(now, choices, out);
        let start = null, timer = null;
        const read = () => fetch('/theory/api/plant').then(r => r.json()).then(d => { if (!d.ok) throw new Error('offline'); return d.values; });
        const pill = (on, a, b) => `<span class="w-pill ${on ? 'on' : 'off'}">${on ? a : b}</span>`;
        function show(v) {
            now.innerHTML = `<div><b>${v.hpt} bar</b>HPT now</div><div><b>${pill(v.compressor, 'running', 'off')}</b>compressor</div>` +
                `<div><b>${pill(v.systemValve, 'open', 'closed')}</b>system valve</div><div><b>${v.gst} bar</b>GST</div>`;
        }
        function refresh() {
            if (start) return;
            read().then(show).catch(function () {
                now.innerHTML = '<div><b>–</b>plant not reachable</div>';
                out.textContent = 'This needs the running CybICS stack.';
            });
        }
        refresh();
        timer = setInterval(refresh, 2000);
        window.addEventListener('pagehide', () => clearInterval(timer));
        choices.addEventListener('click', function (e) {
            const guess = e.target.dataset && e.target.dataset.k;
            if (!guess || start) return;
            read().then(function (v) {
                start = v;
                show(v);
                choices.querySelectorAll('button').forEach(b => { b.disabled = true; b.classList.toggle('primary', b === e.target); });
                let left = PREDICT_SECONDS;
                out.textContent = `Watching… ${left} s`;
                const tick = setInterval(function () {
                    left -= 1;
                    if (left > 0) { out.textContent = `Watching… ${left} s`; return; }
                    clearInterval(tick);
                    read().then(function (end) {
                        show(end);
                        const delta = end.hpt - start.hpt;
                        const real = delta >= 3 ? 'up' : delta <= -3 ? 'down' : 'flat';
                        // The same cases as the plant model in hwio-virtual.
                        const vent = start.boSen ? ' The blow-out valve was open (it opens above 220 bar and closes at 200) and vented about half a bar a second.' : '';
                        const why = start.compressor && start.gst < 50
                            ? 'The compressor was on, but the GST held less than 50 bar, too little to push against, so it moved no gas.' + vent
                            : start.compressor
                                ? 'The compressor was running, so it pushed gas from the GST into the HPT, about 1 bar a second.' + (vent && ' The open blow-out valve only slowed the rise.')
                                : start.systemValve
                                    ? 'The compressor was off and the system valve open, so the consumer drew gas out of the HPT, about 1 bar a second on average.' + vent
                                    : 'The compressor was off and the system valve closed, so no gas went in and the consumer took none out.' + vent;
                        out.innerHTML = `<b class="${real === guess ? 'w-ok' : 'w-err'}">${real === guess ? 'Right.' : 'Not this time.'}</b> ` +
                            `The HPT went from ${start.hpt} to ${end.hpt} bar. ${escapeHtml(why)} ` +
                            (end.compressor !== start.compressor ? `Meanwhile the compressor was switched ${end.compressor ? 'on' : 'off'}. In automatic mode that is the PLC reacting to its limits (it starts the compressor below 60 bar and stops it at 90); in manual mode it was the operator. ` : '') +
                            '<button class="t-btn" type="button" data-again>Try again</button>';
                        out.querySelector('[data-again]').addEventListener('click', function () {
                            start = null; out.textContent = '';
                            choices.querySelectorAll('button').forEach(b => { b.disabled = false; b.classList.remove('primary'); });
                            refresh();
                        });
                    }).catch(function () { out.textContent = 'The plant stopped answering.'; start = null; });
                }, 1000);
            }).catch(function () { out.textContent = 'The plant is not reachable; this needs the running CybICS stack.'; });
        });
    });
})();
