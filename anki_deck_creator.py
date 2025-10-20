import genanki
import random
import os
from anki_template import get_anki_model

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
    
    # Generiamo un model_id casuale da passare a get_anki_model
    model_id = random.randrange(1 << 30, 1 << 31)
    my_model = get_anki_model(theme=theme, model_id=model_id)
    
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