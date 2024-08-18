from flask import Flask, render_template, request, redirect, url_for
import cx_Oracle
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# Database connection details
dsn = cx_Oracle.makedsn("DESKTOP-IT2AN7M", 1521, service_name="xe")
connection = cx_Oracle.connect(user="system", password="gopi9392", dsn=dsn)

# Function to send email
def send_email(to_email, subject, body):
    from_email = "gopisankarnelluri22@gmail.com"
    password = "uvrq czls jjdn fylj"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())

@app.route('/')
def index():
    return render_template('role.html')

@app.route('/submit', methods=['POST'])
def submit():
    role = request.form['role']
    if role == 'requester':
        return redirect(url_for('requester_form'))
    elif role == 'supporting_team':
        return redirect(url_for('supporter_form'))
    elif role == 'dashboard':
        return render_template('dashboard.html')
    return redirect(url_for('index'))

@app.route('/requester', methods=['GET', 'POST'])
def requester_form():
    if request.method == 'POST':
        email = request.form['email']
        name = request.form['name']
        department = request.form['department']
        problem_category = request.form['problem_category']
        to_mail = request.form['to_mail']
        problem_description = request.form['problem_description']
        
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO problems1 (email, name, department, problem_category, to_mail, problem_description, submitted_date)
            VALUES (:email, :name, :department, :problem_category, :to_mail, :problem_description, CURRENT_TIMESTAMP)
            RETURNING problem1_id INTO :problem1_id
            """
            problem1_id_var = cursor.var(int)
            cursor.execute(sql, {
                'email': email,
                'name': name,
                'department': department,
                'problem_category': problem_category,
                'to_mail': to_mail,
                'problem_description': problem_description,
                'problem1_id': problem1_id_var
            })
            problem1_id = problem1_id_var.getvalue()
            connection.commit()
        
        # Send email to user
        send_email(email, 'WE HAVE RECEIVED YOUR PROBLEM', f'Your problem has been submitted successfully regarding {problem_description}. Your problem ID is {problem1_id}.\nwe will solve it soon.\n\nbest regards,\nnarasaraopeta engineering college,\nnarasaraopeta.')

        # Send email to the selected recipient
        send_email(to_mail, 'New Problem Submitted', f'A new problem has been submitted by {name} with the Problem ID: {problem1_id} regarding {problem_description}\nPLEASE SOLVE IT SOON.\n\nbest regards,\nnarasaraopeta engineering college,\n narasaraopeta.')

        return redirect(url_for('index'))

    return render_template('requester.html')

@app.route('/supporter', methods=['GET', 'POST'])
def supporter_form():
    if request.method == 'POST':
        problem1_id = request.form['problem_id']
        status = request.form['status']
        remarks = request.form['remarks']

        with connection.cursor() as cursor:
            # Fetch email of the requester using the problem1_id
            sql = "SELECT email FROM problems1 WHERE problem1_id = :problem1_id"
            cursor.execute(sql, {'problem1_id': problem1_id})
            result = cursor.fetchone()
            if result:
                requester_email = result[0]
                
                # Update the problem status, remarks, and cleared_date
                sql_update = """
                UPDATE problems1
                SET status = :status, remarks = :remarks, cleared_date = CASE WHEN :status = 'CLEARED' OR :status = 'RESOLVED' THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE problem1_id = :problem1_id
                """
                cursor.execute(sql_update, {
                    'status': status,
                    'remarks': remarks,
                    'problem1_id': problem1_id
                })
                connection.commit()
                
                # Send email to the requester
                send_email(requester_email, 'Problem Status Update', f'Your problem with ID {problem1_id} has been {status}.\nTHANK U FOR YOUR COOPERATION\n\nbest regards,\nnarasaraopeta engineering college,\n narasaraopeta.')

        return redirect(url_for('index'))

    return render_template('supporter.html')

@app.route('/search', methods=['GET'])
def search():
    status = request.args.get('status')

    # Query to fetch problems based on status
    if status == 'CLEARED' or status == 'RESOLVED':
        query = """
        SELECT submitted_date, problem1_id, problem_category, problem_description, cleared_date 
        FROM problems1 
        WHERE status = 'CLEARED' OR status = 'RESOLVED'
        """
    elif status == 'NOT_CLEARED':
        query = """
        SELECT submitted_date, problem1_id, problem_category, problem_description, NULL as cleared_date 
        FROM problems1 
        WHERE status IS NULL OR status != 'CLEARED'
        """
    else:
        query = """
        SELECT submitted_date, problem1_id, problem_category, problem_description, cleared_date 
        FROM problems1
        """

    cursor = connection.cursor()
    cursor.execute(query)
    problems = cursor.fetchall()
    cursor.close()

    return render_template('results.html', problems=problems, status=status)

if __name__ == '__main__':
    app.run(port=5000)
