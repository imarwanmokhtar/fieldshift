# Field Shift

**Decision support for crop rotation, powered by NASA Earth observations.**

Field Shift helps farmers explore crop-rotation strategies that can improve soil health and strengthen resilience to changing temperature, rainfall and water conditions. It supports farmer judgment and local agricultural expertise. It does not replace them.

Built for the NASA Space Apps Challenge 2026: *Adapting Farms with NASA Data*. Pilot region: Dakahlia, Egypt.

---

## Scope of this repository (phase 1)

This phase contains only:

1. A **landing page** that explains the project.
2. **Authentication** (sign up, log in, log out) with Supabase.
3. An **empty dashboard** that a user reaches after creating an account or logging in.

Out of scope for now (planned for later phases):

- Collecting farm or field data during sign-up
- The Python recommendation engine
- Maps, charts and rotation comparison screens

Sign-up asks only for an email and a password. No profile or farm data is collected.

---

## Tech stack

| Layer | Choice |
| --- | --- |
| Framework | Next.js (App Router, TypeScript) |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Auth and database | Supabase (`@supabase/supabase-js`, `@supabase/ssr`) |
| Hosting | Vercel (recommended) |

---

## Getting started

### 1. Create the project

```bash
npx create-next-app@latest field-shift --typescript --tailwind --eslint --app --src-dir
cd field-shift
npx shadcn@latest init
npx shadcn@latest add button input label card sonner
npm install @supabase/supabase-js @supabase/ssr
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. In **Project Settings, API**, copy the project URL and the anon (publishable) key.
3. In **Authentication, Providers**, make sure **Email** is enabled.
4. In **Authentication, URL Configuration**, set:
   - Site URL: `http://localhost:3000`
   - Redirect URLs: `http://localhost:3000/auth/callback`
5. Optional for quick testing: turn off **Confirm email** so new users can log in immediately. Turn it back on for production.

### 3. Environment variables

Create `.env.local` in the project root:

```bash
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Never commit `.env.local`. Never put the service role key in client code.

### 4. Run it

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Suggested project structure

```
src/
  app/
    page.tsx                 # Landing page
    login/page.tsx           # Log in
    signup/page.tsx          # Sign up (email + password only)
    auth/callback/route.ts   # Supabase email confirmation / code exchange
    dashboard/
      layout.tsx             # Protected layout (redirects if not signed in)
      page.tsx               # Empty dashboard
  components/
    landing/                 # Hero, Problem, HowItWorks, DataSources, Principles, Footer
    ui/                      # shadcn components
    brutal-button.tsx        # Button with sliding hover effect
  lib/
    supabase/
      client.ts              # Browser client
      server.ts              # Server client (cookies)
      middleware.ts          # Session refresh helper
  middleware.ts              # Protects /dashboard, refreshes session
