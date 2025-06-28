# Pre-Workflow Checklist

## ✅ **Before Running New Workflow**

### **API Key Verification**
- [ ] **Check API key validity**: Test locally with `OPENROUTER_API_KEY=<key> PYTHONPATH=. python3 scripts/verify_news.py`
- [ ] **Verify GitHub Secrets**: Ensure `OPENROUTER_API_KEY` in GitHub repo settings matches config
- [ ] **Check API balance**: Verify sufficient credits on OpenRouter account
- [ ] **Test API access**: Run a small verification call before full workflow

### **Data State Verification**  
- [ ] **V3 tooltips working**: Check main site tooltips display correctly
- [ ] **V4 tooltips working**: Check /v4-site/ tooltips display correctly
- [ ] **Cache cleared**: Hard refresh both sites (Cmd+Shift+R)
- [ ] **Recent updates visible**: Confirm latest articles appear

### **Workflow Monitoring**
- [ ] **Watch logs closely**: Don't assume "success" means no errors
- [ ] **Look for hidden failures**: API 401s may not fail the workflow
- [ ] **Monitor costs**: Track LLM usage during runs
- [ ] **Verify outputs**: Check actual article processing, not just exit codes

## 🚨 **Red Flags to Watch For**

### **In Workflow Logs**
- [ ] **"Verifier replied empty"** - API failure
- [ ] **"JSON parse error"** - LLM output corruption  
- [ ] **"HTTP 401"** - Authentication failure
- [ ] **"Failed after X attempts"** - Retry exhaustion
- [ ] **Successful exit but no cost reported** - Silent failure

### **On Websites**
- [ ] **HTML corruption visible** - Display format issues
- [ ] **No tooltips working** - JavaScript parsing errors
- [ ] **Identical content V3/V4** - Deployment conflicts  
- [ ] **Old timestamps** - Cache not clearing

## 🔧 **Emergency Fixes Available**

### **Tooltip Issues**
```bash
python3 scripts/fix_display_format.py  # Fix formatting
python3 scripts/auto_cache_bust.py     # Force refresh
```

### **API Issues**
```bash
# Test API locally first:
OPENROUTER_API_KEY=<key> PYTHONPATH=. python3 scripts/verify_news.py

# Check account balance at:
# https://openrouter.ai/account
```

### **Deployment Issues**
- V3 deploys to: `betterfrench.io` (root)
- V4 deploys to: `betterfrench.io/v4-site/` (subdirectory)
- Check both locations after workflow

## 📊 **Success Indicators**

### **V3 Workflow Success**
- [ ] New articles with recent timestamps
- [ ] Working tooltips with **English:** _French_ format
- [ ] Cost reported in logs ($0.01-0.05 typical)
- [ ] No API error messages

### **V4 Workflow Success** 
- [ ] `quality_checked: true` in data
- [ ] Enhanced cultural context in tooltips
- [ ] Deploys to `/v4-site/` not root
- [ ] Higher processing cost than V3 (GPT-4o verification)

## 🎯 **Next Steps After This Fix**

1. **Test both sites immediately**: Check tooltips work
2. **Run small workflow test**: Process just a few articles first
3. **Monitor API usage**: Watch for authentication issues
4. **Verify deployment separation**: Ensure V4 doesn't overwrite V3

---

**Last Updated**: 2025-06-28 after fixing 14,930 tooltip format issues 