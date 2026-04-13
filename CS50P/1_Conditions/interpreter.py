def main():
    """ask for input of expression"""
    """have the input str swithced to float with 1 decimal"""
    """Output float result"""
    expresion = input("Expression: ")
    x, y, z = expresion.split(" ")
    x = float(x)
    z = float(z)
    if y == "+":
        result = x + z

    elif y == "-":
        result = x - z
    elif y == "*":
        result = x * z

    else:
        result = x / z
    print(round(result,1))

main()

