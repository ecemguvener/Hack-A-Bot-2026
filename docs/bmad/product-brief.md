# Product Brief: NeuroCalm Adaptive Tremor Support

- **Date:** 2026-03-21
- **Author:** Hack-A-Bot Team
- **Status:** Draft
- **Version:** 0.1

---

## 1. Executive Summary

NeuroCalm is an assistive embedded prototype for people with Parkinsonian hand tremor. The system measures hand movement in real time and adapts vibration feedback per user profile to improve short-session hand stability during task performance. The design uses two Raspberry Pi Pico 2 boards and nRF24 wireless coordination to satisfy the Project 6 Creative brief and provide a measurable, repeatable live demo.

**Key Points:**
- Problem: Hand tremor reduces control in daily tasks and confidence.
- Solution: Personalized adaptive vibration support using IMU-driven feedback.
- Target Users: People with Parkinsonian hand tremor (primary), caregivers/clinicians (secondary).
- Timeline: 20-hour hackathon build, live judged demo.

---

## 2. Problem Statement

### The Problem

Users with Parkinsonian tremor experience involuntary hand oscillations that make precise and steady actions difficult. Existing low-cost workaround approaches (for example weighted gloves) are static and not personalized to each user’s tremor pattern.

### Who Experiences This Problem

People with Parkinsonian tremor, especially during tasks requiring steady hand posture or controlled movement.

**Primary Users:**
- People with Parkinsonian hand tremor
- Adults needing better hand stability for daily tasks
- Users seeking non-invasive assistive support

**Secondary Users:**
- Caregivers
- Rehabilitation or clinical staff

### Current Situation

**How Users Currently Handle This:**
Weighted glove with components (static configuration).

**Pain Points:**
- Static support does not adapt to changing tremor patterns.
- Limited feedback on whether support is helping.
- Setup is trial-and-error and user-specific tuning is hard.

### Impact & Urgency

**Impact if Unsolved:**
Lower independence and task confidence for affected users.

**Why Now:**
Strong judging fit for assistive tech with measurable outcomes and clear two-node wireless architecture.

**Frequency:**
Symptoms can appear repeatedly during normal daily hand tasks.

---

## 3. Target Users

### User Personas

#### Persona 1: Independent Daily User
- **Role:** Person living with Parkinsonian tremor
- **Goals:** Improve steadiness for short daily tasks
- **Pain Points:** Inconsistent control, frustration from visible shake
- **Technical Proficiency:** Low to medium
- **Usage Pattern:** Short repeated sessions during the day

#### Persona 2: Caregiver-Supported User
- **Role:** Patient supported by caregiver
- **Goals:** Safer and more reliable assisted task performance
- **Pain Points:** Hard to tune one fixed support setting
- **Technical Proficiency:** Low
- **Usage Pattern:** Supervised sessions and profile switching

### User Needs

**Must Have:**
- Real-time tremor sensing and feedback loop
- Personalized profile behavior per user
- Stable operation with safe fallback mode

**Should Have:**
- Clear session metrics for baseline vs assisted behavior
- Simple mode/profile switching

**Nice to Have:**
- Longitudinal progress tracking across multiple sessions
- Clinician-facing tuning presets

---

## 4. Proposed Solution

### Solution Overview

NeuroCalm uses a wearable/handheld sensing node (Pico A) to estimate tremor characteristics and apply adaptive vibration patterns, while a companion node (Pico B) handles profile control, UI, and telemetry over nRF24. The adaptation logic evaluates movement features and adjusts support per user profile in-session.

### Key Capabilities

1. **Real-Time Motion Sensing**
   - Description: BMI160 IMU samples hand motion continuously.
   - User Value: Captures each user’s movement pattern instead of fixed assumptions.

2. **Adaptive Feedback Selection**
   - Description: Controller chooses among candidate vibration settings based on observed response.
   - User Value: Personalized assistance rather than one-size-fits-all support.

3. **Two-Node Wireless Control**
   - Description: Companion Pico updates mode/profile and receives telemetry.
   - User Value: Easy adjustment and transparent operation during demo/use.

4. **Safety and Reliability Behaviors**
   - Description: RF timeout and invalid sensor data trigger safe fallback behavior.
   - User Value: Predictable and safe operation.

5. **Live Measurable Metrics**
   - Description: Session outputs include amplitude/smoothness/stability scores.
   - User Value: Immediate evidence of assistance effect.

### What Makes This Different

Unlike static weighted support, this system continuously adapts feedback to user-specific movement behavior during operation.

**Unique Value Proposition:**
Personalized, low-cost, edge-based tremor support using embedded wireless coordination.

