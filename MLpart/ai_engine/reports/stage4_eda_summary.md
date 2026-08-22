# EcoMind AI — Stage 4 EDA Summary

- Records analysed: **363,168**
- Date range: **2025-07-01 00:00:00 → 2025-08-08 23:45:00**
- Total energy: **546,351.6 kWh**
- Buildings: **9** | Rooms: **97**

## Graph observations

### 1. Daily campus energy trend
Campus load shows weekday peaks and exam-period lift in library/lab demand.

### 2. Building-wise consumption
Hostels and computer labs dominate total energy due to occupancy duration and IT/HVAC load.

### 3. Building × hour energy heatmap
Academic blocks peak 09:00–16:00; hostels invert with night-time occupancy.

### 4. Peak hour analysis
Mean interval energy rises through late morning and remains elevated until evening hostel load.

### 5. Weather vs energy
Higher outdoor temperature correlates with AC-driven energy, especially above ~29°C.

### 6. Occupancy vs energy
Energy scales with occupancy but HVAC/IT rooms sit above the occupancy-only trend.

### 7. Device contribution proxy
Air-conditioning is the largest controllable contributor whenever outdoor temperature is high.

### 8. Weekly / monthly-scale trend
Weekly totals are stable with a late-July exam-window increase.

### 9. Weekend vs weekday
Weekday academic/admin load exceeds weekends; hostels remain relatively sticky.

### 10. Top-20 room utilization
Library halls and cafeteria dining rooms show the highest average occupancy ratios.

### 11. Category mean energy intensity
Computer labs have the highest mean intensity due to dense IT load plus HVAC.

### 12. Working-hours energy split
Working hours raise academic energy; after-hours residual load is a wastage target.

### 13. Humidity vs energy
Humidity is weakly associated with energy; temperature and occupancy dominate.

### 14. Active devices vs energy
Mean energy increases monotonically with concurrently active end-use devices.

### 15. Cooling load index vs energy
Cooling load index is a strong engineered predictor of HVAC-dominated intervals.

### 16. Power factor distribution
Power factor clusters near 0.90–0.96; AC-on intervals pull PF slightly lower.

### 17. Voltage distribution
Branch voltage stays around the 230 V Indian nominal with realistic feeder noise.

### 18. Indoor vs outdoor temperature
Indoor temperatures are suppressed relative to outdoor when HVAC is active.

### 19. Day-of-week energy
Monday–Friday academic schedules produce higher campus totals than weekends.

### 20. Occupancy heatmap by category
Hostels fill overnight; cafeteria peaks at lunch; library occupancy rises in the exam window.

### 21. Mean building utilization
Admin utilization is high during workdays but low absolute energy due to smaller rooms.

### 22. AC operating profile
AC duty cycle tracks hot working hours — the primary HVAC optimization lever.

### 23. Empty-room lighting wastage share
About 0.12% of intervals show lights on with zero occupancy — a lighting-control target.

### 24. Building weekend vs weekday intensity
Academic buildings drop sharply on weekends; hostels do not, confirming schedule-aware controls.
