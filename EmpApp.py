from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Homepage.html')


@app.route("/payroll", methods=['GET', 'POST'])
def payroll():
    return render_template('Payroll.html')


@app.route("/payroll/output", methods=['POST'])
def payrollOutput():
    return render_template('PayrollOutput.html')

@app.route("/addemp", methods=['GET', 'POST'])
def addEmp():
    return render_template('AddEmp.html')

@app.route("/addemp/output", methods=['POST'])
def AddEmpOutput():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/attendance", methods=['GET', 'POST'])
def att():
    return render_template('Attendance.html')


@app.route("/attendance/output", methods=['POST'])
def attOutput():
    return render_template('AttendanceOutput.html')

#Leave
@app.route("/leave", methods=['GET', 'POST'])
def leave():
    return render_template('Leave.html')

#LeaveOutput
@app.route("/leave/output", methods=['POST'])
def leaveOutput():
    return render_template('LeaveOutput.html', date = datetime.now())  

#Payroll Calculator
from datetime import datetime

@app.route("/payroll", methods=['GET', 'POST'])
def PayRoll():
    return  render_template('Payroll.html', date = datetime.now())

@app.route("/payroll/results", methods=['GET', 'POST'])
def CalculatePayRoll():

    cursor = db_conn.cursor()
    

    if 'emp_id' in request.form and 'workingHoursPerDay' in request.form and 'totalWorkDays' in request.form:
        emp_id = emp_id = int(request.form.get('emp_id'))
        workingHoursPerDay = int(request.form.get('workingHoursPerDay'))
        totalWorkDays = int(request.form.get('totalWorkDays'))


        #Monthly Salary Formula: totalWorkingHrs * salaryPerHr 

        salaryPerHr = 50
        bonusRate = 0.3
        totalWorkingHrs = workingHoursPerDay * totalWorkDays 
        salary = float(totalWorkingHrs * salaryPerHr) 
        bonus = float(salary * bonusRate)
        totalSalary =  float(salary + bonus)
    
    else:
        print("Data Insufficient!!")
        return render_template('Payroll.html', date=datetime.now())

    return render_template('PayrollOutput.html',date=datetime.now(), emp_id=emp_id, mthSalary = totalSalary, workingHours = totalWorkingHrs ,BonusEarned=bonus)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