```

---

## Authentication flow

1. **Sign up** (`/signup`): email and password, then `supabase.auth.signUp`. No other fields.
2. **Log in** (`/login`): `supabase.auth.signInWithPassword`.
3. **Session handling**: `@supabase/ssr` stores the session in cookies. `middleware.ts` refreshes it on each request.
4. **Route protection**:
   - `/dashboard` requires a session. Otherwise redirect to `/login`.
   - `/login` and `/signup` redirect to `/dashboard` if already signed in.
5. **Dashboard**: after sign-up or log-in the user lands on an empty dashboard (see below).
6. **Log out**: `supabase.auth.signOut`, then redirect to `/`.

Use `supabase.auth.getUser()` on the server to check authentication, not `getSession()`.

---

## Dashboard (empty state)

The dashboard shows:

- A top bar with the Field Shift wordmark and a **Log out** button
- A greeting using the user's email
- A single empty-state card, for example: *"Your dashboard is empty. Farm and field tools are coming soon."*

No data tables are required in this phase. Row Level Security matters once user data is added, so enable it on every table you create later.

---

## Landing page content

The landing page explains what Field Shift does, using the challenge brief.

### Sections

1. **Hero**
   - Headline: *Choose your next crop with evidence, not guesswork.*
   - Subline: A decision-support tool that turns NASA Earth observations into clear crop-rotation options for farmers.
   - Buttons: **Get started** (to `/signup`) and **Log in**.
   - Small tag: *NASA Space Apps Challenge 2026*

2. **The problem**
   - Temperatures are shifting and rainfall is less predictable.
   - Water is getting scarcer and soils are losing health.
   - A crop that helps soil in one place can use too much water, bring disease, miss the market or fall outside the season somewhere else.

3. **What Field Shift does**
   - Compares **at least three rotation strategies**, including the farmer's current one.
   - For each strategy, shows: why it was suggested, what evidence supports it, expected benefits, information gaps, and risks that need local review.
   - Lets farmers set their own priorities, such as saving water, adding income or improving soil structure.

4. **How it works** (three steps)
   1. *Observe*: Satellite and climate data describe local conditions over many years.
   2. *Compare*: Rotation strategies are scored against heat, water, soil and market priorities.
   3. *Decide*: The farmer reviews clear explanations, with risks and uncertainty stated, and makes the final call.

5. **Data behind it** (a grid of cards, one per source)
   - **Landsat, MODIS/VIIRS, Sentinel-2**: crop vigor (NDVI), bare-field periods, seasonal change
   - **NASA POWER and ERA5**: temperature, radiation, humidity, frost and heat risk, water demand
   - **GPM / IMERG**: rainfall and extreme-storm patterns
   - **SMAP**: soil moisture trends
   - **ECOSTRESS**: land-surface temperature and evapotranspiration
   - **GRACE / GRACE-FO**: long-term water storage trends
   - **FAO GAEZ**: crop suitability by climate and soil

   Add a footnote: *Satellite data is coarse in places and does not replace ground measurements. Each result states its uncertainty.*

6. **Principles** (short statements)
   - Supports farmer judgment. It never replaces it.
   - Every recommendation shows its reasoning.
   - Gaps and risks are stated openly.
   - Local agricultural experts should review before decisions are made.

7. **Pilot region**: Dakahlia, Egypt (Nile Delta), with a short line on why it was chosen.

8. **Footer**: project name, NASA Space Apps Challenge 2026, team name, and a note that NASA does not endorse this project.

Keep copy short, plain and free of jargon. Explain terms such as NDVI and evapotranspiration in one sentence when they appear.

---

## Design system

**Style: modern brutalism.** Thick black borders, flat color blocks, hard offset shadows, oversized type, visible grid, no gradients, no soft blur.

### Colors

Define these as CSS variables and map them in `tailwind.config` / `globals.css`:

| Token | Role | Suggested value |
| --- | --- | --- |
| `--green-light` | Main backgrounds, highlights | `#B7F5A0` |
| `--green-dark` | Primary buttons, section blocks | `#14532D` |
| `--black` | Text, borders, shadows | `#0A0A0A` |
| `--paper` | Neutral surface | `#F4FFF0` |

Rules:
- Text is black on light green or paper, and paper on dark green.
- Borders are 2 to 4 px solid black.
- Shadows are hard offsets, for example `box-shadow: 6px 6px 0 var(--black)`, with no blur.
- Keep contrast at WCAG AA or better. Check the light green against black text.

### Typography

- Headlines: a heavy grotesque or mono face (for example *Space Grotesk*, *Archivo Black* or *JetBrains Mono*) via `next/font`.
- Body: a clean sans at 16 px or larger.
- Use uppercase and tight tracking for labels.

### Buttons with a sliding hover effect

All buttons share one component (`brutal-button.tsx`, built on the shadcn `Button`).

Behavior:
- Resting state: a flat color fill, a 3 px black border and a hard shadow.
- On hover, a second color panel **slides in from the left** behind the label, and the text color flips for contrast.
- On press, the button moves toward its shadow (`translate(4px, 4px)`, shadow shrinks to zero).

Implementation sketch (Tailwind):

```tsx
<button className="group relative overflow-hidden border-[3px] border-black bg-[--green-light] px-6 py-3 font-bold uppercase shadow-[6px_6px_0_#0A0A0A] transition-transform active:translate-x-[4px] active:translate-y-[4px] active:shadow-none">
  <span className="absolute inset-0 -translate-x-full bg-[--green-dark] transition-transform duration-300 ease-out group-hover:translate-x-0" />
  <span className="relative transition-colors duration-300 group-hover:text-[--paper]">
    Get started
  </span>
</button>
```

Respect `prefers-reduced-motion`: disable the slide and use an instant color change instead.

### Layout

- Full-width color blocks separated by thick black rules.
- A 12-column grid with large gutters. Cards are square-cornered with hard shadows.
- Mobile first. The landing page and auth forms must work at 360 px width.

---

## Deployment

1. Push the repository to GitHub.
2. Import it into Vercel and add the two environment variables.
3. In Supabase **URL Configuration**, add the production URL as the Site URL and add `https://<your-domain>/auth/callback` as a redirect URL.
4. Turn **Confirm email** on for production.

---

## Roadmap

- [ ] Farm and field onboarding (after sign-up)
- [ ] Python engine for data processing and recommendations
- [ ] Data harmonization to a common grid (NASA POWER, ERA5, Landsat/Sentinel-2, SMAP, IMERG)
- [ ] Rotation strategy comparison (at least three, including the current one)
- [ ] Priority sliders and scenario sliders (hotter, drier)
- [ ] Maps and time-series visualizations

---

## Data and attribution

Field Shift uses data and concepts from NASA Earth observation missions and Space Agency Partner resources. NASA does not endorse this project. Participants must follow the data use terms of each data source.

## License

To be decided by the team.
