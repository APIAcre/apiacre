const API = "/arcade/lanternwake/api";
const PAGE = "/arcade/lanternwake";
const COLORS = ["#c56b50", "#477e98", "#778649", "#936b97"];
const HARBOR_NAMES = ["Kelp Quay", "Ember Pier", "Moon Jetty"];
const SHORT_NAMES = ["Kelp", "Ember", "Moon"];
const ACTION_NAMES = { deploy: "Place", ferry: "Ferry", bank: "Bank" };
const $ = (id) => document.getElementById(id);

let room = null;
let identity = null;
let selected = null;
let busy = false;
let polling = false;
let generation = 0;
let lastPainted = "";
let receivedAt = performance.now();
let connectionProblem = false;
let noticeTimer;
let failedPolls = 0;
let nextPollAt = 0;

function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}

function storageGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

function storageSet(key, value) {
  try { localStorage.setItem(key, value); } catch { /* This tab can still play. */ }
}

function savedIdentity(code) {
  try {
    const data = JSON.parse(storageGet(`lanternwake.session.${code}`));
    if (data && typeof data.token === "string" && Number.isInteger(data.seat)) return data;
  } catch { /* A malformed saved session is not a seat credential. */ }
  return null;
}

function getName() {
  const name = $("player-name").value.trim() || "Harbor guest";
  storageSet("lanternwake.name", name);
  return name;
}

function seatName(index) {
  return room?.seats?.[index]?.name || `Captain ${index + 1}`;
}

function isMyTurn() {
  return Boolean(identity && room?.phase === "active" && room.game?.current_player === identity.seat);
}

function notify(message, error = false, retry = false) {
  clearTimeout(noticeTimer);
  $("notice-text").textContent = message;
  $("notice").classList.toggle("error", error);
  $("retry-connection").hidden = !retry;
  $("notice").hidden = false;
  if (!error) noticeTimer = setTimeout(() => { $("notice").hidden = true; }, 5000);
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  const headers = { Accept: "application/json", ...options.headers };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  try {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers,
      cache: "no-store",
      signal: controller.signal,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    });
    let data;
    try { data = await response.json(); } catch { data = null; }
    if (!response.ok) {
      const detail = data?.detail ?? data?.error ?? data?.message;
      const text = typeof detail === "string" ? detail : detail?.message;
      const error = new Error(text || `The harbor could not complete that request (${response.status}).`);
      error.status = response.status;
      throw error;
    }
    if (!data || typeof data !== "object") throw new Error("The harbor sent an unreadable update. Please retry.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The harbor took too long to answer. Please retry.");
    if (error instanceof TypeError) throw new Error("The connection drifted away. Your table is still there; retry when you are online.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function auth() {
  return { Authorization: `Bearer ${identity.token}` };
}

function setBusy(value) {
  busy = value;
  ["quick-play", "create-room", "start-game", "join-this-room"].forEach((id) => { $(id).disabled = value; });
  $("join-form").querySelector("button").disabled = value;
  $("commit-move").disabled = value || !isMyTurn() || !selected;
  if (room) paintRoom(true);
}

function acceptSeat(data) {
  const code = String(data.code || data.room?.code || "").toUpperCase();
  if (!code || typeof data.token !== "string" || !Number.isInteger(data.seat)) {
    throw new Error("The table did not return a valid seat. Please try again.");
  }
  identity = { token: data.token, seat: data.seat };
  storageSet(`lanternwake.session.${code}`, JSON.stringify(identity));
  generation += 1;
  lastPainted = "";
  selected = null;
  const url = new URL(location.href);
  url.searchParams.set("room", code);
  history.replaceState({}, "", url);
  if (data.room) receive(data.room);
  else room = { code, phase: "lobby", seats: [] };
  return code;
}

async function createGame(quick) {
  if (busy) return;
  setBusy(true);
  try {
    const data = await request("/rooms", { method: "POST", body: { name: getName(), seats: quick ? 2 : Number($("seat-count").value) } });
    const code = acceptSeat(data);
    if (quick) {
      receive(await request(`/rooms/${encodeURIComponent(code)}/start`, { method: "POST", headers: auth(), body: {} }));
    } else await poll(true);
    $("notice").hidden = true;
  } catch (error) {
    notify(error.message, true);
  } finally { setBusy(false); }
}

