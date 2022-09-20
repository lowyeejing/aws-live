from flask import Flask, render_template, request
from datetime import datetime, timedelta
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

#Homepage
@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Homepage.html')

#ManageEmployee
@app.route("/emp", methods=['GET', 'POST'])
def manageEmployee():
    return render_template('ManageEmployee.html')

#AddEmployee
@app.route("/addemp", methods=['GET', 'POST'])
def addEmp():
    return render_template('AddEmp.html')

#AddEmployeeOutput
@app.route("/addemp/output", methods=['POST'])
def AddEmpOutput():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, emp_image_file))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Upload image file in S3 #
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

#Attendance
@app.route("/attendance")
def att():
    return render_template('Attendance.html')

#AttendanceCheckIn
@app.route("/attendance/checkIn",methods=['GET','POST'])
def checkIn():

    emp_id = request.form['emp_id']
    check_in = datetime.now()
    check_in = check_in.strftime('%Y-%m-%d %H:%M:%S')
    check_out = " "

    insert_sql = "INSERT INTO attendance VALUES (%s, %s, %s)"
    cursor = db_conn.cursor()

    print ("Check in time:{}",check_in)

    try:
        cursor.execute(insert_sql, (emp_id, check_in, check_out))
        db_conn.commit()
        print("Check In inserted into MySQL...")

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html", id=emp_id, check_in=check_in, check_out=check_out)

#AttendanceOutput
@app.route("/attendance/output", methods=['GET', 'POST'])
def checkOut():
    emp_id = request.form['emp_id']
    check_out = datetime.now()
    check_out = check_out.strftime('%Y-%m-%d %H:%M:%S')

    select_sql = "SELECT check_in FROM attendance WHERE emp_id = %(emp_id)s"

    update_sql = "UPDATE attendance SET check_out = (%(check_out)s) WHERE emp_id = %(emp_id)s"

    cursor = db_conn.cursor()
    # check_in = cursor.execute(select_sql, {'emp_id': emp_id})

    try:
        cursor.execute(select_sql, {'emp_id':emp_id})
        
        LoginTime= cursor.fetchall()
       
        for row in LoginTime:
            check_in = row
            print(check_in[0])

        try:
            cursor.execute(update_sql, {'check_out': check_out ,'emp_id': emp_id})
            db_conn.commit()
            print("Check Out updated into MySQL")
        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("All modification done...")
    return render_template('AttendanceOutput.html', id=emp_id, check_in=check_in[0], check_out=check_out)
    
#SearchEmployee
@app.route("/searchemp")
def searchemp():
    return render_template('SearchEmp.html')

#SearchEmployeeOutput
@app.route("/searchemp/output", methods=['GET','POST'])
def searchempOutput():

    emp_id = request.form['emp_id']
    getRowRecord = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()
        
    try:
        cursor.execute(getRowRecord, { 'emp_id': int(emp_id) })

        for result in cursor:
            print(result)
        

    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()
    
    return render_template("SearchEmpOutput.html",result=result)

#DeleteEmployee
@app.route("/deleteemp", methods=['GET', 'POST'])
def deleteEmp():
    return render_template('DeleteEmp.html')

#DeleteEmployeeOutput
@app.route("/deleteemp/output", methods=['GET', 'POST'])
def deleteEmpOutput():

    emp_id = request.form['emp_id']

    cursor = db_conn.cursor()
    getRowRecord = "DELETE * FROM employee WHERE emp_id = %(emp_id)s" 
   

    try:
        cursor.execute(getRowRecord, {'emp_id':emp_id})

        for result in cursor:
            print(result)
        

    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()

    db_conn.commit()
    return render_template("DeleteEmpOutput.html")  

    #Delete S3 picture
    # emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    # s3 = boto3.resource('s3')

    # try:
    #     s3_client.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
    #     return render_template("DeleteEmp.html",result=result)

    # except Exception as e:
    #     return str(e)

#Leave
@app.route("/leave", methods=['GET', 'POST'])
def leave():
    return render_template('Leave.html')

#LeaveOutput
@app.route("/leave/output", methods=['POST'])
def leaveOutput():

    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    leave_type = request.form['leave_type']
    comment = request.form['comment']
    emp_leave_file = request.files['emp_leave_file']

    startDate = datetime.strptime(start_date, "%Y-%m-%d")
    endDate = datetime.strptime(end_date, "%Y-%m-%d")

    difference = endDate - startDate
    daysLeave = difference + timedelta(1)
    daysLeave = daysLeave.days

    insert_sql = "INSERT INTO empleave VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_leave_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, start_date, end_date, leave_type, comment))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        
        # Uplaod image file in S3 #
        emp_leave_file_name_in_s3 = "emp-id-" + str(emp_id) + "_leave_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_leave_file_name_in_s3, Body=emp_leave_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_leave_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('LeaveOutput.html', date = datetime.now(), name = emp_name, id = emp_id, ttldaysofleave = daysLeave, typeOfLeave = leave_type)  

#Payroll Calculator
from datetime import datetime

@app.route("/payroll", methods=['GET', 'POST'])
def PayRoll():
    return  render_template('Payroll.html', date = datetime.now())

#Payroll Output
@app.route("/payroll/output", methods=['GET', 'POST'])
def CalculatePayRoll():

    cursor = db_conn.cursor()
    

    if 'emp_id' in request.form and 'workingHoursPerDay' in request.form and 'totalWorkDays' in request.form:
        emp_id = emp_id = int(request.form.get('emp_id'))
        workingHoursPerDay = float(request.form.get('workingHoursPerDay'))
        totalWorkDays = int(request.form.get('totalWorkDays'))


        #Monthly Salary Formula: totalWorkingHrs * salaryPerHr 

        salaryPerHr = 50
        bonusRate = 0.3
        totalWorkingHrs = workingHoursPerDay * totalWorkDays 
        salary = float(totalWorkingHrs * salaryPerHr) 
        bonus = salary * bonusRate
        totalSalary = (salary + bonus)
    
    else:
        print("Data Insufficient!!")
        return render_template('Payroll.html', date=datetime.now())

    return render_template('PayrollOutput.html',date=datetime.now(), emp_id=emp_id, mthSalary = totalSalary, workingHours = totalWorkingHrs ,BonusEarned=bonus)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

