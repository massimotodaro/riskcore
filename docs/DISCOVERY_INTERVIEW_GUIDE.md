# RISKCORE Discovery Interview Guide

> Questions to ask when meeting with hedge fund prospects
> **Primary Audience:** CROs (Chief Risk Officers)
> **Secondary:** CTOs, PMs, COOs
> **Last Updated:** 2026-01-12

---

## Pre-Meeting Preparation

Before the meeting, research:
- [ ] Firm's AUM and structure (multi-PM? single strategy?)
- [ ] Number of PMs and strategies
- [ ] Recent news (launches, hires, regulatory)
- [ ] LinkedIn profiles of attendees
- [ ] Any public information about their technology stack

---

## Part 1: Warm-Up (5 minutes)

*Build rapport before diving into pain points*

### About Their Role

1. **"Can you tell me about your role and what a typical day looks like?"**
   - Listen for: manual processes, fire drills, recurring headaches

2. **"How is your team structured? Who do you work most closely with?"**
   - Listen for: reporting lines, who owns risk decisions

3. **"How many PMs do you currently have? How many strategies?"**
   - Note: This tells you complexity and potential deal size

---

## Part 2: Current State Assessment (10 minutes)

*Understand their world before proposing solutions*

### Systems & Infrastructure

4. **"Walk me through how a trade flows from execution to your risk report."**
   - Listen for: manual steps, multiple systems, delays

5. **"What systems do your PMs use for booking trades?"**
   - Common answers: Bloomberg AIM/EMSX, Enfusion, Eze Eclipse, internal
   - Follow-up: "Is that consistent across all PMs or does each PM choose?"

6. **"How do you get position data from PMs today?"**
   - Listen for: CSV exports, manual emails, overnight batch, real-time feeds

7. **"What's your primary risk system right now?"**
   - Common answers: Excel, RiskMetrics, Aladdin, internal, nothing
   - Follow-up: "What do you like about it? What's frustrating?"

### Risk Aggregation

8. **"How do you aggregate risk across all your PMs?"**
   - This is THE question - listen carefully
   - Common answers: "We don't really", "Excel", "One person owns it"

9. **"How often do you have firm-wide risk visibility? Real-time? Daily? Weekly?"**
   - Listen for: gaps in visibility, stale data concerns

10. **"Who is responsible for pulling this together? How long does it take?"**
    - Quantify the pain: "So someone spends X hours per day on this?"

---

## Part 3: Pain Points Deep Dive (15 minutes)

*The CRO-focused section - this is RISKCORE's value proposition*

### Cross-PM Visibility

11. **"What keeps you up at night when it comes to cross-PM risk?"**
    - Open-ended - let them talk
    - Common themes: concentration, correlation, hidden overlap

12. **"Have you ever been surprised by a position that multiple PMs held?"**
    - Story-based - they'll share real examples
    - Follow-up: "How did you discover it? What happened?"

13. **"How do you know if two PMs are effectively running the same trade?"**
    - This is correlation/overlap detection
    - Follow-up: "What would you do if you found that?"

14. **"When markets move sharply, how quickly can you see firm-wide exposure?"**
    - Speed matters in crisis
    - Follow-up: "March 2020 - how did that go for your team?"

### Netting & Concentration

15. **"Do you net positions across PMs for risk purposes?"**
    - If yes: "How is that calculated?"
    - If no: "Would that be useful? Why or why not?"

16. **"How do you monitor single-name concentration across the firm?"**
    - Common answer: "We should do this better"

17. **"What's your process when a limit is breached?"**
    - Listen for: workflow, escalation, PM communication

### Correlation Concerns

18. **"How do you think about correlation risk across PMs?"**
    - Advanced question - if they light up, they're sophisticated
    - Follow-up: "Realized correlation? Implied from holdings?"

19. **"In a drawdown, are you confident you know how PMs will move together?"**
    - Fear-based - touches on crisis scenarios

20. **"Do you differentiate between PMs who offset each other vs. amplify?"**
    - This is diversification benefit calculation

---

## Part 4: Technical Questions (10 minutes)

*CTO-focused - may be in same meeting or separate*

### Integration & Data

21. **"What's your preferred way to receive data from third-party systems?"**
    - Options: API (REST), FIX, File (SFTP), Real-time stream
    - Follow-up: "Do you have a standard onboarding process?"

22. **"Where does your position data live? What's the source of truth?"**
    - Listen for: Prime broker, OMS, internal database

23. **"How do you feel about cloud vs. on-premises for sensitive data?"**
    - CRITICAL for RISKCORE - we're on-premises only
    - If they say "cloud is fine" - explain our approach anyway

24. **"What's your data residency requirement? Any regulatory constraints?"**
    - EU firms may have GDPR concerns
    - Some have specific geography requirements

### Security & Compliance

25. **"What security certifications do you require from vendors?"**
    - SOC 2, ISO 27001, penetration testing
    - Follow-up: "Is that a blocker or a nice-to-have?"

26. **"How do you handle user access control? SSO? 2FA?"**
    - Enterprise requirement for larger firms

27. **"Do you have a vendor security questionnaire you'd need us to complete?"**
    - Gets practical about procurement process

### Export & Automation

28. **"What export options does your current OMS have? CSV? Excel? SFTP?"**
    - Key insight: Every system can export files
    - Follow-up: "How often do you export? Daily? Real-time?"

