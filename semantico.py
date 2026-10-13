import copy

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
        # Una línea se registra una sola vez aunque el id aparezca varias veces en ella
        if linea is not None and linea not in simbolo.lineas:
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
            self.usar_identificador(nodo)
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
        self.usar_identificador(destino)
        self.expresion(expr)

    # ── SELECCIÓN / ITERACIÓN / REPETICIÓN ──────
    def visitar_if(self, nodo):
        condicion, entonces, parte_else = nodo.children
        self.expresion(condicion.children[0])
        self.en_ambito(f"if@{nodo.lineno}", entonces.children)
        if parte_else.children:
            self.en_ambito(f"else@{nodo.lineno}", parte_else.children)

    def visitar_while(self, nodo):
        condicion, cuerpo = nodo.children
        self.expresion(condicion.children[0])
        self.en_ambito(f"while@{nodo.lineno}", cuerpo.children)

    def visitar_do(self, nodo):
        cuerpo, condicion = nodo.children
        self.en_ambito(f"do@{nodo.lineno}", cuerpo.children)
        self.expresion(condicion.children[0])

    def visitar_bloque(self, nodo):
        self.en_ambito(f"bloque@{nodo.lineno}", nodo.children)

    # ── ENTRADA / SALIDA ────────────────────────
    def visitar_cin(self, nodo):
        self.usar_identificador(nodo.children[0])

    def visitar_cout(self, nodo):
        for salida in nodo.children:
            for parte in salida.children:
                if parte.type != 'cadena':
                    self.expresion(parte)

    # ── EXPRESIONES ─────────────────────────────
    def expresion(self, nodo):
        """Recorre la expresión; las hojas identificador consultan la tabla."""
        if nodo is None or nodo.type in NODOS_ERROR:
            return
        if self.es_identificador(nodo):
            self.usar_identificador(nodo)
        elif self.es_literal(nodo):
            nodo.tipo = self.tipo_literal(nodo)
        else:
            for hijo in nodo.children:
                self.expresion(hijo)

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
        nodo.ambito = simbolo.ambito
        return simbolo


# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================
def analizar_semantica(ast):
    return AnalizadorSemantico().analizar(ast)
