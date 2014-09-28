import traceback
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
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT 
                                first_name, last_name, nhs_number, to_char(date_of_birth, 'DD-Mon-YYYY'), tel_no, urgency 
                                patient_id, allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth
                            FROM patients p left outer join referrals r on r.patient_id = p.id""")
                patients = [", ".join(filter (None, x)) for x in cur.fetchall()]
                return "<br>".join(patients)
    except Exception, err:
        print "Error reading DB"
        print traceback.format_exc()

@app.route('/book', methods=['POST'])
def book_appointment():
    try:
        doc = lxml.etree.fromstring(request.stream.read())
        first_name      = doc.xpath('/data/Patient/FirstName/text()')[0]
        last_name       = doc.xpath('/data/Patient/LastName/text()')[0]
        nhs_number      = doc.xpath('/data/Patient/NHSNumber/text()')[0]
        date_of_birth   = doc.xpath('/data/Patient/Dob/text()')[0]
        tel_no          = doc.xpath('/data/Patient/ContactTel/text()')[0]
        urgency         = doc.xpath('/data/Patient/Urgency/text()')[0]

        allergies           = doc.xpath('/data/ReferralDetails/Allergies/text()')[0]
        medical_history     = doc.xpath('/data/ReferralDetails/MedicalHistory/text()')[0]
        bleeding_disorders  = doc.xpath('/data/ReferralDetails/BleedingDisorders/text()')[0]
        medications         = doc.xpath('/data/ReferralDetails/Medications/text()')[0]
        treatment_requested = doc.xpath('/data/ReferralDetails/TreatmentRequested/text()')[0]
        parents_aware_flag  = doc.xpath('/data/ReferralDetails/ParentsAware/text()')[0]
        problem_teeth       = doc.xpath('/data/ReferralDetails/ProblemTeeth/text()')[0] 

        appointment_date    = doc.xpath('/data/Appointment/ApptDate/text()')[0] 
        time_of_day         = doc.xpath('/data/Appointment/Clinic/text()')[0] 
    except Exception, err:
        print "Error parsing XML"
        print traceback.format_exc()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                  INSERT INTO patients
                  (first_name, last_name, nhs_number, date_of_birth, tel_no, urgency)
                  VALUES
                  (%s, %s, %s, %s, %s, %s)
			      RETURNING id
                """
                values = (first_name, last_name, nhs_number, date_of_birth, tel_no, urgency)
                cur.execute(query, values)
                patient_id = cur.fetchone()[0]		
                print "patient_id is %s\n" , patient_id
    except Exception, err:
        print "Error writing patient"
        print traceback.format_exc()


    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                  INSERT INTO referrals
                  (patient_id, allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth, referral_date)
                  VALUES
                  (%s, %s, %s, %s, %s, %s, %s, %s, now())
                """
                values = (patient_id, allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth)
                cur.execute(query, values)
    except Exception, err:
        print "Error writing referral"
        print traceback.format_exc()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                  INSERT INTO appointments
                  (patient_id, appointment_date, time_of_day)
                  VALUES
                  (%s, %s, %s)
                """
                values = (patient_id, appointment_date, time_of_day)
                cur.execute(query, values)
    except Exception, err:
        print "Error writing referral"
        print traceback.format_exc()
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
