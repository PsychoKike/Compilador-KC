import ply.yacc as yacc
from lexer import tokens, find_column
from graphviz import Digraph

# Lista global para almacenar errores sintácticos
syntax_errors = []

# Nodo del árbol sintáctico abstracto
class ASTNode:
    def __init__(self, type, children=None, leaf=None, level=1):
        self.type = type
        self.children = children if children is not None else []
        self.leaf = leaf
        self.level = level if level is not None else 1

    # Función para agregar nodos y aristas al gráfico del árbol
    def add_nodes(self, graph):
        if self:
            graph.node(str(id(self)), f"{self.type}\n{self.leaf if self.leaf else ''}\n{self.level}")
            for child in self.children:
                child.add_nodes(graph)
                graph.edge(str(id(self)), str(id(child)))

def calculate_levels(node, level=1):
    node.level = level
    for child in node.children:
        if isinstance(child, ASTNode):
            calculate_levels(child, level + 1)


# Reglas gramaticales
def p_program(p):
    '''program : PROGRAM LBRACE list_decl list_sent RBRACE'''
    p[0] = ASTNode('program', [p[3], p[4]])

def p_list_decl(p):
    '''list_decl : list_decl decl
                 | decl
                 | empty'''
    if len(p) == 3:
        p[0] = ASTNode('list_decl', [p[1], p[2]])
    else:
        p[0] = ASTNode('list_decl', [p[1]])

def p_decl(p):
    '''decl : tipo list_id SEMICOLON'''
    p[0] = ASTNode('decl', [p[1], p[2]])

def p_tipo(p):
    '''tipo : INT
            | FLOAT
            | BOOL'''
    p[0] = ASTNode('tipo', leaf=p[1])

def p_list_id(p):
    '''list_id : list_id COMMA IDENTIFIER
               | IDENTIFIER'''
    if len(p) == 4:
        p[0] = ASTNode('list_id', [p[1], ASTNode('identifier', leaf=p[3])])
    else:
        p[0] = ASTNode('list_id', [ASTNode('identifier', leaf=p[1])])

def p_list_sent(p):
    '''list_sent : list_sent sent
                 | sent
                 | empty'''
    if len(p) == 3:
        p[0] = ASTNode('list_sent', [p[1], p[2]])
    else:
        p[0] = ASTNode('list_sent', [p[1]])

def p_sent(p):
    '''sent : sent_if
            | sent_while
            | sent_do
            | sent_read
            | sent_write
            | bloque
            | sent_assign
            | BREAK'''
    p[0] = ASTNode('sent', [p[1]])

def p_sent_if(p):
    '''sent_if : IF LPAREN exp_bool RPAREN THEN bloque else_part FI'''
    p[0] = ASTNode('sent_if', [p[3], p[6], p[7]])

def p_else_part(p):
    '''else_part : ELSE bloque
                 | empty'''
    p[0] = ASTNode('else_part', [p[2]] if len(p) == 3 else [p[1]])

def p_sent_while(p):
    '''sent_while : WHILE LPAREN exp_bool RPAREN bloque'''
    p[0] = ASTNode('sent_while', [p[3], p[5]])

def p_sent_do(p):
    '''sent_do : DO bloque UNTIL LPAREN exp_bool RPAREN SEMICOLON'''
    p[0] = ASTNode('sent_do', [p[2], p[5]])

def p_sent_read(p):
    '''sent_read : READ IDENTIFIER SEMICOLON'''
    p[0] = ASTNode('sent_read', [ASTNode('identifier', leaf=p[2])])

def p_sent_write(p):
    '''sent_write : WRITE exp_bool_or_value SEMICOLON'''
    p[0] = ASTNode('sent_write', [p[2]])

def p_exp_value(p):
    '''exp_value : NUMBER
                 | IDENTIFIER'''
    p[0] = ASTNode('exp_value', leaf=p[1])

def p_bloque(p):
    '''bloque : LBRACE list_sent RBRACE'''
    p[0] = ASTNode('bloque', [p[2]])

def p_sent_assign_expr(p):
    '''sent_assign : IDENTIFIER ASSIGN expr SEMICOLON'''
    p[0] = ASTNode('sent_assign', [ASTNode('identifier', leaf=p[1]), p[3]])

def p_sent_assign_exp_bool(p):
    '''sent_assign : IDENTIFIER ASSIGN exp_bool SEMICOLON'''
    p[0] = ASTNode('sent_assign', [ASTNode('identifier', leaf=p[1]), p[3]])

