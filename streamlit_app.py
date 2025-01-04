# Скрипт для дозагрузки потерянных яндекс.музыкой в конце декабря скробблов
# Если что пишите t.me/Roman_Deev или пингуйте в t.me/yandexvernitescrobbling

# Для начала запросите у яндекса архив данных яндекс.музыки: https://id.yandex.ru/personal/data
# Распакуйте его и положите в одну папку со скриптом файл history.json

# Установите библиотеки
# pip install yandex-music pylast

# В last.fm может показываться местное время. Далее нужно UTC
# т.е. если в Last.fm московское время, то вычтите 3 часа

import streamlit as st
from datetime import datetime, time
start_date = st.date_input("Выберите начальную дату")
start_time = st.time_input("Выберите начальное время")
START_TIME = datetime.combine(start_date, start_time)

end_date = st.date_input("Выберите конечную дату")
end_time = st.time_input("Выберите конечное время")
END_TIME = datetime.combine(end_date, end_time)


filtered = []


import json
from datetime import datetime
from yandex_music import Client
import os
import pandas as pd

os.environ['http_proxy'] = 'http://TV4GO0:1Z7dhD8iey@2.59.50.3:5500'
os.environ['https_proxy'] = 'http://TV4GO0:1Z7dhD8iey@2.59.50.3:5500'

uploaded_file = st.file_uploader("Загрузите файл history.json", type=["json"])
if uploaded_file:
    try:
        history = json.load(uploaded_file)  # Загружаем JSON-объект из загруженного файла
        start_time = START_TIME
        print(start_time)
        end_time = END_TIME
        for item in history:
            item_time = datetime.fromisoformat(item["timestamp"].rstrip("Z") + "+00:00")
            if start_time <= item_time < end_time:
                filtered.append(item)
        
        client = Client().init()
        rich_results = client.tracks(list(set(list(map(lambda x: x['id'], filtered)))))
        ids_map = {x.id: x for x in rich_results}
        
        scrobbles = []
        problems = []
        
        for item in filtered:
            try:
                track_info = {"artist": ids_map[item['id']].artists[0].name,
                              "title": ids_map[item['id']].title,
                              "album": ids_map[item['id']].albums[0].title if ids_map[item['id']].albums else None,
                              "timestamp": item['timestamp'],
                              "duration": ids_map[item['id']].duration_ms // 1000
                              if ids_map[item['id']].duration_ms is not None
                              else None,
                              }
               
                #st.write(list(track_info.values()))
                scrobbles.append(track_info)
            except:
                problems.append(item)
        
        if len(problems):
            with open("problems_tracks.txt", "w") as f:
                for item in problems:
                     print(item, ids_map[item['id']].artists[0].name)
        
        st.write("Проверьте начало и конец списка")
        df = pd.DataFrame(scrobbles)
        print(df)
        st.dataframe(df) 
        st.write("Загрузить в Last.fm? Введите 'yes' или 'no'.")

        ans = st.text_input("Ваш ответ:")
        
        if ans.lower() == "yes":
            import pylast
        
            SESSION_KEY_FILE = ".session_key"
            network = pylast.LastFMNetwork("15ea55ecc2d12d5910bd1a56c89fb604",
                                           "2dff873c07e12a590e512c62b86b899c")
            if not os.path.exists(SESSION_KEY_FILE):
                skg = pylast.SessionKeyGenerator(network)
                url = skg.get_web_auth_url()
        
                st.write(f"Пожалуйста, авторизуйтесь в last.fm: {url}\n")
                import time
                import webbrowser
        
                webbrowser.open(url)
        
                while True:
                    try:
                        session_key = skg.get_web_auth_session_key(url)
                        with open(SESSION_KEY_FILE, "w") as f:
                            f.write(session_key)
                        break
                    except pylast.WSError:
                        time.sleep(1)
            else:
                session_key = open(SESSION_KEY_FILE).read()
        
            network.session_key = session_key
        
            st.write("Начало загрузки")
            for track in scrobbles:
                print("Загружаем ", track, end="")
                timestamp = int(datetime.fromisoformat(track["timestamp"].rstrip("Z") + "+00:00").timestamp())
                lastfm_user = network.get_user(network.username)
                network.scrobble(artist=track["artist"],
                                 title=track["title"],
                                 album=track['album'],
                                 duration=track['duration'],
                                 timestamp=timestamp)
                print(" Done!")
            st.write("Всё загружено")
    finally:
        print("ok")
