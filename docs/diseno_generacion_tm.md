# Diseño de la Generación de Código TM — Compilador KC

Entrega final · Compiladores II · UAA · 2026

Este documento define, **antes de implementar**, cómo el compilador KC traduce el árbol
semántico anotado a instrucciones de la máquina TM (Tiny Machine) de Louden, cómo se
ejecutan y cómo se muestran en el IDE. Se toma como referencia `cgen.c`, `code.c`,
`intermedio.c` y `tm.c` del proyecto TINY.

---

## 1. Flujo completo

```
Programa fuente
   │  lexer.py / sintac.py        (léxico y sintáctico)
   ▼
AST  ──► semantico.py ──► AST anotado + tabla de símbolos
                              │   (solo si NO hay errores léxicos, sintácticos ni semánticos)
              ┌───────────────┴───────────────┐
              ▼                               ▼
     intermedio.py                     cgen.py + emisor_tm.py
     programa.ci (3 direcciones)       programa.tm (instrucciones TM)
     solo se muestra                          │
                                              ▼
                                  tm/tm.exe  (tm.c extendido)
                                  ejecución en consola: IN / OUT
```

Igual que en TINY, el `.ci` y el `.tm` se generan **por caminos paralelos desde el mismo
árbol**; el `.ci` no es la entrada de la TM.

---

## 2. Correspondencia TINY ↔ Compilador KC

| TINY (C) | Compilador KC (Python) |
|---|---|
| `TreeNode` con `nodekind` StmtK / ExpK | `ASTNode` con `type`; se despacha por `node.type` |
| `child[]` + `sibling` | `children`; las sentencias hermanas están en `lista_contenido.children` |
| `attr.name` / `attr.val` / `attr.op` | `leaf` (lexema o valor) / `type` (operador) |
| `st_lookup(name)` | `TablaSimbolos`: se busca el símbolo por (nombre, ámbito anotado) y se usa su **posición TM** |
| `code.c` (emitRO, emitRM, emitSkip, emitBackup, emitRestore, emitRM_Abs) | `emisor_tm.py`, clase `EmisorTM` con las mismas operaciones |
| `cgen.c` (codeGen, cGen, genStmt, genExp) | `cgen.py`, clase `GeneradorTM` |
| `intermedio.c` | `intermedio.py` |
| `main.c` (abre archivos, genera solo si `!Error`) | `file_operations.py` (IDE) |
| `tm.c` | `tm/tm_kc.c` → `tm/tm.exe` (tm.c extendido, ver sección 6) |

Registros (igual que `code.h`): `ac = 0`, `ac1 = 1`, `gp = 5` (variables), `mp = 6`
(temporales, crece hacia abajo desde la última dirección), `pc = 7`.

**Memoria de variables.** La tabla de símbolos asigna desplazamientos en bytes (0, 4, 8…),
pero la TM direcciona por celda. El generador numera los símbolos en orden de declaración
(0, 1, 2…) y usa ese número como desplazamiento respecto de `gp`: `LD ac, k(gp)`.

---

## 3. Traducción de expresiones (`genExp`)

| Nodo KC | Instrucciones TM |
|---|---|
| Literal `int` / `float` | `LDC ac, valor(0)` |
| Literal `true` / `false` | `LDC ac, 1(0)` / `LDC ac, 0(0)` |
| Identificador | `LD ac, k(gp)` |
| `grupo` `( e )` | se genera `e` |
| `a op b` (`+ - * /`) | igual que TINY: `a` → `ST ac, tmp(mp)` → `b` → `LD ac1, tmp(mp)` → `ADD/SUB/MUL/DIV ac, ac1, ac` |
| `/` entre enteros | `DIV` seguido de `TRNC ac, ac, 0` (truncar hacia cero) |
| `%` | `a - TRNC(a / b) * b` con temporales |
| `^` | ciclo: `r = 1; repetir b veces r = r * a` (exponente entero; si es negativo, `1 / r`) |
| `< <= > >= == !=` | `SUB ac, ac1, ac` y salto `JLT/JLE/JGT/JGE/JEQ/JNE` que deja 1 o 0 en `ac` (como TINY) |
| `&&`, `and` | ambos operandos valen 0/1 → `MUL ac, ac1, ac` |
| `\|\|`, `or` | `ADD` y luego normalizar a 0/1 con `JGT` |
| `not` | `1 - a` |
| `x++` / `x--` en expresión | carga `x`, guarda `x ± 1`; el valor de la expresión es el previo (postfijo) o el nuevo (prefijo) |
| Conversión `int→float` | no requiere instrucción: la TM extendida trabaja en reales |

---

## 4. Traducción de sentencias (`genStmt`)

