// EqualPlay AI — frontend for the FastAPI replay API.
// For local development, serve this folder on port 5500 (see README).
const API_BASE = 'http://127.0.0.1:8000';
const $ = (id) => document.getElementById(id);
const MAX_MINUTE = 90;
const TICK_MS = 900;
let minute = 0;
let playing = false;
let timer = null;
let mode = 'visual';
let latestState = null;
let requestSequence = 0;
let lastAnnouncedEventId = null;
let hasLoaded = false;

const STATS = [
  ['Possession', 'possession', '%'],
  ['Shots', 'shots', ''],
  ['Shots on target', 'shots_on_target', ''],
  ['Expected goals (xG)', 'xg', ''],
  ['Pass accuracy', 'pass_accuracy', '%'],
  ['Corners', 'corners', ''],
  ['Fouls', 'fouls', ''],
  ['Yellow cards', 'yellow_cards', ''],
  ['Tackles', 'tackles', ''],
  ['Interceptions', 'interceptions', ''],
];

function safeText(value, fallback = '—') {
  return value === null || value === undefined ? fallback : String(value);
}
function eventDescription(event, simple = false) {
  const team = event.team_id === 'HOME' ? 'London City FC' : 'Manchester Royals';
  const type = event.event_type;
  if (type === 'shot' && event.outcome === 'goal') return simple ? `${team} scored a goal.` : `GOAL! ${team} scores! The match changes in the ${event.minute}th minute.`;
  if (type === 'shot') return simple ? `${team} took a shot.` : `${team} takes a shot — ${String(event.outcome || 'attempt').replaceAll('_', ' ')}.`;
  if (type === 'yellow_card') return simple ? `A ${team} player got a yellow card.` : `Yellow card shown to ${team}.`;
  if (type === 'red_card') return simple ? `A ${team} player got a red card.` : `Red card! ${team} will have to adjust.`;
  if (type === 'corner') return `${team} wins a corner.`;
  return `${team}: ${type.replaceAll('_', ' ')}.`;
}
function isImportant(event) {
  return event.event_type === 'shot' || event.event_type === 'corner' || event.event_type === 'yellow_card' || event.event_type === 'red_card';
}
function updateStats(stats) {
  const home = stats?.HOME || {};
  const away = stats?.AWAY || {};
  $('stats-list').replaceChildren();
  for (const [label, key, suffix] of STATS) {
    const h = home[key], a = away[key];
    const hNumber = Number(h) || 0, aNumber = Number(a) || 0;
    const total = hNumber + aNumber;
    const hWidth = total > 0 ? 100 * hNumber / total : 50;
    const row = document.createElement('div'); row.className = 'stat';
    const values = document.createElement('div'); values.className = 'stat-values';
    const hValue = document.createElement('span'); hValue.textContent = `${safeText(h)}${h == null ? '' : suffix}`;
    const title = document.createElement('span'); title.className = 'stat-label'; title.textContent = label;
    const aValue = document.createElement('span'); aValue.textContent = `${safeText(a)}${a == null ? '' : suffix}`;
    values.append(hValue, title, aValue);
    const track = document.createElement('div'); track.className = 'stat-track'; track.setAttribute('aria-hidden', 'true');
    const hBar = document.createElement('div'); hBar.className = 'stat-home'; hBar.style.width = `${hWidth}%`;
    const aBar = document.createElement('div'); aBar.className = 'stat-away'; aBar.style.width = `${100 - hWidth}%`;
    track.append(hBar, aBar); row.append(values, track); $('stats-list').append(row);
  }
}
function render(state) {
  latestState = state;
  const currentMinute = state.minute ?? minute;
  $('minute-display').textContent = `${currentMinute}'`;
  $('stats-minute').textContent = `${currentMinute}'`;
  $('slider-value').textContent = `${currentMinute} / 90 min`;
  $('minute-slider').value = currentMinute;
  $('match-state').textContent = currentMinute === 90 ? 'FULL TIME' : currentMinute === 0 ? 'KICKOFF' : 'MATCH REPLAY';
  $('home-name').textContent = state.teams?.HOME?.name || 'London City FC';
  $('away-name').textContent = state.teams?.AWAY?.name || 'Manchester Royals';
  $('home-score').textContent = state.score?.HOME ?? 0;
  $('away-score').textContent = state.score?.AWAY ?? 0;
  updateStats(state.stats);
  const events = (state.key_events || []).filter(isImportant);
  const latest = events.at(-1);
  const featured = $('featured-event'); featured.replaceChildren();
  const time = document.createElement('span'); time.className = 'event-minute'; time.textContent = `${latest?.minute ?? currentMinute}'`;
  const p = document.createElement('p'); p.textContent = latest ? eventDescription(latest, mode === 'simple') : 'Ready for kickoff. Press Play to experience the match.';
  featured.append(time, p);
  const feed = $('event-feed'); feed.replaceChildren();
  if (!events.length) { const li = document.createElement('li'); li.textContent = 'No major events yet.'; feed.append(li); }
  for (const event of events.slice(-12).reverse()) {
    const li = document.createElement('li');
    const stamp = document.createElement('strong'); stamp.textContent = `${event.minute}'`;
    li.append(stamp, document.createTextNode(eventDescription(event, mode === 'simple'))); feed.append(li);
  }
  if (latest && playing && latest.event_id !== lastAnnouncedEventId) {
    lastAnnouncedEventId = latest.event_id;
    if (latest.event_type === 'shot' && latest.outcome === 'goal' || latest.event_type === 'red_card') {
      $('announcement').textContent = eventDescription(latest, mode === 'simple');
    }
    if (mode === 'audio') speak(eventDescription(latest));
  }
}
async function fetchReplay(nextMinute) {
  const seq = ++requestSequence;
  try {
    const response = await fetch(`${API_BASE}/api/replay?minute=${nextMinute}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (seq !== requestSequence) return;
    $('connection').textContent = '● API connected';
    minute = nextMinute;
    render(data);
    hasLoaded = true;
  } catch (err) {
    if (seq !== requestSequence) return;
    $('connection').textContent = '● API unavailable';
    $('featured-event').querySelector('p').textContent = `Could not connect to FastAPI (${err.message}). Start uvicorn and check /api/replay.`;
    pause();
  }
}
function speak(text) {
  if (!('speechSynthesis' in window)) { $('announcement').textContent = 'Speech synthesis is unavailable in this browser.'; return; }
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.lang = 'en-GB';
  speechSynthesis.speak(utterance);
}
function pause() { playing = false; clearInterval(timer); timer = null; $('play-button').textContent = '▶ Play match'; }
function play() {
  if (minute >= MAX_MINUTE) { minute = 0; lastAnnouncedEventId = null; fetchReplay(0); }
  playing = true; $('play-button').textContent = '❚❚ Pause';
  timer = setInterval(() => {
    if (minute >= MAX_MINUTE) { pause(); return; }
    fetchReplay(minute + 1);
  }, TICK_MS);
}
$('play-button').addEventListener('click', () => playing ? pause() : play());
$('reset-button').addEventListener('click', () => { pause(); speechSynthesis?.cancel?.(); lastAnnouncedEventId = null; fetchReplay(0); });
$('minute-slider').addEventListener('input', (event) => { pause(); speechSynthesis?.cancel?.(); lastAnnouncedEventId = null; fetchReplay(Number(event.target.value)); });
$('speak-button').addEventListener('click', () => { if (latestState) { const events = (latestState.key_events || []).filter(isImportant); const latest = events.at(-1); speak(latest ? eventDescription(latest, mode === 'simple') : 'The match is ready for kickoff.'); } });
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => {
  mode = button.dataset.mode;
  document.body.classList.toggle('simple-mode', mode === 'simple');
  document.body.classList.toggle('audio-mode', mode === 'audio');
  document.querySelectorAll('[data-mode]').forEach(b => { const active = b === button; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
  if (mode !== 'audio' && 'speechSynthesis' in window) speechSynthesis.cancel();
  if (latestState) render(latestState);
}));
fetchReplay(0);
