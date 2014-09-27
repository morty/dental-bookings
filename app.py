import os
import psycopg2
import urlparse
import lxml.etree
from flask import Flask, Response, request

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
            cur.execute("SELECT first_name, last_name, nhs_number, to_char(date_of_birth, 'DD-Mon-YYYY'), tel_no, urgency FROM patients")
            patients = [", ".join(x) for x in cur.fetchall()]
            return "<br>".join(patients)

@app.route('/book', methods=['POST'])
def book_appointment():
    doc = lxml.etree.fromstring(request.stream.read())
    first_name = doc.xpath('/data/Patient/FirstName/text()')[0]
    last_name = doc.xpath('/data/Patient/LastName/text()')[0]
    nhs_number = doc.xpath('/data/Patient/NHSNumber/text()')[0]
    date_of_birth = doc.xpath('/data/Patient/Dob/text()')[0]
    tel_no = doc.xpath('/data/Patient/ContactTel/text()')[0]
    urgency = doc.xpath('/data/Patient/Urgency/text()')[0]

    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """
              INSERT INTO patients
              (first_name, last_name, nhs_number, date_of_birth, tel_no, urgency)
              VALUES
              (%s, %s, %s, %s, %s, %s)
            """
            values = (first_name, last_name, nhs_number, date_of_birth, tel_no, urgency)
            cur.execute(query, values)
    return "OK"

@app.route("/appointments")
def get_appointments():
    xml = """
       <AppointmentList>
         <Appointment>
           <Date>2014-10-01</Date>
           <Time>AM</Time>
           <Title>01-Oct-2014 (AM)</Title>
         </Appointment>
         <Appointment>
           <Date>2014-10-01</Date>
           <Time>PM</Time>
           <Title>01-Oct-2014 (PM)</Title>
         </Appointment>
         <Appointment>
           <Date>2014-10-08</Date>
           <Time>AM</Time>
           <Title>08-Oct-2014 (AM)</Title>
         </Appointment>
         <Appointment>
           <Date>2014-10-08</Date>
           <Time>PM</Time>
           <Title>08-Oct-2014 (PM)</Title>
         </Appointment>
       </AppointmentList>
    """
    return Response(xml, mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