| Sentencia KC | Instrucciones TM | Saltos |
|---|---|---|
| Declaración | ninguna (solo reserva posición) | — |
| `x = e;` | `e` → `ST ac, k(gp)` | — |
| `cin >> x;` | `IN ac` (+ `TRNC` si `x` es `int`) → `ST ac, k(gp)` | — |
| `cout << e;` | `e` → `OUT ac` | — |
| `cout << "texto";` | solo comentario `*` (la TM no imprime cadenas) | — |
| `x++;` / `x--;` | `LD` → `LDC ac1,1` → `ADD/SUB` → `ST` | — |
| `if c then A else B end` | igual que TINY | `JEQ` al `else` y `LDA pc` al final, completados con backpatching |
| `while c … end` | inicio: `c`; `JEQ` al final; cuerpo; `LDA pc` al inicio | `JEQ` completado al conocer el final |
| `do … until c` | inicio: cuerpo; `c`; `JEQ ac` al inicio (repite mientras sea falsa) | salto hacia atrás, dirección conocida |
| `do … while c` | inicio: cuerpo; `c`; `JNE ac` al inicio | salto hacia atrás |
| `break;` | `LDA pc` al final del ciclo más interno | pila de saltos pendientes, se completan al cerrar el ciclo |

**Destinos de salto.** La TM no entiende etiquetas `L1`, `L2`. Como en `code.c`,
`emitir_salto_reservado()` (emitSkip) deja un hueco, el generador continúa y, cuando
conoce el destino, `retroceder()` (emitBackup) escribe la instrucción con el
desplazamiento relativo a `pc` (`a − (loc + 1)`) y `restaurar()` (emitRestore) vuelve
al final.

Preludio y cierre (igual que TINY): `LD mp, 0(ac)` · `ST ac, 0(ac)` … `HALT 0,0,0`.

---

## 5. Código intermedio de tres direcciones (`.ci`)

`intermedio.py` sigue a `intermedio.c`: temporales `t1, t2…`, etiquetas `L1, L2…`,
instrucciones `x = y op z`, `if_false t goto L`, `goto L`, `label L`, `read x`, `write t`,
`halt`, más `while`, `do-while`, `do-until`, `break` y la conversión `t = itof x`.
Se muestra en el IDE rotulado como **"Código intermedio de tres direcciones"**.

---

## 6. Extensión de la máquina TM (`tm/tm_kc.c`)

La TM original solo maneja enteros y los ejercicios requieren reales. Se copia `tm.c` a
`tm/tm_kc.c` con estos cambios mínimos:

| Cambio | Motivo |
|---|---|
| Registros `reg[]` y memoria `dMem[]` de tipo `double` | Operar con reales |
| `LDC` acepta constantes con punto decimal | Cargar literales `float` |
| `IN` acepta reales (“Ingrese un numero (IN):”) | Leer datos reales |
| `OUT` imprime enteros sin decimales y reales con decimales | Salida legible |
| Nueva instrucción RR `TRNC r,s,0`: `reg[r] = trunc(reg[s])` | División entera, `%` y lectura de enteros |
| Opción `-g` en la línea de comandos: ejecuta el programa al abrir y después deja el menú de comandos | Demostración directa desde el IDE |
| `IADDR_SIZE` y `DADDR_SIZE` mayores | Programas con ciclos para `^` y `%` |

Se compila con `gcc` a `tm/tm.exe`; ambos archivos se incluyen en el proyecto con rutas
relativas.

---

## 7. Integración en el IDE

* **Compilar (Run):** léxico → sintáctico → semántico → (si no hay errores) `.tm` y `.ci`.
  Con errores no se genera código y los paneles de código se limpian con el aviso
  correspondiente, para no mostrar una salida anterior como válida.
* **Pestaña "Código Intermedio":** listado del `.tm` con columnas Dirección · Instrucción ·
  Operandos · Comentario; sub-pestaña **"Código intermedio de tres direcciones"** con el `.ci`.
* **Botón "▶ Ejecutar TM":** abre una consola con `tm/tm.exe programa.tm -g`, donde la TM
  pide las entradas (`IN`) y muestra las salidas (`OUT`).
* Los archivos se guardan junto al programa fuente (`programa.tm`, `programa.ci`); si la
  pestaña no está guardada, en la carpeta `salida/` del proyecto.

---

## 8. Limitaciones conocidas del lenguaje (no se presentan como implementadas)

| Limitación | Cómo se escribe en KC |
|---|---|
| No hay menos unario (`-1`) | `0 - 1` |
| `cout` imprime una expresión (o cadena + expresión) por sentencia | un `cout` por valor |
| La TM no imprime cadenas | las cadenas solo aparecen como comentario en el `.tm` |
| `while x > 0 { … }` sin paréntesis seguido de otra sentencia da error sintáctico (previo) | usar `while … end` |
| No hay arreglos | acumuladores por separado |

---

## 9. Programas del Grupo 4

| # | Tipo | Programa | Construcciones que usa |
|---|---|---|---|
| 1 | Secuencial | Dinosaurio: libras → kg (× 0.4536), pies → m (× 0.3048) | `cin`, `float`, `*`, `cout` |
| 2 | Selectivo | `VAL = 100·V`, `100^V`, `100/V` o `0` según `NUM` | `if` anidados, `^`, `/` |
| 3 | Selectivo | Pago del trabajador: sueldo + horas extra (máx. 30) por categoría; categoría > 4 sin extra | `if` anidados, `float` |
| 4 | Repetitivo | Ventas: cuántas ≤ 200, entre 200 y 400, ≥ 400 | ciclo con centinela, contadores |
| 5 | Repetitivo | Estadio: precios P1–P5, ventas (CLAVE, CANT) hasta −1; importe por venta, boletos por tipo, recaudación total | ciclo con centinela, `if` anidados, acumuladores |
