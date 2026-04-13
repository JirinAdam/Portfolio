import emoji

def main():
    texmoji = input("Input: ")
    print(emoji.emojize(texmoji, language='alias'))

if __name__ == '__main__':
    main()
