# Trend Triggers — What Qualifies for Hijacking

## Urgency Levels

### FIRE — Post within 2 hours
Speed is everything. First mover on a trend = 5-10x normal reach.

**Triggers:**
- OpenClaw critical security vulnerability disclosed (CVE with CVSS 9.0+)
- Indian government announces AI regulation affecting SMBs
- Major AI company announcement directly impacting small business (Anthropic, OpenAI, Google)
- LinkedIn itself announces algorithm change
- Viral incident involving AI agents (positive or negative)
- India-specific AI policy (DPDP Act enforcement, AI advisory)

**Response format:** Text post (fastest to publish). Hook: Bold opinion on the news. Body: What it means for Indian SMBs.
**Quality bar:** 150-char hook must work. Voice must be authentic. 360Brew rules still apply. Skip full 6-variant generation — produce 2 variants max.

### HOT — Post within 6 hours
Still time-sensitive but allows for slightly more polish.

**Triggers:**
- Viral LinkedIn post in AI/Indian business niche (1000+ reactions)
- Trending Twitter/X topic in #AI or #IndianStartups
- Major competitor move (new AI agent service launches in India)
- Industry report released (McKinsey, Deloitte, Nasscom AI report)
- High-profile AI failure or success story in the news

**Response format:** Text post or quick video response. Can include data from research agent.
**Quality bar:** Full voice_profile match. At least hook + comment-worthiness scored.

### WARM — Post within 24 hours
Not urgent but timely. Can be a high-quality scheduled post tied to the trend.

**Triggers:**
- Startup funding round in AI/automation space (India or global)
- New case study published (by consulting firm or named company)
- Industry conference or event generating LinkedIn buzz
- Platform feature launch (LinkedIn, WhatsApp Business, etc.)
- Competitor pricing change or feature announcement

**Response format:** Carousel or detailed text post. Full research brief. Full scoring.
**Quality bar:** Full PostForge pipeline. All 6 dimensions scored.

### COOL — Add to research backlog
Not time-sensitive. Interesting angle for future content.

**Triggers:**
- Interesting Reddit/HN discussion in adjacent topic
- Academic paper published on AI agents/productivity
- Slow-burn trend gaining momentum (not yet peak)
- Content idea from community comments or DMs

**Response format:** N/A — goes to `research/briefs/backlog.md` for future sprint planning.
**Quality bar:** N/A.

## Detection Sources (Scanned Every 4 Hours)

| Source | What to Monitor | Tool |
|--------|----------------|------|
| LinkedIn News | Trending topics with reader counts | Agent-Reach LinkedIn MCP |
| Twitter/X | #AI, #IndianStartups, #SMB, #OpenClaw trending | Agent-Reach Twitter CLI |
| Reddit | r/india hot, r/artificial hot, r/smallbusiness hot | Agent-Reach rdt-cli |
| Hacker News | Front page AI/agent stories | Agent-Reach / WebSearch |
| Google News | Alerts: "OpenClaw", "AI agents India", "MSME automation" | WebSearch |
| LinkedIn feed | Viral posts from competitors/peers (1000+ reactions) | Manual / Agent-Reach |

## Angle Framework for Trend Response

When responding to a trend, always connect back to Humanless's expertise:

1. **What happened** (2-3 sentences, factual)
2. **Your unique take** (how this affects Indian SMBs / AI agents)
3. **Insight only a builder would know** (technical or business depth)
4. **CTA** (debate-triggering question tied to the trend)

Template:
```
[HOOK: Bold opinion on the news, <150 chars, specific]

[What happened — 2-3 sentences]

[Your take — how this changes things for Indian SMBs]

[Insight from building Humanless — what most people miss]

[CTA: Question that invites debate from peers]
```
