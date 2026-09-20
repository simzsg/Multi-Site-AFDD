# AltoTech Global — Senior Full Stack Engineer Assessment
# Implementation Blueprint / AI Coding Agent Plan

> Purpose: ใช้ไฟล์นี้เป็น Blueprint หลักสำหรับวางแผนและสั่ง AI Coding Agent ให้สร้าง Assessment ให้ครบตามโจทย์
>
> Source: `2026 Sep - Senior Full-stack Software Engineer - Multi-Site AFDD with BrickSchema.pdf`
>
> Scope นี้ยึดตาม Assessment ที่ให้มาเป็นหลัก และไม่เพิ่ม requirement ที่เอกสารไม่ได้บังคับ

---

# 1. เป้าหมายของ Assessment

ต้องสร้างระบบ Building Operations + Automatic Fault Detection and Diagnostics (AFDD) ที่ช่วย Property Engineer เปลี่ยน operational knowledge ให้เป็น monitoring rule ที่ reusable และตรวจสอบย้อนหลังได้

ระบบต้องตอบให้ได้อย่างน้อย:

1. Equipment ตัวไหนต้องให้ความสนใจ
2. เกิดปัญหาเพราะอะไร
3. Space/Room ไหนอาจได้รับผลกระทบ
4. Rule สามารถตรวจสอบ ปรับ และ version ได้อย่างไร

## Hero Journey ที่ต้อง Demo

```text
Engineer เขียน Natural Language Request
        ↓
AI ตีความเป็น Rule Draft
        ↓
Ontology Discovery
        ↓
Rule Validation
        ↓
Target Preview
        ↓
Human Review / Confirmation
        ↓
Activate Rule
        ↓
Telemetry Simulator ส่งข้อมูล
        ↓
Ingestion Pipeline
        ↓
AFDD Evaluator
        ↓
ตรวจพบ Seeded Fault
        ↓
สร้าง Issue + Evidence
        ↓
Dashboard แสดงเหตุผล
        ↓
แสดง AHU → Zone → Room ที่อาจได้รับผลกระทบ
```

**ห้ามให้ AI Activate Rule เอง**

---

# 2. Required Technology Boundary

| Layer | Requirement |
|---|---|
| Backend | Python + FastAPI หรือ Django |
| Frontend | React + TypeScript |
| Telemetry History | TimescaleDB |
| Relational App Data | PostgreSQL หรือ Supabase-managed PostgreSQL |
| Ontology | เลือก representation/storage เอง |
| Broker | เลือกเอง |
| Infrastructure | Docker Compose |

## สิ่งที่เลือกเองได้

- Broker
- Ontology storage approach
- Database/service boundaries
- API structure
- Rule representation
- UI information architecture
- Persistence/scaling strategy

ทุก choice สำคัญต้องมีเหตุผลและ trade-off ใน documentation

---

# 3. สิ่งที่ไม่ต้องทำ

อย่าเสียเวลาเพิ่ม scope ในส่วนต่อไปนี้:

- Physical gateways
- Production cloud deployment
- Equipment control
- Work orders
- 3D visualization
- Autonomous rule activation

Core ที่ required ต้องเสร็จก่อน bonus

---

# 4. Known Assessment Data

ข้อมูลหลักที่ Assessment ให้มา:

```text
Buildings       3
Floors          12
Zones           24
Occupied Rooms  48
AHUs            24
IAQ Devices     48
Meters          12
```

แต่ละ Building:

```text
4 Floors
1 Lobby
1 Plant Room
8 AHUs
4 Floor Electricity Meters
16 Occupied Rooms
```

แต่ละ Floor:

```text
2 HVAC Zones
```

แต่ละ Zone:

```text
2 Occupied Rooms
```

แต่ละ Occupied Room:

```text
1 IAQ Device
- Temperature
- Humidity
- CO2
```

หนึ่ง AHU:

```text
1 AHU
→ directly serves 1 HVAC Zone
```

---

# 5. BrickSchema / Ontology Model

ต้องใช้ shared semantic meaning และ explicit relationships

## Space

```text
Building
  ↓ contains
Floor
  ↓ contains
Room

HVAC_Zone
  ↓ groups/serves
Rooms
```

## Equipment

```text
AHU
  ↓ installed in
Plant Room

AHU
  ↓ directly serves
HVAC Zone
  ↓ contains
Rooms
```

**สำคัญ:** Installation Room ของ AHU ต้องแยกจาก Served/Affected Rooms

ตัวอย่าง:

```text
Building A
└── Floor 2
    ├── Plant Room
    │   └── AHU-A2-01
    │
    └── Zone A2-01
        ├── Room A2-01-01
        └── Room A2-01-02
```

