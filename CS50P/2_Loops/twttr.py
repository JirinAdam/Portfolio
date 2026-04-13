def main():
    vowels =['a','e','i','o','u','A','E','I','O','U']
    twt = input("Input: ")
    #out = twt()

    for v in twt:
        if v in vowels:
            twt = twt.replace(v,"")

    print("Output:", twt)
if __name__ == "__main__":
    main()