def word_count():
    with open("homework1/task6_read_me.txt", "r", encoding="utf-8") as file:
        contents = file.read()
        words = contents.split()
        return len(words)