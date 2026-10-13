# Diseño del Análisis Semántico — Compilador KC

Fase 3 · Compiladores II · UAA · 2026

Este documento define, **antes de implementar**, las reglas semánticas, los atributos, la
tabla de símbolos y el catálogo de errores que usará el analizador semántico. Todo parte del
AST que ya construye `sintac.py`; la gramática no se modifica para esta fase.

---

## 1. Punto de partida: forma del AST

Cada nodo es un `ASTNode(type, children, leaf, level, lineno, col)`. Las formas relevantes son:

| Construcción | Forma en el AST | Línea / columna |
|---|---|---|
| Declaración | `declaracion → tipo(int\|float\|real\|bool) → [id, id, …]` | tipo e ids |
| Asignación | `= → [id, expresión]` | `=` e id |
| Identificador | nodo hoja, `leaf` = lexema (`str`) | sí |
| Literal entera / flotante | nodo hoja, `leaf` = `int` / `float` de Python | sí |
| Literal booleana | nodo hoja, `leaf` = `'true'` / `'false'` (palabra reservada) | sí |
| Operación binaria | nodo con `type` = operador (`+ - * / % ^ < <= > >= == != && \|\| and or`) | operador |
| Negación lógica | `not → [expresión]` | sí |
| Agrupación | `grupo → [expresión]` | sí |
| `if` | `if → [condicion, entonces, else]` | `if` |
| `while` | `while → [condicion, cuerpo]` | `while` |
| `do … while` / `do … until` | `do-while` / `do-until → [cuerpo, condicion]` | `do` |
| Incremento / decremento | nodo hoja con el identificador (`x++;` → `x`) | sí |
| Entrada | `cin → [id]` | sí |
| Salida | `cout → salida → [expresión \| cadena, …]` | `cout` |
| Bloque | `bloque → lista_contenido` | `{` |
| Nodos de error sintáctico | `error`, `errores`, `error_expresion`, `error_recuperado` | — |

Se distingue un identificador de una literal por el tipo de Python de `leaf`
(`str` frente a `int`/`float`), y `true`/`false` por ser palabras reservadas.

---

## 2. Atributos

| Atributo | Clase | Dónde se calcula | Hacia dónde se propaga |
|---|---|---|---|
| `dtype` | **Heredado** | En el nodo `tipo` de la declaración | Del nodo `tipo` hacia cada identificador declarado (hermanos/hijos) |
| `tipo` | **Sintetizado** | Hojas: literal → tipo de la literal; id → búsqueda en tabla | De las hojas hacia los operadores y hasta la raíz de la expresión |
| `valor` | **Sintetizado** | Solo literales y operaciones cuyos operandos tienen `valor` (expresión constante) | Hacia el operador padre; no se fuerza si un operando es variable |
| `conversion` | Sintetizado (marca) | En el operando `int` que se promueve a `float` | Queda anotado en el nodo convertido (`int→float`) |
| `ambito` | **Heredado** | Pila de ámbitos al entrar a `main`, bloques y cuerpos de control | Del contexto hacia cada declaración y cada uso de identificador |
| `tipo_esperado` | **Heredado** | `bool` en condiciones; tipo de la variable destino en `=` | Del nodo de control / asignación hacia la expresión |

---

## 3. Reglas por construcción

### 3.1 Declaración de variables — `tipo lista_ids ;`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo declarado, lexema, línea y columna de cada identificador, ámbito actual |
| Atributos | `dtype` (heredado) · `ambito` (heredado) |
| Obtención / propagación | `dtype` sale del nodo `tipo` (`real` se normaliza a `float`) y se hereda a cada id de la lista |
| Tabla de símbolos | **Búsqueda solo en el ámbito actual** y luego **inserción** (nombre, tipo, línea, dirección, ámbito) |
| Validez | El identificador no existe en el ámbito actual |
| Errores | **SEM02** si ya fue declarado en el mismo ámbito (no se inserta de nuevo) |

Regla semántica: `tipo.dtype = tipo.lexema` · para cada `id` en `lista_ids`: `id.dtype = tipo.dtype`; `insertar(id.lexema, id.dtype, id.linea, ambito)`.

### 3.2 Asignación — `id = expresión ;`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la variable destino, tipo (y valor) de la expresión |
| Atributos | `id.tipo` (de tabla) · `expresion.tipo`, `expresion.valor` (sintetizados) · `tipo_esperado` (heredado = `id.tipo`) · `conversion` |
| Obtención / propagación | El tipo de `id` se obtiene por búsqueda; el de la expresión sube desde sus hojas; `=` recibe ambos y se anota con el tipo resultante |
| Tabla de símbolos | **Búsqueda** de `id`; se registra la línea de uso |
| Validez | Tipos iguales, o `int` → `float` (conversión implícita marcada) |
| Errores | **SEM01** id no declarado · **SEM04** asignar `float` a `int` · **SEM03** asignar `bool` ↔ numérico. Si la expresión es `error`, no se reporta nada adicional |

