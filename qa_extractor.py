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
    """Trasforma le formule matematiche da $...$ a \\(...\\) ignorando i blocchi di codice."""
    if not text:
        return text

    # Pattern per trovare blocchi di codice (inline e multiline) e formule matematiche
    pattern = re.compile(r'(```.*?```|`[^`]+`|\$[^$]+\$)', re.DOTALL)
    
    parts = []
    last_end = 0
    
    for match in pattern.finditer(text):
        # Aggiungi il testo tra l'ultima corrispondenza e quella attuale
        parts.append(text[last_end:match.start()])
        
        # Controlla se la corrispondenza è una formula matematica o un blocco di codice
        part = match.group(0)
        if part.startswith('$') and part.endswith('$'):
            # È una formula matematica, trasformala
            formula = part[1:-1]
            parts.append(rf'\\({formula}\\)')
        else:
            # È un blocco di codice, lascialo invariato
            parts.append(part)
        
        last_end = match.end()
        
    # Aggiungi il resto del testo dopo l'ultima corrispondenza
    parts.append(text[last_end:])
    
    return "".join(parts)

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
                
                # Applica trasformazioni nell'ordine corretto
                # 1. Trasforma le formule matematiche
                domanda_formattata = transform_math_formulas(domanda)
                risposta_formattata = transform_math_formulas(next_risposta)
                
                # 2. Trasforma il resto del markdown in HTML
                domanda_formattata = transform_markdown_formatting(domanda_formattata)
                risposta_formattata = transform_markdown_formatting(risposta_formattata)

                # 3. Escape dell'HTML per Anki
                domanda_formattata = escape_anki_html(domanda_formattata)
                risposta_formattata = escape_anki_html(risposta_formattata)
                
                qa_dict[domanda_formattata] = risposta_formattata
    
    return qa_dict