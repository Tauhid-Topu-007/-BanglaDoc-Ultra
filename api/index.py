from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
import torch
import re
from fastapi.middleware.cors import CORSMiddleware
import io
import hashlib
import json
from datetime import datetime
from typing import Optional, List
import unicodedata
from collections import Counter
import os
import random
from difflib import get_close_matches

# Initialize FastAPI app
app = FastAPI(title='BanglaDoc Ultra - বাংলা ডকুমেন্ট প্রসেসিং আলট্রা', 
              description='বাংলা ভাষার জন্য বিশ্বস্তরীয় এআই ডকুমেন্ট প্রসেসিং প্ল্যাটফর্ম', 
              version='3.0')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bangla Date System
BANGLA_NUMBERS = {
    0: '০', 1: '১', 2: '২', 3: '৩', 4: '৪',
    5: '৫', 6: '৬', 7: '৭', 8: '৮', 9: '৯'
}

BANGLA_DAYS = {
    'Monday': 'সোমবার',
    'Tuesday': 'মঙ্গলবার',
    'Wednesday': 'বুধবার',
    'Thursday': 'বৃহস্পতিবার',
    'Friday': 'শুক্রবার',
    'Saturday': 'শনিবার',
    'Sunday': 'রবিবার'
}

BANGLA_MONTHS = [
    'বৈশাখ', 'জ্যৈষ্ঠ', 'আষাঢ়', 'শ্রাবণ',
    'ভাদ্র', 'আশ্বিন', 'কার্তিক', 'অগ্রহায়ণ',
    'পৌষ', 'মাঘ', 'ফাল্গুন', 'চৈত্র'
]

BANGLA_SEASONS_MONTHS = {
    'গ্রীষ্ম': ['বৈশাখ', 'জ্যৈষ্ঠ'],
    'বর্ষা': ['আষাঢ়', 'শ্রাবণ'],
    'শরৎ': ['ভাদ্র', 'আশ্বিন'],
    'হেমন্ত': ['কার্তিক', 'অগ্রহায়ণ'],
    'শীত': ['পৌষ', 'মাঘ'],
    'বসন্ত': ['ফাল্গুন', 'চৈত্র']
}

BENGALI_CHARS = {'অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'এ', 'ঐ', 'ও', 'ঔ', 'ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন', 'প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'শ', 'ষ', 'স', 'হ', 'ড়', 'ঢ়', 'য়', 'ৎ', 'ং', 'ঃ', 'ঁ'}

BANGLA_WORD_DICT = {
    'প্রযুক্তি': ['টেক', 'সফটওয়্যার', 'হার্ডওয়্যার', 'নেটওয়ার্ক', 'ডেটা'],
    'শিক্ষা': ['বিদ্যালয়', 'কলেজ', 'বিশ্ববিদ্যালয়', 'শিক্ষক', 'ছাত্র'],
    'স্বাস্থ্য': ['চিকিৎসা', 'ঔষধ', 'হাসপাতাল', 'ডাক্তার', 'নার্স'],
    'কৃষি': ['ফসল', 'মাঠ', 'কৃষক', 'ধান', 'শস্য'],
    'অর্থনীতি': ['ব্যাংক', 'টাকা', 'লেনদেন', 'বিনিয়োগ', 'সঞ্চয়']
}

BANGLA_IDIOMS = {
    'অকাল কুষ্মাণ্ড': 'অসময়ের বাড়াবাড়ি',
    'অন্ধের যষ্টি': 'একমাত্র ভরসা',
    'আকাশ কুমুম': 'অসম্ভব বস্তু',
    'উলুবনে মুক্তা ছড়ানো': 'অযোগ্য স্থানে মূল্যবান বস্তু দেওয়া'
}

def to_bangla_number(num):
    """Convert English number to Bangla"""
    return ''.join(BANGLA_NUMBERS[int(d)] for d in str(num))

