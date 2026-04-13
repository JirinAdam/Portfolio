# Output the user’s grocery list in all uppercase
# Sorted alphabetically by item
# Prefixing each line with the number of times the user inputted that item. No need to pluralize the items.
#--Treat the user’s input case-insensitively.

def main():
    shoplist = {}

    try:
        while True:
            # Get input from user (convert to uppercase for consistency)
            item = input().upper()
            # Check if item is already in the list
            if item in shoplist:
                # If it is, increment its count
                shoplist[item] += 1
                # If not, add it to the list with a count of 1
            else:
                shoplist[item] = 1
                # Sort the list alphabetically
            #shoplist = sorted(shoplist)

    except EOFError:
        # Print the list in all uppercase, with counts and sorted alphabetically
        for item in sorted(shoplist.keys()):
            print(f"{shoplist[item]} {item}")


main()
