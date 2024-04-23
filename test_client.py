import requests
import pika

GAMES_URL = "http://localhost:5000/api/games/"


if __name__ == "__main__":
	resp = requests.get(GAMES_URL)

	game = resp.json()["items"][0]

	print("trying to spectate game " + game["id"])

	resp = requests.get(game["@controls"]["self"]["href"])

	game = resp.json()
	print(game["@controls"]["boardgame:spectate"]["href"])

	resp = requests.get(game["@controls"]["boardgame:spectate"]["href"])

	
