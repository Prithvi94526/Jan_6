# Safe SQLite Query API


This project is a FastAPI web service that lets users query a SQLite database using natural language questions. Instead of writing SQL manually, users can type questions in plain English, and the system uses Google Gemini AI to automatically convert them into SQL queries.

The API includes safety checks to ensure only SELECT statements are allowed, only the users table is queried, only certain columns (id, name, created_at) are accessible, and results are limited to 100 rows to prevent excessive data access.

This makes it easy to explore and retrieve user data safely, without requiring SQL knowledg
