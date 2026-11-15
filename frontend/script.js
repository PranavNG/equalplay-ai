// EqualPlay AI — frontend for the FastAPI replay API.
// For local development, serve this folder on port 5500 (see README).
const API_BASE = 'http://127.0.0.1:8000';
const $ = (id) => document.getElementById(id);
const MAX_MINUTE = 90;
let tickMs = 3000;
let highlightMinutes = [];
let commentaryEvents = [];
let commentaryIndex = -1;
let keyEventIds = new Set();
let commentaryReady = false;
let currentCommentary = null;
let highlightLoaded = false;
let speechPromise = Promise.resolve();
let playbackGeneration = 0;
let replayBusy = false;
let minute = 0;
let allKeyMoments = [];
let playing = false;
let timer = null;
let cancelPlaybackWait = null;
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
  const team = latestState?.teams?.[event.team_id]?.name || (event.team_id === 'HOME' ? 'Chelsea' : 'Manchester City');
  const player = event.player_name || 'The player';
  const type = event.event_type;
  if (type === 'shot' && event.outcome === 'goal') return simple ? `${player} scored for ${team}.` : `GOOOAL! ${player} finds the net for ${team}! What a moment in this match!`;
  if (type === 'shot') {
    if (simple) return `${player} took a shot for ${team}.`;
    const endings = {saved:`The keeper makes the save!`, blocked:`But the effort is blocked!`, off_target:`Oh, it's off target!`};
    return `${player} goes for goal for ${team}! ${endings[event.outcome] || 'The chance does not result in a goal.'}`;
  }
  if (type === 'yellow_card') return simple ? `A ${team} player received a yellow card.` : `The referee reaches for a yellow card! A booking for ${team}.`;
  if (type === 'red_card') return simple ? `A ${team} player received a red card.` : `Oh, that's a red card! ${team} are down a player!`;
  if (type === 'corner') return simple ? `${team} won a corner.` : `${team} push forward and win a corner. Can they make this count?`;
  return `${team}: ${String(type || 'event').replaceAll('_',' ')}.`;
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
  $('match-state').textContent = currentMinute >= 90 ? 'FULL TIME' : currentMinute === 45 ? 'HALF-TIME' : currentMinute === 0 ? 'KICKOFF' : currentMinute < 45 ? 'FIRST HALF' : 'SECOND HALF';
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
    if ((latest.event_type === 'shot' && latest.outcome === 'goal') || latest.event_type === 'red_card') {
      $('announcement').textContent = eventDescription(latest, true);
    }
    if (mode === 'audio' && !commentaryReady) speechPromise = speak(eventDescription(latest));
  }
  if (currentMinute === 45 || (currentMinute === 46 && playing)) {
    const home = state.teams?.HOME?.name || 'Chelsea';
    const away = state.teams?.AWAY?.name || 'Manchester City';
    const score = `${state.score?.HOME ?? 0} to ${state.score?.AWAY ?? 0}`;
    const message = currentMinute === 45
      ? `Half-time! ${home} ${score} ${away}. We'll be back for the second half.`
      : `We're underway in the second half! ${home} against ${away}.`;
    p.textContent = message;
    time.textContent = `${currentMinute}'`;
    $('announcement').textContent = message;
    if (playing && mode === 'audio' && !commentaryReady) speechPromise = speak(message);
  }
  if (currentCommentary) {
    const content = mode === 'simple' ? currentCommentary.simplified : currentCommentary.expressive;
    p.textContent = content;
    time.textContent = `${currentCommentary.minute}'`;
    $('caption-minute').textContent = `${currentCommentary.minute}'`;
    $('live-caption-text').textContent = content;
    const feed = $('event-feed');
    feed.replaceChildren();
    const current = commentaryIndex < 0 ? [] : commentaryEvents.slice(Math.max(0, commentaryIndex - 11), commentaryIndex + 1).reverse();
    for (const item of current) {
      const li = document.createElement('li');
      const stamp = document.createElement('strong'); stamp.textContent = `${item.minute}'`;
      li.append(stamp, document.createTextNode(mode === 'simple' ? item.simplified : item.expressive));
      feed.append(li);
    }
  } else {
    $('caption-minute').textContent = `${currentMinute}'`;
    $('live-caption-text').textContent = p.textContent;
  }
  renderKeyMoments();
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
function selectedVoice() {
  const voices = speechSynthesis.getVoices();
  return voices.find(v => v.voiceURI === $('voice-select').value) || null;
}
function populateVoices() {
  if (!('speechSynthesis' in window)) return;
  const select = $('voice-select');
  const previous = select.value;
  select.replaceChildren(new Option('System default', ''));
  for (const voice of speechSynthesis.getVoices().filter(v => v.lang.startsWith('en'))) {
    select.add(new Option(`${voice.name} (${voice.lang})`, voice.voiceURI));
  }
  select.value = [...select.options].some(o => o.value === previous) ? previous : '';
}
if ('speechSynthesis' in window) {
  populateVoices();
  speechSynthesis.addEventListener?.('voiceschanged', populateVoices);
}
function speak(text) {
  if (!('speechSynthesis' in window)) {
    $('announcement').textContent = 'Speech synthesis is unavailable in this browser.';
    return Promise.resolve();
  }
  speechSynthesis.cancel();
  return new Promise(resolve => {
    const utterance = new SpeechSynthesisUtterance(text);
    const voice = selectedVoice();
    if (voice) { utterance.voice = voice; utterance.lang = voice.lang; }
    else utterance.lang = 'en-GB';
    utterance.rate = Number($('voice-rate').value);
    let done = false;
    const finish = () => { if (!done) { done = true; resolve(); } };
    utterance.onend = finish;
    utterance.onerror = finish;
    speechSynthesis.speak(utterance);
  });
}
function pause() {
  playing = false;
  playbackGeneration++;
  clearTimeout(timer);
  timer = null;
  if (cancelPlaybackWait) {
    const resolveWait = cancelPlaybackWait;
    cancelPlaybackWait = null;
    resolveWait();
  }
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  $('play-button').textContent = '▶ Play match';
}
function waitFor(ms) {
  return new Promise(resolve => {
    const finish = () => {
      timer = null;
      cancelPlaybackWait = null;
      resolve();
    };
    cancelPlaybackWait = finish;
    timer = setTimeout(finish, ms);
  });
}
function visibleCommentaryIndexes() {
  const keyOnly = $('replay-mode').value === 'key';
  return commentaryEvents.map((item, i) => i).filter(i => !keyOnly || keyEventIds.has(commentaryEvents[i].event_id));
}
async function loadCommentary() {
  try {
    const [commentaryResponse, replayResponse] = await Promise.all([
      fetch(`${API_BASE}/api/ai/commentary`), fetch(`${API_BASE}/api/replay?minute=90`)
    ]);
    if (!commentaryResponse.ok || !replayResponse.ok) throw new Error('Commentary unavailable');
    const commentary = await commentaryResponse.json();
    const state = await replayResponse.json();
    commentaryEvents = commentary.highlights || [];
    keyEventIds = new Set((state.key_events || []).filter(isImportant).map(e => String(e.event_id)));
    highlightMinutes = [...new Set((state.key_events || []).filter(isImportant).map(e => Number(e.minute)))].sort((a,b) => a-b);
    commentaryReady = commentaryEvents.length > 0;
    highlightLoaded = true;
  } catch (error) {
    commentaryReady = false;
    highlightLoaded = false;
    console.warn('Using standard replay because commentary could not load:', error);
  }
}
function nextHighlight() {
  return [...highlightMinutes, 45, 46, MAX_MINUTE].filter(m => m > minute).sort((a,b) => a-b)[0] ?? null;
}
async function scheduleNext(generation) {
  if (!playing || generation !== playbackGeneration || replayBusy) return;
  replayBusy = true;
  try {
    if (commentaryReady) {
      const indexes = visibleCommentaryIndexes();
      const nextIndex = indexes.find(i => i > commentaryIndex);
      if (nextIndex === undefined) { pause(); return; }
      commentaryIndex = nextIndex;
      currentCommentary = commentaryEvents[nextIndex];
      speechPromise = Promise.resolve();
      await fetchReplay(currentCommentary.minute);
      if (!playing || generation !== playbackGeneration) return;
      const text = mode === 'simple' ? currentCommentary.simplified : currentCommentary.expressive;
      if (mode === 'audio') {
        await speak(text);
        if (playing && generation === playbackGeneration) await waitFor(300);
      } else {
        await waitFor(tickMs);
      }
    } else {
      if (minute >= MAX_MINUTE) { pause(); return; }
      const next = highlightLoaded ? nextHighlight() : Math.min(minute + 1, MAX_MINUTE);
      if (next === null) { pause(); return; }
      speechPromise = Promise.resolve();
      await fetchReplay(next);
      if (!playing || generation !== playbackGeneration) return;
      if (mode === 'audio') await speechPromise;
      await waitFor(tickMs);
    }
  } finally {
    replayBusy = false;
    if (playing && generation === playbackGeneration) scheduleNext(generation);
  }
}
async function play() {
  if (playing) return;
  if (!commentaryReady && !highlightLoaded) await loadCommentary();
  if (commentaryReady && (commentaryIndex >= commentaryEvents.length - 1 || minute >= MAX_MINUTE)) {
    commentaryIndex = -1; currentCommentary = null; await fetchReplay(0);
  } else if (!commentaryReady && minute >= MAX_MINUTE) await fetchReplay(0);
  playing = true;
  $('play-button').textContent = '❚❚ Pause';
  const generation = ++playbackGeneration;
  scheduleNext(generation);
}
function seekCommentary(targetMinute) {
  commentaryIndex = -1;
  for (let i = 0; i < commentaryEvents.length; i++) {
    if (commentaryEvents[i].minute <= targetMinute) commentaryIndex = i;
    else break;
  }
  currentCommentary = commentaryIndex >= 0 ? commentaryEvents[commentaryIndex] : null;
}
$('replay-speed').addEventListener('change', e => {
  tickMs = Number(e.target.value);
  /* The updated speed applies to the next highlight. */
});
$('test-voice').addEventListener('click', () => speak('Welcome to EqualPlay AI. Here is your match commentary.'));
$('play-button').addEventListener('click', () => playing ? pause() : play());
$('reset-button').addEventListener('click', () => { pause(); lastAnnouncedEventId = null; commentaryIndex = -1; currentCommentary = null; fetchReplay(0); });
$('minute-slider').addEventListener('input', (event) => { pause(); lastAnnouncedEventId = null; const target = Number(event.target.value); seekCommentary(target); fetchReplay(target); });
$('replay-mode').addEventListener('change', () => { pause(); commentaryIndex = -1; currentCommentary = null; fetchReplay(0); });
$('speak-button').addEventListener('click', () => { if (currentCommentary) { speak(mode === 'simple' ? currentCommentary.simplified : currentCommentary.expressive); return; } if (latestState) { const events = (latestState.key_events || []).filter(isImportant); const latest = events.at(-1); speak(latest ? eventDescription(latest, mode === 'simple') : 'The match is ready for kickoff.'); } });
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', () => {
  mode = button.dataset.mode;
  document.body.classList.toggle('simple-mode', mode === 'simple');
  document.body.classList.toggle('audio-mode', mode === 'audio');
  document.querySelectorAll('[data-mode]').forEach(b => { const active = b === button; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
  if (mode !== 'audio' && 'speechSynthesis' in window) speechSynthesis.cancel();
  if (latestState) render(latestState);
}));
fetchReplay(0);

