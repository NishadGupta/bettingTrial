from flask import Blueprint, render_template, request, flash, redirect, url_for, Flask, jsonify
import uuid

def createGameHandler(mydb, request):
    data = request.get_json()

    if 'uuid' not in data or not data['uuid']:
        response_data = {
            'route': 'login',
            'status': 302
        }
        return jsonify(response_data), 302
    
    if request.method == "GET":
        response_data = {
            'route': 'createGame',
            'uuid': data['uuid'],
            'status': 302
        }
        return jsonify(response_data), 302

    game_uuid = uuid.uuid4()
    numPlayers = data['numPlayers']
    playerList = str([data['uuid']])

    mycursor = mydb.cursor()
    sql = "INSERT INTO gamesIds (gameuuid, playerlist, totalplayers, is_active) VALUES (%s, %s, %s, %s)"
    values = (str(game_uuid), playerList, numPlayers, True)
    mycursor.execute(sql, values)
    mydb.commit()

    response_data = {
        'route': 'joinGameRoom',
        'uuid': data['uuid'],
        'game_uuid': game_uuid,
        'status': 302
    }
    return jsonify(response_data), 302