### 3.3 Expresiones aritméticas — `+ - * / % ^` (y `++`/`--` binarios)

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo y valor de ambos operandos |
| Atributos | `tipo`, `valor` (sintetizados) · `conversion` en el operando promovido |
| Obtención / propagación | De los hijos al operador; el resultado sigue subiendo |
| Tabla de símbolos | Indirecta: los operandos identificador hacen **búsqueda** |
| Validez | Ambos operandos numéricos. `%` requiere ambos `int` |
| Errores | **SEM05** si algún operando es `bool` (o `%` con `float`). Si un operando es `error`, el resultado es `error` sin nuevo reporte |

### 3.4 Expresiones relacionales — `< <= > >= == !=`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo y valor de ambos operandos |
| Atributos | `tipo` = `bool`, `valor` si ambos operandos son constantes |
| Obtención / propagación | De los hijos al operador |
| Tabla de símbolos | Indirecta (búsqueda de identificadores operandos) |
| Validez | `< <= > >=`: ambos numéricos. `== !=`: ambos numéricos o ambos `bool` |
| Errores | **SEM05** `bool` con `< <= > >=` · **SEM06** `==`/`!=` entre `bool` y numérico |

### 3.5 Expresiones lógicas — `&& || and or not`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo y valor de los operandos |
| Atributos | `tipo` = `bool`, `valor` si es constante |
| Obtención / propagación | De los hijos al operador |
| Tabla de símbolos | Indirecta |
| Validez | Todos los operandos `bool` |
| Errores | **SEM05** si algún operando es numérico. El nodo `error_expresion` (operando faltante) se toma como `error` sin nuevo reporte |

### 3.6 Selección — `if expr then … [else …] end`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la condición |
| Atributos | `tipo_esperado` = `bool` (heredado a la condición) · `condicion.tipo` (sintetizado) · `ambito` |
| Obtención / propagación | La condición sintetiza su tipo; `if` lo compara con `bool`. `entonces` y `else` abren un ámbito nuevo cada uno |
| Tabla de símbolos | Indirecta; inserciones de las declaraciones internas en el ámbito del bloque |
| Validez | `condicion.tipo == bool` |
| Errores | **SEM07** condición no booleana (no se reporta si la condición ya es `error`) |

### 3.7 Iteración — `while expr … end` / `while (expr) { … }`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la condición |
| Atributos | Igual que `if`; `cuerpo` abre un ámbito |
| Tabla de símbolos | Indirecta |
| Validez | `condicion.tipo == bool` |
| Errores | **SEM07** |

### 3.8 Repetición — `do … until expr` / `do … while expr`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la condición |
| Atributos | Igual que `while`; el cuerpo se analiza antes que la condición |
| Tabla de símbolos | Indirecta |
| Validez | `condicion.tipo == bool` |
| Errores | **SEM07** |

### 3.9 Incremento / decremento — `x++;`, `x--;`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la variable |
| Atributos | `tipo` (de tabla) |
| Tabla de símbolos | **Búsqueda**; registra línea de uso |
| Validez | Variable numérica |
| Errores | **SEM01** no declarada · **SEM05** si es `bool` |

### 3.10 Entrada — `cin >> id ;`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Existencia y tipo de la variable |
| Atributos | `tipo` (de tabla) |
| Tabla de símbolos | **Búsqueda**; registra línea de uso |
| Validez | Variable declarada (cualquier tipo) |
| Errores | **SEM01** |

### 3.11 Salida — `cout << expr ;`

| Aspecto | Detalle |
|---|---|
| Información necesaria | Tipo de la expresión (cadenas siempre válidas) |
| Atributos | `tipo`, `valor` de la expresión |
| Tabla de símbolos | Indirecta |
| Validez | Cualquier expresión bien tipada o cadena |
| Errores | Solo los que provengan de la propia expresión |

### 3.12 Bloque, `break` y nodos de error

* `bloque` abre y cierra un ámbito.
* `break` no requiere información semántica en esta fase.
* Los nodos de error sintáctico se recorren sin reportar errores semánticos; su tipo es `error`.

---

## 4. Reglas de tipos

Tipos del lenguaje: `int`, `float` (`real` es sinónimo), `bool`. Tipo interno adicional: `error`.

| Situación | Resultado |
|---|---|
| `int` op aritmético `int` | `int` (la división `/` entre enteros es entera) |
| `int` op aritmético `float` (o viceversa) | `float`, con conversión implícita `int→float` anotada en el operando `int` |
| `float` op aritmético `float` | `float` |
| `%` con algún `float` | Error **SEM05** |
| Operador aritmético con `bool` | Error **SEM05** |
| Relacional con numéricos | `bool` (se promueve `int→float` si se mezclan) |
| `<`, `<=`, `>`, `>=` con `bool` | Error **SEM05** |
| `==`, `!=` entre `bool` y numérico | Error **SEM06** |
| Lógicos (`&&`, `\|\|`, `and`, `or`, `not`) con `bool` | `bool` |
| Lógicos con numérico | Error **SEM05** |
| Asignar `int` a variable `float` | Válido, conversión `int→float` anotada en `=` |
| Asignar `float` a variable `int` | Error **SEM04** |
| Asignar numérico a `bool` o `bool` a numérico | Error **SEM03** |
| Condición de `if` / `while` / `do-while` / `do-until` | Debe ser `bool`; si no, **SEM07** |

