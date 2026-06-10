const DEFAULT_AUDIO_PORT = 5000;
const SESSION_POLL_INTERVAL_MS = 5000;
const DEVICE_TOKEN_STORAGE_KEY = "voice_call_device_token";

const state = {
  apiBase: window.location.origin,
  deviceToken: loadOrCreateDeviceToken(),
  activeRoom: loadActiveRoom(),
  joinedSession: loadJoinedSession(),
  statusTimer: null,
  sessionTimer: null
};

const elements = {
  healthBadge: document.getElementById("healthBadge"),
  backendBadge: document.getElementById("backendBadge"),
  hostForm: document.getElementById("hostForm"),
  closeRoomButton: document.getElementById("closeRoomButton"),
  activeRoomPanel: document.getElementById("activeRoomPanel"),
  activeRoomTitle: document.getElementById("activeRoomTitle"),
  activeRoomMeta: document.getElementById("activeRoomMeta"),
  statusHint: document.getElementById("statusHint"),
  lookupForm: document.getElementById("lookupForm"),
  roomCodeInput: document.getElementById("roomCodeInput"),
  lookupResult: document.getElementById("lookupResult"),
  lookupTitle: document.getElementById("lookupTitle"),
  lookupMeta: document.getElementById("lookupMeta"),
  roomName: document.getElementById("roomName"),
  roomStage: document.getElementById("roomStage"),
  roomStageTitle: document.getElementById("roomStageTitle"),
  roomStageMeta: document.getElementById("roomStageMeta"),
  membersList: document.getElementById("membersList"),
  voiceHint: document.getElementById("voiceHint"),
  leaveRoomButton: document.getElementById("leaveRoomButton")
};

boot();

elements.hostForm.addEventListener("submit", handleCreateRoom);
elements.lookupForm.addEventListener("submit", handleLookupRoom);
elements.closeRoomButton.addEventListener("click", handleCloseRoom);
elements.leaveRoomButton.addEventListener("click", handleLeaveRoom);

async function boot() {
  elements.backendBadge.textContent = state.apiBase;
  await checkHealth();
  restoreActiveRoom();
  await restoreJoinedSession();

  const roomCodeFromUrl = window.location.pathname.startsWith("/room/")
    ? decodeURIComponent(window.location.pathname.split("/").pop())
    : "";

  if (roomCodeFromUrl && (!state.joinedSession || state.joinedSession.roomCode !== roomCodeFromUrl)) {
    elements.roomCodeInput.value = roomCodeFromUrl;
    await joinRoomSession(roomCodeFromUrl);
  }
}

async function checkHealth() {
  try {
    const payload = await apiRequest("/api/health");
    elements.healthBadge.textContent = `后端在线 - ${payload.service}`;
    elements.healthBadge.classList.add("healthy");
  } catch (error) {
    elements.healthBadge.textContent = `后端不可用 - ${error.message}`;
    elements.healthBadge.classList.add("error");
  }
}

async function handleCreateRoom(event) {
  event.preventDefault();

  const payload = {
    name: elements.roomName.value.trim(),
    public_host: window.location.hostname || "127.0.0.1",
    public_port: DEFAULT_AUDIO_PORT,
    owner_name: "",
    notes: ""
  };

  try {
    const response = await apiRequest("/api/rooms/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    state.activeRoom = {
      backendUrl: state.apiBase,
      manageToken: response.manage_token,
      refreshIntervalSeconds: response.heartbeat_interval_seconds,
      room: response.room
    };
    saveActiveRoom(state.activeRoom);
    renderActiveRoom();
    startRoomStatusLoop();
    await joinRoomSession(response.room.room_code);
    elements.statusHint.textContent = "房间已创建，你已进入该房间。";
  } catch (error) {
    elements.statusHint.textContent = `创建失败：${error.message}`;
  }
}

async function handleLookupRoom(event) {
  event.preventDefault();
  const roomCode = elements.roomCodeInput.value.trim().toUpperCase();
  if (!roomCode) {
    return;
  }
  await joinRoomSession(roomCode);
}

