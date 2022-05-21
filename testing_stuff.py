import soundcloud
import math
import wget
import os.path
import sys
def download_stream(activities, count=1):
    for i in range(count):
        for activity in activities.collection:
            print(activity.type)
            track = activity.origin
            title = track.title.replace('/', '_')
            print(title)
            #print(track.streamable)
            #print(track.downloadable)
            
            if activity.type == 'track' or activity.type == 'track-repost':
                stream_url = client.get(track.stream_url, allow_redirects=False)
                url = stream_url.location
                path = title + '.mp3'
                if os.path.isfile(path):
                    print('Already downloaded')
                else:
                    wget.download(url, path)
        next = activities.next_href.split('=')[-1]
        activities = client.get('me/activities/all', cursor=next)
def get_followers(name):
    followings=[]
    user = client.get('/users/' + name)
    count = user.followings_count
    loop_count = math.ceil(count/50)
    for i in range(loop_count):
        followings.extend(client.get('/users/' + name + '/followings', offset=50*i))
    return followings

def build_table(following):
    freq_table = {}
    for i in following:
        print(i.permalink, end="")
        followings=get_followers(i.permalink)
        #print(i.permalink)
        for j in followings:
            if j.permalink in freq_table:
                print('+', end="")
                freq_table[j.permalink] += 1
            else:
                print('0', end="")
                freq_table[j.permalink] = 1
        print('')
    return freq_table

def print_table(freq_table, followings):
    magic_from_SO = sorted( ((v,k) for k,v in freq_table.items()), reverse=True)
    follow_list=[]

    for i in followings:
        follow_list.append(i.permalink)


    for i in magic_from_SO:
        if i[0] < 3:
            break
        if i[1] not in follow_list:
            print('+', end="")
        print(i[1] , ":" , i[0])


#client = soundcloud.Client(client_id="f367f38aa03863c376a626bcbab2e126")




scdl_client_id='74b69a87904e81fab39f4319552a4c9d',
client = soundcloud.Client(
            client_id='74b69a87904e81fab39f4319552a4c9d',
            client_secret='9b860adc16b41862736db68915ef8e22',
            username='hatten@archlinux.us',
            password='sound[{'
            )
#redirect(client.authorize_url())
#client.authorize_url()


#access_token, expires, scope, refresh_token = client.exchange_token(
            #code=request.args.get('code'))
print("Hi There, %s" % client.get('/me').username)



#download_stream(activities, 2)

activities = client.get('/me/activities/all')
print(activities.collection[0].origin.title)
print(client.get(activities.next_href).collection[0].origin.title)
print(client.get(activities.future_href).collection[0].origin.title)
#print(client.get('/me/activities/all').collection[0].title)
#sys.exit(0)

activities = client.get('/me/activities/all')
print('current')
for activity in activities.collection[:3]:
    print(activity.origin.title)

activities = client.get(activities.next_href)
print('next')
for activity in activities.collection[:3]:
    print(activity.origin.title)

activities = client.get(activities.future_href)
print('future')
for activity in activities.collection[:3]:
    print(activity.origin.title)
#next = activities.next_href.split('=')[-1]
#print(next)
#next_activities = client.get('me/activities/all', cursor=next)
#print(activities.future_href)
#a = activities.future_href.split('&')[-2]
#b = a.split('?')[-1]
#c = b.split('=')[-1]
#print(a)
#print(b)
#print(c)
#c = '41d55b73-54c0-0000-6390-d4db2ad3c2a2'

#print(activities.next_href)
#print(activities.future_href)
#activities = client.get(activities.future_href)
#for activity in activities.collection:
    #print(activity.type)
    #print(activity.origin.title)
#activities = next_activities
    #break
    #stream_url = client.get(track.stream_url, allow_redirects=False)
    #url = stream_url.location
    #print(dir(activity.origin))
    #print(dir(activity.fields))

#print(dir(client.get('/me/activities')))
#print(client.get('/me/act'))



#followings = get_followers('jakkdl')
#table = build_table(followings)
#print_table(table, followings)
