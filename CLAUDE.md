# Compilador KC — Contexto para Claude Code

## Sobre mí

* Me llamo **Enrique**. Dirígete a mí por mi nombre en cada respuesta.
* Responde siempre en español.
* Soy estudiante de 9.º semestre de Ingeniería en Sistemas Computacionales (UAA), materia Compiladores II.

## Proyecto

Compilador desarrollado durante dos semestres. Ya funcionan las fases anteriores:

* Análisis léxico (genera tokens con lexema, línea y columna).
* Análisis sintáctico (construye el AST).
* IDE con listas separadas de errores léxicos, sintácticos y semánticos (Verificar si existen estos errores antes de realizar alguna modificación al codigo).

Ahora toca la **Fase 3: Análisis Semántico**.
Los requisitos oficiales están en "D:\\UAA OCTAVO SEMESTRE\\Compiladores 1\\Codigos\\CompiladorKC\\Compilador KC\\CompiladoresII\_Fase3\_Analisis\_Semantico\_2026.pdf". **Léelo antes de empezar.**

Entrega y revisión: **15 y 16 de octubre de 2026**. Hay 10 % de penalización por día de retraso.

## Alcance actual: Fases 0, 1 y 2 del plan

### Fase 0 — Diagnóstico

1. Explora el proyecto e identifica el lenguaje, la estructura de carpetas, el lexer, el parser, las clases de nodos del AST y el código del IDE.
2. Verifica que el archivo oficial de pruebas compila sin errores léxicos ni sintácticos.
3. Revisa si los nodos del AST conservan lexema, línea y columna. Si no, propón el cambio mínimo para conservarlos.
4. Reporta lo encontrado **antes** de modificar código.

### Fase 1 — Diseño semántico (documentar antes de implementar)

Crea `docs/diseno\\\_semantico.md` con:

* Una tabla por cada construcción de la gramática (declaraciones, asignación, expresiones aritméticas, relacionales y lógicas, selección, iteración, repetición, entrada y salida) indicando:

  * información semántica que necesita;
  * atributos que intervienen y si son **sintetizados** o **heredados**;
  * de dónde se obtiene cada atributo y hacia dónde se propaga;
  * qué consulta a la tabla de símbolos;
  * condiciones de validez y errores posibles.
* Las reglas de tipos (sección siguiente).
* La estructura de la tabla de símbolos.
* El catálogo de errores semánticos.

### Fase 2 — Tabla de símbolos y declaraciones

1. Implementar la tabla de símbolos como estructura tipo diccionario con operaciones de **inserción**, **búsqueda** y manejo de **ámbito**.
2. Procesar las declaraciones propagando el tipo hacia cada identificador mediante el atributo heredado `dtype`.
3. Al usar un identificador: buscarlo en la tabla, registrar la línea de uso y obtener su tipo.
4. Detectar identificadores **no declarados** y **declaraciones duplicadas**.
5. Crear una **copia profunda del AST** original; las anotaciones semánticas se agregan sobre la copia para poder comparar AST original vs. AST anotado.

## Reglas de tipos (propuesta; ajustar si la gramática define otra cosa)

Tipos del lenguaje: `int`, `float`, `bool`.

|Situación|Resultado|
|-|-|
|`int` op aritmético `int`|`int`|
|`int` op aritmético `float` (o viceversa)|`float`, con conversión implícita `int→float` marcada en el nodo|
|`float` op aritmético `float`|`float`|
|Operador aritmético con `bool`|Error: uso indebido de operador|
|Operador relacional con numéricos|`bool`|
|Operadores lógicos (`\\\&\\\&`, `||
|Asignar `int` a variable `float`|Válido, conversión `int→float`|
|Asignar `float` a variable `int`|Error: conversión no válida|
|Asignar numérico a `bool` o `bool` a numérico|Error: incompatibilidad de tipos|
|Condición de if / while / until|Debe ser `bool`; si no, error|

* Si una subexpresión tiene error, su tipo es `error` y **no se reportan errores adicionales** derivados de ella (evita errores en cascada). El análisis debe continuar.
* Atributo **valor**: calcularlo solo cuando la expresión sea constante; no forzarlo en otros casos.

## Tabla de símbolos

Cada entrada debe contener:

* Nombre / lexema
* Tipo de dato
* Lista de números de línea donde aparece (declaración y usos)
* Dirección o desplazamiento de memoria (propuesta: `int` = 4, `float` = 4, `bool` = 1; ajustar a lo que ya defina el proyecto)
* Ámbito

La tabla debe **usarse de verdad durante el análisis**, no generarse solo para mostrarla:

* Declaración → inserción
* Uso de identificador → búsqueda
* Expresión → obtención y propagación de tipos
* Asignación → comparar tipo del identificador con tipo de la expresión

## Catálogo de errores semánticos

Cada error se reporta con código, línea, columna (si existe) y descripción clara, en la lista de errores semánticos del IDE.

|Código|Error|
|-|-|
|SEM01|Identificador no declarado|
|SEM02|Identificador duplicado en el mismo ámbito|
|SEM03|Incompatibilidad de tipos|
|SEM04|Conversión de tipos no válida|
|SEM05|Uso indebido de operador según el tipo de sus operandos|
|SEM06|Inconsistencia de tipos en asignación o expresión|
|SEM07|Condición no booleana en estructura de control|

(En la Fase 2 solo se implementan SEM01 y SEM02; el resto corresponde a la Fase 3 del plan.)

## Restricciones obligatorias

* **No modificar la gramática** para facilitar la implementación.
* **No rehacer** el lexer ni el parser; solo adecuaciones mínimas.
* **No cambiar ni reemplazar el archivo oficial de pruebas.**
* No romper el manejo de errores léxicos y sintácticos existente.

## Forma de trabajar

* Explícame cada cambio importante antes de hacerlo y por qué.
* Sigue el estilo de código y las convenciones que ya tiene el proyecto.
* Haz cambios pequeños y verificables; compila y prueba con el archivo oficial después de cada paso.
* Al terminar cada fase, redacta en `docs/notas\\\_documento.md` 2 o 3 párrafos explicando lo implementado, para usarlos después en el PDF de entrega.

