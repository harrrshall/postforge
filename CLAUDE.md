# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Humanless** is an AI agent service business targeting Indian SMBs. It provides automated AI employees using OpenClaw (open-source AI agent framework) for customer service, scheduling, reporting, and business operations. The repo contains the marketing website, a promotional video composition, and business research/case studies.

## Repository Structure

- **`frontend/`** — Next.js 15 marketing website (landing page + case studies)
- **`humanless_demo/`** — Remotion video composition for a 47.7s promotional video
- **`casestudies/`** — Verified industry case study research (markdown)
- **`business-intelligence.md`** — Market analysis, competitive landscape, revenue strategy

## Frontend (Next.js)

### Commands
```bash
cd frontend
npm run dev      # Dev server
npm run build    # Production build
npm start        # Start production server
npm run lint     # ESLint
```

### Tech Stack
- Next.js 15.2.4 with App Router, React 19, TypeScript 5.8
- @calcom/embed-react for booking, react-icons
- Custom CSS only (no component library) — dark brutalist "Kinetic Monolith" design system

### Architecture
- `app/page.tsx` — Main landing page (~10K LOC): hero, services, integrations, pricing, Cal.com booking embed, WhatsApp CTAs
- `app/case-studies/` — Dynamic routes by sector (`[sector]/page.tsx`), data-driven from `data.ts` (6 sectors: healthcare, e-commerce, content, agencies, education, local-business)
- `app/case-studies/shell.tsx` — Shared UI shell for case study pages
- `app/globals.css` — Full design system: color palette (dark bg #09090b, accent orange #ff995f), typography (Space Grotesk, JetBrains Mono, Inter), dot grid overlays, tonal stacking depth
- `DESIGN.md` — Detailed design system specification; follow this when making UI changes

### Design Principles
- Dark mode only, no light variant
- Tonal stacking for depth (no shadows), minimal borders (ghost borders only)
- No rounded corners > 12px, no glows, no soft shadows
- Minimum 4.5:1 contrast ratio
- Typography: Space Grotesk for headers, JetBrains Mono for code/technical, Inter for body

## Humanless Demo (Remotion Video)

### Commands
```bash
cd humanless_demo
npm run dev      # Remotion Studio (interactive preview)
npm run build    # Bundle video composition
npm run lint     # ESLint + TypeScript check
```

### Tech Stack
- Remotion 4.0.441, React 19, TypeScript 5.9, Tailwind CSS 4.0
- @remotion/transitions (fade, slide, wipe, clock-wipe), @remotion/light-leaks

### Architecture
- `src/Root.tsx` — Composition registration: "HumanlessLaunch", 1920x1080, 30fps, 1432 frames (12 scenes, 8 transitions, 3 light leaks)
- `src/Composition.tsx` — All video scenes and animations
- `out/HumanlessLaunch.mp4` — Rendered output
- `remotion.config.ts` — JPEG image format, Tailwind v4 integration

## Key Business Context

- Target market: Indian SMBs (healthcare, e-commerce, agencies, education, local business)
- Pricing tiers: ₹4,999 (Starter), ₹14,999 (Pro), Custom (Enterprise)
- Integrations showcased: WhatsApp, Telegram, Notion, Google Calendar, Razorpay, Zoho, Stripe, Shopify, Jira, Airtable, Slack, Discord, Email
- CTAs link to WhatsApp and Cal.com booking
