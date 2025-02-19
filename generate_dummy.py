import hashlib
from tools import xpath, make_dir, os_scan_walk
from print_text3 import xprint

import names
import random


from pyroDB import PickleTable

DATA_DIR = make_dir('data')

xprint("/y/Generating dummy data for the server/=/")

Dusers = PickleTable(xpath(DATA_DIR, 'users.pdb'))
Dusers.blank_sheet()
print("Users table created")
Dusers.add_columns(['uid', 'username', 'passwordHash', 'email', 'previllage', 'api_key'], exist_ok=True)


# privillage 9 = admin
Dusers.add_row_as_list([0, 'admin', '21232f297a57a5a743894a0e4a801fc3', 'admin@fec.edu.com', 9, 'admin123'])
Dusers.add_row_as_list([2, 'SYSTEM', '202cb962ac59075b964b07152d234b70', 'SYSTEM', 9, 'syskey1245'])
# privillage 999999 = principal
Dusers.add_row_as_list([1, 'principal', '5f4dcc3b5aa765d61d8327deb882cf99', 'principal@fec.edu.com', 999999, 'principal123'])

# privillage 3 = teacher
Dusers.add_row_as_list([101, 'teacher', '5f4dcc3b5aa765d61d8327deb882cf99', 'Patricia Halford', 3, 'Patricia123'])

# privillage 1 = student
ratul = Dusers.add_row_as_list([1001, 'Ratul', 'c918f24cb99ddbdbf84d427cc5d65690', 'ratul840@fec.edu.com', 1, 'student123'])

Dstudents = PickleTable(xpath(DATA_DIR, 'students.pdb'))
Dstudents.blank_sheet()
Dstudents.add_columns(['uid', 'dept', 'student_id', 'wifi_login_count'], exist_ok=True)


Dstudents.add_row_as_list([ratul['uid'], 'CSE', 20222001, 0])


student_id = 20222000

for i in range(1000):
	name = names.get_full_name()
	email = name.replace(' ', '').lower() + '@fec.edu.com'
	password = hashlib.md5((email+'123').encode()).hexdigest()
	uid = i+1002
	Dusers.add_row_as_list([uid, names.get_full_name(), '', email, 1, 'student123'], AD=False)

	dept = random.choice(['CSE', 'EEE', 'BBA', 'ENG', 'LAW', 'PHARMACY'])
	student_id += 1

	Dstudents.add_row_as_list([uid, dept, student_id, 0], AD=False)

Dusers.dump()
Dusers.to_csv()

Dstudents.dump()
Dstudents.to_csv()
xprint("/g/Users data generated/=/")


Dexam_rooms = PickleTable(xpath(DATA_DIR, 'exam_rooms.pdb'))
Dexam_rooms.blank_sheet()
Dexam_rooms.add_columns(["student_id", "room_number", "seat_number"], exist_ok=True)

r100 = 200
r10 = 0
s = 1

print(Dstudents)

for student in Dstudents.rows():
	# each room 20 seats, room starts from 200 (after 210, 300 starts)
	if s == 21:
		r10 += 1
		s = 1
	if r10 == 10:
		r100 += 1
		r10 = 0

	Dexam_rooms.add_row_as_list([student['student_id'], r100 + r10*10, s], AD=False)

	s += 1

Dexam_rooms.dump()
Dexam_rooms.to_csv()
xprint("/g/Exam rooms data generated/=/")






