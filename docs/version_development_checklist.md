# AI Engine Version Development Checklist

## **Purpose**
This checklist ensures NO CRITICAL ISSUES are missed when developing new AI Engine versions. Created after V5 development revealed multiple oversights that required manual discovery.

**Rule: Check EVERY item before claiming a version is "ready"**

---

## **🏗️ ARCHITECTURE & DESIGN**

### **Core System Design**
- [ ] **Architecture document created** (`ARCHITECTURE_README.md`)
- [ ] **Problem statement defined** (What does this version solve?)
- [ ] **Quality preservation verified** (No reduction from previous version)
- [ ] **Backward compatibility planned** (Data, APIs, workflows)
- [ ] **Deployment strategy defined** (Separate sites, directories, domains)
- [ ] **Rollback plan documented** (How to revert if issues found)

### **Data Flow Design**
- [ ] **Input sources identified** (31 RSS feeds, data files, APIs)
- [ ] **Processing pipeline mapped** (Each step documented)
- [ ] **Output formats specified** (JSON schemas, HTML structures)
- [ ] **Error handling designed** (Fallbacks, retries, graceful degradation)
- [ ] **Data persistence strategy** (Storage, cleanup, retention)

---

## **🔑 API KEYS & SECURITY**

### **API Key Management**
- [ ] **Separate API keys for different purposes** (dev, scraper, processor)
- [ ] **GitHub Secrets configured** (All required keys added)
- [ ] **Local environment setup documented** (How to test locally)
- [ ] **API key rotation plan** (What happens when keys expire)
- [ ] **Rate limiting considered** (Usage caps, cost controls)
- [ ] **Error handling for API failures** (401, 429, 503 responses)

### **Security Checklist**
- [ ] **No API keys in code** (All externalized to environment)
- [ ] **No API keys in git history** (Scan for accidental commits)
- [ ] **Minimal permissions** (Each workflow only has needed permissions)
- [ ] **Secrets rotation tested** (Workflows work with new keys)

---

## **📦 DEPENDENCIES & IMPORTS**

### **Package Dependencies**
- [ ] **requirements.txt updated** (All new dependencies added)
- [ ] **Package installation in workflows** (pip install commands complete)
- [ ] **Version pinning strategy** (Prevent breaking changes)
- [ ] **Cross-version compatibility** (V3, V4, V5 packages work together)
- [ ] **Python version compatibility** (3.11 works for all components)

### **Import Path Handling**
- [ ] **Robust import patterns** (Try/except for different environments)
- [ ] **PYTHONPATH handling** (CI vs local environments)
- [ ] **Relative vs absolute imports** (Consistent strategy)
- [ ] **Module not found fallbacks** (Graceful handling of missing modules)
- [ ] **Cross-package imports tested** (V5 importing V3/V4 components)

---

## **🔧 WORKFLOWS & CI/CD**

### **GitHub Actions Setup**
- [ ] **Workflow files created** (One for each major component)
- [ ] **Permissions configured** (contents: write, pages: write, etc.)
- [ ] **Environment variables set** (API keys, PYTHONPATH, etc.)
- [ ] **Concurrency handling** (Prevent overlapping runs)
- [ ] **Scheduling configured** (Correct cron expressions)
- [ ] **Manual triggers enabled** (workflow_dispatch for testing)

### **Dependency Installation**
- [ ] **All required packages installed** (requirements.txt + engine packages)
- [ ] **Installation order correct** (Base packages before engines)
- [ ] **Missing system dependencies identified** (spaCy models, etc.)
- [ ] **Build-time dependencies included** (Compilation tools if needed)

### **Error Handling & Monitoring**
- [ ] **Workflow failure modes identified** (What can go wrong)
- [ ] **Retry logic implemented** (For transient failures)
- [ ] **Fallback behaviors defined** (What happens when components fail)
- [ ] **Logging strategy implemented** (Sufficient debug information)
- [ ] **Cost monitoring included** (Track LLM usage and expenses)

---

## **🎯 QUALITY PRESERVATION**

### **Proven Component Reuse**
- [ ] **V3 scoring system preserved** (Keyword lists, weights, thresholds)
- [ ] **V3 prompts preserved** (`contextual_words_v3.jinja`, `simplify_titles_summaries_v3.jinja`)
- [ ] **V4 verification preserved** (`review_tooltips.jinja`, GPT-4o verification)
- [ ] **Display formats preserved** (**English:** _French word_ tooltip format)
- [ ] **Quality schemas preserved** (Article model, QualityScores structure)

### **Selection & Scoring Quality**
- [ ] **Selection criteria documented** (How articles are chosen)
- [ ] **Scoring thresholds verified** (Minimum quality standards maintained)
- [ ] **Profile integration tested** (User preferences actually influence results)
- [ ] **Diversity mechanisms working** (No "heat wave spam" problems)
- [ ] **Source quality maintained** (31 comprehensive sources, not reduced)

### **Processing Quality**
- [ ] **Enhancement pipeline tested** (V3+V4 processing works correctly)
- [ ] **Tooltip generation verified** (Contextual words display properly)
- [ ] **Title simplification tested** (French→English translations accurate)
- [ ] **Summary generation tested** (Appropriate reading level maintained)
- [ ] **Cultural notes included** (Educational context preserved)

---

## **🌐 WEBSITE & DEPLOYMENT**

