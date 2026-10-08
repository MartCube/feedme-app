// The feed page's views live under /feed/:uid/info/… — the page itself, its
// edit form and delete confirm, and one source's page and remove confirm. This
// names the view a path's tail means and where Back from it goes, shared by the
// mobile page (swipe-back) and the panels (the back button), which must agree.
export type InfoView = 'info' | 'edit' | 'delete' | 'source' | 'remove'

export function infoView(rest: string[]): InfoView {
  if (rest[0] === 'edit') return 'edit'
  if (rest[0] === 'delete') return 'delete'
  if (rest[0] === 'source' && rest[1]) return rest[2] === 'remove' ? 'remove' : 'source'
  return 'info'
}

export function infoBack(uid: string, rest: string[]): string {
  const root = `/feed/${uid}/info`
  switch (infoView(rest)) {
    case 'info': return `/feed/${uid}`
    case 'delete': return `${root}/edit`
    case 'remove': return `${root}/source/${rest[1]}`
    default: return root
  }
}

// vue-router hands a catch-all back as an array, a lone string, or nothing.
export function restOf(param: string | string[] | undefined): string[] {
  if (Array.isArray(param)) return param.filter(Boolean)
  return param ? [param] : []
}
