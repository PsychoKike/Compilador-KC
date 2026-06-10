import ply.yacc as yacc
from lexer import tokens, find_column, lexer as lex_instance

# ================================
# PRECEDENCIA
# ================================
precedence = (
    ('left',  'OR', 'OR_OP'),
    ('left',  'AND', 'AND_OP'),
    ('left',  'NOT'),
    ('left',  'EQ', 'NE'),
    ('left',  'LT', 'LE', 'GT', 'GE'),
    ('left',  'PLUS', 'MINUS'),
    ('left',  'INCREMENT', 'DECREMENT'),
    ('left',  'TIMES', 'DIVIDE', 'MODULO'),
    ('right', 'POWER'),
)

syntax_errors = []


# ================================
# NODO AST
# ================================
class ASTNode:
    def __init__(self, type, children=None, leaf=None, level=1, lineno=None):
        self.type     = type
        self.children = children if children is not None else []
        self.leaf     = leaf
        self.level    = level
        self.lineno   = lineno

    def __repr__(self):
        return f"ASTNode({self.type}, leaf={self.leaf})"


def calculate_levels(node, level=1):
    if node is None:
        return
    node.level = level
    for child in node.children:
        if isinstance(child, ASTNode):
            calculate_levels(child, level + 1)


# ================================
# GRAMÁTICA
# ================================

def p_program(p):
    '''program : MAIN LBRACE lista_declaracion RBRACE'''
    p[0] = ASTNode('program', [p[3]], lineno=p.lineno(1))

def p_lista_declaracion(p):
    '''lista_declaracion : lista_declaracion declaracion
                         | lista_declaracion lista_sentencias
                         | declaracion
                         | lista_sentencias
                         | empty'''
    if len(p) == 3:
        p[0] = ASTNode('lista_declaracion', [p[1], p[2]])
    else:
        p[0] = ASTNode('lista_declaracion', [p[1]])

def p_declaracion(p):
    '''declaracion : declaracion_variable'''
    p[0] = ASTNode('declaracion', [p[1]])

def p_declaracion_variable(p):
    '''declaracion_variable : tipo identificadores SEMICOLON'''
    p[0] = ASTNode('declaracion_variable', [p[1], p[2]], lineno=p.lineno(3))

def p_tipo(p):
    '''tipo : INT
            | FLOAT
            | BOOL'''
    p[0] = ASTNode('tipo', leaf=p[1], lineno=p.lineno(1))

def p_identificadores(p):
    '''identificadores : identificadores COMMA IDENTIFIER
                       | IDENTIFIER'''
    if len(p) == 4:
        p[0] = ASTNode('identificadores',
                       [p[1], ASTNode('id', leaf=p[3], lineno=p.lineno(3))])
    else:
        p[0] = ASTNode('identificadores',
                       [ASTNode('id', leaf=p[1], lineno=p.lineno(1))])

def p_lista_sentencias(p):
    '''lista_sentencias : lista_sentencias sentencia
                        | sentencia
                        | empty'''
    if len(p) == 3:
        p[0] = ASTNode('lista_sentencias', [p[1], p[2]])
    else:
        p[0] = ASTNode('lista_sentencias', [p[1]])

def p_sentencia(p):
    '''sentencia : seleccion
                 | iteracion
                 | repeticion
                 | sent_in
                 | sent_out
                 | asignacion
                 | bloque
                 | BREAK SEMICOLON'''
    if len(p) == 3:
        p[0] = ASTNode('sentencia',
                       [ASTNode('break', lineno=p.lineno(1))],
                       lineno=p.lineno(1))
    else:
        p[0] = ASTNode('sentencia', [p[1]])

def p_asignacion(p):
    '''asignacion : IDENTIFIER ASSIGN sent_expresion'''
    p[0] = ASTNode('asignacion',
                   [ASTNode('id', leaf=p[1], lineno=p.lineno(1)), p[3]],
                   lineno=p.lineno(2))

def p_sent_expresion(p):
    '''sent_expresion : expresion SEMICOLON
                      | SEMICOLON'''
    if len(p) == 3:
        p[0] = ASTNode('sent_expresion', [p[1]], lineno=p.lineno(2))
    else:
        p[0] = ASTNode('sent_expresion', lineno=p.lineno(1))

def p_seleccion(p):
    '''seleccion : IF expresion THEN lista_sentencias else_part END'''
    p[0] = ASTNode('seleccion', [p[2], p[4], p[5]], lineno=p.lineno(1))

def p_else_part(p):
    '''else_part : ELSE lista_sentencias
                 | empty'''
    if len(p) == 3:
        p[0] = ASTNode('else_part', [p[2]])
    else:
        p[0] = ASTNode('else_part', [p[1]])

def p_iteracion(p):
    '''iteracion : WHILE expresion lista_sentencias END'''
    p[0] = ASTNode('iteracion', [p[2], p[3]], lineno=p.lineno(1))

def p_repeticion(p):
    '''repeticion : DO lista_sentencias WHILE expresion SEMICOLON'''
    p[0] = ASTNode('repeticion', [p[2], p[4]], lineno=p.lineno(1))

def p_sent_in(p):
    '''sent_in : CIN RSHIFT IDENTIFIER SEMICOLON'''
    p[0] = ASTNode('sent_in',
                   [ASTNode('id', leaf=p[3], lineno=p.lineno(3))],
                   lineno=p.lineno(1))

def p_sent_out(p):
    '''sent_out : COUT LSHIFT salida SEMICOLON'''
    p[0] = ASTNode('sent_out', [p[3]], lineno=p.lineno(1))

