# CB Odontología y Estética

Website and online appointment system for a dental practice in Santa Fe, Argentina.

> This is a real client project and a portfolio piece. The repository is public so it can be reviewed by recruiters and prospective clients — it is **not** open source. See [License](#license).

## Screenshots

_Pending — screenshots and a live demo link will be added once the site is deployed._

## About

CB Odontología y Estética is the practice of Dr. Cecilia Brassesco, offering general and aesthetic dentistry in Santa Fe, Argentina.

The site has a single job: make booking an appointment the natural next step. Everything else — presenting the practice, building trust, easing the anxiety around dental visits — exists to support that one action.

This project covers the full digital presence: a brand-aligned website and the integrated booking system the practice uses day to day.

## Tech stack

- **Frontend** — HTML, CSS, JavaScript. A single-page, mobile-first landing built from modular blocks, designed to scale into a multi-page site later.
- **Backend** — Supabase (backend-as-a-service): database, authentication, and access control.
- **Notifications** — automated email for booking confirmations, cancellations, and reminders.
- **Secondary channel** — WhatsApp for pre-booking questions, currently handled manually.

## Features

- Patient self-booking on the web, with Google sign-in.
- Admin panel for the practice to manage appointments and define availability (base hours plus exceptions such as holidays or time off).
- Variable-length appointments set by the practitioner, on a 30-minute block model.
- Automated email confirmations, cancellations, and reminders.
- Single source of truth — every booking channel writes through one backend, so appointments can't collide.

## Architecture

All booking channels (the web today, WhatsApp later) read and write through one backend that owns the rules: no double-bookings, availability is respected, and a cancellation frees the slot again. Centralizing the logic keeps the channels from stepping on each other and makes the system straightforward to grow.

**The browser never talks to the database.** Every table has row-level security on with no policies at all, so the client-side key reads nothing; the backend — Supabase Edge Functions — holds the only key that gets through. Table permissions are granted one verb at a time, in a versioned migration that ships alongside the feature needing it, so no grant exists without a written reason next to it.

_An architecture diagram will be added here._

## API

The gatekeeper endpoints built so far:

| Endpoint | Session | What it answers |
|---|---|---|
| `GET /tratamientos` | not required | The treatments the practice offers. Public on purpose — the same list appears on the landing page. |
| `GET /horarios-disponibles` | not required | The half-hour grid for one practitioner over a date range, each block marked `libre`, `ocupado`, `no_entra` or `fuera_de_plazo`. Public on purpose too: a patient should see whether a slot exists *before* signing up. |
| `GET /mis-pacientes` | **required** | The patients booked under the caller's address — one address can cover several people, such as a parent booking for their children. Returns id and name only. |

Appointment length is never accepted from the request: the backend looks it up by treatment id. Otherwise a hand-crafted request could book a four-hour checkup and wreck the calendar.

## Project status

In active development.

- **Done** — data model (7 tables, integrity constraints and an exclusion constraint that makes overlapping appointments impossible at the database level), brand identity, system architecture, access-control model.
- **In progress** — the booking endpoint (`POST /reservar`) and its three notification emails.
- **Next** — cancellation by non-guessable link, the admin panel, deployment, and (later) WhatsApp bot integration.

## Author

**Juan Manuel Brassesco**
[github.com/juanmbrassesco-dev](https://github.com/juanmbrassesco-dev)

## License

© 2026 Juan Manuel Brassesco. All rights reserved.

This repository is published for portfolio and review purposes only. The project is built for a specific client and is not licensed for reuse, redistribution, or modification. You're welcome to read through the code; please don't copy or repurpose it without permission.
