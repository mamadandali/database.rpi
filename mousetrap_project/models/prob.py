# کتابخانههای لازم
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# ----------------------
# ۱. دادههای ورودی شما (جایگزین کنید)
# ----------------------
# فرض میکنیم سه آرایه داریم:
temperature = np.array([25, 30, 18, 22, 35])  # مثال: دما
humidity = np.array([60, 80, 45, 70, 90])     # مثال: رطوبت
labels = np.array([0, 1, 0, 1, 1])            # مثال: برچسب (۰ یا ۱)

# ----------------------
# ۲. ترکیب دادهها در ماتریس ویژگیها
# ----------------------
X = np.column_stack((temperature, humidity))  # ماتریس ویژگیها (دما و رطوبت)
y = labels                                     # آرایه برچسبها

# ----------------------
# ۳. پیشپردازش دادهها
# ----------------------
# نرمالسازی دادهها با StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# تقسیم داده به آموزش و آزمون (۸۰٪ آموزش، ۲۰٪ آزمون)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# ----------------------
# ۴. آموزش مدل
# ----------------------
# ایجاد و آموزش مدل رگرسیون لجستیک
model = LogisticRegression(class_weight='balanced')  # تنظیم وزن برای دادههای نامتعادل
model.fit(X_train, y_train)

# ----------------------
# ۵. ارزیابی مدل
# ----------------------
# پیشبینی روی داده آزمون
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]  # احتمال کلاس مثبت (۱)

# محاسبه معیارهای ارزیابی
print("\nنتایج ارزیابی:")
print("دقت (Accuracy):", accuracy_score(y_test, y_pred))
print("صحت (Precision):", precision_score(y_test, y_pred))
print("فراخوانی (Recall):", recall_score(y_test, y_pred))
print("F1-Score:", f1_score(y_test, y_pred))
print("AUC-ROC:", roc_auc_score(y_test, y_proba))

# ----------------------
# ۶. پیشبینی روی داده جدید
# ----------------------
# مثال: دمای ۲۸ و رطوبت ۷۵
new_data = np.array([[28, 75]])  # شکل باید (1, 2) باشد
new_data_scaled = scaler.transform(new_data)  # نرمالسازی با اسکیلر آموزشدیده

# پیشبینی نهایی
prediction = model.predict(new_data_scaled)
probability = model.predict_proba(new_data_scaled)[0][1]

print("\nپیشبینی برای داده جدید:")
print("کلاس پیشبینیشده:", prediction)
print("احتمال وقوع رویداد (کلاس ۱):", probability)
