# Reddit account connect

Reddit rate-limits and bot-flags anonymous access. To pull subreddits reliably we need the
user to **connect their Reddit account** (OAuth) so requests carry their permissions. This is
out of scope for the initial add-feed build — there, Reddit is selectable and behaves like the
other types (paste a subreddit URL, mock results). This backlog item captures the connect work.

## Task 1 — Connect screen (UI/UX)

Before a user can add a Reddit feed, they connect their account once.

- **Entry point:** picking **Reddit** in the add-feed type list. If not yet connected, route to
  a **Connect Reddit** step instead of the paste input.
- **Connect screen:** explains why (avoid bot-flagging, get their subreddits/permissions) and a
  single **Connect Reddit** action. On success, continue into the normal paste → results flow.
- **Connected state:** once connected, picking Reddit skips straight to the input. Surface
  connection status somewhere in Settings (connect / disconnect) — placement TBD.
- No backend yet: the connect action is mocked (fakes a successful connection).

## Task 2 — Backend OAuth (once backend is ready)

- Real Reddit OAuth: authorize, exchange, store + refresh tokens per user.
- Use the connection to fetch subreddit feeds under the user's permissions.
- Wire the mocked connect action from Task 1 to the real flow; handle expiry / revoke /
  reconnect.

## Relationship to the add-feed build

The initial add-feed flow (see the add-feed spec) is designed so this connect step can slot in
front of the Reddit input branch without reshaping the other types.
