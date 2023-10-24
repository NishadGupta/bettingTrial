from flask import Blueprint, render_template, request, flash, redirect, url_for, Flask, jsonify
import uuid


def registerPlayer(mydb, request):
    if request.method == "POST":
        data = request.get_json()
        emailAddress = data["email"]
        password = data["password"]
        confirmPassword = data["confirmPassword"]
        if password != confirmPassword or len(emailAddress) == 0:
            response_data = {
                'error': 'Invalid email/password',
                'status': 400
            }
            return jsonify(response_data), 400
        
        mycursor = mydb.cursor()
        sql = "SELECT email_id from userDetails"
        mycursor.execute(sql)
        emails = mycursor.fetchall()

        if emailAddress in emails:
            response_data = {
                'error': 'User already registered',
                'status': 400
            }
            return jsonify(response_data), 400

        firstName = data["firstName"]
        lastName = data["lastName"]
        contact = data["contact"]

        if len(firstName) == 0 or len(lastName) == 0 or len(contact) == 0:
            response_data = {
                'error': 'Invalid FirstName/LastName/Password',
                'status': 400
            }
            return jsonify(response_data), 400

        answerOne = data["answerOne"]
        answerTwo = data["answerTwo"]
        answerThree = data["answerThree"]

        if len(answerOne) == 0 or len(answerTwo) == 0 or len(answerThree) == 0:
            response_data = {
                'error': 'Invalid Security Answers',
                'status': 400
            }
            return jsonify(response_data), 400
        
        
        new_uuid = uuid.uuid4() 
        mycursor = mydb.cursor()
        sql = "INSERT INTO userDetails (id, email_id, firstName, lastName, password, contact) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (str(new_uuid), emailAddress, firstName, lastName, password, contact)

        mycursor.execute(sql, values)
        mydb.commit()

        mycursor = mydb.cursor()
        sql = "INSERT INTO resetpassword (email_id, answer_one, answer_two, answer_three) VALUES (%s, %s, %s, %s)"
        values = (emailAddress, answerOne, answerTwo, answerThree)
        mycursor.execute(sql, values)
        mydb.commit()
        response_data = {
            'route': 'login',
            'status': 302
        }
        return jsonify(response_data), 302
    
    return jsonify(), 200