from flask import Blueprint, render_template, redirect, url_for, jsonify

def loginPlayer(mydb, request):
    if request.method == "POST":
        data = request.get_json()
        if 'uuid' in data and data['uuid']:
            response_data = {
                'route': 'game-list',
                'uuid': data['uuid'],
                'status': 302
            }
            return jsonify(response_data), 302
        emailAddress = data['emailAddress']
        password = data["password"]
        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM userDetails where email_id ='" + str(emailAddress) + "' and password = '" + str(password) + "';")
        myresult = mycursor.fetchall()
        print(myresult)

        if myresult == []:
            response_data = {
                'route': 'login',
                'status': 302
            }
            return jsonify(response_data), 302
        else:
            response_data = {
                'route': 'game-list',
                'uuid': myresult[0][0],
                'status': 302
            }
            return jsonify(response_data), 302

    else:
        response_data = {
            'route': 'login',
            'status': 302
        }
        return jsonify(response_data), 302