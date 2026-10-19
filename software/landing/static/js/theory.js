/* Theory Path lessons: table of contents, glossary terms, checkpoints, the
   quiz, and the registry the interactive widgets (theory-widgets.js) mount
   through. Everything is progressive: without JavaScript the article, the
   objectives and the takeaways still read in full. */
(function () {
    'use strict';

    const dataEl = document.getElementById('theory-data');
    const DATA = dataEl ? JSON.parse(dataEl.textContent) : { quiz: [], checkpoints: [], glossary: [] };

    function escapeHtml(text) {
        return String(text).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }
    // Question texts are plain strings; `backticks` become code.
    function inline(text) {
        return escapeHtml(text).replace(/`([^`]+)`/g, '<code>$1</code>');
    }
    function el(tag, attrs, html) {
        const node = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) {
            if (k === 'class') node.className = v; else node.setAttribute(k, v);
        }
        if (html !== undefined) node.innerHTML = html;
        return node;
    }

    // ---- Widget registry ----
    const widgets = {};
    window.TheoryWidgets = {
        register(name, mount) { widgets[name] = mount; },
        util: { el, escapeHtml, inline },
        challenges: DATA.challenges || {},
        // Per-lesson data for widgets that need more than a few attributes,
        // from "exercises" in the sidecar, keyed by the widget's data-id.
        exercises: DATA.exercises || {},
    };
    function mountWidgets() {
        document.querySelectorAll('.article [data-widget]').forEach(function (node) {
            const name = node.dataset.widget;
            if (name === 'checkpoint') return mountCheckpoint(node);
            const mount = widgets[name];
            if (!mount) return;
            try { mount(node); } catch (e) {
                node.innerHTML = '<p class="w-err">This interactive example could not be loaded.</p>';
                console.error('widget ' + name, e);
            }
        });
    }

    // ---- Questions (shared by checkpoints and the quiz) ----
    function renderQuestion(q, index, prefix) {
        const multi = q.type === 'multi';
        const box = el('div', { class: 'q', role: 'group', 'aria-labelledby': `${prefix}-q${index}` });
        box.appendChild(el('div', { class: 'q-text', id: `${prefix}-q${index}` }, inline(q.question)));
        if (multi) box.appendChild(el('div', { class: 'q-hint' }, 'Select all that apply.'));
        const options = el('div', { class: 'q-options' });
        // Shown in a new order on every visit, so the position of the right
        // answer gives nothing away. Each input keeps its option's index in
        // the sidecar, which is what the server grades.
        const order = q.options.map((_, i) => i);
        for (let i = order.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [order[i], order[j]] = [order[j], order[i]];
        }
        // "True, False" reads oddly the other way round.
        if (q.options.length === 2 && /^(true|yes)$/i.test(q.options[0])) order.sort();
        order.forEach(function (i) {
            const option = q.options[i];
            const label = el('label', { class: 'q-option' });
            const input = el('input', { type: multi ? 'checkbox' : 'radio', name: `${prefix}-${index}`, value: String(i) });
            label.appendChild(input);
            label.appendChild(el('span', {}, inline(option)));
            options.appendChild(label);
        });
        box.appendChild(options);
        box.appendChild(el('div', { class: 'q-feedback', 'aria-live': 'polite' }));
        return box;
    }
    function selected(box) {
        const picked = [...box.querySelectorAll('input:checked')].map(i => Number(i.value));
        return box.querySelector('input[type=checkbox]') ? picked : (picked.length ? picked[0] : null);
    }
    function isCorrect(q, answer) {
        if (Array.isArray(q.answer)) {
            return Array.isArray(answer) && answer.length === q.answer.length && q.answer.every(a => answer.includes(a));
        }
        return answer === q.answer;
    }
    function grade(box, q) {
        const answer = selected(box);
        const ok = isCorrect(q, answer);
        const expected = Array.isArray(q.answer) ? q.answer : [q.answer];
        const given = Array.isArray(answer) ? answer : (answer === null ? [] : [answer]);
        box.querySelectorAll('.q-option').forEach(function (label) {
            const i = Number(label.querySelector('input').value);
            label.classList.toggle('correct', expected.includes(i) && given.includes(i));
            label.classList.toggle('wrong', !expected.includes(i) && given.includes(i));
            label.classList.toggle('missed', expected.includes(i) && !given.includes(i));
            label.querySelector('input').disabled = true;
        });
        box.classList.add('graded');
        const feedback = box.querySelector('.q-feedback');
        feedback.className = 'q-feedback show ' + (ok ? 'ok' : 'bad');
        feedback.innerHTML = `<b>${ok ? 'Correct.' : (given.length ? 'Not quite.' : 'No answer given.')}</b>${inline(q.explanation)}`;
        return { ok, answer };
    }
    function ungrade(box) {
        box.classList.remove('graded');
        box.querySelectorAll('.q-option').forEach(function (label) {
            label.classList.remove('correct', 'wrong', 'missed');
            const input = label.querySelector('input');
            input.disabled = false; input.checked = false;
        });
        box.querySelector('.q-feedback').className = 'q-feedback';
    }

    // A checkpoint is practice, not a test: the reader picks, presses Check,
    // reads the explanation and may try again. Nothing is recorded.
    function mountCheckpoint(node) {
        const q = (DATA.checkpoints || []).find(c => c.id === node.dataset.id);
        if (!q) return;
        const box = renderQuestion(q, 0, 'cp-' + q.id);
        box.insertBefore(el('div', { class: 'q-eyebrow' }, 'Quick check'), box.firstChild);
        node.replaceWith(box);
        const actions = el('div', { class: 'q-actions' });
        const check = el('button', { class: 't-btn', type: 'button', disabled: '' }, 'Check');
        const retry = el('button', { class: 't-btn', type: 'button', hidden: '' }, 'Try again');
        actions.append(check, retry);
        box.insertBefore(actions, box.querySelector('.q-feedback'));
        box.addEventListener('change', function () { check.disabled = !box.querySelector('input:checked'); });
        check.addEventListener('click', function () {
            const { ok } = grade(box, q);
            check.hidden = true;
            retry.hidden = ok;
        });
        retry.addEventListener('click', function () {
            ungrade(box);
            check.hidden = false; check.disabled = true; retry.hidden = true;
        });
    }

    function mountQuiz() {
        const holder = document.getElementById('quiz-questions');
        if (!holder || !DATA.quiz.length) return;
        const boxes = DATA.quiz.map((q, i) => holder.appendChild(renderQuestion(q, i, 'quiz')));
        boxes.forEach(function (box, i) {
            box.querySelector('.q-text').insertAdjacentHTML('afterbegin', `<span class="q-eyebrow">Question ${i + 1} of ${boxes.length}</span><br>`);
        });
        const check = document.getElementById('quiz-check');
        const retry = document.getElementById('quiz-retry');
        const result = document.getElementById('quiz-result');
        // The page has no answers: the board grades the attempt, records it
        // and only then sends back the right answers and the explanations.
        check.addEventListener('click', function () {
            const unanswered = boxes.filter(b => !b.querySelector('input:checked')).length;
            if (unanswered && !confirm(`${unanswered} question(s) have no answer yet. Check anyway?`)) return;
            const answers = boxes.map(selected);
            check.disabled = true;
            fetch(`/theory/api/progress/${encodeURIComponent(DATA.topic)}`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers }),
            }).then(function (r) {
                if (!r.ok) throw new Error(r.status);
                return r.json();
            }).then(function (entry) {
                boxes.forEach((box, i) => grade(box, { ...DATA.quiz[i], ...entry.results[i] }));
                const passed = entry.correct / entry.total >= DATA.passRatio;
                result.className = 'quiz-result ' + (passed ? 'ok' : 'bad');
                result.textContent = `${entry.correct} of ${entry.total} correct. ` +
                    (passed ? 'Lesson completed!' : `You need ${Math.ceil(DATA.passRatio * entry.total)} to complete it; read the explanations and try again.`);
                if (entry.passed) {
                    const status = document.getElementById('status');
                    status.classList.add('done'); status.textContent = '✓ Completed';
                }
                check.hidden = true; retry.hidden = false;
                const first = boxes.find(b => b.querySelector('.q-feedback.bad'));
                (first || result).scrollIntoView({ behavior: 'smooth', block: 'center' });
            }).catch(function () {
                result.className = 'quiz-result bad';
                result.textContent = 'Your answers could not be checked: the board did not answer. Try again in a moment.';
            }).finally(function () { check.disabled = false; });
        });
        retry.addEventListener('click', function () {
            boxes.forEach(ungrade);
            result.textContent = '';
            check.hidden = false; retry.hidden = true;
            boxes[0].scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    }

    // ---- Table of contents ----
    function mountToc() {
        const toc = document.getElementById('toc');
        if (!toc) return;
        if (matchMedia('(max-width: 1099px)').matches) toc.open = false;
        const links = [...toc.querySelectorAll('a')];
        const targets = links.map(a => document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
        if (!('IntersectionObserver' in window)) return;
        const visible = new Map();
        const observer = new IntersectionObserver(function (entries) {
            entries.forEach(e => visible.set(e.target.id, e.isIntersecting));
            const current = targets.find(t => visible.get(t.id));
            if (!current) return;
            links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + current.id));
        }, { rootMargin: '-70px 0px -60% 0px' });
        targets.forEach(t => observer.observe(t));
    }

    // ---- Glossary: the first use of each term in the article explains itself ----
    function mountGlossary() {
        const entries = (DATA.glossary || []).flatMap(function (entry) {
            return [entry.term, ...(entry.aliases || [])].map(name => ({ name, entry }));
        }).sort((a, b) => b.name.length - a.name.length);
        if (!entries.length) return;
        const article = document.getElementById('article');
        const skip = 'code, pre, svg, h1, h2, h3, h4, a, button, summary, .w, .q, .t-box, figcaption, table';
        const done = new Set();
        const walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT, {
            acceptNode: n => (n.parentElement.closest(skip) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
        });
        const nodes = [];
        while (walker.nextNode()) nodes.push(walker.currentNode);
        const pattern = name => new RegExp(`(^|[^\\w-])(${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?![\\w-])`,
            /^[A-Z0-9/&-]+$/.test(name) ? '' : 'i');
        const regexes = entries.map(e => ({ ...e, re: pattern(e.name) }));
        nodes.forEach(function (node) {
            for (const { entry, re } of regexes) {
                if (done.has(entry.term)) continue;
                const m = re.exec(node.nodeValue);
                if (!m) continue;
                done.add(entry.term);
                const start = m.index + m[1].length;
                const after = node.splitText(start);
                after.nodeValue = after.nodeValue.slice(m[2].length);
                const button = el('button', { class: 'term', type: 'button', 'aria-expanded': 'false' });
                button.textContent = m[2];
                button.dataset.term = entry.term;
                // Keep "(term)" or "term," on one line: the button is a box of
                // its own, and the line could otherwise break between them.
                const wrap = el('span', { class: 'term-wrap' });
                node.parentNode.insertBefore(wrap, after);
                if (/[(\["“‘]$/.test(node.nodeValue)) {
                    wrap.appendChild(document.createTextNode(node.nodeValue.slice(-1)));
                    node.nodeValue = node.nodeValue.slice(0, -1);
                }
                wrap.appendChild(button);
                const tail = /^[)\],.;:!?”’'"]+/.exec(after.nodeValue);
                if (tail) {
                    wrap.appendChild(document.createTextNode(tail[0]));
                    after.nodeValue = after.nodeValue.slice(tail[0].length);
                }
                break;  // one term per text node keeps the offsets simple
            }
        });
        let pop = null;
        function close() { if (pop) { pop.owner.setAttribute('aria-expanded', 'false'); pop.remove(); pop = null; } }
        function open(button) {
            close();
            const entry = DATA.glossary.find(e => e.term === button.dataset.term);
            pop = el('div', { class: 'term-pop', role: 'tooltip' },
                `<strong>${escapeHtml(entry.term)}</strong>${inline(entry.definition)}` +
                (entry.link ? `<br><a href="${escapeHtml(entry.link)}">Read more &rarr;</a>` : ''));
            pop.owner = button;
            document.body.appendChild(pop);
            const r = button.getBoundingClientRect();
            const left = Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - pop.offsetWidth - 12);
            pop.style.left = Math.max(8, left) + 'px';
            pop.style.top = (window.scrollY + r.bottom + 6) + 'px';
            button.setAttribute('aria-expanded', 'true');
        }
        article.addEventListener('click', function (e) {
            const button = e.target.closest('.term');
            if (!button) return;
            e.stopPropagation();
            if (pop && pop.owner === button) close(); else open(button);
        });
        document.addEventListener('click', e => { if (pop && !pop.contains(e.target)) close(); });
        document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    }

    // ---- Figures that are wider than the screen say so ----
    function markScrollingFigures() {
        document.querySelectorAll('.article figure').forEach(function (fig) {
            fig.classList.toggle('scrolls', fig.scrollWidth > fig.clientWidth + 4);
        });
    }

    // ---- The core path keeps its own Previous and Next ----
    function choosePager() {
        const core = document.getElementById('pager-core');
        if (!core) return;
        let coreOnly = false;
        try { coreOnly = localStorage.getItem('cybics-theory-core') === '1'; } catch (e) {}
        core.hidden = !coreOnly;
        document.getElementById('pager').hidden = coreOnly;
    }

    document.addEventListener('DOMContentLoaded', function () {
        choosePager();
        mountWidgets();
        mountQuiz();
        mountToc();
        mountGlossary();
        markScrollingFigures();
        window.addEventListener('resize', markScrollingFigures);
    });
})();
