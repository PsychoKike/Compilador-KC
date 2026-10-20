import unittest
from pathlib import Path

from sintac import parse_code
from semantico import analizar_semantica
from lexer import reset_lexer, process_input, lexer


class SemanticaTests(unittest.TestCase):
    def analizar(self, contenido):
        ast, errores = parse_code('main {\n' + contenido + '\n}')
        self.assertEqual(errores, [])
        anotado, tabla, errores = analizar_semantica(ast)
        self.assertFalse(hasattr(ast.children[0], 'valor'))
        return anotado, {s.nombre: s for s in tabla.entradas}, errores

    def test_evaluacion_paso_a_paso(self):
        ast, tabla, errores = self.analizar('int x, y; x = 2 + 3 - 1; y = x + 7;')
        self.assertEqual(errores, [])
        expr = ast.children[1].children[1]
        self.assertEqual(expr.children[0].valor, 5)
        self.assertEqual(expr.valor, 4)
        self.assertEqual(tabla['y'].valor, 11)
        self.assertEqual(ast.children[1].children[0].valor, 4)

    def test_conversion_y_asignacion_invalida(self):
        ast, tabla, errores = self.analizar('int x; float f; x = 8; f = x; x = 2.0;')
        self.assertEqual([e[0] for e in errores], ['SEM04'])
        self.assertEqual(tabla['x'].valor, 8)
        self.assertIsInstance(tabla['f'].valor, float)
        self.assertEqual(ast.children[3].conversion, 'int→float')

    def test_null_conserva_tipo(self):
        ast, tabla, errores = self.analizar('int x, y; float f; y = x + 2; x = f;')
        self.assertEqual([e[0] for e in errores], ['SEM04'])
        self.assertIsNone(tabla['y'].valor)
        self.assertEqual(ast.children[2].children[1].tipo, 'int')

    def test_operadores_y_cascada(self):
        _, _, errores = self.analizar('int x; bool b; x = true + 1; x = z + 2; b = 2 == true;')
        self.assertEqual([e[0] for e in errores], ['SEM05', 'SEM01', 'SEM06'])

    def test_entrada_y_actualizaciones(self):
        _, tabla, errores = self.analizar('int x, y; x = 4; y = x++; ++x; cin >> x; y = x + 1;')
        self.assertEqual(errores, [])
        self.assertIsNone(tabla['x'].valor)
        self.assertIsNone(tabla['y'].valor)

    def test_valor_final_de_incremento_y_decremento_en_arbol(self):
        ast, tabla, errores = self.analizar(
            'float a; int x; a = 61.0; a++; a--; x = 4; x--; ++x;')
        self.assertEqual(errores, [])
        self.assertEqual([ast.children[i].valor for i in (3, 4, 6, 7)],
                         [62.0, 61.0, 3, 4])
        self.assertEqual(tabla['a'].valor, 61.0)
        self.assertEqual(tabla['x'].valor, 4)

    def test_postfijo_en_expresion_conserva_valor_previo(self):
        ast, tabla, errores = self.analizar('int x, y; x = 4; y = x++;')
        self.assertEqual(errores, [])
        self.assertEqual(ast.children[2].children[1].valor, 4)
        self.assertEqual(tabla['y'].valor, 4)
        self.assertEqual(tabla['x'].valor, 5)

    def test_ramas_y_ciclos(self):
        _, tabla, errores = self.analizar('int x; bool b; x = 2; if b then x = 3; else x = 4; end while true do x = x + 1; end')
        self.assertEqual(errores, [])
        self.assertIsNone(tabla['x'].valor)
        _, tabla, errores = self.analizar('int x; x = 2; if false then x = 9; else x = 4; end while false do x = 8; end')
        self.assertEqual(errores, [])
        self.assertEqual(tabla['x'].valor, 4)

    def test_division_entera_y_cero(self):
        _, tabla, errores = self.analizar('int x, y; x = (0 - 7) / 2; y = 1 / 0;')
        self.assertEqual(errores, [])
        self.assertEqual(tabla['x'].valor, -3)
        self.assertIsNone(tabla['y'].valor)

    def test_archivo_oficial(self):
        fuente = Path(__file__).with_name('TEST 2026.txt').read_text(encoding='utf-8')
        reset_lexer()
        process_input(fuente)
        self.assertEqual(lexer.errors, [])
        ast, errores = parse_code(fuente)
        self.assertEqual(errores, [])
        _, _, errores = analizar_semantica(ast)
        self.assertEqual([(e[0], e[1]) for e in errores],
                         [('SEM01', 4), ('SEM04', 5), ('SEM04', 14),
                          ('SEM04', 16), ('SEM01', 33), ('SEM01', 37)])


if __name__ == '__main__':
    unittest.main()