AHU อยู่ Plant Room แต่ Room ที่อาจได้รับผลกระทบคือ Rooms ใน Zone ที่ AHU ให้บริการ

## Brick classes ที่ระบุในโจทย์

Spaces:

```text
brick:Building
brick:Floor
brick:Room
brick:HVAC_Zone
```

Equipment:

```text
brick:AHU
brick:Electrical_Meter
```

AHU points:

```text
brick:Run_Status
brick:Alarm
brick:Supply_Air_Temperature_Sensor
brick:Return_Air_Temperature_Sensor
brick:Supply_Air_Temperature_Setpoint
```

Other measurements:

```text
brick:Electrical_Power_Sensor
brick:Electrical_Energy_Sensor
brick:Zone_Air_Temperature_Sensor
brick:Humidity_Sensor
brick:CO2_Sensor
```

ใช้ BrickSchema version และ mappings ตาม supporting pack ของ Assessment

---

# 6. Recommended Repository Structure

โครงสร้างแนะนำ:

```text
afdd-platform/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── domain/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── ontology/
│   │   ├── afdd/
│   │   ├── ai/
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
│
├── workers/
│   ├── ingestion/
│   └── afdd/
│
├── simulator/
│   ├── fixtures/
│   └── Dockerfile
│
├── database/
│   ├── migrations/
│   └── seed/
│
├── docs/
│   ├── architecture.md
│   ├── brickschema.md
│   ├── afdd.md
│   ├── ai-rule-authoring.md
│   ├── decisions.md
│   └── demo.md
│
├── tests/
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore
```

ชื่อจริงปรับได้ แต่ต้องรักษา service boundaries และ responsibilities ให้ชัดเจน

---

# 7. Phase 0 — อ่าน Supporting Pack ก่อนเขียน Code

## เป้าหมาย

ทำความเข้าใจ authoritative data ก่อน

## ต้องตรวจ

- Entity IDs
- Relationships
- Brick types
- Point IDs
- Units
- Timestamps
- Quality values
- Telemetry fixtures
- Normal events
- Sustained-fault events
- OFF events
- Missing-data events
- Recovery events
- Duplicate events
- Invalid events
- Rule verification cases
- Target sets
- Exclusions
- Issue windows
- Property-specific override
- Natural-language test cases

## Output

สร้าง:

```text
docs/data-model.md
```

และบันทึก:

- inventory counts
- entity types
- relationship model
- telemetry schema
- test scenarios
- expected outcomes

**ห้าม invent IDs หรือ expected results ถ้ามีข้อมูลใน supporting pack ให้ใช้ข้อมูลนั้นเป็น source of truth**

---

# 8. Phase 1 — Architecture

ก่อน implement ให้สร้าง Architecture Decision Record

## ต้องตัดสินใจ

### Database

แยก:

```text
PostgreSQL
→ application/domain data

TimescaleDB
→ telemetry history
```

TimescaleDB ใช้ PostgreSQL foundation ได้ตามโจทย์

### Ontology

เลือกหนึ่งแนวทางและอธิบาย:

- relational/recursive queries
- PostgreSQL graph extension
- dedicated graph/RDF database เช่น Neo4j หรือ GraphDB

ต้องอธิบาย:

- query behavior
- operational complexity
- migration
- onboarding building ใหม่
- changed ontology
- hybrid-cloud evolution

### Broker

เลือก broker และอธิบาย:

- delivery model
- acknowledgement
- retry
- duplicate behavior
- consumer failure
- observability

## Output

```text
docs/architecture.md
docs/decisions.md
```

---

# 9. Phase 2 — Database & Ontology Registry

## ต้องเก็บ Application Data

ตัวอย่าง logical domains:

```text
properties/buildings
floors
zones
rooms
equipment
telemetry_points
ontology_relationships
rules
rule_versions
rule_overrides
issues
issue_evidence
ai_requests
ai_tool_runs
ai_reviewed_drafts
audit_events
```

ชื่อ table ปรับได้

## Telemetry

TimescaleDB ต้องรองรับ:

```text
point_id
event_id
device_timestamp
value
unit
quality
received_at
```

ควรแยก:

```text
device_timestamp
received_at
```

เพราะ AFDD ต้องใช้ timestamp จาก device ไม่ใช่ platform receipt time

---

# 10. Phase 3 — Telemetry Simulator

## เป้าหมาย

จำลอง device จริง

ต้อง:

- stream AHU readings
- stream meter readings
- stream IAQ readings
- run Building A/B/C พร้อมกันหรือเลือกเฉพาะบาง building
- selectable interval เช่น 15 หรือ 60 seconds
- preserve event ID
- preserve device timestamp

Flow:

```text
Simulator
    ↓
Broker
    ↓
Ingestion Consumer
```

## Fixture Modes

ต้องรองรับข้อมูลที่โจทย์ให้มา:

```text
normal
sustained-fault
OFF
missing-data
recovery
duplicate
invalid
```

## Seed/Run command

ต้องมี command ที่ documented และ reproducible เช่น:

```bash
docker compose up
```

และ command สำหรับ:

```text
seed
reset
replay telemetry
run simulator
```

ชื่อ command จริงเลือกเอง

---

# 11. Phase 4 — Ingestion Pipeline

Flow:

```text
Broker
 ↓
Consumer
 ↓
Validate
 ↓
Resolve Point Identity
 ↓
Idempotency Check
 ↓
Persist History
 ↓
Update Current State
 ↓
ACK
```

## Validation

ตรวจอย่างน้อย:

```text
Identity
Type
Timestamp
Unit
Quality
```

## Duplicate

Event เดิมต้องไม่มี second effect

เช่น:

```text
event_id = ABC123

received ครั้งแรก
→ persist

received ซ้ำ
→ no second effect
```

## Out-of-order

ถ้า:

```text
newer observation
device_timestamp = 10:10

older observation
device_timestamp = 10:05
```

older observation ห้าม overwrite current value

แต่ historical telemetry สามารถเก็บตาม policy ที่ออกแบบไว้

## Invalid

ต้อง reject และแสดงผลให้เห็นในระบบ

## Missing

ห้ามสร้าง fake value เพื่อกลบ gap

ต้องแสดงว่า data missing

---

# 12. Phase 5 — Core APIs

ต้องมี API สำหรับ:

## Discovery

```text
GET buildings
GET floors
GET zones
GET rooms
GET equipment
GET points
```

## Relationships

```text
GET equipment/{id}/relationships
GET equipment/{id}/served-spaces
GET zones/{id}/rooms
```

## Telemetry

```text
GET points/{id}/latest
GET points/{id}/history
```

## Health

```text
GET health
GET ingestion-health
GET evaluator-health
```

## Rules

```text
POST rules
GET rules
GET rules/{id}
POST rules/{id}/validate
POST rules/{id}/preview
POST rules/{id}/activate
POST rules/{id}/disable
POST rules/{id}/adjust
GET rules/{id}/versions
```

## Issues

```text
GET issues
GET issues/{id}
GET issues/{id}/evidence
GET issues/{id}/affected-spaces
```

API paths เป็น design choice แต่ต้องครอบคลุม capability ที่โจทย์ต้องการ

เปิด OpenAPI documentation

---

# 13. Phase 6 — Rule Schema

Rule ต้อง configurable

**ห้าม hard-code required rule เป็น code path เดียว**

แยก:

```text
Target Scope
+
Fault Logic
```

## Target Scope

ต้องรองรับ concept อย่างน้อย:

```text
property type
building
served floor
served zone
served room
equipment type
exclusions
```

## Fault Logic

ต้องรองรับ concept อย่างน้อย:

```text
operating state
comparison
threshold
unit
duration
severity
recovery
```

ตัวอย่าง logical configuration:

```json
{
  "target": {
    "property_type": "office",
    "served_space": {
      "type": "tenant_area"
    },
    "equipment_type": "AHU"
  },
  "logic": {
    "operating_state": {
      "point": "Run_Status",
      "equals": "ON"
    },
    "comparison": {
      "left": "Supply_Air_Temperature",
      "operator": "ABS_DIFF_GT",
      "right": "Supply_Air_Temperature_Setpoint",
      "threshold": 3,
      "unit": "C"
    },
    "duration_minutes": 15,
    "severity": "CRITICAL"
  }
}
```

ตัวอย่างนี้เป็นโครงสร้างออกแบบ ไม่ใช่ข้อมูลที่ต้อง copy แบบตายตัว

---

# 14. Phase 7 — Required AFDD Rule

ต้อง implement rule นี้:

```text
Target:
AHUs serving tenant areas
on selected office-building floors

Condition:
AHU is ON

AND

Supply Air Temperature differs from
Supply Air Temperature Setpoint
by more than 3°C

AND

condition remains true continuously
for 15 minutes

Result:
one Critical issue
```

ต้อง support:

```text
property-specific threshold OR duration override
```

และ:

```text
exclude equipment missing required point
```

---

# 15. Phase 8 — Ontology-Based Target Resolution

Rule ต้อง resolve target จาก relationships