const summaryButton = $('generate-summary-button');
const summaryContent = $('ai-summary-content');

summaryButton.addEventListener('click', async () => {
  summaryButton.disabled = true;
  summaryButton.textContent = 'Generating summary...';
  summaryContent.classList.remove('error');
  summaryContent.textContent = 'Analysing match events...';

  try {
    const response = await fetch(`${API_BASE}/api/ai/summary`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    summaryContent.textContent = data.summary;

    summaryButton.textContent = 'Generate Again';
  } catch (error) {
    summaryContent.classList.add('error');
    summaryContent.textContent =
      `Unable to generate summary: ${error.message}`;

    summaryButton.textContent = 'Try Again';
  } finally {
    summaryButton.disabled = false;
  }
});

function renderKeyMoments() {
  const container = $('key-moments-list');
  container.replaceChildren();

  const descriptions = { takes_lead: 'Puts their team in front', equaliser: 'Brings the scores level', extends_lead: 'Increases the advantage' };

  const visibleMoments = allKeyMoments.filter(
    moment => moment.minute <= minute
  );

  for (const moment of visibleMoments) {
    const item = document.createElement('div');
    item.className = 'key-moment-item';

    if (moment.is_winning_goal && minute >= 90) {
      item.classList.add('winning-goal');
    }

    const minuteLabel = document.createElement('span');
    minuteLabel.className = 'key-moment-minute';
    minuteLabel.textContent = `${moment.minute}'`;

    const details = document.createElement('div');
    details.className = 'key-moment-details';

    const player = document.createElement('strong');
    player.textContent = moment.player_name || 'Unknown player';

    const description = document.createElement('p');
    description.textContent = moment.is_winning_goal && minute >= 90
      ? 'Match-winning goal — the decisive finish in this result.'
      : `${descriptions[moment.significance] || 'Changes the score'} — the match stands at ${moment.score.HOME}–${moment.score.AWAY}.`;

    details.append(player, description);

    const score = document.createElement('span');
    score.className = 'key-moment-score';
    score.textContent = `${moment.score.HOME}–${moment.score.AWAY}`;

    item.append(minuteLabel, details, score);
    container.appendChild(item);
  }

  if (visibleMoments.length === 0) {
    container.textContent =
      'No key moments yet. Advance the replay to see them.';
  }
}

async function loadKeyMoments() {
  const container = $('key-moments-list');

  try {
    const response = await fetch(`${API_BASE}/api/key-moments`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    allKeyMoments = data.moments;

    renderKeyMoments();
  } catch (error) {
    container.textContent =
      `Unable to load key moments: ${error.message}`;
  }
}

loadKeyMoments();

// Synchronise the landing-page preview with the existing replay response.
const originalRender = render;
render = function (state) {
  originalRender(state);
  $('preview-home').textContent = state.teams?.HOME?.name || 'Chelsea';
  $('preview-away').textContent = state.teams?.AWAY?.name || 'Manchester City';
  $('preview-score').textContent = `${state.score?.HOME ?? 0} – ${state.score?.AWAY ?? 0}`;
  $('preview-state').textContent = $('match-state').textContent;
  const stats = $('preview-stats'); stats.replaceChildren();
  for (const [label, key, suffix] of STATS.slice(0, 4)) {
    const home = state.stats?.HOME?.[key], away = state.stats?.AWAY?.[key];
    const row = document.createElement('div'); row.className = 'preview-stat';
    const header = document.createElement('div'); header.className = 'preview-stat-head';
    const left = document.createElement('strong'); left.textContent = home == null ? '—' : `${home}${suffix}`;
    const title = document.createElement('span'); title.textContent = label;
    const right = document.createElement('strong'); right.textContent = away == null ? '—' : `${away}${suffix}`;
    header.append(left, title, right);
    const track = document.createElement('div'); track.className = 'preview-track';
    const bar = document.createElement('span');
    const h = Number(home) || 0, a = Number(away) || 0;
    bar.style.width = `${h + a > 0 ? 100 * h / (h + a) : 50}%`;
    track.append(bar); row.append(header, track); stats.append(row);
  }
  const events = $('preview-events'); events.replaceChildren();
  const keyEvents = (state.key_events || []).filter(isImportant).slice(-4).reverse();
  if (!keyEvents.length) events.textContent = 'No major events yet.';
  for (const event of keyEvents) {
    const row = document.createElement('div'); row.className = 'preview-event';
    const stamp = document.createElement('strong'); stamp.textContent = `${event.minute}'`;
    const detail = document.createElement('span'); detail.textContent = eventDescription(event, true);
    row.append(stamp, detail); events.append(row);
  }
};

// Spoken AI summary uses browser speech synthesis; Azure still generates the text.
const narrateButton = $('narrate-summary-button');
let summaryNarrating = false;
function stopSummaryNarration() {
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  summaryNarrating = false;
  narrateButton.textContent = '▶ Listen to summary';
}
narrateButton.addEventListener('click', () => {
  if (summaryNarrating) { stopSummaryNarration(); return; }
  if (!('speechSynthesis' in window)) { $('announcement').textContent = 'Speech synthesis is unavailable in this browser.'; return; }
  const summary = summaryContent.textContent.trim();
  if (!summary) return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(summary);
  const voice = selectedVoice();
  if (voice) { utterance.voice = voice; utterance.lang = voice.lang; }
  else utterance.lang = 'en-GB';
  utterance.rate = Number($('voice-rate').value);
  utterance.onend = utterance.onerror = () => { summaryNarrating = false; narrateButton.textContent = '▶ Listen to summary'; };
  summaryNarrating = true; narrateButton.textContent = '■ Stop narration';
  speechSynthesis.speak(utterance);
});
summaryButton.addEventListener('click', () => { stopSummaryNarration(); narrateButton.disabled = true; });
const summaryObserver = new MutationObserver(() => {
  narrateButton.disabled = summaryButton.disabled || summaryContent.classList.contains('error') || !['Generate Again'].includes(summaryButton.textContent.trim());
});
summaryObserver.observe(summaryContent, {childList:true,characterData:true,subtree:true});
summaryObserver.observe(summaryButton, {childList:true,characterData:true,subtree:true});

// Persistent, keyboard-accessible accessibility preferences.
const menuToggle = $('accessibility-toggle');
const menu = $('accessibility-menu');
function closeAccessibility() { menu.hidden = true; menuToggle.setAttribute('aria-expanded','false'); }
menuToggle.addEventListener('click', () => { menu.hidden = !menu.hidden; menuToggle.setAttribute('aria-expanded',String(!menu.hidden)); });
document.addEventListener('click', event => { if (!event.target.closest('.accessibility-wrap')) closeAccessibility(); });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && !menu.hidden) { closeAccessibility(); menuToggle.focus(); } });
function savePreferences() { try { localStorage.setItem('equalplay-prefs', JSON.stringify({mode, voice:$('voice-select').value, rate:$('voice-rate').value, speed:$('replay-speed').value})); } catch (_) {} }
for (const id of ['voice-select','voice-rate','replay-speed']) $(id).addEventListener('change', savePreferences);
document.querySelectorAll('[data-mode]').forEach(button => button.addEventListener('click', savePreferences));
try {
  const saved = JSON.parse(localStorage.getItem('equalplay-prefs') || '{}');
  if (saved.mode) document.querySelector(`[data-mode="${saved.mode}"]`)?.click();
  if (saved.rate && [...$('voice-rate').options].some(o=>o.value===saved.rate)) $('voice-rate').value=saved.rate;
  if (saved.speed && [...$('replay-speed').options].some(o=>o.value===saved.speed)) { $('replay-speed').value=saved.speed; tickMs=Number(saved.speed); }
  if (saved.voice) { const applyVoice=()=>{ if ([...$('voice-select').options].some(o=>o.value===saved.voice)) $('voice-select').value=saved.voice; }; applyVoice(); if ('speechSynthesis' in window) speechSynthesis.addEventListener?.('voiceschanged',applyVoice); }
} catch (_) {}
