# TechBallCamp: Game Design & Learning Framework
**Version:** 1.0  
**Purpose:** Football-training-inspired drill suite where SARA learns tremor patterns and user learns to control motor disabilities through progressive difficulty

---

## 1. Game Philosophy

TechBallCamp is **not a treatment tool**. It is a **co-learning system** where:

- **SARA learns** the user's tremor signature, fatigue patterns, and optimal sensitivity settings
- **User learns** their own capabilities and builds confidence through progressive challenge
- **Both improve together** — SARA's filter gets smarter, user's accuracy improves, filters become less necessary
- **Game is fun** — borrows pacing, reward systems, and progression from sports training culture

---

## 2. Visual & Audio Design

### 2.1 Aesthetic: Football Training Camp

The entire UI is themed around a **football coaching environment**:

- **Color Scheme:** Stadium grass (green), field markings (white/gold), scoreboard (bright, high-contrast)
- **Audio:** Coach whistle for drill start, crowd cheers for success, encouraging voice-over narration
- **UI Elements:** Scoreboard, coach avatar (optional), drill selector (like playbook), difficulty dial (like "level 1 - rookie", "level 5 - pro")
- **Metaphors:** 
  - Drills = football plays
  - Difficulty = "Rookie → Veteran → Pro → All-Star" progression
  - Tremor = "wind resistance" or "crowd noise" to filter out
  - Accuracy = "catch rate" or "completion %"

### 2.2 Accessibility-First Design

All elements must be:
- **High contrast** (ADA WCAG AAA compliant)
- **Resizable** (user can increase any element)
- **Audio + Visual** (every visual feedback has audio equivalent)
- **Keyboard-navigable** (no mouse-only interaction required)
- **Simple, clear language** (no jargon; "Hit the target" not "Achieve positional accuracy")

---

## 3. Drill Library (8 Core Drills)

### 3.1 Hold Steady (Baseline Tremor)

**Purpose:** Measure baseline resting tremor without movement demand.

**Mechanic:**
- Large circular target appears center-screen
- User moves cursor to target and **holds still** for 10 seconds
- Visual feedback: circle around cursor shows stability
  - Green ring = stable (cursor within 10px of center)
  - Yellow ring = slightly unstable
  - Red ring = unstable (cursor drifting >30px)

**Scoring:**
- Time in green = percentage accuracy
- Example: "8 seconds green, 2 seconds yellow" = 80% accuracy

**SARA's Learning:**
- Captures tremor amplitude and frequency at rest
- Detects any pattern (smooth wandering vs. oscillating tremor)
- Establishes baseline for this session

**Difficulty Levels:**
1. Rookie: 5-second hold, target is large (100px radius)
2. Veteran: 10-second hold, target medium (60px radius)
3. Pro: 15-second hold, target small (40px radius)
4. All-Star: 20-second hold, target very small (25px radius)

---

### 3.2 Precision Tap (Jitter Pattern)

**Purpose:** Measure how tremor affects rapid, accurate clicking.

**Mechanic:**
- Targets appear on screen one at a time
- User must click each target as quickly and accurately as possible
- Targets disappear after click or after 2-second timeout

**Scoring:**
- Hits / Total targets = hit rate %
- Average time to hit = response speed
- Distance from target center = accuracy (in pixels)

**SARA's Learning:**
- Captures jitter during clicking (acceleration spikes)
- Learns how quickly user can move and stop
- Detects if tremor increases with speed demand

**Difficulty Levels:**
1. Rookie: 40 targets, 3-second timeout, large targets (60px), targets spread far apart
2. Veteran: 40 targets, 2-second timeout, medium targets (40px), targets closer
3. Pro: 40 targets, 1.5-second timeout, small targets (25px), targets very close
4. All-Star: 40 targets, 1-second timeout, tiny targets (15px), targets overlapping

---

### 3.3 Sweep (Smooth Pursuit)

**Purpose:** Measure ability to make smooth, continuous movement vs. tremor-induced oscillation.

**Mechanic:**
- Horizontal line appears on screen
- User must move cursor to line and follow it smoothly across screen (left to right)
- Cursor should stay on line (±10px tolerance)
- Drill lasts 5-10 seconds depending on difficulty

**Scoring:**
- Time on line / Total time = line-following accuracy %
- Oscillation detected = # of tremor peaks while moving

**SARA's Learning:**
- Distinguishes intentional movement from tremor oscillation
- Learns user's "natural" smooth speed
- Captures tremor frequency specifically during movement (often different from resting)