def get_bangla_date_full():
    """Get complete Bangla date with year, month, day, season"""
    now = datetime.now()
    
    # Bangla year calculation (Bengali calendar is 593 years behind Gregorian)
    bangla_year = now.year - 593
    if now.month < 4:  # Before April, Bengali year is one less
        bangla_year -= 1
    
    # Bangla month calculation
    month_index = (now.month - 1) % 12
    bangla_month = BANGLA_MONTHS[month_index]
    
    # Bangla day of month (approximate, typically 5-6 days offset)
    bangla_day = now.day
    if now.day > 13:
        bangla_day = now.day - 13
    else:
        bangla_day = now.day + 17
    
    # Get current season
    current_season = "বসন্ত"
    for season, months in BANGLA_SEASONS_MONTHS.items():
        if bangla_month in months:
            current_season = season
            break
    
    # Get day name
    day_name = BANGLA_DAYS[now.strftime('%A')]
    
    return {
        'bangla_date': f"{to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)}",
        'bangla_day': day_name,
        'bangla_month': bangla_month,
        'bangla_year': to_bangla_number(bangla_year),
        'bangla_day_number': to_bangla_number(bangla_day),
        'season': current_season,
        'season_icon': {
            'গ্রীষ্ম': '☀️', 'বর্ষা': '🌧️', 'শরৎ': '🍂',
            'হেমন্ত': '🌾', 'শীত': '❄️', 'বসন্ত': '🌸'
        }.get(current_season, '🌍'),
        'english_date': now.strftime('%B %d, %Y'),
        'english_day': now.strftime('%A'),
        'time': now.strftime('%I:%M %p'),
        'full_bangla_datetime': f"{day_name}, {to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)} - {now.strftime('%I:%M %p')}"
    }

def clean_bangla_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def bangla_word_count(text):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    return len(words)

def bangla_char_count(text):
    return len([c for c in text if c in BENGALI_CHARS])

def bangla_sentence_count(text):
    sentences = re.split(r'[।?!]', text)
    return len([s for s in sentences if s.strip()])

def extract_keywords_advanced(text, num=10):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    word_freq = Counter(words)
    stopwords = {'এবং', 'হয়ে', 'হতে', 'থেকে', 'একটি', 'এই', 'ও', 'সে', 'তা', 'আমি', 'তুমি', 'করে', 'করা', 'হয়', 'ছিল', 'হবে', 'নেই', 'না', 'যদি', 'তবে'}
    filtered = {k:v for k,v in word_freq.items() if k not in stopwords and len(k) > 1}
    return sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:num]

