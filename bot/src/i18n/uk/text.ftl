start = 👋 Привіт, <b>{ $first_name }!</b>

    Я — ваш бот техпідтримки, і я тут, щоб допомогти вам швидко та зручно.

    💡 Ось що ви можете зробити:

    📩 <b>Створити заявку на допомогу</b>
    📝 <b>Перевірити статус існуючої заявки</b>

    Щоб почати, оберіть одну з опцій нижче
unknown_user = Ви ще не зареєстровані.
describe_problem = Будь ласка, опишіть вашу проблему максимально детально.
incorrect_name = Ім'я містить недопустимі символи. Введіть ще раз.
correct_name = Ви ввели <b>{ $name }</b>
enter_name_again = Будь ласка, введіть своє ім'я та прізвище.
enter_respond_again = Будь ласка, надішльть відповідь ще раз
name_saved = І'мя збережено ✅
is_correct_description = Надіслати заявку?
enter_description_again = Будь ласка, введіть опис ще раз.
request_saved = Заявку надіслано ✅
respond_sanded = Відповідь надіслано ✅
status = 📊 Статистика заявок:

        <b>🟢 Відкритих: { $open_count }
        🟡 В процесі: { $in_progress_count }</b>
send_respond = Надішліть відповідь
ticket_not_found = Заявки з id { $ticket_id } не знайдено
ticket = 🎫 <b>Заявка { $ticket_id }</b>

        🔎 <b>Опис:
        { $description}

        Відповіді:
        { $comments }</b>
        <i>📌 Статус: { $status }
        🕒 Створено: { $created_at}</i>
correct_respond = Надіслати користувачу відповідь?