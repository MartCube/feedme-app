# User Stories

Grouped by feature area. Each story is something a user should be able to do in the finished
app. These map directly to the screens in [screens-and-flows.md](./screens-and-flows.md).

## Reading

- As a user, I can **see all my feeds** on the home screen so I know what I'm subscribed to.
- As a user, I can **open a feed** to see its latest posts.
- As a user, I can **browse a feed's posts** as a scrollable list of cards (image, title,
  date).
- As a user, I can **open a post and read it in full** (title, image, content, date).
- As a user, posts are shown **newest first** so I see fresh content at the top.

## Saving

- As a user, I can **save a post** while reading it, so I can come back to it later.
- As a user, I can **see all my saved posts in one place** (Saved posts), across feeds.
- As a user, I can **open a saved post** and read it like any other post.
- As a user, I can **unsave a post** when I no longer want it in my saved list.

## Folders

- As a user, I can **group feeds into a named folder** so related sources sit together.
- As a user, I can **put one feed in several folders** (membership is many-to-many).
- As a user, I can **expand a folder** in the feeds list to see its member feeds, or **tap the
  folder** to read all its feeds as one merged, newest-first stream.
- As a user, I can **create a folder** from the navbar **+** menu (alongside New feed).
- As a user, I can **rename a folder**.
- As a user, I can **add or remove feeds** from a folder.
- As a user, I can **mute a feed inside a folder** so it's excluded from that folder's merged
  read while staying readable on its own and in other folders.
- As a user, I can **delete a folder** — and I'm warned that its feeds (those not in another
  folder) will be unsubscribed.
- As a user, feeds **not in any folder** show as loose entries at the top level.

## Source

- As a user, I can **open a post at its original source** (article, YouTube watch page,
  Reddit thread) when I want the full / native experience.
- As a user, I can tell **what kind of source** a feed is (YouTube / Reddit / website) from
  its icon.

## Managing feeds

- As a user, I can **add a new feed by URL** so I can follow a new source.
- As a user, the app **figures out the feed type** from the URL so I don't have to.
- As a user, a **newly added feed appears in my feeds list** immediately.
- As a user, I can **rename a feed**.
- As a user, I can **delete a feed**, which unsubscribes it everywhere (all folders included).
- As a user, I can **open an edit menu** on any feed or folder — **long-press** on mobile, a
  **3-dot / overflow** control on desktop.

## App & settings

- As a user, I can **open Settings** to manage my account and view app info.
- As a user, I can **view the design system** reference from Settings.
- As a user, the app is **always in dark mode** and laid out for my phone.

---

## Acceptance notes

- Every story above should be reachable through the navigation map in
  [screens-and-flows.md](./screens-and-flows.md) — no orphan features.
- Saving relies on the saved-posts state described in
  [data-model.md](./data-model.md#saved-state-new--not-yet-in-code).
- "Add a feed by URL" should validate input using the installed VeeValidate + Zod stack.
