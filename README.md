# Проект YaTube
Проект «Yatube» - платформа для блогов с авторизацией, персональными лентами, с комментариями и подпиской на авторов, с программными тестами. 

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:RusanovaAnna/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:
```
cd yatube
```

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```
