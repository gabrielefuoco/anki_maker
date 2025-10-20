import re

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
            return rf'\\({formula}\\)'
        
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