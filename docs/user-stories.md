# User Stories

Grouped by feature area. Each story is something a user should be able to do in the finished
app. These map directly to the screens in [screens-and-flows.md](./screens-and-flows.md).

## Reading

- As a user, I can **see all my feeds** on the home screen so I know what I'm following.
- As a user, I can **open a feed** to see its latest posts — newest first, merged across its
  sources when it has more than one.
- As a user, I can **browse a feed's posts** as a scrollable list of cards (image, title,
  date).
- As a user, I can **open a post and read it in full** (title, image, content, date).
- As a user, posts are shown **newest first** so I see fresh content at the top.

## Saving

- As a user, I can **save a post** while reading it, so I can come back to it later.
- As a user, I can **see all my saved posts in one place** (Saved posts), across feeds.
- As a user, I can **open a saved post** and read it like any other post.
- As a user, I can **unsave a post** when I no longer want it in my saved list.

## Feeds & sources

A **feed** is my own group of sources — one source or several — with a name and a description.

- As a user, I can **group sources into a feed** so related ones sit together and read as one
  merged, newest-first stream — or keep a feed to **a single source**.
- As a user, I can **put one source in several feeds**.
- As a user, I can **open a feed's page** (tap its title above the posts) to see its
  description and its sources.
- As a user, I can **switch a source on or off inside a feed**, right on the feed's page, so
  it's left out of that feed's read (and of All feeds, unless another feed has it on) while
  staying in the feed and in my other feeds.
- As a user, I can **rename a source** in a feed — a blank name goes back to the source's own.
- As a user, I can **change a source's link**.
- As a user, I can **edit a feed's name and description**.
- As a user, I can **add a source to an existing feed** from its page.
- As a user, I can **remove a source from a feed**; the feed stays, even if it ends up empty.
- As a user, I can **delete a feed** — and it asks first. Its sources leave my list unless
  another feed has them; my saved posts stay.

## Source

- As a user, I can **open a post at its original source** (article, YouTube watch page,
  Reddit thread) when I want the full / native experience.
- As a user, I can tell **what kind of source** a post comes from (YouTube / Reddit / website)
  from its icon.

## Managing feeds

- As a user, I can **add a source by URL** so I can follow something new, and **choose which
  feed it goes into** — or **New feed**.
- As a user, the app **figures out the source type** from the URL so I don't have to.
- As a user, a **newly added source appears in its feed** immediately, and a new feed in my
  feeds list.
- As a user, an add that **can't work** (not a feed, or already in that feed) says so and
  leaves everything as it was.

## Account

- As a user, I **sign in before I can read anything** — the app has no guest mode, and my feeds
  are mine (see [backend.md](./backend.md#auth)).
- As a user, I **stay signed in** across reloads and app launches until I sign out.
- As a user, I can **sign out** from Settings → Account, which ends the session everywhere it
  could be replayed, not just on this device's screen.
- As a user, I can **see how I signed in and how long I've been a member** in Settings →
  Account.

## App & settings

- As a user, I can **open Settings** to manage my account and view app info.
- As a user, I can **view the design system** reference from Settings.
- As a user, the app is **always in dark mode** and laid out for my phone.

---

## Acceptance notes

- Every story above should be reachable through the navigation map in
  [screens-and-flows.md](./screens-and-flows.md) — no orphan features.
- Saving relies on the saved-posts state described in
  [data-model.md](./data-model.md#saved-state).
- "Add a source by URL" should validate input using the installed VeeValidate + Zod stack.
