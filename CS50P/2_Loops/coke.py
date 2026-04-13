def main():
    accepted_coins = [25,10,5]
    owed = 50

    while owed>0:
        print("Amount Due: ", owed)
        pay = int(input("Insert Coin: "))
        #check if inserted coin is among accepted coins
        if pay in accepted_coins:
            # Sutract Pay from Owed
            owed -= pay
            continue
    else:
        print("Change Owed: ",-owed)

main()