ห้าม:

```text
name matching
string guessing
hard-coded AHU list
```

ต้องทำ:

```text
Rule Target
 ↓
Ontology Query
 ↓
Candidate Equipment
 ↓
Relationship Validation
 ↓
Required Points Check
 ↓
Exclusions
 ↓
Matched Assets
```

Preview ต้องแสดง:

```text
Matched equipment
Relationship path
Effective local values
Missing points
Exclusions
```

---

# 16. Phase 9 — Deterministic AFDD Evaluator

Evaluator ต้องใช้:

```text
device recorded timestamp
```

ไม่ใช้:

```text
platform received timestamp
```

## Logic

Conceptually:

```text
For each targeted AHU:

    verify required points exist

    verify AHU is ON

    verify readings are fresh

    calculate:

        abs(SAT - Setpoint)

    if difference > effective threshold:

        start/continue qualifying interval

    if condition remains continuously true
    for full duration:

        create issue

    if condition becomes normal:

        recover issue
```

---

# 17. Freshness / Old Data

ต้องมี policy ที่ชัดเจนว่า reading เก่าแค่ไหนจึงไม่นับว่า current

Assessment ต้องการให้:

```text
old readings
missing readings
```

ไม่สามารถสร้าง misleading issue ได้

ค่าความสดของข้อมูลเป็น design decision ต้อง document assumption และใช้ให้ deterministic

---

# 18. AFDD State Lifecycle

ต้องกำหนด behavior อย่างชัดเจน:

```text
NORMAL
  ↓
QUALIFYING
  ↓
ACTIVE ISSUE
  ↓
RECOVERED
```

กรณี:

```text
AHU OFF
→ ไม่ qualify

missing input
→ ไม่ qualify / insufficient data

old input
→ ไม่ qualify / insufficient data

condition normal
→ recovery

fault later happens again
→ new occurrence

rule changed
→ new rule version
```

ต้องป้องกันการสร้าง duplicate issue จาก evaluator รอบถัด ๆ ไป

---

# 19. Issue Evidence Model

ทุก issue ต้อง reconstruct ได้ว่า:

```text
ทำไมเกิด
เกิดเมื่อไร
ใช้ Rule Version ไหน
ข้อมูลอะไรเป็นตัว trigger
```

เก็บอย่างน้อย:

```text
rule_version
trigger_interval
observations
calculated_difference
threshold
data_quality
affected_zone
affected_rooms
```

ควรเก็บ trigger/qualifying observations ให้ตรวจสอบย้อนหลังได้

---

# 20. Rule Versioning

ห้ามแก้ rule แล้วทำให้ issue เก่าเปลี่ยนความหมาย

ตัวอย่าง:

```text
Rule v1
threshold = 3°C
duration = 15m

Issue #100
→ created by Rule v1
```

ภายหลัง:

```text
Rule v2
threshold = 4°C
```

Issue #100 ต้องยังอ้าง:

```text
Rule v1
```

---

# 21. Local Override

ต้อง support property-specific override อย่างน้อยหนึ่งกรณี

Logical flow:

```text
Global Rule
    ↓
Property Override
    ↓
Effective Configuration
    ↓
Evaluation
```

Dashboard ต้องแสดง:

```text
Global value
Local override
Effective value
```

---

# 22. Phase 10 — Dashboard

ต้องมี 3 focused views

## View A — Portfolio / Property Overview

ต้องเห็น:

```text
Property
Floor
Zone

AHU latest values
Meter latest values
IAQ latest values

Active issues

Ingestion time
Evaluation time

Errors
Lag
```

## View B — Issue Investigation

ต้องเห็น:

```text
Rule version
Issue state
Issue timestamps

SAT trend
Setpoint trend
Run status
Calculated difference
Threshold
Qualifying interval
Data gaps
Trigger point
```

## View C — Rule Detail / Preview

ต้องเห็น:

```text
Plain-language intent
Structured configuration
Selectors
Matched assets
Exclusions
Local overrides
Versions
```

Actions:

```text
Validate
Preview
Activate
Disable
Adjust
```

---

# 23. Dashboard Explainability

ต้องแยกประเภทข้อมูล:

## Triggering data

```text
Supply Air Temperature
Supply Air Temperature Setpoint
```

## Context data

```text
Return Air Temperature
AHU Alarm
Room IAQ
Floor Electricity Meter
```

UI ต้องไม่ทำให้ context data ดูเหมือนเป็น trigger

ทุก telemetry value ต้องแสดง:

```text
unit
observed time
freshness
quality
```

และต้องมี states:

```text
loading
empty
error
insufficient data
```