### Minimum Viable Solution

**Core Features for MVP:**
- IMU-based tremor feature extraction at fixed sample rate
- Adaptive vibration profile switching
- Companion node with profile/mode control and telemetry display

**Deferred to Later:**
- Long-term multi-session progress modeling
- Clinical validation and medical-grade safety process

---

## 5. Success Metrics

### Primary Metrics

**Tremor Amplitude Change (Session)**
- Baseline: Measured in an unassisted calibration window
- Target: Demonstrate measurable improvement in assisted mode
- Timeline: During live demo session
- Measurement: Compare baseline vs assisted amplitude features

**Movement Smoothness Score**
- Baseline: Derived from raw motion variability
- Target: Improved smoothness under adaptive assistance
- Timeline: During live demo session
- Measurement: Rolling score from filtered IMU signal

**Task Stability Score**
- Baseline: Unassisted hold/trace stability score
- Target: Better score with adaptive support enabled
- Timeline: During live demo session
- Measurement: Time in stable zone / trajectory deviation

### Secondary Metrics

- RF packet reliability during demo
- Adaptation convergence time per profile
- Number of safe fallback events

### Success Criteria

**Must Achieve:**
- Clear before/after session comparison with at least one improved primary metric
- Stable two-Pico wireless coordination throughout demo

**Should Achieve:**
- Improvement across at least two primary metrics in the same run
- Visible personalization effect when switching profiles/users

---

## 6. Market & Competition

### Market Context

**Market Size:**
Large and growing assistive technology demand driven by aging populations and chronic movement disorders.

**Market Trends:**
- Shift from passive aids to adaptive assistive devices
- Increased demand for low-cost home-use support tools
- Growing interest in edge intelligence for privacy and low latency

**Target Market Segment:**
Entry-level assistive devices for tremor support in home and caregiver settings.

### Competitive Landscape

#### Competitor 1: Weighted gloves and passive braces
- **Strengths:** Simple, low cost, easy access
- **Weaknesses:** No personalization or adaptation
- **Pricing:** Low
- **Market Position:** Basic workaround

#### Competitor 2: Premium therapeutic devices
- **Strengths:** Better engineering and support ecosystems
- **Weaknesses:** Higher cost and limited accessibility
- **Pricing:** Medium to high
- **Market Position:** Specialized solutions

#### Competitor 3: Mobile app guidance without hardware feedback
- **Strengths:** Easy software distribution
- **Weaknesses:** No direct physical stabilization feedback
- **Pricing:** Low to medium
- **Market Position:** Indirect support only

### Competitive Advantages

- Personalized adaptive behavior at low hardware cost
- Fully local embedded control loop (low latency)
- Clear measurable outcome in short sessions

---

## 7. Business Model

- **Primary model:** Device kit sale with simple companion interface
- **Secondary model:** Caregiver/clinic profile presets and service support
- **Early go-to-market:** Pilot programs with rehab/assistive communities

---

## 8. Technical Considerations

- Two-node architecture is mandatory and built-in:
  - Pico A: sensing + adaptation + actuator control
  - Pico B: UI/profile control + telemetry + supervision
- RF transport: nRF24 bidirectional packets with heartbeat
- Sample rate target: 100 Hz IMU loop
- Reliability focus: RF timeout fallback and actuator saturation limits

---

## 9. Risks & Mitigation

- **Risk:** Integration delays across sensing, control, and RF
  - **Mitigation:** Bring up RF link and telemetry first, then add adaptation
- **Risk:** Improvement not obvious in live judging
  - **Mitigation:** Predefined baseline vs assisted protocol with on-screen metrics
- **Risk:** Wireless dropouts
  - **Mitigation:** Heartbeat timeout + safe fallback behavior + short-range demo setup

---

## 10. Resource Estimates

- **Team:** 4 people
- **Available Build Time:** 20 hours
- **Hardware:** 2x Pico 2, 2x nRF24, BMI160, OLED, joystick, power modules, optional vibration actuator/servo proxy
- **Work split:**
  - Embedded sensing/control
  - RF/UI node
  - Hardware integration/power
  - Test protocol + demo + documentation

---

## 11. Dependencies

- Stable BMI160 sampling and calibration
- Reliable two-way nRF24 communication
- Defined trial protocol for baseline vs assisted comparison
- Repeatable demo fixture and timing

---

## 12. Next Steps

1. Finalize hardware fixture and actuator choice for haptic output.
2. Implement RF heartbeat and telemetry first.
3. Implement baseline capture and assisted mode comparison.
4. Define fixed demo script with metric capture table.
5. Proceed to `bmad:brainstorm` or directly to `bmad:prd`.
