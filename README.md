# Field Shift

**Decision support for crop rotation, powered by NASA Earth observations.**

Built for the NASA Space Apps Challenge 2026: *Adapting Farms with NASA Data*. Pilot region: Dakahlia, Egypt.

## Phase 1 scope

- Landing page explaining the project
- Authentication (sign up / log in / log out) with Supabase
- Protected, empty dashboard

## Tech stack

Next.js 16 (App Router, TypeScript) · Tailwind CSS v4 · shadcn/ui · `@supabase/ssr` · Playwright (E2E)

## Getting started

```bash
npm install
npm run dev        # http://localhost:3000
```

Environment lives in `.env.local` (not committed):

```
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
```

### Supabase configuration

1. **Authentication → Sign In / Providers → Email**: enabled. The "Confirm email"
   toggle controls whether sign-up requires an email link before the first login.
2. **Authentication → URL Configuration**:
   - Site URL: `http://localhost:3000`
   - Redirect URLs: `http://localhost:3000/auth/callback` (required for the
     confirmation-link flow when Confirm email is ON)
3. The free-tier built-in email service sends ~2 emails/hour. For real testing
   or production, set a custom SMTP under **Authentication → SMTP Settings**.

## Project structure

```
src/
  proxy.ts                      # Next 16 "proxy" (was middleware): locale redirect, session refresh, route guards
  lib/i18n.ts                   # locales (ar default, en) + full dictionaries
  lib/supabase/                 # browser client, server client, updateSession helper
  app/
    [locale]/                   # locale-prefixed routes: /ar (default), /en
      layout.tsx                # root layout: dir=rtl/ltr, Arabic (Cairo) + Latin fonts
      page.tsx                  # landing page
      login/page.tsx            # log in
      signup/page.tsx           # sign up (email + password only)
      dashboard/                # protected layout + empty-state dashboard
    auth/callback/route.ts      # email-confirmation code exchange
  components/
    landing/                    # hero, problem, how-it-works, data-sources, principles, pilot, footer
    auth/                       # auth shell, login form, signup form
    dashboard/                  # logout button
    brutal-button.tsx           # shared button with sliding hover panel (RTL-aware)
    language-switcher.tsx       # /ar ↔ /en toggle on the current page
    ui/                         # shadcn components
```

## Internationalization (Arabic default)

- URLs are locale-prefixed: `/ar/...` (default) and `/en/...`. Bare paths like
  `/login` redirect to `/ar/login` in `proxy.ts`; unknown locales 404.
- The `<html>` element gets `lang` and `dir` (`rtl` for Arabic) from the URL.
- All copy lives in typed dictionaries in `src/lib/i18n.ts`.
- Arabic uses the **Cairo** font; Latin pages use **Space Grotesk** (headings)
  and **Archivo** (body). Letter-spacing is disabled on Arabic (it breaks
  connected script), and hard shadows + the button slide panel mirror in RTL.

## Auth behavior

- `/dashboard` requires a session (server-side `getUser()`, enforced both in
  `proxy.ts` and `dashboard/layout.tsx`).
- `/login` and `/signup` redirect to `/dashboard` when already signed in.
- With **Confirm email ON** (current state): sign-up ends on a "check your
  email" screen; the confirmation link hits `/auth/callback` which exchanges
  the code for a session and lands on `/dashboard`.
- With **Confirm email OFF**: sign-up logs the user in immediately.

## Tests

```bash
npx playwright test                       # core suite (works in both email modes)
E2E_CONFIRM_OFF=1 npx playwright test     # full flow (requires Confirm email OFF)
```## Design system

Modern brutalism: thick black borders, flat color blocks, hard offset shadows.
Tokens (`--green-light #B7F5A0`, `--green-dark #14532D`, `--ink #0A0A0A`,
`--paper #F4FFF0`) are defined in `src/app/globals.css`. Buttons share
`brutal-button.tsx` and respect `prefers-reduced-motion`.

## Deployment (Vercel)

1. Push to GitHub, import into Vercel, add the two env variables.
2. In Supabase URL Configuration set the production Site URL and add
   `https://<your-domain>/auth/callback` as a redirect URL.
3. Keep **Confirm email** ON for production.

## Notes

- NASA does not endorse this project.
- The Supabase secret key (`sb_secret_...`) must never be committed or used in
  client code — only the publishable key is used here.
