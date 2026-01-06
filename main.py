from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import google.generativeai as genai
import os
import re

def run_sql(sql: str):
    connection = sqlite3.connect("db.sqlite")
    cursor = connection.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    connection.close()
    return rows

def nl_to_sql(question: str) -> str:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = f"""Convert the following natural language question into a SQL SELECT query for a SQLite table called "users" with columns "id", "name", "created_at".
    
    Rules:
    - Only generate SELECT queries (no INSERT, UPDATE, DELETE, or DROP)
    - Always include "LIMIT 100" at the end
    - Return only the SQL query, nothing else
    
    Question: {question}
    
    SQL:"""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    sql = response.text.strip()
    if "LIMIT" not in sql.upper():
        sql = sql.rstrip(";") + " LIMIT 100"
    if not sql.endswith(";"):
        sql += ";"
    return sql

def validate_sql(sql: str) -> str:
    sql = sql.strip()
    if ";" in sql:
        raise ValueError("SQL query cannot contain semicolons")
    sql_upper = sql.upper()
    if sql_upper.count("SELECT") > 1:
        raise ValueError("SQL query cannot contain multiple statements")
    if not sql_upper.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    from_match = re.search(r'\bFROM\s+["\']?(\w+)["\']?', sql_upper, re.IGNORECASE)
    if not from_match:
        raise ValueError("SQL query must include a FROM clause")
    table_name = from_match.group(1).lower()
    if table_name != "users":
        raise ValueError(f"Only table 'users' is allowed, found: {table_name}")
    select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql_upper, re.IGNORECASE | re.DOTALL)
    if not select_match:
        raise ValueError("Invalid SELECT statement format")
    columns_str = select_match.group(1)
    if "*" in columns_str:
        pass
    else:
        column_matches = re.findall(r'["\']?(\w+)["\']?', columns_str)
        sql_keywords = {'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'}
        allowed_columns = {'id', 'name', 'created_at'}
        for col in column_matches:
            col_lower = col.lower()
            if col_lower.upper() in sql_keywords:
                continue
            if '.' in col_lower:
                col_lower = col_lower.split('.')[-1]
            if col_lower not in allowed_columns and col_lower not in sql_keywords:
                raise ValueError(f"Column '{col}' is not allowed. Allowed columns: id, name, created_at")
    if "LIMIT" not in sql_upper:
        sql = sql.rstrip() + " LIMIT 100"
    else:
        limit_match = re.search(r'\bLIMIT\s+(\d+)', sql_upper)
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > 100:
                sql = re.sub(r'\bLIMIT\s+\d+', 'LIMIT 100', sql, flags=re.IGNORECASE)
        else:
            sql = re.sub(r'\bLIMIT\b', 'LIMIT 100', sql, flags=re.IGNORECASE)
    return sql

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query")
async def query(request: QueryRequest):
    sql = nl_to_sql(request.question)
    validated_sql = validate_sql(sql)
    rows = run_sql(validated_sql)
    return {"sql": validated_sql, "rows": rows}