---

# 24. Affected Space Calculation

เมื่อ Issue เกิด:

```text
AHU
 ↓ directly serves
HVAC Zone
 ↓
Rooms
```

Affected scope:

```text
Zone
Rooms
```

ต้องแสดงว่าเป็น:

```text
Potentially affected
```

ไม่ใช่ claim ว่า room มี mechanical fault

AFDD issue เป็นเหตุผลให้ investigate ไม่ใช่ proof ของ mechanical root cause

---

# 25. Phase 11 — AI Rule Authoring

ต้องสร้าง agentic workflow

ไม่ใช่:

```text
prompt → LLM → POST /activate
```

## Required architecture

```text
User Request
 ↓
AI Orchestrator
 ↓
Bounded Tools
 ├── ontology discovery
 ├── rule validation
 ├── target preview
 ├── exclusion analysis
 └── clarification
 ↓
Structured Rule Draft
 ↓
Human Review
 ↓
Human Confirmation
 ↓
Activation
```

---

# 26. AI Safety Boundary

AI:

```text
MAY:
- interpret request
- plan
- call bounded tools
- inspect results
- ask clarification
- produce structured draft
```

AI:

```text
MUST NOT:
- invent asset IDs
- execute arbitrary code
- query unrestricted database
- directly activate rule
```

Server ต้องเป็นคน resolve identities

Deterministic service ต้อง validate final structured rule

---

# 27. AI State Machine

แนะนำให้มี explicit states:

```text
RECEIVED
 ↓
PLANNING
 ↓
DISCOVERING
 ↓
VALIDATING
 ↓
PREVIEWING
 ↓
NEEDS_CLARIFICATION
 ↓
DRAFT_READY
 ↓
HUMAN_REVIEW
 ↓
CONFIRMED
 ↓
ACTIVATED
```

Failure paths:

```text
FAILED
STOPPED
TIMEOUT
UNSUPPORTED
NO_MATCH
INVALID_TOOL_OUTPUT
```

ชื่อ state ปรับได้ แต่ behavior ต้องชัดเจน

---

# 28. AI Tool Contracts

Tool ทุกตัวต้อง bounded และ structured

ตัวอย่าง capability:

```text
discover_ontology(...)
validate_rule(...)
preview_rule_target(...)
get_exclusions(...)
```

Tool response ต้องเป็น schema ที่ deterministic

ห้ามให้ model เขียน SQL หรือ query unrestricted database เอง

---

# 29. AI Clarification

ถ้า request ขาดข้อมูลสำคัญ:

```text
AI ต้องถาม
```

ห้ามเดา

ตัวอย่าง variation ใน Assessment:

```text
Compare return-air temperature
with room IAQ temperature
in same zone
while AHU is ON
above 5°C
→ Warning
```

ถ้าต้องรู้ว่า:

- รวม room readings อย่างไร
- freshness เท่าไร
- duration เท่าไร

ให้ถาม user แทนการเดา

---

# 30. AI Failure Handling

ต้อง handle:

```text
paraphrase
missing details
unexpected ontology result
unsupported logic
empty target
invalid tool output
timeout
retry
stop limit
```

ทุก failure ต้องปลอดภัย:

```text
No automatic activation
```

---

# 31. AI Persistence / Audit

ต้อง persist:

```text
request
tool results
reviewed draft
human confirmation
activation result
audit history
rule version
```

และควรเก็บ:

```text
tool traces
latency
retries
stop reasons
model version
schema version
```

เพื่อ reproduce failure

---

# 32. AI Test Matrix

ต้องมี repeatable test cases:

| Case | Expected |
|---|---|
| Supported | Produce valid draft |
| Paraphrased | Interpret same intent |
| Ambiguous | Ask clarification |
| Unsupported | Safe rejection |
| No-match | No activation |
| Invented asset | Reject / resolve from server |
| Changed ontology | Re-discover / validate |
| Recoverable failure | Retry |
| Invalid tool output | Reject safely |
| Timeout | Stop safely |
| Missing detail | Clarification |

อย่างน้อยต้องมี real model call ตามโจทย์

Deterministic stubs ใช้ใน tests ได้

---

# 33. Phase 12 — Testing

ต้อง test ทั้ง system

## Foundation

```text
valid event
invalid event
duplicate
out-of-order
missing
wrong unit
wrong identity
```

## AFDD

```text
normal data
fault < 15 min
fault = 15 min
fault > 15 min
AHU OFF
missing data
old data
recovery
repeated fault
rule version
override
missing required point
```

## Ontology

```text
correct relationship
wrong relationship
installation room vs served room
target scope
exclusion
```

