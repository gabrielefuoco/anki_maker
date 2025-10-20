import genanki
import random

def get_anki_model(theme, model_id=None):
    """
    Crea e restituisce un modello Anki configurato.
    Se model_id non è fornito, ne viene generato uno casuale.
    """
    if model_id is None:
        model_id = random.randrange(1 << 30, 1 << 31)

    # Definizione del tema di default se non fornito
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

    my_model = genanki.Model(
        model_id,
        'Modello Domanda-Risposta Personalizzato',
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
        .MathJax_Display { 
            text-align: center !important; 
            margin: 1em 0em !important;
        }
        """,
        model_type=0,
        sort_field_index=0
    )
    return my_model