async function joinGame(code) {
  if (busy) return;
  const clean = String(code).trim().toUpperCase();
  if (!/^[A-Z0-9]{4,8}$/.test(clean)) {
    notify("Enter the match code from your invitation.", true);
    $("room-code").focus();
    return;
  }
  setBusy(true);
  try {
    const existing = savedIdentity(clean);
    if (existing) {
      const data = await request(`/rooms/${encodeURIComponent(clean)}`);
      identity = existing;
      generation += 1;
      lastPainted = "";
      selected = null;
      const url = new URL(location.href);
      url.searchParams.set("room", clean);
      history.replaceState({}, "", url);
      receive(data);
    } else {
      acceptSeat(await request(`/rooms/${encodeURIComponent(clean)}/join`, { method: "POST", body: { name: getName() } }));
    }
    $("notice").hidden = true;
    await poll(true);
  } catch (error) {
    notify(error.message, true);
  } finally { setBusy(false); }
}

async function startGame() {
  if (busy || !room || !identity) return;
  setBusy(true);
  try {
    receive(await request(`/rooms/${encodeURIComponent(room.code)}/start`, { method: "POST", headers: auth(), body: {} }));
  } catch (error) { notify(error.message, true); }
  finally { setBusy(false); }
}

function receive(data) {
  room = data.room && !data.code ? data.room : data;
  receivedAt = performance.now();
  failedPolls = 0;
  nextPollAt = 0;
  if (connectionProblem) {
    connectionProblem = false;
    notify("Back at the table. The latest turn is ready.");
  }
  paintRoom();
  paintClock();
}

async function poll(force = false) {
  if (!room?.code || polling || (busy && !force) || (!force && performance.now() < nextPollAt)) return;
  polling = true;
  const code = room.code;
  const currentGeneration = generation;
  try {
    const data = await request(`/rooms/${encodeURIComponent(code)}`);
    if (generation === currentGeneration && room?.code === code) receive(data);
  } catch (error) {
    if (generation !== currentGeneration || room?.code !== code) return;
    if (error.status === 404) {
      backHome();
      $("room-code").value = code;
      notify("That table is no longer available. Check its code or start a new match.", true);
      return;
    }
    connectionProblem = true;
    failedPolls += 1;
    nextPollAt = performance.now() + Math.min(15000, 1000 * (2 ** Math.min(failedPolls, 4)));
    notify(error.message, true, true);
  } finally { polling = false; }
}

function view(which) {
  ["landing", "lobby", "match"].forEach((id) => { $(id).hidden = id !== which; });
}

function paintRoom(force = false) {
  if (!room) { view("landing"); return; }
  const key = `${room.code}:${room.version}:${room.phase}:${identity?.seat ?? "watch"}:${busy}`;
  if (!force && key === lastPainted) return;
  lastPainted = key;
  if (room.phase === "lobby") {
    view("lobby");
    paintLobby();
    return;
  }
  if (!room.game) return;
  view("match");
  $("copy-match").textContent = room.code;
  $("copy-match").setAttribute("aria-label", `Copy invitation for match ${room.code}`);
  const game = room.game;
  $("match-kicker").textContent = room.phase === "finished" ? "THE BAY REMEMBERS A GOOD RIVALRY" : `TIDE ${game.round} OF ${game.max_rounds} · ${game.player_count} CAPTAINS`;
  $("round-title").textContent = `Tide ${game.round} / ${game.max_rounds}`;
  if (room.phase === "finished") $("chart-rule").textContent = "Final lanterns, after all tide payouts.";
  else $("chart-rule").replaceChildren(document.createTextNode("Sole leader takes the reward."), node("br"), node("strong", "", "Ties pay nobody."));
  $("match-title").textContent = room.phase === "finished" ? "Every light had its moment." : "A little light goes a long way.";
  paintPlayers();
  normalizeSelection();
  paintHarbors();
  paintActions();
  paintForecast();
  paintLog();
  paintResult();
}

function crest(index, empty = false) {
  const mark = node("span", `crest${empty ? " empty-crest" : ""}`, empty ? "–" : String(index + 1));
  mark.style.setProperty("--player-color", COLORS[index]);
  mark.setAttribute("aria-hidden", "true");
  return mark;
}