def text_summarization_advanced(text, ratio=0.3):
    sentences = re.split(r'[।?!]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if len(sentences) <= 3:
        return text
    
    scored = []
    for sent in sentences:
        score = len(sent.split())
        keywords = extract_keywords_advanced(sent, 5)
        score += len(keywords) * 3
        position_score = 1 - (sentences.index(sent) / len(sentences))
        score += position_score * 2
        scored.append((sent, score))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    num_sentences = max(2, int(len(sentences) * ratio))
    selected = [s for s, _ in scored[:num_sentences]]
    selected.sort(key=lambda x: sentences.index(x))
    
    return '। '.join(selected) + '।'

def sentiment_analysis_advanced(text):
    positive = ['ভালো', 'চমৎকার', 'সুন্দর', 'আনন্দ', 'খুশি', 'পছন্দ', 'সফল', 'জয়', 'প্রিয়', 'উত্তম']
    negative = ['খারাপ', 'মন্দ', 'দুঃখ', 'বেদনা', 'ঘৃণা', 'ব্যর্থ', 'হার', 'শোক', 'ক্ষতি', 'অসুখ']
    
    words = text.split()
    pos_count = sum(1 for w in words if w in positive)
    neg_count = sum(1 for w in words if w in negative)
    
    total = pos_count + neg_count
    if total == 0:
        return {'sentiment': 'নিউট্রাল', 'emoji': '😐', 'score': 0}
    
    if pos_count > neg_count:
        sentiment = 'পজিটিভ'
        emoji = '😊'
        score = pos_count / total
    elif neg_count > pos_count:
        sentiment = 'নেগেটিভ'
        emoji = '😢'
        score = neg_count / total
    else:
        sentiment = 'নিউট্রাল'
        emoji = '😐'
        score = 0.5
    
    return {'sentiment': sentiment, 'emoji': emoji, 'score': score, 'positive': pos_count, 'negative': neg_count}

def text_complexity_analysis(text):
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
    unique_words = len(set(words))
    vocab_richness = unique_words / len(words) if words else 0
    complex_words = len([w for w in words if len(w) > 5])
    
    if avg_word_len < 4:
        level = 'সহজ'
    elif avg_word_len < 6:
        level = 'মধ্যম'
    else:
        level = 'কঠিন'
    
    return {
        'level': level,
        'avg_word_length': f'{avg_word_len:.1f}',
        'vocab_richness': f'{vocab_richness:.2%}',
        'complex_words': complex_words,
        'total_words': len(words)
    }

def text_to_braille_bangla(text):
    braille_map = {
        'অ': '⠁', 'আ': '⠜', 'ই': '⠊', 'ঈ': '⠡', 'উ': '⠥', 'ঊ': '⠳',
        'ক': '⠅', 'খ': '⠭', 'গ': '⠛', 'ঘ': '⠣', 'চ': '⠉', 'ছ': '⠺',
        'জ': '⠚', 'ঝ': '⠱', 'ট': '⠞', 'ঠ': '⠹', 'ড': '⠙', 'ঢ': '⠮',
        'ত': '⠞', 'থ': '⠹', 'দ': '⠙', 'ধ': '⠮', 'ন': '⠝', 'প': '⠏',
        'ফ': '⠋', 'ব': '⠃', 'ভ': '⠧', 'ম': '⠍', 'য': '⠽', 'র': '⠗',
        'ল': '⠇', 'শ': '⠱', 'ষ': '⠱', 'স': '⠎', 'হ': '⠓'
    }
    
    result = []
    for char in text:
        if char in braille_map:
            result.append(braille_map[char])
        else:
            result.append(char)
    return ''.join(result)

class BanglaTextInput(BaseModel):
    text: str = Field(..., min_length=3, max_length=10000)
    operation: str = Field("summarize")
    length_ratio: Optional[float] = Field(0.3, ge=0.1, le=0.8)

@app.get("/bangla/date")
async def get_bangla_date_info():
    return get_bangla_date_full()

@app.post("/bangla/super-summarize")
async def super_summarize(input_data: BanglaTextInput):
    try:
        text = clean_bangla_text(input_data.text)
        if len(text) < 20:
            return {"error": "কমপক্ষে ২০ অক্ষরের টেক্সট দিন", "status": "error"}
        
        strategy1 = text_summarization_advanced(text, input_data.length_ratio)
        strategy2 = extract_keywords_advanced(text, 10)
        strategy3 = '। '.join(text.split('। ')[:max(2, int(len(text.split('। ')) * 0.3))]) + '।'
        
        return {
            'original_length': len(text),
            'word_count': bangla_word_count(text),
            'sentence_count': bangla_sentence_count(text),
            'smart_summary': strategy1,
            'quick_summary': strategy3,
            'key_concepts': [k for k, v in strategy2],
            'compression_rate': f"{(1 - len(strategy1)/len(text)) * 100:.1f}%",
            'status': 'success'
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.post("/bangla/complete-analysis")
async def complete_analysis(input_data: BanglaTextInput):
    try:
        text = clean_bangla_text(input_data.text)
        
        return {
            'basic_stats': {
                'characters': len(text),
                'bangla_chars': bangla_char_count(text),
                'words': bangla_word_count(text),
                'sentences': bangla_sentence_count(text),
                'avg_word_length': f"{sum(len(w) for w in text.split()) / len(text.split()):.1f}" if text.split() else '0'
            },
            'quality_metrics': {
                'complexity': text_complexity_analysis(text),
                'readability': 'সহজ' if len(text.split()) < 100 else 'মধ্যম' if len(text.split()) < 300 else 'কঠিন',
                'vocabulary_size': len(set(text.split()))
            },
            'semantic_analysis': {
                'sentiment': sentiment_analysis_advanced(text),
                'keywords': [k for k, v in extract_keywords_advanced(text, 7)],
                'main_topic': max(BANGLA_WORD_DICT.keys(), key=lambda topic: sum(1 for w in text.split() if w in BANGLA_WORD_DICT.get(topic, [])))
            },
            'special': {
                'braille': text_to_braille_bangla(text[:100]) + ('...' if len(text) > 100 else ''),
                'bangla_date': get_bangla_date_full()['full_bangla_datetime']
            },
            'status': 'success'
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.get("/bangla/idiom-search/{idiom}")
async def search_idiom(idiom: str):
    if idiom in BANGLA_IDIOMS:
        return {'idiom': idiom, 'meaning': BANGLA_IDIOMS[idiom], 'found': True}
    
    similar = get_close_matches(idiom, BANGLA_IDIOMS.keys(), n=3, cutoff=0.5)
    return {'idiom': idiom, 'meaning': 'খুঁজে পাওয়া যায়নি', 'suggestions': similar, 'found': False}

@app.post("/bangla/text-transform")
async def text_transform(input_data: BanglaTextInput):
    try:
        text = input_data.text
        return {
            'original': text,
            'transforms': {
                'reverse': text[::-1],
                'word_count': len(text.split()),
                'char_count': len(text),
                'bangla_char_count': bangla_char_count(text),
                'uppercase': text.upper(),
                'capitalized': text.title(),
                'slug': text.lower().replace(' ', '-')[:50]
            },
            'status': 'success'
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.post("/bangla/grammar-correction")
async def grammar_correction(input_data: BanglaTextInput):
    try:
        text = input_data.text
        corrections = []
        suggestions = []
        
        words = text.split()
        for i in range(len(words)-1):
            if words[i] == words[i+1]:
                corrections.append(f"পুনরাবৃত্ত শব্দ: '{words[i]}' দুইবার এসেছে")
                suggestions.append("একটি শব্দ মুছে ফেলুন")
        
        if not text.strip().endswith(('।', '?', '!')):
            corrections.append("বাক্যের শেষে বিরাম চিহ্ন নেই")
            suggestions.append("শেষে '।' যোগ করুন")
        
        if '  ' in text:
            corrections.append("একাধিক স্পেস পাওয়া গেছে")
            suggestions.append("একটি স্পেস রাখুন")
        
        return {
            'original': text,
            'corrected': text if not corrections else text + ('।' if not text.endswith(('।', '?', '!')) else ''),
            'corrections': corrections,
            'suggestions': suggestions,
            'has_errors': len(corrections) > 0,
            'status': 'success'
        }
    except Exception as e:
        return {'error': str(e), 'status': 'error'}

@app.get("/")
async def home():
    bangla_date = get_bangla_date_full()
    
    html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, height=device-height">
    <title>BanglaDoc Ultra - বিশ্বস্তরীয় বাংলা এআই প্রসেসর</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html, body {{
            height: 100%;
            width: 100%;
            overflow: hidden;
        }}

        body {{
            font-family: 'Hind Siliguri', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .navbar {{
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            flex-shrink: 0;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo-icon {{
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #0f2027, #2c5364);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}

        .logo-icon i {{
            font-size: 24px;
            color: white;
        }}

        .logo-text {{
            font-size: 24px;
            font-weight: 700;
            color: #0f2027;
        }}

        .logo-sub {{
            font-size: 10px;
            color: #666;
        }}

        .datetime-widget {{
            background: linear-gradient(135deg, #0f2027, #2c5364);
            padding: 8px 18px;
            border-radius: 25px;
            color: white;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }}

        .datetime-widget i {{
            margin-right: 5px;
        }}

        .bangla-date {{
            font-weight: 600;
            background: rgba(255,255,255,0.2);
            padding: 4px 10px;
            border-radius: 15px;
        }}

        .main-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 15px 20px 20px 20px;
            gap: 15px;
        }}

        .features-wrapper {{
            flex-shrink: 0;
            overflow-x: auto;
            overflow-y: visible;
            padding-bottom: 5px;
        }}

        .features-grid {{
            display: flex;
            gap: 12px;
            min-width: min-content;
        }}

        .feature-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 10px 18px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .feature-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .feature-card.active {{
            background: linear-gradient(135deg, #0f2027, #2c5364);
            color: white;
        }}

        .feature-icon {{
            font-size: 18px;
            margin-right: 6px;
        }}

        .feature-title {{
            font-size: 12px;
            font-weight: 600;
            display: inline;
        }}

        .split-panels {{
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            min-height: 0;
        }}

        .panel {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            min-height: 0;
        }}

        .panel-title {{
            font-size: 18px;
            font-weight: 600;
            color: #0f2027;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
            flex-shrink: 0;
        }}

        .panel-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }}

        textarea {{
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            font-family: 'Hind Siliguri', monospace;
            font-size: 14px;
            resize: none;
            outline: none;
            flex: 1;
            min-height: 0;
            background: #fafafa;
        }}

        textarea:focus {{
            border-color: #2c5364;
            background: white;
        }}

        .summary-output {{
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background: #fafafa;
            border-radius: 15px;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
        }}

        .input-footer, .output-footer {{
            margin-top: 12px;
            padding: 8px 12px;
            background: #f0f0f0;
            border-radius: 10px;
            font-size: 12px;
            color: #666;
            display: flex;
            justify-content: space-between;
            flex-shrink: 0;
        }}

        .action-buttons {{
            display: flex;
            gap: 12px;
            margin-top: 15px;
            flex-shrink: 0;
        }}

        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #0f2027, #2c5364);
            color: white;
            flex: 1;
        }}

        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(15, 32, 39, 0.3);
        }}

        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}

        .btn-secondary:hover {{
            background: #e0e0e0;
        }}

        .loader {{
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #2c5364;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .char-counter {{
            color: #888;
        }}

        .char-counter.warning {{
            color: #ff9800;
        }}

        .char-counter.valid {{
            color: #4caf50;
        }}

        @media (max-width: 968px) {{
            .split-panels {{
                grid-template-columns: 1fr;
                gap: 15px;
            }}
            
            .navbar {{
                flex-direction: column;
                padding: 10px 15px;
            }}
            
            .main-container {{
                padding: 10px;
            }}
            
            .feature-title {{
                font-size: 11px;
            }}
            
            .btn {{
                padding: 8px 15px;
                font-size: 12px;
            }}
            
            .datetime-widget {{
                font-size: 11px;
                gap: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            <div class="logo-icon">
                <i class="fas fa-brain"></i>
            </div>
            <div>
                <div class="logo-text">BanglaDoc Ultra</div>
                <div class="logo-sub">বিশ্বস্তরীয় বাংলা এআই প্রসেসর</div>
            </div>
        </div>
        <div class="datetime-widget">
            <div><i class="fas fa-calendar-alt"></i> {bangla_date['bangla_day']}</div>
            <div class="bangla-date"><i class="fas fa-clock"></i> {bangla_date['bangla_date']}</div>
            <div><i class="fas fa-leaf"></i> {bangla_date['season_icon']} {bangla_date['season']}</div>
            <div><i class="fas fa-clock"></i> {bangla_date['time']}</div>
        </div>
    </div>

    <div class="main-container">
        <div class="features-wrapper">
            <div class="features-grid">
                <div class="feature-card active" onclick="setOperation('summarize')">
                    <span class="feature-icon">📝</span>
                    <span class="feature-title">সুপার সামারাইজার</span>
                </div>
                <div class="feature-card" onclick="setOperation('analysis')">
                    <span class="feature-icon">🔬</span>
                    <span class="feature-title">সম্পূর্ণ বিশ্লেষণ</span>
                </div>
                <div class="feature-card" onclick="setOperation('sentiment')">
                    <span class="feature-icon">😊</span>
                    <span class="feature-title">সেন্টিমেন্ট</span>
                </div>
                <div class="feature-card" onclick="setOperation('grammar')">
                    <span class="feature-icon">✅</span>
                    <span class="feature-title">গ্রামার চেক</span>
                </div>
                <div class="feature-card" onclick="setOperation('transform')">
                    <span class="feature-icon">🔄</span>
                    <span class="feature-title">টেক্সট ট্রান্সফর্ম</span>
                </div>
                <div class="feature-card" onclick="setOperation('idiom')">
                    <span class="feature-icon">📖</span>
                    <span class="feature-title">ইডিয়ম খুঁজি</span>
                </div>
            </div>
        </div>

        <div class="split-panels">
            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-pen-fancy"></i> ইনপুট ম্যাট্রিক্স
                </div>
                <div class="panel-content">
                    <textarea id="input-text" placeholder="এখানে আপনার বাংলা টেক্সট লিখুন...&#10;AI ব্যবহার করে আমরা আপনার টেক্সট প্রসেস করব"></textarea>
                    <div class="input-footer">
                        <span><i class="fas fa-info-circle"></i> নূন্যতম ২০ অক্ষর প্রয়োজন</span>
                        <span class="char-counter" id="char-counter">০ অক্ষর</span>
                    </div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-title">
                    <i class="fas fa-star-of-life"></i> আউটপুট ফলাফল
                </div>
                <div class="panel-content">
                    <div id="output-content" class="summary-output">
                        <i class="fas fa-brain" style="margin-right: 10px; color: #2c5364;"></i>
                        ফলাফল এখানে দেখাবে...
                    </div>
                    <div class="output-footer">
                        <span><i class="fas fa-robot"></i> BanglaDoc AI</span>
                        <span id="timestamp">{bangla_date['full_bangla_datetime']}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="action-buttons">
            <button class="btn btn-primary" id="process-btn" onclick="processText()">
                <i class="fas fa-play"></i> প্রসেস করুন
            </button>
            <button class="btn btn-secondary" onclick="clearAll()">
                <i class="fas fa-trash"></i> ক্লিয়ার
            </button>
            <button class="btn btn-secondary" onclick="loadExample()">
                <i class="fas fa-file-alt"></i> উদাহরণ
            </button>
            <button class="btn btn-secondary" onclick="copyOutput()">
                <i class="fas fa-copy"></i> কপি
            </button>
        </div>
    </div>

    <script>
        let currentOperation = 'summarize';
        
        function updateCharCounter() {{
            const text = document.getElementById('input-text').value;
            const length = text.length;
            const counter = document.getElementById('char-counter');
            counter.textContent = length + ' অক্ষর';
            
            if (length > 0 && length < 20) {{
                counter.classList.add('warning');
                counter.classList.remove('valid');
            }} else if (length >= 20) {{
                counter.classList.add('valid');
                counter.classList.remove('warning');
            }}
        }}
        
        document.getElementById('input-text').addEventListener('input', updateCharCounter);
        
        function setOperation(op) {{
            currentOperation = op;
            const cards = document.querySelectorAll('.feature-card');
            cards.forEach(card => card.classList.remove('active'));
            event.target.closest('.feature-card').classList.add('active');
        }}
        
        async function processText() {{
            const text = document.getElementById('input-text').value;
            if (!text.trim()) {{
                alert('দয়া করে কিছু টেক্সট লিখুন');
                return;
            }}
            
            if (text.length < 20) {{
                alert('কমপক্ষে ২০ অক্ষরের টেক্সট দিন');
                return;
            }}
            
            const outputDiv = document.getElementById('output-content');
            const processBtn = document.getElementById('process-btn');
            const originalText = processBtn.innerHTML;
            
            outputDiv.innerHTML = '<div class="loader"></div> AI প্রসেসিং হচ্ছে...';
            processBtn.innerHTML = '<div class="loader"></div> প্রসেসিং...';
            processBtn.disabled = true;
            
            try {{
                let response, data;
                
                if (currentOperation === 'summarize') {{
                    response = await fetch('/bangla/super-summarize', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text, operation: 'summarize', length_ratio: 0.3 }})
                    }});
                    data = await response.json();
                    
                    if (data.status === 'success') {{
                        outputDiv.innerHTML = `
                            <div style="background: #e3f2fd; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>📊 পরিসংখ্যান:</strong><br>
                                📝 অক্ষর: ${{data.original_length}} | 📖 শব্দ: ${{data.word_count}} | 📜 বাক্য: ${{data.sentence_count}}<br>
                                🎯 কম্প্রেশন: ${{data.compression_rate}}
                            </div>
                            <div style="background: #d4edda; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>✨ স্মার্ট সারাংশ:</strong><br>
                                ${{data.smart_summary}}
                            </div>
                            <div style="background: #fff3cd; padding: 12px; border-radius: 10px;">
                                <strong>🔑 মূল ধারণা:</strong><br>
                                ${{data.key_concepts.join(' • ')}}
                            </div>
                        `;
                    }} else {{
                        outputDiv.innerHTML = `<div style="background: #f8d7da; padding: 15px; border-radius: 10px;">❌ ${{data.error}}</div>`;
                    }}
                }} 
                else if (currentOperation === 'analysis') {{
                    response = await fetch('/bangla/complete-analysis', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text, operation: 'analyze' }})
                    }});
                    data = await response.json();
                    
                    if (data.status === 'success') {{
                        outputDiv.innerHTML = `
                            <div style="background: linear-gradient(135deg, #667eea20, #764ba220); padding: 15px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>📊 মৌলিক তথ্য:</strong><br>
                                অক্ষর: ${{data.basic_stats.characters}} | বাংলা অক্ষর: ${{data.basic_stats.bangla_chars}}<br>
                                শব্দ: ${{data.basic_stats.words}} | বাক্য: ${{data.basic_stats.sentences}}
                            </div>
                            <div style="background: #e3f2fd; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>😊 সেন্টিমেন্ট:</strong><br>
                                ${{data.semantic_analysis.sentiment.emoji}} ${{data.semantic_analysis.sentiment.sentiment}}
                                (পজিটিভ: ${{data.semantic_analysis.sentiment.positive}}, নেগেটিভ: ${{data.semantic_analysis.sentiment.negative}})
                            </div>
                            <div style="background: #d4edda; padding: 12px; border-radius: 10px;">
                                <strong>🔑 কীওয়ার্ড:</strong><br>
                                ${{data.semantic_analysis.keywords.join(' • ')}}<br><br>
                                <strong>🏷️ মূল বিষয়:</strong> ${{data.semantic_analysis.main_topic}}
                            </div>
                        `;
                    }}
                }}
                else if (currentOperation === 'sentiment') {{
                    response = await fetch('/bangla/complete-analysis', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text, operation: 'analyze' }})
                    }});
                    data = await response.json();
                    
                    if (data.status === 'success') {{
                        const sentiment = data.semantic_analysis.sentiment;
                        outputDiv.innerHTML = `
                            <div style="text-align: center; padding: 20px;">
                                <div style="font-size: 60px;">${{sentiment.emoji}}</div>
                                <div style="font-size: 28px; font-weight: bold; margin: 15px 0;">${{sentiment.sentiment}}</div>
                                <div style="background: #e3f2fd; padding: 12px; border-radius: 10px; max-width: 300px; margin: 0 auto;">
                                    পজিটিভ: ${{'❤️'.repeat(Math.min(5, sentiment.positive))}}<br>
                                    নেগেটিভ: ${{'💔'.repeat(Math.min(5, sentiment.negative))}}<br>
                                    আত্মবিশ্বাস: ${{(sentiment.score * 100).toFixed(1)}}%
                                </div>
                            </div>
                        `;
                    }}
                }}
                else if (currentOperation === 'grammar') {{
                    response = await fetch('/bangla/grammar-correction', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text, operation: 'grammar' }})
                    }});
                    data = await response.json();
                    
                    if (data.status === 'success') {{
                        if (data.has_errors) {{
                            outputDiv.innerHTML = `
                                <div style="background: #f8d7da; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                    <strong>⚠️ ভুল পাওয়া গেছে:</strong><br>
                                    ${{data.corrections.join('<br>')}}
                                </div>
                                <div style="background: #fff3cd; padding: 12px; border-radius: 10px;">
                                    <strong>💡 সাজেশন:</strong><br>
                                    ${{data.suggestions.join('<br>')}}
                                </div>
                            `;
                        }} else {{
                            outputDiv.innerHTML = `<div style="background: #d4edda; padding: 20px; text-align: center; border-radius: 10px;">✅ আপনার টেক্সটে কোনো গ্রামার ভুল নেই!</div>`;
                        }}
                    }}
                }}
                else if (currentOperation === 'transform') {{
                    response = await fetch('/bangla/text-transform', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text, operation: 'transform' }})
                    }});
                    data = await response.json();
                    
                    if (data.status === 'success') {{
                        outputDiv.innerHTML = `
                            <div style="background: #e3f2fd; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>📝 মূল টেক্সট:</strong><br>
                                ${{data.original}}
                            </div>
                            <div style="background: #f0f0f0; padding: 12px; border-radius: 10px; margin-bottom: 12px;">
                                <strong>🔄 রিভার্স:</strong><br>
                                ${{data.transforms.reverse}}
                            </div>
                            <div style="background: #d4edda; padding: 12px; border-radius: 10px;">
                                <strong>📊 পরিসংখ্যান:</strong><br>
                                শব্দ: ${{data.transforms.word_count}} | অক্ষর: ${{data.transforms.char_count}}<br>
                                বাংলা অক্ষর: ${{data.transforms.bangla_char_count}}
                            </div>
                        `;
                    }}
                }}
                else if (currentOperation === 'idiom') {{
                    const idiomWord = text.trim().split(' ')[0];
                    response = await fetch(`/bangla/idiom-search/${{encodeURIComponent(idiomWord)}}`);
                    data = await response.json();
                    
                    if (data.found) {{
                        outputDiv.innerHTML = `
                            <div style="background: #d4edda; padding: 20px; border-radius: 10px; text-align: center;">
                                <strong>📖 ইডিয়ম:</strong> ${{data.idiom}}<br><br>
                                <strong>📝 অর্থ:</strong> ${{data.meaning}}
                            </div>
                        `;
                    }} else {{
                        outputDiv.innerHTML = `
                            <div style="background: #fff3cd; padding: 15px; border-radius: 10px;">
                                <strong>⚠️ "${{data.idiom}}" খুঁজে পাওয়া যায়নি</strong><br><br>
                                <strong>💡 সম্ভাব্য ইডিয়ম:</strong><br>
                                ${{data.suggestions.join(', ')}}
                            </div>
                        `;
                    }}
                }}
            }} catch (error) {{
                outputDiv.innerHTML = `<div style="background: #f8d7da; padding: 15px; border-radius: 10px; color: #dc3545;">❌ এরর: ${{error.message}}</div>`;
            }} finally {{
                processBtn.innerHTML = originalText;
                processBtn.disabled = false;
            }}
        }}
        
        function clearAll() {{
            document.getElementById('input-text').value = '';
            document.getElementById('output-content').innerHTML = '<i class="fas fa-brain" style="margin-right: 10px; color: #2c5364;"></i> ফলাফল এখানে দেখাবে...';
            updateCharCounter();
        }}
        
        function copyOutput() {{
            const output = document.getElementById('output-content').innerText;
            if (output && !output.includes('ফলাফল এখানে দেখাবে')) {{
                navigator.clipboard.writeText(output);
                alert('আউটপুট কপি করা হয়েছে!');
            }} else {{
                alert('কপি করার মতো কিছু নেই');
            }}
        }}
        
        function loadExample() {{
            const example = "বাংলাদেশ একটি ছোট কিন্তু জনবহুল দেশ। এটি দক্ষিণ এশিয়ায় অবস্থিত। ঢাকা এর রাজধানী। এখানে অনেক প্রাকৃতিক সৌন্দর্য রয়েছে। সুন্দরবন বিশ্বের সবচেয়ে বড় ম্যানগ্রোভ বন। কক্সবাজার বিশ্বের দীর্ঘতম সমুদ্র সৈকত। বাংলাদেশের অর্থনীতি দ্রুত বাড়ছে। পোশাক শিল্প এখানকার প্রধান রপ্তানি খাত। তথ্য প্রযুক্তি খাতেও বাংলাদেশ এগিয়ে যাচ্ছে। বাংলাদেশের মানুষ খুব আতিথেয়তাপ্রিয়। এখানে ছয়টি ঋতু। বাংলা নববর্ষ খুব উৎসাহের সাথে পালিত হয়।";
            document.getElementById('input-text').value = example;
            updateCharCounter();
        }}
        
        updateCharCounter();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "BanglaDoc Ultra",
        "version": "3.0",
        "bangla_date": get_bangla_date_full()['full_bangla_datetime'],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║     🚀 BanglaDoc Ultra - বিশ্বস্তরীয় বাংলা এআই প্রসেসর v3.0        ║
    ║                                                                       ║
    ║     📍 Server: http://127.0.0.1:8000                                 ║
    ║     📖 API Docs: http://127.0.0.1:8000/docs                          ║
    ║                                                                       ║
    ║     ✨ আলট্রা ফিচারসমূহ:                                              ║
    ║     • বাংলা তারিখ ও সময় সম্পূর্ণ দেখায়                              ║
    ║     • ৫০-৫০ স্প্লিট লেআউট (ইনপুট ও আউটপুট সমান)                     ║
    ║     • ১০০% পেজ উচ্চতা ব্যবহার                                        ║
    ║     • সুপার সামারাইজেশন                                              ║
    ║     • সম্পূর্ণ টেক্সট বিশ্লেষণ                                       ║
    ║     • সেন্টিমেন্ট অ্যানালাইসিস                                       ║
    ║     • গ্রামার করেকশন                                                 ║
    ║     • টেক্সট ট্রান্সফর্মেশন                                          ║
    ║     • ইডিয়ম খোঁজা                                                   ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)