**Difficulty Levels:**
1. Rookie: slow line (120px/sec), wide tolerance (±15px), straight line
2. Veteran: moderate line (180px/sec), normal tolerance (±10px), straight line
3. Pro: fast line (240px/sec), tight tolerance (±8px), gentle wave pattern
4. All-Star: very fast line (300px/sec), very tight tolerance (±5px), zigzag pattern

---

### 3.4 Rhythm (Timing Consistency)

**Purpose:** Measure timing precision and detect fatigue-induced timing drift.

**Mechanic:**
- Music beat plays in background
- Target appears and disappears on each beat (50ms visibility)
- User must click target on beat (±100ms window = "perfect", ±150ms = "good", ±200ms = "ok")

**Scoring:**
- Perfect hits (±100ms) count as 100 points
- Good hits (±100-150ms) count as 50 points
- Ok hits (±150-200ms) count as 25 points
- Miss = 0 points
- Total score / (40 beats * 100) = accuracy %

**SARA's Learning:**
- Establishes baseline reaction time (usually 200-300ms)
- Detects if timing gets worse as drill progresses (fatigue indicator)
- Learns if tremor is worse at specific beat timing

**Difficulty Levels:**
1. Rookie: 60 BPM beat, wide tolerance window (±150ms), 40 beats
2. Veteran: 90 BPM beat, medium tolerance (±125ms), 40 beats
3. Pro: 120 BPM beat, narrow tolerance (±100ms), 40 beats
4. All-Star: 150 BPM beat, very narrow tolerance (±75ms), 40 beats

---

### 3.5 Reaction Time (Stimulus Response)

**Purpose:** Measure baseline reaction time and how fatigue affects response speed.

**Mechanic:**
- Random delay (0.5-3 sec)
- Then stimulus appears (visual color change, audio beep, or both)
- User clicks target as fast as possible
- Measure time from stimulus to click

**Scoring:**
- Average reaction time in ms
- Consistency (std dev of reaction times)
- If reaction times increase during drill = fatigue indicator

**SARA's Learning:**
- Establishes user's baseline reaction time
- Detects if tremor causes delayed decision-making
- Learns how fatigue affects response speed

**Difficulty Levels:**
1. Rookie: audio stimulus (loud beep), large target (60px), 10 trials
2. Veteran: audio + visual (beep + color flash), medium target (40px), 15 trials
3. Pro: visual only (color flash), small target (25px), 20 trials
4. All-Star: subtle visual (border glow), tiny target (15px), 30 trials

---

### 3.6 Sweep with Obstacles (Ball Tracking)

**Purpose:** Measure smooth pursuit under dynamic conditions with obstacle avoidance.

**Mechanic:**
- Moving circle ("ball") travels across screen in unpredictable pattern
- User must keep cursor on circle
- Obstacles appear that user must avoid (move cursor around obstacle while following ball)
- Drill lasts 10-15 seconds

**Scoring:**
- Time on ball / Total time = tracking accuracy %
- Collisions with obstacles = count of obstacles hit

**SARA's Learning:**
- Learns how well user can predict movement and make corrections
- Detects tremor under dynamic conditions (harder than static)
- Learns reaction speed to obstacles

**Difficulty Levels:**
1. Rookie: slow ball (100px/sec), few obstacles (3), medium ball size (40px)
2. Veteran: moderate ball (150px/sec), moderate obstacles (5), medium ball (30px)
3. Pro: fast ball (200px/sec), many obstacles (8), small ball (25px)
4. All-Star: very fast ball (250px/sec), many obstacles (10), tiny ball (15px)

---

### 3.7 Multi-Tap (Rapid Repeated Clicks)

**Purpose:** Detect high-frequency tremor and tremor-induced repeat keypresses.

**Mechanic:**
- Target appears
- User must click target as many times as possible in 10 seconds
- System counts valid clicks (click on target = valid, miss = invalid)

**Scoring:**
- Valid clicks / Time = clicks per second (CPS)
- Invalid clicks / Total clicks = accuracy %
- Tremor-induced double-clicks detected and filtered

**SARA's Learning:**
- Measures high-frequency tremor (clicks between intentional clicks)
- Learns how fast user can click without tremor interference
- Detects if double-clicks appear (tremor causing rapid re-trigger)

**Difficulty Levels:**
1. Rookie: large target (80px), stationary target, 10 seconds
2. Veteran: medium target (50px), slowly moving target, 10 seconds
3. Pro: small target (30px), moving target, 10 seconds
4. All-Star: tiny target (15px), fast-moving target, 10 seconds

---

### 3.8 Endurance Challenge (Sustained Task)

**Purpose:** Detect fatigue onset and how tremor/accuracy degrades over time.

