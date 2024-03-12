#'scrap_menu' 함수에서 스크래핑한 메뉴 데이터를 사용해 이미지를 생성하는 부분
# 생성된 이미지를 인스타그램 스토리에 업로드 하는 기능
# 이 작업을 매일 아침 7시마다 실행하도록 스케줄링 하는 기능 

import os
import schedule
import time
import argparse
import requests

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
def scrape_menu():
    #요청할 url
    url = "https://jvision.ac.kr/vision/main/?menu=308"
    
    #URL로부터 HTML 가져오기
    response = requests.get(url)

    # print(response.content) #해당 페이지의 소스코드
    # BeautifulSoup 객체 생성
    soup = BeautifulSoup( #html 내부를 검색
        response.content, #html 넘겨주기
        "html.parser",    #BeautifulSoup에게 어떠한 형태의 데이터를 넘겨줬는지 전달하기  
        )

    # 'foodlist' 클래스를 가진 div 태그 찾기
    foodlist_div = soup.find("div", class_ ="foodlist")
    if not foodlist_div:
        print("식단 정보를 찾을 수 없습니다")
        return None
    

    menus = []
    for foodbox in foodlist_div.find_all("div", class_="foodbox"):
        date_info = foodbox.find_previous_sibling("div", class_="foodayw").find("div", class_="fooday")
        if date_info:
            day = date_info.find("div", class_="fd2").text.strip()
            year = date_info.find("div", class_="fd1").text.strip()
            full_date = f"{year}.{day}"
            print(f"날짜: {full_date}:")
        else:
            print('날짜 정보를 찾을 수 없습니다.')
            continue

        meal_time=foodbox.find("div", class_="fbt").text.strip()
        menu_items = foodbox.find("div", class_="fblist").find_all("li")
        menu_text = f"{meal_time:}\n" + "\n".join(item.text.strip() for item in menu_items if item.text.strip())
        for item in menu_items:
                menu_text = item.text.strip()
                if menu_text:
                        print(f"- {menu_text}")


# 이미지를 생성하는 함수
def create_menu_image(menu_text):
    if menu_text is None:
        return None
    
    #이미지 설정
    image_width = 1080
    image_height=1920    
    backgroung_color=(255,255,255)
    text_color=(0,0,0)
    font_size=40
    padding = 50

    image = Image.new('RGB', (image_width, image_height, backgroung_color))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("aral.ttf", font_size) # 폰트 파일 경로 수정 필요

    current_height = padding
    for date, menu_text in menus:
        draw.text((padding, current_height), date, fill=text_color, font=font)
        current_height += font_size + 10 #날짜와 메뉴 사이 간격 조정
        draw.text((padding, current_height), menu_text, fill=text_color, font=font)
        current_height += (menu_text.count('\n') + 1) * font_size + 20

    today_str = datetime.now().strftime('%Y%m%d')
    image_path = f'{IG_IMAGE_PATH}/{today_str}.jpg'
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

# 메인 작업 함수
def job():
    menus = scrape_menu()
    if menus:
        image_path = create_menu_image(menus)
        upload_story(image_path)


#스케줄링 설정
schedule.every().day.at("06:00").do(job)

#메인 실행
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
    
