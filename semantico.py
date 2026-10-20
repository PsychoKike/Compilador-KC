import copy
import operator

# ================================================================
# TIPOS DEL LENGUAJE
# ================================================================
# 'real' es sinónimo de 'float' (ver lexer.py)
TIPOS   = {'int': 'int', 'float': 'float', 'real': 'float', 'bool': 'bool'}
TAMANOS = {'int': 4, 'float': 4, 'bool': 1}

# Nodos generados por la recuperación de errores sintácticos
NODOS_ERROR = ('error', 'errores', 'error_expresion', 'error_recuperado',
               'sin nodos válidos')

# ================================================================
# TABLA DE SÍMBOLOS
# ================================================================
class Simbolo:
    def __init__(self, nombre, tipo, linea, col, direccion, ambito):
        self.nombre    = nombre
        self.tipo      = tipo
        self.lineas    = [linea]      # la primera es la declaración
        self.col       = col
        self.direccion = direccion
        self.ambito    = ambito
        self.valor     = None
        self.revision  = 0

    def __repr__(self):
        return (f"Simbolo({self.nombre}, {self.tipo}, lineas={self.lineas}, "
                f"dir={self.direccion}, ambito={self.ambito})")


class TablaSimbolos:
    """
    Pila de ámbitos; cada ámbito es un diccionario lexema -> Simbolo.
    'entradas' conserva todos los símbolos (aunque su ámbito ya se haya
    cerrado) para mostrarlos en el IDE.
    """
    def __init__(self):
        self.pila           = []      # [(nombre_ambito, {lexema: Simbolo}), ...]
        self.entradas       = []
        self.siguiente_dir  = 0

    # ── ÁMBITOS ─────────────────────────────────
    def entrar_ambito(self, nombre):
        self.pila.append((nombre, {}))

    def salir_ambito(self):
        self.pila.pop()

    def ambito_actual(self):
        return self.pila[-1][0]

    # ── BÚSQUEDA ────────────────────────────────
    def buscar_local(self, nombre):
        return self.pila[-1][1].get(nombre)

    def buscar(self, nombre):
        # Del ámbito más interno hacia el global
        for _, simbolos in reversed(self.pila):
            if nombre in simbolos:
                return simbolos[nombre]
        return None

    # ── INSERCIÓN ───────────────────────────────
    def insertar(self, nombre, tipo, linea, col):
        """Devuelve el Simbolo insertado, o None si ya existe en el ámbito actual."""
        if self.buscar_local(nombre) is not None:
            return None
        simbolo = Simbolo(nombre, tipo, linea, col,
                          self.siguiente_dir, self.ambito_actual())
        self.siguiente_dir += TAMANOS[tipo]
        self.pila[-1][1][nombre] = simbolo
        self.entradas.append(simbolo)
        return simbolo

    def registrar_uso(self, simbolo, linea):

        if linea is not None:
            simbolo.lineas.append(linea)


