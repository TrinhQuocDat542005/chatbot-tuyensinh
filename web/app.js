import { renderAnswer } from './render.js';

const $ = (id) => document.getElementById(id);
let sender = crypto.randomUUID(), busy = false;
const controls = [$('send'), $('new-session'), ...document.querySelectorAll('[data-question]')];

function notice(text = '') { $('notice').textContent = text; $('notice').hidden = !text; }
function scrollEnd() { $('conversation-scroll').scrollTop = $('conversation-scroll').scrollHeight; }
function setBusy(value) { busy = value; for (const button of controls) button.disabled = value; $('chat-form').setAttribute('aria-busy', String(value)); }
function draft(text) { $('message').value = text; $('message').focus(); resize(); }
function resize() { $('message').style.height = 'auto'; $('message').style.height = Math.min($('message').scrollHeight, 140) + 'px'; }

function row(kind, text) {
  const element = document.createElement('article'); element.className = 'message-row ' + kind;
  const avatar = document.createElement('div'); avatar.className = 'avatar'; avatar.setAttribute('aria-hidden', 'true'); avatar.textContent = kind === 'user' ? 'B' : 'u.';
  const body = document.createElement('div'); body.className = 'message-body';
  const label = document.createElement('p'); label.className = 'message-label'; label.textContent = kind === 'user' ? 'BẠN' : 'TRỢ LÝ UTH';
  const card = document.createElement('div'); card.className = 'message-card';
  if (kind === 'user') card.textContent = text; else renderAnswer(card, text);
  body.append(label, card); element.append(avatar, body); $('messages').append(element); scrollEnd();
  return { element, body, card };
}

async function api(path, payload) {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: AbortSignal.timeout(65000) });
  if (!response.ok) throw new Error('Không thể kết nối trợ lý.');
  return response.json();
}

function feedback(body, messageId) {
  const group = document.createElement('div'); group.className = 'feedback';
  const label = document.createElement('span'); label.textContent = 'Câu trả lời có hữu ích không?'; group.append(label);
  for (const [vote, title] of [[true, 'Hữu ích'], [false, 'Chưa hữu ích']]) {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = title; button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', async () => {
      const buttons = group.querySelectorAll('button'); buttons.forEach((b) => { b.disabled = true; });
      try {
        await api('/api/feedback', { message_id: messageId, helpful: vote });
        button.setAttribute('aria-pressed', 'true'); label.textContent = 'Đã ghi nhận phản hồi. Cảm ơn bạn!';
      } catch { buttons.forEach((b) => { b.disabled = false; }); notice('Chưa gửi được phản hồi. Bạn có thể thử lại.'); }
    });
    group.append(button);
  }
  body.append(group);
}

async function send(text, messageId = crypto.randomUUID(), retryRow = null) {
  if (busy || !text.trim()) return;
  setBusy(true); notice(); $('welcome').hidden = true;
  if (!retryRow) row('user', text);
  else retryRow.element.remove();
  const loading = row('assistant', 'Trợ lý đang tìm thông tin…'); loading.card.classList.add('typing');
  try {
    const result = await api('/api/chat', { sender, message: text, message_id: messageId });
    loading.element.remove();
    const replies = result.messages.filter((m) => typeof m.text === 'string' && m.text.trim());
    if (!replies.length) throw new Error('Không có câu trả lời.');
    for (const reply of replies) {
      const answer = row('assistant', reply.text);
      feedback(answer.body, crypto.randomUUID());
    }
    scrollEnd();
  } catch {
    loading.element.remove();
    const failed = row('assistant', 'Chưa nhận được phản hồi từ trợ lý. Câu hỏi và lịch sử của bạn vẫn ở đây.');
    failed.card.classList.add('error-card');
    const retry = document.createElement('button'); retry.className = 'retry'; retry.type = 'button'; retry.textContent = 'Thử gửi lại';
    retry.addEventListener('click', () => send(text, messageId, failed)); failed.card.append(retry); scrollEnd();
  } finally { setBusy(false); $('message').focus(); }
}

$('chat-form').addEventListener('submit', (event) => {
  event.preventDefault(); if (busy) return;
  const text = $('message').value.trim();
  if (!text) return; $('message').value = ''; resize(); send(text);
});
$('message').addEventListener('input', resize);
$('message').addEventListener('keydown', (event) => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('chat-form').requestSubmit(); } });
document.querySelectorAll('[data-question]').forEach((button) => button.addEventListener('click', () => draft(button.dataset.question)));
$('new-session').addEventListener('click', () => {
  if (busy) return; sender = crypto.randomUUID(); $('messages').replaceChildren(); $('welcome').hidden = false;
  $('message').value = ''; $('major').value = ''; notice('Đã bắt đầu phiên mới. Ngành, năm và điểm của phiên trước không được dùng lại.'); resize(); $('message').focus();
});
for (const [id, question] of [['major-intro', 'giới thiệu ngành'], ['major-cutoff', 'điểm chuẩn ngành']]) {
  $(id).addEventListener('click', () => {
    if (!$('major').value) { notice('Chọn một ngành trước khi tra cứu nhé.'); $('major').focus(); return; }
    notice(); draft(question + ' ' + $('major').value + (id === 'major-cutoff' ? ' năm ' + $('year').value : ''));
  });
}

async function health() {
  let online = false;
  try { const response = await fetch('/api/health', { signal: AbortSignal.timeout(7000) }); online = response.ok && (await response.json()).ready; } catch { /* Status remains offline, history is untouched. */ }
  $('connection').className = 'connection ' + (online ? 'online' : 'offline');
  $('connection-text').textContent = online ? 'Trợ lý sẵn sàng' : 'Chưa kết nối trợ lý';
}
async function catalog() {
  try {
    const response = await fetch('/api/majors', { signal: AbortSignal.timeout(7000) }); if (!response.ok) throw new Error();
    const data = await response.json(); $('major').replaceChildren(new Option('Chọn ngành bạn quan tâm', ''));
    for (const major of data.majors) $('major').append(new Option(major.name, major.name));
    $('catalog-note').textContent = 'Danh mục kiểm tra ' + data.checked_at + '. Chọn ngành để điền câu hỏi.';
  } catch { $('major').replaceChildren(new Option('Danh mục chưa sẵn sàng', '')); $('catalog-note').textContent = 'Bạn vẫn có thể nhập tên ngành trong câu hỏi.'; }
}
health(); catalog(); setInterval(health, 30000);
