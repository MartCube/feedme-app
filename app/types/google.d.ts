// Google Identity Services is a script tag, not a package, so window.google has
// no types of its own. Only the members pages/login.vue calls are declared —
// this is a hand-written companion to the generated api.d.ts beside it.
export {}

declare global {
  interface GoogleCredentialResponse {
    // The id_token JWT. POST /auth/google verifies it and answers with one of
    // our own tokens.
    credential: string
    select_by: string
  }

  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: GoogleCredentialResponse) => void
            ux_mode?: 'popup' | 'redirect'
          }) => void
          // The chrome is Google's: theme, size, shape, text and width are the
          // whole surface. A custom button would mean the OAuth code flow.
          renderButton: (parent: HTMLElement, options: {
            theme?: 'outline' | 'filled_blue' | 'filled_black'
            size?: 'small' | 'medium' | 'large'
            shape?: 'rectangular' | 'pill' | 'circle' | 'square'
            text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
            width?: number
          }) => void
        }
      }
    }
  }
}
