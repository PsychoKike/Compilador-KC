import lexer
import sintac
import argparse

def test_lexer(input_text, source='console'):
    lexer.lexer.input(input_text)
    tokens = []
    errors = []
    while True:
        token = lexer.lexer.token()
        if not token:
            break
        tokens.append(token)
        token.lexpos = lexer.find_column(input_text, token)
        #column = lexer.find_column(input_text, token)
        if source == 'console':
            print(f"LexToken({token.type}, '{token.value}', {token.lineno}, {token.lexpos})")
        errors = lexer.lexer.errors

    return tokens, errors

def test_parser(tokens):
    result, errors = sintac.parse_code(tokens)
    for error in errors:
        print(error)
    return result

def tokens_to_text(tokens):
    """
    Convierte una lista de tokens en texto plano.
    """
    return ' '.join(str(token.value) for token in tokens)

def main():
    parser = argparse.ArgumentParser(description='Lexer Test Script')
    parser.add_argument('input', type=str, help='Input text or path to input file')
    args = parser.parse_args()

    # Leer el texto de entrada desde el argumento proporcionado
    input_text = None
    try:
        # Intentar abrir el archivo si el argumento es un nombre de archivo
        with open(args.input, 'r') as file:
            input_text = file.read()
    except FileNotFoundError:
        # Si no se encuentra el archivo, se asume que el argumento es el texto de entrada directamente
        input_text = args.input

    # Ejecutar el análisis léxico
    print("### Lexer Output ###")
    tokens, _ = test_lexer(input_text, source='console')

    # Ejecutar el análisis sintáctico
    print("\n### Parser Output ###")
    input_tokens = tokens_to_text(tokens)
    result = test_parser(input_tokens)
    if result:
        print("Analisis sintactico correcto")

if __name__ == '__main__':
    main()
