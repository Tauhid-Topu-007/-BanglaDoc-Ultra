from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import re
import random
from datetime import datetime
from collections import Counter
import unicodedata

app = FastAPI()

# Bangla Date System
BANGLA_NUMBERS = {0: '০', 1: '১', 2: '২', 3: '৩', 4: '৪', 5: '৫', 6: '৬', 7: '৭', 8: '৮', 9: '৯'}
BANGLA_DAYS = {'Monday': 'সোমবার', 'Tuesday': 'মঙ্গলবার', 'Wednesday': 'বুধবার', 'Thursday': 'বৃহস্পতিবার', 'Friday': 'শুক্রবার', 'Saturday': 'শনিবার', 'Sunday': 'রবিবার'}
BANGLA_MONTHS = ['বৈশাখ', 'জ্যৈষ্ঠ', 'আষাঢ়', 'শ্রাবণ', 'ভাদ্র', 'আশ্বিন', 'কার্তিক', 'অগ্রহায়ণ', 'পৌষ', 'মাঘ', 'ফাল্গুন', 'চৈত্র']
BANGLA_SEASONS_MONTHS = {'গ্রীষ্ম': ['বৈশাখ', 'জ্যৈষ্ঠ'], 'বর্ষা': ['আষাঢ়', 'শ্রাবণ'], 'শরৎ': ['ভাদ্র', 'আশ্বিন'], 'হেমন্ত': ['কার্তিক', 'অগ্রহায়ণ'], 'শীত': ['পৌষ', 'মাঘ'], 'বসন্ত': ['ফাল্গুন', 'চৈত্র']}

def to_bangla_number(num):
    return ''.join(BANGLA_NUMBERS[int(d)] for d in str(num))

def get_bangla_date_full():
    now = datetime.now()
    bangla_year = now.year - 593
    if now.month < 4:
        bangla_year -= 1
    month_index = (now.month - 1) % 12
    bangla_month = BANGLA_MONTHS[month_index]
    bangla_day = now.day if now.day > 13 else now.day + 17
    if bangla_day > 31:
        bangla_day = bangla_day - 31
    current_season = "বসন্ত"
    for season, months in BANGLA_SEASONS_MONTHS.items():
        if bangla_month in months:
            current_season = season
            break
    day_name = BANGLA_DAYS[now.strftime('%A')]
    season_icon = {'গ্রীষ্ম': '☀️', 'বর্ষা': '🌧️', 'শরৎ': '🍂', 'হেমন্ত': '🌾', 'শীত': '❄️', 'বসন্ত': '🌸'}.get(current_season, '🌍')
    return {
        'bangla_date': f"{to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)}",
        'bangla_day': day_name,
        'season': current_season,
        'season_icon': season_icon,
        'time': now.strftime('%I:%M %p'),
        'full_bangla_datetime': f"{day_name}, {to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)} - {now.strftime('%I:%M %p')}"
    }

def clean_bangla_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def bangla_word_count(text):
    return len(re.findall(r'[\u0980-\u09FF]+', text))

def bangla_char_count(text):
    bengali_chars = {'অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'এ', 'ঐ', 'ও', 'ঔ', 'ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন', 'প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'শ', 'ষ', 'স', 'হ', 'ড়', 'ঢ়', 'য়', 'ৎ', 'ং', 'ঃ', 'ঁ'}
    return len([c for c in text if c in bengali_chars])

def bangla_sentence_count(text):
    sentences = re.split(r'[।?!]', text)
    return len([s for s in sentences if s.strip()])

def extract_keywords_advanced(text, num=7):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    word_freq = Counter(words)
    stopwords = {'এবং', 'হয়ে', 'হতে', 'থেকে', 'একটি', 'এই', 'ও', 'সে', 'তা', 'আমি', 'তুমি'}
    for stop in stopwords:
        word_freq.pop(stop, None)
    return [w for w, _ in word_freq.most_common(num)]

