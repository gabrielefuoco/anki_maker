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
def transform_markdown_formatting(text):
    """Trasforma la formattazione markdown in HTML compatibile con Anki.
    
    Args:
        text: Testo da trasformare
        
    Returns:
        Testo con la formattazione convertita in HTML
    """
    if not text:
        return text
        
    # Converti grassetto (**testo** -> <b>testo</b>)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Converti corsivo (*testo* -> <i>testo</i>)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    
    # Converti testo barrato (~~testo~~ -> <s>testo</s>)
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    # Converti codice inline (`testo` -> <code>testo</code>)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Converti sottolineato (__testo__ -> <u>testo</u>)
    text = re.sub(r'__(.+?)__', r'<u>\1</u>', text)
    
    # Converti testo evidenziato (==testo== -> <mark>testo</mark>)
    text = re.sub(r'==(.+?)==', r'<mark>\1</mark>', text)
    
    # Converti liste non ordinate
    lines = text.split('\n')
    in_list = False
    for i, line in enumerate(lines):
        if line.strip().startswith('- '):
            if not in_list:
                lines[i] = '<ul>' + line
                in_list = True
        elif in_list and not line.strip().startswith('- '):
            lines[i-1] = lines[i-1] + '</ul>'
            in_list = False
    
    if in_list:
        lines[-1] = lines[-1] + '</ul>'
    
    # Converti liste ordinate
    in_list = False
    for i, line in enumerate(lines):
        if re.match(r'^\d+\. ', line.strip()):
            if not in_list:
                lines[i] = '<ol>' + line
                in_list = True
        elif in_list and not re.match(r'^\d+\. ', line.strip()):
            lines[i-1] = lines[i-1] + '</ol>'
            in_list = False
    
    if in_list:
        lines[-1] = lines[-1] + '</ol>'
    
    # Converti elementi delle liste
    for i, line in enumerate(lines):
        if line.strip().startswith('- '):
            lines[i] = re.sub(r'^- ', '<li>', line) + '</li>'
        elif re.match(r'^\d+\. ', line.strip()):
            lines[i] = re.sub(r'^\d+\. ', '<li>', line) + '</li>'
    
    text = '\n'.join(lines)
    return text

def transform_math_formulas(text):
    """Trasforma le formule matematiche da $...$ a \\(...\\).
    
    Args:
        text: Testo da trasformare
        
    Returns:
        Testo con le formule trasformate
    """
    if not text:
        return text
    
    # Prima converti la formattazione markdown per identificare i blocchi di codice
    text_with_markdown = transform_markdown_formatting(text)
    
    # Pattern per trovare formule tra $ ma solo fuori dai blocchi di codice
    def replace_math_outside_code(text):
        # Trova tutti i blocchi di codice (inline e block)
        code_blocks = []
        
        # Trova blocchi di codice inline (`code`)
        for match in re.finditer(r'`([^`]+)`', text):
            code_blocks.append((match.start(), match.end()))
        
        # Trova blocchi di codice HTML già convertiti (<code>...</code>)
        for match in re.finditer(r'<code[^>]*>.*?</code>', text, re.DOTALL):
            code_blocks.append((match.start(), match.end()))
        
        # Trova blocchi di codice multilinea (```...```)
        for match in re.finditer(r'```.*?```', text, re.DOTALL):
            code_blocks.append((match.start(), match.end()))
        
        # Ordina i blocchi di codice per posizione
        code_blocks.sort()
        
        def is_inside_code_block(pos):
            """Verifica se una posizione è all'interno di un blocco di codice"""
            for start, end in code_blocks:
                if start <= pos < end:
                    return True
            return False
        
        def replace_formula(match):
            # Verifica se la formula è all'interno di un blocco di codice
            if is_inside_code_block(match.start()):
                return match.group(0)  # Non sostituire se è dentro un blocco di codice
            formula = match.group(1)
            return rf'\({formula}\)'
        
        # Sostituisci le formule matematiche solo se non sono in blocchi di codice
        return re.sub(r'\$([^$]+)\$', replace_formula, text)
    
    # Applica la trasformazione delle formule matematiche
    result = replace_math_outside_code(text_with_markdown)
    
    return result