def p_sent_assign_factor(p):
    '''sent_assign : IDENTIFIER ASSIGN factor SEMICOLON'''
    p[0] = ASTNode('sent_assign', [ASTNode('identifier', leaf=p[1]), p[3]])

def p_exp_bool(p):
    '''exp_bool : exp_bool OR comb
                | comb'''
    if len(p) == 4:
        p[0] = ASTNode('exp_bool', [p[1], ASTNode('operator', leaf=p[2]), p[3]])
    else:
        p[0] = ASTNode('exp_bool', [p[1]])

def p_exp_bool_or_value(p):
    '''exp_bool_or_value : exp_bool
                         | exp_value'''
    p[0] = p[1]


def p_comb(p):
    '''comb : comb AND igualdad
            | igualdad'''
    if len(p) == 4:
        p[0] = ASTNode('comb', [p[1], ASTNode('operator', leaf=p[2]), p[3]])
    else:
        p[0] = ASTNode('comb', [p[1]])

def p_igualdad(p):
    '''igualdad : igualdad EQ rel
                | igualdad NE rel
                | rel'''
    if len(p) == 4:
        p[0] = ASTNode('igualdad', [p[1],
 ASTNode('operator', leaf=p[2]), p[3]])
    else:
        p[0] = ASTNode('igualdad', [p[1]])

def p_rel(p):
    '''rel : expr op_rel expr'''
    p[0] = ASTNode('rel', [p[1], p[2], p[3]])

def p_op_rel(p):
    '''op_rel : LT
              | LE
              | GT
              | GE
              | EQ
              | NE'''
    p[0] = ASTNode('op_rel', leaf=p[1])

def p_expr(p):
    '''expr : expr PLUS term
            | expr MINUS term
            | term'''
    if len(p) == 4:
        p[0] = ASTNode('expr', [p[1], ASTNode('operator', leaf=p[2]), p[3]])
    else:
        p[0] = ASTNode('expr', [p[1]])

def p_term(p):
    '''term : term TIMES unario
            | term DIVIDE unario
            | unario'''
    if len(p) == 4:
        p[0] = ASTNode('term', [p[1], ASTNode('operator', leaf=p[2]), p[3]])
    else:
        p[0] = ASTNode('term', [p[1]])

def p_unario(p):
    '''unario : PLUS unario
              | MINUS unario
              | factor'''
    if len(p) == 3:
        p[0] = ASTNode('unario', [ASTNode('operator', leaf=p[1]), p[2]])
    else:
        p[0] = ASTNode('unario', [p[1]])

def p_factor(p):
    '''factor : NUMBER
              | IDENTIFIER
              | TRUE
              | FALSE
              | LPAREN exp_bool RPAREN'''
    if len(p) == 2:
        p[0] = ASTNode('factor', leaf=p[1])
    else:
        p[0] = ASTNode('factor', [p[2]])

def p_empty(p):
    '''empty :'''
    p[0] = ASTNode('empty')

# Función para manejar los errores sintácticos
def p_error(p):
    if p:
        error_msg = f"Syntax error at line {p.lineno}: Unexpected token '{p.value}'"
        syntax_errors.append(error_msg)
        # Recuperación del parser
        #tok = p.value
        #print(f"Valor de tok: {tok}")
        #while tok and tok not in [';', '{', '}', '(', ')']:
        #    tok = parser.token()  # Obtener el siguiente token
        #parser.errok()  # Restablecer el estado del parser
        #print(f"Valor de p: {p.value}")
    else:
        syntax_errors.append("Syntax Error: Unexpected end of file.")

# Construcción del parser
parser = yacc.yacc()

# Función para dibujar el AST
def draw_ast(node):
    def add_nodes_edges(graph, node):
        if node:
            graph.node(str(id(node)), f"{node.type}\n{node.leaf if node.leaf else ''}\n{node.level}")
            for child in node.children:
                graph.edge(str(id(node)), str(id(child)))
                add_nodes_edges(graph, child)

    dot = Digraph()
    add_nodes_edges(dot, node)
    return dot

# Función para analizar el código y devolver el resultado y los errores
def parse_code(code):
    global syntax_errors
    syntax_errors = []  # Reiniciar la lista de errores
    
    # Análisis sintáctico
    result = parser.parse(code)
     
    # Devolver el resultado y los errores sintácticos
    return result, syntax_errors
