def main():
    """Ask for input of File name"""
    file_name = input("File name: ").lower().strip()

    """Conditions to print output of file type"""
    if file_name.endswith(".pdf"):
        print("application/pdf")
    elif file_name.endswith(".zip"):
        print("application/zip")
    elif file_name.endswith(".gif"):
        print("image/gif")
    elif file_name.endswith(".png"):
        print("image/png")
    elif file_name.endswith(".jpg") or file_name.endswith(".jpeg"):
        print("image/jpeg")
    elif file_name.endswith(".txt"):
        print("text/plain")
    else:
        print("application/octet-stream")

main()