function paintLobby() {
  $("lobby-code").textContent = room.code;
  const filled = room.seats.filter((seat) => seat.kind !== "empty").length;
  const host = identity?.seat === room.host_seat;
  $("lobby-status").textContent = `${filled} of ${room.seats.length} seats taken. Share the code or invite link.`;
  const rows = room.seats.map((seat, index) => {
    const li = node("li");
    li.append(crest(index, seat.kind === "empty"));
    const info = node("div");
    const label = seat.kind === "empty" ? "A bot will join here" : `${seat.name}${identity?.seat === index ? " (you)" : ""}`;
    info.append(node("span", "seat-name", label));
    info.append(node("span", "seat-kind", seat.kind === "empty" ? "Or invite someone before starting" : `${seat.kind === "agent" ? "API agent" : seat.kind === "bot" ? "Harbor bot" : "Human captain"}${index === room.host_seat ? " · host" : ""}`));
    li.append(info);
    return li;
  });
  $("lobby-seats").replaceChildren(...rows);
  $("start-game").hidden = !host;
  $("start-game").disabled = busy;
  $("join-this-room").hidden = Boolean(identity) || filled >= room.seats.length;
  $("lobby-start-note").textContent = host ? "Start whenever you’re ready. Every empty seat becomes a bot; everyone gets 16 seconds per turn." : identity ? "The host will start the match. Empty seats become bots." : "You’re viewing this table. Take an empty seat to play.";
}

function paintPlayers() {
  const game = room.game;
  $("players").style.setProperty("--player-count", game.player_count);
  const items = room.seats.map((seat, index) => {
    const active = room.phase === "active" && game.current_player === index;
    const card = node("article", `player${active ? " current" : ""}`);
    card.style.setProperty("--player-color", COLORS[index]);
    card.setAttribute("aria-label", `${seat.name}${identity?.seat === index ? ", you" : ""}: ${game.scores[index]} points, ${game.reserves[index]} lanterns in reserve${active ? ", current turn" : ""}`);
    card.append(crest(index));
    const info = node("div", "player-info");
    info.append(node("span", "player-name", `${seat.name}${identity?.seat === index ? " · you" : ""}`));
    info.append(node("span", "player-kind", `${seat.kind === "bot" ? "BOT" : seat.kind === "agent" ? "AGENT" : "HUMAN"}${active ? " · PLAYING" : ""}`));
    const reserve = node("span", "player-reserve");
    reserve.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 7; i += 1) reserve.append(node("i", `mini-lantern${i >= game.reserves[index] ? " empty" : ""}`));
    info.append(reserve);
    const score = node("span", "player-score", String(game.scores[index]));
    score.append(node("small", "", "POINTS"));
    card.append(info, score);
    return card;
  });
  $("players").replaceChildren(...items);
}

function control(counts) {
  const maximum = Math.max(...counts);
  if (maximum === 0) return { leader: null, tied: false };
  const leaders = counts.flatMap((count, index) => count === maximum ? [index] : []);
  return { leader: leaders.length === 1 ? leaders[0] : null, tied: leaders.length > 1 };
}

function harborArt(index) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 220 150");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `#art-${["kelp", "ember", "moon"][index]}`);
  svg.append(use);
  return svg;
}

