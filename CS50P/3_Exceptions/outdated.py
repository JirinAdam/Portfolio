lit_month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def main ():
    while True:
        # title the input to reflect the list format
        date = input("Date: ").title()
        #Check if month is in lit_month
        if any(month in date for month in lit_month):
            try:
                for month in lit_month:
                    if month in date:
                        m = lit_month.index(month) +1
                        # Split the date into parts
                        s_date = date.replace(",", " ").split()
                        # convert to int
                        d = int(s_date[1])
                        y = int(s_date[2])
                        if 1 <= d <= 31:
                            print(f"{y}-{m:02}-{d:02}")
                            return
            except (ValueError, IndexError):
                continue

        else:
            # Handle the MM/DD/YYYY format
            try:
                s_date = date.split("/")
                # convert to int
                m = int(s_date[0])
                d = int(s_date[1])
                y = int(s_date[2])
                if 1 <= m <= 12 and 1 <= d <= 31:
                    print(f"{y}-{m:02}-{d:02}")
                    return
            except (ValueError, IndexError):
                continue

if __name__ == "__main__":
    main()