## AI

ใช้ matrix จาก Section 32

---

# 34. Phase 13 — Observability

ต้องสามารถตอบ:

```text
Telemetry event อยู่ตรงไหน?
ทำไมไม่เข้า?
ทำไม duplicate ไม่เกิดผล?
Evaluator ตรวจเมื่อไร?
Issue trigger จาก observation ไหน?
AI เรียก tool อะไร?
ทำไม AI หยุด?
```

Structured logs ต้องมี context ที่จำเป็น

อย่างน้อย:

```text
event_id
point_id
timestamp
service
rule_id
rule_version
issue_id
request_id
tool_run_id
```

---

# 35. Phase 14 — Docker Compose

Compose ต้องประกอบ service ที่จำเป็น:

```text
frontend
api
broker
simulator
ingestion
afdd-worker
postgres/timescaledb
```

ระบบต้องสามารถ start ได้ด้วย documented command เดียว

ต้องมี:

```text
health checks
environment variables
migration
seed
reset
telemetry replay/simulation
```

---

# 36. Phase 15 — README

README ต้องทำให้ Engineer คนอื่นสามารถ:

```text
clone
configure
start
seed
reset
run telemetry
run tests
inspect API
open dashboard
run demo
```

โดยไม่ต้องถามผู้พัฒนา

ต้องมี:

```text
Product purpose
Implemented scope
Architecture summary
Known limitations
Prerequisites
Environment variables
Setup
Migration
Seed
Reset
Simulation/replay
Startup
Health checks
Tests
API access
Demo steps
```

---

# 37. Required Documentation

ต้องมี:

```text
docs/
├── architecture.md
├── brickschema.md
├── afdd.md
├── ai-rule-authoring.md
├── decisions.md
└── demo.md
```

## architecture.md

อธิบาย:

```text
component diagram
telemetry ingestion flow
AFDD evaluation flow
NL rule flow
service boundaries
data stores
trust boundaries
```

## brickschema.md

อธิบาย:

```text
entity classes
relationships
application metadata
ontology storage
time-series identity mapping
new-building onboarding
changed ontology
```

## afdd.md

อธิบาย:

```text
rule schema
target/fault separation
timing
freshness
issue lifecycle
evidence
limitations
```

## ai-rule-authoring.md

อธิบาย:

```text
agent
bounded tools
deterministic services
stores
trust boundaries
success sequence
clarification/failure sequence
tool contracts
retry
stop conditions
observability
versioning
scaling
```

## decisions.md

บันทึก:

```text
alternative options
chosen option
reason
trade-offs
```

## demo.md

อธิบาย:

```text
end-to-end sequence
expected result
screenshots
video / screenshot walkthrough
AI assistance note
```

---

# 38. Demo Script

ต้องเตรียม Demo ตามลำดับนี้

## Step 1

Start system

```text
docker compose up
```

## Step 2

Seed supplied inventory

ตรวจ:

```text
3 buildings
12 floors
24 zones
48 rooms
24 AHUs
48 IAQ devices
12 meters
```

## Step 3

Start telemetry

แสดง current state

## Step 4

เปิด AI Rule Authoring

Input request:

```text
For all office properties, monitor AHUs serving tenant areas.
While an AHU is ON, if supply-air temperature differs from
its setpoint by more than 3°C continuously for 15 minutes,
create a Critical issue.
```

## Step 5

AI แสดง:

```text
interpreted intent
target
logic
validation
matched assets
exclusions
```

## Step 6

Human confirms

เท่านั้นจึง activate

## Step 7

Replay seeded fault

## Step 8

Dashboard เปิด Issue

แสดง:

```text
when
why
threshold
duration
observations
rule version
```

## Step 9

แสดง affected scope

```text
AHU
→ Zone
→ Rooms
```

## Step 10

แสดง pipeline health

```text
ingestion
evaluation
errors
lag
```

## Step 11

Demonstrate one failure

เช่น:

```text
missing data
```

หรือ

```text
duplicate event
```

แล้วอธิบาย behavior

---

# 39. Review Session Preparation

Review ประมาณ:

```text
60–75 minutes
```

ต้องพร้อม:

1. Demo hero journey
2. Trace telemetry event ผ่านระบบ
3. Investigate failure 1 case
4. Explain architecture
5. Explain trade-offs
6. Handle small in-scope variation

สิ่งที่ reviewer สนใจคือ reasoning มากกว่า presentation polish

---

# 40. Priority / Time Management

Assessment ระบุ expected effort ประมาณ:

```text
16–20 hours
4–5 days
```

ไม่ใช่ hard time limit

