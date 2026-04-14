import ply.lex as lex

# ================================
# TOKENS
# ================================
tokens = (
    'PROGRAM', 'IF', 'ELSE', 'FI', 'DO', 'UNTIL', 'WHILE', 'READ', 'WRITE',
    'FLOAT', 'INT', 'BOOL', 'NOT_OP', 'AND', 'OR', 'TRUE', 'FALSE', 'BREAK', 'THEN',

    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER', 'MODULO',

    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'ASSIGN',

    'SEMICOLON', 'COMMA', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',

    'IDENTIFIER', 'NUMBER',
    
    # OPERADORES LARGOS (IMPORTANTE: deben ir al final para evitar conflictos con los cortos)
    'INCREMENT', 'DECREMENT', 'AND_OP', 'OR_OP'
)

# ================================
# PALABRAS RESERVADAS
# ================================
keywords = {
    'program', 'if', 'else', 'fi', 'do', 'until', 'while',
    'read', 'write', 'float', 'int', 'bool',
    'not', 'and', 'or', 'true', 'false', 'break', 'then'
}

# ================================
# OPERADORES (IMPORTANTE: largos primero)
# ================================
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='

t_LT = r'<'
t_GT = r'>'
t_ASSIGN = r'='

def t_INCREMENT(t):
    r'\+\s*\+'
    t.value = '++'
    return t

def t_DECREMENT(t):
    r'\-\s*\-'
    t.value = '--'
    return t

def t_AND_OP(t):
    r'&\s*&'
    t.value = '&&'
    return t

def t_OR_OP(t):
    r'\|\s*\|'
    t.value = '||'
    return t

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_POWER = r'\^'
t_MODULO = r'%'
t_NOT_OP = r'!'


# ================================
# SÍMBOLOS
# ================================
t_SEMICOLON = r';'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'{'
t_RBRACE = r'}'

# ================================
# COMENTARIOS
# ================================

# // comentario
def t_COMMENT_SINGLELINE(t):
    r'//.*'
    pass

# /* comentario */
def t_COMMENT_MULTILINE(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

# ================================
# IDENTIFICADORES Y KEYWORDS
# ================================
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value.lower() in keywords:
        t.type = t.value.upper()
    return t

# ================================
# NÚMEROS
# ================================
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# ================================
# IGNORAR ESPACIOS Y TABS
# ================================
t_ignore = ' \t'

# ================================
# SALTOS DE LÍNEA
# ================================
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# ================================
# ERRORES
# ================================
def t_error(t):
    column = find_column(t.lexer.lexdata, t)
    error_message = f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}, column {column}"
    
    t.lexer.errors.append((t.value[0], t.lexer.lineno, column, error_message))
    
    t.lexer.skip(1)  # 🔥 IMPORTANTE para evitar loops infinitos

# ================================
# COLUMNA
# ================================
def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# ================================
# BUILD LEXER
# ================================
lexer = lex.lex()
lexer.errors = []

# ================================
# FUNCIONES AUX
# ================================
def process_input(input_text):
    lexer.input(input_text)
    tokens_list = []

    while True:
        token = lexer.token()
        if not token:
            break
        tokens_list.append(token)

    return tokens_list


def reset_lexer():
    lexer.lineno = 1
    lexer.errors = []