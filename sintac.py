import ply.yacc as yacc
import re
from lexer import tokens, find_column

precedence = (
    ('left',  'OR', 'OR_OP'),
    ('left',  'AND', 'AND_OP'),
    ('right', 'NOT'),
    ('left',  'EQ', 'NE'),
    ('left',  'LT', 'LE', 'GT', 'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'INCREMENT', 'DECREMENT'),
    ('left',  'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'POWER'),
)

syntax_errors = []
_error_nodes  = []

class ASTNode:
    def __init__(self, type, children=None, leaf=None, level=1, lineno=None, col=None):
        self.type     = type
        self.children = children if children is not None else []
        self.leaf     = leaf
        self.level    = level
        self.lineno   = lineno
        self.col      = col
    def __repr__(self):
        return f"ASTNode({self.type}, leaf={self.leaf})"

# Columna (base 1) del símbolo i de la producción, usando lexpos del token
def _col(p, i):
    data  = p.lexer.lexdata
    start = data.rfind('\n', 0, p.lexpos(i)) + 1
    return p.lexpos(i) - start + 1

# Nodo hoja (identificador o literal) con lexema, línea y columna
def _hoja(p, i):
    return ASTNode(str(p[i]), leaf=p[i], lineno=p.lineno(i), col=_col(p, i))

def calculate_levels(node, level=1):
    if node is None:
        return
    node.level = level
    for child in node.children:
        if isinstance(child, ASTNode):
            calculate_levels(child, level + 1)

# ================================================================
# PROGRAMA RAÍZ — Corregido para soportar tanto 'main {' como 'main() {'
# ================================================================
def p_program(p):
    '''program : MAIN LBRACE lista_contenido RBRACE
               | MAIN LPAREN RPAREN LBRACE lista_contenido RBRACE'''
    contenido = p[5] if p[2] == '(' else p[3]
    p[0] = ASTNode("main", contenido.children)

# ================================================================
# LISTA DE CONTENIDO
# ================================================================
def p_lista_contenido_multi(p):
    '''lista_contenido : lista_contenido item_contenido'''
    p[1].children.append(p[2])
    p[0] = p[1]

def p_lista_contenido_uno(p):
    '''lista_contenido : item_contenido'''
    p[0] = ASTNode('lista_contenido', [p[1]])

def p_lista_contenido_error(p):
    '''lista_contenido : lista_contenido error SEMICOLON
                       | lista_contenido error RBRACE
                       | lista_contenido error END'''
    nodo_err = ASTNode('error_recuperado',
                       leaf=f'token inválido ignorado (línea {p.lineno(2)})',
                       lineno=p.lineno(2))
    p[1].children.append(nodo_err)
    p[0] = p[1]

def p_lista_contenido_vacia(p):
    '''lista_contenido : empty'''
    p[0] = ASTNode('lista_contenido', [])

def p_item_contenido(p):
    '''item_contenido : declaracion_variable
                      | sentencia'''
    p[0] = p[1]

# ================================================================
# DECLARACIONES
# ================================================================
def p_declaracion_variable(p):
    '''declaracion_variable : tipo lista_ids SEMICOLON'''
    p[1].children = p[2].children
    p[0] = ASTNode("declaracion", [p[1]], lineno=p[1].lineno, col=p[1].col)

def p_tipo(p):
    '''tipo : INT
            | FLOAT
            | BOOL'''
    p[0] = ASTNode(p[1].lower(), lineno=p.lineno(1), col=_col(p, 1))

def p_lista_ids_multi(p):
    '''lista_ids : lista_ids COMMA IDENTIFIER'''
    p[1].children.append(_hoja(p, 3))
    p[0] = p[1]

def p_lista_ids_uno(p):
    '''lista_ids : IDENTIFIER'''
    p[0] = ASTNode("ids", [_hoja(p, 1)])

# ================================================================
# SENTENCIAS
# ================================================================
def p_sentencia(p):
    '''sentencia : asignacion
                 | sent_if
                 | sent_while
                 | sent_do
                 | sent_cin
                 | sent_cout
                 | bloque
                 | sent_incr
                 | sent_decr
                 | BREAK SEMICOLON'''
    if len(p) == 3:
        p[0] = ASTNode('break', lineno=p.lineno(1))
    else:
        p[0] = p[1]

# Corregidos para no generar el nodo estructural de incremento/decremento
def p_sent_incr(p):
    '''sent_incr : IDENTIFIER INCREMENT SEMICOLON
                 | INCREMENT IDENTIFIER SEMICOLON'''
    p[0] = _hoja(p, 1 if p[2] == '++' else 2)

def p_sent_decr(p):
    '''sent_decr : IDENTIFIER DECREMENT SEMICOLON
                 | DECREMENT IDENTIFIER SEMICOLON'''
    p[0] = _hoja(p, 1 if p[2] == '--' else 2)

def p_asignacion(p):
    '''asignacion : IDENTIFIER ASSIGN expresion SEMICOLON'''
    p[0] = ASTNode("=", [
        _hoja(p, 1),
        p[3]
    ], lineno=p.lineno(2), col=_col(p, 2))

# ================================================================
# IF
# ================================================================
def p_sent_if_std(p):
    '''sent_if : IF expresion THEN lista_contenido parte_else END SEMICOLON
               | IF expresion THEN lista_contenido parte_else END'''
    p[0] = ASTNode('if', [
        ASTNode('condicion', [p[2]]),
        ASTNode('entonces',  [p[4]]),
        p[5],
    ], lineno=p.lineno(1))

def p_sent_if_paren_then(p):
    '''sent_if : IF LPAREN expresion RPAREN THEN lista_contenido parte_else END SEMICOLON'''
    p[0] = ASTNode('if', [
        ASTNode('condicion', [p[3]]),
        ASTNode('entonces',  [p[6]]),
        p[7],
    ], lineno=p.lineno(1))

def p_sent_if_error_then(p):
    '''sent_if : IF error THEN lista_contenido parte_else END'''
    p[0] = ASTNode('if', [
        ASTNode('condicion', [ASTNode('error_expresion', leaf='expresión inválida en if')]),
        ASTNode('entonces',  [p[4]]),
        p[5],
    ], lineno=p.lineno(1))

def p_sent_if_paren_nothen(p):
    '''sent_if : IF LPAREN expresion RPAREN lista_contenido parte_else END'''
    p[0] = ASTNode('if', [
        ASTNode('condicion', [p[3]]),
        ASTNode('entonces',  [p[5]]),
        p[6],
    ], lineno=p.lineno(1))

def p_parte_else(p):
    '''parte_else : ELSE lista_contenido
                  | empty'''
    if len(p) == 3:
        p[0] = ASTNode('else', [p[2]])
    else:
        p[0] = ASTNode('else', [])

# ================================================================
# WHILE — Soportando palabra clave DO y terminación con SEMICOLON
# ================================================================
def p_sent_while_std(p):
    '''sent_while : WHILE expresion DO lista_contenido END SEMICOLON
                  | WHILE expresion lista_contenido END SEMICOLON
                  | WHILE expresion DO lista_contenido END
                  | WHILE expresion lista_contenido END'''
    cuerpo = p[4] if isinstance(p[3], str) else p[3]
    p[0] = ASTNode('while', [
        ASTNode('condicion', [p[2]]),
        ASTNode('cuerpo',    [cuerpo]),
    ], lineno=p.lineno(1))

def p_sent_while_paren_end(p):
    '''sent_while : WHILE LPAREN expresion RPAREN DO lista_contenido END SEMICOLON
                  | WHILE LPAREN expresion RPAREN lista_contenido END SEMICOLON'''
    cuerpo = p[6] if p[5].lower() == 'do' else p[5]
    p[0] = ASTNode('while', [
        ASTNode('condicion', [p[3]]),
        ASTNode('cuerpo',    [cuerpo]),
    ], lineno=p.lineno(1))

def p_sent_while_paren_bloque(p):
    '''sent_while : WHILE LPAREN expresion RPAREN bloque
                  | WHILE LPAREN expresion RPAREN bloque SEMICOLON'''
    p[0] = ASTNode('while', [
        ASTNode('condicion', [p[3]]),
        ASTNode('cuerpo',    [p[5]]),
    ], lineno=p.lineno(1))

def p_sent_while_bloque(p):
    '''sent_while : WHILE expresion bloque'''
    p[0] = ASTNode('while', [
        ASTNode('condicion', [p[2]]),
        ASTNode('cuerpo',    [p[3]]),
    ], lineno=p.lineno(1))

# ================================================================
# DO-WHILE
# ================================================================
def p_sent_do_std(p):
    '''sent_do : DO lista_contenido WHILE expresion SEMICOLON'''
    p[0] = ASTNode('do-while', [
        ASTNode('cuerpo',    [p[2]]),
        ASTNode('condicion', [p[4]]),
    ], lineno=p.lineno(1))

# DO ... UNTIL (con o sin punto y coma final)
def p_sent_do_until(p):
    '''sent_do : DO lista_contenido UNTIL expresion
               | DO lista_contenido UNTIL expresion SEMICOLON'''
    p[0] = ASTNode('do-until', [
        ASTNode('cuerpo',    [p[2]]),
        ASTNode('condicion', [p[4]]),
    ], lineno=p.lineno(1))

def p_sent_do_paren(p):
    '''sent_do : DO lista_contenido WHILE LPAREN expresion RPAREN SEMICOLON'''
    p[0] = ASTNode('do-while', [
        ASTNode('cuerpo',    [p[2]]),
        ASTNode('condicion', [p[5]]),
    ], lineno=p.lineno(1))

def p_sent_do_bloque(p):
    '''sent_do : DO bloque WHILE expresion SEMICOLON
               | DO bloque WHILE LPAREN expresion RPAREN SEMICOLON'''
    cond = p[5] if p[4] == '(' else p[4]
    p[0] = ASTNode('do-while', [
        ASTNode('cuerpo',    [p[2]]),
        ASTNode('condicion', [cond]),
    ], lineno=p.lineno(1))

# ================================================================
# CIN / COUT
# ================================================================
def p_sent_cin(p):
    '''sent_cin : CIN RSHIFT IDENTIFIER SEMICOLON
                | CIN IDENTIFIER SEMICOLON'''
    i = 3 if p[2] == '>>' else 2
    p[0] = ASTNode('cin', [ASTNode('id', leaf=p[i], lineno=p.lineno(i), col=_col(p, i))],
                   lineno=p.lineno(1))

def p_sent_cout(p):
    '''sent_cout : COUT LSHIFT salida SEMICOLON
                 | COUT salida SEMICOLON'''
    sal = p[3] if p[2] == '<<' else p[2]
    p[0] = ASTNode('cout', [sal], lineno=p.lineno(1))

def p_salida(p):
    '''salida : STRING
              | expresion
              | STRING LSHIFT expresion
              | expresion LSHIFT STRING'''
    if len(p) == 2:
        if isinstance(p[1], ASTNode):
            p[0] = ASTNode('salida', [p[1]])
        else:
            p[0] = ASTNode('salida', [ASTNode('cadena', leaf=p[1])])
    else:
        if isinstance(p[1], str):
            p[0] = ASTNode('salida', [ASTNode('cadena', leaf=p[1]), p[3]])
        else:
            p[0] = ASTNode('salida', [p[1], ASTNode('cadena', leaf=p[3])])

def p_bloque(p):
    '''bloque : LBRACE lista_contenido RBRACE'''
    p[0] = ASTNode('bloque', [p[2]], lineno=p.lineno(1))

# ================================================================
# EXPRESIONES
# ================================================================
def p_expresion_rel(p):
    '''expresion : expresion_simple rel_op expresion_simple'''
    p[0] = ASTNode(p[2].leaf, [p[1], p[3]], lineno=p[2].lineno, col=p[2].col)

def p_expresion_logica(p):
    '''expresion : expresion AND_OP expresion
                 | expresion OR_OP  expresion
                 | expresion AND    expresion
                 | expresion OR     expresion'''
    p[0] = ASTNode(p[2], [p[1], p[3]], lineno=p.lineno(2), col=_col(p, 2))

def p_expresion_logica_error(p):
    '''expresion : expresion AND_OP error
                 | expresion OR_OP error
                 | expresion AND error
                 | expresion OR error'''
    p[0] = ASTNode(p[2], [p[1], ASTNode('error_expresion', leaf='operando faltante')],
                   lineno=p.lineno(2), col=_col(p, 2))

def p_expresion_not(p):
    '''expresion : NOT expresion'''
    p[0] = ASTNode('not', [p[2]], lineno=p.lineno(1), col=_col(p, 1))

def p_expresion_simple_expr(p):
    '''expresion : expresion_simple'''
    p[0] = p[1]

def p_rel_op(p):
    '''rel_op : LT
              | LE
              | GT
              | GE
              | EQ
              | NE'''
    p[0] = ASTNode('op_rel', leaf=p[1], lineno=p.lineno(1), col=_col(p, 1))

def p_expresion_simple_op(p):
    '''expresion_simple : expresion_simple suma_op termino'''
    p[0] = ASTNode(p[2].leaf, [p[1], p[3]], lineno=p[2].lineno, col=p[2].col)

def p_expresion_simple_term(p):
    '''expresion_simple : termino'''
    p[0] = p[1]

def p_suma_op(p):
    '''suma_op : PLUS
               | MINUS
               | INCREMENT
               | DECREMENT'''
    p[0] = ASTNode('op', leaf=p[1], lineno=p.lineno(1), col=_col(p, 1))

def p_termino_op(p):
    '''termino : termino mult_op factor'''
    p[0] = ASTNode(p[2].leaf, [p[1], p[3]], lineno=p[2].lineno, col=p[2].col)

def p_termino_factor(p):
    '''termino : factor'''
    p[0] = p[1]

def p_mult_op(p):
    '''mult_op : TIMES
               | DIVIDE
               | MODULO'''
    p[0] = ASTNode('op', leaf=p[1], lineno=p.lineno(1), col=_col(p, 1))

def p_factor_pot(p):
    '''factor : factor POWER componente'''
    p[0] = ASTNode("^", [p[1], p[3]], lineno=p.lineno(2), col=_col(p, 2))

def p_factor_comp(p):
    '''factor : componente'''
    p[0] = p[1]

def p_componente_paren(p):
    '''componente : LPAREN expresion RPAREN'''
    p[0] = ASTNode('grupo', [p[2]], lineno=p.lineno(1), col=_col(p, 1))

def p_componente_numero(p):
    '''componente : NUMBER
                  | FLOAT_NUMBER'''
    p[0] = _hoja(p, 1)

def p_componente_id(p):
    '''componente : IDENTIFIER
                  | TRUE
                  | FALSE'''
    p[0] = _hoja(p, 1)

# Modificados en expresiones para no generar nodos intermedios de ++ y --
def p_componente_incr(p):
    '''componente : IDENTIFIER INCREMENT
                  | INCREMENT IDENTIFIER'''
    p[0] = _hoja(p, 1 if p[2] == '++' else 2)

def p_componente_decr(p):
    '''componente : IDENTIFIER DECREMENT
                  | DECREMENT IDENTIFIER'''
    p[0] = _hoja(p, 1 if p[2] == '--' else 2)

def p_empty(p):
    '''empty :'''
    p[0] = ASTNode('empty')

# ================================================================
# MANEJO DE ERRORES
# ================================================================
def p_error(p):
    global syntax_errors, _error_nodes

    if p is None:
        syntax_errors.append((0, 0, "Error sintáctico: fin de archivo inesperado."))
        return

    col = '?'
    if hasattr(p.lexer, 'lexdata') and p.lexer.lexdata:
        line_start = p.lexer.lexdata.rfind('\n', 0, p.lexpos) + 1
        col = p.lexpos - line_start + 1

    syntax_errors.append((
        p.lineno,
        col,
        f"Error sintáctico en línea {p.lineno}, columna {col}: token inesperado '{p.value}' ({p.type})"
    ))

    _error_nodes.append(
        ASTNode(
            'error',
            leaf=f"línea {p.lineno}, col {col}: '{p.value}'",
            lineno=p.lineno
        )
    )

parser = yacc.yacc()

# ================================================================
# LIMPIADOR DE CABECERA — Corregido para soportar main() {
# ================================================================
def _fix_header(source_code):
    lines = source_code.split('\n')
    pre_errors = []

    if re.match(r'^\s*main\s*(\(\s*\))?\s*\{\s*$', lines[0], re.IGNORECASE):
        return source_code, pre_errors

    if re.search(r'\bmain\b', lines[0], re.IGNORECASE) and '{' in lines[0]:
        pre_errors.append((1, 1,
            f"Error sintáctico en línea 1, columna 1: "
            f"contenido inválido antes del programa: '{lines[0].strip()[:60]}'"))
        lines[0] = 'main {'
        i = 1
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped == '{':
                lines[i] = ''
                break
            elif stripped and not re.match(
                r'^(int|float|bool|real|if|while|do|cin|cout|break|[a-zA-Z_]\w*\s*[=;])',
                stripped, re.IGNORECASE
            ):
                pre_errors.append((i + 1, 1,
                    f"Error sintáctico en línea {i+1}, columna 1: "
                    f"contenido inválido antes del programa: '{stripped[:60]}'"))
                lines[i] = ''
            else:
                break
            i += 1
        return '\n'.join(lines), pre_errors

    brace_line = -1
    for i, line in enumerate(lines):
        if line.strip() == '{':
            brace_line = i
            break

    if brace_line == -1:
        return source_code, pre_errors

    for i in range(brace_line):
        if lines[i].strip():
            pre_errors.append((i + 1, 1,
                f"Error sintáctico en línea {i+1}, columna 1: "
                f"contenido inválido antes del programa: '{lines[i].strip()[:60]}'"))
        lines[i] = ''
    lines[brace_line] = 'main {'

    return '\n'.join(lines), pre_errors

# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================
def parse_code(source_code):
    global syntax_errors, _error_nodes
    syntax_errors = []
    _error_nodes  = []

    from lexer import reset_lexer
    reset_lexer()

    clean_code, pre_errors = _fix_header(source_code)
    for err in pre_errors:
        syntax_errors.append(err)

    result = parser.parse(clean_code, tracking=True)

    if result is None:
        children = _error_nodes if _error_nodes else [ASTNode('sin nodos válidos')]
        result = ASTNode('program', children=children)
    elif _error_nodes:
        result.children = [c for c in result.children if c.type != 'errores']
        result.children.append(ASTNode('errores', children=list(_error_nodes)))

    calculate_levels(result)
    return result, syntax_errors