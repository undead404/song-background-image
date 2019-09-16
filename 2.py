from tkinter import *
from tkinter import ttk

names = []
options = [("Да", 1), ("Нет", 2)]
point = 0


def start(event):
        # If you use `global` something went wrong
    global names
    # consider switching to object-oriented approach instead of using global variables
    user = name_ent.get()
    names.append(user)
    print(names)
    new_window()


def select():
    global point
    l = option.get()
    if l == 1:
        point += 1
    elif l == 2:
        point += 2
    print(point)


def new_window():
    global options
    global language
    global option

    # Even the var name 'root' is gonna notify you
    # that there should be only one root.
    # Consider alternatives
    root1 = Tk()
    root1.title("Тест Айзенка")
    root1.geometry("600x700")

    description = Label(root1,
                        text="Вам предлагается ответить на 57 вопросов. Вопросы направлены на выявление\nвашего обычного способа поведения. Постарайтесь представить типичны ситуации\nи дайте первый «естественный» ответ, который придет вам в голову.",
                        justify=LEFT,
                        padx=15, pady=10)
    description.grid(row=0, column=0, sticky=W)

    option = IntVar()

    row = 1
    for txt, val in options:
        Radiobutton(root1, text=txt, value=val, variable=option, padx=15, pady=10, command=select)\
            .grid(row=row, sticky=W)
        row += 1

    sel = Label(root1, padx=15, pady=10)
    sel.grid(row=row, sticky=W)


# Wrap main part
# in `if __name__ == '__main__':` block
root = Tk()
root.title("Тест Айзенка")
root.geometry("600x320")

# Better take file name from CLI parameters
image = PhotoImage(file="image.gif")
image1 = Label(root, image=image)
image1.grid(column=1, row=0, padx=130)

text = Label(root, text="Пройди тест и узнай свой темперамент",
             font="Helvetica 20")
text.grid(row=2, column=1, pady=10)

name = Label(root, text="Введи свое имя", font="Helvetica 14")
name.grid(column=1, row=3, sticky=W, padx=65, pady=20)

name_ent = Entry(root, width=25, font="Helvetica 14")
name_ent.grid(column=1, row=3, sticky=E, pady=20, padx=70)

start_btn = ttk.Button(root, text="НАЧАТЬ ТЕСТ")
start_btn.grid(column=1, row=4, pady=10, padx=130)

start_btn.bind("<Button-1>", start)


root.mainloop()
