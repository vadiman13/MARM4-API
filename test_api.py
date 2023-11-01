import json
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import time
from datetime import datetime
import pytz
import os
import urllib3


# Загрузка токена авторизации из файла
def load_auth_token():
    with open('auth_token.txt', 'r') as file:
        return file.read().strip()


# Функция для выполнения запроса и проверки результатов
def execute_request(request_name, url, auth_token, duration_time=None):
    headers = {'Authorization': f'Bearer {auth_token}'}
    print("Выполняется запрос:", request_name)
    print("URL запроса:", url)

    try:
        response = requests.get(url, headers=headers)
        print("Запрос выполнен.")

        # Получение статуса ответа
        status = response.status_code

        # Получение времени выполнения запроса
        duration = response.elapsed.total_seconds()

        # Определение маркера в зависимости от статуса и времени выполнения запроса
        marker = "🔵" if status == 200 and (duration_time is None or duration <= duration_time) else "🔴"

        # Запись результатов теста в файл
        with open('test_results.txt', 'a', encoding='utf-8') as file:
            file.write(f"{marker} {request_name}\n")
            file.write(f"URL запроса: {url}\n")
            file.write(f"Статус ответа: {status}\n")
            if status == 500:
                file.write("🔴internal server error")
                file.write("\n")
            else:
                # Получение времени выполнения запроса
                duration = response.elapsed.total_seconds()
                file.write(f"Скорость выполнения запроса: {duration} сек\n")
                if marker == "🔴":
                    file.write(f"🔴Бизнес-лимит: {str(duration_time)} сек.\n")
            file.write("\n")

        print("Результаты записаны в файл.")
    except requests.exceptions.RequestException as e:
        # Если возникла ошибка, записываем соответствующий маркер, сообщение об ошибке в файл
        marker = "🔴"
        error_message = str(e)

        with open('test_results.txt', 'a', encoding='utf-8') as file:
            file.write(f"{marker} {request_name}\n")
            file.write(f"URL запроса: {url}\n")
            file.write(f"Ошибка: {error_message}\n\n")
            file.write("\n")
        print("Результаты записаны в файл.")


# Загрузка списка запросов из файла
def load_requests():
    requests_list = []
    folder_path = 'requests'

    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                requests_list.append(data[0])

    print("Запросы из файлов получены.")
    return requests_list


# Основная функция для выполнения всех автотестов
def run_tests():
    # Загрузка списка запросов из папки "requests"
    requests_list = load_requests()

    print("Запросы для выполнения получены.")

    # Загрузка токена авторизации
    auth_token = load_auth_token()

    print("Токен получен.")

    # Очистка файла test_results перед записью результатов
    with open('test_results.txt', 'w', encoding='utf-8') as file:
        file.write('')

    print("Файл очищен.")

    # Выполнение тестов для каждого запроса
    for request in requests_list:
        request_name = request['name']
        url = request['url']
        if 'durationTime' in request:
            duration_time = request['durationTime']
            execute_request(request_name, url, auth_token, duration_time)
        else:
            execute_request(request_name, url, auth_token)

    print("Тесты выполнены.")


# Запуск автотестов
run_tests()

# Отправка письма
def send_email():
    # Данные для авторизации на почтовом сервере
    email = 'smtp_user@stm-labs.ru'
    password = 'COgNF6FR'

    # Создание объекта MIMEMultipart
    msg = MIMEMultipart()

    # Получение текущей даты и времени по Московскому времени
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz)
    date_time = now.strftime("%d/%m/%Y %H:%M:%S")

    # Проверка наличия ошибок
    with open('test_results.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # Проверка наличия запросов со статусом, отличным от 200
        has_errors = any("🔴" in line for line in lines)

        # Формирование символов-маркеров цвета в теме письма
    subject_color = "🔴" if has_errors else "🔵"
    subject = f"{subject_color} Мониторинг API МАРМ-4: {date_time} (Московское время)"

    # Заполнение полей письма
    msg['From'] = email
    if has_errors:
        msg['To'] = 'kotyukovvv@rambler.ru'
    else:
        msg['To'] = 'kotyukovvv@rambler.ru'
    msg['Subject'] = subject

    # Чтение файла с результатами тестов
    with open('test_results.txt', 'r', encoding='utf-8') as file:
        content = file.read()

        # Добавление текста письма
        msg.attach(MIMEText(content, 'plain'))

    # Создание объекта MIMEBase и добавление файла-вложения
    with open('test_results.txt', 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment", filename="test_results.txt")

        # Прикрепление файла-вложения к письму
        msg.attach(part)

    # Установка соединения с почтовым сервером
    with smtplib.SMTP('smtp.lancloud.ru', 587) as server:
        server.starttls()
        server.login(email, password)

        # Отправка письма
        server.send_message(msg)

        print("Отправка письма.")

        # Закрытие соединения с почтовым сервером
        server.quit()

    print("Закрытие соединения с почтовым сервером.")


# Отправка письма с результатами тестов
send_email()
print("Отправка письма с результатами тестов.")