async function joinRoomSession(roomCode) {
  try {
    if (state.joinedSession && state.joinedSession.roomCode === roomCode) {
      await refreshJoinedRoomState();
      return;
    }

    if (state.joinedSession && state.joinedSession.roomCode !== roomCode) {
      await leaveJoinedSession();
    }

    const payload = await apiRequest(`/api/rooms/${encodeURIComponent(roomCode)}/join`, {
      method: "POST",
      body: JSON.stringify({})
    });

    state.joinedSession = {
      roomCode,
      participantToken: payload.participant_token,
      displayName: payload.participant.display_name
    };
    saveJoinedSession(state.joinedSession);
    renderLookupRoom(payload.room, payload.participant);
    renderRoomStage(payload.room, payload.participants, payload.messages);
    startSessionLoop();
    window.history.replaceState({}, "", `/room/${roomCode}`);
  } catch (error) {
    elements.lookupResult.classList.remove("hidden");
    elements.lookupTitle.textContent = "房间未找到";
    elements.lookupMeta.textContent = `房间码：${roomCode}`;
    hideRoomStage();
    elements.voiceHint.textContent = `加入失败：${error.message}`;
  }
}

async function handleCloseRoom() {
  if (!state.activeRoom) {
    return;
  }

  try {
    await apiRequest(`/api/rooms/${encodeURIComponent(state.activeRoom.room.room_code)}/close`, {
      method: "POST",
      headers: {
        "X-Manage-Token": state.activeRoom.manageToken
      },
      body: JSON.stringify({})
    });
  } catch (_error) {
    // Ignore close failures and clear local state anyway.
  }

  stopRoomStatusLoop();
  if (state.joinedSession && state.joinedSession.roomCode === state.activeRoom.room.room_code) {
    await leaveJoinedSession();
    hideRoomStage();
    elements.lookupResult.classList.add("hidden");
    window.history.replaceState({}, "", "/");
  }
  clearActiveRoom();
  renderActiveRoom();
}

function renderActiveRoom() {
  if (!state.activeRoom) {
    elements.activeRoomPanel.classList.add("hidden");
    elements.closeRoomButton.disabled = true;
    return;
  }

  const room = state.activeRoom.room;
  elements.activeRoomPanel.classList.remove("hidden");
  elements.closeRoomButton.disabled = false;
  elements.activeRoomTitle.textContent = `${room.name} | ${room.room_code}`;
  elements.activeRoomMeta.textContent = `房间码：${room.room_code}`;
  elements.statusHint.textContent = `房间状态保持中，每 ${state.activeRoom.refreshIntervalSeconds} 秒自动更新一次。`;
}

function renderLookupRoom(room, participant = null) {
  elements.lookupResult.classList.remove("hidden");
  elements.lookupTitle.textContent = `${room.name} | ${room.room_code}`;
  if (participant) {
    elements.lookupMeta.textContent = `已加入，当前身份：${participant.display_name}`;
  } else {
    elements.lookupMeta.textContent = "房间可用，输入房间码即可加入。";
  }
}

function restoreActiveRoom() {
  if (!state.activeRoom) {
    return;
  }
  renderActiveRoom();
  startRoomStatusLoop();
}

async function restoreJoinedSession() {
  if (!state.joinedSession) {
    hideRoomStage();
    return;
  }

  try {
    await refreshJoinedRoomState();
    startSessionLoop();
  } catch (error) {
    clearJoinedSession();
    hideRoomStage();
    elements.voiceHint.textContent = `房间恢复失败：${error.message}`;
  }
}

function startRoomStatusLoop() {
  stopRoomStatusLoop();
  if (!state.activeRoom) {
    return;
  }

  const tick = async () => {
    try {
      const payload = await apiRequest(`/api/rooms/${encodeURIComponent(state.activeRoom.room.room_code)}/heartbeat`, {
        method: "POST",
        headers: {
          "X-Manage-Token": state.activeRoom.manageToken
        },
        body: JSON.stringify({})
      });
      state.activeRoom.room = payload.room;
      saveActiveRoom(state.activeRoom);
      elements.statusHint.textContent = `上次更新：${new Date().toLocaleTimeString()}`;
    } catch (error) {
      elements.statusHint.textContent = `状态更新失败：${error.message}`;
    }
  };

  tick();
  state.statusTimer = window.setInterval(tick, state.activeRoom.refreshIntervalSeconds * 1000);
}

function startSessionLoop() {
  stopSessionLoop();
  if (!state.joinedSession) {
    return;
  }

  const tick = async () => {
    try {
      await apiRequest(`/api/rooms/${encodeURIComponent(state.joinedSession.roomCode)}/participants/heartbeat`, {
        method: "POST",
        headers: {
          "X-Participant-Token": state.joinedSession.participantToken
        },
        body: JSON.stringify({})
      });
      await refreshJoinedRoomState();
      elements.voiceHint.textContent = `已连接房间，当前身份：${state.joinedSession.displayName}`;
    } catch (error) {
      elements.voiceHint.textContent = `房间同步失败：${error.message}`;
    }
  };

  tick();
  state.sessionTimer = window.setInterval(tick, SESSION_POLL_INTERVAL_MS);
}