**Mechanic:**
- Repeats one of the easier drills (e.g., Precision Tap) for extended duration (5-10 minutes)
- Performance monitored across time
- If accuracy drops below threshold, drill can auto-stop with encouragement

**Scoring:**
- Accuracy over time (plot showing degradation)
- Time until 20% accuracy drop = fatigue onset time
- Total hits in endurance session

**SARA's Learning:**
- Establishes how long user can sustain high accuracy
- Learns fatigue progression curve
- Detects if tremor gets worse as fatigue increases

**Difficulty Levels:**
1. Rookie: 3-minute hold-steady drill, no timeout, large targets
2. Veteran: 5-minute precision-tap drill, standard targets
3. Pro: 7-minute precision-tap drill, small targets
4. All-Star: 10-minute multi-tap drill, tiny targets

---

## 4. Progression System

### 4.1 Difficulty Ramping (Per Session)

User **starts at difficulty 1** for each drill type (first time). On each successful completion:

```
Completion Quality = (Accuracy * Speed * Consistency) / 3

If Completion Quality > 75%:
  → Increase difficulty to next level
  
Repeat until user reaches ceiling (Completion Quality < 50%)
```

**Example Progression:**
1. User plays Precision Tap - Rookie (8/10 = 80% accuracy)
   - Completion Quality = (0.80 * 0.95 * 0.92) = 0.70 (below 75%, try again)
   - Or if they nail it:
   - Completion Quality = (0.95 * 0.98 * 0.96) = 0.90 (above 75%, advance!)

2. User advances to Precision Tap - Veteran
   - If they score 60% accuracy
   - Completion Quality = (0.60 * 0.85 * 0.80) = 0.41 (below 50%, CEILING REACHED)
   - System notes: "Your ceiling for Precision Tap is Veteran difficulty"

### 4.2 Session Arc

Recommended session flow (30-45 min total):

```
1. Warm-Up (5 min)
   - Hold Steady (1 min) → establish baseline for today
   - Rhythm (2 min) → easy, fun, gets user in headspace
   - Light Sweep (2 min) → loosens up coordination

2. Training Block (20 min)
   - 2-3 drill types, each ramped to personal ceiling
   - 3-4 min per drill
   - Build from easier to harder

3. Cool-Down (5 min)
   - Endurance or light drill
   - Not ramping difficulty
   - Just for fun, gauge overall fatigue

4. Post-Drill Analysis (5 min)
   - Coach AI summarizes session
   - Shows progress vs. yesterday/last week
   - Highlights what SARA learned
```

---

## 5. Progression Tracking & Leaderboards

### 5.1 Personal Bests

Track and celebrate user's **personal bests** in each drill:

```json
{
  "personal_bests": {
    "precision_tap": {
      "highest_difficulty": "Pro",
      "highest_accuracy": 0.94,
      "date": "2026-05-08"
    },
    "rhythm": {
      "highest_difficulty": "All-Star",
      "highest_accuracy": 0.88,
      "date": "2026-05-05"
    }
  }
}
```

### 5.2 Progression Over Time

Show **trend graphs** (daily, weekly, monthly):

- Accuracy trend (is user improving?)
- Difficulty ceiling trend (user reaching higher levels?)
- Session frequency (consistency)
- Estimated filter sensitivity auto-adjusted (is SARA getting better?)

### 5.3 Optional: Community Leaderboards

**Only if user opts-in:**
- Anonymous leaderboards per drill/difficulty
- No real names, no identifying data
- Encourages friendly competition
- **Privacy-first:** user can disable any time

---

## 6. Reward & Motivation System

### 6.1 Coaching Persona

Coach provides:
- **Encouragement** — "Great hold! 85% steady. That's improving!"
- **Insights** — "I noticed your tremor got stronger around 3 minutes. You might want breaks then."
- **Celebration** — Crowd cheers on personal bests
- **Honesty** — "Today wasn't your best session, but that's ok. Rest up and try again tomorrow!"

### 6.2 Achievement Badges (Optional)

If user completes milestones:
- "Steady Eddie" — Hold Steady for 15 seconds at 90%+ accuracy
- "Lightning Reflexes" — Reaction Time at All-Star difficulty
- "Endurance King" — Complete 10-minute Endurance challenge
- "Tremor Buster" — Improve tremor filtering accuracy by 20% vs. baseline
- "Week Warrior" — 7 consecutive days of training

### 6.3 No Punishment

- No "lives" system that can fail
- No time limits that cause stress
- Missing a target = try again, not "game over"
- User can pause/stop anytime, no penalty
- If fatigue detected, *offer* break instead of forcing

---

## 7. SARA's Learning Integration

### 7.1 Real-Time Filter Adjustment