function paintHarbors() {
  const cards = room.game.harbors.map((harbor, index) => {
    const target = isMyTurn() && selected && (selected.type === "ferry" ? selected.to === index : selected.harbor === index);
    const origin = isMyTurn() && selected?.type === "ferry" && selected.from === index;
    const card = node("article", `harbor${target ? " selected" : ""}${origin ? " origin" : ""}`);
    card.dataset.harbor = String(index);
    const button = node("button", "harbor-button");
    button.dataset.boardHarbor = String(index);
    button.disabled = !isMyTurn() || busy;
    button.setAttribute("aria-label", `${harbor.name}, reward ${harbor.reward} points${target ? ", selected destination" : ""}${origin ? ", ferry origin" : ""}. Select this harbor.`);
    button.append(harborArt(index), node("span", "harbor-number", `HARBOR 0${index + 1}`), node("span", "harbor-title", harbor.name));
    const reward = node("span", "reward", String(harbor.reward));
    reward.append(node("small", "", "POINTS"));
    button.append(reward);
    const counts = node("div", "harbor-counts");
    harbor.lanterns.forEach((count, player) => {
      const row = node("div", "lantern-row");
      row.style.setProperty("--player-color", COLORS[player]);
      row.setAttribute("aria-label", `${seatName(player)}: ${count} lantern${count === 1 ? "" : "s"}`);
      const mark = node("span", "row-seat", String(player + 1));
      mark.setAttribute("aria-hidden", "true");
      const track = node("span", "lantern-track");
      track.setAttribute("aria-hidden", "true");
      for (let i = 0; i < count; i += 1) track.append(node("i", "lantern"));
      if (count === 0) track.append(node("i", "empty-water"));
      const total = node("span", "lantern-total", String(count));
      total.setAttribute("aria-hidden", "true");
      row.append(mark, track, total);
      counts.append(row);
    });
    const holding = control(harbor.lanterns);
    const text = room.phase === "finished"
      ? holding.leader !== null ? `${seatName(holding.leader)} has the final lantern lead` : holding.tied ? "Final lanterns: a tied lead" : "Final lanterns: quiet water"
      : holding.leader !== null ? `${seatName(holding.leader)} leads · ${harbor.reward} points at tide` : holding.tied ? "Tied lead · no tide points" : "Quiet water · no leader yet";
    card.append(button, counts, node("p", "harbor-control", text));
    return card;
  });
  const active = document.activeElement?.dataset?.boardHarbor;
  $("harbors").replaceChildren(...cards);
  if (active !== undefined) $("harbors").querySelector(`[data-board-harbor="${active}"]`)?.focus({ preventScroll: true });
  $("chart-hint").textContent = room.phase === "finished" ? "The tide has settled. Every move is in the journal below." : isMyTurn() ? selected?.type === "ferry" ? "Choose a destination on the chart. Set your starting harbor in the move panel." : "Tap a harbor, then confirm your move in the panel." : "Watch the lanterns. Your next opportunity is already taking shape.";
}

function available() {
  return isMyTurn() && Array.isArray(room.legal_actions) ? room.legal_actions : [];
}

function sameAction(left, right) {
  return Boolean(left && right && left.type === right.type && left.count === right.count && left.harbor === right.harbor && left.from === right.from && left.to === right.to);
}

function normalizeSelection() {
  const legal = available();
  if (!legal.length) { selected = null; return; }
  if (legal.some((action) => sameAction(action, selected))) return;
  selected = legal.find((action) => action.type === selected?.type && action.count === 2) || legal.find((action) => action.type === "deploy" && action.count === 2) || legal[0];
}

function selectAction(criteria) {
  if (!isMyTurn() || busy) return;
  const legal = available().filter((action) => Object.entries(criteria).every(([key, value]) => action[key] === value));
  if (!legal.length) {
    notify(criteria.type === "bank" ? "You need a lantern in that harbor before you can bank it." : "That move is not available. Choose one of the highlighted options.", true);
    return;
  }
  const keepTarget = legal.find((action) => action.count === selected?.count && action.harbor === selected?.harbor && action.from === selected?.from && action.to === selected?.to);
  selected = keepTarget || legal.find((action) => action.count === selected?.count) || legal.find((action) => action.count === 2) || legal[0];
  paintHarbors();
  paintActions();
}

function choiceGroup(label, field, options) {
  const group = node("fieldset", "action-field");
  group.append(node("legend", "", label));
  const row = node("div", "choice-row");
  options.forEach(({ value, label: text }) => {
    const choice = node("button", `choice-button${field === "count" ? " amount-choice" : ""}`, text);
    choice.type = "button";
    choice.dataset.field = field;
    choice.dataset.value = String(value);
    choice.id = `choice-${field}-${value}`;
    choice.setAttribute("aria-pressed", String(selected?.[field] === value));
    let candidates = available().filter((action) => action.type === selected.type && action[field] === value);
    if (field === "count") candidates = candidates.filter((action) => action.harbor === selected.harbor && action.from === selected.from && action.to === selected.to);
    if (field === "to") candidates = candidates.filter((action) => action.from === selected.from);
    choice.disabled = busy || candidates.length === 0;
    row.append(choice);
  });
  group.append(row);
  return group;
}

