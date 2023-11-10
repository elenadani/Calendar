import sys
import sqlite3
import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor, QPixmap


class Calendar(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(200, 200, 500, 500)
        self.setWindowTitle('Календарь')

        self.calendar = QCalendarWidget(self)
        self.calendar.setDateRange(QDate(2023, 1, 1), QDate(2024, 12, 31))

        self.day_plan = QPlainTextEdit(self)
        self.day_plan.move(320, 20)
        self.day_plan.resize(160, 250)

        self.calendar.clicked.connect(self.show_day_plans)

        self.save_bt = QPushButton('Сохранить', self)
        self.save_bt.move(320, 275)
        self.save_bt.resize(110, 40)
        self.save_bt.clicked.connect(self.save)

        self.del_bt = QPushButton('Удалить событие', self)
        self.del_bt.move(320, 320)
        self.del_bt.resize(140, 40)
        self.del_bt.clicked.connect(self.delete_dialog)

        self.day_title = QLabel(self)
        self.day_title.move(320, 1)
        self.day_title.resize(160, 10)

        self.button_of_importance = QRadioButton('Важное событие', self)
        self.button_of_importance.move(330, 230)
        self.button_of_importance.resize(110, 30)

        self.im_title = QLabel(self)
        self.im_title.move(10, 190)
        self.im_title.resize(100, 15)
        self.im_title.setText('Важные дни:')

        self.for_important_events = QTextEdit(self)
        self.for_important_events.move(10, 210)
        self.for_important_events.resize(140, 285)
        self.for_important_events.setReadOnly(True)

        self.cur_title = QLabel(self)
        self.cur_title.move(165, 190)
        self.cur_title.resize(160, 15)
        self.cur_title.setText('В этом месяце:')

        self.for_current_events = QTextEdit(self)
        self.for_current_events.move(165, 210)
        self.for_current_events.resize(140, 285)
        self.for_current_events.setReadOnly(True)

        self.image = QLabel(self)
        self.image.move(320, 365)
        self.image.resize(160, 129)

        self.was_colored()
        self.show_important_events()
        self.show_events_in_this_month()
        self.show_season()

        data = self.get_current_data()
        self.day_title.setText(data)

    # Получение выбранной даты из календаря
    def get_current_data(self):
        d = self.calendar.selectedDate().toPyDate()
        d = str(d)
        year, month, day = d[2:4], d[5:7], d[8:]
        return f'{day}.{month}.{year}'

    # Показывает картинку текущего сезона
    def show_season(self):
        date = self.get_current_data()
        season = date[3:5]
        if season in ['01', '02', '12']:
            self.pixmap = QPixmap('image_jpg/winter.jpg')  # https://f.vividscreen.info/soft/9f81789510a62604dfe6d2de011b12ed/Winter-Train-Ride-wide-i.jpg
        elif season in ['03', '04', '05']:
            self.pixmap = QPixmap('image_jpg/spring.jpg')  # https://ru.vividscreen.info/pic/in-mountains/648/
        elif season in ['06', '07', '08']:
            self.pixmap = QPixmap('image_jpg/summer.jpg')  # https://ru.vividscreen.info/pic/nice-scenery/2919/
        elif season in ['09', '10', '11']:
            self.pixmap = QPixmap('image_jpg/autumn.jpg')  # https://ru.vividscreen.info/pic/autumn-morning/27929/
        self.image.setPixmap(self.pixmap)

    # Вспомогательная функция для функции was_colored
    def paint_last_events(self, color, date):
        d = date[0]
        year, month, day = '20' + d[6:], d[3:5], d[:2]
        qdate = QDate(int(year), int(month), int(day))
        date_format = self.calendar.dateTextFormat(qdate)
        date_format.setBackground(color)
        self.calendar.setDateTextFormat(qdate, date_format)

    # Функция для сохранения уже закрашенных ячеек при новом запуске программы
    # Закрашивает ячейки, на которых есть события
    def was_colored(self):
        con = sqlite3.connect('calendar_db.sqlite')
        cur = con.cursor()
        dates = cur.execute("""SELECT Data FROM Days""").fetchall()
        for date in dates:
            events = cur.execute("""SELECT Events FROM Days WHERE Data = ?""", (date[0],)).fetchone()
            importance = cur.execute("""SELECT Important FROM Days WHERE Data = ?""", (date[0],)).fetchone()
            if importance[0] == 1:
                self.paint_last_events(QColor(255, 102, 102), date)
            elif events[0] is not None:
                self.paint_last_events(QColor(153, 255, 255), date)
            else:
                self.paint_last_events(QColor(255, 255, 255), date)
        con.commit()
        con.close()

    # Закрашивает ячейку в передаваемый цвет
    def paint_event(self, color):
        d = self.calendar.selectedDate().toPyDate()
        d = str(d)
        year, month, day = d[:4], d[5:7], d[8:]
        qdate = QDate(int(year), int(month), int(day))
        date_format = self.calendar.dateTextFormat(qdate)
        date_format.setBackground(color)
        self.calendar.setDateTextFormat(qdate, date_format)

    # Показывает информацию о выбранном дне
    def show_day_plans(self):
        data = self.get_current_data()
        self.day_title.setText(data)
        con = sqlite3.connect('calendar_db.sqlite')
        cur = con.cursor()
        result = cur.execute("""SELECT Events FROM Days WHERE Data = ?""", (data,)).fetchall()
        importance = cur.execute("""SELECT Important FROM Days WHERE Data = ?""", (data,)).fetchall()
        if importance[0][0] == 1:
            self.button_of_importance.setChecked(True)
        else:
            self.button_of_importance.setChecked(False)
        self.day_plan.setPlainText(result[0][0])
        con.commit()
        con.close()
        self.show_season()

    # Показывает дни событий с пометкой "важные"
    def show_important_events(self):
        self.for_important_events.clear()
        try:
            file_im = open('file_with_im_ev.txt', 'r', encoding='utf8')
            days = file_im.read().split('\n')
            for el in days:
                self.for_important_events.append(el)
            file_im.close()
        except FileNotFoundError:
            file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
            file_im.close()

    # Показывает дни этого месяца, на которых есть события
    def show_events_in_this_month(self):
        self.for_current_events.clear()
        try:
            file_c = open('current_events.txt', 'r', encoding='utf8')
            days = file_c.read().split('\n')
            for el in days:
                self.for_current_events.append(el)
            file_c.close()
        except FileNotFoundError:
            file_c = open('current_events.txt', 'w', encoding='utf8')
            file_c.close()

    # Определяет, принадлежит ли выбранная дата этому месяцу
    # И если да, то записывает дату в специальный файл
    def determine_if_in_this_month(self):
        data = self.get_current_data()
        year_d = data[6:]
        month_d = data[3:5]
        current_date = datetime.datetime.now()
        year_c = current_date.year
        month_c = current_date.month
        year_d = '20' + year_d
        if year_c == int(year_d) and month_c == int(month_d):
            try:
                file_c_1 = open('current_events.txt', 'r', encoding='utf8')
                cur_ev = file_c_1.readlines()
                data = data + '\n'
                if data not in cur_ev:
                    file_c = open('current_events.txt', 'a', encoding='utf8')
                    file_c.write(data)
                    file_c.close()
            except FileNotFoundError:
                file_c = open('current_events.txt', 'w', encoding='utf8')
                data = data + '\n'
                file_c.write(data)
                file_c.close()

    # Сохраняет изменения данных о выбранном дне
    def save(self):
        self.determine_if_in_this_month()
        data = self.get_current_data()

        # Передаёт в переменную внесённый текст
        input_t = self.day_plan.toPlainText()

        con = sqlite3.connect('calendar_db.sqlite')
        cur = con.cursor()
        # Обновляет информацию о событии в БД
        cur.execute("""UPDATE Days SET Events = ? WHERE Data = ?""", (input_t, data))

        # Проверяет важно событие или нет
        if self.button_of_importance.isChecked() is True:
            cur.execute("""UPDATE Days SET Important = 1 WHERE Data = ?""", (data,))
            self.paint_event(QColor(255, 102, 102))

            # Если да, то записывает дату в специальный файл
            try:
                file_im_1 = open('file_with_im_ev.txt', 'r', encoding='utf8')
                im_ev = file_im_1.readlines()
                data = data + '\n'
                if data not in im_ev:
                    file_im = open('file_with_im_ev.txt', 'a', encoding='utf8')
                    file_im.write(data)
                    file_im.close()
            except FileNotFoundError:
                file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
                data = data + '\n'
                file_im.write(data)
                file_im.close()

        else:
            cur.execute("""UPDATE Days SET Important = 0 WHERE Data = ?""", (data,))
            self.paint_event(QColor(153, 255, 255))

            # Удаляет дату из файла, если оно неважно, но до этого было важным
            try:
                file_im_1 = open('file_with_im_ev.txt', 'r', encoding='utf8')
                im_ev = file_im_1.readlines()
                data = data + '\n'
                if data in im_ev:
                    im_ev.remove(data)
                file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
                for el in im_ev:
                    file_im.write(el)
                file_im.close()
                file_im_1.close()
            except FileNotFoundError:
                file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
                data = data + '\n'
                file_im.write(data)
                file_im.close()

        con.commit()
        con.close()
        # Обновляет показывающуюся информацию
        self.day_plan.setPlainText(input_t)
        self.show_important_events()
        self.show_events_in_this_month()

    # Удаляет данные о событии
    def delete(self):
        self.day_plan.clear()
        data = self.get_current_data()
        con = sqlite3.connect('calendar_db.sqlite')
        cur = con.cursor()
        # Обновляет информацию в БД
        cur.execute("""UPDATE Days SET Events = NULL WHERE Data = ?""", (data,))
        cur.execute("""UPDATE Days SET Important = 0 WHERE Data = ?""", (data,))
        con.commit()
        con.close()
        self.button_of_importance.setChecked(False)
        self.paint_event(QColor(255, 255, 255))

        # Удаляет дату, если она была в файлах

        try:
            file_im_1 = open('file_with_im_ev.txt', 'r', encoding='utf8')
            im_ev = file_im_1.readlines()
            data = data + '\n'
            if data in im_ev:
                im_ev.remove(data)
            file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
            for el in im_ev:
                file_im.write(el)
            file_im.close()
            file_im_1.close()
        except FileNotFoundError:
            file_im = open('file_with_im_ev.txt', 'w', encoding='utf8')
            file_im.close()

        # Обновляет показывающуюся информацию
        self.show_important_events()

        try:
            file_c_1 = open('current_events.txt', 'r', encoding='utf8')
            cur_ev = file_c_1.readlines()
            data = data
            if data in cur_ev:
                cur_ev.remove(data)
            file_c = open('current_events.txt', 'w', encoding='utf8')
            for el in cur_ev:
                file_c.write(el)
            file_c.close()
            file_c_1.close()
        except FileNotFoundError:
            file_c = open('current_events.txt', 'w', encoding='utf8')
            file_c.close()

        # Обновляет показывающуюся информацию
        self.show_events_in_this_month()

    # Вызывает диалоговое окно с уточнением о уверенности в удалении событий
    def delete_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Вы уверены?")
        date = self.get_current_data()
        dlg.setText(f"Удалить все события запланированные на {date}?")
        dlg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
        dlg.setIcon(QMessageBox.Question)
        button = dlg.exec()

        if button == QMessageBox.Yes:
            self.delete()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Calendar()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())