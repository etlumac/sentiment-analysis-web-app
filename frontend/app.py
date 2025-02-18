import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from collections import Counter

STOP_WORDS = {"и", "в", "на", "с", "по", "за", "к", "под", "от", "что", "как", "для", "то", "а", "ли", "будет", "меня", "будет", "пока", "может", "уже", "раз", "мы"
              "не", "но", "до", "из", "у", "же", "так", "вы", "он", "она", "они", "это", "все", "при", "я", "есть", "днём", "не", "почему", "только", "непример", "нас"
              "мы", "мне", "мой", "моя", "моё", "мои", "твой", "твоя", "твоё", "твои", "-", "спасибо", "ты", "очень", "ни", "их", "всем", "такие", "их", "или"}

# , ""




API_TEXT = "http://127.0.0.1:8000/analyze/"
API_FILE = "http://127.0.0.1:8000/analyze-file/"

st.title("🔍 Анализ тональности текста")

# Сохраняем загруженные данные в сессию, чтобы не пропадали
if "df" not in st.session_state:
    st.session_state.df = None

# Поле для текста
text_input = st.text_area("Введите текст для анализа:")

if st.button("Анализировать текст"):
    if text_input.strip():
        try:
            response = requests.post(API_TEXT, json={"text": text_input})

            if response.status_code == 200:
                data = response.json()
                st.write(f"**Тональность:** {data['sentiment']}")
                st.write(f"**Уверенность модели:** {round(data['confidence'] * 100, 2)}%")
            else:
                st.error("Ошибка API! Попробуйте позже.")

        except requests.exceptions.JSONDecodeError:
            st.error("Ошибка обработки ответа API!")

    else:
        st.warning("Введите текст!")

# Поле для загрузки файла
uploaded_file = st.file_uploader("Загрузите XLSX-файл с колонкой 'MessageText'", type=["xlsx"])

if uploaded_file and st.button("Анализировать файл"):
    try:
        files = {
            "file": ("file.xlsx", uploaded_file.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        response = requests.post(API_FILE, files=files)

        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            st.session_state.df = df  # Сохраняем в session_state

        else:
            st.error("Ошибка API! Попробуйте позже.")

    except requests.exceptions.JSONDecodeError:
        st.error("Ошибка обработки ответа API!")

# Проверяем, загружены ли данные, перед фильтрацией
if st.session_state.df is not None:
    df = st.session_state.df

    # Функция для очистки HTML-тегов
    def clean_html(text):
        return BeautifulSoup(text, "html.parser").get_text(strip=True)

    # Очистим текст перед отображением
    df["MessageText"] = df["MessageText"].apply(clean_html)

    # График распределения
    fig = px.pie(df, names="sentiment", title="Распределение тональности", hole=0.3)
    st.plotly_chart(fig)

    # Фильтр по тональности
    keyword = st.text_input("🔍 Поиск по ключевым словам:", "")

    all_classes = ["Все классы"] + list(df["sentiment"].unique())
    selected_class = st.selectbox("Фильтр по классу:", all_classes)
    
    # Фильтруем данные
    filtered_df = df  # Начинаем с полного DataFrame

    if keyword:
        filtered_df = filtered_df[filtered_df["MessageText"].str.contains(keyword, case=False, na=False)]

    if selected_class != "Все классы":
        filtered_df = filtered_df[filtered_df["sentiment"] == selected_class]

    st.write(filtered_df)  # Выводим отфильтрованные данные

    # Преобразуем SubmitDate в datetime, учитывая ISO 8601 формат
    df["SubmitDate"] = pd.to_datetime(df["SubmitDate"], errors="coerce")

    # Удаляем строки с NaT (ошибочные даты)
    df = df.dropna(subset=["SubmitDate"])

    # Создаем колонку с месяцем (год-месяц)
    df["month"] = df["SubmitDate"].dt.to_period("M").astype(str)

    # Группируем по месяцам и тональности
    df_grouped = df.groupby(["month", "sentiment"]).size().reset_index(name="count")

    # Создаем сводную таблицу для построения отдельных столбцов
    df_pivot = df_grouped.pivot(index="month", columns="sentiment", values="count").fillna(0)

    # Добавляем общий подсчет сообщений
    df_pivot["total_messages"] = df_pivot.sum(axis=1)

    # Превращаем индекс в колонку
    df_pivot.reset_index(inplace=True)

    # Создаем столбчатую диаграмму
    fig = px.bar(df_pivot, x="month", y=df_pivot.columns[1:-1],  # Исключаем 'month' и 'total_messages'
             title="Изменение тональности сообщений по месяцам",
             labels={"value": "Количество сообщений", "variable": "sentiment"},
             barmode="group")  # Группируем столбцы

    # Добавляем трендовую линию общего количества сообщений
    fig.add_scatter(x=df_pivot["month"], y=df_pivot["total_messages"], mode="lines+markers",
                name="Общее количество сообщений", line=dict(color="black"))

    # Отображаем график
    st.plotly_chart(fig)


    # Функция для подсчета частоты слов по классам
    def get_top_words_by_class(df, top_n=15):
        word_counts = []
        
        for sentiment_class in df["sentiment"].unique():
            subset = df[df["sentiment"] == sentiment_class]
        
            # Объединяем весь текст этого класса и разбиваем на слова
            words = " ".join(subset["MessageText"]).lower().split()

            # Фильтруем слова, убирая стоп-слова
            words = [word for word in words if word not in STOP_WORDS]

            word_freq = Counter(words).most_common(top_n)  # ТОП-10 слов
        
            for word, count in word_freq:
                word_counts.append({"word": word, "count": count, "sentiment": sentiment_class})
    
        return pd.DataFrame(word_counts)

    # Получаем таблицу с частотой слов
    word_df = get_top_words_by_class(df)

    # Строим Treemap
    fig_treemap = px.treemap(word_df, 
                          path=["sentiment", "word"], 
                          values="count", 
                          title="Популярные слова по классам",
                          color="sentiment", 
                          color_discrete_map={"positive": "green", "negative": "red", "neutral": "blue"})

    # Отображаем в Streamlit
    st.plotly_chart(fig_treemap)
