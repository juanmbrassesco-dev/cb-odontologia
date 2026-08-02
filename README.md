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

_An architecture diagram will be added here._

## Project status

In active development.

- **Done** — data model, brand identity, system architecture.
- **In progress** — front-end build and Supabase setup.
- **Next** — booking flow, deployment, and (later) WhatsApp bot integration.

## Author

**Juan Manuel Brassesco**
[github.com/juanmbrassesco-dev](https://github.com/juanmbrassesco-dev)

## License

© 2026 Juan Manuel Brassesco. All rights reserved.

This repository is published for portfolio and review purposes only. The project is built for a specific client and is not licensed for reuse, redistribution, or modification. You're welcome to read through the code; please don't copy or repurpose it without permission.
