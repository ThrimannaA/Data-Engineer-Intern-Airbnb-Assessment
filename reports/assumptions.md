# Assumptions Document

## Data Quality Assumptions

### 1. Price Field
  **Assumption:** The `price` column in listings and calendar files contains USD amounts with `$` prefix and comma separators

  **Implication:** Must strip `$` and `,` before converting to numeric

  **Validation:** After cleaning, ensure no negative prices and reasonable ranges

  **Treatment:** Negative or zero prices will be flagged as invalid and handled with explicit nulls

### 2. Availability Dates
  **Assumption:** Calendar data covers 365 days from the snapshot date

  **Implication:** Availability_365 should match sum of available calendar days

  **Validation:** Check consistency between `availability_365` and calendar counts

  **Treatment:** If mismatch >5%, investigate and document

### 3. Missing Values'

  **Assumption:** Missing values represent unknown information rather than meaningful categories

  **Implication:** Explicit nulls will be used rather than imputation in most cases

  **Validation:** High null rates in review scores may indicate newer listings

  **Treatment:** Nulls preserved as `NULL` in star schema; analysts can decide imputation strategy

### 4. Host Information

  **Assumption:** Host data (response_rate, host_since) is as reported and current

  **Implication:** Older records may have less accurate host information

  **Validation:** Compare host_tenure calculations with host_since dates

  **Treatment:** Host_since before snapshot date is validated; impossible dates flagged

### 5. Neighbourhood Mapping

  **Assumption:** Neighbourhood names are consistent across files

  **Implication:** Joins on neighbourhood name should be exact matches

  **Validation:** Check for misspellings or variations (e.g., "Harlem" vs "Central Harlem")

  **Treatment:** Fuzzy matching for small discrepancies; manual review for major differences

### 6. Review Scores

  **Assumption:** Review scores are out of 10 (overall rating system)

  **Implication:** Scores can be compared meaningfully across listings

  **Validation:** Check score distribution for expected patterns (typically 4.0-5.0)

  **Treatment:** Scores outside expected range flagged for investigation

### 7. City Snapshot Dates

  **Assumption:** All files for a city come from the same snapshot date

  **Implication:** Data is consistent within each city dataset
  
  **Validation:** Check file timestamps and data recency
  
  **Treatment:** If dates differ, note in decision log

### 8. Regulatory Context
  
  **Assumption:** Regulatory impacts (NYC Local Law 18, Barcelona 2028 ban) are reflected in market dynamics

  **Implication:** Analysis should examine whether these regulations correlate with observable patterns
  
  **Validation:** Compare trends before/after key regulatory dates where data allows
  
  **Treatment:** Regulatory analysis is qualitative and contextual, not causal

## Data Processing Assumptions

### 9. Cross-City Harmonization

  **Assumption:** Column names and types are similar enough across cities to harmonize
  
  **Implication:** Can build unified pipeline with mapping for minor differences

  **Validation:** Schema comparison conducted in notebook
  
  **Treatment:** Differences documented in decision log

### 10. Star Schema Implementation
  
  **Assumption:** Analytical queries are best served by dimensional model

  **Implication:** Denormalization decisions balance query performance vs storage
  
  **Validation:** Query performance tested with representative use cases

  **Treatment:** Trade-offs documented and indexed appropriately

## Business Context Assumptions

### 11. Calendar as Occupancy Proxy
  
  **Assumption:** Unavailable nights in calendar represent booked nights
  
  **Implication:** Revenue estimates = price × nights_unavailable

  **Validation:** Compare with review counts as demand proxy

  **Treatment:** Explicitly caveat in analysis

### 12. Market Definition
  
  **Assumption:** Each city is a distinct market with own dynamics

  **Implication:** Cross-city comparisons need normalization

  **Validation:** Market concentration and supply characteristics compared

  **Treatment:** Report suggests areas for deeper investigation

## Limitations

1. **No Transaction Data:** Calendar availability is a proxy, not actual bookings
2. **Snapshot Nature:** Quarterly snapshots miss continuous dynamics
3. **Potential Scraping Artifacts:** Data quality may vary by snapshot
4. **Missing Historical Context:** Only current snapshot available
5. **Regulatory Attribution:** Cannot establish causation between regulations and market changes
6. **Platform Changes:** Airbnb policy changes not captured
7. **Guest Demographics:** No data on who books or for what purpose
8. **Competitor Context:** No data on alternative accommodations (hotels, VRBO)

## Decision Log Reference

All major decisions in the project are documented in `reports/decision_log.md` with:

- Options considered

- Chosen approach

- Trade-offs accepted

- Rationale for selection

### Database Selection

- **Decision:** 

Switched from DuckDB to SQLite

- **Rationale:** 

SQLite has better compatibility across systems

No need for pre-existing database files

Built into Python standard library

Simpler for the assessment environment

- **Trade-offs:** 

SQLite has less analytical functionality than DuckDB

Some advanced window functions not available

But still sufficient for all required queries