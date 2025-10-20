import re
import os
import json
import csv
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import genanki
import random
from io import BytesIO
import tempfile
import zipfile
from qa_extractor import extract_qa_from_markdown
from anki_deck_creator import create_anki_deck # Importa la funzione

# Configurazione della pagina
st.set_page_config(
    page_title="Flashcard Creator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    /* Tema generale con migliore contrasto */
    .stApp {
        background-color: #ffffff;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #2c3e50 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50 !important;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .stats-container {
        background-color: #f8f9fa;
        color: #2c3e50 !important;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stats-container h3 {
        color: #2c3e50 !important;
        margin-bottom: 1rem;
    }
    
    .stats-container p {
        color: #34495e !important;
        margin: 0.5rem 0;
    }
    
    .preview-card {
        background-color: #ffffff;
        color: #2c3e50 !important;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin: 1rem 0;
        border-left: 4px solid #e74c3c;
        border: 1px solid #e9ecef;
    }
    
    .preview-card h4 {
        color: #e74c3c !important;
        margin-bottom: 1rem;
    }
    
    .preview-card div {
        color: #2c3e50 !important;
        line-height: 1.6;
    }
    
    .answer-card {
        background-color: #f8f9fa;
        color: #2c3e50 !important;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        margin: 1rem 0;
        border-left: 4px solid #27ae60;
        border: 1px solid #e9ecef;
    }
    
    .answer-card h4 {
        color: #27ae60 !important;
        margin-bottom: 1rem;
    }
    
    .answer-card div {
        color: #2c3e50 !important;
        line-height: 1.6;
    }
    
    .file-upload-area {
        border: 2px dashed #bdc3c7;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        color: #2c3e50 !important;
    }
    
    /* Miglioramenti per sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Colori per testi vari */
    .stMarkdown, .stText {
        color: #2c3e50 !important;
    }
    
    /* Contenitori principali */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        background-color: #ffffff;
    }
    
    /* Footer styling */
    .footer-info {
        background-color: #f8f9fa;
        color: #7f8c8d !important;
        padding: 20px;
        border-radius: 10px;
        margin-top: 2rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    
    .footer-info p {
        color: #7f8c8d !important;
        margin: 0.5rem 0;
    }
    
    .footer-info small {
        color: #95a5a6 !important;
    }
</style>
""", unsafe_allow_html=True)
# Le funzioni transform_markdown_formatting, transform_math_formulas,
# escape_anki_html, e extract_qa_from_markdown sono state spostate in qa_extractor.py
# e extract_qa_from_markdown viene importata da lì.

# La funzione create_anki_deck è stata spostata in anki_deck_creator.py
# e viene importata da lì.

# Inizializzazione dello stato della sessione
if 'qa_dict' not in st.session_state:
    st.session_state.qa_dict = {}
if 'qa_dict_per_file' not in st.session_state:
    st.session_state.qa_dict_per_file = {}
if 'current_preview_index' not in st.session_state:
    st.session_state.current_preview_index = 0
if 'theme' not in st.session_state:
    st.session_state.theme = {
        "question_bg": "#ffffff",
        "question_fg": "#2c3e50",
        "answer_bg": "#f8f9fa",
        "answer_fg": "#2c3e50",
        "font_family": "Arial, sans-serif",
        "question_font_size": "16px",
        "answer_font_size": "14px",
        "border_radius": "8px",
        "box_shadow": "0 1px 3px rgba(0,0,0,0.1)"
    }

# Header principale
st.markdown('<h1 class="main-header">🎯 Flashcard Creator</h1>', unsafe_allow_html=True)

# Sidebar per configurazioni
with st.sidebar:
    st.header("⚙️ Configurazioni")
    
    # Tema
    st.subheader("🎨 Personalizzazione Tema")
    
    question_bg = st.color_picker("Colore sfondo domanda", st.session_state.theme["question_bg"])
    question_fg = st.color_picker("Colore testo domanda", st.session_state.theme["question_fg"])
    answer_bg = st.color_picker("Colore sfondo risposta", st.session_state.theme["answer_bg"])
    answer_fg = st.color_picker("Colore testo risposta", st.session_state.theme["answer_fg"])
    
    font_family = st.selectbox(
        "Font",
        ["Arial, sans-serif", "Helvetica, sans-serif", "Times New Roman, serif", "Courier New, monospace"],
        index=0
    )
    
    question_font_size = st.slider("Dimensione font domanda", 12, 24, 16)
    answer_font_size = st.slider("Dimensione font risposta", 12, 24, 14)
    
    # Aggiorna tema
    st.session_state.theme.update({
        "question_bg": question_bg,
        "question_fg": question_fg,
        "answer_bg": answer_bg,
        "answer_fg": answer_fg,
        "font_family": font_family,
        "question_font_size": f"{question_font_size}px",
        "answer_font_size": f"{answer_font_size}px"
    })
    
    if st.button("🔄 Reset Tema"):
        st.session_state.theme = {
            "question_bg": "#ffffff",
            "question_fg": "#2c3e50",
            "answer_bg": "#f8f9fa",
            "answer_fg": "#2c3e50",
            "font_family": "Arial, sans-serif",
            "question_font_size": "16px",
            "answer_font_size": "14px",
            "border_radius": "8px",
            "box_shadow": "0 1px 3px rgba(0,0,0,0.1)"
        }
        st.rerun()

# Layout principale
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<h2 class="section-header">📁 Caricamento File</h2>', unsafe_allow_html=True)
    
    # Upload dei file
    uploaded_files = st.file_uploader(
        "Carica file Markdown (.md)",
        type=['md'],
        accept_multiple_files=True,
        help="Seleziona uno o più file Markdown contenenti domande e risposte"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file caricati")
        
        # Mostra i file caricati
        for file in uploaded_files:
            st.write(f"📄 {file.name}")
        
        if st.button("🔄 Elabora File", type="primary"):
            with st.spinner("Elaborazione file in corso..."):
                st.session_state.qa_dict = {}
                st.session_state.qa_dict_per_file = {}
                
                for file in uploaded_files:
                    content = file.read().decode('utf-8')
                    qa_dict_temp = extract_qa_from_markdown(content)
                    
                    if qa_dict_temp:
                        st.session_state.qa_dict_per_file[file.name] = qa_dict_temp
                        st.session_state.qa_dict.update(qa_dict_temp)
                
                st.session_state.current_preview_index = 0
                
                if st.session_state.qa_dict:
                    st.success(f"✅ Elaborate {len(st.session_state.qa_dict)} domande e risposte totali")
                else:
                    st.warning("⚠️ Nessuna domanda e risposta trovata nei file")

with col2:
    st.markdown('<h2 class="section-header">📊 Statistiche</h2>', unsafe_allow_html=True)
    
    if st.session_state.qa_dict:
        total_questions = len(st.session_state.qa_dict)
        empty_answers = sum(1 for answer in st.session_state.qa_dict.values() if not answer)
        files_count = len(st.session_state.qa_dict_per_file)
        
        st.markdown(f"""
        <div class="stats-container">
            <h3>📈 Statistiche Attuali</h3>
            <p><strong>📝 Domande totali:</strong> {total_questions}</p>
            <p><strong>✅ Risposte complete:</strong> {total_questions - empty_answers}</p>
            <p><strong>❌ Risposte mancanti:</strong> {empty_answers}</p>
            <p><strong>📁 File elaborati:</strong> {files_count}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📊 Carica alcuni file per vedere le statistiche")

# Sezione anteprima e modifica
if st.session_state.qa_dict:
    st.markdown('<h2 class="section-header">👀 Anteprima e Modifica</h2>', unsafe_allow_html=True)
    
    # Controlli di navigazione
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Precedente"):
            st.session_state.current_preview_index = max(0, st.session_state.current_preview_index - 1)
    
    with col2:
        total = len(st.session_state.qa_dict)
        st.markdown(f"<div style='text-align: center; font-size: 1.2em; font-weight: bold;'>{st.session_state.current_preview_index + 1} / {total}</div>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Successiva ➡️"):
            st.session_state.current_preview_index = min(len(st.session_state.qa_dict) - 1, st.session_state.current_preview_index + 1)
    
    # Mostra domanda e risposta corrente
    if st.session_state.qa_dict:
        items = list(st.session_state.qa_dict.items())
        current_question, current_answer = items[st.session_state.current_preview_index]
        
        # Anteprima domanda
        st.markdown(f"""
        <div class="preview-card">
            <h4>❓ Domanda:</h4>
            <div>{current_question}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Anteprima risposta
        st.markdown(f"""
        <div class="answer-card">
            <h4>💡 Risposta:</h4>
            <div>{current_answer}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Editor per modifiche
        with st.expander("✏️ Modifica questa domanda/risposta"):
            new_question = st.text_area("Modifica domanda:", value=current_question, height=100)
            new_answer = st.text_area("Modifica risposta:", value=current_answer, height=150)
            
            if st.button("💾 Salva Modifiche"):
                if new_question.strip():
                    # Rimuovi la vecchia domanda
                    del st.session_state.qa_dict[current_question]
                    # Aggiungi la nuova
                    st.session_state.qa_dict[new_question] = new_answer
                    st.success("✅ Modifiche salvate!")
                    st.rerun()
                else:
                    st.error("❌ La domanda non può essere vuota")

# Sezione esportazione
if st.session_state.qa_dict:
    st.markdown('<h2 class="section-header">📤 Esportazione</h2>', unsafe_allow_html=True)
    
    # Nome del mazzo
    deck_name = st.text_input("Nome del mazzo Anki:", value="Il Mio Mazzo Flashcard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 Esporta Anki (.apkg)", type="primary"):
            try:
                with st.spinner("Creazione mazzo Anki..."):
                    anki_package = create_anki_deck(
                        st.session_state.qa_dict,
                        deck_name=deck_name,
                        theme=st.session_state.theme,
                        qa_dict_per_file=st.session_state.qa_dict_per_file
                    )
                    
                    # Salva direttamente in un buffer senza file temporaneo
                    buffer = BytesIO()
                    
                    # Crea un file temporaneo con un nome unico
                    import uuid
                    temp_filename = f"temp_anki_{uuid.uuid4().hex}.apkg"
                    temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
                    
                    try:
                        # Scrivi il file temporaneo
                        anki_package.write_to_file(temp_path)
                        
                        # Leggi il contenuto e copialo nel buffer
                        with open(temp_path, 'rb') as f:
                            buffer.write(f.read())
                        
                        # Elimina immediatamente il file temporaneo
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                    except Exception as temp_error:
                        # Se c'è un errore, assicurati che il file temporaneo sia eliminato
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                        raise temp_error
                    
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Scarica Mazzo Anki",
                        data=buffer.getvalue(),
                        file_name=f"{deck_name}.apkg",
                        mime="application/octet-stream"
                    )
                    
                    st.success("✅ Mazzo Anki creato! Clicca per scaricare.")
            except Exception as e:
                st.error(f"❌ Errore nella creazione del mazzo: {str(e)}")
    
    with col2:
        if st.button("📊 Esporta CSV"):
            try:
                # Crea DataFrame
                df = pd.DataFrame(list(st.session_state.qa_dict.items()), columns=['Domanda', 'Risposta'])
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Scarica CSV",
                    data=csv,
                    file_name=f"{deck_name}.csv",
                    mime="text/csv"
                )
                st.success("✅ CSV pronto per il download!")
            except Exception as e:
                st.error(f"❌ Errore nell'esportazione CSV: {str(e)}")
    
    with col3:
        if st.button("🔧 Esporta XML"):
            try:
                root = ET.Element("flashcards")
                for domanda, risposta in st.session_state.qa_dict.items():
                    card = ET.SubElement(root, "card")
                    q = ET.SubElement(card, "question")
                    q.text = domanda
                    a = ET.SubElement(card, "answer")
                    a.text = risposta
                
                xml_str = ET.tostring(root, encoding='unicode')
                
                st.download_button(
                    label="📥 Scarica XML",
                    data=xml_str,
                    file_name=f"{deck_name}.xml",
                    mime="text/xml"
                )
                st.success("✅ XML pronto per il download!")
            except Exception as e:
                st.error(f"❌ Errore nell'esportazione XML: {str(e)}")
    
    with col4:
        if st.button("🗂️ Esporta JSON"):
            try:
                json_str = json.dumps(st.session_state.qa_dict, ensure_ascii=False, indent=2)
                
                st.download_button(
                    label="📥 Scarica JSON",
                    data=json_str,
                    file_name=f"{deck_name}.json",
                    mime="application/json"
                )
                st.success("✅ JSON pronto per il download!")
            except Exception as e:
                st.error(f"❌ Errore nell'esportazione JSON: {str(e)}")

# Footer informativo
st.markdown("---")
st.markdown("""
<div class='footer-info'>
    <p>🎯 <strong>Flashcard Creator</strong> - Versione Streamlit</p>
    <p>Converti i tuoi file Markdown in flashcard Anki con formattazione avanzata e supporto per formule matematiche</p>
    <p><small>Supporta formattazione Markdown, liste, codice e formule LaTeX ($formula$)</small></p>
</div>
""", unsafe_allow_html=True)