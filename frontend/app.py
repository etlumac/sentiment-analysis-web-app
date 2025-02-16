import streamlit as st
import requests
import pandas as pd
import plotly.express as px

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

# **Проверяем, загружены ли данные, перед фильтрацией**
if st.session_state.df is not None:
    df = st.session_state.df

    # График распределения
    fig = px.pie(df, names="sentiment", title="Распределение тональности", hole=0.3)
    st.plotly_chart(fig)

    # **Исправленный фильтр по тональности**
    all_classes = ["Все классы"] + list(df["sentiment"].unique())
    selected_class = st.selectbox("Фильтр по классу:", all_classes)

    # Фильтруем данные
    if selected_class == "Все классы":
        filtered_df = df
    else:
        filtered_df = df[df["sentiment"] == selected_class]

    st.write(filtered_df)  # Выводим отфильтрованные данные


