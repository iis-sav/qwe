import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Text, Scrollbar
from PIL import Image, ImageTk
import os
import sqlite3
import io
from datetime import datetime

class DeviceAppWithDB:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление устройствами с БД")
        self.root.geometry("1000x700")

        # Список устройств
        self.devices = ["Камеры", "Микроконтроллера", "Датчик движения", "Термометр"]

        # Инициализация базы данных
        self.init_database()

        # Главное меню
        self.create_main_menu()

        # Основная область
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Показать начальный экран
        self.show_welcome()

    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect('devices.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Создание таблиц
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                text_content TEXT,
                image_data BLOB,
                image_path TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Создание индексов
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_device_name ON devices(device_name)
        ''')

        self.conn.commit()

        # Заполняем начальные данные, если таблица пустая
        self.cursor.execute("SELECT COUNT(*) FROM devices")
        if self.cursor.fetchone()[0] == 0:
            for device in self.devices:
                default_text = self.get_default_text(device)
                self.cursor.execute('''
                    INSERT INTO devices (device_name, text_content)
                    VALUES (?, ?)
                ''', (device, default_text))
            self.conn.commit()

    def get_default_text(self, device):
        """Получить текст по умолчанию для устройства"""
        defaults = {
            "Камеры": "Характеристики камер:\n• Разрешение\n• Фокусное расстояние\n• Чувствительность",
            "Микроконтроллера": "Характеристики микроконтроллера:\n• Архитектура\n• Частота\n• Память",
            "Датчик движения": "Характеристики датчика:\n• Дальность\n• Угол обзора\n• Чувствительность",
            "Термометр": "Характеристики термометра:\n• Диапазон\n• Точность\n• Время отклика"
        }
        return defaults.get(device, f"Добавьте текст для {device}")

    def create_main_menu(self):
        """Простое главное меню"""
        menu_frame = ttk.Frame(self.root)
        menu_frame.pack(fill=tk.X, padx=10, pady=5)

        # Кнопки меню
        ttk.Button(menu_frame, text="📷 Изображение",
                   command=self.show_image).pack(side=tk.LEFT, padx=5)

        ttk.Button(menu_frame, text="📝 Характеристики",
                   command=self.show_chars).pack(side=tk.LEFT, padx=5)

        ttk.Button(menu_frame, text="⚙️ Функции",
                   command=self.show_func).pack(side=tk.LEFT, padx=5)

        # Управление БД
        ttk.Button(menu_frame, text="💾 Экспорт БД",
                   command=self.export_db).pack(side=tk.RIGHT, padx=5)

        ttk.Button(menu_frame, text="🗑️ Очистить БД",
                   command=self.clear_db_confirm).pack(side=tk.RIGHT, padx=5)

        ttk.Button(menu_frame, text="🏠 Главная",
                   command=self.show_welcome).pack(side=tk.RIGHT, padx=5)

    def clear_main_frame(self):
        """Очистить основную область"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_welcome(self):
        """Главный экран"""
        self.clear_main_frame()

        ttk.Label(self.main_frame, text="Управление устройствами с БД",
                  font=('Arial', 20)).pack(pady=30)

        ttk.Label(self.main_frame, text="Выберите раздел в меню",
                  font=('Arial', 12)).pack(pady=10)

        # Статистика из БД
        stats_frame = ttk.LabelFrame(self.main_frame, text="Статистика из базы данных", padding=20)
        stats_frame.pack(pady=20, padx=50, fill=tk.X)

        for device in self.devices:
            self.cursor.execute('''
                SELECT text_content, image_data 
                FROM devices 
                WHERE device_name = ?
            ''', (device,))
            result = self.cursor.fetchone()

            if result:
                text_content, image_data = result
                has_text = "✅" if text_content and len(text_content) > 10 else "❌"
                has_image = "✅" if image_data else "❌"

                device_frame = ttk.Frame(stats_frame)
                device_frame.pack(fill=tk.X, pady=3)

                ttk.Label(device_frame, text=f"{device}:",
                          width=20, anchor='w').pack(side=tk.LEFT)
                ttk.Label(device_frame, text=f"Текст: {has_text}").pack(side=tk.LEFT, padx=10)
                ttk.Label(device_frame, text=f"Фото: {has_image}").pack(side=tk.LEFT, padx=10)

    def show_image(self):
        """Раздел с изображениями"""
        self.clear_main_frame()

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        for device in self.devices:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=device)

            # Заголовок
            ttk.Label(tab, text=f"Изображение для {device}",
                      font=('Arial', 14)).pack(pady=10)

            # Область для изображения
            img_label = ttk.Label(tab)
            img_label.pack(pady=10)

            # Загружаем изображение из БД
            self.load_image_from_db(device, img_label)

            # Кнопки
            btn_frame = ttk.Frame(tab)
            btn_frame.pack(pady=10)

            ttk.Button(btn_frame, text="Загрузить фото",
                       command=lambda d=device, l=img_label: self.load_image_to_db(d, l)).pack(side=tk.LEFT, padx=5)

            ttk.Button(btn_frame, text="Удалить фото",
                       command=lambda d=device, l=img_label: self.delete_image_from_db(d, l)).pack(side=tk.LEFT, padx=5)

            ttk.Button(btn_frame, text="Просмотр",
                       command=lambda d=device: self.view_full_image(d)).pack(side=tk.LEFT, padx=5)

    def load_image_from_db(self, device_name, label):
        """Загрузить изображение из базы данных"""
        try:
            self.cursor.execute('''
                SELECT image_data FROM devices WHERE device_name = ?
            ''', (device_name,))
            result = self.cursor.fetchone()

            if result and result[0]:
                # Преобразуем бинарные данные в изображение
                image_data = result[0]
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((350, 250))
                photo = ImageTk.PhotoImage(image)

                label.config(image=photo, text="")
                label.image = photo  # сохраняем ссылку
            else:
                label.config(image='', text="Изображение не загружено")
        except Exception as e:
            label.config(image='', text="Ошибка загрузки")
            print(f"Ошибка загрузки: {e}")

    def load_image_to_db(self, device_name, label):
        """Загрузить изображение в базу данных"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )

        if file_path:
            try:
                # Читаем файл как бинарные данные
                with open(file_path, 'rb') as file:
                    image_data = file.read()

                # Обновляем запись в базе данных
                self.cursor.execute('''
                    UPDATE devices 
                    SET image_data = ?, image_path = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE device_name = ?
                ''', (image_data, file_path, device_name))
                self.conn.commit()

                # Обновляем отображение
                self.load_image_from_db(device_name, label)

                messagebox.showinfo("Успех", f"Изображение для {device_name} сохранено в БД")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")

    def delete_image_from_db(self, device_name, label):
        """Удалить изображение из базы данных"""
        if messagebox.askyesno("Подтверждение", f"Удалить изображение для {device_name}?"):
            self.cursor.execute('''
                UPDATE devices 
                SET image_data = NULL, image_path = NULL, last_updated = CURRENT_TIMESTAMP
                WHERE device_name = ?
            ''', (device_name,))
            self.conn.commit()

            label.config(image='', text="Изображение удалено")
            messagebox.showinfo("Удалено", f"Изображение для {device_name} удалено из БД")

    def view_full_image(self, device_name):
        """Просмотр изображения в полном размере"""
        try:
            self.cursor.execute('SELECT image_data FROM devices WHERE device_name = ?', (device_name,))
            result = self.cursor.fetchone()

            if result and result[0]:
                # Создаем новое окно для просмотра
                view_window = tk.Toplevel(self.root)
                view_window.title(f"Изображение - {device_name}")
                view_window.geometry("600x500")

                image_data = result[0]
                image = Image.open(io.BytesIO(image_data))

                # Масштабируем для окна
                width, height = image.size
                if width > 550 or height > 400:
                    ratio = min(550/width, 400/height)
                    new_size = (int(width * ratio), int(height * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                photo = ImageTk.PhotoImage(image)

                label = ttk.Label(view_window, image=photo)
                label.image = photo
                label.pack(pady=20)

                ttk.Label(view_window, text=f"Размер: {width}x{height}").pack(pady=5)
            else:
                messagebox.showinfo("Нет изображения", f"Для {device_name} нет сохраненного изображения")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть изображение: {str(e)}")

    def show_chars(self):
        """Раздел с характеристиками"""
        self.clear_main_frame()

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        for device in self.devices:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=device)

            # Заголовок
            ttk.Label(tab, text=f"Характеристики {device}",
                      font=('Arial', 14)).pack(pady=10)

            # Текстовое поле
            text_frame = ttk.Frame(tab)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            text_widget = Text(text_frame, height=15, width=60, font=('Arial', 10))
            scrollbar = Scrollbar(text_frame, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Загружаем текст из БД
            self.load_text_from_db(device, text_widget)

            # Кнопки
            btn_frame = ttk.Frame(tab)
            btn_frame.pack(pady=10)

            ttk.Button(btn_frame, text="Сохранить в БД",
                       command=lambda d=device, tw=text_widget: self.save_text_to_db(d, tw)).pack(side=tk.LEFT, padx=5)

            ttk.Button(btn_frame, text="Загрузить из файла",
                       command=lambda d=device, tw=text_widget: self.load_text_from_file(d, tw)).pack(side=tk.LEFT, padx=5)

            ttk.Button(btn_frame, text="Сбросить",
                       command=lambda d=device, tw=text_widget: self.reset_text(d, tw)).pack(side=tk.LEFT, padx=5)

    def load_text_from_db(self, device_name, text_widget):
        """Загрузить текст из базы данных"""
        try:
            self.cursor.execute('''
                SELECT text_content FROM devices WHERE device_name = ?
            ''', (device_name,))
            result = self.cursor.fetchone()

            if result and result[0]:
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", result[0])
        except Exception as e:
            print(f"Ошибка загрузки текста: {e}")

    def save_text_to_db(self, device_name, text_widget):
        """Сохранить текст в базу данных"""
        text = text_widget.get("1.0", tk.END).strip()

        try:
            self.cursor.execute('''
                UPDATE devices 
                SET text_content = ?, last_updated = CURRENT_TIMESTAMP
                WHERE device_name = ?
            ''', (text, device_name))
            self.conn.commit()

            messagebox.showinfo("Сохранено", f"Текст для {device_name} сохранен в БД")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {str(e)}")

    def load_text_from_file(self, device_name, text_widget):
        """Загрузить текст из файла"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", text)

                # Автоматически сохраняем в БД
                self.save_text_to_db(device_name, text_widget)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def reset_text(self, device_name, text_widget):
        """Сбросить текст к значениям по умолчанию"""
        if messagebox.askyesno("Подтверждение", "Сбросить текст к значениям по умолчанию?"):
            default_text = self.get_default_text(device_name)
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", default_text)
            self.save_text_to_db(device_name, text_widget)

    def show_func(self):
        """Раздел с функциями"""
        self.clear_main_frame()

        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        for device in self.devices:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=device)

            # Разделяем на две колонки
            left_frame = ttk.Frame(tab)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            right_frame = ttk.Frame(tab)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Левая колонка - функции (текст)
            ttk.Label(left_frame, text=f"Функции {device}",
                      font=('Arial', 12)).pack()

            func_text = Text(left_frame, height=12, width=40)
            func_text.pack(fill=tk.BOTH, expand=True, pady=5)

            # Правая колонка - примеры (изображения)
            ttk.Label(right_frame, text=f"Примеры для {device}",
                      font=('Arial', 12)).pack()

            func_img_label = ttk.Label(right_frame)
            func_img_label.pack(pady=10)

            # Загружаем изображение из БД
            self.load_image_from_db(device, func_img_label)

            # Кнопки внизу
            btn_frame = ttk.Frame(tab)
            btn_frame.pack(side=tk.BOTTOM, pady=10)

            ttk.Button(btn_frame, text="Добавить текст",
                       command=lambda: func_text.insert(tk.END, "• Новая функция\n")).pack(side=tk.LEFT, padx=2)

            ttk.Button(btn_frame, text="Загрузить фото",
                       command=lambda d=device, l=func_img_label: self.load_image_to_db(d, l)).pack(side=tk.LEFT, padx=2)

            ttk.Button(btn_frame, text="Сохранить всё",
                       command=self.save_all).pack(side=tk.LEFT, padx=2)

    def save_all(self):
        """Сохранить все изменения"""
        self.conn.commit()
        messagebox.showinfo("Сохранено", "Все данные сохранены в БД")

    def export_db(self):
        """Экспорт базы данных"""
        try:
            # Создаем копию БД
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"devices_backup_{timestamp}.db"
            shutil.copy2('devices.db', backup_file)

            messagebox.showinfo("Экспорт", f"База данных экспортирована в файл:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать БД: {str(e)}")

    def clear_db_confirm(self):
        """Подтверждение очистки базы данных"""
        if messagebox.askyesno("Внимание!",
                               "Вы уверены, что хотите очистить всю базу данных?\nЭто действие нельзя отменить!"):
            self.clear_db()

    def clear_db(self):
        """Очистка базы данных"""
        try:
            self.cursor.execute("DELETE FROM devices")
            self.conn.commit()

            # Восстанавливаем начальные данные
            for device in self.devices:
                default_text = self.get_default_text(device)
                self.cursor.execute('''
                    INSERT INTO devices (device_name, text_content)
                    VALUES (?, ?)
                ''', (device, default_text))
            self.conn.commit()

            messagebox.showinfo("Очищено", "База данных очищена и восстановлены значения по умолчанию")
            self.show_welcome()  # Обновляем статистику
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить БД: {str(e)}")

    def __del__(self):
        """Закрытие соединения с БД при удалении объекта"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    root = tk.Tk()
    app = DeviceAppWithDB(root)
    root.mainloop()

if __name__ == "__main__":
    main()
