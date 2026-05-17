"""
Sample book catalog for the custom vectorizers tutorial.

These are classic software engineering books with rich descriptions
that work well for semantic search demonstrations.
"""

BOOKS = [
    {
        "title": "The Pragmatic Programmer",
        "author": "David Thomas",
        "genre": "Software Development",
        "year": 1999,
        "description": (
            "The Pragmatic Programmer is a guide to becoming a better developer. "
            "It covers topics like career development, architectural thinking, "
            "metaprogramming, and how to write flexible, dynamic programs. "
            "The book emphasizes practical advice, tips, and techniques that "
            "you can apply immediately to improve your coding skills."
        ),
    },
    {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "genre": "Software Development",
        "year": 2008,
        "description": (
            "Clean Code teaches you how to write code that is easy to read, "
            "understand, and maintain. Uncle Bob presents a comprehensive guide "
            "to writing clean functions, proper naming conventions, error handling, "
            "and code formatting. The book includes case studies transforming "
            "bad code into clean code with detailed explanations."
        ),
    },
    {
        "title": "Design Patterns",
        "author": "Gang of Four",
        "genre": "Software Architecture",
        "year": 1994,
        "description": (
            "Design Patterns: Elements of Reusable Object-Oriented Software is "
            "a classic reference for 23 essential design patterns. Written by the "
            "Gang of Four, this book categorizes patterns into creational, "
            "structural, and behavioral groups. Each pattern includes usage "
            "examples, implementation advice, and relationships with other patterns."
        ),
    },
    {
        "title": "Introduction to Algorithms",
        "author": "Cormen, Leiserson, Rivest, Stein",
        "genre": "Computer Science",
        "year": 1990,
        "description": (
            "Introduction to Algorithms, known as CLRS in the field, is a "
            "comprehensive textbook on algorithms and data structures. It covers "
            "sorting, searching, graph algorithms, dynamic programming, and "
            "computational complexity. The book is widely used in university "
            "courses and serves as a reference for practicing engineers."
        ),
    },
    {
        "title": "Structure and Interpretation of Computer Programs",
        "author": "Harold Abelson",
        "genre": "Computer Science",
        "year": 1984,
        "description": (
            "SICP teaches fundamental concepts of programming through Scheme, "
            "covering recursion, abstraction, interpreters, and compilers. "
            "The book emphasizes treating computation as a mathematical "
            "phenomenon while developing deep understanding of how programs work. "
            "It's known for its challenging exercises and elegant approach."
        ),
    },
    {
        "title": "The Mythical Man-Month",
        "author": "Frederick Brooks",
        "genre": "Project Management",
        "year": 1975,
        "description": (
            "The Mythical Man-Month explores the challenges of software project "
            "management. Brooks' famous observation that adding people to a late "
            "project makes it later remains relevant today. The book discusses "
            "scheduling, team organization, and why software development differs "
            "fundamentally from other engineering disciplines."
        ),
    },
    {
        "title": "Refactoring",
        "author": "Martin Fowler",
        "genre": "Software Development",
        "year": 1999,
        "description": (
            "Refactoring is a systematic approach to improving code structure "
            "without changing its behavior. Fowler catalogs dozens of refactoring "
            "patterns, from simple extract method to more complex extractions. "
            "Each pattern includes motivation, procedure, and examples showing "
            "how to safely transform legacy code into cleaner, more maintainable form."
        ),
    },
    {
        "title": "Code Complete",
        "author": "Steve McConnell",
        "genre": "Software Development",
        "year": 2004,
        "description": (
            "Code Complete is a practical guide to software construction. "
            "It covers everything from naming variables and writing conditions "
            "to class design, error handling, and code tuning. McConnell synthesizes "
            "research and best practices into actionable guidance for writing "
            "high-quality, maintainable code across various programming languages."
        ),
    },
]
