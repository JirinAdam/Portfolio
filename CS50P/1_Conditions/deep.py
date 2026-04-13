def main():
    question = input("What is the answer to THE Great Question of Life, the Universe and Everything? ")
    answer = question.lower().strip()
    if answer == "42" or answer == "forty-two" or answer == "forty two":
        print("Yes")
    else:
        print("No")

main()