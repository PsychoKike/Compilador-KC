import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from lexer import reset_lexer, process_input, lexer
from sintac import parse_code
from semantico import analizar_semantica
from cgen import generar_codigo_tm
from intermedio import generar_codigo_intermedio

DIR = Path(__file__).parent
TM_EXE = DIR / 'tm' / 'tm.exe'


def compilar_y_ejecutar(fuente, entradas):
    """Compila el fuente a .tm, lo ejecuta en tm.exe y devuelve las salidas OUT."""
    reset_lexer()
    process_input(fuente)
    assert lexer.errors == [], lexer.errors
    ast, errores = parse_code(fuente)
    assert errores == [], errores
    anotado, tabla, errores = analizar_semantica(ast)
    assert errores == [], errores
    emisor = generar_codigo_tm(anotado, tabla)
    generar_codigo_intermedio(anotado)          # también debe generarse sin fallar
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, 'programa.tm')
        Path(ruta).write_text(emisor.texto(), encoding='utf-8')
        datos = ''.join(f'{x}\n' for x in entradas) + 'q\n'
        r = subprocess.run([str(TM_EXE), ruta, '-g'], input=datos,
                           capture_output=True, text=True, timeout=30)
    assert 'Ejecucion finalizada (HALT)' in r.stdout, r.stdout[-500:]
    return re.findall(r'\(OUT\): (\S+)', r.stdout)


def programa(nombre):
    return (DIR / 'Grupo 4' / nombre).read_text(encoding='utf-8')


@unittest.skipUnless(TM_EXE.exists(), 'falta tm/tm.exe')
class GeneracionTMTests(unittest.TestCase):

    def test_1_dinosaurio(self):
        self.assertEqual(compilar_y_ejecutar(programa('1_dinosaurio.txt'), [1000, 50]),
                         ['453.592', '15.24'])

    def test_2_funcion_val(self):
        fuente = programa('2_funcion_val.txt')
        self.assertEqual(compilar_y_ejecutar(fuente, [1, 5]), ['500'])
        self.assertEqual(compilar_y_ejecutar(fuente, [2, 3]), ['1000000'])
        self.assertEqual(compilar_y_ejecutar(fuente, [3, 8]), ['12.5'])
        self.assertEqual(compilar_y_ejecutar(fuente, [7, 2]), ['0'])

    def test_3_pago_trabajador(self):
        fuente = programa('3_pago_trabajador.txt')
        self.assertEqual(compilar_y_ejecutar(fuente, [5000, 2, 40]), ['1140', '6140'])
        self.assertEqual(compilar_y_ejecutar(fuente, [4000.5, 4, 10]), ['700', '4700.5'])
        self.assertEqual(compilar_y_ejecutar(fuente, [3000, 5, 12]), ['0', '3000'])

    def test_4_ventas(self):
        self.assertEqual(
            compilar_y_ejecutar(programa('4_ventas.txt'), [5, 150, 200, 250, 399.5, 400]),
            ['2', '350', '2', '649.5', '1', '400'])

    def test_5_estadio(self):
        entradas = [10, 20, 30, 40, 50.5,  1, 3,  5, 2,  1, 1,  -1, -1]
        self.assertEqual(
            compilar_y_ejecutar(programa('5_estadio.txt'), entradas),
            ['1', '3', '30', '5', '2', '101', '1', '1', '10',
             '4', '0', '0', '0', '2', '141'])

    def test_construcciones_del_lenguaje(self):
        fuente = '''main {
          int a, i, s; float f; bool b;
          a = 7;
          cout << a / 2;  cout << a % 3;  cout << 2 ^ 10;  cout << -a + 1;
          f = a / 2.0;    cout << f;
          b = a >= 5 && not (a == 6);  cout << b;
          i = 1; s = 0;
          while i <= 100
            s = s + i;
            if s > 20 then break; end
            i++;
          end
          cout << s;
          i = 0;
          do i = i + 3; while i < 10;
          cout << i;
          do i--; until i == 5
          cout << i;
        }'''
        self.assertEqual(compilar_y_ejecutar(fuente, []),
                         ['3', '1', '1024', '-6', '3.5', '1', '21', '12', '5'])


if __name__ == '__main__':
    unittest.main()
