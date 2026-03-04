import ply.lex as lex

# Definir tokens
tokens = (
    'PROGRAM', 'IF', 'ELSE', 'FI', 'DO', 'UNTIL', 'WHILE', 'READ', 'WRITE',
    'FLOAT', 'INT', 'BOOL', 'NOT', 'AND', 'OR', 'TRUE', 'FALSE', 'BREAK',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'ASSIGN',
    'SEMICOLON', 'COMMA', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'IDENTIFIER', 'NUMBER', 'TB', 'THEN'
)

# Expresiones regulares para tokens simples
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_POWER = r'\^'
t_LT = r'<'
t_LE = r'<='
t_GT = r'>'
t_GE = r'>='
t_EQ = r'=='
t_NE = r'!='
t_ASSIGN = r'='
t_SEMICOLON = r';'
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'{'
t_RBRACE = r'}'

# Expresión regular para identificar tabuladores
def t_TB(t):
    r'\t'
    t.value = 'TB'
    return t

# Regla para comentarios de una sola línea
def t_COMMENT_SINGLELINE(t):
    r'\/\/.*'
    pass  # Ignorar los comentarios de una sola línea

# Regla para comentarios de varias líneas
# Regla para comentarios de varias líneas
def t_COMMENT_MULTILINE(t):
    r'\/\*(.|\n)*?\*\/'
    # Incrementar el número de líneas según la cantidad de saltos de línea dentro del comentario
    t.lexer.lineno += t.value.count('\n')
    # Encontrar la última posición de '\n' dentro del comentario
    last_newline_pos = t.value.rfind('\n', 0, t.lexpos)
    # Si encontramos un salto de línea dentro del comentario, ajustar la posición léxica
    if last_newline_pos != -1:
        t.lexer.lexpos = last_newline_pos + 1
    pass  # Ignorar los comentarios de varias líneas


# Expresión regular para identificar identificadores (variables, palabras clave, etc.)
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value.lower() in keywords:
        t.type = t.value.upper()  # Convertir a palabra clave si es una palabra reservada
    return t

# Expresión regular para el token BREAK
def t_BREAK(t):
    r'break'
    t.type = 'BREAK'
    return t

# Expresión regular para identificar números (enteros y flotantes)
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Ignorar caracteres como espacios en blanco
t_ignore = ' '

# Manejo de tabuladores (para contar un tabulador como un solo elemento)
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)  # Incrementar el número de líneas según la cantidad de saltos de línea

# Manejo de errores
def t_error(t):
    column = find_column(t.lexer.lexdata, t)
    error_message = f"Ilegal character '{t.value[0]}' at line {t.lexer.lineno}, column {column}"
    t.lexer.errors.append((t.value[0], t.lexer.lineno, column, error_message))
    t.lexer.skip(1)

# Función auxiliar para encontrar la columna exacta
def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    column = (token.lexpos - line_start) + 1
    return column

# Construir el lexer y lista de errores
lexer = lex.lex()
lexer.errors = []  

# Definir palabras clave
keywords = {
    'program', 'if', 'else', 'fi', 'do', 'until', 'while', 'read', 'write',
    'float', 'int', 'bool', 'not', 'and', 'or', 'true', 'false', 'break', 'then'
}

def process_input(input_text):
    lexer.input(input_text)
    tokens = []
    while True:
        token = lexer.token()
        if not token:
            break
        tokens.append(token)
    return tokens

def reset_lexer():
    lexer.lineno = 1
    lexer.errors = []
