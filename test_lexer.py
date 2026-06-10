import lexer

def test_lexer(input_text, source='console'):
    lexer.lexer.input(input_text)
    tokens = []
    while True:
        token = lexer.lexer.token()
        if not token:
            break
        token.lexpos = lexer.find_column(input_text, token)
        tokens.append(token)
        if source == 'console':
            print(f"LexToken({token.type}, '{token.value}', {token.lineno}, {token.lexpos})")
    errors = lexer.lexer.errors
    return tokens, errors


def tokens_to_text(tokens):
    return ' '.join(str(token.value) for token in tokens)


# Solo se ejecuta si se llama directamente desde consola
if __name__ == '__main__':
    import argparse
    from sintac import parse_code

    parser = argparse.ArgumentParser(description='Lexer/Parser Test Script')
    parser.add_argument('input', type=str, help='Texto o ruta de archivo')
    args = parser.parse_args()

    try:
        with open(args.input, 'r') as f:
            input_text = f.read()
    except FileNotFoundError:
        input_text = args.input

    print("### Lexer Output ###")
    tokens, _ = test_lexer(input_text, source='console')

    print("\n### Parser Output ###")
    result, errors = parse_code(tokens_to_text(tokens))
    if result:
        print("Análisis sintáctico correcto")
    for e in errors:
        print(e)