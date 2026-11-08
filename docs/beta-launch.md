# Beta Launch Checklist

What has to exist outside the code before strangers can use FeedMe: friends, a post on
social media or a forum, a few potential investors. Sized for **under 100 users**, on free
tiers wherever one is good enough. The one cost is the domain (about $10–15 a year).

Hosting (where the api, database, worker and imgproxy run) is its own deploy task and isn't
decided here. This page lists only what the app needs from it.

## 1. Domain

Needed for two things: the address people open, and sending email that lands in inboxes.
Free subdomains like `*.vercel.app` or `*.netlify.app` can host the site but **can't send
email**, because an email service has to verify DNS records you control.

- [ ] Buy a domain (Porkbun, Namecheap, Cloudflare). Some endings like `.xyz` cost $1–3 for
      the first year, but renewals cost more.
- [ ] Point it at the host once hosting is chosen: the app on the root (or `app.`), the api
      and imgproxy on their own subdomains (e.g. `api.`, `img.`).

## 2. Email

The app sends two emails: **confirm your email** (after sign-up) and **reset your password**.
In dev they land in Mailpit at http://localhost:8025 (`docker compose up -d mailpit`). Nothing
is sent for real.

**Recommended: Resend, free plan** (3,000 a month, 100 a day at the time of writing; check
when signing up). The free plan without a verified domain only delivers to your own address,
so it can't send to users.

- [ ] Create a Resend account and add the domain. Paste the DNS records it shows (SPF,
      DKIM) at your registrar, then wait for "Verified".
- [ ] Create an API key with sending access.
- [ ] Set in the api's environment:

```
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=465
EMAIL_USE_SSL=1
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=<the API key>
DEFAULT_FROM_EMAIL=FeedMe <noreply@your-domain>
```

**Free fallback: a Gmail account.** Works without a domain and is enough for under 100 users
(about 500 emails a day), but mail comes from `@gmail.com` and Google may lock an account it
thinks is sending automated mail.

- [ ] Create the Gmail account and turn on 2-Step Verification (required for app passwords).
- [ ] Google Account → Security → App passwords → create one.
- [ ] Set:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_HOST_USER=<the gmail address>
EMAIL_HOST_PASSWORD=<the 16-character app password>
DEFAULT_FROM_EMAIL=FeedMe <the gmail address>
```

Moving from Gmail to Resend later only changes these values. No code changes.

- [ ] Send yourself a reset email from the deployed app and check it arrives, not in spam,
      and that its link opens the app.

## 3. Settings the deploy must set

Backend (api, worker and scheduler all read the same environment):

- [ ] `SECRET_KEY`: long and random. It also signs the email links, so changing it later
      voids every link already sent.
- [ ] `DEBUG=0`, `ALLOWED_HOSTS=api.<domain>`
- [ ] `APP_URL=https://<domain>`: the base of the links in emails.
- [ ] `CORS_ALLOWED_ORIGINS=https://<domain>`
- [ ] `IMGPROXY_KEY`, `IMGPROXY_SALT` (new random hex, not the compose dev values),
      `IMGPROXY_PUBLIC_URL=https://img.<domain>`
- [ ] `NUM_PROXIES`: the number of reverse proxies in front of the api (usually 1).
- [ ] The email block above.
- [ ] `GOOGLE_OAUTH_CLIENT_ID`, and add `https://<domain>` to the client's authorised
      JavaScript origins in Google Cloud Console.
- [ ] `YOUTUBE_API_KEY` (optional: without it, YouTube search by name finds nothing).

Frontend:

- [ ] `NUXT_PUBLIC_API_BASE=https://api.<domain>/api/v1`
- [ ] `NUXT_PUBLIC_GOOGLE_CLIENT_ID`: the same client id.
- [ ] `NUXT_PUBLIC_CONTACT_EMAIL`: the address Terms and Privacy tell people to write to.
      Without it the pages render without a contact line.

## 4. Before you share the link

- [ ] Sign up with a fresh address, confirm the email, sign out, reset the password, sign in
      with the new one, delete the account. Every step should work on a phone.
- [ ] Read `/terms` and `/privacy` once more. They're written to match what the backend
      actually stores. Change them when that changes, and update their "Last updated" date.
      They're plain-language beta pages, not reviewed by a lawyer.