def escape_anki_html(text):
    """
    Esegue l'escape dei caratteri speciali HTML che potrebbero essere interpretati come tag.
    
    Args:
        text: Testo da cui fare l'escape
        
    Returns:
        Testo con i caratteri speciali HTML escapati
    """
    if not text:
        return text
    
    # Sostituisci i < e > che non fanno parte di un tag HTML valido
    # Preserva i tag HTML validi come <b>, <i>, ecc.
    valid_tags = r'</?(?:b|i|u|s|code|mark|ul|ol|li|div|span|br|hr|p)(?:\s+[^>]*)?>'
    parts = re.split(f'({valid_tags})', text)
    
    for i in range(len(parts)):
        # Se la parte non corrisponde a un tag HTML valido
        if i % 2 == 0:  # parti alternate sono testo normale
            # Escape di < e > che non fanno parte di tag HTML validi
            parts[i] = re.sub(r'<', '&lt;', parts[i])
            parts[i] = re.sub(r'>', '&gt;', parts[i])
    
    return ''.join(parts)

def extract_qa_from_markdown(content):
    """Estrae domande e risposte dal contenuto markdown."""
    # Dividi il contenuto in blocchi usando il separatore ---
    # Modifica per rendere lo split più robusto a spazi attorno a ---
    blocks = re.split(r'\n\s*---\s*\n', content)
    
    qa_dict = {}
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Pattern per trovare le domande
        domanda_pattern = r'(?:(?:\*\*)?\s*Domanda\s*(?:\*\*)?\s*:\s*)\s*(?:\*\*)?\s*(.*?)(?=(?:(?:\*\*)?\s*(?:Risposta(?:\s+corretta)?|Domanda)\s*(?:\*\*)?\s*:\s*)|$)'
        domande = re.finditer(domanda_pattern, block, re.DOTALL | re.IGNORECASE)
        domande_list = [(m.start(), m.end(), m.group(1).strip()) for m in domande]
        
        # Pattern per trovare le risposte
        risposta_pattern = r'(?:(?:\*\*)?\s*Risposta(?:\s+corretta)?\s*(?:\*\*)?\s*:\s*)\s*(?:\*\*)?\s*(.*?)(?=(?:(?:\*\*)?\s*(?:Domanda|Risposta(?:\s+corretta)?)\s*(?:\*\*)?\s*:\s*)|$)'
        risposte = re.finditer(risposta_pattern, block, re.DOTALL | re.IGNORECASE)
        risposte_list = [(m.start(), m.end(), m.group(1).strip()) for m in risposte]
        
        # Associa ogni domanda con la risposta che la segue
        for i, (d_start, d_end, domanda) in enumerate(domande_list):
            next_risposta = None
            for r_start, r_end, risposta in risposte_list:
                if r_start > d_start:
                    next_domanda_exists = any(nd_start < r_start for nd_start, _, _ in domande_list[i+1:] if i+1 < len(domande_list))
                    if not next_domanda_exists:
                        next_risposta = risposta
                        break
            
            if next_risposta:
                # Pulisci asterischi
                domanda = re.sub(r'^(\*\*)+\s*', '', domanda).strip()
                domanda = re.sub(r'\s*(\*\*)+$', '', domanda).strip()
                next_risposta = re.sub(r'^(\*\*)+\s*', '', next_risposta).strip()
                next_risposta = re.sub(r'\s*(\*\*)+$', '', next_risposta).strip()
                
                # Applica trasformazioni
                domanda_formattata = transform_math_formulas(domanda)
                risposta_formattata = transform_math_formulas(next_risposta)
                
                # Escape HTML
                domanda_formattata = escape_anki_html(domanda_formattata)
                risposta_formattata = escape_anki_html(risposta_formattata)
                
                qa_dict[domanda_formattata] = risposta_formattata
    
    return qa_dict

