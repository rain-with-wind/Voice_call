const state = {
  apiBase: window.location.origin,
  activeRoom: loadActiveRoom(),
  statusTimer: null
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
  serverCommand: document.getElementById("serverCommand"),
  clientCommand: document.getElementById("clientCommand"),
  joinPublicCommand: document.getElementById("joinPublicCommand"),
  lookupForm: document.getElementById("lookupForm"),
  roomCodeInput: document.getElementById("roomCodeInput"),
  lookupResult: document.getElementById("lookupResult"),
  lookupTitle: document.getElementById("lookupTitle"),
  lookupMeta: document.getElementById("lookupMeta"),
  refreshRoomsButton: document.getElementById("refreshRoomsButton"),
  roomsList: document.getElementById("roomsList"),
  roomName: document.getElementById("roomName"),
  publicPort: document.getElementById("publicPort")
};

boot();

elements.hostForm.addEventListener("submit", handleCreateRoom);
elements.lookupForm.addEventListener("submit", handleLookupRoom);
elements.refreshRoomsButton.addEventListener("click", loadRooms);
elements.closeRoomButton.addEventListener("click", handleCloseRoom);
document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", () => copyBlock(button.dataset.copyTarget));
});

async function boot() {
  elements.backendBadge.textContent = state.apiBase;
  await checkHealth();
  restoreActiveRoom();
  await loadRooms();

  const roomCodeFromUrl = window.location.pathname.startsWith("/room/")
    ? decodeURIComponent(window.location.pathname.split("/").pop())
    : "";

  if (roomCodeFromUrl) {
    elements.roomCodeInput.value = roomCodeFromUrl;
    await lookupRoom(roomCodeFromUrl);
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
    public_port: Number(elements.publicPort.value),
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
    renderCommandBlocks(response.room);
    await loadRooms();
  } catch (error) {
    writeCommand("serverCommand", error.message);
  }
}

async function handleLookupRoom(event) {
  event.preventDefault();
  const roomCode = elements.roomCodeInput.value.trim().toUpperCase();
  if (!roomCode) {
    return;
  }
  await lookupRoom(roomCode);
}

async function lookupRoom(roomCode) {
  try {
    const payload = await apiRequest(`/api/rooms/${encodeURIComponent(roomCode)}`);
    renderLookupRoom(payload.room);
    renderClientCommands(payload.room);
    window.history.replaceState({}, "", `/room/${roomCode}`);
  } catch (error) {
    elements.lookupResult.classList.remove("hidden");
    elements.lookupTitle.textContent = "房间未找到";
    elements.lookupMeta.textContent = roomCode;
    writeCommand("clientCommand", error.message);
  }
}

async function loadRooms() {
  try {
    const payload = await apiRequest("/api/rooms");
    renderRooms(payload.rooms || []);
  } catch (error) {
    elements.roomsList.className = "rooms-list empty-state";
    elements.roomsList.textContent = error.message;
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
  clearActiveRoom();
  renderActiveRoom();
  await loadRooms();
}

function renderActiveRoom() {
  if (!state.activeRoom) {
    elements.activeRoomPanel.classList.add("hidden");
    elements.closeRoomButton.disabled = true;
    writeCommand("serverCommand", "创建房间后，这里会生成服务端命令。");
    writeCommand("joinPublicCommand", "创建房间后，这里会生成 join-public 命令。");
    return;
  }

  const room = state.activeRoom.room;
  elements.activeRoomPanel.classList.remove("hidden");
  elements.closeRoomButton.disabled = false;
  elements.activeRoomTitle.textContent = `${room.name} | ${room.room_code}`;
  elements.activeRoomMeta.textContent = `${room.public_host}:${room.public_port}`;
  elements.statusHint.textContent = `房间状态保持中，每 ${state.activeRoom.refreshIntervalSeconds} 秒自动更新一次。`;
  renderCommandBlocks(room);
}

function renderCommandBlocks(room) {
  const backendUrl = state.apiBase;

  writeCommand(
    "serverCommand",
    [
      "Linux / WSL:",
      `python3 voice_call.py --mode server --port ${room.public_port}`,
      "",
      "Windows:",
      `python voice_call.py --mode server --port ${room.public_port}`
    ].join("\n")
  );

  writeCommand(
    "joinPublicCommand",
    [
      "Linux / WSL:",
      `python3 voice_call.py join-public --backend-url ${backendUrl} --room-code ${room.room_code}`,
      "",
      "Windows:",
      `python voice_call.py join-public --backend-url ${backendUrl} --room-code ${room.room_code}`
    ].join("\n")
  );

  renderClientCommands(room);
}

function renderClientCommands(room) {
  writeCommand(
    "clientCommand",
    [
      "Linux / WSL:",
      `python3 voice_call.py --mode client --host ${room.public_host} --port ${room.public_port}`,
      "",
      "Windows:",
      `python voice_call.py --mode client --host ${room.public_host} --port ${room.public_port}`
    ].join("\n")
  );
}

function renderLookupRoom(room) {
  elements.lookupResult.classList.remove("hidden");
  elements.lookupTitle.textContent = `${room.name} | ${room.room_code}`;
  elements.lookupMeta.textContent = `${room.public_host}:${room.public_port}`;
}

function renderRooms(rooms) {
  if (!rooms.length) {
    elements.roomsList.className = "rooms-list empty-state";
    elements.roomsList.textContent = "当前没有在线房间。";
    return;
  }

  elements.roomsList.className = "rooms-list";
  elements.roomsList.innerHTML = "";

  rooms.forEach((room) => {
    const card = document.createElement("article");
    card.className = "room-card";
    card.innerHTML = `
      <div class="room-info">
        <p class="mini-label">${escapeHtml(room.room_code)}</p>
        <h3>${escapeHtml(room.name)}</h3>
        <p>${escapeHtml(room.public_host)}:${escapeHtml(String(room.public_port))}</p>
      </div>
      <div class="room-actions">
        <button class="ghost small" data-action="lookup">查看</button>
        <button class="primary small" data-action="client">生成命令</button>
      </div>
    `;

    card.querySelector('[data-action="lookup"]').addEventListener("click", async () => {
      elements.roomCodeInput.value = room.room_code;
      await lookupRoom(room.room_code);
    });

    card.querySelector('[data-action="client"]').addEventListener("click", () => {
      renderLookupRoom(room);
      renderClientCommands(room);
    });

    elements.roomsList.appendChild(card);
  });
}

function restoreActiveRoom() {
  if (!state.activeRoom) {
    return;
  }
  renderActiveRoom();
  startRoomStatusLoop();
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
      await loadRooms();
    } catch (error) {
      elements.statusHint.textContent = `状态更新失败：${error.message}`;
    }
  };

  tick();
  state.statusTimer = window.setInterval(tick, state.activeRoom.refreshIntervalSeconds * 1000);
}

function stopRoomStatusLoop() {
  if (state.statusTimer) {
    window.clearInterval(state.statusTimer);
    state.statusTimer = null;
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

function writeCommand(elementId, content) {
  document.getElementById(elementId).textContent = content;
}

async function copyBlock(elementId) {
  const content = document.getElementById(elementId).textContent;
  try {
    await navigator.clipboard.writeText(content);
  } catch (_error) {
    // Ignore clipboard failures silently.
  }
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${state.apiBase}${path}`, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
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

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
