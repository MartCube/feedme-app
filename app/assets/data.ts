import type { Feed, Folder, Post } from './types'

export const feeds: Feed[] = [
  {
    uid: 'feed_medium_vuejs',
    name: 'Vue.js on Medium',
    feed_url: 'https://medium.com/feed/tag/vuejs',
    site_url: 'https://medium.com/tag/vuejs',
    type: 'website',
  },
  {
    uid: 'feed_youtube',
    name: 'YouTube Channel',
    feed_url: 'https://www.youtube.com/feeds/videos.xml?channel_id=UCgijSqjxEFzRJuQwNBRrTDg',
    site_url: 'https://www.youtube.com/channel/UCgijSqjxEFzRJuQwNBRrTDg',
    type: 'youtube',
  },
  {
    uid: 'feed_reddit_onepiece',
    name: 'r/OnePiece',
    feed_url: 'https://www.reddit.com/r/OnePiece/.rss',
    site_url: 'https://www.reddit.com/r/OnePiece/',
    type: 'reddit',
  },
]

export const folders: Folder[] = [
  {
    uid: 'folder_dev',
    name: 'Dev',
    feed_uids: ['feed_medium_vuejs', 'feed_youtube'],
    muted_feed_uids: [],
  },
]

export const posts: Post[] = [
  {
    uid: 'art_med_1',
    feed_uid: 'feed_medium_vuejs',
    title: 'Building Composable Data Table in Vue3',
    image_url: 'https://picsum.photos/id/0/600/340',
    published_at: '2026-06-22T10:15:00Z',
    post_url: 'https://medium.com/example/composable-data-table',
    content:
      'Composables are the idiomatic way to share stateful logic in Vue 3. In this piece we build a reusable useDataTable() that handles sorting, pagination and row selection without coupling to any single component. We start with the reactive state, expose a clean API, and then wire it into a thin presentational layer. The key insight is keeping the composable free of DOM concerns so it can be unit tested in isolation.',
  },
  {
    uid: 'art_med_2',
    feed_uid: 'feed_medium_vuejs',
    title: 'Why I Stopped Using Vuex and Moved to Pinia',
    image_url: 'https://picsum.photos/id/1/600/340',
    published_at: '2026-06-21T08:00:00Z',
    post_url: 'https://medium.com/example/vuex-to-pinia',
    content:
      'Pinia has become the official state management library for Vue, and after migrating three production apps I am not going back. The store definition is flatter, the TypeScript inference actually works, and there is no more mutations boilerplate. Here is the same counter store written both ways so you can see the difference.',
  },
  {
    uid: 'art_med_3',
    feed_uid: 'feed_medium_vuejs',
    title: 'Server-Side Rendering Vue with Nitro',
    image_url: 'https://picsum.photos/id/2/600/340',
    published_at: '2026-06-20T16:45:00Z',
    post_url: 'https://medium.com/example/vue-ssr-nitro',
    content:
      'Nitro powers the server layer of Nuxt, but you can use it standalone to add SSR to a plain Vue app. This walkthrough sets up a minimal Nitro server, renders the Vue app to a string on each request, and hydrates on the client.',
  },
  {
    uid: 'art_med_4',
    feed_uid: 'feed_medium_vuejs',
    title: 'Five Vue Performance Mistakes You Are Probably Making',
    image_url: 'https://picsum.photos/id/3/600/340',
    published_at: '2026-06-19T12:30:00Z',
    post_url: 'https://medium.com/example/vue-performance-mistakes',
    content:
      'Reactivity is cheap until it is not. The most common performance killer I see is making large, deeply nested objects reactive when a shallowRef would do. The second is unkeyed v-for lists that force full re-renders.',
  },
  {
    uid: 'art_med_5',
    feed_uid: 'feed_medium_vuejs',
    title: 'Typed Props and Emits: A Practical Guide',
    image_url: 'https://picsum.photos/id/4/600/340',
    published_at: '2026-06-18T09:05:00Z',
    post_url: 'https://medium.com/example/typed-props-emits',
    content:
      'With script setup and defineProps you get fully typed component contracts at no runtime cost. This guide covers generic components, typed emits, and how to share prop types across a component library.',
  },
  {
    uid: 'art_yt_1',
    feed_uid: 'feed_youtube',
    title: 'I Rebuilt My Portfolio in Vue 3 (Full Process)',
    image_url: 'https://i.ytimg.com/vi/aqz-KE-bpKQ/hqdefault.jpg',
    published_at: '2026-06-23T14:00:00Z',
    post_url: 'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
    content:
      'In this video I rebuild my developer portfolio from scratch using Vue 3, Vite and Tailwind. Timestamps: 00:00 Intro, 02:13 Project setup, 08:40 Building the layout, 21:05 Animations, 34:50 Deploy. Links and source code are in the description below.',
  },
  {
    uid: 'art_yt_2',
    feed_uid: 'feed_youtube',
    title: 'Vite vs Webpack in 2026 - Is It Even Close?',
    image_url: 'https://i.ytimg.com/vi/ScMzIvxBSi4/hqdefault.jpg',
    published_at: '2026-06-20T17:30:00Z',
    post_url: 'https://www.youtube.com/watch?v=ScMzIvxBSi4',
    content:
      'A head to head benchmark of Vite and Webpack on a real medium-sized app. We measure cold start, HMR latency and production build times. Spoiler: it is not close for dev, but the prod gap is smaller than you think.',
  },
  {
    uid: 'art_yt_3',
    feed_uid: 'feed_youtube',
    title: '10 VS Code Extensions Every Vue Dev Needs',
    image_url: 'https://i.ytimg.com/vi/9bZkp7q19f0/hqdefault.jpg',
    published_at: '2026-06-17T11:00:00Z',
    post_url: 'https://www.youtube.com/watch?v=9bZkp7q19f0',
    content:
      'My current VS Code setup for Vue work in 2026. Covers Volar, the official Vue extension, snippets, and a couple of lesser known tools that save me hours every week.',
  },
  {
    uid: 'art_yt_4',
    feed_uid: 'feed_youtube',
    title: 'Building a Real-Time Chat with Vue and WebSockets',
    image_url: 'https://i.ytimg.com/vi/kJQP7kiw5Fk/hqdefault.jpg',
    published_at: '2026-06-14T15:20:00Z',
    post_url: 'https://www.youtube.com/watch?v=kJQP7kiw5Fk',
    content:
      'Live coding a real-time chat app. We use a native WebSocket connection, handle reconnection, and keep the message list reactive with a composable. Full source in the description.',
  },
  {
    uid: 'art_yt_5',
    feed_uid: 'feed_youtube',
    title: 'Stop Writing Watchers - Use Computed Instead',
    image_url: 'https://i.ytimg.com/vi/RgKAFK5djSk/hqdefault.jpg',
    published_at: '2026-06-11T13:45:00Z',
    post_url: 'https://www.youtube.com/watch?v=RgKAFK5djSk',
    content:
      'A short explainer on why most watchers in Vue codebases should be computed properties instead. I refactor three real examples and explain the reactivity reasoning behind each.',
  },
  {
    uid: 'art_rdt_1',
    feed_uid: 'feed_reddit_onepiece',
    title: '[Theory] What the latest chapter reveals about the Void Century',
    image_url: 'https://picsum.photos/id/24/600/340',
    published_at: '2026-06-23T09:30:00Z',
    post_url: 'https://www.reddit.com/r/OnePiece/comments/example1',
    content:
      'Putting together the poneglyph clues from the last arc, I think we finally have a timeline for the Void Century. Here is my full breakdown with panel references. Edit: thanks for the awards, adding a TL;DR at the top.',
  },
  {
    uid: 'art_rdt_2',
    feed_uid: 'feed_reddit_onepiece',
    title: 'Fan art: Gear 5 Luffy in watercolor',
    image_url: 'https://picsum.photos/id/30/600/340',
    published_at: '2026-06-22T18:10:00Z',
    post_url: 'https://www.reddit.com/r/OnePiece/comments/example2',
    content:
      'Spent about 20 hours on this one. Watercolor on cold press paper, A3 size. Prints available if anyone is interested, link in comments.',
  },
  {
    uid: 'art_rdt_3',
    feed_uid: 'feed_reddit_onepiece',
    title: 'Current Chapter Discussion - Spoilers',
    image_url: 'https://picsum.photos/id/48/600/340',
    published_at: '2026-06-22T02:00:00Z',
    post_url: 'https://www.reddit.com/r/OnePiece/comments/example3',
    content:
      'Official discussion thread for this week\'s chapter. All spoilers allowed inside. Please keep theory posts in their own threads to avoid clutter.',
  },
  {
    uid: 'art_rdt_4',
    feed_uid: 'feed_reddit_onepiece',
    title: 'Just finished a full reread - some thoughts on early foreshadowing',
    image_url: 'https://picsum.photos/id/57/600/340',
    published_at: '2026-06-21T20:40:00Z',
    post_url: 'https://www.reddit.com/r/OnePiece/comments/example4',
    content:
      'Did a full reread over three weeks and the amount of setup planted hundreds of chapters early is staggering. A few examples that hit different the second time around.',
  },
  {
    uid: 'art_rdt_5',
    feed_uid: 'feed_reddit_onepiece',
    title: 'Which arc do you think is the most underrated?',
    image_url: 'https://picsum.photos/id/64/600/340',
    published_at: '2026-06-21T07:15:00Z',
    post_url: 'https://www.reddit.com/r/OnePiece/comments/example5',
    content:
      'Everyone praises the big famous arcs but I want to hear which of the quieter ones you think deserve more love. I will start: the one everyone skips on reread is actually full of great character work.',
  },
]
