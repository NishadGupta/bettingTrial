from flask import Blueprint, render_template, request, flash, redirect, url_for, Flask, jsonify
from flask_cors import CORS, cross_origin
from model.registerPlayer import registerPlayer
from model.loginPlayer import loginPlayer
from model.createGameHandler import createGameHandler
import mysql.connector
from datetime import datetime
from PIL import Image
import json
import os
import ast
import uuid
import random
import ast
# import marketplace

from flask_socketio import SocketIO, emit, join_room, close_room, leave_room #, rooms, leave_room

mydb = mysql.connector.connect(
    user="Nishad", 
    password="Game@1998",
    host="betting-game.mysql.database.azure.com",
    port=3306,
    database="bettinggame", 
    ssl_ca="DigiCertGlobalRootCA.crt.pem", 
    ssl_disabled=False
    )

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

route_users = {}
game_bets = {}

# Migrate the below to redis later
user_game_sid_map = {} # key = (game_uuid, player_uuid), value = user's sid
game_reward = {} # key = game_uuid, value = game's final reward

@app.route("/")
@cross_origin()
def index():
    return loginPlayer(mydb, request)

@app.route('/game/<route>')
def game(route):
    return render_template('game.html', route=route)

# @app.route('/test',  methods = ["GET", "POST"])
# def test():
#     if request.method == "GET":
#         return render_template("test.html")
#     else:
#         return redirect(url_for('game', route=1))

@app.route("/registerPlayer",  methods = ["GET", "POST"])
@cross_origin()
def register():
    return registerPlayer(mydb, request)
    
@app.route("/loginPlayer",  methods = ["GET", "POST"])
@cross_origin()
def login():
    return loginPlayer(mydb, request)

@app.route("/bet", methods=["POST"])
def bet():
    if request.method == "POST":
        user_bet = request.form["bet"]
        coin_toss_result = random.choice(["heads", "tails"])

        if user_bet == coin_toss_result:
            result = "You win!"
        else:
            result = "You lose."

        return render_template("result.html", user_bet=user_bet, result=result, coin_toss_result=coin_toss_result)
    
@app.route('/makeBets/<route>', methods=["GET", "POST"])
def makeBets(route):
    if request.method == "POST":
        emailAddress = request.form.get("email")
        password = request.form.get("password")

        print(emailAddress, password)
        game_bets.append((emailAddress, password))
        print(route, 'game bets', game_bets)
        # user_bet = request.form["bet"]
        # coin_toss_result = random.choice(["heads", "tails"])

        # if user_bet == coin_toss_result:
        #     result = "You win!"
        # else:
        #     result = "You lose."

        return render_template("result.html", user_bet=1, result=1, coin_toss_result=1)
    print("~~~~~~ MAKE YOUR BETS ~~~~~~~")
    return render_template("makeBets.html")

@app.route('/winner', methods=["GET"])
def winner():
    return render_template("winner.html")

@app.route('/loser', methods=["GET"])
def loser():
    return render_template("loser.html")

@socketio.on('determine_winner')
def determine_winner():
    route = request.args.get('route')

@socketio.on('connect')
def handle_connect():
    route = request.args.get('route')
    print('Connected, args route = ', route)

@socketio.on('join')
def join(route_info):
    r = request.args.get('route')
    print('args route', r)
    route = route_info['route']
    if route not in route_users:
        route_users[route] = []

    if len(route_users[route]) < 3:
        route_users[route].append(request.sid)
        print(route_users)
        join_room(route)
        emit('message', {'data': 'Connected', 'count': len(route_users[route])}, room=r)
        print('route', route, 'num users', route_users[route])
        if len(route_users[route]) == 3:
            print('here')
            emit('start_game', {'route': route}, broadcast=True, room=route)
            # return redirect(url_for('login'))
    else:
        emit('message', {'data': 'Room full. Cannot join.'})

