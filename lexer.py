import ply.lex as lex

# ================================
# TOKENS
# ================================
tokens = (
    # Palabras reservadas
    'MAIN', 'IF', 'ELSE', 'THEN', 'END',
    'WHILE', 'DO', 'BREAK',
    'INT', 'FLOAT', 'BOOL',
    'TRUE', 'FALSE',
    'CIN', 'COUT',
    'NOT', 'AND', 'OR',
    'READ', 'WRITE',  # Mantenemos compatibilidad

    # Operadores aritméticos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER', 'MODULO',
    'INCREMENT', 'DECREMENT',

    # Operadores relacionales
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
    'ASSIGN',

    # Operadores lógicos (símbolo)
    'AND_OP', 'OR_OP',

    # Operadores de stream
    'LSHIFT', 'RSHIFT',

    # Símbolos
    'SEMICOLON', 'COMMA', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',

    # Literales
    'IDENTIFIER', 'NUMBER', 'FLOAT_NUMBER', 'STRING',
    'INVALID_FLOAT',
)

# ================================
# PALABRAS RESERVADAS
# ================================
keywords = {
    'main':  'MAIN',
    'if':    'IF',
    'else':  'ELSE',
    'then':  'THEN',
    'end':   'END',
    'while': 'WHILE',
    'until': 'WHILE',   # until → tratado como while
    'do':    'DO',
    'break': 'BREAK',
    'int':   'INT',
    'float': 'FLOAT',
    'real':  'FLOAT',   # real → tratado como float
    'bool':  'BOOL',
    'true':  'TRUE',
    'false': 'FALSE',
    'cin':   'CIN',
    'cout':  'COUT',
    'not':   'NOT',
    'and':   'AND',
    'or':    'OR',
    # compatibilidad
    'read':  'READ',
    'write': 'WRITE',
}

# ================================
# OPERADORES (largos primero)
# ================================
t_LE       = r'<='
t_GE       = r'>='
t_NE       = r'!='
t_LSHIFT   = r'<<'
t_RSHIFT   = r'>>'
t_LT       = r'<'
t_GT       = r'>'
t_ASSIGN   = r'='

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

def t_EQ(t):
    r'==|\=\s*\='
    t.value = '=='
    return t

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_POWER   = r'\^'
t_MODULO  = r'%'

# ================================
# SÍMBOLOS
# ================================
t_SEMICOLON = r';'
t_COMMA     = r','
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'{'
t_RBRACE    = r'}'

# ================================
# COMENTARIOS
# ================================
def t_COMMENT_SINGLELINE(t):
    r'//.*'
    pass

def t_COMMENT_MULTILINE(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

# ================================
# CADENAS
# ================================
def t_STRING(t):
    r'"[^"]*"'
    return t

# ================================
# IDENTIFICADORES Y KEYWORDS
# ================================
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value.lower(), 'IDENTIFIER')
    return t

# ================================
# FLOATS INVÁLIDOS
# ================================
def t_INVALID_FLOAT(t):
    r'\d+\.(?!\d)'
    column = find_column(t.lexer.lexdata, t)
    error_message = f"Invalid float '{t.value}' at line {t.lexer.lineno}, column {column}"
    t.lexer.errors.append((t.value, t.lexer.lineno, column, error_message))
    pass

# ================================
# NÚMEROS
# ================================
def t_FLOAT_NUMBER(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
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
    t.lexer.skip(1)

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