function paintActions() {
  const game = room.game;
  const mine = isMyTurn();
  const finished = room.phase === "finished";
  const current = game.current_player;
  const waitingName = current === null ? "The tide" : seatName(current);
  $("turn-kicker").textContent = finished ? "THE LANTERNS REST" : mine ? "YOUR TURN" : identity ? "WATCH THE WATER" : "YOU ARE WATCHING";
  $("turn-title").textContent = finished ? "A harbor well played." : mine ? "Make a little trouble." : `${waitingName} is thinking.`;
  $("turn-description").textContent = finished ? "The highest score takes the bay. The journal keeps the story." : mine ? `You have ${game.reserves[identity.seat]} lantern${game.reserves[identity.seat] === 1 ? "" : "s"} in reserve. Choose one action.` : `${seatName(current)} has the next move. Each captain acts once before the tide pays out.`;
  $("turn-note").textContent = finished ? "Start a new table for another match." : mine ? "16 seconds per turn. If time runs out, a bot covers your move." : identity ? "Your seat stays yours. A bot covers any turns you miss." : "Share this match code to let others watch. Join a new table to play.";
  $("mobile-turn-bar").hidden = finished;
  $("jump-move").textContent = mine ? "Plan move →" : "Move panel →";
  const controls = $("action-controls");
  const focusedId = controls.contains(document.activeElement) ? document.activeElement.id : null;
  controls.replaceChildren();
  if (mine && selected) {
    const tabs = node("div", "action-tabs");
    tabs.setAttribute("role", "group");
    tabs.setAttribute("aria-label", "Choose an action");
    Object.entries(ACTION_NAMES).forEach(([type, name]) => {
      const button = node("button", "action-tab", name);
      button.id = `action-${type}`;
      button.dataset.type = type;
      button.setAttribute("aria-pressed", String(selected.type === type));
      button.disabled = busy || !available().some((action) => action.type === type);
      tabs.append(button);
    });
    controls.append(tabs);
    if (selected.type === "ferry") {
      controls.append(choiceGroup("FROM HARBOR", "from", SHORT_NAMES.map((label, value) => ({ label, value }))));
      controls.append(choiceGroup("TO HARBOR", "to", SHORT_NAMES.map((label, value) => ({ label, value }))));
    } else {
      controls.append(choiceGroup(selected.type === "deploy" ? "PLACE AT" : "BANK FROM", "harbor", SHORT_NAMES.map((label, value) => ({ label, value }))));
    }
    controls.append(choiceGroup("LANTERNS", "count", [{ value: 1, label: "1 lantern" }, { value: 2, label: "2 lanterns" }]));
    if (focusedId) document.getElementById(focusedId)?.focus({ preventScroll: true });
  }
  paintPreview();
  $("commit-move").hidden = finished || !mine;
  $("commit-move").disabled = busy || !mine || !selected;
  $("commit-move").textContent = busy ? "Sending your move…" : selected ? `${ACTION_NAMES[selected.type]} ${selected.count} lantern${selected.count === 1 ? "" : "s"}` : "Choose a move";
}

function paintPreview() {
  const preview = $("move-preview");
  preview.replaceChildren();
  const game = room.game;
  if (!isMyTurn() || !selected) {
    preview.classList.add("waiting");
    preview.append(node("strong", "", room.phase === "finished" ? "The final lights are on the chart." : "A good moment to plan ahead."));
    preview.append(node("p", "", room.phase === "finished" ? "Look through the journal to see how the scores changed with every tide." : "Compare the current rewards with the next tide. A harbor worth less now may be your best next move."));
    return;
  }
  preview.classList.remove("waiting");
  const { type, count } = selected;
  const player = identity.seat;
  const changed = game.harbors.map((harbor) => [...harbor.lanterns]);
  let heading;
  let target;
  if (type === "deploy") {
    target = selected.harbor;
    changed[target][player] += count;
    heading = `Place ${count} at ${HARBOR_NAMES[target]}.`;
  } else if (type === "ferry") {
    target = selected.to;
    changed[selected.from][player] -= count;
    changed[target][player] += count;
    heading = `Ferry ${count}: ${SHORT_NAMES[selected.from]} to ${SHORT_NAMES[target]}.`;
  } else {
    target = selected.harbor;
    changed[target][player] -= count;
    heading = `Bank ${count} for ${count} point${count === 1 ? "" : "s"} now.`;
  }
  preview.append(node("strong", "", heading));
  const lead = control(changed[target]);
  const reward = game.harbors[target].reward;
  let result = lead.leader === player ? `You would lead ${SHORT_NAMES[target]}. Hold it until the tide closes for ${reward} points.` : lead.tied && changed[target][player] === Math.max(...changed[target]) ? `You would tie the lead at ${SHORT_NAMES[target]}. A tied harbor pays nobody.` : lead.leader === null ? `${SHORT_NAMES[target]} would have no sole leader, so it would pay no tide points.` : `${seatName(lead.leader)} would still lead ${SHORT_NAMES[target]}.`;
  if (type === "bank") result = `Return ${count} to reserve. ${result}`;
  if (type === "ferry") {
    const old = control(changed[selected.from]);
    if (control(game.harbors[selected.from].lanterns).leader === player && old.leader !== player) result += ` You give up your lead at ${SHORT_NAMES[selected.from]}.`;
  }
  preview.append(node("p", "", result));
  if (game.turn_in_round === game.player_count - 1) {
    const payouts = game.scores.map(() => 0);
    changed.forEach((counts, index) => { const winner = control(counts).leader; if (winner !== null) payouts[winner] += game.harbors[index].reward; });
    const paying = payouts.flatMap((points, index) => points ? [`${index === player ? "you" : seatName(index)} +${points}`] : []);
    preview.append(node("p", "preview-change", `This closes the tide: ${paying.length ? paying.join(", ") : "no harbor rewards"}. Each winning harbor returns one lantern.`));
  } else {
    const remaining = game.player_count - game.turn_in_round - 1;
    preview.append(node("p", "preview-change", `${remaining} more captain${remaining === 1 ? "" : "s"} will act before this tide pays out.`));
  }
}

