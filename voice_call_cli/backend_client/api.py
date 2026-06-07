"""@file api.py
@brief Minimal HTTP client used by the CLI to talk to the public backend.
"""

import json
import urllib.error
import urllib.parse
import urllib.request


class PublicBackendClient:
    """@brief Wrap backend API calls for room registration and lookup."""

    def __init__(self, backend_url, timeout=10):
        """@brief Create a backend client instance.

        @param backend_url Base URL of the public backend.
        @param timeout Timeout for HTTP requests, in seconds.
        """
        self.backend_url = backend_url.rstrip("/")
        self.timeout = timeout

    def health(self):
        """@brief Query the backend health endpoint.

        @return dict JSON payload returned by `/api/health`.
        """
        return self._request("GET", "/api/health")

    def register_room(self, payload):
        """@brief Register a new public room.

        @param payload JSON-serializable registration payload.
        @return dict Backend response containing room details and manage token.
        """
        return self._request("POST", "/api/rooms/register", payload)

    def list_rooms(self):
        """@brief Fetch all currently active rooms.

        @return dict Backend response containing the room list.
        """
        return self._request("GET", "/api/rooms")

    def get_room(self, room_code):
        """@brief Query a room by its room code.

        @param room_code User-facing room code.
        @return dict Backend response containing the room details.
        """
        room_code = urllib.parse.quote(room_code)
        return self._request("GET", f"/api/rooms/{room_code}")

    def heartbeat(self, room_code, manage_token):
        """@brief Refresh a room so it remains visible to other users.

        @param room_code Room code to refresh.
        @param manage_token Secret management token issued at registration time.
        @return dict Backend response containing the updated room record.
        """
        room_code = urllib.parse.quote(room_code)
        return self._request(
            "POST",
            f"/api/rooms/{room_code}/heartbeat",
            {},
            headers={"X-Manage-Token": manage_token},
        )

    def close_room(self, room_code, manage_token):
        """@brief Close a room on the public backend.

        @param room_code Room code to close.
        @param manage_token Secret management token issued at registration time.
        @return dict Backend response confirming the close request.
        """
        room_code = urllib.parse.quote(room_code)
        return self._request(
            "POST",
            f"/api/rooms/{room_code}/close",
            {},
            headers={"X-Manage-Token": manage_token},
        )

    def _request(self, method, path, payload=None, headers=None):
        """@brief Send an HTTP request and decode its JSON response.

        @param method HTTP method such as `GET` or `POST`.
        @param path Backend route path beginning with `/`.
        @param payload Optional JSON request body.
        @param headers Optional additional headers.
        @return dict Parsed JSON payload from the backend.
        @exception RuntimeError Raised when the backend is unreachable or
            returns an error response.
        """
        body = None
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{self.backend_url}{path}",
            data=body,
            headers=request_headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
                message = payload.get("error") or raw
            except json.JSONDecodeError:
                message = raw or str(exc)
            raise RuntimeError(f"Backend request failed ({exc.code}): {message}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Backend unreachable: {exc.reason}") from exc
