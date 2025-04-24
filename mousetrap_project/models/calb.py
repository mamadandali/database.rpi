import statistics

def calibrate_sensors(temperatures, threshold, calibration_callback):
    """
    دماسنجهای معیوب را شناسایی کرده و عملیات کالیبراسیون را اجرا میکند.
    
    پارامترها:
        temperatures (list): لیست دماهای خوانده شده از سنسورها
        threshold (float): حد مجاز اختلاف دما از میانه (بر حسب درجه)
        calibration_callback (function): تابعی که برای کالیبراسیون دماسنج معیوب فراخوانی میشود
    """
    if len(temperatures) < 1:
        return
    
    median_temp = statistics.median(temperatures)
    faulty_indices = []
    
    for index, temp in enumerate(temperatures):
        if abs(temp - median_temp) > threshold:
            faulty_indices.append(index)
    
    if faulty_indices:
        print(f"⚠️ خطا در دماسنج(های) {faulty_indices} | میانه سیستم: {median_temp}°C")
        for idx in faulty_indices:
            calibration_callback(idx)
    else:
        print("✅ تمام دماسنجها نرمال هستند.")

# مثال استفاده:
def simulate_calibration(sensor_id):
    print(f"انجام کالیبراسیون برای دماسنج {sensor_id}...")

# تست سناریوهای مختلف
if __name__ == "__main__":
    # سناریو 1: سه دماسنج با یک خطای واضح
    temps1 = [20.1, 22.3, 50.0]
    calibrate_sensors(temps1, 5.0, simulate_calibration)
    
    # سناریو 2: پنج دماسنج با یک خطا
    temps2 = [20.0, 21.5, 22.0, 23.3, 49.9]
    calibrate_sensors(temps2, 4.0, simulate_calibration)
    
    # سناریو 3: بدون خطا
    temps3 = [22.0, 22.1, 21.9]
    calibrate_sensors(temps3, 1.0, simulate_calibration)