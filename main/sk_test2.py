import flet as ft
import os
import pickle
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

CREDENTIALS_FILE = os.path.join(BASE_DIR, 'skf.json')
TOKEN_PICKLE = os.path.join(BASE_DIR, 'token.pickle')
DATA_FILE = os.path.join(BASE_DIR, 'players_data.txt')

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = '1zBPSOVdXVfylJdaLWWo02QxsUPr_t1sz'


font_color_column = '#ffc979'

def authenticate_google_drive():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as error:
        return None

def upload_file_to_drive(filename, file_id):
    service = authenticate_google_drive()
    if service is None:
        return
    try:
        file_metadata = {
            'name': filename,
        }
        media = MediaFileUpload(filename, mimetype='text/plain')

        existing_file = service.files().get(fileId=file_id, fields='id, parents').execute()
        if existing_file:
            file = service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            #сюда звук
        else:
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
    except Exception as error:
        print(f"Ошибка: {error}")


def download_file_from_drive(file_id, filename):
    service = authenticate_google_drive()
    if service is None:
        return
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(filename, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            done = downloader.next_chunk()
        #Сюда звук
    except Exception as error:
        return


def main(page: ft.Page):
    page.window_width = 1500
    page.window_height = 700
    page.window_resizable = False
    page.window_maximizable = False
    page.bgcolor = '#1e1e1e'
   

    columns = [
        ft.DataColumn(ft.Text("Ник", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("K/D", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Посещаемость", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Оружие", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Броня", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Приведа", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Био броня", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Био приведа", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("Под кик?", weight=ft.FontWeight.BOLD, color=font_color_column)),
        ft.DataColumn(ft.Text("", weight=ft.FontWeight.BOLD)),
    ]

    rows = []
    clan_count_container = ft.Container(content=ft.Text("Число людей в списке:", size=14, weight=ft.FontWeight.BOLD, color='#a162a3'))
    average_kd_container = ft.Container(content=ft.Text("Средний K/D: 0.0", size=14, weight=ft.FontWeight.BOLD, color='#a162a3'))
    average_priveda_container = ft.Container(content=ft.Text("Средняя Приведа: 0.0", size=14, weight=ft.FontWeight.BOLD, color='#a162a3'))
    average_bio_priveda_container = ft.Container(content=ft.Text("Средняя Био Приведа: 0.0", size=14, weight=ft.FontWeight.BOLD, color='#a162a3'))

    def save_data():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            for row in rows:
                data = [
                    row.cells[0].content.value.strip(),  # nickname
                    row.cells[1].content.value.strip(),  # kd
                    row.cells[2].content.value.strip(),  # visits
                    row.cells[3].content.value.strip(),  # weapon
                    row.cells[4].content.value.strip(),  # armor
                    row.cells[5].content.value.strip(),  # priveda
                    row.cells[6].content.value.strip(),  # bio armor
                    row.cells[7].content.value.strip(),  # bio priveda
                    "True" if row.cells[8].content.value else "False",
                ]
                f.write(";".join(data) + "\n")
        upload_file_to_drive(DATA_FILE, '1QP7RA556xR-NdnahrNo9HERb3BZvHRwM')
        update_clan_count()

    def load_data():
        try:
            download_file_from_drive('1QP7RA556xR-NdnahrNo9HERb3BZvHRwM', DATA_FILE)
        except Exception as e:
            return

        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    data = line.strip().split(";")
                    if len(data) == 9:
                        add_player(
                            None,
                            nickname=data[0],
                            kd=data[1],
                            attendance=data[2],
                            weapon=data[3],
                            armor=data[4],
                            priveda=data[5],
                            bio_armor=data[6],
                            bio_priveda=data[7],
                            active=data[8] == "True"
                        )
            update_clan_count()
            update_table()

    def add_player(e, nickname="", kd="", attendance="", weapon="", armor="", priveda="", bio_armor="", bio_priveda="", active=False):
        def remove_player(row_index):
            rows.pop(row_index)
            update_table()
            update_clan_count()

        new_row = ft.DataRow(
            cells=[ft.DataCell(ft.TextField(value=nickname, hint_text="Введите ник", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=kd, hint_text="0.0", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=attendance, hint_text="?/7", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=weapon, hint_text="Введите оружие", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=armor, hint_text="Введите броню", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=priveda, hint_text="Введите приведу", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=bio_armor, hint_text="Введите био броню", expand=True, border_radius=10)),
                   ft.DataCell(ft.TextField(value=bio_priveda, hint_text="Введите био приведу", expand=True, border_radius=10)),
                   ft.DataCell(ft.Checkbox(value=active, on_change=lambda e: update_active_status(new_row, e.control.value), overlay_color='#1e1e1e', hover_color='#464646', check_color='black', active_color='#646464')),
                   ft.DataCell(ft.ElevatedButton("Удалить", on_click=lambda e: remove_player(rows.index(new_row)), color='#c40202'))],
        )

        rows.append(new_row)
        update_table()
        update_clan_count()

    def update_active_status(row, is_active):
        row.cells[8].content.value = is_active
        update_table()

    def update_table():
        table.rows = rows
        page.update()

    def update_clan_count():
        total_kd = total_priveda = total_bio_priveda = 0
        count_kd = count_priveda = count_bio_priveda = 0

        for row in rows:
            try:
                kd_value = float(row.cells[1].content.value)
                if kd_value > 0:
                    total_kd += kd_value
                    count_kd += 1
            except ValueError:
                pass

            try:
                priveda_value = float(row.cells[5].content.value)
                if priveda_value > 0:
                    total_priveda += priveda_value
                    count_priveda += 1
            except ValueError:
                pass

            try:
                bio_priveda_value = float(row.cells[7].content.value)
                if bio_priveda_value > 0:
                    total_bio_priveda += bio_priveda_value
                    count_bio_priveda += 1
            except ValueError:
                pass

        average_kd = total_kd / count_kd if count_kd > 0 else 0
        average_priveda = total_priveda / count_priveda if count_priveda > 0 else 0
        average_bio_priveda = total_bio_priveda / count_bio_priveda if count_bio_priveda > 0 else 0

        clan_count_container.content = ft.Text(f"Число людей в списке: {len(rows)}", size=14, weight=ft.FontWeight.BOLD, color='#a162a3')
        average_kd_container.content = ft.Text(f"Средний K/D: {average_kd:.2f}", size=14, weight=ft.FontWeight.BOLD, color='#a162a3')
        average_priveda_container.content = ft.Text(f"Средняя Приведа: {average_priveda:.2f}", size=14, weight=ft.FontWeight.BOLD, color='#a162a3')
        average_bio_priveda_container.content = ft.Text(f"Средняя Био Приведа: {average_bio_priveda:.2f}", size=14, weight=ft.FontWeight.BOLD, color='#a162a3')

        page.update()

    table = ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.border.all(1, "black"),
        heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=14),
        data_text_style=ft.TextStyle(size=12),
        divider_thickness=1,
        column_spacing=10,
    )

    add_button = ft.ElevatedButton("Добавить человека", on_click=lambda e: add_player(e), color='#0d904f')
    save_button = ft.ElevatedButton("Сохранить", on_click=lambda e: save_data(), color='#0d904f')

    scrollable_table = ft.Container(
        content=ft.ListView(
            controls=[table],
            height=550,
        ),
        expand=True,
        border=ft.border.all(2, "black"),
        border_radius=ft.border_radius.all(5),
        padding=10,
        bgcolor="#282828",
    )

    page.add(
    ft.Column(
        [
            scrollable_table,
            ft.Row(
                [
                    add_button,
                    clan_count_container,
                    average_kd_container,
                    average_priveda_container,
                    average_bio_priveda_container,
                    save_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=5,
            ),
        ],
        spacing=25,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
)

    load_data()

ft.app(target=main)