**During drill:**
```
Drill runs
    ↓
[SARA analyzes input in real-time]
    ↓
If tremor spike detected:
  → Slightly increase filter sensitivity
  → Continue drill (user doesn't notice)
    ↓
User completes drill
    ↓
[SARA evaluates: did increasing filter help?]
```

### 7.2 Post-Drill Recommendation

**After drill completes:**
```
Analysis complete
    ↓
SARA shows summary:
  - Tremor detected: 4.2 Hz frequency, 2.3px amplitude
  - Filter sensitivity was level 4
  - With filter: 78% accuracy
  - Without filter (estimated): 68% accuracy
  - Recommended for next session: level 4 is optimal
    ↓
MamaLedger updated with learned sensitivity curve
```

### 7.3 Cross-Session Learning

**Between sessions:**
```
User returns next day
    ↓
SARA loads yesterday's learned profile
    ↓
If condition changed (worsening/improving detected):
  → Show explanation: "Your tremor was slightly stronger yesterday.
     I've adjusted my filter from level 4 to level 5. Let me know
     if that feels better."
    ↓
If condition stable:
  → "Same settings as yesterday. Ready to go?"
```

---

## 8. Medical & OT Integration (Future)

### 8.1 Therapist Notes Input

Occupational therapists can input notes:

```
[Optional QR Code or secure link]

OT enters:
- Patient name (encrypted)
- Recommended break intervals
- Medication timing
- Special sensitivity (pain points, triggers)
- Goals for this week

SARA incorporates into drill recommendations
```

### 8.2 Progress Export for Medical Records

User can export session data (with consent):

```json
{
  "export_date": "2026-05-10",
  "privacy_level": "HIPAA_compliant",
  "sessions_exported": 30,
  "summary": {
    "tremor_frequency_hz": 4.3,
    "tremor_amplitude_px": 2.4,
    "avg_accuracy": 0.82,
    "fatigue_onset_time_sec": 95,
    "progression_status": "stable"
  },
  "note": "User has completed 30 TechBallCamp drills. Tremor profile is stable over 4 weeks. Recommended filter sensitivity is level 5."
}
```

---

## 9. Implementation Roadmap

### Phase 1: Core Mechanics ✅
- [ ] Hold Steady drill (simplest, baseline)
- [ ] Precision Tap drill
- [ ] Basic scoring system
- [ ] Difficulty ramping logic

### Phase 2: Full Drill Suite ✅
- [ ] Remaining 6 drills implemented
- [ ] Coach persona voice (optional AI or recorded audio)
- [ ] Visual theme (football stadium aesthetic)

### Phase 3: Learning Integration ✅
- [ ] Real-time filter adjustment during drills
- [ ] Post-drill biometric analysis
- [ ] Cross-session learning (load yesterday's profile)

### Phase 4: Progression & Rewards ✅
- [ ] Personal best tracking
- [ ] Trend graphs (daily, weekly, monthly)
- [ ] Achievement badges

### Phase 5: Medical Integration (Future)
- [ ] OT notes input
- [ ] HIPAA-compliant export
- [ ] Therapist dashboard (optional)

### Phase 6: Multiplayer & Community (Future)
- [ ] Leaderboards
- [ ] Achievements shared anonymously
- [ ] Multiplayer co-op drills

---

## 10. Testing & Validation

**Before shipping:**

- [ ] Test with 5+ users with Parkinson's; verify drill difficulty progression works
- [ ] Test with 3+ users with Essential Tremor; verify filter effectiveness improves
- [ ] Verify audio + visual accessibility (screen reader compatible)
- [ ] Verify drill latency: <16ms per frame (60fps target)
- [ ] Verify SARA learns within 10 drills (confidence > 0.8)
- [ ] User satisfaction: >4/5 stars (fun, motivating, not frustrating)
- [ ] HIPAA compliance: biometric data never exposed

**Success Criteria:**
- User accuracy improves by >10% from first to 10th drill
- SARA's learned filter effectiveness > 0.3 (more helps than hurts)
- User reports increased confidence in daily tasks
- Therapists report patient engagement and measurable motor improvement

---

## 11. References

- [BIOMETRIC_PROTOCOL_SPEC.md](BIOMETRIC_PROTOCOL_SPEC.md) — tremor detection, learned profiles, filter algorithm
- [SPEC_SHEET_GEN0_CSHARP.md](SPEC_SHEET_GEN0_CSHARP.md) — main C# frontend spec
- [DisabilityMapper](../DisabilityMapper) — baseline WPF app providing HID input capture

---

**Status:** Game design specification ready for implementation  
**Next Step:** Begin Phase 1 (Hold Steady & Precision Tap drills) with C# WPF UI
