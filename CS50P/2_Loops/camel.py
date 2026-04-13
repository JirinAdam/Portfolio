def main():
    camel_case = input("camelCase: ")
    snake_case = ""
    for l in camel_case:
        if l.isupper():
            snake_case += "_" + l.lower()
        else:
            snake_case += l
    print("snake_case:", snake_case)
main()