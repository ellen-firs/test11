# Скрипт для дозагрузки потерянных яндекс.музыкой в конце декабря скробблов
# Если что пишите t.me/Roman_Deev или пингуйте в t.me/yandexvernitescrobbling

# Для начала запросите у яндекса архив данных яндекс.музыки: https://id.yandex.ru/personal/data
# Распакуйте его и положите в одну папку со скриптом файл history.json

# Установите библиотеки
# pip install yandex-music pylast

# В last.fm может показываться местное время. Далее нужно UTC
# т.е. если в Last.fm московское время, то вычтите 3 часа



import streamlit as st
from datetime import datetime, date, time, timezone

default_date = date(2024, 12, 26)
default_time = time(0, 0)
start_date_choose = st.date_input("Выберите начальную дату", value = default_date)
start_time_choose = st.time_input("Выберите начальное время", value = default_time)
START_TIME = datetime.combine(start_date_choose, start_time_choose)

end_date_choose = st.date_input("Выберите конечную дату")
end_time_choose = st.time_input("Выберите конечное время")
END_TIME = datetime.combine(end_date_choose, end_time_choose)

filtered = []


import json
from yandex_music import Client
import os
import pandas as pd

os.environ['http_proxy'] = 'http://TV4GO0:1Z7dhD8iey@2.59.50.3:5500'
os.environ['https_proxy'] = 'http://TV4GO0:1Z7dhD8iey@2.59.50.3:5500'

uploaded_file = st.file_uploader("Загрузите файл history.json", type=["json"])
if uploaded_file:
    try:
        history = json.load(uploaded_file)  # Загружаем JSON-объект из загруженного файла
        start_time = START_TIME.replace(tzinfo=timezone.utc)
        print(start_time)
        print("\n")
        end_time = END_TIME.replace(tzinfo=timezone.utc)
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
        df_reversed = df.iloc[::-1]
        st.dataframe(df_reversed) 
        st.write("Загрузить в Last.fm? Введите 'yes' или 'no'.")

        ans = st.text_input("Ваш ответ:")
        
        if ans.lower() == "yes":
            import pylast
        
            SESSION_KEY_FILE = ".session_key"
            network = pylast.LastFMNetwork("15ea55ecc2d12d5910bd1a56c89fb604",
                                   "2dff873c07e12a590e512c62b86b899c")
            skg = pylast.SessionKeyGenerator(network)
            url = skg.get_web_auth_url()
        
            st.write(f"Пожалуйста, авторизуйтесь в last.fm: {url}\n")
            import time
            import webbrowser
        
            webbrowser.open(url)
            while True:
                try:
                    network.session_key = skg.get_web_auth_session_key(url)
                    break
                except pylast.WSError:
                    time.sleep(1)
            else:
                session_key = open(SESSION_KEY_FILE).read()
        
            #network.session_key = session_key
            
            st.write("Начало загрузки")
            
            scrollable_container = st.empty()
            scrollable_html = """
                            <div style=" 
                                height: 300px; 
                                overflow-y: auto; 
                                border: 1px solid #ddd; 
                                padding: 10px;  
                            " id="scrollable">
                                {content}
                            </div>
                            """
            content = ""

            
            for track in scrobbles:
                #st.write("Загружаем ", *track.values(), end="")
                track_info = *track.values()
                content += f"<p>Загружаем: {track_info}</p>"
                scrollable_container.markdown(
                    scrollable_html.format(content=content), unsafe_allow_html=True
                )
                time.sleep(0.1)

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
