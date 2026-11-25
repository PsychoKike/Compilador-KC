# ================================================================
# CÓDIGO INTERMEDIO DE TRES DIRECCIONES
# Equivalente a intermedio.c (extensión didáctica de TINY): recorre el
# AST anotado y escribe instrucciones con temporales t1, t2... y
# etiquetas L1, L2... Es solo para mostrarse; la TM no lo ejecuta.
# ================================================================

CONTENEDORES = ('main', 'program', 'lista_contenido', 'entonces', 'else', 'cuerpo', 'bloque')

NOMBRES_OP = {'and': '&&', 'or': '||', '++': '+', '--': '-'}


class GeneradorIntermedio:

    def __init__(self):
        self.lineas   = []
        self.temporal = 0
        self.etiqueta = 0
        self.ciclos   = []      # etiqueta de salida de cada ciclo (para break)

    def emitir(self, texto):
        self.lineas.append(texto)

    def nuevo_temporal(self):
        self.temporal += 1
        return f"t{self.temporal}"

    def nueva_etiqueta(self):
        self.etiqueta += 1
        return f"L{self.etiqueta}"

    @staticmethod
    def es_identificador(nodo):
        return (isinstance(nodo.leaf, str) and nodo.type == nodo.leaf
                and not nodo.children
                and nodo.leaf.lower() not in ('true', 'false'))

    # ── EXPRESIONES (postorden): devuelve el nombre del resultado ──
    def expresion(self, nodo):
        op = nodo.type.lower()
        if self.es_identificador(nodo):
            nombre = nodo.leaf
            if getattr(nodo, 'actualizacion', None):
                signo = '+' if nodo.actualizacion > 0 else '-'
                if nodo.postfijo:
                    previo = self.nuevo_temporal()
                    self.emitir(f"{previo} = {nombre}")
                    self.emitir(f"{nombre} = {nombre} {signo} 1")
                    return previo
                self.emitir(f"{nombre} = {nombre} {signo} 1")
            return nombre
        if not nodo.children:
            # literal: número, true o false
            return str(nodo.leaf).lower() if isinstance(nodo.leaf, str) else str(nodo.leaf)
        if op == 'grupo':
            return self.expresion(nodo.children[0])
        if op in ('neg', 'not'):
            operando = self.convertir(nodo.children[0])
            tmp = self.nuevo_temporal()
            self.emitir(f"{tmp} = {'-' if op == 'neg' else 'not'} {operando}")
            return tmp
        izq = self.convertir(nodo.children[0])
        der = self.convertir(nodo.children[1])
        tmp = self.nuevo_temporal()
        self.emitir(f"{tmp} = {izq} {NOMBRES_OP.get(op, op)} {der}")
        return tmp

    def convertir(self, nodo):
        """Resultado de un operando; si se promueve int→float se hace explícito."""
        nombre = self.expresion(nodo)
        if getattr(nodo, 'conversion', None) == 'int→float':
            tmp = self.nuevo_temporal()
            self.emitir(f"{tmp} = itof {nombre}")
            return tmp
        return nombre

    # ── SENTENCIAS ──────────────────────────────
    def sentencia(self, nodo):
        if nodo is None:
            return
        tipo = nodo.type
        if self.es_identificador(nodo):                    # x++; / x--;
            if getattr(nodo, 'actualizacion', None):
                signo = '+' if nodo.actualizacion > 0 else '-'
                self.emitir(f"{nodo.leaf} = {nodo.leaf} {signo} 1")
        elif tipo in CONTENEDORES:
            for hijo in nodo.children:
                self.sentencia(hijo)
        elif tipo == '=':
            destino, expr = nodo.children
            resultado = self.expresion(expr)
            if getattr(nodo, 'conversion', None) == 'int→float':
                tmp = self.nuevo_temporal()
                self.emitir(f"{tmp} = itof {resultado}")
                resultado = tmp
            self.emitir(f"{destino.leaf} = {resultado}")
        elif tipo == 'cin':
            self.emitir(f"read {nodo.children[0].leaf}")
        elif tipo == 'cout':
            for salida in nodo.children:
                for parte in salida.children:
                    if parte.type == 'cadena':
                        self.emitir(f"write {parte.leaf}")
                    else:
                        self.emitir(f"write {self.expresion(parte)}")
        elif tipo == 'if':
            condicion, entonces, parte_else = nodo.children
            cond = self.expresion(condicion.children[0])
            l_else = self.nueva_etiqueta()
            self.emitir(f"if_false {cond} goto {l_else}")
            self.sentencia(entonces)
            if parte_else.children:
                l_fin = self.nueva_etiqueta()
                self.emitir(f"goto {l_fin}")
                self.emitir(f"label {l_else}")
                self.sentencia(parte_else)
                self.emitir(f"label {l_fin}")
            else:
                self.emitir(f"label {l_else}")
        elif tipo == 'while':
            condicion, cuerpo = nodo.children
            l_inicio, l_fin = self.nueva_etiqueta(), self.nueva_etiqueta()
            self.emitir(f"label {l_inicio}")
            cond = self.expresion(condicion.children[0])
            self.emitir(f"if_false {cond} goto {l_fin}")
            self.ciclos.append(l_fin)
            self.sentencia(cuerpo)
            self.ciclos.pop()
            self.emitir(f"goto {l_inicio}")
            self.emitir(f"label {l_fin}")
        elif tipo in ('do-while', 'do-until'):
            cuerpo, condicion = nodo.children
            l_inicio, l_fin = self.nueva_etiqueta(), self.nueva_etiqueta()
            self.emitir(f"label {l_inicio}")
            self.ciclos.append(l_fin)
            self.sentencia(cuerpo)
            self.ciclos.pop()
            cond = self.expresion(condicion.children[0])
            salto = 'if_false' if tipo == 'do-until' else 'if_true'
            self.emitir(f"{salto} {cond} goto {l_inicio}")
            self.emitir(f"label {l_fin}")
        elif tipo == 'break' and self.ciclos:
            self.emitir(f"goto {self.ciclos[-1]}")
        # declaraciones, empty: no generan código intermedio

    def generar(self, ast):
        self.emitir("# CODIGO INTERMEDIO DE TRES DIRECCIONES - Compilador KC")
        self.emitir("# Los temporales t1, t2... y etiquetas L1, L2... son simbolicos;")
        self.emitir("# la TM no ejecuta este archivo (ejecuta el .tm).")
        self.emitir("")
        self.sentencia(ast)
        self.emitir("halt")
        return "\n".join(self.lineas) + "\n"


def generar_codigo_intermedio(ast_anotado):
    return GeneradorIntermedio().generar(ast_anotado)