ดังนั้นต้อง prioritize:

## P0 — ต้องเสร็จ

```text
Docker Compose
Seed
Telemetry
Ingestion
Ontology
AFDD Engine
Issue Evidence
Dashboard
AI Rule Draft
Validation
Human Confirmation
Tests
README
Architecture docs
Demo
```

## P1 — เพิ่มถ้ามีเวลา

```text
better UX
more test coverage
better observability
better failure visualization
```

## P2 — Bonus

```text
Historical Backtesting
MCP server
```

Bonus ห้ามทำจน core ไม่ reliable

---

# 41. Optional Bonus — Historical Backtesting

ถ้ามีเวลา:

```text
Draft Rule
 ↓
Historical Period
 ↓
Same Evaluator
 ↓
Predicted Issues
 ↓
Insufficient-data intervals
 ↓
Compare configurations
```

ต้องแยกออกจาก:

```text
Live Issues
Activation
```

---

# 42. Optional Bonus — MCP

สามารถ expose:

```text
ontology
AFDD rules
current issues
historical issues
evidence
```

ผ่าน MCP

แต่ยังต้อง:

```text
validation
versioning
audit
preview
human activation
```

---

# 43. AI Coding Agent Instructions

ใช้ Blueprint นี้เป็น source of truth

## Global instruction

```text
You are implementing a Senior Full Stack Engineer assessment.

Treat the supplied assessment document and supporting pack as the source of truth.

Do not invent entity IDs, relationships, expected outcomes, telemetry fixtures, or requirements when they are supplied by the assessment data.

Do not skip core requirements for convenience.

Prioritize correctness, deterministic behavior, traceability, explainability, reproducibility, and testability over UI polish.

Do not hard-code the required AFDD rule as a special code path. Implement a configurable rule schema separating target scope from fault logic.

Do not allow the AI rule-authoring workflow to directly activate rules.

All AI-generated rule drafts must pass server-side ontology resolution, validation, preview, and human confirmation.

Do not query unrestricted data from the AI agent.

Do not allow AI to invent asset identities.

Use device-recorded timestamps for telemetry evaluation, not platform receipt timestamps.

Duplicate telemetry must be idempotent.

Older observations must not overwrite newer current state.

Missing or stale telemetry must remain visibly insufficient/missing and must not create misleading AFDD issues.

Every issue must preserve the rule version and evidence required to reconstruct why the issue triggered.

Keep AHU installation location separate from the spaces served by the AHU.

Before implementing a major architectural decision, document the decision and trade-off.

After each implementation phase, run relevant tests and verify behavior before proceeding.
```

---

# 44. Recommended AI Execution Order

อย่าสั่ง AI ว่า:

```text
Build the whole project.
```

ให้ทำเป็น phases

```text
Phase 0
Read assessment + supporting pack
→ produce data model and requirements checklist

Phase 1
Architecture
→ component boundaries
→ database choice
→ ontology strategy
→ broker strategy
→ ADR

Phase 2
Database + ontology registry

Phase 3
Telemetry simulator

Phase 4
Broker + ingestion

Phase 5
Current state + TimescaleDB

Phase 6
Core APIs

Phase 7
Rule schema

Phase 8
Ontology target resolver

Phase 9
Deterministic AFDD evaluator

Phase 10
Issue lifecycle + evidence

Phase 11
Dashboard

Phase 12
AI rule authoring

Phase 13
Testing

Phase 14
Docker Compose + reproducibility

Phase 15
Documentation

Phase 16
Demo preparation

Phase 17
Final assessment audit
```

---

# 45. Definition of Done

Project ถือว่าเสร็จเมื่อ reviewer สามารถทำทั้งหมดนี้ได้โดยไม่ต้องถาม developer:

```text
[ ] docker compose starts system
[ ] health checks pass
[ ] seed produces expected inventory
[ ] simulator streams telemetry
[ ] ingestion validates events
[ ] duplicate has no second effect
[ ] old event does not overwrite newer state
[ ] invalid event is visibly rejected
[ ] missing data remains missing
[ ] ontology relationships resolve correctly
[ ] AHU → Zone → Room path works
[ ] installation room is separated from served rooms
[ ] rule target can be changed independently
[ ] fault logic can be changed independently
[ ] required 3°C / 15-minute rule works
[ ] AHU OFF does not trigger
[ ] missing/old data does not misleadingly trigger
[ ] recovery works
[ ] later fault can recur
[ ] local override works
[ ] missing required point is excluded
[ ] issue stores rule version
[ ] issue stores evidence
[ ] dashboard reconstructs seeded issue
[ ] dashboard shows affected rooms
[ ] dashboard shows pipeline health
[ ] AI produces structured draft
[ ] AI resolves identities through server tools
[ ] AI can ask clarification
[ ] AI rejects unsupported/no-match cases safely
[ ] AI cannot activate without human confirmation
[ ] AI traces are persisted
[ ] tests cover core scenarios
[ ] OpenAPI is available
[ ] README is reproducible
[ ] architecture documentation exists
[ ] demo evidence exists
[ ] private GitHub repository is configured
[ ] no secrets are committed
```