function paintForecast() {
  const game = room.game;
  $("forecast").style.setProperty("--tides", game.max_rounds);
  const items = game.forecast.map((rewards, index) => {
    const round = index + 1;
    const current = round === game.round && room.phase !== "finished";
    const tide = node("div", `tide${current ? " current" : ""}${round < game.round || room.phase === "finished" ? " past" : ""}`);
    tide.setAttribute("aria-label", `Tide ${round}${current ? ", current" : ""}: Kelp ${rewards[0]}, Ember ${rewards[1]}, Moon ${rewards[2]} points`);
    tide.append(node("span", "tide-label", `${current ? "NOW · " : ""}TIDE ${round}`));
    const values = node("span", "tide-values");
    values.setAttribute("aria-hidden", "true");
    rewards.forEach((reward) => values.append(node("span", "", String(reward))));
    tide.append(values);
    return tide;
  });
  $("forecast").replaceChildren(...items);
}

function paintLog() {
  const log = room.game.log || [];
  const list = $("match-log");
  const atEnd = list.scrollHeight - list.scrollTop - list.clientHeight < 45;
  const scroll = list.scrollTop;
  const items = log.map((entry) => {
    const row = node("li", `log-${entry.kind}`);
    row.append(node("span", "log-seq", entry.kind === "tide" ? `T${entry.round}` : String(entry.seq).padStart(2, "0")));
    row.append(node("span", "", entry.text));
    return row;
  });
  list.replaceChildren(...items);
  list.scrollTop = atEnd ? list.scrollHeight : scroll;
  $("log-count").textContent = `(${log.length})`;
}

function paintResult() {
  const finished = room.phase === "finished";
  $("result").hidden = !finished;
  if (!finished) return;
  const game = room.game;
  const winners = game.winners || [];
  const names = winners.map(seatName);
  const won = identity && winners.includes(identity.seat);
  $("result-title").textContent = winners.length > 1 ? `${names.join(" & ")} share the bay.` : won ? "The bay is yours." : `${names[0] || "A captain"} takes the tide.`;
  const points = winners.length ? game.scores[winners[0]] : Math.max(...game.scores);
  $("result-detail").textContent = `${points} points${winners.length > 1 ? " each" : ""}. ${game.finish_reason && game.finish_reason !== "rounds_complete" ? "The match has ended; these are the final scores." : "The last tide has paid out. Thanks for a good little rivalry."}`;
}

function paintClock() {
  if (!room || room.phase !== "active") { $("turn-clock").textContent = ""; return; }
  const elapsed = (performance.now() - receivedAt) / 1000;
  const left = Math.max(0, Math.ceil(Number(room.turn_seconds_left || 0) - elapsed));
  $("turn-clock").textContent = left > 0 ? `${left}s` : "…";
  $("turn-clock").classList.toggle("urgent", left <= 5 && isMyTurn());
  $("turn-clock").setAttribute("aria-label", left > 0 ? `${left} seconds left in this turn` : "Resolving the next turn");
  $("mobile-turn-text").textContent = `${isMyTurn() ? "Your turn" : "Watching"} · ${left > 0 ? `${left}s` : "resolving"}`;
}