def p_salida(p):
    '''salida : STRING
              | expresion
              | STRING LSHIFT expresion
              | expresion LSHIFT STRING'''
    if len(p) == 2:
        if isinstance(p[1], ASTNode):
            p[0] = ASTNode('salida', [p[1]])
        else:
            p[0] = ASTNode('salida', [ASTNode('string', leaf=p[1])])
    else:
        if isinstance(p[1], str):
            p[0] = ASTNode('salida', [ASTNode('string', leaf=p[1]), p[3]])
        else:
            p[0] = ASTNode('salida', [p[1], ASTNode('string', leaf=p[3])])

def p_bloque(p):
    '''bloque : LBRACE lista_sentencias RBRACE'''
    p[0] = ASTNode('bloque', [p[2]], lineno=p.lineno(1))

# ── EXPRESIONES ──────────────────────────────

def p_expresion(p):
    '''expresion : expresion_simple rel_op expresion_simple
                 | expresion_simple'''
    if len(p) == 4:
        p[0] = ASTNode('expresion', [p[1], p[2], p[3]])
    else:
        p[0] = ASTNode('expresion', [p[1]])

def p_rel_op(p):
    '''rel_op : LT
              | LE
              | GT
              | GE
              | EQ
              | NE'''
    p[0] = ASTNode('rel_op', leaf=p[1])

def p_expresion_simple(p):
    '''expresion_simple : expresion_simple suma_op termino
                        | termino'''
    if len(p) == 4:
        p[0] = ASTNode('expresion_simple', [p[1], p[2], p[3]])
    else:
        p[0] = ASTNode('expresion_simple', [p[1]])

def p_suma_op(p):
    '''suma_op : PLUS
               | MINUS
               | INCREMENT
               | DECREMENT'''
    p[0] = ASTNode('suma_op', leaf=p[1])

def p_termino(p):
    '''termino : termino mult_op factor
               | factor'''
    if len(p) == 4:
        p[0] = ASTNode('termino', [p[1], p[2], p[3]])
    else:
        p[0] = ASTNode('termino', [p[1]])

def p_mult_op(p):
    '''mult_op : TIMES
               | DIVIDE
               | MODULO'''
    p[0] = ASTNode('mult_op', leaf=p[1])

def p_factor(p):
    '''factor : factor pot_op componente
              | componente'''
    if len(p) == 4:
        p[0] = ASTNode('factor', [p[1], p[2], p[3]])
    else:
        p[0] = ASTNode('factor', [p[1]])

def p_pot_op(p):
    '''pot_op : POWER'''
    p[0] = ASTNode('pot_op', leaf=p[1])

def p_componente(p):
    '''componente : LPAREN expresion RPAREN
                  | NUMBER
                  | FLOAT_NUMBER
                  | IDENTIFIER
                  | TRUE
                  | FALSE
                  | op_logico componente'''
    if len(p) == 4:
        p[0] = ASTNode('componente', [p[2]])
    elif len(p) == 3:
        p[0] = ASTNode('componente', [p[1], p[2]])
    else:
        p[0] = ASTNode('componente', leaf=p[1])

def p_op_logico(p):
    '''op_logico : AND_OP
                 | OR_OP
                 | NOT
                 | AND
                 | OR'''
    p[0] = ASTNode('op_logico', leaf=p[1])

def p_empty(p):
    '''empty :'''
    p[0] = ASTNode('empty')


# ================================
# MANEJO DE ERRORES — con línea real
# Tokens de sincronización: ; } end
# El parser consume tokens hasta encontrar
# uno de esos puntos y luego continúa,
# evitando errores en cascada.
# ================================

_SYNC_TOKENS = {'SEMICOLON', 'RBRACE', 'END', 'IF', 'WHILE', 'DO', 'MAIN'}

# Nodos de error acumulados durante el parse
_error_nodes = []

def p_error(p):
    global syntax_errors, _error_nodes

    if p is None:
        syntax_errors.append((0, 0, "Error sintáctico: fin de archivo inesperado."))
        return

    # Calcular columna real
    col = '?'
    if hasattr(p.lexer, 'lexdata') and p.lexer.lexdata:
        line_start = p.lexer.lexdata.rfind('\n', 0, p.lexpos) + 1
        col = p.lexpos - line_start + 1

    error_msg = (
        f"Error sintáctico en línea {p.lineno}, "
        f"columna {col}: token inesperado '{p.value}' ({p.type})"
    )
    syntax_errors.append((p.lineno, col, error_msg))

    # Nodo de error para el árbol parcial
    _error_nodes.append(
        ASTNode('error',
                leaf=f"linea {p.lineno}, col {col}: '{p.value}'",
                lineno=p.lineno)
    )

    # Avanzar tokens hasta un punto de sincronización
    while True:
        tok = parser.token()
        if tok is None:
            break
        if tok.type in _SYNC_TOKENS:
            parser.restart()
            break

    parser.errok()


# ================================
# BUILD PARSER
# ================================
parser = yacc.yacc()


# ================================
# FUNCIÓN PRINCIPAL
# Siempre devuelve un AST, nunca None.
# Si hubo errores devuelve árbol parcial.
# ================================
def parse_code(source_code):
    global syntax_errors, _error_nodes
    syntax_errors = []
    _error_nodes  = []

    from lexer import reset_lexer
    reset_lexer()

    result = parser.parse(source_code, tracking=True)

    # Caso 1: parser no construyó nada — árbol solo con errores
    if result is None:
        result = ASTNode(
            'program (con errores)',
            children=_error_nodes if _error_nodes
                     else [ASTNode('sin nodos validos')]
        )

    # Caso 2: parser construyó algo pero hubo errores parciales
    elif _error_nodes:
        nodo_errores = ASTNode('errores detectados', children=_error_nodes)
        result.children.append(nodo_errores)

    return result, syntax_errors