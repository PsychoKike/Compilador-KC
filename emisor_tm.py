# ================================================================
# EMISOR DE INSTRUCCIONES TM
# Equivalente a code.c / code.h de TINY (Louden): escribe las
# instrucciones con su dirección y resuelve las posiciones de salto.
# ================================================================

# ── REGISTROS (code.h) ─────────────────────────
PC  = 7     # contador del programa
MP  = 6     # "memory pointer": tope de memoria para temporales
GP  = 5     # "global pointer": base de las variables
AC  = 0     # acumulador
AC1 = 1     # segundo acumulador


def formatear_constante(valor):
    """Constante para LDC sin notación científica (la TM no la lee)."""
    if isinstance(valor, bool):
        return '1' if valor else '0'
    if isinstance(valor, int) or float(valor).is_integer():
        return str(int(valor))
    texto = format(valor, '.10f').rstrip('0').rstrip('.')
    return texto if texto not in ('', '-0') else '0'


class EmisorTM:
    """
    Guarda las instrucciones en orden de emisión (igual que code.c las
    escribe en el archivo) y también por dirección, para mostrarlas en
    el IDE ordenadas.
    """
    def __init__(self, trace=True):
        self.trace         = trace
        self.emit_loc      = 0      # emitLoc: posición que se escribe
        self.high_emit_loc = 0      # highEmitLoc: posición más alta usada
        self.lineas        = []     # texto del .tm en orden de emisión
        self.instrucciones = {}     # dirección -> (op, operandos, comentario)

    # ── AUXILIARES ──────────────────────────────
    def _registrar(self, op, operandos, comentario):
        loc = self.emit_loc
        # La TM suma números separados por +/-: un comentario no debe iniciar así
        if comentario[:1] in ('+', '-'):
            comentario = 'op ' + comentario
        texto = f"{loc:3d}:  {op:>5}  {operandos} "
        if self.trace and comentario:
            texto += f"\t{comentario}"
        self.lineas.append(texto)
        self.instrucciones[loc] = (op, operandos, comentario)
        self.emit_loc += 1
        if self.high_emit_loc < self.emit_loc:
            self.high_emit_loc = self.emit_loc

    # ── emitComment ─────────────────────────────
    def comentario(self, texto):
        if self.trace:
            self.lineas.append(f"* {texto}")

    # ── emitRO: instrucción solo registros ──────
    def emit_ro(self, op, r, s, t, comentario=""):
        self._registrar(op, f"{r},{s},{t}", comentario)

    # ── emitRM: registro-memoria ────────────────
    def emit_rm(self, op, r, d, s, comentario=""):
        self._registrar(op, f"{r},{formatear_constante(d)}({s})", comentario)

    # ── emitSkip: reservar posiciones ───────────
    def saltar(self, cuantas):
        i = self.emit_loc
        self.emit_loc += cuantas
        if self.high_emit_loc < self.emit_loc:
            self.high_emit_loc = self.emit_loc
        return i

    # ── emitBackup: regresar a una reservada ────
    def retroceder(self, loc):
        if loc > self.high_emit_loc:
            self.comentario("BUG en retroceder")
        self.emit_loc = loc

    # ── emitRestore: volver al final ────────────
    def restaurar(self):
        self.emit_loc = self.high_emit_loc

    # ── emitRM_Abs: salto absoluto -> relativo a pc
    def emit_rm_abs(self, op, r, a, comentario=""):
        self._registrar(op, f"{r},{a - (self.emit_loc + 1)}({PC})", comentario)

    # ── SALIDA ──────────────────────────────────
    def texto(self):
        return "\n".join(self.lineas) + "\n"

    def listado(self):
        """Instrucciones ordenadas por dirección: [(dir, op, operandos, comentario)]."""
        return [(loc, *self.instrucciones[loc]) for loc in sorted(self.instrucciones)]