# @app.route("/createGame", methods = ["GET", "POST"])
@socketio.on('createGame')
def createGame(data):
    # return createGameHandler(mydb, request)
    mydb = mysql.connector.connect(
    user="Nishad", 
    password="Game@1998",
    host="betting-game.mysql.database.azure.com",
    port=3306,
    database="bettinggame", 
    ssl_ca="DigiCertGlobalRootCA.crt.pem", 
    ssl_disabled=False
    )

    if 'uuid' not in data or not data['uuid']:
        response_data = {
            'route': 'login',
            'status': 302
        }
        emit('redirect-to-login', response_data, broadcast=False)
    
    else:
        game_uuid = uuid.uuid4()
        numPlayers = data['numPlayers']
        balance = data['balance']
        playerList = str([data['uuid']])
        mycursor = mydb.cursor()
        sql = "INSERT INTO gamesDetail (gameuuid, playerlist, totalplayers, balance, is_active) VALUES (%s, %s, %s, %s, %s)"
        values = (str(game_uuid), playerList, numPlayers, balance, True)
        mycursor.execute(sql, values)
        mydb.commit()

        # Maintain player-game-sid map
        user_game_sid_map[(game_uuid, data['uuid'])] = request.sid

        response_data = {
            'route': 'game/'+str(game_uuid),
            'uuid': data['uuid'],
            'game_uuid': str(game_uuid),
            'status': 302
        }
        
        join_room(game_uuid)
        emit('lobby', response_data, broadcast=False)