def text_summarization_advanced(text, ratio=0.3):
    sentences = re.split(r'[।?!]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    if len(sentences) <= 3:
        return text
    scored = []
    for sent in sentences:
        score = len(sent.split())
        keywords = extract_keywords_advanced(sent, 3)
        score += len(keywords) * 3
        scored.append((sent, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    num = max(2, int(len(sentences) * ratio))
    selected = [s for s, _ in scored[:num]]
    selected.sort(key=lambda x: sentences.index(x))
    return '। '.join(selected) + '।'

def sentiment_analysis_advanced(text):
    positive = {'ভালো', 'চমৎকার', 'সুন্দর', 'আনন্দ', 'খুশি', 'পছন্দ', 'সফল', 'জয়', 'প্রিয়'}
    negative = {'খারাপ', 'মন্দ', 'দুঃখ', 'বেদনা', 'ঘৃণা', 'ব্যর্থ', 'হার', 'শোক', 'ক্ষতি'}
    words = text.split()
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    if pos > neg:
        return {'sentiment': 'পজিটিভ', 'emoji': '😊', 'positive': pos, 'negative': neg, 'score': pos/(pos+neg) if (pos+neg)>0 else 0}
    elif neg > pos:
        return {'sentiment': 'নেগেটিভ', 'emoji': '😢', 'positive': pos, 'negative': neg, 'score': neg/(pos+neg) if (pos+neg)>0 else 0}
    return {'sentiment': 'নিউট্রাল', 'emoji': '😐', 'positive': pos, 'negative': neg, 'score': 0.5}

def text_complexity_analysis(text):
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
    if avg_word_len < 4:
        level = 'সহজ'
    elif avg_word_len < 6:
        level = 'মধ্যম'
    else:
        level = 'কঠিন'
    return {'level': level, 'avg_word_length': f'{avg_word_len:.1f}'}

# API Models
class BanglaTextInput(BaseModel):
    text: str

# API Endpoints
@app.get("/api/bangla-date")
async def get_bangla_date_api():
    return get_bangla_date_full()

@app.post("/api/super-summarize")
async def super_summarize(input_data: BanglaTextInput):
    text = clean_bangla_text(input_data.text)
    if len(text) < 20:
        return {"error": "কমপক্ষে ২০ অক্ষরের টেক্সট দিন", "status": "error"}
    summary = text_summarization_advanced(text)
    keywords = extract_keywords_advanced(text)
    return {
        'smart_summary': summary,
        'key_concepts': keywords,
        'word_count': bangla_word_count(text),
        'compression_rate': f"{(1 - len(summary)/len(text)) * 100:.1f}%",
        'status': 'success'
    }

@app.post("/api/complete-analysis")
async def complete_analysis(input_data: BanglaTextInput):
    text = clean_bangla_text(input_data.text)
    return {
        'basic_stats': {
            'characters': len(text),
            'bangla_chars': bangla_char_count(text),
            'words': bangla_word_count(text),
            'sentences': bangla_sentence_count(text)
        },
        'sentiment': sentiment_analysis_advanced(text),
        'keywords': extract_keywords_advanced(text, 7),
        'complexity': text_complexity_analysis(text),
        'status': 'success'
    }

@app.post("/api/sentiment")
async def sentiment_api(input_data: BanglaTextInput):
    return sentiment_analysis_advanced(input_data.text)

@app.post("/api/grammar-check")
async def grammar_check(input_data: BanglaTextInput):
    text = input_data.text
    corrections = []
    if '  ' in text:
        corrections.append("একাধিক স্পেস পাওয়া গেছে")
    if not text.strip().endswith(('।', '?', '!')):
        corrections.append("বাক্যের শেষে বিরাম চিহ্ন নেই")
    return {'has_errors': len(corrections) > 0, 'corrections': corrections, 'status': 'success'}

@app.post("/api/text-transform")
async def text_transform(input_data: BanglaTextInput):
    text = input_data.text
    return {
        'reverse': text[::-1],
        'word_count': len(text.split()),
        'char_count': len(text),
        'bangla_char_count': bangla_char_count(text),
        'status': 'success'
    }

# HTML Route
@app.get("/")
async def home():
    bangla_date = get_bangla_date_full()
    
    html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BanglaDoc Ultra - বাংলা এআই প্রসেসর</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Hind Siliguri', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            min-height: 100vh;
        }}
        .navbar {{
            background: rgba(255,255,255,0.95);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .logo {{ display: flex; align-items: center; gap: 10px; }}
        .logo-icon {{
            width: 45px; height: 45px;
            background: linear-gradient(135deg, #0f2027, #2c5364);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} }}
        .logo-icon i {{ font-size: 24px; color: white; }}
        .logo-text {{ font-size: 22px; font-weight: 700; color: #0f2027; }}
        .datetime-widget {{
            background: linear-gradient(135deg, #0f2027, #2c5364);
            padding: 8px 15px;
            border-radius: 25px;
            color: white;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 15px; }}
        .features-grid {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
            justify-content: center;
        }}
        .feature-card {{
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 10px 18px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }}
        .feature-card:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
        .feature-card.active {{ background: linear-gradient(135deg, #0f2027, #2c5364); color: white; }}
        .feature-icon {{ font-size: 16px; margin-right: 5px; }}
        .feature-title {{ font-size: 13px; font-weight: 600; }}
        .split-panels {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .panel {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 20px;
            min-height: 400px;
            display: flex;
            flex-direction: column;
        }}
        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            color: #0f2027;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        textarea {{
            width: 100%;
            min-height: 250px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
            outline: none;
        }}
        textarea:focus {{ border-color: #2c5364; }}
        .summary-output {{
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background: #fafafa;
            border-radius: 15px;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
        }}
        .action-buttons {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 15px;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            cursor: pointer;
            font-weight: 500;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #0f2027, #2c5364);
            color: white;
            flex: 1;
        }}
        .btn-secondary {{ background: #f0f0f0; color: #333; }}
        .loader {{
            display: inline-block;
            width: 18px; height: 18px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #2c5364;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .footer {{ text-align: center; padding: 15px; color: rgba(255,255,255,0.7); font-size: 11px; }}
        @media (max-width: 768px) {{
            .split-panels {{ grid-template-columns: 1fr; }}
            .features-grid {{ justify-content: center; }}
            .datetime-widget {{ font-size: 10px; gap: 6px; }}
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            <div class="logo-icon"><i class="fas fa-brain"></i></div>
            <div><div class="logo-text">BanglaDoc Ultra</div></div>
        </div>
        <div class="datetime-widget">
            <span><i class="fas fa-calendar-alt"></i> {bangla_date['bangla_day']}</span>
            <span class="bangla-date"><i class="fas fa-clock"></i> {bangla_date['bangla_date']}</span>
            <span><i class="fas fa-leaf"></i> {bangla_date['season_icon']} {bangla_date['season']}</span>
            <span><i class="fas fa-clock"></i> {bangla_date['time']}</span>
        </div>
    </div>

    <div class="container">
        <div class="features-grid" id="features-grid"></div>

        <div class="split-panels">
            <div class="panel">
                <div class="panel-title"><i class="fas fa-pen-fancy"></i> ইনপুট টেক্সট</div>
                <textarea id="input-text" placeholder="এখানে আপনার বাংলা টেক্সট লিখুন..."></textarea>
                <div class="action-buttons">
                    <button class="btn btn-primary" id="processBtn" onclick="processText()"><i class="fas fa-play"></i> প্রসেস</button>
                    <button class="btn btn-secondary" onclick="clearAll()"><i class="fas fa-trash"></i> ক্লিয়ার</button>
                    <button class="btn btn-secondary" onclick="loadExample()"><i class="fas fa-file-alt"></i> উদাহরণ</button>
                </div>
            </div>
            <div class="panel">
                <div class="panel-title"><i class="fas fa-star-of-life"></i> ফলাফল</div>
                <div id="output-content" class="summary-output"><i class="fas fa-brain"></i> ফলাফল এখানে দেখাবে...</div>
            </div>
        </div>
        <div class="footer"><p>⚡ BanglaDoc Ultra | বাংলা এআই প্রসেসর</p></div>
    </div>

    <script>
        const features = [
            {{ id: 'summarize', icon: '📝', name: 'সুপার সামারাইজার' }},
            {{ id: 'analysis', icon: '🔬', name: 'সম্পূর্ণ বিশ্লেষণ' }},
            {{ id: 'sentiment', icon: '😊', name: 'সেন্টিমেন্ট' }},
            {{ id: 'grammar', icon: '✅', name: 'গ্রামার চেক' }},
            {{ id: 'transform', icon: '🔄', name: 'টেক্সট ট্রান্সফর্ম' }}
        ];
        let currentFeature = features[0];

        function renderFeatures() {{
            const grid = document.getElementById('features-grid');
            grid.innerHTML = features.map(f => `
                <div class="feature-card ${f.id === currentFeature.id ? 'active' : ''}" onclick="setFeature('${f.id}')">
                    <span class="feature-icon">${f.icon}</span>
                    <span class="feature-title">${f.name}</span>
                </div>
            `).join('');
        }}

        function setFeature(id) {{
            currentFeature = features.find(f => f.id === id);
            renderFeatures();
        }}

        async function processText() {{
            const text = document.getElementById('input-text').value;
            if (!text.trim()) {{ alert('টেক্সট লিখুন'); return; }}
            if (text.length < 20) {{ alert('কমপক্ষে ২০ অক্ষর দিন'); return; }}
            
            const output = document.getElementById('output-content');
            const btn = document.getElementById('processBtn');
            output.innerHTML = '<div class="loader"></div> প্রসেসিং...';
            btn.disabled = true;
            
            try {{
                let response, data;
                const apiMap = {{
                    summarize: '/api/super-summarize',
                    analysis: '/api/complete-analysis',
                    sentiment: '/api/sentiment',
                    grammar: '/api/grammar-check',
                    transform: '/api/text-transform'
                }};
                const url = apiMap[currentFeature.id];
                response = await fetch(url, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ text: text }})
                }});
                data = await response.json();
                output.innerHTML = formatOutput(data);
            }} catch(err) {{
                output.innerHTML = `<div style="background:#f8d7da; padding:15px; border-radius:10px;">❌ ${err.message}</div>`;
            }} finally {{ btn.disabled = false; }}
        }}

        function formatOutput(data) {{
            if (data.error) return `<div style="background:#f8d7da; padding:15px; border-radius:10px;">❌ ${data.error}</div>`;
            let html = '';
            for (let [key, val] of Object.entries(data)) {{
                if (key !== 'status') {{
                    if (typeof val === 'object') {{
                        html += `<div style="background:white; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #2c5364;"><strong>📌 ${key}:</strong><br><pre style="margin-top:5px;">${JSON.stringify(val, null, 2)}</pre></div>`;
                    }} else {{
                        html += `<div style="background:white; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #2c5364;"><strong>📌 ${key}:</strong><br>${val}</div>`;
                    }}
                }}
            }}
            return html;
        }}

        function clearAll() {{
            document.getElementById('input-text').value = '';
            document.getElementById('output-content').innerHTML = '<i class="fas fa-brain"></i> ফলাফল এখানে দেখাবে...';
        }}

        function loadExample() {{
            document.getElementById('input-text').value = 'বাংলাদেশ একটি ছোট কিন্তু জনবহুল দেশ। এটি দক্ষিণ এশিয়ায় অবস্থিত। ঢাকা এর রাজধানী। এখানে অনেক প্রাকৃতিক সৌন্দর্য রয়েছে। সুন্দরবন বিশ্বের সবচেয়ে বড় ম্যানগ্রোভ বন। কক্সবাজার বিশ্বের দীর্ঘতম সমুদ্র সৈকত।';
        }}

        renderFeatures();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

handler = app