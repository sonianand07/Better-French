# AI Engine v5: Intelligent Separated Architecture

## 🎯 **Core Innovation: Intelligent Topic-Aware Curation**

AI Engine v5 solves the fundamental problems of v3/v4:
- **No more bulk processing overload** (separated workflows)
- **Intelligent semantic deduplication** (heat wave = heat waves)
- **Topic-aware selection** (avoids bombarding same news themes)
- **Website-aware curation** (considers existing 100 articles)

## 🏗️ **Two-Workflow Architecture**

### Workflow 1: Data Collection (Hourly)
```yaml
name: Collect & Curate News - v5
schedule: '0 * * * *'  # Every hour
```
**What it does:**
- Scrapes news sources
- Applies semantic deduplication
- Analyzes topics vs existing website content
- Selects 10 truly NEW/DIFFERENT articles
- Stores in `ai_engine_v5/data/collected/hourly_batch_YYYYMMDD_HH.json`

### Workflow 2: AI Processing (On-demand)
```yaml
name: Process Collected Articles - v5
workflow_dispatch: true  # Manual trigger
```
**What it does:**
- Reads collected batches
- Applies V3 processing (Gemini 2.5 Flash)
- Applies V4 verification (GPT-4o-mini)
- Deploys enhanced websites
- Preserves development data for iteration

## 🧠 **Intelligent Curation System**

### Problem Solved:
❌ **Before:** "Heat wave in Paris", "Heat waves continue in France", "Paris swelters in heat"
✅ **After:** AI Engine v5 recognizes these as the SAME story and picks the best one

### How It Works:

#### 1. **Semantic Deduplication**
```python
# Instead of simple string matching
if article.title == existing.title:  # ❌ Miss semantic duplicates

# v5 uses semantic similarity
if semantic_similarity(article, existing) > 0.85:  # ✅ Catches variations
```

#### 2. **Topic Analysis**
```python
# Analyze what topics are already covered on website
existing_topics = analyze_website_topics(current_articles)
# ["heat_wave", "politics", "sports", "economy"]

# Score new articles based on topic diversity
for article in candidates:
    topic_score = calculate_topic_novelty(article, existing_topics)
```

#### 3. **Quality-Based Selection**
```python
# When multiple articles cover same topic, pick the best one
if topic_overlap:
    selected = max(articles, key=lambda x: x.quality_score)
```

## 📊 **Data Flow**

```
[News Sources] 
    ↓
[Hourly Scraper] (raw articles)
    ↓
[Semantic Deduplicator] (removes duplicates)
    ↓
[Topic Analyzer] (analyzes vs website)
    ↓
[Quality Selector] (picks best 10)
    ↓
[Collected Batch] → hourly_batch_YYYYMMDD_HH.json
    ↓
[AI Processor] (when triggered)
    ↓
[V3 + V4 Enhancement]
    ↓
[Website Deployment]
```

## 🎯 **Development Benefits**

### **Preserved V3/V4 Capabilities:**
- ✅ V3 processing (simplified titles, summaries, tooltips)
- ✅ V4 verification (quality checking, error correction)
- ✅ Dual website deployment (comparison)

### **New v5 Advantages:**
- 🔥 **No bulk processing** - AI only sees 10 articles max
- 🧠 **Semantic intelligence** - recognizes topic variations
- 📊 **Website awareness** - considers existing content
- 🚀 **Development friendly** - work with same data during iteration
- 💰 **Cost predictable** - bounded AI usage
- 🔧 **Easy debugging** - separate scraping from processing

## 📈 **Expected Results**

### **Website Quality:**
- **More diverse topics** (no heat wave spam)
- **Higher quality articles** (best of each topic)
- **Balanced coverage** (politics + sports + culture, not just politics)

### **Operational Efficiency:**
- **10 articles per batch** instead of 1,000+
- **Predictable costs** (~$0.50 per processing run)
- **Faster iteration** (work with cached data during development)
- **Better monitoring** (clear separation of concerns)

## 🚀 **Implementation Roadmap**

### Phase 1: Intelligent Curator
- [ ] Semantic similarity engine
- [ ] Topic analysis system
- [ ] Website content analyzer
- [ ] Quality-based selector

### Phase 2: Data Collection Workflow
- [ ] Hourly scraper workflow
- [ ] Collected data storage
- [ ] Batch management system

### Phase 3: AI Processing Workflow
- [ ] V3 processing integration
- [ ] V4 verification integration
- [ ] Dual website deployment

### Phase 4: Development Tools
- [ ] Data replay system
- [ ] Topic visualization
- [ ] Quality metrics dashboard

**🎯 Goal: Launch v5 with first intelligent batch by next week!** 