import streamlit as st
import PyPDF2
import pdfplumber
import requests
import json
import re
from collections import Counter
import random
from datetime import datetime, timedelta
import time
import base64

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Neon English AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS - Neon Tema
def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Audiowide&family=Rajdhani:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0A0A0A 0%, #1a1a2e 50%, #16213e 100%);
        color: #00FFFF;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0A0A0A 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .neon-title {
        font-family: 'Audiowide', cursive;
        font-size: 3.5rem;
        background: linear-gradient(45deg, #00FFFF, #FF00FF, #00FF00);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        text-shadow: 0 0 30px rgba(0, 255, 255, 0.5);
        margin-bottom: 1rem;
    }
    
    .neon-subtitle {
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.2rem;
        color: rgba(0, 255, 255, 0.8);
        text-align: center;
        letter-spacing: 3px;
        margin-bottom: 2rem;
    }
    
    .game-card {
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .game-card:hover {
        box-shadow: 0 0 30px rgba(0, 255, 255, 0.4);
        transform: translateY(-5px);
    }
    
    .neon-button {
        background: linear-gradient(45deg, #00FFFF, #FF00FF);
        color: #0A0A0A;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .neon-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(255, 0, 255, 0.4);
    }
    
    .word-card {
        background: rgba(0, 255, 255, 0.1);
        border: 1px solid rgba(0, 255, 255, 0.3);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .word-card:hover {
        background: rgba(0, 255, 255, 0.2);
        transform: scale(1.05);
    }
    
    .correct-answer {
        background: rgba(0, 255, 0, 0.2) !important;
        border-color: #00FF00 !important;
    }
    
    .wrong-answer {
        background: rgba(255, 0, 0, 0.2) !important;
        border-color: #FF0000 !important;
    }
    
    .progress-bar {
        background: rgba(0, 255, 255, 0.2);
        border-radius: 10px;
        height: 10px;
        margin: 10px 0;
    }
    
    .progress-fill {
        background: linear-gradient(45deg, #00FFFF, #FF00FF);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
    
    .timer {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        color: #FF00FF;
        text-align: center;
        text-shadow: 0 0 10px rgba(255, 0, 255, 0.5);
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border: 1px solid;
    }
    
    .user-message {
        background: rgba(0, 255, 255, 0.1);
        border-color: rgba(0, 255, 255, 0.3);
        margin-left: 20%;
    }
    
    .bot-message {
        background: rgba(255, 0, 255, 0.1);
        border-color: rgba(255, 0, 255, 0.3);
        margin-right: 20%;
    }
    </style>
    """, unsafe_allow_html=True)

# Utility fonksiyonları
class PDFProcessor:
    @staticmethod
    def extract_text_from_pdf(pdf_file):
        """PDF'den metin çıkar"""
        try:
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            st.error(f"PDF okuma hatası: {e}")
            return ""
    
    @staticmethod
    def extract_words(text):
        """Metinden İngilizce kelimeleri çıkar"""
        # Temel stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Kelimeleri çıkar ve temizle
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [word for word in words if word not in stop_words]
        
        # Benzersiz kelimeleri say
        word_counts = Counter(words)
        return dict(word_counts.most_common(100))  # En çok kullanılan 100 kelime

class Translator:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def translate_with_gemini(self, word):
        """Gemini API ile çeviri yap"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        
        prompt = f"""
        Translate the English word "{word}" to Turkish. 
        Provide ONLY the Turkish translation, no explanations.
        If it's a verb, provide the basic form.
        Example: "running" -> "koşmak"
        """
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            return f"Çeviri hatası: {str(e)}"

class GameGenerator:
    @staticmethod
    def create_flashcards(vocabulary):
        """Kelime kartları oluştur"""
        flashcards = []
        for word, meaning in vocabulary.items():
            flashcards.append({
                'english': word,
                'turkish': meaning,
                'flipped': False
            })
        return flashcards
    
    @staticmethod
    def create_fill_blank(vocabulary, num_questions=10):
        """Boşluk doldurma soruları oluştur"""
        sentences = []
        words = list(vocabulary.keys())
        
        # Basit cümle şablonları
        templates = [
            "I {} to school every day.",
            "She {} a book yesterday.",
            "They are {} in the park.",
            "We have {} this movie before.",
            "He will {} his homework tonight.",
            "The cat is {} on the chair.",
            "We should {} more water.",
            "She can {} very fast.",
            "They were {} when I arrived.",
            "I want to {} a new language."
        ]
        
        for i in range(min(num_questions, len(templates))):
            word = random.choice(words)
            template = random.choice(templates)
            sentence = template.format("_____")
            answer = word
            
            sentences.append({
                'sentence': sentence,
                'answer': answer,
                'user_answer': '',
                'correct': None
            })
        
        return sentences
    
    @staticmethod
    def create_matching_game(vocabulary, num_pairs=8):
        """Eşleştirme oyunu oluştur"""
        words = list(vocabulary.items())
        random.shuffle(words)
        pairs = words[:num_pairs]
        
        english_words = [pair[0] for pair in pairs]
        turkish_meanings = [pair[1] for pair in pairs]
        random.shuffle(turkish_meanings)
        
        return {
            'english_words': english_words,
            'turkish_meanings': turkish_meanings,
            'correct_pairs': dict(pairs),
            'user_selections': {},
            'completed_pairs': set()
        }

class ChatBot:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def ask_gemini(self, prompt, vocabulary=None):
        """Gemini API ile sohbet"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        context = ""
        if vocabulary:
            context = f"Current vocabulary: {', '.join(vocabulary.keys())}. "
        
        full_prompt = f"{context}You are an English teaching assistant. Answer in Turkish unless asked otherwise. Keep responses concise and helpful. User question: {prompt}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"🤖 Üzgünüm, bir hata oluştu: {str(e)}"

# Ana uygulama
def main():
    inject_custom_css()
    
    # Başlık
    st.markdown('<div class="neon-title"> ENGLISH LEARNİNG </div>', unsafe_allow_html=True)
    st.markdown('<div class="neon-subtitle">AI-Powered English Learning Assistant</div>', unsafe_allow_html=True)
    
    # Sidebar - Giriş ve API
    with st.sidebar:
        st.markdown("### 🔑 API Ayarları")
        api_key = st.text_input("Gemini API Key", type="password", 
                               help="Google AI Studio'dan alınan API key")
        
        st.markdown("### 👤 Kullanıcı")
        username = st.text_input("Kullanıcı Adı", value="English Learner")
        
        st.markdown("### 📚 Öğrenme İlerlemesi")
        if 'learned_words' not in st.session_state:
            st.session_state.learned_words = set()
        
        st.write(f"Öğrenilen kelimeler: {len(st.session_state.learned_words)}")
        
        # Günlük meydan okuma
        if 'daily_challenge' not in st.session_state:
            st.session_state.daily_challenge = None
            st.session_state.challenge_date = None
        
        if st.button("🔄 Günlük Meydan Okuma", use_container_width=True):
            if st.session_state.get('vocabulary'):
                words = list(st.session_state.vocabulary.keys())[:10]
                st.session_state.daily_challenge = words
                st.session_state.challenge_date = datetime.now().date()
                st.success("Yeni günlük meydan okuma oluşturuldu!")
    
    # Ana içerik alanı
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📁 PDF Yükle", "🎴 Kartlar", "✍️ Boşluk Doldur", "🎯 Eşleştirme", 
        "🕹️ Hızlı Test", "💬 Asistan"
    ])
    
    # Tab 1: PDF Yükleme
    with tab1:
        st.markdown("### 📄 PDF Dosyası Yükle")
        uploaded_file = st.file_uploader("İngilizce PDF dosyası seçin", type="pdf")
        
        if uploaded_file is not None:
            with st.spinner("PDF analiz ediliyor..."):
                # PDF'den metin çıkar
                text = PDFProcessor.extract_text_from_pdf(uploaded_file)
                
                if text:
                    # Kelimeleri çıkar
                    word_counts = PDFProcessor.extract_words(text)
                    
                    if word_counts:
                        # Çevirileri yap
                        if api_key:
                            translator = Translator(api_key)
                            vocabulary = {}
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, (word, count) in enumerate(word_counts.items()):
                                status_text.text(f"Çeviriliyor: {word}...")
                                translation = translator.translate_with_gemini(word)
                                vocabulary[word] = translation
                                progress_bar.progress((i + 1) / len(word_counts))
                            
                            status_text.text("✅ Çeviri tamamlandı!")
                            st.session_state.vocabulary = vocabulary
                            
                            # Sonuçları göster
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📊 Kelime İstatistikleri")
                                st.write(f"Toplam kelime: {len(text.split())}")
                                st.write(f"Benzersiz kelime: {len(word_counts)}")
                                st.write(f"Çevrilen kelime: {len(vocabulary)}")
                            
                            with col2:
                                st.markdown("#### 🎯 En Sık Kullanılan Kelimeler")
                                for word, count in list(word_counts.items())[:10]:
                                    st.write(f"**{word}**: {count} kez → {vocabulary.get(word, 'Çeviri bekleniyor')}")
                            
                        else:
                            st.error("Lütfen API key girin")
                    else:
                        st.error("PDF'den kelime çıkarılamadı")
                else:
                    st.error("PDF okunamadı veya metin içermiyor")
    
    # Tab 2: Flashcard Oyunu
    with tab2:
        st.markdown("### 🎴 Kelime Kartları")
        
        if 'vocabulary' in st.session_state and st.session_state.vocabulary:
            if 'flashcards' not in st.session_state:
                st.session_state.flashcards = GameGenerator.create_flashcards(st.session_state.vocabulary)
                st.session_state.current_card = 0
                st.session_state.flipped = False
            
            if st.session_state.flashcards:
                card = st.session_state.flashcards[st.session_state.current_card]
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    st.markdown('<div class="game-card">', unsafe_allow_html=True)
                    
                    if not st.session_state.flipped:
                        st.markdown(f"<h2 style='text-align: center; color: #00FFFF;'>{card['english']}</h2>", 
                                  unsafe_allow_html=True)
                        st.markdown("<p style='text-align: center; color: #666;'>Türkçe anlamı için tıkla</p>", 
                                  unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h2 style='text-align: center; color: #FF00FF;'>{card['turkish']}</h2>", 
                                  unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: #00FFFF;'>{card['english']}</p>", 
                                  unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Kontrol butonları
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if st.button("🔄 Çevir", use_container_width=True):
                            st.session_state.flipped = not st.session_state.flipped
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("✅ Öğrendim", use_container_width=True):
                            st.session_state.learned_words.add(card['english'])
                            st.success(f"'{card['english']}' kelimesi öğrenildi!")
                    
                    with col_btn3:
                        if st.button("➡️ Sonraki", use_container_width=True):
                            st.session_state.current_card = (st.session_state.current_card + 1) % len(st.session_state.flashcards)
                            st.session_state.flipped = False
                            st.rerun()
                
                # İlerleme
                st.write(f"Kart {st.session_state.current_card + 1} / {len(st.session_state.flashcards)}")
                st.progress((st.session_state.current_card + 1) / len(st.session_state.flashcards))
        else:
            st.info("📚 Önce PDF yükleyip kelimeleri çıkarın")
    
    # Tab 3: Boşluk Doldurma
    with tab3:
        st.markdown("### ✍️ Boşluk Doldurma")
        
        if 'vocabulary' in st.session_state and st.session_state.vocabulary:
            if 'fill_blank_questions' not in st.session_state:
                st.session_state.fill_blank_questions = GameGenerator.create_fill_blank(st.session_state.vocabulary)
                st.session_state.current_question = 0
                st.session_state.score = 0
            
            if st.session_state.fill_blank_questions:
                question = st.session_state.fill_blank_questions[st.session_state.current_question]
                
                st.markdown('<div class="game-card">', unsafe_allow_html=True)
                st.markdown(f"#### {question['sentence']}")
                
                user_answer = st.text_input("Cevabınız:", value=question['user_answer'], 
                                          key=f"blank_{st.session_state.current_question}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Kontrol Et", use_container_width=True):
                        if user_answer.strip().lower() == question['answer'].lower():
                            st.success("🎉 Doğru!")
                            question['correct'] = True
                            st.session_state.score += 1
                            st.session_state.learned_words.add(question['answer'])
                        else:
                            st.error(f"❌ Yanlış! Doğru cevap: **{question['answer']}**")
                            question['correct'] = False
                
                with col2:
                    if st.button("➡️ Sonraki Soru", use_container_width=True):
                        st.session_state.current_question = (st.session_state.current_question + 1) % len(st.session_state.fill_blank_questions)
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # İstatistikler
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Skor", st.session_state.score)
                with col2:
                    st.metric("Soru", f"{st.session_state.current_question + 1}/{len(st.session_state.fill_blank_questions)}")
                with col3:
                    correct_answers = sum(1 for q in st.session_state.fill_blank_questions if q.get('correct'))
                    st.metric("Doğru", f"{correct_answers}/{len(st.session_state.fill_blank_questions)}")
        else:
            st.info("📚 Önce PDF yükleyip kelimeleri çıkarın")
    
    # Tab 4: Eşleştirme Oyunu
    with tab4:
        st.markdown("### 🎯 Kelime Eşleştirme")
        
        if 'vocabulary' in st.session_state and st.session_state.vocabulary:
            if 'matching_game' not in st.session_state:
                st.session_state.matching_game = GameGenerator.create_matching_game(st.session_state.vocabulary)
                st.session_state.selected_english = None
                st.session_state.selected_turkish = None
            
            game = st.session_state.matching_game
            
            # İngilizce kelimeler
            st.markdown("#### İngilizce Kelimeler")
            cols = st.columns(4)
            for i, word in enumerate(game['english_words']):
                with cols[i % 4]:
                    if word not in game['completed_pairs']:
                        if st.button(word, key=f"eng_{word}", use_container_width=True,
                                   type="primary" if st.session_state.selected_english == word else "secondary"):
                            st.session_state.selected_english = word
            
            # Türkçe anlamlar
            st.markdown("#### Türkçe Anlamlar")
            cols = st.columns(4)
            for i, meaning in enumerate(game['turkish_meanings']):
                with cols[i % 4]:
                    if meaning not in game['user_selections'].values():
                        if st.button(meaning, key=f"tr_{meaning}", use_container_width=True,
                                   type="primary" if st.session_state.selected_turkish == meaning else "secondary"):
                            st.session_state.selected_turkish = meaning
            
            # Eşleştirme kontrolü
            if st.session_state.selected_english and st.session_state.selected_turkish:
                correct_meaning = game['correct_pairs'].get(st.session_state.selected_english)
                
                if st.session_state.selected_turkish == correct_meaning:
                    st.success(f"🎉 Doğru! {st.session_state.selected_english} = {st.session_state.selected_turkish}")
                    game['completed_pairs'].add(st.session_state.selected_english)
                    game['user_selections'][st.session_state.selected_english] = st.session_state.selected_turkish
                    st.session_state.learned_words.add(st.session_state.selected_english)
                else:
                    st.error("❌ Yanlış eşleştirme!")
                
                st.session_state.selected_english = None
                st.session_state.selected_turkish = None
                st.rerun()
            
            # İlerleme
            progress = len(game['completed_pairs']) / len(game['english_words'])
            st.write(f"Tamamlanan: {len(game['completed_pairs'])}/{len(game['english_words'])}")
            st.progress(progress)
            
            if progress == 1:
                st.balloons()
                st.success("🎊 Tüm eşleştirmeleri tamamladınız!")
                
                if st.button("🔄 Yeni Oyun", use_container_width=True):
                    st.session_state.matching_game = GameGenerator.create_matching_game(st.session_state.vocabulary)
                    st.session_state.selected_english = None
                    st.session_state.selected_turkish = None
                    st.rerun()
        else:
            st.info("📚 Önce PDF yükleyip kelimeleri çıkarın")
    
    # Tab 5: Hızlı Test
    with tab5:
        st.markdown("### 🕹️ Hızlı Kelime Testi")
        
        if 'vocabulary' in st.session_state and st.session_state.vocabulary:
            if 'quick_test' not in st.session_state:
                words = list(st.session_state.vocabulary.items())
                random.shuffle(words)
                st.session_state.quick_test = words[:5]  # 5 kelimelik test
                st.session_state.test_answers = {}
                st.session_state.test_submitted = False
            
            if st.session_state.quick_test:
                st.markdown("#### Aşağıdaki kelimelerin Türkçe anlamlarını yazın:")
                
                for i, (word, correct_meaning) in enumerate(st.session_state.quick_test):
                    user_answer = st.text_input(
                        f"{i+1}. {word}",
                        value=st.session_state.test_answers.get(word, ""),
                        key=f"test_{word}"
                    )
                    st.session_state.test_answers[word] = user_answer
                
                if st.button("✅ Testi Bitir", use_container_width=True):
                    st.session_state.test_submitted = True
                    correct_count = 0
                    
                    for word, correct_meaning in st.session_state.quick_test:
                        user_answer = st.session_state.test_answers.get(word, "").strip()
                        if user_answer.lower() == correct_meaning.lower():
                            correct_count += 1
                            st.session_state.learned_words.add(word)
                    
                    st.session_state.test_score = correct_count
                
                if st.session_state.test_submitted:
                    st.markdown("---")
                    st.markdown(f"#### 📊 Test Sonucu: {st.session_state.test_score}/5")
                    
                    if st.session_state.test_score == 5:
                        st.balloons()
                        st.success("🎉 Mükemmel! Tüm cevaplar doğru!")
                    elif st.session_state.test_score >= 3:
                        st.warning("👍 İyi iş! Biraz daha pratik yapabilirsin")
                    else:
                        st.error("📚 Daha fazla çalışma zamanı!")
                    
                    if st.button("🔄 Yeni Test", use_container_width=True):
                        del st.session_state.quick_test
                        del st.session_state.test_answers
                        del st.session_state.test_submitted
                        st.rerun()
        else:
            st.info("📚 Önce PDF yükleyip kelimeleri çıkarın")
    
    # Tab 6: AI Asistan
    with tab6:
        st.markdown("### 💬 AI İngilizce Asistanı")
        
        if not api_key:
            st.warning("Lütfen sidebar'dan API key girin")
        else:
            chatbot = ChatBot(api_key)
            
            # Sohbet geçmişi
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Sohbeti göster
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f'<div class="chat-message user-message"><strong>👤 Siz:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message bot-message"><strong>🤖 Asistan:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
            
            # Giriş alanı
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input("Sorunuz:", placeholder="Örnek: 'happy' kelimesinin anlamı nedir?")
            
            with col2:
                if st.button("Gönder", use_container_width=True):
                    if user_input.strip():
                        # Kullanıcı mesajını ekle
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': user_input,
                            'timestamp': datetime.now()
                        })
                        
                        # AI yanıtı al
                        with st.spinner("Asistan düşünüyor..."):
                            vocabulary = st.session_state.get('vocabulary', {})
                            response = chatbot.ask_gemini(user_input, vocabulary)
                            
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response,
                                'timestamp': datetime.now()
                            })
                        
                        st.rerun()
            
            # Hızlı soru butonları
            st.markdown("#### 🚀 Hızlı Sorular")
            col1, col2, col3 = st.columns(3)
            
            quick_questions = [
                "Öğrendiğim kelimeleri göster",
                "Bana rastgele bir kelime ve cümle söyle",
                "İngilizce öğrenme tavsiyeleri ver"
            ]
            
            for i, question in enumerate(quick_questions):
                with [col1, col2, col3][i]:
                    if st.button(question, use_container_width=True):
                        vocabulary = st.session_state.get('vocabulary', {})
                        response = chatbot.ask_gemini(question, vocabulary)
                        
                        st.session_state.chat_history.extend([
                            {'role': 'user', 'content': question, 'timestamp': datetime.now()},
                            {'role': 'assistant', 'content': response, 'timestamp': datetime.now()}
                        ])
                        st.rerun()

if __name__ == "__main__":
    main()
