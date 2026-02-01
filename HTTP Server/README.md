# PyHTTP Server

یک سرور HTTP/1.1 ساده که از پایه با پایتون و سوکت‌نویسی (Socket Programming) پیاده‌سازی شده است.

---

## Setup

```bash
# نصب پیش‌نیازها
pip install -r requirements.txt

# پیشنهاد ما استفاده از پکیج منیجیر uv میباشذ
uv sysnc

# یا
uv add -r requirements.txt

# اجرای ساده
python main.py

# اجرا با uv
uv run main.py

# اجرا با پارامترهای دلخواه
python main.py --port 8000 --debug --static ./public

# اجرا با پارامترهای دلخواه uv
uv run main.py --port 8000 --debug --static ./public

```

# Parameters

```bash

# --port -> در چه پورتی سرور ما اجرا شود

# --debug -> فعال سازی حالت عیب یابی و گرفتن لاگ بیشتر

# --static -> محل قرارگیری فایل های js , css , html

```
