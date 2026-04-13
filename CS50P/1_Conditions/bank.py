def main():
    hello = input("Greetings: ")
    if hello.lower().strip() == "hello":
        print("$0")
    elif hello.lower().strip().startswith("hello"):
        print("$0")
    elif hello.lower().strip().startswith("h"):
        print("$20")
    else:
        print("$100")
main()