def create_anki_deck(qa_dict, deck_name="Flashcard Domande e Risposte", theme=None, qa_dict_per_file=None):
    """Crea un mazzo Anki dalle domande e risposte."""
    if theme is None:
        theme = {
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
    
    # Creiamo un modello per le nostre note
    model_id = random.randrange(1 << 30, 1 << 31)
    my_model = genanki.Model(
        model_id,
        'Modello Domanda-Risposta',
        fields=[
            {'name': 'Domanda'},
            {'name': 'Risposta'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': f'''
                <script type="text/x-mathjax-config">
                    MathJax.Hub.Config({{
                        messageStyle: "none",
                        tex2jax: {{inlineMath: [['\\\\(','\\\\)']]}},
                        displayAlign: "center",
                        "HTML-CSS": {{ scale: 100 }}
                    }});
                </script>
                <script type="text/javascript">
                    if (typeof MathJax === "undefined") {{
                        var script = document.createElement("script");
                        script.type = "text/javascript";
                        script.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS_HTML";
                        document.getElementsByTagName("head")[0].appendChild(script);
                    }}
                </script>
                <div style="max-width: 600px; margin: 0 auto; font-family: {theme['font_family']}; font-size: {theme['question_font_size']}; 
                     padding: 20px; background-color: {theme['question_bg']}; color: {theme['question_fg']}; 
                     border-radius: {theme['border_radius']}; box-shadow: {theme['box_shadow']}; text-align: left;">
                    {{{{Domanda}}}}
                </div>
                ''',
                'afmt': f'''
                <script type="text/x-mathjax-config">
                    MathJax.Hub.Config({{
                        messageStyle: "none",
                        tex2jax: {{inlineMath: [['\\\\(','\\\\)']]}},
                        displayAlign: "center",
                        "HTML-CSS": {{ scale: 100 }}
                    }});
                </script>
                <script type="text/javascript">
                    if (typeof MathJax === "undefined") {{
                        var script = document.createElement("script");
                        script.type = "text/javascript";
                        script.src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS_HTML";
                        document.getElementsByTagName("head")[0].appendChild(script);
                    }}
                </script>
                <div style="max-width: 600px; margin: 0 auto; font-family: {theme['font_family']}; font-size: {theme['question_font_size']}; 
                     padding: 20px; background-color: {theme['question_bg']}; color: {theme['question_fg']}; 
                     border-radius: {theme['border_radius']}; box-shadow: {theme['box_shadow']}; text-align: left;">
                    {{{{Domanda}}}}
                </div>
                <hr id="answer" style="max-width: 600px; margin: 10px auto; border: 1px solid #e0e0e0;">
                <div style="max-width: 600px; margin: 0 auto; font-family: {theme['font_family']}; font-size: {theme['answer_font_size']}; 
                     padding: 20px; background-color: {theme['answer_bg']}; color: {theme['answer_fg']}; 
                     border-radius: {theme['border_radius']}; box-shadow: {theme['box_shadow']}; text-align: left;">
                    {{{{Risposta}}}}
                </div>
                ''',
            },
        ],
        css="""
        .card {
            text-align: center;
            background-color: #f7f7f7;
            padding: 20px 10px;
        }
        code {
            background-color: #f5f5f5;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: "Courier New", monospace;
        }
        mark {
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 2px;
        }
        ul, ol {
            margin-left: 20px;
            padding-left: 0;
            text-align: left;
        }
        li {
            margin: 5px 0;
        }
        """,
        model_type=0,
        sort_field_index=0
    )
    
    # Creiamo il mazzo principale
    main_deck_id = random.randrange(1 << 30, 1 << 31)
    main_deck = genanki.Deck(main_deck_id, deck_name)
    
    # Lista per raccogliere tutti i mazzi
    all_decks = [main_deck]
    
    # Se abbiamo qa_dict_per_file, creiamo sottomazzi per ogni file
    if qa_dict_per_file:
        for file_name, file_qa_dict in qa_dict_per_file.items():
            subdeck_name = os.path.splitext(file_name)[0]
            subdeck_id = random.randrange(1 << 30, 1 << 31)
            subdeck = genanki.Deck(subdeck_id, f"{deck_name}::{subdeck_name}")
            all_decks.append(subdeck)
            
            for domanda, risposta in file_qa_dict.items():
                note = genanki.Note(model=my_model, fields=[domanda, risposta])
                subdeck.add_note(note)
    else:
        for domanda, risposta in qa_dict.items():
            note = genanki.Note(model=my_model, fields=[domanda, risposta])
            main_deck.add_note(note)
    
    my_package = genanki.Package(all_decks)
    return my_package

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