async function commitMove() {
  if (busy || !isMyTurn() || !selected) return;
  const action = { ...selected };
  const version = room.version;
  const code = room.code;
  const oldGeneration = generation;
  setBusy(true);
  try {
    const data = await request(`/rooms/${encodeURIComponent(code)}/moves`, { method: "POST", headers: auth(), body: { version, action } });
    if (oldGeneration !== generation || room?.code !== code) return;
    selected = null;
    receive(data);
    $("notice").hidden = true;
  } catch (error) {
    if (oldGeneration === generation) {
      notify(error.status === 409 ? "The turn changed before that move arrived. The board is refreshing; choose again if it is still your turn." : error.message, true);
      await poll(true);
    }
  } finally { setBusy(false); }
}

async function copyInvite() {
  if (!room) return;
  const url = new URL(PAGE, location.origin);
  url.searchParams.set("room", room.code);
  try {
    await navigator.clipboard.writeText(url.href);
    notify("Invite link copied. Bring a friend or an agent.");
  } catch { notify(`Match code: ${room.code}. Invite link: ${url.href}`); }
}

function backHome() {
  const wasActive = room?.phase === "active";
  generation += 1;
  room = null;
  identity = null;
  selected = null;
  lastPainted = "";
  connectionProblem = false;
  failedPolls = 0;
  nextPollAt = 0;
  const url = new URL(location.href);
  url.searchParams.delete("room");
  history.replaceState({}, "", url);
  view("landing");
  if (wasActive) notify("Your table keeps playing. Rejoin with its code; a bot covers missed turns.");
  window.scrollTo({ top: 0, behavior: "instant" });
}

$("quick-play").addEventListener("click", () => createGame(true));
$("create-room").addEventListener("click", () => createGame(false));
$("join-form").addEventListener("submit", (event) => { event.preventDefault(); joinGame($("room-code").value); });
$("join-this-room").addEventListener("click", () => joinGame(room.code));
$("start-game").addEventListener("click", startGame);
$("commit-move").addEventListener("click", commitMove);
$("copy-lobby").addEventListener("click", copyInvite);
$("copy-match").addEventListener("click", copyInvite);
$("new-game").addEventListener("click", backHome);
$("jump-chart").addEventListener("click", () => document.querySelector(".chart").scrollIntoView({ block: "start", behavior: "instant" }));
$("jump-move").addEventListener("click", () => document.querySelector(".action-dock").scrollIntoView({ block: "start", behavior: "instant" }));
document.querySelectorAll(".back-home").forEach((button) => button.addEventListener("click", backHome));
$("dismiss-notice").addEventListener("click", () => { $("notice").hidden = true; });
$("retry-connection").addEventListener("click", () => poll(true));
$("rules-button").addEventListener("click", () => $("rules").showModal());
$("close-rules").addEventListener("click", () => $("rules").close());
$("rules-done").addEventListener("click", () => $("rules").close());
$("rules").addEventListener("click", (event) => { if (event.target === $("rules")) { const rect = $("rules").getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $("rules").close(); } });
$("action-controls").addEventListener("click", (event) => {
  const type = event.target.closest("button[data-type]");
  if (type) { selectAction({ type: type.dataset.type }); return; }
  const choice = event.target.closest("button[data-field]");
  if (!choice || !selected) return;
  const field = choice.dataset.field;
  const value = Number(choice.dataset.value);
  const criteria = { type: selected.type, [field]: value };
  if (field === "count") {
    if (selected.type === "ferry") Object.assign(criteria, { from: selected.from, to: selected.to });
    else criteria.harbor = selected.harbor;
  }
  if (field === "to") criteria.from = selected.from;
  selectAction(criteria);
});
$("harbors").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-board-harbor]");
  if (!button || !selected) return;
  const harbor = Number(button.dataset.boardHarbor);
  selectAction(selected.type === "ferry" ? { type: "ferry", from: selected.from, to: harbor } : { type: selected.type, harbor });
});

const storedName = storageGet("lanternwake.name");
if (storedName) $("player-name").value = storedName.slice(0, 20);
const initialCode = new URL(location.href).searchParams.get("room")?.trim().toUpperCase();
if (initialCode && /^[A-Z0-9]{4,8}$/.test(initialCode)) {
  identity = savedIdentity(initialCode);
  room = { code: initialCode, phase: "lobby", seats: [] };
  $("room-code").value = initialCode;
  poll(true);
}
setInterval(() => { if (!document.hidden) poll(); }, 1000);
setInterval(paintClock, 250);
document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(true); });
window.addEventListener("online", () => poll(true));