# ================================================================
# ANALIZADOR SEMÁNTICO
# ================================================================
class AnalizadorSemantico:

    def __init__(self):
        self.tabla   = TablaSimbolos()
        self.errores = []      # (código, línea, columna, descripción)

    # ── PUNTO DE ENTRADA ────────────────────────
    def analizar(self, ast):
        """
        Recibe el AST original y devuelve (ast_anotado, tabla, errores).
        El AST original no se modifica: se anota una copia profunda.
        """
        anotado = copy.deepcopy(ast)
        self.tabla.entrar_ambito('main')
        self.visitar(anotado)
        self.tabla.salir_ambito()
        return anotado, self.tabla, self.errores

    # ── ERRORES ─────────────────────────────────
    def error(self, codigo, nodo, descripcion):
        linea = nodo.lineno if nodo.lineno is not None else '-'
        col   = nodo.col    if getattr(nodo, 'col', None) is not None else '-'
        self.errores.append((codigo, linea, col, f"{codigo}: {descripcion}"))
        nodo.error_sem = codigo

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

    # ── RECORRIDO DE SENTENCIAS ─────────────────
    def visitar(self, nodo):
        if nodo is None or nodo.type in NODOS_ERROR:
            return

        # Sentencia x++; / x--; (el parser deja solo el identificador)
        if self.es_identificador(nodo):
            self.expresion(nodo)
            return

        metodo = {
            'declaracion': self.visitar_declaracion,
            '=':           self.visitar_asignacion,
            'if':          self.visitar_if,
            'while':       self.visitar_while,
            'do-while':    self.visitar_do,
            'do-until':    self.visitar_do,
            'bloque':      self.visitar_bloque,
            'cin':         self.visitar_cin,
            'cout':        self.visitar_cout,
            'break':       lambda n: None,
            'empty':       lambda n: None,
        }.get(nodo.type)

        if metodo:
            metodo(nodo)
        else:
            # main, lista_contenido y contenedores: recorrer hijos en orden
            for hijo in nodo.children:
                self.visitar(hijo)

    def en_ambito(self, nombre, nodos):
        self.tabla.entrar_ambito(nombre)
        for n in nodos:
            self.visitar(n)
        self.tabla.salir_ambito()

    # ── DECLARACIÓN: tipo lista_ids ; ───────────
    def visitar_declaracion(self, nodo):
        nodo_tipo = nodo.children[0]
        # Atributo heredado dtype: del nodo tipo hacia cada identificador
        dtype = TIPOS[nodo_tipo.type]
        nodo_tipo.dtype = dtype
        for ident in nodo_tipo.children:
            ident.dtype  = dtype
            ident.valor  = None
            ident.ambito = self.tabla.ambito_actual()
            simbolo = self.tabla.insertar(ident.leaf, dtype, ident.lineno, ident.col)
            if simbolo is None:
                previo = self.tabla.buscar_local(ident.leaf)
                self.error('SEM02', ident,
                           f"identificador '{ident.leaf}' ya declarado en el ámbito "
                           f"'{previo.ambito}' (línea {previo.lineas[0]})")
                ident.tipo = previo.tipo
            else:
                ident.tipo      = dtype
                ident.direccion = simbolo.direccion

    # ── ASIGNACIÓN: id = expresión ; ────────────
    def visitar_asignacion(self, nodo):
        destino, expr = nodo.children
        simbolo = self.usar_identificador(destino)
        self.expresion(expr)
        nodo.valor = None
        nodo.tipo = 'error'
        tipo = getattr(expr, 'tipo', 'error')
        if simbolo is None or tipo == 'error':
            return
        expr.tipo_esperado = simbolo.tipo
        if simbolo.tipo == 'int' and tipo == 'float':
            self.error('SEM04', nodo,
                       f"no se puede asignar float a int en '{simbolo.nombre}'")
            return
        if simbolo.tipo != tipo and (simbolo.tipo, tipo) != ('float', 'int'):
            self.error('SEM03', nodo,
                       f"asignación incompatible a '{simbolo.nombre}': {tipo} → {simbolo.tipo}")
            return
        valor = expr.valor
        if simbolo.tipo == 'float' and tipo == 'int':
            nodo.conversion = 'int→float'
            valor = float(valor) if valor is not None else None
        simbolo.valor = destino.valor = nodo.valor = valor
        simbolo.revision += 1
        nodo.tipo = simbolo.tipo

    # ── SELECCIÓN / ITERACIÓN / REPETICIÓN ──────
    def visitar_if(self, nodo):
        condicion, entonces, parte_else = nodo.children
        self.validar_condicion(condicion)
        inicial = self.estado_valores()
        self.en_ambito(f"if@{nodo.lineno}", entonces.children)
        estado_then = self.estado_valores()
        self.restaurar_valores(inicial)
        if parte_else.children:
            self.en_ambito(f"else@{nodo.lineno}", parte_else.children)
        estado_else = self.estado_valores()
        valor = condicion.valor
        for simbolo in inicial:
            a, b = estado_then[simbolo][0], estado_else[simbolo][0]
            simbolo.valor = a if valor is True else b if valor is False else a if a == b else None

    def visitar_while(self, nodo):
        condicion, cuerpo = nodo.children
        self.validar_condicion(condicion)
        inicial = self.estado_valores()
        # Un ciclo se analiza una vez; los valores de sus variables escritas
        # dependen de cuántas iteraciones ocurran en ejecución.
        self.invalidar_escrituras(cuerpo)
        self.en_ambito(f"while@{nodo.lineno}", cuerpo.children)
        self.cerrar_ciclo(inicial, condicion.valor is False)

    def visitar_do(self, nodo):
        cuerpo, condicion = nodo.children
        inicial = self.estado_valores()
        self.invalidar_escrituras(cuerpo)
        self.en_ambito(f"do@{nodo.lineno}", cuerpo.children)
        self.validar_condicion(condicion)
        self.cerrar_ciclo(inicial)

    def estado_valores(self):
        return {s: (s.valor, s.revision) for _, ambito in self.tabla.pila for s in ambito.values()}

    @staticmethod
    def restaurar_valores(estado):
        for simbolo, (valor, _) in estado.items():
            simbolo.valor = valor

    def invalidar_escrituras(self, nodo):
        if nodo.type in ('=', 'cin'):
            simbolo = self.tabla.buscar(nodo.children[0].leaf)
            if simbolo:
                simbolo.valor = None
        elif getattr(nodo, 'actualizacion', None):
            simbolo = self.tabla.buscar(nodo.leaf)
            if simbolo:
                simbolo.valor = None
        for hijo in nodo.children:
            self.invalidar_escrituras(hijo)

    @staticmethod
    def cerrar_ciclo(inicial, no_ejecutado=False):
        for simbolo, (valor, revision) in inicial.items():
            simbolo.valor = valor if no_ejecutado or simbolo.revision == revision else None

    def validar_condicion(self, nodo):
        expr = nodo.children[0]
        expr.tipo_esperado = 'bool'
        self.expresion(expr)
        nodo.tipo, nodo.valor = expr.tipo, expr.valor
        if expr.tipo not in ('bool', 'error'):
            self.error('SEM07', expr, f"la condición debe ser bool, se obtuvo {expr.tipo}")

    def visitar_bloque(self, nodo):
        self.en_ambito(f"bloque@{nodo.lineno}", nodo.children)

    # ── ENTRADA / SALIDA ────────────────────────
    def visitar_cin(self, nodo):
        ident = nodo.children[0]
        simbolo = self.usar_identificador(ident)
        if simbolo is not None:
            simbolo.valor = ident.valor = None
            simbolo.revision += 1

    def visitar_cout(self, nodo):
        for salida in nodo.children:
            for parte in salida.children:
                if parte.type != 'cadena':
                    self.expresion(parte)

    # ── EXPRESIONES ─────────────────────────────
    def expresion(self, nodo):
        """Recorre la expresión; las hojas identificador consultan la tabla."""
        if nodo is None:
            return
        nodo.valor = None
        nodo.tipo = 'error'
        if nodo.type in NODOS_ERROR:
            return
        if self.es_identificador(nodo):
            simbolo = self.usar_identificador(nodo)
            actualizacion = getattr(nodo, 'actualizacion', None)
            if simbolo and actualizacion:
                if simbolo.tipo == 'bool':
                    self.error('SEM05', nodo, 'incremento/decremento requiere una variable numérica')
                    nodo.tipo = 'error'
                    return
                previo = simbolo.valor
                simbolo.valor = previo + actualizacion if previo is not None else None
                simbolo.revision += 1
                nodo.valor = previo if nodo.postfijo else simbolo.valor
        elif self.es_literal(nodo):
            nodo.tipo = self.tipo_literal(nodo)
        else:
            for hijo in nodo.children:
                self.expresion(hijo)
            self.evaluar_operador(nodo)

    def evaluar_operador(self, nodo):
        hijos = nodo.children
        if not hijos or any(getattr(h, 'tipo', 'error') == 'error' for h in hijos):
            return
        op = nodo.type.lower()
        if op == 'grupo':
            nodo.tipo, nodo.valor = hijos[0].tipo, hijos[0].valor
            return
        tipos = [h.tipo for h in hijos]
        numericos = all(t in ('int', 'float') for t in tipos)
        aritmeticos = {'+': operator.add, '-': operator.sub, '*': operator.mul,
                      '/': operator.truediv, '%': operator.mod, '^': operator.pow,
                      '++': operator.add, '--': operator.sub}
        relaciones = {'<': operator.lt, '<=': operator.le, '>': operator.gt,
                      '>=': operator.ge, '==': operator.eq, '!=': operator.ne}
        logicos = {'&&': operator.and_, 'and': operator.and_,
                   '||': operator.or_, 'or': operator.or_, 'not': operator.not_}
        if op in aritmeticos:
            valido = numericos and (op != '%' or tipos == ['int', 'int'])
            nodo.tipo = 'float' if 'float' in tipos else 'int'
            funcion = aritmeticos[op]
        elif op in relaciones:
            valido = numericos or (op in ('==', '!=') and tipos == ['bool', 'bool'])
            nodo.tipo, funcion = 'bool', relaciones[op]
        elif op in logicos:
            valido = all(t == 'bool' for t in tipos)
            nodo.tipo, funcion = 'bool', logicos[op]
        else:
            return
        if not valido:
            nodo.tipo = 'error'
            codigo = 'SEM06' if op in ('==', '!=') else 'SEM05'
            self.error(codigo, nodo, f"operador '{op}' incompatible con {' y '.join(tipos)}")
            return
        valores = [h.valor for h in hijos]
        if numericos and 'float' in tipos:
            for i, hijo in enumerate(hijos):
                if hijo.tipo == 'int':
                    hijo.conversion = 'int→float'
                    if valores[i] is not None:
                        valores[i] = float(valores[i])
        if any(v is None for v in valores):
            return
        try:
            if op == '/' and nodo.tipo == 'int':
                # División entera truncada hacia cero, también para negativos.
                a, b = valores
                resultado = abs(a) // abs(b)
                nodo.valor = -resultado if (a < 0) != (b < 0) else resultado
            else:
                resultado = funcion(*valores)
                nodo.valor = int(resultado) if nodo.tipo == 'int' else resultado
        except (ArithmeticError, ValueError, TypeError):
            # No hay valor calculable (por ejemplo división entre cero).
            nodo.valor = None

    @staticmethod
    def tipo_literal(nodo):
        if isinstance(nodo.leaf, str):
            nodo.valor = nodo.leaf.lower() == 'true'
            return 'bool'
        nodo.valor = nodo.leaf
        return 'float' if isinstance(nodo.leaf, float) else 'int'

    # ── USO DE IDENTIFICADOR ────────────────────
    def usar_identificador(self, nodo):
        """Búsqueda en la tabla: registra la línea de uso y obtiene el tipo."""
        simbolo = self.tabla.buscar(nodo.leaf)
        if simbolo is None:
            self.error('SEM01', nodo, f"identificador '{nodo.leaf}' no declarado")
            nodo.tipo = 'error'
            return None
        self.tabla.registrar_uso(simbolo, nodo.lineno)
        nodo.tipo   = simbolo.tipo
        nodo.valor  = simbolo.valor
        nodo.ambito = simbolo.ambito
        return simbolo


# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================
def analizar_semantica(ast):
    return AnalizadorSemantico().analizar(ast)
