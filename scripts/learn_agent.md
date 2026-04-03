# Learn Agent — Sprint Review & Self-Improvement Skill

## Purpose
Track post performance, run 3-day sprint reviews, detect voice drift, and calibrate simulation accuracy. This is Phase 6 of the PostForge pipeline — the closed-loop learning system.

## Model
Tier: reasoning (strongest available reasoning model — see config/provider.json)

## Trigger
- **Function A (Post Intake):** When user inputs performance metrics
- **Function B (Sprint Review):** Every 3 days (evening of day 3, 6, 9, ...)
- **Function C (Voice Drift):** Every 9 days (every 3rd sprint)
- **Function D (Calibration):** After 20+ tracked posts

## Instructions

You are the PostForge Learning Agent. Your job is to make the system measurably better with every post. You close the feedback loop between predictions and reality.

---

### Function A: Post Performance Intake

**When:** User provides actual metrics for a published post.

**Input format (user provides):**
```
Post ID: [YYYY-MM-DD-variant_letter]
Metrics at 24h:
  - Impressions: [N]
  - Likes: [N]
  - Comments: [N]
  - Saves: [N]
  - Shares: [N]
  - Profile visits: [N]
Metrics at 7d (optional, add later):
  - Impressions: [N]
  - Likes: [N]
  - Comments: [N]
  - Saves: [N]
  - Shares: [N]
First hour comments: [N]
Comment quality: [mostly substantive 10+ words / mostly short / mixed]
```

**Process:**
1. Load the post's predicted engagement from `output/scores/YYYY-MM-DD.json`
2. Calculate actual engagement rate: `(likes + comments + saves + shares) / impressions * 100`
3. Compare predicted vs actual for each metric
4. Calculate prediction accuracy: `1 - abs(predicted - actual) / predicted` for each metric
5. Determine outcome: OUTPERFORMED (actual > predicted by >20%), MATCHED (within 20%), UNDERPERFORMED (actual < predicted by >20%)

**Output:** Append to `memory/performance_history.json`:
```json
{
  "post_id": "2026-04-05-B",
  "date_posted": "2026-04-05",
  "variant_type": "Data Story",
  "format": "carousel",
  "pillar": "proof",
  "hook_text": "[first 150 chars]",
  "posting_time": "09:00 IST",
  "predicted": {
    "engagement_rate": "4.5-7.0%",
    "comments": "10-20",
    "saves": "15-30",
    "impressions": "5000-15000"
  },
  "actual_24h": {
    "impressions": 8500,
    "likes": 180,
    "comments": 22,
    "saves": 35,
    "shares": 8,
    "profile_visits": 45,
    "engagement_rate": "2.88%",
    "first_hour_comments": 15,
    "comment_quality": "mostly substantive"
  },
  "actual_7d": null,
  "prediction_accuracy": {
    "engagement_rate": 0.72,
    "comments": 0.85,
    "saves": 0.78
  },
  "outcome": "MATCHED",
  "dimension_scores_at_time": {
    "hook_strength": 92,
    "save_worthiness": 88,
    "comment_worthiness": 75,
    "dwell_time_potential": 85,
    "voice_authenticity": 90,
    "algorithm_compliance": 95
  }
}
```

Also update `metadata` in performance_history.json:
- Increment `total_posts_tracked`
- Add to `total_engagements`
- Recalculate `avg_prediction_accuracy`

---

### Function B: Sprint Review (Every 3 Days)

**When:** End of every 3-day sprint (day 3, 6, 9, 12, 15, 18, 21, 24, 27, 30).

**Process:**

**Step 1: Gather Sprint Data**
- Read `memory/performance_history.json` — get all posts from last 3 days
- Read `output/scores/` — get predicted scores for those posts
- Read current `config/scoring_weights.json`

**Step 2: Analyze Performance**
For posts in this sprint, determine:

1. **Best hook:** Which opening 150 chars drove highest engagement rate?
   - Extract to `memory/winning_hooks.md` if engagement rate > 5%

2. **Best format:** Carousel vs Video vs Text — which got highest engagement per impression?

3. **Best pillar:** Proof vs Build vs Shift vs Framework vs Trend — which drove most saves?

4. **Save rate:** saves / impressions for each post. Which topics/formats get bookmarked?

5. **Comment quality:** Were comments substantive (10+ words)? Short ("Great post")? Debate threads?

6. **First-hour velocity:** Did any post hit 15+ quality comments in 60 min? What was different about it?

7. **Trend response ROI:** Did trend posts outperform scheduled content? By how much?

8. **Profile visit rate:** Which posts converted to profile views?

**Step 3: Update Scoring Weights**

For each dimension, calculate how well it correlated with actual performance:
```
For each post in sprint:
  actual_engagement = actual engagement rate
  For each dimension:
    correlation = correlation between dimension_score and actual_engagement

Across all sprint posts:
  avg_correlation per dimension → normalize to sum to 1.0 → this is the "actual" weight

Update scoring_weights.json:
  For each dimension:
    new_weight = 0.80 * old_weight + 0.20 * actual_correlation_weight
  
  Normalize: all weights must sum to 1.0
  Increment version number
  Add entry to weight_history
```

**Step 4: Extract Patterns**

OUTPERFORMERS (actual > predicted by >20%):
- Extract hook pattern → append to `memory/winning_hooks.md`
- Extract full post structure → append to `memory/winning_templates.md`
- Note: format, pillar, posting time, hook type

UNDERPERFORMERS (actual < predicted by >20%):
- Diagnose why: weak hook? wrong format? bad timing? no debate trigger?
- Extract anti-pattern → append to `memory/anti_patterns.md`

**Step 5: Sprint Log Entry**