### **Website Generation**
- [ ] **HTML structure preserved** (Same UI/UX as proven versions)
- [ ] **CSS files copied** (Styling consistency maintained)
- [ ] **JavaScript functionality** (Tooltips, interactions work correctly)
- [ ] **Data format compatibility** (rolling_articles.json structure preserved)
- [ ] **Metadata included** (Generation timestamps, version info)

### **Deployment Strategy**
- [ ] **Deployment destinations configured** (Root site, subdirectories)
- [ ] **Cache busting implemented** (Users see updates immediately)
- [ ] **Deployment conflicts avoided** (V3, V4, V5 don't overwrite each other)
- [ ] **Rollback strategy tested** (Can revert to previous version)
- [ ] **URL structure documented** (Where users find each version)

---

## **🧪 TESTING & VALIDATION**

### **System Testing**
- [ ] **Integration tests created** (All components work together)
- [ ] **End-to-end testing** (Full pipeline from scraping to website)
- [ ] **Error condition testing** (API failures, malformed data, etc.)
- [ ] **Performance testing** (Processing speed, memory usage)
- [ ] **Cost validation** (LLM usage within expected parameters)

### **Quality Assurance**
- [ ] **Output quality verified** (Articles meet educational standards)
- [ ] **UI/UX testing completed** (Website functions properly)
- [ ] **Cross-browser compatibility** (Tooltips work in all browsers)
- [ ] **Mobile responsiveness** (Website usable on mobile devices)
- [ ] **Accessibility compliance** (Screen readers, keyboard navigation)

### **Comparison Testing**
- [ ] **V3 vs V5 quality comparison** (No degradation in article quality)
- [ ] **V4 vs V5 enhancement comparison** (Tooltip quality maintained)
- [ ] **Performance comparison** (Speed, cost, reliability metrics)
- [ ] **User experience comparison** (Loading times, interaction smoothness)

---

## **📋 DOCUMENTATION & MAINTENANCE**

### **Documentation Requirements**
- [ ] **README files updated** (Clear setup and usage instructions)
- [ ] **Architecture documentation** (System design and data flow)
- [ ] **API documentation** (Endpoints, data formats, authentication)
- [ ] **Troubleshooting guide** (Common issues and solutions)
- [ ] **Deployment guide** (Step-by-step deployment instructions)

### **Maintenance Planning**
- [ ] **Monitoring strategy** (How to detect issues in production)
- [ ] **Update procedures** (How to modify the system safely)
- [ ] **Backup and recovery** (Data protection and restoration)
- [ ] **Performance optimization** (Bottleneck identification and resolution)
- [ ] **Cost optimization** (LLM usage efficiency improvements)

---

## **🚨 CRITICAL FAILURE MODES**

### **Issues That MUST Be Checked**
- [ ] **Generic LLM prompts** (Proven keyword systems replaced with vague instructions)
- [ ] **Missing threshold filtering** (Articles accepted without quality gates)
- [ ] **Import path failures** (ModuleNotFoundError in CI environments)
- [ ] **API key exposure** (Keys accidentally committed or exposed)
- [ ] **Dependency conflicts** (Package version incompatibilities)
- [ ] **Data format mismatches** (New version can't read previous data)
- [ ] **Deployment overwrites** (New version destroys previous deployments)
- [ ] **Silent quality degradation** (System appears to work but produces poor results)

### **Testing Red Flags**
- [ ] **"Success" with no cost reported** (API calls may be failing silently)
- [ ] **Identical content across versions** (Deployment conflicts)
- [ ] **Missing tooltips** (JavaScript parsing errors)
- [ ] **Broken article links** (Data format corruption)
- [ ] **Empty or minimal article sets** (Selection criteria too restrictive)

---

## **✅ FINAL VALIDATION CHECKLIST**

### **Before Release**
- [ ] **All previous items checked** (No shortcuts taken)
- [ ] **End-to-end test successful** (Full pipeline working)
- [ ] **Quality comparison completed** (No degradation from previous version)
- [ ] **Documentation complete** (Future maintainers can understand system)
- [ ] **Rollback plan tested** (Can revert if issues discovered)
- [ ] **Monitoring enabled** (Can detect issues in production)

### **Post-Release**
- [ ] **Monitor first 24 hours** (Watch for immediate issues)
- [ ] **Validate data quality** (Check actual article processing results)
- [ ] **User feedback collection** (Detect UX/UI issues)
- [ ] **Performance monitoring** (Ensure system remains responsive)
- [ ] **Cost tracking** (Verify LLM usage within budget)

---

## **📝 VERSION-SPECIFIC NOTES**

### **V5 Lessons Learned**
1. **Quality degradation through generic LLM prompts** - Always preserve proven keyword-based systems
2. **Import path failures in CI** - Use robust import patterns with fallbacks
3. **Missing dependencies** - Install ALL required packages, not just main requirements
4. **API key security issues** - Use separate keys for different purposes
5. **Silent failures** - Implement comprehensive error detection and reporting

### **V6 Considerations** (Future)
- [ ] **Multi-language support** (Extend beyond French)
- [ ] **User personalization** (Individual user profiles and preferences)
- [ ] **Real-time processing** (Live article updates without batch processing)
- [ ] **Advanced analytics** (User engagement tracking and optimization)
- [ ] **Mobile app integration** (API endpoints for mobile applications)

---

**Created**: 2025-06-29 after V5 development challenges  
**Updated**: After each version release  
**Owner**: AI pair-programmer and human maintainer  
**Review**: Before starting any new version development 