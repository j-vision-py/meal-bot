#'scrap_menu' 함수에서 스크래핑한 메뉴 데이터를 사용해 이미지를 생성하는 부분
# 생성된 이미지를 인스타그램 스토리에 업로드 하는 기능
# 이 작업을 매일 아침 7시마다 실행하도록 스케줄링 하는 기능 

import os
import schedule
import time
import argparse
import requests
import pickle
import textwrap
import ast
from bs4 import BeautifulSoup 
# 웹 페이지의 HTML 또는 XML을 파싱하기 위한 Python 라이브러리, bs4 패키지 안에 잇다. 
from datetime import datetime
from instagrapi import Client
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv


load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_CREDENTIAL_PATH = "./ig_settings.json"
IG_IMAGE_PATH = "./menu"

#웹 스크래핑을 수행할 함수

course = {
    2: "조식",
    3: "중식",
    4: "석식"
}

def crawling():
    url = "https://jvision.ac.kr/vision/main/?menu=308"
    return requests.get(url)

def parsing(pageString):
    bsObj = BeautifulSoup(pageString, "html.parser")
    data = {}
    for date in [2, 3, 4, 5, 6]:
        month = bsObj.select(f"body > section:nth-child(5) > div > div > div:nth-child({date}) > div.foodayw > div > div.fd1")
        day = bsObj.select(f"body > section:nth-child(5) > div > div > div:nth-child({date}) > div.foodayw > div > div.fd2")
        if not month or not day:
            continue
        for order in [2, 3, 4]:
            list = bsObj.select(f"body > section:nth-child(5) > div > div > div:nth-child({date}) > div:nth-child({order}) > div.fblist > ul > li")
            if not list:
                continue
            menus = []
            for item in list:
                menus.append(item.text.strip())
            data[f"{month[0].text.strip()}월 {day[0].text.strip()}일 {course[order]}"] = menus

    return data

# 스크래핑 함수 실행 및 일주일치 점심, 석식 결과 저장

def save_scrape_menu():
    page = crawling()
    scrape_menus = parsing(page.text)
    if scrape_menus:
        with open('scraped_menus.pkl', 'wb') as file:
            pickle.dump(scrape_menus, file)


menus = {}

lunch_menu = []
dinner_menu = []


# 일자별 데이터 점심 메뉴 불러오기
def get_lunch_and_dinner_menu_for_date():
    specific_date = datetime.now().strftime('%Y.%m월 %d일')
    try:
        with open('scraped_menus.pkl', 'rb') as file:
            menus = pickle.load(file)
            #날짜에 해당하는 메뉴를 반환
            lunch_menu = menus.get(f'{specific_date} 중식', "해당 날짜의 메뉴 정보가 없습니다." )
            dinner_menu = menus.get(f'{specific_date} 석식', "해당 날짜의 메뉴 정보가 없습니다." )
            lunch_menu_for_date = f'{specific_date} 중식: {lunch_menu}'
            dinner_menu_for_date = f'{specific_date} 석식: {dinner_menu}'
            return lunch_menu_for_date, dinner_menu_for_date
    except FileNotFoundError:
        print("식당 데이터 파일을 찾을 수 없습니다.")
        return {}

lunch_menu, dinner_menu = get_lunch_and_dinner_menu_for_date()
def create_menu_image(daily_menus: dict[str, list[str]]) -> str:
    if not daily_menus:
        return None
    
    #이미지 설정
    image_width = 1080
    image_height= 1920    
    backgroung_color = (255,255,255)
    text_color = (0,0,0)
    font_size = 72

    image = Image.new('RGB', (image_width, image_height), backgroung_color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("./font.ttf", font_size) # 폰트 파일 경로 수정 필요

    contents = []
    for date, menu in daily_menus.items():
        contents.append(date)
        sub = False
        for food in menu:
            if '<' in food:
                sub = False
                contents.append('')
            prefix = ''
            if sub:
                prefix = '- '
            contents.append(prefix + food)
            if '<' in food:
                sub = True

    content = '\n'.join(contents)

    text_bbox = draw.textbbox((0, 0), content, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2

    draw.text((x, y), content, fill=text_color, font=font, align='left')

    today_str = datetime.now().strftime('%Y%m%d')
    image_path = f'./{today_str}.jpg'
    image.save(image_path)
    return image_path



# 인스타그램 스토리 업로드 하는 함수
def upload_story(image_path):
    if image_path:
        cl = Client()
        if os.path.exists(IG_CREDENTIAL_PATH):
            cl.load_settings(IG_CREDENTIAL_PATH)
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.photo_upload_to_story(image_path)
        cl.dump_settings(IG_CREDENTIAL_PATH)

def upload_lunch_menu():
    global lunch_menu
    today_date=datetime.now().strftime('%Y.%m월 %d일')
    split_data = lunch_menu.split(': ')
    date = split_data[0]
    menu_list_str = split_data[1]
    menu_list = ast.literal_eval(menu_list_str)
    lunch_menu ={date: menu_list}
    if lunch_menu:
        image_path=create_menu_image(lunch_menu)
        upload_story(image_path)


def upload_dinner_menu():
    global dinner_menu
    today_date=datetime.now().strftime('%Y.%m월 %d일')
    split_data = dinner_menu.split(': ')
    date = split_data[0]
    menu_list_str = split_data[1]
    menu_list = ast.literal_eval(menu_list_str)
    dinner_menu ={date: menu_list}
    if dinner_menu:
        image_path=create_menu_image(dinner_menu)
        upload_story(image_path)



#스케줄링 설정
schedule.every().monday.at("07:00").do(upload_lunch_menu, upload_dinner_menu)
schedule.every().tuesday.at("07:00").do(upload_lunch_menu, upload_dinner_menu)
schedule.every().wednesday.at("07:00").do(upload_lunch_menu, upload_dinner_menu)
schedule.every().thursday.at("07:00").do(upload_lunch_menu, upload_dinner_menu)
schedule.every().friday.at("07:00").do(upload_lunch_menu, upload_dinner_menu)


#메인 실행
if __name__ == "__main__":
    while True:
        parser = argparse.ArgumentParser(description="upload Instagram story")
        parser.add_argument("--uploadnow", action="store_true", help="upload ths stroy immediately")
        args = parser.parse_args()

        if args.uploadnow:
            upload_lunch_menu()
            upload_dinner_menu()
        else:
            print("Program initated.")

            next_run = schedule.next_run()
            print(f"Next scheduled run at: {next_run}")

            while True:
                schedule.run_pending()
                time.sleep(1)            