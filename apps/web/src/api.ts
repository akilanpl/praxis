/** Session-bound transport. A stale 401 must not revoke a newer login. */
export async function api(path: string, body?: unknown) {
  const token = localStorage.getItem("token") || "";
  const response = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data;
  try {
    data = await response.json();
  } catch {
    throw Error("Local API returned an invalid JSON response");
  }
  if (!response.ok) {
    if (
      response.status === 401 &&
      !path.startsWith("/auth/") &&
      localStorage.getItem("token") === token
    ) {
      window.dispatchEvent(new Event("praxis-session-expired"));
    }
    throw Error(
      typeof data?.error === "string" ? data.error : "Request failed",
    );
  }
  return data;
}
