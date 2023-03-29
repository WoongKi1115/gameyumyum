import requests
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from mongoengine import connect
from openpyxl import load_workbook
from starlette.requests import Request
from steamsignin import SteamSignIn
from recommend import recommend_game
from typing import List
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
mongodb_root = os.environ.get('mongodb_root')
steam_key = os.getenv('steam_key')
mongodb_URI = f"mongodb+srv://root:{mongodb_root}@gamenyamnaym.t2iixnv.mongodb.net/test"

# DB 연결
client = MongoClient(mongodb_URI)

# DB 접근
db = client['nyamnyam']

# Collection 접근
games = db['game']


app = FastAPI()
api_url = "http://127.0.0.1:8000"


@app.get("/games/{user_id}")
async def get_game_count(user_id: str):
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=FF1F5EF115E50CEBE0A7C11123959310&steamid={user_id}&format=json"
    response = requests.get(url)
    json_response = response.json()
    game_count = json_response["response"]["game_count"]
    return game_count


@app.get('/login')
async def main(steam_signin: SteamSignIn = Depends(SteamSignIn)):
    url = steam_signin.ConstructURL(api_url+'/processlogin')
    return steam_signin.RedirectUser(url)


@app.get('/processlogin')
async def pr(request: Request, steam_signin: SteamSignIn = Depends(SteamSignIn)):
    return steam_signin.ValidateResults(request.query_params)
# 규칙에 따른 추천 게임 리스트 (인기 게임 몇 개, 사용자 리스트 기반 몇 개 ...)


@app.get("/games/all")
def get_all_game():
    return {"Hello": "World"}

# 5개 이상 플레이한 사용자가 전에 했던 게임 기반으로 (태그) 분석


@app.get("/games/result/{userid}")
def get_game_by_tag(userid: str):
    """ 5개 이상 플레이한 사용자가 전에 했던 게임 기반으로 태그 분석

    Args:
        userid : 유저 아이디

    Returns:
        전에 플레이했던 장르 중 가장 많은 태그 5개

    """

    # 1. 플레이했던 게임 정보(appid) 불러오기
    playedGames = {}
    appids = []
    playedGenres = []
    result = {}
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={steam_key}&steamid={userid}"
    response = requests.get(url)
    json_response = response.json()
    playedGames = json_response["response"]["games"]

    for k in playedGames:
        appids.append(k['appid'])

    # 2. 불러온 appid를 이용해 db에서 game detail 가져오기

    for k in appids:
        playedGenres.append(games.find_one({"appid": str(k)}, {
            "_id": 0, "genres": 1}))

    # 3. game detail list에서 장르 뽑아서 5개 가져오기
    result = recommend_game.get_preference(playedGenres)

    return result

# 5개 미만 플레이한 사용자의 장바구니 기반으로 (태그) 분석


@app.get("/games/result")
def get_game_by_table(table_list: str):
    return {"Hello": "World"}

# 뽑은 게임 리스트에 대한 매치율 저장


@app.post("/games/rate")
def get_rate(preference: list,
             games: list):
    result = recommend_game.get_result(preference, games)
    return result

# 뽑은 리스트랑 비슷한 거 추천


@app.get("/games/similar")
def get_similar_game():

    return {"Hello": "World"}


@app.get("/games/detail/{appid}")
def get_game_detail(appid: str):
    """게임 상세 정보 반환 함수.

    Args:
        appid : 게임의 앱 아이디

    Returns:
        제목, 가격, 스크린샷, 짧은 설명, 개발사, 출시일, 장르, 카테고리
    """
    result = {}

    # DB 조회
    get_game = games.find_one({"appid": appid}, {
                              "_id": 0, "recommendations": 0, "metacritic": 0, "about_the_game": 0})

    # categories, genres, screenshots, developers 리스트화
    get_game["categories"] = get_game["categories"].split(",")
    get_game["genres"] = get_game["genres"].split(",")
    get_game["screenshots"] = get_game["screenshots"].split(",")
    get_game["developers"] = get_game["developers"].split("///")

    result["data"] = get_game

    return result