books_with_isbn = [
    ("The Catcher in the Rye", "978-0316769488"),
    ("To Kill a Mockingbird", "978-0061120084"),
    ("1984", "978-0451524935"),
    ("The Great Gatsby", "978-0743273565"),
    ("Moby-Dick", "978-1503280786"),
    ("Pride and Prejudice", "978-1503290563"),
    ("Brave New World", "978-0060850524"),
    ("The Lord of the Rings", "978-0544003415"),
    ("Jane Eyre", "978-1503278196"),
    ("Crime and Punishment", "978-0486415871"),
    ("Wuthering Heights", "978-1505255607"),
    ("War and Peace", "978-1420954306"),
    ("The Odyssey", "978-0140268867"),
    ("The Iliad", "978-0140275360"),
    ("Frankenstein", "978-0486282114"),
    ("Dracula", "978-0486411095"),
    ("Great Expectations", "978-1503275188"),
    ("The Picture of Dorian Gray", "978-0486278079"),
    ("Anna Karenina", "978-0143035008"),
    ("Les Misérables", "978-0451419439"),
    ("A Tale of Two Cities", "978-1503219700"),
    ("The Hobbit", "978-0547928227"),
    ("Fahrenheit 451", "978-1451673319"),
    ("The Stranger", "978-0679720201"),
    ("Catch-22", "978-1451626650"),
    ("Slaughterhouse-Five", "978-0385333849"),
    ("The Brothers Karamazov", "978-0374528379"),
    ("The Grapes of Wrath", "978-0143039433"),
    ("The Old Man and the Sea", "978-0684801223"),
    ("One Hundred Years of Solitude", "978-0060883287"),
    ("Don Quixote", "978-0060934347"),
    ("Madame Bovary", "978-0140449129"),
    ("Beloved", "978-1400033416"),
    ("The Sun Also Rises", "978-0743297332"),
    ("Dune", "978-0441013593"),
    ("The Road", "978-0307387899"),
    ("Lolita", "978-0679723165"),
    ("A Clockwork Orange", "978-0393312836"),
    ("The Metamorphosis", "978-0486290309"),
    ("Ulysses", "978-1840226355"),
    ("The Sound and the Fury", "978-0679732242"),
    ("Gone with the Wind", "978-1451635621"),
    ("The Scarlet Letter", "978-0486280485"),
    ("The Count of Monte Cristo", "978-0140449266"),
    ("The Alchemist", "978-0061122415"),
    ("The Name of the Wind", "978-0756404741"),
    ("The Book Thief", "978-0375842207"),
    ("The Road Less Traveled", "978-0743243155"),
    ("Mere Christianity", "978-0060652920"),
    ("The Art of War", "978-1590302255"),
    ("The Prince", "978-0486272749"),
    ("Meditations", "978-0140449334"),
    ("The Republic", "978-0140455113"),
    ("Thus Spoke Zarathustra", "978-0140441185"),
    ("Beyond Good and Evil", "978-0140449235"),
    ("The Communist Manifesto", "978-1840220964"),
    ("The Wealth of Nations", "978-0553585971"),
    ("The Federalist Papers", "978-0451528810"),
    ("On the Origin of Species", "978-0486450062"),
    ("A Brief History of Time", "978-0553380163"),
    ("The Selfish Gene", "978-0199291151"),
    ("Sapiens", "978-0062316097"),
    ("Homo Deus", "978-0062464347"),
    ("The Gene", "978-1476733524"),
    ("Thinking, Fast and Slow", "978-0374533557"),
    ("The 48 Laws of Power", "978-0140280197"),
    ("The Power of Habit", "978-0812981605"),
    ("Atomic Habits", "978-0735211292"),
    ("Deep Work", "978-1455586691"),
    ("The 7 Habits of Highly Effective People", "978-0743269513"),
    ("How to Win Friends and Influence People", "978-0671027032"),
    ("Rich Dad Poor Dad", "978-1612680194"),
    ("The Lean Startup", "978-0307887894"),
    ("The Four Hour Workweek", "978-0307465351"),
    ("Zero to One", "978-0804139298"),
    ("The Hard Thing About Hard Things", "978-0062273208"),
    ("Good to Great", "978-0066620992"),
    ("Grit", "978-1501111112"),
    ("Mindset", "978-0345472328"),
    ("Drive", "978-1594484804"),
    ("Outliers", "978-0316017930"),
    ("Blink", "978-0316010665"),
    ("The Tipping Point", "978-0316346626"),
    ("Start with Why", "978-1591846444"),
    ("Leaders Eat Last", "978-1591845324"),
    ("Daring Greatly", "978-1592408412"),
    ("The Gifts of Imperfection", "978-1592858490"),
    ("Man's Search for Meaning", "978-0807014271"),
    ("The Subtle Art of Not Giving a F*ck", "978-0062457714"),
    ("Can't Hurt Me", "978-1544512280"),
    ("Extreme Ownership", "978-1250183866"),
    ("Make Your Bed", "978-1455570249")
] + [
    ("Clean Code: A Handbook of Agile Software Craftsmanship", "978-0132350884"),
    ("The Pragmatic Programmer: Your Journey to Mastery", "978-0201616224"),
    ("Design Patterns: Elements of Reusable Object-Oriented Software", "978-0201633610"),
    ("Introduction to Algorithms", "978-0262033848"),
    ("The Mythical Man-Month: Essays on Software Engineering", "978-0201835953"),
    ("Artificial Intelligence: A Modern Approach", "978-0134610993"),
    ("Code Complete: A Practical Handbook of Software Construction", "978-0735619678"),
    ("The Clean Coder: A Code of Conduct for Professional Programmers", "978-0137081073"),
    ("Refactoring: Improving the Design of Existing Code", "978-0201485677"),
    ("The Art of Computer Programming", "978-0201896831"),
    ("Patterns of Enterprise Application Architecture", "978-0321127426"),
    ("The C Programming Language", "978-0131103627"),
    ("The Algorithm Design Manual", "978-1848000698"),
    ("Programming Pearls", "978-0201657883"),
    ("The Art of Software Testing", "978-0471035391"),
    ("The Lean Startup: How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses", "978-0307887894"),
    ("The Pragmatic Programmer: 20th Anniversary Edition", "978-0135957059"),
    ("Design It!: From Programmer to Software Architect", "978-0134757501"),
    ("Programming in Scala", "978-0981531649"),
    ("Effective Java", "978-0134685991"),
    ("C++ Primer", "978-0321714114"),
    ("Structure and Interpretation of Computer Programs", "978-0262011539"),
    ("Introduction to the Theory of Computation", "978-1133187790"),
    ("Modern Operating Systems", "978-0133591620"),
    ("The Rust Programming Language", "978-1593278281"),
    ("The Go Programming Language", "978-0134190440"),
    ("Design Patterns in C++", "978-0135915080"),
    ("Python Crash Course: A Hands-On, Project-Based Introduction to Programming", "978-1593279288"),
    ("Fluent Python: Clear, Concise, and Effective Programming", "978-1491946008"),
    ("JavaScript: The Good Parts", "978-0596517748"),
    ("Functional Programming in Scala", "978-1617290657"),
    ("Effective Modern C++", "978-1491903995"),
    ("The Pragmatic Programmer: From Journeyman to Master", "978-0201616224"),
    ("Programming Ruby: The Pragmatic Programmers' Guide", "978-0979990263"),
    ("HTML and CSS: Design and Build Websites", "978-1118008188"),
    ("Clean Architecture: A Craftsman's Guide to Software Structure and Design", "978-0134494166"),
    ("Computer Networking: A Top-Down Approach", "978-0133594140"),
    ("Operating System Concepts", "978-1118063330"),
    ("TCP/IP Illustrated, Volume 1: The Protocols", "978-0321336317"),
    ("The Pragmatic Programmer: 20th Anniversary Edition", "978-0135957059"),
    ("Artificial Intelligence: Structures and Strategies for Solving Complex Problems", "978-0201895391"),
    ("Computer Organization and Design: The Hardware/Software Interface", "978-0124077263"),
    ("Advanced Programming in the UNIX Environment", "978-0321637734"),
    ("The Art of UNIX Programming", "978-0131424761"),
    ("Learning Python", "978-1449355739"),
    ("Mathematics for Computer Science", "978-0132846965"),
    ("The Principles of Object-Oriented JavaScript", "978-0994113037"),
    ("Mastering Algorithms with C", "978-1565924537"),
    ("Computer Science: An Overview", "978-0133978429"),
    ("Head First Java", "978-0596009205"),
    ("Test-Driven Development: By Example", "978-0321146533"),
    ("Head First Design Patterns", "978-0596007126"),
    ("The Art of Programming", "978-0201896831"),
    ("Cracking the Coding Interview", "978-0984782857"),
    ("Deep Learning", "978-0262035613"),
    ("Python for Data Analysis", "978-1491957660"),
    ("Python Data Science Handbook", "978-1491912058"),
    ("Fluent Python: Clear, Concise, and Effective Programming", "978-1491946008"),
    ("Linux Pocket Guide", "978-1449302443"),
    ("Algorithmic Thinking: A Problem-Based Introduction", "978-0993773007"),
    ("Clean Code: A Handbook of Agile Software Craftsmanship", "978-0132350884"),
    ("The C++ Programming Language", "978-0321563842"),
    ("Introduction to the Theory of Computation", "978-1133187790"),
    ("Automate the Boring Stuff with Python", "978-1593275990"),
    ("Programming Python", "978-1449357016"),
    ("Python for Everybody: Exploring Data in Python 3", "978-1530051122"),
    ("Design Patterns: Elements of Reusable Object-Oriented Software", "978-0201633610"),
    ("Clean Code: A Handbook of Agile Software Craftsmanship", "978-0132350884"),
    ("The Mythical Man-Month", "978-0201835953"),
    ("Introduction to Algorithms", "978-0262033848"),
    ("Artificial Intelligence: A Modern Approach", "978-0134610993"),
    ("Design Patterns", "978-0201633610"),
    ("Python for Data Analysis", "978-1491957660"),
    ("Advanced Programming in the UNIX Environment", "978-0321637734"),
    ("Practical Object-Oriented Design in Ruby", "978-0321721335"),
    ("The Complete Software Developer's Career Guide", "978-0999296946"),
    ("Computer Programming: An Introduction", "978-0201150434"),
    ("The Software Craftsman: Professionalism, Pragmatism, Pride", "978-0134052512"),
    ("The Complete Reference C", "978-0072226812"),
    ("Data Structures and Algorithms in Java", "978-0134670979"),
    ("Eloquent JavaScript: A Modern Introduction to Programming", "978-1593279509"),
    ("Computer Networks", "978-0132856202"),
    ("Python Cookbook", "978-1449357016"),
    ("Fluent Python", "978-1491946008"),
    ("The Art of Computer Programming", "978-0201896831"),
    ("Design and Analysis of Algorithms", "978-0132316811"),
    ("Software Engineering: A Practitioner's Approach", "978-0078022128"),
    ("Head First Python", "978-0596802370"),
    ("Game Programming Patterns", "978-0992119405"),
    ("Computer Graphics: Principles and Practice", "978-0321399526"),
    ("Data Science from Scratch", "978-1491901421"),
    ("The Clean Coder: A Code of Conduct for Professional Programmers", "978-0137081073"),
    ("Data-Driven Science and Engineering", "978-0691152690"),
    ("Machine Learning Yearning", "978-0999737701"),
    ("Machine Learning: A Probabilistic Perspective", "978-0262018026")
]


Dbooks = PickleTable(xpath(DATA_DIR, 'books.pdb'))
Dbooks.blank_sheet()
Dbooks.add_columns(['isbn', 'title', 'stock', 'borrower_uid'], exist_ok=True)

for book in books_with_isbn:
	Dbooks.add_row_as_list([book[1], book[0], random.randint(0, 10)], AD=False)

Dbooks.dump()
Dbooks.to_csv()
xprint("/g/Books data generated/=/")







