# ================================================================
# GENERADOR DE CÓDIGO TM
# Equivalente a cgen.c de TINY (Louden), adaptado al AST anotado del
# Compilador KC. Recorre el árbol ya validado semánticamente y emite
# instrucciones para la TM extendida (tm/tm_kc.c).
# ================================================================
from emisor_tm import EmisorTM, PC, MP, GP, AC, AC1

# Nodos de sentencias que contienen una lista de sentencias
CONTENEDORES = ('main', 'program', 'lista_contenido', 'entonces', 'else', 'cuerpo')

# Salto condicional que deja 1 en ac cuando (izq - der) cumple la relación
SALTOS_RELACIONALES = {'<': 'JLT', '<=': 'JLE', '>': 'JGT',
                       '>=': 'JGE', '==': 'JEQ', '!=': 'JNE'}

ARITMETICOS = {'+': 'ADD', '++': 'ADD', '-': 'SUB', '--': 'SUB',
               '*': 'MUL', '/': 'DIV'}


class GeneradorTM:

    def __init__(self, tabla, trace=True):
        self.emisor      = EmisorTM(trace)
        self.tmp_offset  = 0        # tmpOffset: temporales respecto de mp
        self.ciclos      = []       # pila de ciclos: saltos pendientes de break
        # st_lookup: cada símbolo recibe una celda de memoria (0, 1, 2, ...)
        # en orden de declaración; se identifica por (nombre, ámbito).
        self.posiciones  = {(s.nombre, s.ambito): i
                            for i, s in enumerate(tabla.entradas)}
        self.simbolos    = {(s.nombre, s.ambito): s for s in tabla.entradas}

    # ── TABLA DE SÍMBOLOS ───────────────────────
    def st_lookup(self, nodo):
        """Posición de memoria de un identificador del árbol anotado."""
        return self.posiciones[(nodo.leaf, nodo.ambito)]

    def tipo_de(self, nodo):
        return self.simbolos[(nodo.leaf, nodo.ambito)].tipo

    # ── TEMPORALES (pila respecto de mp) ────────
    def push(self, comentario):
        self.emisor.emit_rm("ST", AC, self.tmp_offset, MP, comentario)
        self.tmp_offset -= 1
        return self.tmp_offset + 1

    def pop(self, registro, comentario):
        self.tmp_offset += 1
        self.emisor.emit_rm("LD", registro, self.tmp_offset, MP, comentario)

    # ── CLASIFICACIÓN DE HOJAS ──────────────────
    @staticmethod
    def es_identificador(nodo):
        return (isinstance(nodo.leaf, str) and nodo.type == nodo.leaf
                and not nodo.children
                and nodo.leaf.lower() not in ('true', 'false'))

    @staticmethod
    def es_literal(nodo):
        if isinstance(nodo.leaf, (int, float)) and not isinstance(nodo.leaf, bool):
            return True
        return (isinstance(nodo.leaf, str) and nodo.type == nodo.leaf
                and nodo.leaf.lower() in ('true', 'false'))

    # ================================================================
    # cGen: recorrido de sentencias
    # ================================================================
    def c_gen(self, nodo):
        if nodo is None:
            return
        if self.es_identificador(nodo):
            self.gen_actualizacion(nodo)            # sentencia x++; / x--;
        elif nodo.type in CONTENEDORES:
            for hijo in nodo.children:
                self.c_gen(hijo)
        else:
            self.gen_stmt(nodo)

    # ── genStmt ─────────────────────────────────
    def gen_stmt(self, nodo):
        e = self.emisor
        tipo = nodo.type

        if tipo == 'declaracion':
            for ident in nodo.children[0].children:
                if (ident.leaf, getattr(ident, 'ambito', None)) in self.posiciones:
                    e.comentario(f"{ident.dtype} {ident.leaf} -> dMem[{self.st_lookup(ident)}]")

        elif tipo == '=':
            destino, expr = nodo.children
            e.comentario(f"-> asignacion a {destino.leaf}")
            self.gen_exp(expr)
            e.emit_rm("ST", AC, self.st_lookup(destino), GP, f"asignacion: guardar {destino.leaf}")
            e.comentario("<- asignacion")

        elif tipo == 'if':
            condicion, entonces, parte_else = nodo.children
            e.comentario("-> if")
            self.gen_exp(condicion.children[0])
            salto_else = e.saltar(1)
            e.comentario("if: aqui va el salto al else")
            self.c_gen(entonces)
            salto_fin = e.saltar(1)
            e.comentario("if: aqui va el salto al final")
            actual = e.saltar(0)
            e.retroceder(salto_else)
            e.emit_rm_abs("JEQ", AC, actual, "if: saltar al else si es falsa")
            e.restaurar()
            self.c_gen(parte_else)
            actual = e.saltar(0)
            e.retroceder(salto_fin)
            e.emit_rm_abs("LDA", PC, actual, "if: saltar al final")
            e.restaurar()
            e.comentario("<- if")

        elif tipo == 'while':
            condicion, cuerpo = nodo.children
            e.comentario("-> while")
            inicio = e.saltar(0)
            self.gen_exp(condicion.children[0])
            salto_fin = e.saltar(1)
            e.comentario("while: aqui va el salto de salida")
            self.ciclos.append([])
            self.c_gen(cuerpo)
            e.emit_rm_abs("LDA", PC, inicio, "while: regresar a la condicion")
            fin = e.saltar(0)
            e.retroceder(salto_fin)
            e.emit_rm_abs("JEQ", AC, fin, "while: salir si es falsa")
            e.restaurar()
            self.cerrar_ciclo(fin)
            e.comentario("<- while")

        elif tipo in ('do-while', 'do-until'):
            cuerpo, condicion = nodo.children
            e.comentario(f"-> {tipo}")
            inicio = e.saltar(0)
            e.comentario(f"{tipo}: el salto regresa aqui")
            self.ciclos.append([])
            self.c_gen(cuerpo)
            self.gen_exp(condicion.children[0])
            if tipo == 'do-until':
                e.emit_rm_abs("JEQ", AC, inicio, "until: repetir mientras sea falsa")
            else:
                e.emit_rm_abs("JNE", AC, inicio, "do-while: repetir mientras sea verdadera")
            self.cerrar_ciclo(e.saltar(0))
            e.comentario(f"<- {tipo}")

        elif tipo == 'break':
            if self.ciclos:
                self.ciclos[-1].append(e.saltar(1))
                e.comentario("break: aqui va el salto al final del ciclo")

        elif tipo == 'bloque':
            for hijo in nodo.children:
                self.c_gen(hijo)

        elif tipo == 'cin':
            ident = nodo.children[0]
            e.emit_ro("IN", AC, 0, 0, f"leer {ident.leaf}")
            if self.tipo_de(ident) == 'int':
                e.emit_ro("TRNC", AC, AC, 0, "cin: conservar solo la parte entera")
            e.emit_rm("ST", AC, self.st_lookup(ident), GP, f"cin: guardar {ident.leaf}")

        elif tipo == 'cout':
            for salida in nodo.children:
                for parte in salida.children:
                    if parte.type == 'cadena':
                        e.comentario(f"cout: cadena {parte.leaf} (la TM no imprime texto)")
                    else:
                        self.gen_exp(parte)
                        e.emit_ro("OUT", AC, 0, 0, "cout: escribir ac")

        # 'empty' y nodos sin código: no emiten instrucciones

    def cerrar_ciclo(self, fin):
        """Completa los saltos de los break del ciclo actual."""
        e = self.emisor
        for loc in self.ciclos.pop():
            e.retroceder(loc)
            e.emit_rm_abs("LDA", PC, fin, "break: salir del ciclo")
            e.restaurar()

    # ── x++ / x-- (sentencia o dentro de expresión) ──
    def gen_actualizacion(self, nodo, es_expresion=False):
        e   = self.emisor
        loc = self.st_lookup(nodo)
        op  = "ADD" if nodo.actualizacion > 0 else "SUB"
        signo = "++" if nodo.actualizacion > 0 else "--"
        e.emit_rm("LD", AC, loc, GP, f"cargar {nodo.leaf}")
        guardar_previo = es_expresion and nodo.postfijo
        if guardar_previo:
            self.push(f"{nodo.leaf}{signo}: conservar valor previo")
        e.emit_rm("LDC", AC1, 1, 0, "constante 1")
        e.emit_ro(op, AC, AC, AC1, f"{nodo.leaf}{signo}")
        e.emit_rm("ST", AC, loc, GP, f"guardar {nodo.leaf}")
        if guardar_previo:
            self.pop(AC, f"{nodo.leaf}{signo}: valor previo")

    # ================================================================
    # genExp: expresiones (el resultado queda en ac)
    # ================================================================
    def gen_exp(self, nodo):
        e = self.emisor
        op = nodo.type.lower()

        if self.es_literal(nodo):
            valor = nodo.leaf
            if isinstance(valor, str):
                valor = 1 if valor.lower() == 'true' else 0
            e.emit_rm("LDC", AC, valor, 0, f"cargar constante {nodo.leaf}")

        elif self.es_identificador(nodo):
            if getattr(nodo, 'actualizacion', None):
                self.gen_actualizacion(nodo, es_expresion=True)
            else:
                e.emit_rm("LD", AC, self.st_lookup(nodo), GP, f"cargar {nodo.leaf}")

        elif op == 'grupo':
            self.gen_exp(nodo.children[0])

        elif op == 'neg':
            self.gen_exp(nodo.children[0])
            e.emit_rm("LDC", AC1, 0, 0, "menos unario: constante 0")
            e.emit_ro("SUB", AC, AC1, AC, "menos unario: 0 menos ac")

        elif op == 'not':
            self.gen_exp(nodo.children[0])
            e.emit_rm("LDC", AC1, 1, 0, "not: constante 1")
            e.emit_ro("SUB", AC, AC1, AC, "not: 1 menos ac")

        elif op == '%':
            self.gen_modulo(nodo)

        elif op == '^':
            self.gen_potencia(nodo)

        else:
            # Operador binario: igual que TINY (izq a temporal, der en ac)
            izq, der = nodo.children
            e.comentario(f"-> op {op}")
            self.gen_exp(izq)
            self.push("op: guardar operando izquierdo")
            self.gen_exp(der)
            self.pop(AC1, "op: recuperar operando izquierdo")

            if op in ARITMETICOS:
                e.emit_ro(ARITMETICOS[op], AC, AC1, AC, f"op {op}")
                if op == '/' and getattr(nodo, 'tipo', None) == 'int':
                    e.emit_ro("TRNC", AC, AC, 0, "division entera: truncar")
            elif op in SALTOS_RELACIONALES:
                e.emit_ro("SUB", AC, AC1, AC, f"op {op}")
                self.cargar_booleano(SALTOS_RELACIONALES[op])
            elif op in ('&&', 'and'):
                e.emit_ro("MUL", AC, AC1, AC, "op and: ambos 1")
            elif op in ('||', 'or'):
                e.emit_ro("ADD", AC, AC1, AC, "op or: suma de operandos")
                self.cargar_booleano("JGT")
            else:
                e.comentario(f"BUG: operador desconocido {op}")
            e.comentario(f"<- op {op}")

    def cargar_booleano(self, salto):
        """Deja 1 en ac si se cumple el salto sobre ac, y 0 en otro caso."""
        e = self.emisor
        e.emit_rm(salto, AC, 2, PC, "saltar si es verdadera")
        e.emit_rm("LDC", AC, 0, AC, "caso falso")
        e.emit_rm("LDA", PC, 1, PC, "salto incondicional")
        e.emit_rm("LDC", AC, 1, AC, "caso verdadero")

    # ── a % b = a - trunc(a / b) * b ────────────
    def gen_modulo(self, nodo):
        e = self.emisor
        izq, der = nodo.children
        e.comentario("-> op % (a menos trunc(a/b)*b)")
        self.gen_exp(izq)
        t_a = self.push("mod: guardar a")
        self.gen_exp(der)
        t_b = self.push("mod: guardar b")
        e.emit_rm("LD", AC1, t_a, MP, "mod: cargar a")
        e.emit_ro("DIV", AC, AC1, AC, "mod: a / b")
        e.emit_ro("TRNC", AC, AC, 0, "mod: truncar cociente")
        e.emit_rm("LD", AC1, t_b, MP, "mod: cargar b")
        e.emit_ro("MUL", AC, AC, AC1, "mod: cociente * b")
        e.emit_rm("LD", AC1, t_a, MP, "mod: cargar a")
        e.emit_ro("SUB", AC, AC1, AC, "mod: a menos cociente*b")
        self.tmp_offset += 2                  # liberar temporales a y b
        e.comentario("<- op %")

    # ── a ^ n: multiplicación repetida (n entero) ──
    def gen_potencia(self, nodo):
        e = self.emisor
        base, exponente = nodo.children
        e.comentario("-> op ^ (multiplicacion repetida)")
        self.gen_exp(base)
        t_base = self.push("pot: guardar base")
        self.gen_exp(exponente)
        e.emit_ro("TRNC", AC, AC, 0, "pot: exponente entero")
        t_n = self.push("pot: guardar exponente n")
        e.emit_rm("LDC", AC, 0, 0, "pot: bandera exponente negativo = 0")
        t_neg = self.push("pot: guardar bandera")
        e.emit_rm("LDC", AC, 1, 0, "pot: resultado = 1")
        t_res = self.push("pot: guardar resultado")
        # si n < 0: n = 0 - n y bandera = 1
        e.emit_rm("LD", AC, t_n, MP, "pot: cargar n")
        salto_pos = e.saltar(1)
        e.emit_rm("LDC", AC1, 0, 0, "pot: constante 0")
        e.emit_ro("SUB", AC, AC1, AC, "pot: n negativo a positivo")
        e.emit_rm("ST", AC, t_n, MP, "pot: guardar n")
        e.emit_rm("LDC", AC, 1, 0, "pot: bandera = 1")
        e.emit_rm("ST", AC, t_neg, MP, "pot: guardar bandera")
        actual = e.saltar(0)
        e.retroceder(salto_pos)
        e.emit_rm_abs("JGE", AC, actual, "pot: n no negativo")
        e.restaurar()
        # mientras n > 0: resultado = resultado * base; n = n - 1
        inicio = e.saltar(0)
        e.emit_rm("LD", AC, t_n, MP, "pot: cargar n")
        salto_fin = e.saltar(1)
        e.emit_rm("LD", AC, t_res, MP, "pot: cargar resultado")
        e.emit_rm("LD", AC1, t_base, MP, "pot: cargar base")
        e.emit_ro("MUL", AC, AC, AC1, "pot: resultado * base")
        e.emit_rm("ST", AC, t_res, MP, "pot: guardar resultado")
        e.emit_rm("LD", AC, t_n, MP, "pot: cargar n")
        e.emit_rm("LDC", AC1, 1, 0, "pot: constante 1")
        e.emit_ro("SUB", AC, AC, AC1, "pot: n menos 1")
        e.emit_rm("ST", AC, t_n, MP, "pot: guardar n")
        e.emit_rm_abs("LDA", PC, inicio, "pot: repetir")
        fin = e.saltar(0)
        e.retroceder(salto_fin)
        e.emit_rm_abs("JLE", AC, fin, "pot: terminar si n <= 0")
        e.restaurar()
        # si la bandera es 1: resultado = 1 / resultado
        e.emit_rm("LD", AC, t_neg, MP, "pot: cargar bandera")
        salto_sin_inv = e.saltar(1)
        e.emit_rm("LDC", AC, 1, 0, "pot: constante 1")
        e.emit_rm("LD", AC1, t_res, MP, "pot: cargar resultado")
        e.emit_ro("DIV", AC, AC, AC1, "pot: 1 / resultado")
        e.emit_rm("ST", AC, t_res, MP, "pot: guardar resultado")
        actual = e.saltar(0)
        e.retroceder(salto_sin_inv)
        e.emit_rm_abs("JEQ", AC, actual, "pot: exponente no negativo")
        e.restaurar()
        e.emit_rm("LD", AC, t_res, MP, "pot: resultado en ac")
        if getattr(nodo, 'tipo', None) == 'int':
            e.emit_ro("TRNC", AC, AC, 0, "pot: resultado entero")
        self.tmp_offset += 4                  # liberar los 4 temporales
        e.comentario("<- op ^")

    # ================================================================
    # codeGen: preludio, programa y HALT
    # ================================================================
    def code_gen(self, ast, nombre_archivo):
        e = self.emisor
        e.comentario("Compilacion KC a codigo TM")
        e.comentario(f"Archivo: {nombre_archivo}")
        e.comentario("Preludio estandar:")
        e.emit_rm("LD", MP, 0, AC, "cargar maxaddress desde la posicion 0")
        e.emit_rm("ST", AC, 0, AC, "limpiar la posicion 0")
        e.comentario("Fin del preludio.")
        self.c_gen(ast)
        e.comentario("Fin de la ejecucion.")
        e.emit_ro("HALT", 0, 0, 0, "")
        return e


def generar_codigo_tm(ast_anotado, tabla, nombre_archivo="programa.tm"):
    """Devuelve el EmisorTM con el programa completo (texto y listado)."""
    return GeneradorTM(tabla).code_gen(ast_anotado, nombre_archivo)
