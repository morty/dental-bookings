import os
import psycopg2
import urlparse
from flask import Flask, request

def get_connection():
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

    return conn

app = Flask(__name__)

@app.route("/")
def hello():
    message = request.args.get('message', 'No message')
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO messages (message) VALUES (%s)', (message,))

            cur.execute('SELECT message FROM messages')
            messages = [x[0] for x in cur.fetchall()]
            return "<br>".join(messages)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
