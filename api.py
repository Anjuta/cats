#coding utf8
import requests
import vk_auth
import vk
import datetime
from peewee import *
import multiprocessing
from functools import partial
db = SqliteDatabase('my.db')

class Images(Model):
    url = CharField()
    result = CharField()

    class Meta:
        database = db

Images.create_table(True)

def get_images(access_token, lock, offset):
    try:
        print('starting ' + str(offset) + ', time: ' + str(datetime.datetime.now()))
        members = requests.post('https://api.vk.com/method/execute?access_token='+access_token+'&code=return API.groups.getMembers({"group_id":"habr","offset":"'+str(offset)+'","count":"10"});')
        members = members.json()['response']
        for i in range(1, len(members['users'])):
            try:
                member = str(members['users'][i])
                r = requests.post('https://api.vk.com/method/execute?access_token='+access_token+'&code=return API.photos.getAll({"owner_id":"'+member+'","photo_sizes":"1","count":"1000"});')
                fotos = r.json()
                for j in range (1, len(fotos['response'])):
                    cur1= fotos['response'][j]
                    cur = cur1['sizes'][-1:]
                    lock.acquire()
                    try:
                        Images.create(url=cur[0]['src'], result='None')
                    finally:
                        lock.release()
            except Exception as err:
                print('Member ' + str(i) + ' error:', err)
    except Exception as err:
        print(err)
        return
    finally:
        print('done ' + str(offset) + ', time: ' + str(datetime.datetime.now()))

if __name__ == "__main__":
    auth = vk_auth.VKAuth(['photos'], '5786118', '5.52')
    auth.auth()
    access_token = auth.get_token()
    user_id = auth.get_user_id()
    session = vk.Session(access_token=access_token)
    api = vk.API(session)

    rep = list(i * 10 for i in range(0, 5))
    #print(rep)
    pool = multiprocessing.Pool()
    m = multiprocessing.Manager()
    l = m.Lock()
    func = partial(get_images, access_token, l)
    pool.map(func, rep)
    pool.close()
    pool.join()
