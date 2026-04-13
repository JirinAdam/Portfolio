def main():
    what_time = input("What time is it? ")
    time_int = convert(what_time)
    #print(time_int)

    if 7 <= time_int <= 8:
        print("breakfast time")
    elif 12 <= time_int <= 13:
        print("lunch time")

    elif 18 <= time_int <= 19:
        print("dinner time")

    else:
        return  # This will exit the function without printing anything


def convert(time):
    hours, minutes = time.split(":")
    hours = int(hours)
    minutes = int(minutes)

    #convert minutes to Decimal
    minutes = minutes/60

    #convert time to decimal 
    time_now = hours + minutes
    return time_now

if __name__ == "__main__":
    main()