**Control de cascada.** Si una subexpresión resulta `error`, el nodo padre también es
`error` y **no** se emiten errores adicionales por ella. El recorrido continúa con la
siguiente sentencia.

**Atributo valor.** Se calcula solo cuando todos los operandos son constantes (literales u
operaciones entre literales). Una división entre cero constante no se evalúa (sin valor).
Las variables no aportan valor en esta fase.

---

## 5. Tabla de símbolos

### 5.1 Estructura

Pila de ámbitos; cada ámbito es un **diccionario** `lexema → entrada`. Además se conserva
una lista con todas las entradas (incluidas las de ámbitos ya cerrados) para mostrarlas en
el IDE.

| Campo de la entrada | Contenido |
|---|---|
| `nombre` | Lexema del identificador |
| `tipo` | `int`, `float` o `bool` |
| `lineas` | Lista de líneas: la primera es la declaración, las demás son usos |
| `direccion` | Desplazamiento de memoria asignado al declarar |
| `ambito` | Nombre del ámbito (`main`, `if@15`, `else@15`, `while@30`, `bloque@32`, …) |

Tamaños para el desplazamiento: `int` = 4, `float` = 4, `bool` = 1. El desplazamiento es
secuencial y global (asignación estática): cada nueva variable recibe la siguiente dirección libre.

### 5.2 Operaciones

| Operación | Uso en el análisis |
|---|---|
| `entrar_ambito(nombre)` | Al iniciar `main`, `bloque`, `entonces`, `else` y `cuerpo` de ciclos |
| `salir_ambito()` | Al terminar esas construcciones |
| `insertar(nombre, tipo, linea)` | En cada identificador de una declaración; falla si ya existe en el ámbito actual (SEM02) |
| `buscar(nombre)` | En cada uso; recorre la pila del ámbito más interno al global; si no lo encuentra → SEM01 |
| `buscar_local(nombre)` | Verificación de duplicados en el ámbito actual |
| `registrar_uso(entrada, linea)` | Agrega la línea de uso a la entrada encontrada |

### 5.3 Relación AST ↔ tabla

* Declaración → **inserción**
* Uso de identificador → **búsqueda** (y registro de línea)
* Expresión → **obtención** del tipo del identificador y **propagación** hacia arriba
* Asignación → **comparación** del tipo de la variable con el tipo de la expresión

---

## 6. Árbol anotado

Se crea una **copia profunda** (`copy.deepcopy`) del AST original. Las anotaciones se
agregan solo a la copia como atributos del nodo:

| Anotación | Nodos |
|---|---|
| `dtype` | nodo `tipo` e identificadores declarados |
| `tipo` | identificadores, literales, operadores, `=`, condiciones |
| `valor` | literales y expresiones constantes |
| `conversion` | operando o asignación con `int→float` |
| `ambito` | identificadores declarados y usados |
| `direccion` | identificadores declarados |
| `error_sem` | código del error semántico detectado en ese nodo |

El IDE mostrará el AST original y el anotado para compararlos.

---

## 7. Catálogo de errores semánticos

Formato: `(código, línea, columna, descripción)`; se muestran en la pestaña
"Err. Semánticos" del IDE.

| Código | Error | Ejemplo |
|---|---|---|
| SEM01 | Identificador no declarado | `suma = 45;` sin declarar `suma` |
| SEM02 | Identificador duplicado en el mismo ámbito | `int x; float x;` |
| SEM03 | Incompatibilidad de tipos | `x = true;` con `x` entera |
| SEM04 | Conversión de tipos no válida | `x = 32.32;` con `x` entera |
| SEM05 | Uso indebido de operador según el tipo de sus operandos | `true + 1`, `3 && x`, `b++` con `b` booleana |
| SEM06 | Inconsistencia de tipos en expresión | `c == 13` con `c` booleana |
| SEM07 | Condición no booleana en estructura de control | `if x + 1 then … end` |

---

## 8. Resultado esperado con `TEST 2026.txt`

| Línea | Código | Motivo |
|---|---|---|
| 4 | SEM01 | `suma` no declarada |
| 5 | SEM04 | `x = 32.32` (`float` → `int`) |
| 14 | SEM04 | `y = 14.54` (`float` → `int`) |
| 16 | SEM04 | `y = a + 3` (`float` → `int`) |
| 33 | SEM01 | `mas` no declarada |
| 37 | SEM01 | `cin >> mas` (`mas` no declarada) |

Conversiones válidas esperadas: `a = 24.0 + 4 - …` (línea 10) promueve los enteros a `float`;
`a + 3` (línea 16) promueve `3` a `float` antes de detectar el error de asignación.
