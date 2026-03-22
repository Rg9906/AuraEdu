# AURA-EDU

### *Rewiring Perception. Rehabilitation, Reinvented.*

---

## 🧠 Overview

**AURA-EDU** is an AI-powered neuroadaptive wearable system designed to assist individuals affected by **hemispatial neglect**, a neurological condition where a person fails to perceive stimuli on one side of their environment.

Unlike traditional assistive technologies that provide constant external guidance, AURA-EDU introduces a **closed-loop adaptive rehabilitation system** that:

* Observes environmental stimuli
* Evaluates the user’s natural response
* Intervenes only when necessary
* Continuously learns and adapts

The system transforms passive assistance into **active cognitive rehabilitation**, enabling long-term improvement in spatial awareness.

---

## 🚨 Problem Statement

Hemispatial neglect is a common consequence of stroke and traumatic brain injury (TBI), where patients unconsciously ignore one side of their visual field—typically the left.

### Key Challenges:

* Missed environmental stimuli (objects, people, obstacles)
* Frequent collisions and unsafe navigation
* Reduced classroom and social participation
* Dependence on therapists for rehabilitation
* Lack of continuous, real-world training systems

### Limitations of Existing Solutions:

* Primarily clinical and session-based
* Expensive and inaccessible
* Not integrated into daily environments
* No real-time adaptive feedback
* Minimal personalization

---

## 🎯 Objective

To design a **real-time, AI-driven, wearable rehabilitation system** that:

* Detects environmental stimuli across all directions
* Evaluates whether the user responds independently
* Provides directional haptic feedback only when necessary
* Tracks behavioral response patterns over time
* Quantifies cognitive recovery using data-driven metrics

---

## 🧩 Core Concept

AURA-EDU operates on a **closed-loop neuroadaptive framework**:

```text
Sense → Analyze → Evaluate → Respond → Learn → Adapt
```

Instead of immediately assisting the user, the system introduces a **deliberate observation window**, allowing the brain to attempt independent response.

This promotes:

* Neuroplasticity
* Behavioral learning
* Gradual reduction in external dependency

---

## ⚙️ System Architecture

### 1. Sensing Layer

The system captures environmental and spatial data using:

* **4 Ultrasonic Sensors**

  * Positioned: Left, Right, Front, Back
  * Measure proximity to nearby objects

* **1 Forward-Facing Camera**

  * Detects object type (e.g., person, desk, obstacle)
  * Focused on high-risk frontal collisions

---

### 2. Perception Layer

* Object detection using **YOLO (You Only Look Once)**
* Frame divided into spatial zones:

  * Left / Right / Center
* Each detected object is classified directionally

---

### 3. Decision Engine (Core Intelligence)

This is the heart of AURA-EDU.

For every detected stimulus:

#### Step 1 — Detection Trigger

* Object detected OR distance below threshold

#### Step 2 — Observation Window

* System delays intervention
* Monitors user behavior

#### Step 3 — Reaction Evaluation

* If distance increases → **SUCCESS**
* If no response → proceed to intervention

#### Step 4 — Intervention

* Trigger directional vibration
* Mark event as **FAILURE**

---

### 4. Feedback Layer

* **8 Vibration Motors (Haptic Belt)**
* Provide directional cues:

  * Left → Left motors activate
  * Right → Right motors activate
  * Front → Front motors activate

The feedback is:

* Non-intrusive
* Context-aware
* Adaptive over time

---

### 5. Data Layer

Every interaction is recorded as a structured event:

```json
{
  "timestamp": "...",
  "object": "desk",
  "direction": "left",
  "initial_distance": 80,
  "final_distance": 120,
  "reaction_time": 2.3,
  "result": "success"
}
```

---

### 6. Analytics & Metrics Engine

The system computes:

#### 🔹 Success vs Failure Rate

* Percentage of independent responses

#### 🔹 Reaction Time

* Average time taken to respond

#### 🔹 Directional Awareness (CRITICAL)

* Separate tracking for:

  * Left side
  * Right side

#### 🔹 Progress Over Time

* Day-wise performance trends

#### 🔹 SENS-ED Score (Custom Metric)

A composite score based on:

* Success rate
* Reaction speed
* Consistency

---

## 📊 Visualization & Output

The frontend (app/dashboard) displays:

* Live system status
* Detected objects and directions
* Alerts and feedback events
* Graphs:

  * Left vs Right awareness trends
  * Success vs Failure over time
* Performance score and insights

---

## 🔁 Adaptive Learning Loop

AURA-EDU continuously evolves based on user behavior:

* Faster reactions → reduced intervention
* Slower reactions → increased guidance
* Personalized feedback intensity

This creates a **self-improving rehabilitation system**.

---

## 🧪 Current Implementation (Prototype Phase)

The current system operates **without physical hardware**, using simulation:

* Ultrasonic sensor data → simulated dynamically
* Camera input → processed via YOLO on laptop
* Vibration feedback → simulated via software outputs
* Data storage → JSON / backend API

The architecture is designed for seamless transition to hardware integration.

---

## 🔌 Future Hardware Integration

Planned upgrades:

* ESP32 / Raspberry Pi for real-time edge processing
* Real ultrasonic sensors for accurate distance measurement
* Haptic belt with PWM-controlled motors
* Battery monitoring system
* BLE / Wi-Fi communication with dashboard

---

## 🌐 Future Ecosystem Vision

AURA-EDU aims to expand beyond a device into a **neuroadaptive ecosystem**:

* Community platform for users (peer support, shared progress)
* Therapist dashboards for monitoring recovery
* Integration with health platforms (e.g., Apple Health)
* Gamified rehabilitation modules
* Remote monitoring and tele-rehabilitation

---

## 🚀 Why AURA-EDU Matters

AURA-EDU is not just an assistive device.

It is a shift from:

> Passive assistance → Active rehabilitation

From:

> Clinical sessions → Continuous real-world therapy

From:

> Generic solutions → Personalized adaptive systems

---

## 🧠 Final Insight

At its core, AURA-EDU is designed to answer a fundamental question:

> *“What if technology didn’t just help you navigate the world—
> but helped your brain relearn how to perceive it?”*

---

## 🛠️ Tech Stack (Prototype)

* Python
* OpenCV
* YOLO (Ultralytics)
* FastAPI (backend API)
* JSON / Database (data storage)
* FlutterFlow (frontend UI)

---

## 📌 Status

* Concept: ✅ Defined
* System Design: ✅ Complete
* Backend Simulation: 🔄 In Progress
* Hardware Integration: ⏳ Planned

---

## 👥 Team

AURA-EDU is developed as part of an ideathon project focused on **AI-driven assistive technology for inclusive education and rehabilitation**.

---
