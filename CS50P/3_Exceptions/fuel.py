def main():
    while True:
        fuel = input("Fraction: ")
        fraction = fraction_to_percentage(fuel)
        if fraction:
            print(fraction)
            break

def fraction_to_percentage(fraction_str):
    if '/' not in fraction_str:
        return
    x, y = fraction_str.split('/')
    if x > y or y == 0:
        return
    try:
        x,y = int(x), int(y)
    except ValueError:
        return
    except ZeroDivisionError:
        return

    percentage = (int(x) / int(y)) * 100
    if 1 >= percentage:
        return("E")
    elif 99 < percentage:
        return("F")
    else:
        return f"{round(percentage)}%"

main()


