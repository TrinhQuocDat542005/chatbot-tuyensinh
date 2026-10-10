// Deliberately limited Markdown: text, emphasis, links, bullets and score tables.
// All content becomes DOM text; HTML from a message is never executed.
export function safeLink(value) {
  try {
    const url = new URL(value);
    return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

export function appendInline(target, text) {
  const pattern = /\[([^\]\n]+)\]\(([^\s)]+)\)|\*\*([^*\n]+)\*\*|https?:\/\/[^\s<>]+/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    target.append(document.createTextNode(text.slice(cursor, match.index)));
    if (match[3]) {
      const strong = document.createElement('strong');
      strong.textContent = match[3]; target.append(strong);
    } else {
      const raw = match[2] || match[0].replace(/[.,;)]+$/, '');
      const url = safeLink(raw);
      if (url) {
        const link = document.createElement('a');
        link.href = url; link.textContent = match[1] || new URL(url).hostname + ' ↗';
        link.target = '_blank'; link.rel = 'noopener noreferrer'; target.append(link);
        if (!match[2]) target.append(document.createTextNode(match[0].slice(raw.length)));
      } else target.append(document.createTextNode(match[0]));
    }
    cursor = match.index + match[0].length;
  }
  target.append(document.createTextNode(text.slice(cursor)));
}

export function renderAnswer(target, text) {
  const lines = String(text).split('\n');
  let list = null, scoreTable = null;
  for (const line of lines) {
    const score = line.match(/^\s*-?\s*([A-D]\d{2}):\s*([\d.,]+)\/30\s*$/);
    if (score) {
      if (!scoreTable) {
        scoreTable = document.createElement('table'); scoreTable.className = 'score-table';
        const caption = document.createElement('caption'); caption.textContent = 'Tổng điểm tổ hợp THPT';
        const head = document.createElement('thead'), row = document.createElement('tr');
        for (const label of ['Tổ hợp', 'Điểm / 30']) { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; row.append(th); }
        head.append(row); scoreTable.append(caption, head, document.createElement('tbody')); target.append(scoreTable);
      }
      const row = document.createElement('tr');
      for (const value of [score[1], score[2]]) { const td = document.createElement('td'); td.textContent = value; row.append(td); }
      scoreTable.tBodies[0].append(row); list = null; continue;
    }
    scoreTable = null;
    if (line.trim().startsWith('- ')) {
      if (!list) { list = document.createElement('ul'); target.append(list); }
      const li = document.createElement('li'); appendInline(li, line.trim().slice(2)); list.append(li); continue;
    }
    list = null;
    if (!line.trim()) continue;
    const paragraph = document.createElement('p');
    if (/^Nguồn:/i.test(line)) { paragraph.className = 'source-links'; target.classList.add('source-note'); }
    appendInline(paragraph, line); target.append(paragraph);
  }
}
