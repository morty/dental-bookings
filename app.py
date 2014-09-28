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
                                uuid, to_char(appointment_date, 'DD-Mon-YYYY'), time_of_day, first_name, last_name, nhs_number, to_char(date_of_birth, 'DD-Mon-YYYY'), tel_no, urgency 
                                allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth
                            FROM patients p 
                            left outer join referrals r on r.patient_id = p.id
                            left outer join appointments a on a.patient_id = p.id
                    """)
                #patients = [", ".join(filter (None, x)) for x in cur.fetchall()]
                #return "<br>".join(patients)
                rows = cur.fetchall()
                html = """
<html>
<head>
<style>
html, *, body {
    font-size: 14px;
    font-family: Arial;
}

th {
    text-align: left;
    vertical-align: top;
}
</style>
</head>
<body>
<table>
"""
                html += "<tr>"
                html += "<th style=\"display: none\">" + "uuid" + "</th>"
                html += "<th colspan=\"2\">" + "Appointment time" + "</th>"
                html += "<th>" + "First Name" + "</th>"
                html += "<th>" + "Last Name" + "</th>"
                html += "<th>" + "NHS no." + "</th>"
                html += "<th>" + "DOB" + "</th>"
                html += "<th>" + "tel_no" + "</th>"
                html += "<th>" + "Allergies" + "</th>"
                html += "<th>" + "Medical history" + "</th>"
                html += "<th>" + "Bleeding disorders?" + "</th>"
                html += "<th>" + "Medications" + "</th>"
                html += "<th>" + "Treatment required" + "</th>"
                html += "<th>" + "Parents aware?" + "</th>"
                html += "<th>" + "Problem teeth" + "</th>"
                html += "</tr>"
                for row in rows:
                    html += "<tr>"
                    for i in range(0, 15):
                        if i == 0:
                            html += "<td style=\"display: none\">" + row[i] + "</td>"
                        else:
                            html += "<td>" + row[i] + "</td>"
                    html += "</tr>"
                html += "</table>"
                html += "</body></html>"
                return Response(html, mimetype='text/html')
    except Exception, err:
        print "Error reading DB"
        print traceback.format_exc()

@app.route('/book', methods=['POST'])
def book_appointment():
    try:
        doc = lxml.etree.fromstring(request.stream.read())

        uuid            = xfirst(doc.xpath('/data/@instance-id'))

        first_name      = xfirst(doc.xpath('/data/Patient/FirstName/text()'))
        last_name       = xfirst(doc.xpath('/data/Patient/LastName/text()'))
        nhs_number      = xfirst(doc.xpath('/data/Patient/NHSNumber/text()'))
        date_of_birth   = xfirst(doc.xpath('/data/Patient/Dob/text()'))
        tel_no          = xfirst(doc.xpath('/data/Patient/ContactTel/text()'))
        urgency         = ''

        allergies           = xfirst(doc.xpath('/data/ReferralDetails/Allergies/text()'))
        medical_history     = xfirst(doc.xpath('/data/ReferralDetails/MedicalHistory/text()'))
        
        bleeding_disorders  = xfirst(doc.xpath('/data/ReferralDetails/BleedingDisorders/text()'))
        medications         = xfirst(doc.xpath('/data/ReferralDetails/Medications/text()'))
        treatment_requested = xfirst(doc.xpath('/data/ReferralDetails/TreatmentRequested/text()'))
        parents_aware_flag  = xfirst(doc.xpath('/data/ReferralDetails/ParentsAware/text()'))

        problem_teeth = ''
        pt_ul               = xfirst(doc.xpath('/data/ReferralDetails/ProblemTeeth/UpperLeft/text()'))
        pt_ur               = xfirst(doc.xpath('/data/ReferralDetails/ProblemTeeth/UpperRight/text()'))
        pt_ll               = xfirst(doc.xpath('/data/ReferralDetails/ProblemTeeth/LowerLeft/text()'))
        pt_lr               = xfirst(doc.xpath('/data/ReferralDetails/ProblemTeeth/LowerRight/text()'))

        if pt_ul != '':
            problem_teeth = 'Upper-left: ' + pt_ul + "\n"
        if pt_ur != '':
            problem_teeth = 'Upper-right: ' + pt_ul + "\n"
        if pt_ll != '':
            problem_teeth = 'Lower-left: ' + pt_ll + "\n"
        if pt_lr != '':
            problem_teeth = 'Lower-right: ' + pt_lr + "\n"



        appointment_date, time_of_day    = doc.xpath('/data/Appointment/ApptDate/text()')[0].split()
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
                  (patient_id, uuid, allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth, referral_date)
                  VALUES
                  (%s, %s, %s, %s, %s, %s, %s, %s, %s, now())
                """
                values = (patient_id, uuid, allergies, medical_history, bleeding_disorders, medications, treatment_requested, parents_aware_flag, problem_teeth)
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
    #from datetime import *
    #today = datetime.today()
    #print today.strftime("%U")

    
    #weeknum = datetime.date().isocalendar()[1]

    



    xml = """
       <AppointmentList>
         <Appointment>
           <ApptDate>01-Oct-2014 (AM)</ApptDate>
         </Appointment>
         <Appointment>
           <ApptDate>01-Oct-2014 (PM)</ApptDate>
         </Appointment>
         <Appointment>
           <ApptDate>08-Oct-2014 (AM)</ApptDate>
         </Appointment>
         <Appointment>
           <ApptDate>08-Oct-2014 (PM)</ApptDate>
         </Appointment>
       </AppointmentList>
    """


    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT to_char(appointment_date, 'DD-Mon-YYYY') as appointment_date, time_of_day, count(*) 
                                FROM appointments
                                WHERE appointment_date >= now()
                                AND appointment_date <= now() + interval '3 months' 
                                GROUP BY to_char(appointment_date, 'DD-Mon-YYYY'), time_of_day
                                HAVING count(*) < 4
                        """)
                xml = '<AppointmentList>'
                #for x in cur.fetchall():
                #    result += x.appointment_date
                rows = cur.fetchall()
                for row in rows:
                    xml += "<Appointment>\n<ApptDate>" + row[0] + " " + row[1] + "</ApptDate></Appointment>"
                xml += '</AppointmentList>'
                    
    except Exception, err:
        print "Error reading DB"
        print traceback.format_exc()
    return Response(xml, mimetype='text/xml')

def xstr(s):
    print s
    return '' if s is None else str(s)

def xfirst(s):
    if s:
        return s[0] 
    return ''

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
