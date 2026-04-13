def main():
    face_converted = convert()
    print(face_converted)

def convert():
    face = input("How you doing today ? ")
    return face.replace(':)','🙂').replace(':(','🙁')

main()