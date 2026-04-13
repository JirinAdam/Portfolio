def main():
    plate = input("Plate: ")
    if is_valid(plate):
        print("Valid")
    else:
        print("Invalid")

# Numbers cannot be used in the middle of a plate; they must come at the end. For example, AAA222 would be an acceptable … vanity plate; AAA22A would not be acceptable.
# The first number used cannot be a ‘0’.”


def is_valid(s):
    # maximum of 6 characters (letters or numbers) and a minimum of 2 characters- DONE
    if len(s) < 2 or len(s) > 6:
        return False
    # No periods, spaces, or punctuation marks are allowed
    if not s.isalnum():
        return False
    # must start with at least two letters (str)
    if not s[0:2].isalpha():
        return False
    # Numbers cannot be used in the middle of a plate; they must come at the end. For example, AAA222 would be an acceptable … vanity plate; AAA22A would not be acceptable.
    first_number_found = False
    for i in range(len(s)):
        if s[i].isdigit():
            if not first_number_found:
                first_number_fount = True
                if s[i] == '0':
                    return False
            if not s[i:].isdigit():
                return False
            break
    return True

main()
