import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year: int': int(datetime.datetime.today().year)
    }