function stopRoomStatusLoop() {
  if (state.statusTimer) {
    window.clearInterval(state.statusTimer);
    state.statusTimer = null;
  }
}

function stopSessionLoop() {
  if (state.sessionTimer) {
    window.clearInterval(state.sessionTimer);
    state.sessionTimer = null;
  }
}

function saveActiveRoom(room) {
  localStorage.setItem("voice_call_active_room", JSON.stringify(room));
}

function loadActiveRoom() {
  try {
    const raw = localStorage.getItem("voice_call_active_room");
    return raw ? JSON.parse(raw) : null;
  } catch (_error) {
    return null;
  }
}

function clearActiveRoom() {
  state.activeRoom = null;
  localStorage.removeItem("voice_call_active_room");
}

function saveJoinedSession(session) {
  localStorage.setItem("voice_call_joined_session", JSON.stringify(session));
}

function loadJoinedSession() {
  try {
    const raw = localStorage.getItem("voice_call_joined_session");
    return raw ? JSON.parse(raw) : null;
  } catch (_error) {
    return null;
  }
}

function clearJoinedSession() {
  state.joinedSession = null;
  localStorage.removeItem("voice_call_joined_session");
}

function loadOrCreateDeviceToken() {
  try {
    const existing = localStorage.getItem(DEVICE_TOKEN_STORAGE_KEY);
    if (existing) {
      return existing;
    }
  } catch (_error) {
    // Ignore storage access failures and fall through to a volatile token.
  }

  const generated = generateDeviceToken();
  try {
    localStorage.setItem(DEVICE_TOKEN_STORAGE_KEY, generated);
  } catch (_error) {
    // Ignore storage failures and keep using the in-memory token.
  }
  return generated;
}

function generateDeviceToken() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return `vc-web-${window.crypto.randomUUID()}`;
  }
  return `vc-web-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function refreshJoinedRoomState() {
  if (!state.joinedSession) {
    return;
  }

  const payload = await apiRequest(`/api/rooms/${encodeURIComponent(state.joinedSession.roomCode)}/state`);
  renderRoomStage(payload.room, payload.participants);
}

function renderRoomStage(room, participants) {
  elements.roomStage.classList.remove("hidden");
  elements.leaveRoomButton.disabled = false;
  elements.roomStageTitle.textContent = `${room.name} | ${room.room_code}`;
  elements.roomStageMeta.textContent = `当前在线 ${participants.length} 人`;
  renderMembers(participants);
  elements.voiceHint.textContent = state.joinedSession
    ? `房间已连接，当前身份：${state.joinedSession.displayName}`
    : "房间已连接。";
}

function hideRoomStage() {
  elements.roomStage.classList.add("hidden");
  elements.leaveRoomButton.disabled = true;
}

function renderMembers(participants) {
  if (!participants.length) {
    elements.membersList.className = "members-list empty-state";
    elements.membersList.textContent = "当前还没有在线成员。";
    return;
  }

  elements.membersList.className = "members-list";
  elements.membersList.innerHTML = participants.map((participant) => {
    const isSelf = state.joinedSession && participant.participant_token === state.joinedSession.participantToken;
    const selfLabel = isSelf ? " (你)" : "";
    return `<article class="member-pill">${escapeHtml(participant.display_name)}${selfLabel}</article>`;
  }).join("");
}

async function handleLeaveRoom() {
  await leaveJoinedSession();
  hideRoomStage();
  elements.lookupResult.classList.add("hidden");
  elements.voiceHint.textContent = "你已离开房间。";
  window.history.replaceState({}, "", "/");
}

async function leaveJoinedSession() {
  if (!state.joinedSession) {
    return;
  }

  try {
    await apiRequest(`/api/rooms/${encodeURIComponent(state.joinedSession.roomCode)}/participants/leave`, {
      method: "POST",
      headers: {
        "X-Participant-Token": state.joinedSession.participantToken
      },
      body: JSON.stringify({})
    });
  } catch (_error) {
    // Ignore leave failures and clear local state anyway.
  }

  stopSessionLoop();
  clearJoinedSession();
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${state.apiBase}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Device-Token": state.deviceToken,
      ...(options.headers || {})
    },
    body: options.body
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}