---

# 46. Final Assessment Strategy

สิ่งที่ต้องทำให้ reviewer เห็นชัดที่สุด:

```text
1. DATA IS TRUSTWORTHY
        ↓
2. ONTOLOGY GIVES CORRECT MEANING
        ↓
3. RULE TARGETING IS CONFIGURABLE
        ↓
4. AFDD EVALUATION IS DETERMINISTIC
        ↓
5. ISSUE HAS REPRODUCIBLE EVIDENCE
        ↓
6. DASHBOARD EXPLAINS WHY
        ↓
7. AFFECTED SPACES ARE DERIVED FROM RELATIONSHIPS
        ↓
8. AI HELPS BUT CANNOT BYPASS SAFETY
        ↓
9. HUMAN CONTROLS ACTIVATION
        ↓
10. EVERYTHING IS TESTABLE AND REPRODUCIBLE
```

นี่คือแกนหลักของ Assessment

อย่า optimize เพื่อ "ทำ feature เยอะที่สุด"

ให้ optimize เพื่อ:

```text
Correctness
+
Traceability
+
Determinism
+
Explainability
+
Safety
+
Reproducibility
+
Senior-level architecture decisions
```

---

# 47. Final AI Prompt Template

ใช้ prompt นี้นำหน้าแต่ละ phase:

```text
Read the assessment blueprint in docs/ASSESSMENT_BLUEPRINT.md
and the original assessment/supporting data.

You are working on one phase only.

Before coding:
1. Inspect the existing repository.
2. Identify what is already implemented.
3. Map the current implementation against the blueprint.
4. Identify dependencies and risks.
5. State the implementation plan briefly.

During implementation:
1. Follow the assessment source of truth.
2. Do not invent supplied data.
3. Keep domain logic deterministic.
4. Keep services/components focused.
5. Add tests for behavior introduced in this phase.
6. Do not break previously completed phases.
7. Keep configuration separate from hard-coded logic.
8. Preserve observability and traceability.

After implementation:
1. Run tests.
2. Run lint/type checks where applicable.
3. Run the relevant service(s).
4. Verify the required behavior manually where practical.
5. Report changed files.
6. Report tests executed and results.
7. Report known limitations.
8. Do not move to the next phase until this phase is verified.

Do not silently change requirements.
If the assessment does not specify something, make the smallest reasonable implementation choice and document the assumption.
```

---

# 48. Final Checklist Before Submission

```text
CORE
[ ] Foundation reliable
[ ] AFDD deterministic
[ ] Dashboard explainable
[ ] AI safe
[ ] Tests pass

DATA
[ ] Seed reproducible
[ ] Fixtures reproducible
[ ] Duplicate safe
[ ] Missing data visible
[ ] Timestamp semantics correct

ONTOLOGY
[ ] Explicit relationships
[ ] AHU → Zone → Room
[ ] Installation room separated
[ ] Target preview works

RULE
[ ] Scope configurable
[ ] Logic configurable
[ ] 3°C / 15m works
[ ] Override works
[ ] Lifecycle works
[ ] Versioning works
[ ] Evidence works

AI
[ ] Agentic workflow
[ ] Bounded tools
[ ] Server identity resolution
[ ] Validation
[ ] Preview
[ ] Clarification
[ ] Safe rejection
[ ] Human confirmation
[ ] Audit trail

DELIVERY
[ ] Docker Compose
[ ] README
[ ] OpenAPI
[ ] Architecture diagram
[ ] BrickSchema documentation
[ ] AFDD documentation
[ ] AI documentation
[ ] Decision records
[ ] Demo guide
[ ] Screenshots
[ ] Video / walkthrough
[ ] Private GitHub
[ ] No secrets
```

---

## Source Mapping

- Assessment mission and four tasks: Pages 1
- Building operations primer: Page 2
- Ontology and spatial understanding: Page 3
- Data and scope: Page 4
- Foundation: Page 5
- Configurable AFDD engine: Page 6
- Dashboard: Page 7
- AI-assisted rule creation: Page 8
- Delivery and documentation: Pages 9–10
- Evaluation and review: Page 11
