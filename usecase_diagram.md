graph TB
    subgraph Actors["👥 Участники системы"]
        KworkUser["👤 Kwork User<br/>(Пользователь Kwork)"]
        Manager["👨‍💼 Manager<br/>(Менеджер)"]
        Admin["⚙️ Admin<br/>(Администратор)"]
    end

    subgraph System["🤖 Kwork Bot System"]
        UC1["1️⃣ View Messages<br/>(Просмотр сообщений)"]
        UC2["2️⃣ Check Dialogs<br/>(Проверка диалогов)"]
        UC3["3️⃣ Send Message<br/>(Отправка сообщения)"]
        UC4["4️⃣ Create Chat Topic<br/>(Создание топика)"]
        UC5["5️⃣ Process Message AI<br/>(Обработка ИИ)"]
        UC6["6️⃣ Process Message Manager<br/>(Обработка менеджером)"]
        UC7["7️⃣ Handle Files<br/>(Работа с файлами)"]
        UC8["8️⃣ Generate AI Response<br/>(Генерация ответа GPT)"]
        UC9["9️⃣ Manage ManagerMode<br/>(Управление режимом)"]
        UC10["🔟 Check Notifications<br/>(Проверка уведомлений)"]
        UC11["1️⃣1️⃣ Forward to Telegram<br/>(Пересылка в TG)"]
        UC12["1️⃣2️⃣ View Chat History<br/>(История чата)"]
        UC13["1️⃣3️⃣ Extract Text<br/>(Извлечение текста)"]
        UC14["1️⃣4️⃣ Mark as Read<br/>(Отметить прочитанным)"]
    end

    %% Kwork User interactions
    KworkUser -->|initiates| UC1
    KworkUser -->|views| UC2
    KworkUser -->|sends| UC3

    %% Manager interactions
    Manager -->|handles| UC6
    Manager -->|checks| UC12
    Manager -->|controls| UC9

    %% Admin interactions
    Admin -->|creates| UC4

    %% Internal flow dependencies
    UC1 -->|includes| UC2
    UC2 -->|checks for| UC10
    UC2 -->|triggers| UC5
    UC2 -->|triggers| UC6

    UC5 -->|uses| UC7
    UC5 -->|calls| UC8
    UC5 -->|sends via| UC11

    UC6 -->|uses| UC7
    UC6 -->|sends via| UC11

    UC7 -->|processes| UC13

    UC8 -->|uses| UC3
    UC3 -->|sends through| UC11

    UC11 -->|marks as| UC14

    UC10 -->|updates| UC9

    %% Styling
    classDef actor fill:#FFE4C4,stroke:#8B4513,stroke-width:2px,color:#000
    classDef usecase fill:#E1F5FE,stroke:#01579B,stroke-width:2px,color:#000
    classDef system fill:#F3E5F5,stroke:#512DA8,stroke-width:2px,color:#000

    class KworkUser,Manager,Admin actor
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8,UC9,UC10,UC11,UC12,UC13,UC14 usecase
    class System system
