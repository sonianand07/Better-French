# Better French Website

A minimalist, Steve Jobs-inspired website that presents daily French news headlines in simplified format for French learners and native speakers.

## 🚀 Quick Start

### ⚡ One-Command Setup (Recommended)
```bash
cd better-french-website && python3 -m http.server 8000 & sleep 2 && open http://localhost:8000
```
**This single command will:**
- Navigate to the website directory
- Start the web server on port 8000
- Wait for server to start
- Automatically open your browser to the website

### 🌐 Manual Setup
```bash
# From the project root, navigate to website folder
cd better-french-website

# Start local web server
python3 -m http.server 8000

# Open browser manually
open http://localhost:8000
# or visit: http://localhost:8000
```

### 🛑 To Stop Server
```bash
pkill -f "python3 -m http.server 8000"
```

### 🔧 Troubleshooting
- **"Address already in use" error**: Run the stop command above first
- **"File not found" errors**: Make sure you're in the `better-french-website` directory
- **Data not loading**: Ensure `04_Data_Output/` folder exists in the website directory

## 📁 File Structure

```
better-french-website/
├── index.html              # Main HTML page
├── styles.css              # Complete CSS styling
├── script.js               # JavaScript functionality
├── logo.svg                # Better French wordmark
├── favicon.svg             # Minimalist "F" icon
└── README.md               # This file
```

## 🎯 Features

- **Dual Mode Experience**: Toggle between Learner Mode (English) and Native Mode (French)
- **Interactive Tooltips**: Hover over French words for definitions and cultural context
- **Real-time Search**: Filter articles instantly
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Accessibility**: WCAG AA compliant with keyboard navigation

## 🎨 Design

- **Colors**: Pure white background, charcoal text, Bordeaux accents (#8C1A26)
- **Typography**: Work Sans font family with precise weights and sizes
- **Layout**: 8px grid system with Steve Jobs-inspired minimalism
- **Animations**: Smooth 200ms transitions throughout

## 📊 Data Source

The website automatically loads data from:
```
04_Data_Output/Processed_AI/ai_processed_curated_news_data_*.json
```
**Contains:** 30 curated French news articles with:
- Original French headlines with interactive word explanations
- Simplified English/French titles
- Detailed summaries in both languages
- Cultural context and definitions

## 🖱️ Usage

1. **Mode Toggle**: Click "Learner Mode" or "Native Mode" to switch languages
2. **Search**: Type in the search box to filter articles
3. **Read Summaries**: Click "Read English/French Summary" to expand article details
4. **Interactive Words**: Hover over underlined French words for definitions
5. **Load More**: Click "Load 10 more articles" to see additional content

## 🛠️ Browser Support

- Chrome 80+, Firefox 75+, Safari 13+, Edge 80+
- JavaScript ES6+ features required
- No external dependencies

## 📱 Responsive Behavior

- **Desktop (1024px+)**: Two-column grid layout
- **Tablet (600-1024px)**: Single column with optimized spacing
- **Mobile (<600px)**: Touch-optimized with repositioned tooltips

---

**Note**: This website is part of the "Project Better French Max" system and includes all necessary French news data files. The one-command setup automatically handles all dependencies and opens the fully functional website with 30 curated French news articles ready for learning! 🎉

**Last Updated**: June 2025 - Ready to run locally with zero configuration needed. 