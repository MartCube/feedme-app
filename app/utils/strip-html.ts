// RSS summaries are HTML — Reddit wraps a whole <table> around every post — so
// the reader was showing literal markup once it moved off the mock data's plain
// text. Rendering it raw is not the fix: the summary comes from an arbitrary
// third-party feed and nothing sanitises it, so v-html here would be an XSS
// hole. Until T10 serves extracted article text, the detail view shows the
// summary as plain text.
//
// Parsed rather than regexed: entities decode properly and no tag spelling is
// missed. DOMParser builds an inert document — nothing in it executes.
export function stripHtml(html: string): string {
  if (!import.meta.client) return html
  const parsed = new DOMParser().parseFromString(html, 'text/html')
  return parsed.body.textContent?.replace(/\s+/g, ' ').trim() ?? ''
}
