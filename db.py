import pymongo

# Конфигурируем БД
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['ege']
collection = db['users']


# Получаем пользователя
def get_user(id):
    return collection.find_one({'id': id})


# Получаем предметы, которые сдает пользователь
def get_subjects(id):
    return collection.find_one({'id': id})['subjects']


# Получаем всех пользоваталей
def get_all_users():
    return collection.find()


# Добавляем пользователя
def add_user(id):
    collection.insert_one({'id': id, 'subjects': []})


# Вставляем предмет или меняем его статус
def add_subject(id, subject):
    user = collection.find_one({'id': id})
    subject_entry = next((s for s in user['subjects'] if s['name'] == subject), None)

    if subject_entry:
        subject_entry['active'] = not subject_entry['active']
    else:
        user['subjects'].append({'name': subject, 'active': True})

    user['subjects'] = [s for s in user['subjects'] if s['active']]

    collection.update_one({'id': id}, {'$set': {'subjects': user['subjects']}})


# Получаем количество пользователей
def count_users():
    return collection.count_documents({})