@socketio.on('listGames')
def listGames(data):

    if 'uuid' not in data or not data['uuid']:
        # response_data = {
        #         'route': 'login',
        #         'status': 302
        #     }
        # return (response_data), 302
        pass # Socket emit not logged in
    mydb = mysql.connector.connect(
    user="Nishad", 
    password="Game@1998",
    host="betting-game.mysql.database.azure.com",
    port=3306,
    database="bettinggame", 
    ssl_ca="DigiCertGlobalRootCA.crt.pem", 
    ssl_disabled=False
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM gamesDetail")
    games = mycursor.fetchall()
    # print(games)
    games_list = []
    for game in games:
        add_game = {}
        if game[4]:
            add_game[game[0]] = {}
            add_game[game[0]] = {
                'totalPlayers': game[2],
                'currentPlayers': len(ast.literal_eval(game[1]))
            }
            games_list.append(add_game)
    response_data = {
        'uuid': data['uuid'],
        'games_list': games_list,

    }
    emit('get_games_list', response_data, broadcast=False)

    # gameRooms = { roomNumber: len(route_users[roomNumber]) for roomNumber in route_users }
    # emit('get_games_list', { 'rooms': gameRooms, 'user': request.sid }, broadcast=False)

# @app.route("/selectGame", methods = ["POST"])
@socketio.on("selectGame")
def selectGame(data):
    # data = request.get_json()
    # print('selected room', data)
    mydb = mysql.connector.connect(
    user="Nishad", 
    password="Game@1998",
    host="betting-game.mysql.database.azure.com",
    port=3306,
    database="bettinggame", 
    ssl_ca="DigiCertGlobalRootCA.crt.pem", 
    ssl_disabled=False
    )
    if 'uuid' not in data or not data['uuid']:
        response_data = {
                'route': 'login',
                'status': 302
            }
        # return (response_data), 302
        emit('redirect-to-login', response_data, broadcast=False)

    else:
        game_uuid = data['game_uuid']

        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM gamesDetail WHERE gameuuid=%s", (game_uuid,))
        myresult = mycursor.fetchall()

        totalPlayers = myresult[0][2]
        currentPlayers = len(ast.literal_eval(myresult[0][1])) + 1

        if myresult[0][4]:
            mycursor = mydb.cursor()
            
            playersList = ast.literal_eval(myresult[0][1])
            playersList.append(data['uuid'])
            playersList = str(playersList)
            join_room(game_uuid)

            sql1 = "UPDATE gamesDetail SET playerlist = %s WHERE gameuuid = %s"
            val1 = (playersList, game_uuid)

            mycursor.execute(sql1, val1)
            mydb.commit()

            # Maintain player-game-sid map
            user_game_sid_map[(game_uuid, data['uuid'])] = request.sid

            response_data = {
                'uuid': data['uuid'],
                'game_uuid': game_uuid,
                'route': 'game/'+str(game_uuid),
                'status': 302,
                'balance': myresult[0][3]
            }

            if totalPlayers == currentPlayers:
                sql2 = "UPDATE gamesDetail SET is_active = %s WHERE gameuuid = %s"
                val2 = (False, game_uuid)
                mycursor.execute(sql2, val2)
                mydb.commit()

                for player in ast.literal_eval(playersList):
                    sql3 = "INSERT INTO playerbalances (playeruuid, gameuuid, balance, is_active, skip_round, currentbet, has_bet) VALUES (%s, %s, %s, %s, %s, %s, %s);"
                    val3 = (player, game_uuid, myresult[0][3], True, False, 0, False)
                    mycursor.execute(sql3, val3)
                    mydb.commit()

                emit('start-game', response_data, room=game_uuid, broadcast=True)
            # return jsonify(response_data), 302
            else:
                emit('lobby', response_data, broadcast=False)

        else:
            response_data = {
            'uuid': data['uuid'],
            'refresh': True,
            'status': 402
            }
            # return jsonify(response_data), 402
            emit('refresh', response_data, broadcast=False)

            # return redirect(url_for('game', route=str(data)), code=302)
            # return {'url': 'game/'+str(data)}


# @socketio.on('disconnect')
# def handle_disconnect():
#     route = request.args.get('route')
#     if route in route_users:
#         route_users[route].remove(request.sid)
#         emit('message', {'data': 'Disconnected', 'count': len(route_users[route])}, room=route)


# @socketio.on('chat_message')
# def handle_message(data):
#     route = request.args.get('route')
#     emit('chat_message', {'data': data['data'], 'user': request.sid}, broadcast=True, room=route)

@socketio.on('place_bets')
def place_bets(data):
    if 'uuid' not in data or not data['uuid']:
        response_data = {
                'route': 'login',
                'status': 302
            }
        # return (response_data), 302
        emit('redirect-to-login', response_data, broadcast=False)
    
    mydb = mysql.connector.connect(
    user="Nishad", 
    password="Game@1998",
    host="betting-game.mysql.database.azure.com",
    port=3306,
    database="bettinggame", 
    ssl_ca="DigiCertGlobalRootCA.crt.pem", 
    ssl_disabled=False
    )

    game_uuid = data['game_uuid']
    mycursor = mydb.cursor()

    # Place current player's bet and update balance
    mycursor.execute("SELECT * FROM playerbalances WHERE gameuuid=%s AND playeruuid=%s", (game_uuid, data['uuid']))
    currentPlayer = mycursor.fetchall()[0]
    # new_balance = int(currentPlayer[2]) - data['bet']
    # mycursor.execute("UPDATE playerbalances SET has_bet=%s, currentbet=%s, balance=%s WHERE playeruuid=%s AND gameuuid=%s", (True, data['bet'], new_balance, data['uuid'], game_uuid))
    mycursor.execute("UPDATE playerbalances SET has_bet=%s, currentbet=%s WHERE playeruuid=%s AND gameuuid=%s", (True, data['bet'], data['uuid'], game_uuid))
    mydb.commit()

    # Update total game reward - accumulation of all the bets placed so far
    game_reward[game_uuid] = data['bet'] if game_uuid not in game_reward else game_reward[game_uuid] + data['bet']

    # Check if all players have placed bets
    mycursor.execute("SELECT * FROM playerbalances WHERE gameuuid = %s AND is_active = %s AND skip_round = %s;", (game_uuid, True, False))
    playerBetDetails = mycursor.fetchall()
    totalPlayersCount = len(playerBetDetails) # Total players in a given round
    playersBetsPlaced = list(filter(lambda li: li[-1] == 1, playerBetDetails))
    playersBetsCount = len(playersBetsPlaced)

    winning_uuids = []
    losing_uuids = []

    if playersBetsCount == totalPlayersCount:
        skipper_uuid = ''
        max_bet = -1
        for index in range(0, len(playersBetsPlaced), 2):
            if playersBetsPlaced[index][-2] > playersBetsPlaced[index+1][-2]:
                # Set Winner
                mycursor.execute("UPDATE playerbalances SET balance=%s WHERE playeruuid=%s AND gameuuid=%s", (playersBetsPlaced[index][2] - playersBetsPlaced[index][-2], playersBetsPlaced[index][0], game_uuid))
                mydb.commit()
                winning_uuids.append(playersBetsPlaced[index][0])

                # Set Loser
                mycursor.execute("UPDATE playerbalances SET balance=%s, is_active=%s WHERE playeruuid=%s AND gameuuid=%s", (playersBetsPlaced[index+1][2] - playersBetsPlaced[index+1][-2], False, playersBetsPlaced[index+1][0], game_uuid))
                mydb.commit()
                losing_uuids.append(playersBetsPlaced[index+1][0])

                # Find Round Skipper
                if playersBetsPlaced[index][-2] > max_bet:
                    max_bet = playersBetsPlaced[index][-2]
                    skipper_uuid = playersBetsPlaced[index][0]
            else:
                # Set Winner
                mycursor.execute("UPDATE playerbalances SET balance=%s WHERE playeruuid=%s AND gameuuid=%s", (playersBetsPlaced[index+1][2] - playersBetsPlaced[index+1][-2], playersBetsPlaced[index+1][0], game_uuid))
                mydb.commit()
                winning_uuids.append(playersBetsPlaced[index+1][0])

                # Set Loser
                mycursor.execute("UPDATE playerbalances SET balance=%s, is_active=%s WHERE playeruuid=%s AND gameuuid=%s", (playersBetsPlaced[index][2] - playersBetsPlaced[index][-2], False, playersBetsPlaced[index][0], game_uuid))
                mydb.commit()
                losing_uuids.append(playersBetsPlaced[index][0])

                # Find Round Skipper
                if playersBetsPlaced[index+1][-2] > max_bet:
                    max_bet = playersBetsPlaced[index+1][-2]
                    skipper_uuid = playersBetsPlaced[index+1][0]
        
        # Update current round skipper to not skip the next round if there exists such a player
        mycursor.execute("SELECT * FROM playerbalances WHERE gameuuid = %s AND is_active = %s AND skip_round = %s;", (game_uuid, True, True))
        skippedPlayer = mycursor.fetchall()
        if len(skippedPlayer):
            skippedPlayer = skippedPlayer[0]
            mycursor.execute("UPDATE playerbalances SET skip_round=%s WHERE playeruuid=%s AND gameuuid=%s", (False, skippedPlayer[0], game_uuid))
            mydb.commit()
        else:
            skippedPlayer = None

        # Update current round's max bet player to skip the next round only if number of players is greater than 2
        if totalPlayersCount > 2:
            mycursor.execute("UPDATE playerbalances SET skip_round=%s WHERE playeruuid=%s AND gameuuid=%s", (True, skipper_uuid, game_uuid))
            mydb.commit()
        if skippedPlayer is not None:
            winning_uuids.discard(skippedPlayer[0])

        # Broadcast loss to players who lost
        losing_sids = [user_game_sid_map[(game_uuid, losing_uuid)] for losing_uuid in losing_uuids]
        for index, losing_sid in enumerate(losing_sids):
            response_data = {
                'uuid': losing_uuids[index],
                'game_uuid': game_uuid,
                'route': 'listGames'
            }
            emit('lost', response_data, to=losing_sid)
            leave_room(game_uuid, losing_sid)
            del user_game_sid_map[(game_uuid, losing_uuids[index])]
        
        # Broadcast Game Winner
        if not skippedPlayer and totalPlayersCount==2:
            game_winner_uuid = winning_uuids.pop()
            game_winner_sid = user_game_sid_map[(game_uuid, game_winner_uuid)]
            response_data = {
                'uuid': game_winner_uuid,
                'game_uuid': game_uuid,
                'route': 'listGames',
                'reward': game_reward[game_uuid]
            }
            emit('winner', response_data, to=game_winner_sid)
            leave_room(game_uuid, game_winner_sid)
            del user_game_sid_map[(game_uuid, game_winner_uuid)]

        # Continue Game
        else:
            # Identify if round is penultimate, ultimate, or not
            round = 'progress'
            if totalPlayersCount == 2 and skippedPlayer is not None:
                round = 'penultimate'
            elif totalPlayersCount == 2 and skippedPlayer is None:
                round = 'ultimate'
            # Broadcast next round to players who won that round
            winning_sids = [user_game_sid_map[(game_uuid, winning_uuid)] for winning_uuid in winning_uuids]
            winning_balances = list(filter(lambda li: li[2], list(filter(lambda li: li[0] in winning_uuids, playerBetDetails))))
            for index, winning_sid in enumerate(winning_sids):
                response_data = {
                    'uuid': winning_uuids[index],
                    'game_uuid': game_uuid,
                    'balance': winning_balances[index],
                    'round': round
                }
                emit('continue-game', response_data, to=winning_sid)
            
            # Broadcast next round to player who skipped the current round
            response_data = {
                'uuid': skippedPlayer[0],
                'game_uuid': game_uuid,
                'balance': skippedPlayer[2],
                'round': round
            }
            emit('continue-game', response_data, to=user_game_sid_map[(game_uuid, skippedPlayer[0])])
        
        # Reset has_bet field in DB to allow betting in the next round
        mycursor.execute("UPDATE playerbalances SET has_bet=%s WHERE gameuuid=%s", (False, game_uuid))
        mydb.commit()

    


if __name__ == '__main__':
    socketio.run(app, debug=True)

# if __name__ == "__main__":
#     app.run(debug=True)