29. **"Do you have automated report scheduling set up in your OMS?"**
    - Bloomberg AIM has report scheduler
    - Enfusion has scheduled exports
    - If yes: "Where do those files go? Network share? SFTP?"

30. **"Would a watched folder approach work for your infrastructure?"**
    - Explain: "We monitor a folder, auto-import new files"
    - Follow-up: "Do you have a shared drive or SFTP server we could use?"

31. **"What's your appetite for API integration vs. file-based integration?"**
    - Many firms prefer file-based (simpler, no vendor lock-in)
    - API integration requires more IT involvement

---

## Part 5: PM Workflow Questions (5 minutes)

*If a PM is in the room, or ask CRO about PM experience*

32. **"How much time do PMs spend on reporting to central risk?"**
    - Quantify burden: "X hours per week"

33. **"What frustrates PMs most about risk reporting requirements?"**
    - Common: "It's not my job", "Takes time from trading"

34. **"Would PMs prefer self-service risk views or do they want risk to handle it?"**
    - Determines feature priority (PM dashboard vs. CRO-only)

35. **"How do PMs react when you ask them about their positions?"**
    - Cultural question - are PMs collaborative or secretive?

---

## Part 6: Business & Decision Process (10 minutes)

*Qualify the opportunity*

### Budget & Timeline

36. **"Is this a budgeted initiative or exploratory?"**
    - Direct question - saves time
    - Follow-up: "What would need to happen to get budget?"

37. **"What's your timeline for evaluating solutions?"**
    - Listen for: urgent vs. "maybe next year"

38. **"Who else needs to be involved in this decision?"**
    - Map the buying committee: CRO, CTO, COO, CEO?

### Competition & Alternatives

39. **"What else have you looked at? What did you like or not like?"**
    - Competitive intel
    - Common: "We looked at [vendor] but it was too expensive/complex"

40. **"Have you considered building this internally?"**
    - Common for large funds
    - Counter: "What would that cost in dev time? Maintenance?"

41. **"What would make you choose one solution over another?"**
    - Understand their criteria: price, features, support, speed

### Success Criteria

42. **"If this works, what does success look like in 6 months?"**
    - Concrete outcomes: "I can see firm risk in real-time"

43. **"What's the biggest risk in adopting something new?"**
    - Understand objections: integration pain, PM pushback, cost

44. **"What would make this a no-brainer decision?"**
    - Understand their trigger: "If it could do X..."

---

## Part 7: Closing & Next Steps (5 minutes)

### Wrap-Up Questions

45. **"What questions do you have for us?"**
    - Listen and address concerns

46. **"Is there anyone else at your firm who should see this?"**
    - Expand access: other CROs, CTOs, specific PMs

47. **"Would it be helpful to see a demo with sample data?"**
    - Soft close to next meeting

### Proposed Next Steps

- [ ] Schedule demo with broader team
- [ ] Send technical documentation (integration guide)
- [ ] Provide reference customers (when available)
- [ ] Complete security questionnaire
- [ ] Define pilot program scope

---

## Question Categories Quick Reference

| # | Category | Best Asked To | Priority |
|---|----------|---------------|----------|
| 1-3 | Warm-up | Anyone | Required |
| 4-10 | Current State | CRO, CTO | Required |
| 11-20 | Pain Points | CRO | **Critical** |
| 21-27 | Technical (Security) | CTO | Important |
| 28-31 | Export & Automation | CTO | **Important** |
| 32-35 | PM Workflow | PM, CRO | Nice-to-have |
| 36-44 | Business | CRO, COO | Required |
| 45-47 | Closing | Anyone | Required |

---

## Red Flags to Watch For

| Signal | What It Means |
|--------|---------------|
| "We're happy with our current setup" | Not a fit right now - follow up in 6 months |
| "We'd need to build this ourselves" | Long sales cycle, but validates need |
| "Our PMs would never share data" | Cultural barrier - harder sell |
| "We're in the middle of a system migration" | Bad timing - revisit after |
| "I'm not the right person" | Ask for warm intro to right person |

---

## Green Flags to Watch For

| Signal | What It Means |
|--------|---------------|
| "We use spreadsheets for this" | Perfect prospect |
| "I was just talking about this problem" | Active pain |
| "Can you integrate with X?" | Technical engagement |
| "How quickly could we get started?" | Buying signal |
| "Who else is using this?" | Social proof request - closing |

---

## Post-Meeting Actions

- [ ] Send thank-you email within 24 hours
- [ ] Summarize key pain points in CRM
- [ ] Identify 3 specific things RISKCORE solves for them
- [ ] Schedule follow-up within 1 week
- [ ] Loop in technical team if integration questions arose
- [ ] Update pipeline status

---

## Stuart/Tudor Specific Notes

**Context:** Stuart Riley - Tudor Group (legendary multi-manager fund)

**Phase 1 (Done):** Asked simple OMS question via LinkedIn

**Phase 2 (When RISKCORE live):**
- Ask Stuart to arrange 30-min call with CRO + CTO
- Focus questions: #8-20 (pain points), #21-24 (technical)
- Key ask: "What would make Tudor consider a tool like this?"

**Relationship note:** Stuart is a friend - keep it collaborative, not salesy. Focus on "help us build the right thing" vs. "buy our product."

---

*This guide should be customized based on firm size, strategy type, and meeting context.*
