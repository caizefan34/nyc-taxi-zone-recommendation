# External Validation Plan

## Overview
This document outlines plans for future external validation of the NYC Taxi Zone Recommendation system. These are **planned future activities**, not completed work.

## 1. Cross-City Validation
**Status:** Framework designed, not executed.

**Goal:** Validate that the framework generalizes to other cities.

**Steps:**
1. Download Chicago taxi trip data (publicly available)
2. Adapt data pipeline for Chicago format
3. Train forecasting models
4. Calibrate simulator for Chicago
5. Run benchmark and compare with NYC results

**Expected insight:** How much does city-specific calibration matter?

## 2. Real Driver Feedback
**Status:** Not started. Requires IRB approval.

**Goal:** Collect feedback from actual taxi drivers on recommendations.

**Method:**
- Survey or interview study with NYC taxi drivers
- Compare driver preferences with policy recommendations
- Identify practical deployment barriers

## 3. Online A/B Testing
**Status:** Not started. Requires production infrastructure.

**Goal:** Measure policy impact in a real deployment.

**Requirements:**
- Partner with dispatch platform or fleet operator
- Implement real-time recommendation API
- Track revenue, utilization, driver satisfaction
- Randomize recommendations across drivers

## 4. Production Deployment
**Status:** Not started.

**Requirements:**
- Real-time data ingestion pipeline
- Low-latency inference (< 100ms)
- Monitoring and alerting
- Gradual rollout with safety constraints

## Timeline (Provisional)
| Phase | Activity | Estimated Duration |
|-------|----------|-------------------|
| 1 | Cross-city validation | 3-6 months |
| 2 | Driver feedback study | 6-12 months |
| 3 | A/B testing design | 12-18 months |
| 4 | Production deployment | 18-24 months |

## Limitations
- All items are FUTURE WORK, not completed
- Timelines are estimates and depend on resources
- Cross-city validation requires new data downloads
- Real driver studies require additional approvals
