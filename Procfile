web: gunicorn camera_rental.wsgi:application --log-file - --timeout 300
## --timeout 300 是一個選用參數，用於設置 Gunicorn 的請求超時時間，以防長時間請求導致斷開。