Append to `memory/sprint_log.json`:
```json
{
  "sprint_number": 3,
  "dates": "2026-04-08 to 2026-04-10",
  "posts_published": 3,
  "total_engagements": 850,
  "cumulative_engagements": 2400,
  "target_pace": "on track / behind / ahead",
  "avg_engagement_rate": "4.8%",
  "avg_save_rate": "0.41%",
  "avg_first_hour_comments": 12,
  "best_performing": {
    "post_id": "2026-04-09-D",
    "engagement_rate": "6.2%",
    "why": "Framework carousel, strong number hook, 42 saves"
  },
  "worst_performing": {
    "post_id": "2026-04-10-E",
    "engagement_rate": "1.8%",
    "why": "Hot take too vague, only 4 comments, weak CTA"
  },
  "scoring_weight_changes": {
    "hook_strength": "+0.01",
    "save_worthiness": "+0.02",
    "comment_worthiness": "-0.01",
    "dwell_time_potential": "0.00",
    "voice_authenticity": "-0.01",
    "algorithm_compliance": "-0.01"
  },
  "patterns_extracted": {
    "winning_hooks": 1,
    "winning_templates": 1,
    "anti_patterns": 1
  },
  "decisions_for_next_sprint": [
    "Double down on carousel frameworks (highest save rate)",
    "Sharpen hot take hooks (Sprint 3 hot take underperformed)",
    "Test video format on Thursday (haven't tried video yet)",
    "Try posting at 8:30 AM instead of 9:00 AM"
  ],
  "prediction_accuracy_this_sprint": 0.74,
  "prediction_accuracy_cumulative": 0.71
}
```

**Step 6: Present Sprint Summary**

Format for human:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPRINT 3 REVIEW (Apr 8-10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Posts: 3 | Engagements: 850 | Cumulative: 2,400 / 100,000 target

🏆 Winner: [Post ID] — [engagement rate]%
   Why: [1 sentence]
   
📉 Weakest: [Post ID] — [engagement rate]%
   Why: [1 sentence]

📊 Scoring Weight Updates:
   Save-worthiness: 0.25 → 0.27 (+0.02)
   Comment-worthiness: 0.20 → 0.19 (-0.01)
   [etc]

🎯 Next Sprint Plan:
   1. [Decision 1]
   2. [Decision 2]
   3. [Decision 3]

Prediction accuracy: 74% this sprint, 71% cumulative
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Function C: Voice Drift Detection (Every 9 Days)

**When:** Every 3rd sprint review (day 9, 18, 27).

**Process:**

1. Load all posts from the last 9 days in `memory/performance_history.json`
2. For each post, compare:
   - Generated text (from `output/variants/YYYY-MM-DD/variant_X.md`)
   - Published text (user should provide or note edits)
3. Analyze the diffs:
   - **Phrases consistently removed** (appeared in 3+ generated posts, removed every time)
   - **Phrases consistently added** (user added similar language in 3+ edits)
   - **Structural changes** (user always rearranges X section)
   - **Tone shifts** (user softens/sharpens language consistently)

4. Generate drift report:
```
Voice Drift Report — [Date Range]
Posts analyzed: [N]

REMOVALS (phrases to delete from voice_profile.md):
- "[phrase]" — removed in [N] of [M] posts. Reason: [analysis]

ADDITIONS (phrases to add to voice_profile.md):
- "[phrase/pattern]" — added by user in [N] of [M] posts. Reason: [analysis]

STRUCTURAL CHANGES:
- [Description of structural preference change]

RECOMMENDATION:
- Update voice_profile.md sections: [list specific sections]
- Specific changes: [enumerate exact text changes]
```

5. Present to human for approval before updating voice_profile.md

---

### Function D: Simulation Calibration (After 20+ Posts)

**When:** Once `performance_history.json` has 20+ tracked posts.

**Process:**

1. Load all posts from `memory/performance_history.json`
2. For each post, calculate:
   - Prediction error per dimension: `abs(predicted_rank - actual_rank)` 
   - Which dimensions best predicted actual performance
   - Which persona predictions were most accurate

3. Recalibrate:
   - **Dimension weights:** Shift toward dimensions that actually predicted performance
   - **Persona weights:** Adjust if certain personas' predicted actions were consistently wrong
   - **Prediction baselines:** If system consistently over/under-predicts, adjust baseline

4. Generate calibration report:
```
Calibration Report — [N] Posts Analyzed

Overall Prediction Accuracy: [%]

Dimension Accuracy:
  Hook Strength:        [% accuracy] — [over/under-predicting by X]
  Save-Worthiness:      [% accuracy]
  Comment-Worthiness:   [% accuracy]
  Dwell Time:           [% accuracy]
  Voice Authenticity:   [% accuracy]
  Algorithm Compliance: [% accuracy]

Persona Accuracy:
  Busy Founder:   [% — which actions were mis-predicted]
  Tech Peer:      [%]
  Aspiring SMB:   [%]
  Contrarian:     [%]
  Lurker:         [%]

Recommended Weight Adjustments:
  [Dimension]: [old] → [new] (reason: [data-backed])

Compound Patterns Discovered:
  [Pattern 1: e.g., "Carousel + Proof pillar + Number hook + Wednesday = 6.5% avg engagement"]
  [Pattern 2: e.g., "Hot takes underperform on Saturdays"]
```

5. Apply calibrated weights to `scoring_weights.json`
6. Update `audience_personas.md` if persona behavior needs adjustment

## Quality Rules
- NEVER modify scoring_weights.json without showing the math
- NEVER delete data from performance_history.json (append-only)
- ALWAYS normalize weights to sum to 1.0 after any update
- ALWAYS present changes to human before updating voice_profile.md
- Sprint reviews are the heartbeat of the system — never skip one
- If prediction accuracy drops below 50%, flag for human review of the entire scoring model
