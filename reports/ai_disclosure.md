# AI Usage Disclosure

## AI Usage Philosophy

AI tools were used as development assistants rather than decision makers throughout this project. While AI assisted with code generation, debugging, documentation, and analytical approaches, all technical decisions, validation procedures, business interpretations, and final conclusions were made by the author.

All AI-generated outputs were critically reviewed, tested, and modified where necessary before inclusion in the final submission. AI suggestions were treated as recommendations rather than authoritative answers, and their suitability was evaluated against project requirements, data characteristics, and business objectives.

The final deliverables represent human-led work supported by AI-assisted productivity and problem-solving tools.

---

## 1. AI Tools Used

| Tool               | Version           | Purpose                                    | Usage Frequency |
| ------------------ | ----------------- | ------------------------------------------ | --------------- |
| **DeepSeek**       | Latest            | Code structure, debugging, report template | High            |
| **Claude**         | Claude 3.5 Sonnet | Pipeline design, statistical explanation   | High            |
| **GitHub Copilot** | Latest            | Code completion, function generation       | Medium          |

---

## 2. AI-Assisted Sections

### Data Engineering

- Assisted with ingestion pipeline structure
- Suggested error handling approaches
- Helped debug SQLite loading issues
- Assisted in schema design

### Data Analysis

- Suggested EDA approaches
- Assisted with statistical test implementation
- Helped interpret cross-city comparisons

### Reporting

- Assisted with report organization
- Suggested wording for business insights
- Helped improve documentation clarity

---

## 3. Key Prompts Used

### Data Engineering Prompts

1. _"Design error handling and logging for reusable Airbnb data ingestion pipeline"_

    **Response**: Provided structure with LocalDataLoader class

    **Modification**: Added Windows compatibility (encoding fixes)

2. _"Implement star schema for Airbnb data with SQLite"_

    **Response**: Generated dimension and fact table creation

    **Modification**: Added dynamic column detection

### Statistical Prompts

3. _"Implement hypothesis tests H1-H5 with effect sizes and business interpretations"_

    **Response**: Provided scipy implementations

    **Modification**: Added Levene's test for variance checking

4. _"Create correlation analysis with VIF for multicollinearity"_

    **Response**: Generated correlation matrix code

    **Modification**: Added business interpretation

### ML Prompts

5. _"Implement XGBoost price prediction with feature importance"_

    **Response**: Provided model training code

    **Modification**: Added SHAP for explainability

### NLP Prompts

6. _"Create sentiment analysis and topic modeling for Airbnb reviews"_

    **Response**: Provided VADER and NMF implementation

    **Modification**: Added RAG system

### Dashboard Prompts

7. _"Create Streamlit dashboard for cross-city Airbnb comparison"_
    
    **Response**: Provided dashboard structure

    **Modification**: Added radar chart for comparison

### Report Prompts

8. _"Write business interpretations for EDA findings"_

    **Response**: Provided initial drafts

    **Modification**: Customized for three-city analysis

---

## 4. Output Validation

### Code Validation

- **All AI-generated code**: Reviewed line-by-line
- **Error handling**: Verified for edge cases
- **Data types**: Validated for SQLite compatibility
- **Performance**: Tested with sample datasets

### Statistical Validation

- **Manual Cross-Check**: Key calculations verified with alternative methods
- **Assumption Checks**: Normality, variance, independence verified
- **Effect Sizes**: Compared with literature benchmarks

### Model Validation

- **Cross-Validation**: 5-fold CV to prevent overfitting
- **Residual Analysis**: Checked for patterns
- **Feature Importance**: Validated against domain knowledge

### Business Validation

- **Interpretations**: Verified against known market patterns
- **Recommendations**: Assessed for feasibility
- **Insights**: Cross-referenced with multiple sources

---

## 5. Modifications Made

### Code Modifications

| AI Output             | Modification         | Reason                  |
| --------------------- | -------------------- | ----------------------- |
| DuckDB implementation | Converted to SQLite  | Windows compatibility   |
| Standard emojis       | Removed from logging | Console encoding issues |
| Hardcoded paths       | Converted to config  | Reusability             |
| Price tier logic      | Customized function  | Null handling           |

### Analysis Modifications

| AI Output               | Modification               | Reason               |
| ----------------------- | -------------------------- | -------------------- |
| Generic interpretations | Customized for 3 cities    | Business context     |
| Standard visualizations | Enhanced for accessibility | Clarity              |
| One-size-fits-all       | City-specific breakdowns   | Comparative analysis |

---

## 6. Critical Assessment

### Rejected AI Suggestions

1. **Neural Network Architecture**
      **Suggestion**: Use deep learning for price prediction

      **Rejection Reason**: Overkill for this dataset, XGBoost performed well

      **Decision**: Stick with XGBoost

2. **Cloud Deployment**
      **Suggestion**: Deploy to AWS/GCP

      **Rejection Reason**: Assessment focus on analysis, not deployment

      **Decision**: Document architecture instead

3. **Complex Feature Engineering**
      **Suggestion**: Create 30+ interaction features

      **Rejection Reason**: Risk of overfitting

      **Decision**: Keep to 15 well-chosen features

### Substantially Modified AI Suggestions

1. **Price Tier Assignment**
      **Original**: Used `pd.cut()` with bins

      **Modified**: Custom function with null handling

      **Reason**: Avoided `NoneType` comparison errors

2. **Sentiment Analysis**
      **Original**: Only used VADER

      **Modified**: Added correlation with ratings

      **Reason**: Business value of sentiment-rating relationship

---

## 7. Lessons Learned

### Effective AI Collaboration

1. **Specific Prompts**: More specific prompts yield better outputs
2. **Iterative Refinement**: Multiple iterations improve quality
3. **Validation is Essential**: Always verify AI outputs
4. **Context Matters**: Provide business context in prompts
5. **Document Everything**: Track what was AI-assisted

### AI Limitations

1. **Context Window**: Cannot process full dataset at once
2. **Business Nuance**: Requires human interpretation
3. **Edge Cases**: Often missed in initial implementation
4. **Current Events**: May not know latest data
5. **Customization**: Always needs adaptation

---

## 8. Ethical Considerations

### Responsible AI Use

1. **Disclosure**: Full transparency about AI usage
2. **Validation**: All outputs verified
3. **Ownership**: Intellectual ownership maintained
4. **Originality**: AI used for acceleration, not replacement
5. **Attribution**: Not claiming AI work as original

### Data Privacy

1. **No Personal Data**: All data is public Airbnb data
2. **No API Keys**: Not exposed in code
3. **Local Processing**: All computation local
4. **GDPR Compliance**: Anonymized data only

---

## 9. AI Contribution Summary

| Area             | AI Contribution | Human Contribution | Balance       |
| ---------------- | --------------- | ------------------ | ------------- |
| Code Development | 40%             | 60%                | Human-led     |
| Analysis         | 30%             | 70%                | Human-led     |
| Interpretation   | 20%             | 80%                | Human-led     |
| Report Writing   | 30%             | 70%                | Human-led     |
| **Overall**      | **30%**         | **70%**            | **Human-led** |

---

## 10. Conclusion

AI tools were used responsibly as acceleration and assistance tools throughout this assessment. All AI-generated outputs were critically evaluated, validated, and modified as needed. The final submission represents human-led work with AI assistance, maintaining intellectual ownership and professional integrity.

**Key Principles Followed:**

- ✅ Full disclosure
- ✅ Critical evaluation
- ✅ Output validation
- ✅ Human leadership
- ✅ Business context

---
