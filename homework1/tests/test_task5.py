from homework1.src.task5 import book_list, student_dict

def test_books():
    assert book_list() == ["To Kill a Mocking Bird by Harper Lee", "Pride and Prejudice by Jane Austen", "The Great Gatsby by F. Scott Fitzgerald"]

def test_student1():
    students = student_dict()
    assert students.get(1001) == "Chase"

def test_student5():
    students = student_dict()
    assert students.get(1005) == "Fable"

def test_student10():
    students = student_dict()
    assert students.get(1010) == "Sol"